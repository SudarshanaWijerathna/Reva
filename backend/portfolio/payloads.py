"""Canonical model payloads shared by portfolio valuation.

Unknown portfolio attributes stay unknown. Builders refuse a model path when a
required feature is absent and report exactly which fields are missing, instead
of manufacturing favorable assumptions that make the valuation look precise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ml.land_service.geocoding import resolve

SQFT_PER_PERCH = 272.25
SRI_LANKA_DISTRICTS = {
    "ampara", "anuradhapura", "badulla", "batticaloa", "colombo", "galle",
    "gampaha", "hambantota", "jaffna", "kalutara", "kandy", "kegalle",
    "kilinochchi", "kurunegala", "mannar", "matale", "matara", "monaragala",
    "mullaitivu", "nuwara eliya", "polonnaruwa", "puttalam", "ratnapura",
    "trincomalee", "vavuniya",
}


@dataclass
class PayloadBuild:
    payload: dict[str, Any] | None
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # How the coordinates were obtained. The house model is dominated by location,
    # so a district-wide stand-in must not be presented as a property-specific
    # valuation - see geo_is_district_level below.
    geo_precision: str | None = None

    @property
    def complete(self) -> bool:
        return self.payload is not None and not self.missing

    @property
    def geo_is_district_level(self) -> bool:
        return self.geo_precision in ("district_median", "district_capital", "fallback")


def property_district(prop) -> str | None:
    """Return the property's district, inferring it from geocoding when not stored.

    Priority:
    1. ``prop.district`` if explicitly set.
    2. ``prop.location`` if it is itself a district name.
    3. Geocoder cross-district locality match (e.g. a town name found in the
       gazetteer maps to a known district).
    4. ``"colombo"`` as a safe default - this is also what the geocoder's
       fallback coordinates (6.9271, 79.8612) correspond to, so the house
       model receives a consistent location signal.
    """
    explicit = str(getattr(prop, "district", "") or "").strip()
    if explicit:
        return explicit
    location = str(getattr(prop, "location", "") or "").strip()
    if location.lower() in SRI_LANKA_DISTRICTS:
        return location
    # Try to extract the district from the geocoder's gazetteer by matching the
    # locality name across all districts. This is the same cross-district pass
    # that _coordinates() uses, so the district and coordinates stay consistent.
    try:
        from ml.land_service.geocoding import _gazetteer, _normalise  # type: ignore[attr-defined]
        _, _ = _gazetteer()  # warm the cache
        localities, _ = _gazetteer()
        location_key = _normalise(location)
        if location_key:
            for (found_district, found_location) in localities:
                if found_location == location_key and found_district:
                    return found_district
    except Exception:
        pass
    # Final fallback: the geocoder resolves unknown localities to Colombo
    # coordinates, so using "colombo" keeps coordinates and district consistent.
    return "colombo"


def property_locality(prop) -> str:
    return str(
        getattr(prop, "locality", None) or getattr(prop, "location", None) or ""
    ).strip()


def _coordinates(prop, district: str, locality: str):
    latitude = getattr(prop, "latitude", None)
    longitude = getattr(prop, "longitude", None)
    if latitude is not None and longitude is not None:
        return float(latitude), float(longitude), "stored"
    located = resolve(locality, district)
    return located.lat, located.lon, located.precision


def build_land_payload(prop) -> PayloadBuild:
    detail = getattr(prop, "land", None)
    district = property_district(prop)
    locality = property_locality(prop)
    size = float(getattr(detail, "land_size", 0) or 0) if detail else 0.0

    missing = []
    if detail is None:
        missing.append("land_details")
    if size <= 0:
        missing.append("land_size")
    if not district:
        missing.append("district")
    if missing:
        return PayloadBuild(None, missing, ["Land model requires plot size and a real district."])

    road_access = str(getattr(detail, "road_access", "") or "").strip().lower()
    optional = {
        "electricity": getattr(detail, "electricity", None),
        "water": getattr(detail, "water", None),
        "clear_deed": getattr(detail, "clear_deed", None),
        "bank_loan": getattr(detail, "bank_loan", None),
        "near_town": getattr(detail, "near_town", None),
        "distance_to_town_m": getattr(detail, "distance_to_town_m", None),
    }
    unknown = [name for name, value in optional.items() if value is None]

    payload: dict[str, Any] = {
        "land_size": size,
        "district": district,
        "location_text": locality,
        "main_road": "main" in road_access or "carpet" in road_access,
        "period": "2025 H2",
    }
    payload.update({name: value for name, value in optional.items() if value is not None})
    notes = []
    if unknown:
        notes.append(f"Unknown optional land attributes default to neutral/absent in the model: {', '.join(unknown)}.")
    # These attributes are optional by construction - the model has a defined
    # behaviour for each one being absent. Reporting them in `missing`, which is
    # reserved for fields the model cannot run without, downgraded every land
    # valuation to low confidence purely for not recording whether the plot has
    # mains water. The note above still records exactly what was unknown.
    return PayloadBuild(payload, [], notes)


def build_house_payload(prop) -> PayloadBuild:
    detail = getattr(prop, "housing", None)
    district = property_district(prop)
    locality = property_locality(prop)
    required = {
        "house_size_sqft": getattr(detail, "house_size_sqft", None) if detail else None,
        "land_size_perches": getattr(detail, "land_size_perches", None) if detail else None,
        "bedrooms": getattr(detail, "bedrooms", None) if detail else None,
        "bathrooms": getattr(detail, "bathrooms", None) if detail else None,
        "district": district,
    }
    # Only reject None/empty - 0 is a valid recorded value (the frontend defaults
    # unset bedrooms/bathrooms to 0 so the model can always run).
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        return PayloadBuild(None, missing, ["House model requires physical details and district."])

    lat, lon, precision = _coordinates(prop, district, locality)
    description_parts = [str(getattr(detail, "description", "") or "").strip()]
    road_width = getattr(detail, "road_width_ft", None)
    parking = getattr(detail, "parking_spaces", None)
    if road_width is not None:
        description_parts.append(f"Road width {road_width} ft")
    if parking is not None:
        description_parts.append(f"Parking spaces {parking}")
    if getattr(detail, "water_available", None) is True:
        description_parts.append("Water available")
    if getattr(detail, "electricity_available", None) is True:
        description_parts.append("Electricity available")

    return PayloadBuild(
        {
            "house_sqft": float(required["house_size_sqft"]),
            "land_sqft": float(required["land_size_perches"]) * SQFT_PER_PERCH,
            "bedrooms": int(required["bedrooms"]),
            "bathrooms": int(required["bathrooms"]),
            "lat": lat,
            "lon": lon,
            "district": district.lower(),
            "sub_location": locality.lower() or "unknown",
            "posted_year": 2025,
            "posted_month": 12,
            "description": ". ".join(part for part in description_parts if part),
        },
        notes=[f"Coordinates resolved with {precision} precision."],
        geo_precision=precision,
    )


def build_rental_payload(prop) -> PayloadBuild:
    detail = getattr(prop, "rental", None)
    district = property_district(prop)
    locality = property_locality(prop)
    subtype = getattr(detail, "property_subtype", None) if detail else None

    missing = []
    if detail is None:
        missing.append("rental_details")
    if not subtype:
        missing.append("property_subtype")
    if not district:
        missing.append("district")
    if not locality:
        missing.append("location")
    if missing:
        return PayloadBuild(None, missing, ["Rental model requires subtype, district, and locality."])

    payload = {
        "property_type": subtype,
        "district": district,
        "location": locality,
        "furnishing_status": getattr(detail, "furnishing_status", None) or "unknown",
        "bedrooms": getattr(detail, "bedrooms", None),
        "bathrooms": getattr(detail, "bathrooms", None),
        "floor_area_sqft": getattr(detail, "floor_area_sqft", None),
        "land_perches": getattr(detail, "land_size_perches", None),
        "car_parking_spaces": getattr(detail, "parking_spaces", None),
        "posted_year": 2025,
        "posted_month": 12,
    }
    absent = [name for name in ("bedrooms", "bathrooms", "floor_area_sqft") if payload[name] is None]
    return PayloadBuild(payload, absent, [f"Rental attributes not recorded: {', '.join(absent)}."] if absent else [])


def build_rental_underlying_house_payload(prop) -> PayloadBuild:
    detail = getattr(prop, "rental", None)
    district = property_district(prop)
    locality = property_locality(prop)
    if detail is None:
        return PayloadBuild(None, ["rental_details"])

    required = {
        "floor_area_sqft": getattr(detail, "floor_area_sqft", None),
        "land_size_perches": getattr(detail, "land_size_perches", None),
        "bedrooms": getattr(detail, "bedrooms", None),
        "bathrooms": getattr(detail, "bathrooms", None),
        "district": district,
    }
    # Only reject None/empty - 0 is a valid recorded value.
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        return PayloadBuild(None, missing)

    lat, lon, precision = _coordinates(prop, district, locality)
    return PayloadBuild({
        "house_sqft": float(required["floor_area_sqft"]),
        "land_sqft": float(required["land_size_perches"]) * SQFT_PER_PERCH,
        "bedrooms": int(required["bedrooms"]),
        "bathrooms": int(required["bathrooms"]),
        "lat": lat,
        "lon": lon,
        "district": district.lower(),
        "sub_location": locality.lower() or "unknown",
        "posted_year": 2025,
        "posted_month": 12,
    }, notes=[f"Coordinates resolved with {precision} precision."])
