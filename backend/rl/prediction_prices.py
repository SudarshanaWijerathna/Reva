"""Price-based state features for the RL agent.

The agent expects three monthly signals, defined by the generator that produced
its training data (``backend/rl/agent.md``):

    land_trend      realised month-over-month change in land prices, clipped to
                    [-0.10, 0.15]
    rental_yield    monthly rent divided by house price, around 0.006
    housing_signal  three-month forward change in house prices, clipped to
                    [-0.15, 0.20]

**What was wrong.** ``land_trend`` and ``housing_signal`` were computed by
dividing an LSTM index value by a scraped LKR price. Those are different
quantities - index points and rupees - so the ratio had no meaning. In practice
it produced -0.547 and -0.939 on every call, both of which clipped to their
floors. Measured against the DQN's own ``reva_scaler.pkl``, the agent was being
queried at **-7.5 and -4.2 standard deviations** from its training distribution,
with two of its three price features frozen at a constant.

``land_trend`` was also computed forward, as ``(forecast - current) / current``,
while the training generator defined it backward as a realised month-over-month
change. The module docstring described a third thing again. All three now agree.

**What replaced it.** Both signals are ratios within a single index series, so
the units cancel and what survives is a real growth rate. ``rental_yield`` keeps
using the scraper, which is correct as it stands: rent and price both come from
the same source in the same currency, and the resulting yield already sits inside
the trained distribution.

Clipping is deliberately retained. The bounds match ``agent.md`` exactly and are
defence in depth; what changed is that values now land inside them rather than on
them. Every signal is reported before and after clipping, and a value that hits a
bound raises a warning - that single line of telemetry would have surfaced this
years earlier.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from backend.core.cache_service import get_current_prices
from backend.predictions.diagnostics import report_signal

logger = logging.getLogger(__name__)

# Global, runtime-editable feature boundaries. These match the ranges the
# training generator clipped to; see agent.md.
LAND_TREND_BOUNDS: Tuple[float, float] = (-0.10, 0.15)
RENTAL_YIELD_BOUNDS: Tuple[float, float] = (0.002, 0.012)
HOUSING_SIGNAL_BOUNDS: Tuple[float, float] = (-0.15, 0.20)

# Horizon of the forward house-price signal, in months, per the training generator.
HOUSING_SIGNAL_HORIZON_MONTHS = 3


def set_feature_boundaries(
    *,
    land_trend: Tuple[float, float] | None = None,
    rental_yield: Tuple[float, float] | None = None,
    housing_signal: Tuple[float, float] | None = None,
) -> None:
    """Update global clipping boundaries for generated features."""
    global LAND_TREND_BOUNDS, RENTAL_YIELD_BOUNDS, HOUSING_SIGNAL_BOUNDS

    if land_trend is not None:
        LAND_TREND_BOUNDS = _validate_bounds(land_trend, "land_trend")
    if rental_yield is not None:
        RENTAL_YIELD_BOUNDS = _validate_bounds(rental_yield, "rental_yield")
    if housing_signal is not None:
        HOUSING_SIGNAL_BOUNDS = _validate_bounds(housing_signal, "housing_signal")


def get_feature_boundaries() -> Dict[str, Tuple[float, float]]:
    """Return current global clipping boundaries for all features."""
    return {
        "land_trend": LAND_TREND_BOUNDS,
        "rental_yield": RENTAL_YIELD_BOUNDS,
        "housing_signal": HOUSING_SIGNAL_BOUNDS,
    }


# --------------------------------------------------------------------------
# Raw signal inputs
# --------------------------------------------------------------------------

def _land_trend_raw() -> tuple[float, str]:
    """Realised month-over-month change in the land index."""
    from backend.predictions import market_index

    try:
        ratio = market_index.trend_ratio("land", from_offset=-1, to_offset=0)
    except Exception as exc:
        logger.warning("Land index unavailable for land_trend: %s", exc)
        return 0.0, "unavailable"

    if ratio is None:
        return 0.0, "unavailable"
    return float(ratio), "index_realised_mom"


def _housing_signal_raw() -> tuple[float, str]:
    """
    Forward three-month change in the house index.

    The training generator used a genuinely forward change. The published index
    ends a quarter or more behind real time and, per the walk-forward backtest in
    ``ml/market_index_training_report.json``, the LSTM loses to a naive forecast
    at every horizon. So the forward forecast is used only when it survives the
    plausibility guards; otherwise the realised three-month change stands in as a
    momentum estimate. Which one was used is reported rather than hidden.
    """
    from backend.predictions import market_index

    forecast = _forward_index_change(HOUSING_SIGNAL_HORIZON_MONTHS)
    if forecast is not None:
        return forecast, "index_forecast_3m"

    try:
        ratio = market_index.trend_ratio(
            "house", from_offset=-HOUSING_SIGNAL_HORIZON_MONTHS, to_offset=0
        )
    except Exception as exc:
        logger.warning("House index unavailable for housing_signal: %s", exc)
        return 0.0, "unavailable"

    if ratio is None:
        return 0.0, "unavailable"
    return float(ratio), "index_realised_3m_momentum"


def _forward_index_change(horizon_months: int) -> float | None:
    """
    Forward change implied by the cached LSTM forecast, or None if unusable.

    Reuses the guards already applied in the prediction path - staleness, the
    per-series volatility band, and the plausibility clamp - so the agent and the
    valuation endpoint never disagree about whether a forecast is trustworthy.
    """
    try:
        from backend.dynamic.services import _lstm_growth_factors

        factors = _lstm_growth_factors("house", steps=horizon_months)
    except Exception as exc:
        logger.debug("Forward index change unavailable: %s", exc)
        return None

    if not factors or len(factors) < horizon_months:
        return None
    return float(factors[horizon_months - 1]) - 1.0


def _rental_yield_raw() -> tuple[float, str]:
    """
    Monthly rent over house price, both from the scraper.

    Dimensionally sound as it stands: the two figures come from the same source
    in the same currency, so the ratio is a real yield.
    """
    try:
        current_prices = get_current_prices() or {}
    except Exception as exc:
        logger.warning("Current prices unavailable for rental_yield: %s", exc)
        return 0.0, "unavailable"

    rent = _to_float(current_prices.get("rentals", {}).get("national average", 0.0))
    price = _to_float(current_prices.get("sales", {}).get("national average", 0.0))

    if price <= 0 or rent <= 0:
        return 0.0, "unavailable"
    return rent / price, "scraper_national_average"


def get_price_inputs() -> Dict[str, Any]:
    """Raw signal values plus the provenance of each, before clipping."""
    land_trend, land_source = _land_trend_raw()
    housing_signal, housing_source = _housing_signal_raw()
    rental_yield, rental_source = _rental_yield_raw()

    return {
        "land_trend": land_trend,
        "rental_yield": rental_yield,
        "housing_signal": housing_signal,
        "sources": {
            "land_trend": land_source,
            "rental_yield": rental_source,
            "housing_signal": housing_source,
        },
    }


# --------------------------------------------------------------------------
# Clipped signals
# --------------------------------------------------------------------------

def generate_state_price_signals(inputs: Dict[str, Any] | None = None, *, test: bool = False) -> Dict[str, float]:
    """
    Generate the three clipped monthly price features for the RL state.

    Definitions, matching the training generator in agent.md:
        land_trend     = index_land(t) / index_land(t-1) - 1
        rental_yield   = monthly_rent / house_price
        housing_signal = index_house(t+3) / index_house(t) - 1

    Returns:
        dict: {"land_trend", "rental_yield", "housing_signal"}
    """
    raw = inputs if inputs is not None else get_price_inputs()

    signals = {
        "land_trend": _clip(raw.get("land_trend", 0.0), LAND_TREND_BOUNDS),
        "rental_yield": _clip(raw.get("rental_yield", 0.0), RENTAL_YIELD_BOUNDS),
        "housing_signal": _clip(raw.get("housing_signal", 0.0), HOUSING_SIGNAL_BOUNDS),
    }

    # Observation only - report_signal never alters a value. A signal clipped on
    # every call is a constant, and the agent cannot learn from a constant.
    if not test:
        for name, bounds in (
            ("land_trend", LAND_TREND_BOUNDS),
            ("rental_yield", RENTAL_YIELD_BOUNDS),
            ("housing_signal", HOUSING_SIGNAL_BOUNDS),
        ):
            report_signal(name, float(raw.get(name, 0.0)), signals[name], bounds)

    return signals


def _clip(value: float, bounds: Tuple[float, float]) -> float:
    lower, upper = bounds
    return max(lower, min(upper, float(value)))


def _validate_bounds(bounds: Tuple[float, float], name: str) -> Tuple[float, float]:
    if len(bounds) != 2:
        raise ValueError(f"{name} bounds must be a (min, max) pair")
    lower, upper = float(bounds[0]), float(bounds[1])
    if lower > upper:
        raise ValueError(f"{name} bounds must satisfy min <= max")
    return lower, upper


def _to_float(value: object, default: float = 0.0) -> float:
    """Convert cache/model values like '1,234.56' to float safely."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").strip())
        except ValueError:
            return default
    return default


def get_data() -> Dict[str, Any]:
    """
    Deprecated. Use :func:`get_price_inputs`.

    The previous version returned a six-tuple of prices mixing index points with
    scraped rupees, which is what made the ratios meaningless. Nothing downstream
    needs those absolute levels any more.
    """
    logger.debug("get_data() is deprecated; use get_price_inputs().")
    return get_price_inputs()
