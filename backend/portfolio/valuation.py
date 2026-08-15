"""
Portfolio valuation.

``calculate_portfolio`` summed three incompatible quantities into one
``portfolio_value``:

* **housing** - a total sale price, correct
* **land** - a price *per perch*, so a 40-perch plot counted as one perch
* **rental** - a *monthly rent*, added to capital values as though 657,000 of
  rent were comparable to 85,120,000 of house

Everything that enters ``portfolio_value`` here is a capital value in LKR. Rental
income is reported separately, because rent is a flow and a portfolio value is a
stock; adding them produces a number that means nothing.

Three engines, selected by ``PORTFOLIO_VALUATION_ENGINE``:

``legacy``       Exactly the previous behaviour, unit bugs included. The default,
                 so nothing a user has already seen moves until it is chosen.
``scraper_fixed``The same scraper prices with the units corrected. Isolates how
                 much of any change is the unit fix alone.
``hybrid``       The per-property ML models moved by the market index, falling
                 back to ``scraper_fixed`` per property when a model cannot be
                 applied.

Splitting the middle engine out matters: without it, flipping to ``hybrid``
conflates a bug fix with a model change, and there is no way to attribute a
difference to either.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

LEGACY = "legacy"
SCRAPER_FIXED = "scraper_fixed"
HYBRID = "hybrid"
ENGINES = (LEGACY, SCRAPER_FIXED, HYBRID)

SQFT_PER_PERCH = 272.25

# Fallback capitalisation yield when the scraper cannot supply one. Roughly the
# ratio the scraper's own national averages imply (657,000 x 12 / 85,120,000).
DEFAULT_ANNUAL_YIELD = float(os.getenv("REVA_RENTAL_CAP_YIELD", "0.0926"))


_announced_engines: set[str] = set()


def _announce(engine: str, reason: str) -> None:
    """Say which engine is running, once per distinct outcome."""
    if engine in _announced_engines:
        return
    _announced_engines.add(engine)
    message = "Portfolio valuation engine: %s (%s)."
    if engine == LEGACY:
        logger.warning(
            message + " The legacy engine returns scraper district averages, not "
            "per-property model values. Set PORTFOLIO_VALUATION_ENGINE=hybrid and restart "
            "to use the ML models.",
            engine, reason,
        )
    else:
        logger.info(message, engine, reason)


def active_engine() -> str:
    raw = os.getenv("PORTFOLIO_VALUATION_ENGINE")
    if raw is None:
        # Silently defaulting is what let a configured `hybrid` sit in .env while
        # every valuation on screen came from the legacy engine.
        _announce(LEGACY, "PORTFOLIO_VALUATION_ENGINE is not set in this process")
        return LEGACY

    engine = raw.strip().lower()
    if engine not in ENGINES:
        logger.warning("Unknown PORTFOLIO_VALUATION_ENGINE %r; falling back to %s.", raw, LEGACY)
        _announce(LEGACY, f"PORTFOLIO_VALUATION_ENGINE={raw!r} is not one of {', '.join(ENGINES)}")
        return LEGACY

    _announce(engine, "from PORTFOLIO_VALUATION_ENGINE")
    return engine


@dataclass
class PropertyValuation:
    """A property's worth, with the unit and the route that produced it."""

    capital_value: float | None
    monthly_income: float | None = None
    method: str = "unavailable"
    confidence: str = "low"
    notes: list[str] = field(default_factory=list)
    lower_value: float | None = None
    upper_value: float | None = None
    valuation_as_of: date | None = None
    valuation_status: str = "legacy"
    model_version: str | None = None
    model_anchor: str | None = None
    index_version: str | None = None
    index_factor: float | None = None
    feature_hash: str | None = None
    market_monthly_rent: float | None = None
    annual_net_operating_income: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "capital_value": round(self.capital_value, 2) if self.capital_value is not None else None,
            "estimated_current_value": round(self.capital_value, 2) if self.capital_value is not None else None,
            "monthly_income": round(self.monthly_income, 2) if self.monthly_income is not None else None,
            "market_monthly_rent": round(self.market_monthly_rent, 2) if self.market_monthly_rent is not None else None,
            "annual_net_operating_income": round(self.annual_net_operating_income, 2) if self.annual_net_operating_income is not None else None,
            "value_range": {
                "lower": round(self.lower_value, 2) if self.lower_value is not None else None,
                "upper": round(self.upper_value, 2) if self.upper_value is not None else None,
                "coverage": "indicative_p80",
            },
            "valuation_as_of": self.valuation_as_of.isoformat() if self.valuation_as_of else None,
            "valuation_status": self.valuation_status,
            "valuation_method": self.method,
            "valuation_confidence": self.confidence,
            "valuation_notes": list(self.notes),
            "model_version": self.model_version,
            "model_anchor": self.model_anchor,
            "index_version": self.index_version,
            "index_factor": self.index_factor,
            "feature_hash": self.feature_hash,
            "valuation_provenance": dict(self.provenance),
        }


# --------------------------------------------------------------------------
# Scraper inputs
# --------------------------------------------------------------------------

def _scraper_price(property_type: str, location: str) -> float | None:
    """
    District average price, or None when there is none.

    Returning 0.0 for "unknown" was the single most damaging line in this module.
    Zero is a number: it is added into ``portfolio_value``, it is subtracted from
    the cost basis to produce an unrealized gain of exactly minus the purchase
    price, and it renders as "-" in the UI. So a scraper with no data for a
    location produced a portfolio that looked like a total loss, with no error
    anywhere. None propagates as "no estimate", which is the truth.
    """
    from backend.predictions.utils import get_current_market_price

    try:
        price = float(get_current_market_price(property_type, (location or "").strip().lower()) or 0.0)
    except Exception as exc:
        logger.warning("Scraper price unavailable for %s/%s: %s", property_type, location, exc)
        return None
    if price <= 0:
        logger.warning(
            "Scraper has no %s price for %r. Reporting no estimate rather than zero.",
            property_type, location,
        )
        return None
    return price


def _no_estimate(method: str, reason: str, valuation_date: date | None) -> PropertyValuation:
    """A valuation that honestly has no number, rather than a zero pretending to be one."""
    return PropertyValuation(
        capital_value=None,
        monthly_income=None,
        method=method,
        confidence="low",
        notes=[reason],
        valuation_as_of=valuation_date,
        valuation_status="unavailable",
    )


def implied_annual_yield() -> float:
    """Annual rental yield implied by the scraper's own national averages."""
    from backend.core.cache_service import get_current_prices

    try:
        prices = get_current_prices() or {}
        rent = float(prices.get("rentals", {}).get("national average", 0) or 0)
        price = float(prices.get("sales", {}).get("national average", 0) or 0)
        if rent > 0 and price > 0:
            return (rent * 12.0) / price
    except Exception as exc:
        logger.debug("Could not derive a capitalisation yield: %s", exc)
    return DEFAULT_ANNUAL_YIELD


def _capitalise(monthly_rent: float) -> tuple[float, float]:
    """Convert a monthly rent into a capital value. Returns (capital, yield)."""
    annual_yield = implied_annual_yield()
    if annual_yield <= 0:
        annual_yield = DEFAULT_ANNUAL_YIELD
    return (monthly_rent * 12.0) / annual_yield, annual_yield


# --------------------------------------------------------------------------
# Per-property detail
# --------------------------------------------------------------------------

def _land_size(prop) -> float | None:
    detail = getattr(prop, "land", None)
    size = getattr(detail, "land_size", None) if detail else None
    return float(size) if size else None


def _monthly_rent(prop) -> float | None:
    detail = getattr(prop, "rental", None)
    rent = getattr(detail, "monthly_rent", None) if detail else None
    return float(rent) if rent else None


def _housing_payload(prop) -> dict[str, Any] | None:
    """
    Build a house-model payload, or None when the record cannot support one.

    ``HousingProperty`` stores land size, floor area, floors, built year and
    condition - but not bedrooms or bathrooms, which the model requires. Rather
    than invent them, housing falls back to the scraper and says so. Adding those
    two columns is the change that would let the model value housing properly.
    """
    detail = getattr(prop, "housing", None)
    if detail is None:
        return None

    house_sqft = float(getattr(detail, "house_size_sqft", 0) or 0)
    if house_sqft <= 0:
        return None

    bedrooms = getattr(detail, "bedrooms", None)
    bathrooms = getattr(detail, "bathrooms", None)
    if bedrooms is None or bathrooms is None:
        return None

    from ml.land_service.geocoding import resolve

    location = (prop.location or "").strip()
    located = resolve(location, location)
    perches = float(getattr(detail, "land_size_perches", 0) or 0)

    return {
        "house_sqft": house_sqft,
        "land_sqft": perches * SQFT_PER_PERCH if perches > 0 else house_sqft * 1.5,
        "bedrooms": int(bedrooms),
        "bathrooms": int(bathrooms),
        "lat": located.lat,
        "lon": located.lon,
        "district": location.lower(),
        "sub_location": location.lower(),
        "posted_year": 2025,
        "posted_month": 12,
    }


def _land_payload(prop) -> dict[str, Any] | None:
    detail = getattr(prop, "land", None)
    size = _land_size(prop)
    if detail is None or not size:
        return None

    road_access = str(getattr(detail, "road_access", "") or "").strip().lower()
    return {
        "land_size": size,
        "district": (prop.location or "").strip(),
        "location_text": (prop.location or "").strip(),
        "main_road": "main" in road_access or "carpet" in road_access,
        "electricity": True,
        "clear_deed": True,
        "water": True,
        "bank_loan": False,
        "near_town": False,
        "distance_to_town_m": 0,
        "period": "2025 H2",
    }


# --------------------------------------------------------------------------
# Engines
# --------------------------------------------------------------------------

def _value_legacy(prop, valuation_date: date | None = None) -> PropertyValuation:
    """Previous behaviour, unit bugs and all - but no zero standing in for unknown."""
    price = _scraper_price(prop.property_type, prop.location)
    if price is None:
        return _no_estimate(
            "legacy_scraper",
            f"The scraper has no {prop.property_type} price for '{prop.location}'.",
            valuation_date,
        )
    return PropertyValuation(
        capital_value=price,
        monthly_income=_monthly_rent(prop) if prop.property_type == "rental" else None,
        method="legacy_scraper",
        confidence="low",
        notes=["Legacy engine: land is per perch and rental is a monthly rent, both "
               "summed as capital values."],
        valuation_as_of=valuation_date,
        valuation_status="legacy",
    )


def _value_scraper_fixed(prop, valuation_date: date | None = None) -> PropertyValuation:
    """Scraper prices with the units corrected."""
    property_type = prop.property_type
    notes: list[str] = []

    if property_type == "land":
        per_perch = _scraper_price("land", prop.location)
        if per_perch is None:
            return _no_estimate(
                "scraper_land_total", f"The scraper has no land price for '{prop.location}'.", valuation_date
            )
        size = _land_size(prop)
        if not size:
            notes.append("Plot size is not recorded, so the per-perch rate stands in for the plot value.")
            return PropertyValuation(
                per_perch, None, "scraper_land_per_perch", "low", notes,
                valuation_as_of=valuation_date, valuation_status="scraper_fixed",
            )
        return PropertyValuation(
            per_perch * size, None, "scraper_land_total", "medium",
            [f"Per-perch rate x {size:g} perches."],
            valuation_as_of=valuation_date, valuation_status="scraper_fixed",
        )

    if property_type == "rental":
        rent = _monthly_rent(prop) or _scraper_price("rental", prop.location)
        if not rent:
            return _no_estimate(
                "scraper_rental_capitalised",
                f"No recorded rent, and the scraper has no rental price for '{prop.location}'.",
                valuation_date,
            )
        capital, annual_yield = _capitalise(rent)
        return PropertyValuation(
            capital, rent, "scraper_rental_capitalised", "low",
            [f"Rent capitalised at {annual_yield:.2%} annual yield; rent is reported separately "
             "and is not part of the portfolio capital value."],
            valuation_as_of=valuation_date, valuation_status="scraper_fixed",
        )

    price = _scraper_price("housing", prop.location)
    if price is None:
        return _no_estimate(
            "scraper_housing", f"The scraper has no housing price for '{prop.location}'.", valuation_date
        )
    return PropertyValuation(
        price, None, "scraper_housing", "low",
        ["District average sale price; not specific to this property."],
        valuation_as_of=valuation_date, valuation_status="scraper_fixed",
    )


def _value_hybrid(prop, db=None, valuation_date: date | None = None) -> PropertyValuation:
    """
    Per-property ML models moved by the index, with a per-property fallback.

    The fallback is the point of this engine, and it had been lost: an earlier
    refactor left ``return value_property_v2(...)`` as the first statement with
    the old fallback body unreachable below it. Any exception inside a model then
    escaped to the catch-all in ``value_property``, which produced a valuation
    with no value, no date and no status - rendered as "-" with "Date unavailable".
    One property whose model cannot run must not erase its estimate; it falls back
    to the corrected scraper price and says why.
    """
    from backend.portfolio.valuation_v2 import value_property_v2

    try:
        return value_property_v2(PropertyValuation, prop, db=db, valuation_date=valuation_date)
    except Exception as exc:
        logger.warning(
            "Hybrid valuation failed for property %s; falling back to the corrected scraper price.",
            getattr(prop, "id", "?"), exc_info=True,
        )
        fallback = _value_scraper_fixed(prop, valuation_date)
        fallback.notes.append(
            f"Hybrid engine failed ({type(exc).__name__}: {exc}); fell back to the corrected "
            "scraper price. The backend log holds the traceback."
        )
        return fallback


ENGINE_FUNCTIONS = {
    LEGACY: _value_legacy,
    SCRAPER_FIXED: _value_scraper_fixed,
    HYBRID: _value_hybrid,
}


def value_property(prop, engine: str | None = None, db=None, valuation_date: date | None = None) -> PropertyValuation:
    """Value one property with the selected engine, never raising."""
    chosen = (engine or active_engine()).strip().lower()
    valuation_date = valuation_date or date.today()
    try:
        if chosen == HYBRID:
            return _value_hybrid(prop, db=db, valuation_date=valuation_date)
        function = ENGINE_FUNCTIONS.get(chosen, _value_legacy)
        return function(prop, valuation_date)
    except Exception as exc:
        # exc_info so the traceback reaches the log. Previously only the message
        # survived, in a note the UI showed as a tooltip and nobody read.
        logger.warning("Valuation failed for property %s.", getattr(prop, "id", "?"), exc_info=True)
        return PropertyValuation(
            None, None, "failed", "low", [f"Valuation failed: {type(exc).__name__}: {exc}"],
            valuation_as_of=valuation_date, valuation_status="unavailable",
        )
