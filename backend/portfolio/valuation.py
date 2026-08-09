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


def active_engine() -> str:
    engine = os.getenv("PORTFOLIO_VALUATION_ENGINE", LEGACY).strip().lower()
    if engine not in ENGINES:
        logger.warning("Unknown PORTFOLIO_VALUATION_ENGINE %r; falling back to %s.", engine, LEGACY)
        return LEGACY
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

def _scraper_price(property_type: str, location: str) -> float:
    from backend.predictions.utils import get_current_market_price

    try:
        return float(get_current_market_price(property_type, (location or "").strip().lower()) or 0.0)
    except Exception as exc:
        logger.warning("Scraper price unavailable for %s/%s: %s", property_type, location, exc)
        return 0.0


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

def _value_legacy(prop) -> PropertyValuation:
    """Previous behaviour, reproduced exactly - unit bugs and all."""
    price = _scraper_price(prop.property_type, prop.location)
    return PropertyValuation(
        capital_value=price,
        monthly_income=_monthly_rent(prop) if prop.property_type == "rental" else None,
        method="legacy_scraper",
        confidence="low",
        notes=["Legacy engine: land is per perch and rental is a monthly rent, both "
               "summed as capital values."],
    )


def _value_scraper_fixed(prop) -> PropertyValuation:
    """Scraper prices with the units corrected."""
    property_type = prop.property_type
    notes: list[str] = []

    if property_type == "land":
        per_perch = _scraper_price("land", prop.location)
        size = _land_size(prop)
        if not size:
            notes.append("Plot size is not recorded, so the per-perch rate stands in for the plot value.")
            return PropertyValuation(per_perch, None, "scraper_land_per_perch", "low", notes)
        return PropertyValuation(
            per_perch * size, None, "scraper_land_total", "medium",
            [f"Per-perch rate x {size:g} perches."],
        )

    if property_type == "rental":
        rent = _monthly_rent(prop) or _scraper_price("rental", prop.location)
        capital, annual_yield = _capitalise(rent)
        return PropertyValuation(
            capital, rent, "scraper_rental_capitalised", "low",
            [f"Rent capitalised at {annual_yield:.2%} annual yield; rent is reported separately "
             "and is not part of the portfolio capital value."],
        )

    return PropertyValuation(
        _scraper_price("housing", prop.location), None, "scraper_housing", "low",
        ["District average sale price; not specific to this property."],
    )


def _value_hybrid(prop, db=None, valuation_date: date | None = None) -> PropertyValuation:
    """Per-property ML models moved by the index, with a per-property fallback."""
    from backend.portfolio.valuation_v2 import value_property_v2

    return value_property_v2(PropertyValuation, prop, db=db, valuation_date=valuation_date)

    # Historical implementation retained below for comparison context. Hybrid
    # now exits through the canonical V2 service above.
    from backend.predictions import market_index

    property_type = prop.property_type

    if property_type == "land":
        payload = _land_payload(prop)
        if payload is None:
            fallback = _value_scraper_fixed(prop)
            fallback.notes.append("Land model unavailable: plot size is not recorded.")
            return fallback
        try:
            from ml.land_service.service import predict_land_price

            result = predict_land_price(payload)
            factor = market_index.growth_factor("land", anchor_period=payload["period"])
            total = float(result["total_value"]) * factor.value
            notes = [f"Land model x index factor {factor.value:.4f} ({factor.confidence})."]
            notes.extend(result["details"]["coverage"]["note"] for _ in (0,))
            return PropertyValuation(total, None, "model_land", result.get("confidence", "medium"), notes)
        except Exception as exc:
            logger.warning("Land model failed for property %s: %s", getattr(prop, "id", "?"), exc)
            fallback = _value_scraper_fixed(prop)
            fallback.notes.append(f"Land model failed: {type(exc).__name__}.")
            return fallback

    if property_type == "rental":
        rent = _monthly_rent(prop)
        if rent:
            capital, annual_yield = _capitalise(rent)
            return PropertyValuation(
                capital, rent, "stored_rent_capitalised", "medium",
                [f"The recorded rent is better evidence than a model estimate; capitalised at "
                 f"{annual_yield:.2%}."],
            )
        return _value_scraper_fixed(prop)

    payload = _housing_payload(prop)
    if payload is None:
        fallback = _value_scraper_fixed(prop)
        fallback.notes.append(
            "House model unavailable: HousingProperty records no bedrooms or bathrooms, which the "
            "model requires. Adding those two columns would enable it."
        )
        return fallback

    try:
        from ml.house_service.service import predict_house_price

        result = predict_house_price(payload)
        factor = market_index.growth_factor("house")
        total = float(result["predicted_value"]) * factor.value
        return PropertyValuation(
            total, None, "model_house", "medium",
            [f"House model x index factor {factor.value:.4f} ({factor.confidence})."],
        )
    except Exception as exc:
        logger.warning("House model failed for property %s: %s", getattr(prop, "id", "?"), exc)
        fallback = _value_scraper_fixed(prop)
        fallback.notes.append(f"House model failed: {type(exc).__name__}.")
        return fallback


ENGINE_FUNCTIONS = {
    LEGACY: _value_legacy,
    SCRAPER_FIXED: _value_scraper_fixed,
    HYBRID: _value_hybrid,
}


def value_property(prop, engine: str | None = None, db=None, valuation_date: date | None = None) -> PropertyValuation:
    """Value one property with the selected engine, never raising."""
    chosen = (engine or active_engine()).strip().lower()
    function = ENGINE_FUNCTIONS.get(chosen, _value_legacy)
    try:
        if chosen == HYBRID:
            return _value_hybrid(prop, db=db, valuation_date=valuation_date)
        return function(prop)
    except Exception as exc:
        logger.warning("Valuation failed for property %s: %s", getattr(prop, "id", "?"), exc)
        return PropertyValuation(None, None, "failed", "low", [f"{type(exc).__name__}: {exc}"])
