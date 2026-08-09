"""Observed-index, property-specific portfolio valuation.

Current value and forecast value are deliberately separate. This module only
uses published observations. A stale or geographically ineligible index leaves
the model anchor unchanged and marks the result accordingly.
"""

from __future__ import annotations

import math
import os
from datetime import date
from typing import Any

from backend.portfolio.payloads import (
    PayloadBuild,
    build_house_payload,
    build_land_payload,
    build_rental_payload,
    build_rental_underlying_house_payload,
    property_district,
)
from backend.portfolio.provenance import feature_hash, model_manifest
from backend.predictions import market_index

CBSL_INDEX_GEOGRAPHY = "Colombo"
DEFAULT_CAP_RATE = float(os.getenv("REVA_RENTAL_CAP_YIELD", "0.0926") or "0.0926")


def _predict(asset: str, payload: dict[str, Any], db=None) -> dict[str, Any]:
    if db is not None:
        from backend.predictions.model_runtime import predict_with_active_model

        return predict_with_active_model(db, asset, payload)
    if asset == "land":
        from ml.land_service.service import predict_land_price

        return predict_land_price(payload)
    if asset == "house":
        from ml.house_service.service import predict_house_price

        return predict_house_price(payload)
    from ml.rental_service.service import predict_rental_price

    return predict_rental_price(payload)


def _observed_factor(asset: str, prop, anchor_period: str | None, valuation_date: date):
    district = property_district(prop)
    if not district or district.strip().lower() != CBSL_INDEX_GEOGRAPHY.lower():
        return market_index.GrowthFactor(
            value=1.0,
            confidence=market_index.Confidence.DEGRADED,
            asset=asset,
            anchor_month=market_index.anchor_month_for(asset, anchor_period),
            reasons=[
                f"CBSL asking-price index covers Colombo district; property district is {district or 'unknown'}."
            ],
        )
    return market_index.growth_factor(
        asset,
        anchor_period=anchor_period,
        target_month=f"{valuation_date.year}-{valuation_date.month:02d}",
    )


def _interval(value: float, confidence: str, explicit: dict | None = None) -> tuple[float, float]:
    if explicit and explicit.get("lower") is not None and explicit.get("upper") is not None:
        return float(explicit["lower"]), float(explicit["upper"])
    width = {"high": 0.20, "medium": 0.30, "low": 0.45}.get(confidence, 0.50)
    return max(0.0, value * (1.0 - width)), value * (1.0 + width)


def _status(factor) -> str:
    if factor.confidence == market_index.Confidence.DEGRADED:
        return "anchor_only"
    if factor.target_month == market_index.latest_month(factor.asset):
        return "observed_index"
    return "observed_index"


def _result(
    valuation_cls,
    *,
    value: float | None,
    monthly_income: float | None,
    market_rent: float | None,
    noi: float | None,
    method: str,
    confidence: str,
    notes: list[str],
    valuation_date: date,
    status: str,
    payload: dict[str, Any],
    model: dict[str, Any],
    factor=None,
    interval: tuple[float, float] | None = None,
    extra_provenance: dict[str, Any] | None = None,
):
    # Monetary outputs cross an API boundary and are persisted in snapshots.
    # Normalise binary floating-point artefacts before either happens.
    value = round(value, 2) if value is not None else None
    monthly_income = round(monthly_income, 2) if monthly_income is not None else None
    market_rent = round(market_rent, 2) if market_rent is not None else None
    noi = round(noi, 2) if noi is not None else None
    lower, upper = (None, None)
    if value is not None:
        lower, upper = interval or _interval(value, confidence)
        lower, upper = round(lower, 2), round(upper, 2)
    observed = factor.target_month if factor is not None else None
    actual_as_of = valuation_date
    if observed:
        year, month = (int(part) for part in observed.split("-"))
        if observed != f"{valuation_date.year}-{valuation_date.month:02d}":
            import calendar

            actual_as_of = date(year, month, calendar.monthrange(year, month)[1])
    elif factor is not None and factor.confidence == market_index.Confidence.DEGRADED and model.get("anchor_month"):
        year, month = (int(part) for part in model["anchor_month"].split("-"))
        import calendar

        actual_as_of = date(year, month, calendar.monthrange(year, month)[1])

    index_version = f"cbsl_api:{market_index.latest_month(factor.asset)}" if factor is not None else "none"

    provenance = {
        "model": model,
        "feature_hash": feature_hash(payload),
        "index": {
            "source": "Central Bank of Sri Lanka Asking Price Index (2019=100)",
            "segment": market_index.ASSET_COLUMN.get(factor.asset) if factor is not None else None,
            "geography": "Colombo district",
            "observation": observed,
            "factor": factor.value if factor is not None else None,
            "confidence": factor.confidence if factor is not None else None,
            "reasons": factor.reasons if factor is not None else [],
            "version": index_version,
        },
    }
    if extra_provenance:
        provenance.update(extra_provenance)
    return valuation_cls(
        capital_value=value,
        monthly_income=monthly_income,
        market_monthly_rent=market_rent,
        annual_net_operating_income=noi,
        method=method,
        confidence=confidence,
        notes=notes,
        lower_value=lower,
        upper_value=upper,
        valuation_as_of=actual_as_of,
        valuation_status=status,
        model_version=model["model_version"],
        model_anchor=model.get("anchor_month"),
        index_version=provenance["index"]["version"],
        index_factor=factor.value if factor is not None else None,
        feature_hash=provenance["feature_hash"],
        provenance=provenance,
    )


def _unavailable(valuation_cls, prop, build: PayloadBuild, valuation_date: date, asset: str):
    model = model_manifest(asset)
    notes = list(build.notes) + [f"Missing required fields: {', '.join(build.missing)}."]
    return _result(
        valuation_cls,
        value=None,
        monthly_income=None,
        market_rent=None,
        noi=None,
        method=f"{asset}_unavailable",
        confidence="low",
        notes=notes,
        valuation_date=valuation_date,
        status="unavailable",
        payload={"property_id": getattr(prop, "id", None), "missing": build.missing},
        model=model,
    )


def value_land(valuation_cls, prop, db, valuation_date: date):
    build = build_land_payload(prop)
    if build.payload is None:
        return _unavailable(valuation_cls, prop, build, valuation_date, "land")
    model = model_manifest("land")
    prediction = _predict("land", build.payload, db)
    anchor = float(prediction["total_value"])
    factor = _observed_factor("land", prop, build.payload.get("period"), valuation_date)
    value = anchor * factor.value
    confidence = prediction.get("confidence", "medium")
    if build.missing or factor.confidence == market_index.Confidence.DEGRADED:
        confidence = "low" if confidence == "medium" else confidence
    notes = list(build.notes)
    notes.append(f"Land model total at anchor x observed index factor {factor.value:.4f}.")
    notes.extend(factor.reasons)
    return _result(
        valuation_cls, value=value, monthly_income=None, market_rent=None, noi=None,
        method="land_avm_x_observed_index", confidence=confidence, notes=notes,
        valuation_date=valuation_date, status=_status(factor), payload=build.payload,
        model=model, factor=factor,
    )


def value_house(valuation_cls, prop, db, valuation_date: date):
    build = build_house_payload(prop)
    if build.payload is None:
        return _unavailable(valuation_cls, prop, build, valuation_date, "house")
    model = model_manifest("house")
    prediction = _predict("house", build.payload, db)
    anchor = float(prediction["predicted_value"])
    factor = _observed_factor("house", prop, None, valuation_date)
    value = anchor * factor.value
    confidence = "medium" if factor.confidence != market_index.Confidence.DEGRADED else "low"
    notes = list(build.notes)
    notes.append(f"House AVM total at anchor x observed index factor {factor.value:.4f}.")
    notes.extend(factor.reasons)
    return _result(
        valuation_cls, value=value, monthly_income=None, market_rent=None, noi=None,
        method="house_avm_x_observed_index", confidence=confidence, notes=notes,
        valuation_date=valuation_date, status=_status(factor), payload=build.payload,
        model=model, factor=factor,
    )


def _annual_noi(detail, monthly_rent: float) -> float:
    vacancy = min(max(float(getattr(detail, "vacancy_rate", 0) or 0), 0.0), 1.0)
    annual_effective_rent = monthly_rent * 12.0 * (1.0 - vacancy)
    expenses = (
        float(getattr(detail, "monthly_maintenance", 0) or 0) * 12.0
        + float(getattr(detail, "monthly_management_fees", 0) or 0) * 12.0
        + float(getattr(detail, "annual_rates_taxes", 0) or 0)
        + float(getattr(detail, "annual_insurance", 0) or 0)
        + float(getattr(detail, "annual_other_expenses", 0) or 0)
    )
    return max(annual_effective_rent - expenses, 0.0)


def value_rental(valuation_cls, prop, db, valuation_date: date):
    detail = getattr(prop, "rental", None)
    if detail is None:
        return _unavailable(valuation_cls, prop, PayloadBuild(None, ["rental_details"]), valuation_date, "rental")

    rent_build = build_rental_payload(prop)
    stored_rent = float(getattr(detail, "monthly_rent", 0) or 0)
    predicted_rent = None
    rent_prediction = None
    if rent_build.payload is not None:
        try:
            rent_prediction = _predict("rental", rent_build.payload, db)
            predicted_rent = float(rent_prediction["predicted_value"])
        except Exception:
            predicted_rent = None
    market_rent = stored_rent or predicted_rent
    if not market_rent:
        return _unavailable(valuation_cls, prop, PayloadBuild(None, ["monthly_rent", "rental_model_payload"]), valuation_date, "rental")

    noi = _annual_noi(detail, market_rent)
    cap_rate = DEFAULT_CAP_RATE if DEFAULT_CAP_RATE > 0 else 0.0926
    income_value = noi / cap_rate if noi > 0 else 0.0

    market_value = None
    house_factor = None
    house_build = build_rental_underlying_house_payload(prop)
    if house_build.payload is not None:
        try:
            house_prediction = _predict("house", house_build.payload, db)
            house_factor = _observed_factor("house", prop, None, valuation_date)
            market_value = float(house_prediction["predicted_value"]) * house_factor.value
        except Exception:
            market_value = None

    notes = list(rent_build.notes)
    if market_value and income_value:
        value = market_value * 0.60 + income_value * 0.40
        method = "rental_market_income_reconciled"
        confidence = "medium" if house_factor and house_factor.is_usable else "low"
        low = min(market_value, income_value) * 0.85
        high = max(market_value, income_value) * 1.15
        notes.append("Reconciled 60% underlying sale AVM and 40% NOI income approach.")
    else:
        value = income_value
        method = "rental_noi_capitalised"
        confidence = "low"
        low, high = _interval(value, confidence)
        notes.append("Underlying sale AVM unavailable; capital value uses NOI income approach only.")
    notes.append(f"NOI capitalised at {cap_rate:.2%}; gross monthly rent is not treated as capital value.")

    factor = house_factor
    model = model_manifest("house" if market_value else "rental")
    payload = {
        "rental": rent_build.payload or {},
        "underlying_house": house_build.payload or {},
        "cap_rate": cap_rate,
    }
    return _result(
        valuation_cls, value=value, monthly_income=stored_rent or market_rent,
        market_rent=predicted_rent or market_rent, noi=noi, method=method,
        confidence=confidence, notes=notes, valuation_date=valuation_date,
        status=_status(factor) if factor else "income_approach", payload=payload,
        model=model, factor=factor, interval=(low, high),
        extra_provenance={
            "income_approach": {"annual_noi": noi, "cap_rate": cap_rate, "value": income_value},
            "market_approach": {"value": market_value},
            "rent_model": rent_prediction,
        },
    )


def value_property_v2(valuation_cls, prop, db=None, valuation_date: date | None = None):
    valuation_date = valuation_date or date.today()
    kind = str(getattr(prop, "property_type", "") or "").strip().lower()
    if kind == "land":
        return value_land(valuation_cls, prop, db, valuation_date)
    if kind in {"house", "housing"}:
        return value_house(valuation_cls, prop, db, valuation_date)
    if kind == "rental":
        return value_rental(valuation_cls, prop, db, valuation_date)
    return _unavailable(valuation_cls, prop, PayloadBuild(None, ["property_type"]), valuation_date, "house")
