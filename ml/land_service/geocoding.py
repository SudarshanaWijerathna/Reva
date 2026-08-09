"""
Location resolution for the land model, without a live network call on the hot path.

``derive_features`` previously called Nominatim inside every request, behind an
``lru_cache`` that died with the process. Nominatim's usage policy is one request
per second and it blocks server IPs that exceed it, so under any real traffic that
path degrades to timeouts and then to a ban - while holding a request open for up
to five seconds each time.

Resolution order:

1. **Gazetteer** (``data/geo/sri_lanka_gazetteer.csv``). Localities with median
   coordinates taken from the project's own geocoded house listings, plus a
   district-capital centroid for all 25 districts. No network, no rate limit.
2. **Persistent cache**, in Redis when configured and otherwise a JSON file, so a
   lookup survives process restarts instead of being repeated.
3. **Nominatim**, only when ``REVA_GEOCODING_ONLINE`` is enabled. Off by default:
   the gazetteer covers the districts the land model was trained on, and a
   silently-degrading network dependency in the request path is worse than a
   slightly coarser coordinate.
4. **District centroid**, which is what the old code fell back to anyway.

Every result reports how it was obtained, so a coordinate derived from a district
centroid is never mistaken for a street-level match.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
GAZETTEER_PATH = REPO_ROOT / "data" / "geo" / "sri_lanka_gazetteer.csv"
CACHE_PATH = Path(os.getenv("REVA_GEOCODE_CACHE", REPO_ROOT / "data" / "geo" / "geocode_cache.json"))

COLOMBO = (6.9271, 79.8612)
SRI_LANKA_SUFFIX = "Sri Lanka"

# Live geocoding is opt-in. See the module docstring for why.
ONLINE_ENABLED = os.getenv("REVA_GEOCODING_ONLINE", "false").strip().lower() in ("true", "1", "yes", "on")
ONLINE_TIMEOUT_SECONDS = float(os.getenv("REVA_GEOCODING_TIMEOUT", "2.0"))

_cache_lock = threading.Lock()


@dataclass(frozen=True)
class GeoResult:
    lat: float
    lon: float
    precision: str   # locality | cached | online | district_centroid | fallback
    source: str
    matched: str

    @property
    def is_precise(self) -> bool:
        return self.precision in ("locality", "cached", "online")

    def as_dict(self) -> dict:
        return {
            "lat": self.lat,
            "lon": self.lon,
            "precision": self.precision,
            "source": self.source,
            "matched": self.matched,
        }


def _normalise(value: str | None) -> str:
    return (value or "").strip().lower()


# --------------------------------------------------------------------------
# Gazetteer
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _gazetteer() -> tuple[dict[tuple[str, str], tuple[float, float]], dict[str, tuple[float, float]]]:
    """Return (localities keyed by (district, location), district centroids)."""
    import csv

    localities: dict[tuple[str, str], tuple[float, float]] = {}
    centroids: dict[str, tuple[float, float]] = {}

    if not GAZETTEER_PATH.exists():
        logger.warning("Gazetteer missing at %s; falling back to district centroids only.", GAZETTEER_PATH)
        return localities, centroids

    with GAZETTEER_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                point = (float(row["lat"]), float(row["lon"]))
            except (TypeError, ValueError):
                continue
            district, location = _normalise(row.get("district")), _normalise(row.get("location"))
            if row.get("precision") == "district_centroid" or not location:
                centroids[district] = point
            else:
                localities[(district, location)] = point

    return localities, centroids


def known_localities(district: str | None = None) -> list[str]:
    localities, _ = _gazetteer()
    target = _normalise(district)
    return sorted(
        location for (found_district, location) in localities
        if not target or found_district == target
    )


# --------------------------------------------------------------------------
# Persistent cache
# --------------------------------------------------------------------------

def _cache_key(query: str) -> str:
    return f"geocode:{query}"


def _cache_get(query: str) -> tuple[float, float] | None:
    try:
        from backend.core.redis_client import get_redis

        client = get_redis()
        if client is not None:
            raw = client.get(_cache_key(query))
            if raw:
                point = json.loads(raw)
                return float(point[0]), float(point[1])
    except Exception as exc:
        logger.debug("Redis geocode cache unavailable: %s", exc)

    try:
        if CACHE_PATH.exists():
            with CACHE_PATH.open("r", encoding="utf-8") as handle:
                point = json.load(handle).get(query)
            if point:
                return float(point[0]), float(point[1])
    except Exception as exc:
        logger.debug("File geocode cache unreadable: %s", exc)
    return None


def _cache_put(query: str, point: tuple[float, float]) -> None:
    try:
        from backend.core.redis_client import get_redis

        client = get_redis()
        if client is not None:
            client.set(_cache_key(query), json.dumps(list(point)))
    except Exception as exc:
        logger.debug("Could not write Redis geocode cache: %s", exc)

    try:
        with _cache_lock:
            existing = {}
            if CACHE_PATH.exists():
                with CACHE_PATH.open("r", encoding="utf-8") as handle:
                    existing = json.load(handle)
            existing[query] = list(point)
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with CACHE_PATH.open("w", encoding="utf-8") as handle:
                json.dump(existing, handle, indent=1, sort_keys=True)
    except Exception as exc:
        logger.debug("Could not write file geocode cache: %s", exc)


# --------------------------------------------------------------------------
# Online lookup (opt-in)
# --------------------------------------------------------------------------

def _geocode_online(query: str) -> tuple[float, float] | None:
    if not ONLINE_ENABLED:
        return None
    try:
        from geopy.geocoders import Nominatim

        geolocator = Nominatim(user_agent="reva_land_app", timeout=ONLINE_TIMEOUT_SECONDS)
        located = geolocator.geocode(query)
        if located:
            return float(located.latitude), float(located.longitude)
    except Exception as exc:
        logger.info("Online geocoding failed for %r: %s", query, exc)
    return None


# --------------------------------------------------------------------------

def resolve(location_text: str | None, district: str | None) -> GeoResult:
    """Resolve a location to coordinates, reporting how precise the answer is."""
    localities, centroids = _gazetteer()
    district_key, location_key = _normalise(district), _normalise(location_text)

    if location_key:
        point = localities.get((district_key, location_key))
        if point:
            return GeoResult(point[0], point[1], "locality", "gazetteer", f"{location_key}, {district_key}")

        # A locality name is often unique enough to match across districts.
        for (found_district, found_location), candidate in localities.items():
            if found_location == location_key:
                return GeoResult(
                    candidate[0], candidate[1], "locality", "gazetteer",
                    f"{found_location}, {found_district}",
                )

        query = f"{location_text}, {district}, {SRI_LANKA_SUFFIX}" if district else f"{location_text}, {SRI_LANKA_SUFFIX}"

        cached = _cache_get(query)
        if cached:
            return GeoResult(cached[0], cached[1], "cached", "geocode_cache", query)

        online = _geocode_online(query)
        if online:
            _cache_put(query, online)
            return GeoResult(online[0], online[1], "online", "nominatim", query)

    centroid = centroids.get(district_key)
    if centroid:
        return GeoResult(centroid[0], centroid[1], "district_centroid", "gazetteer", district_key)

    return GeoResult(COLOMBO[0], COLOMBO[1], "fallback", "colombo_default", district_key or "unknown")
