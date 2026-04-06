"""Utilities for building RL agent price-based state features.

This module generates the three monthly signals expected by the RL agent:
	- land_trend
	- rental_yield
	- housing_signal

Each signal is clipped to configurable global boundaries so the ranges can be
adjusted without changing call sites.
"""

from __future__ import annotations

from typing import Dict, Tuple
from backend.core.cache_service import get_current_prices
#from backend.predictions.house_api import predict_house_price
#from backend.predictions.land_api import predict_land_price
#from backend.predictions.rental_api import predict_rental_price


# Global, runtime-editable feature boundaries.
# Update these values directly or via ``set_feature_boundaries``.
LAND_TREND_BOUNDS: Tuple[float, float] = (-0.10, 0.15)
RENTAL_YIELD_BOUNDS: Tuple[float, float] = (0.002, 0.012)
HOUSING_SIGNAL_BOUNDS: Tuple[float, float] = (-0.15, 0.20)


def set_feature_boundaries(
	*,
	land_trend: Tuple[float, float] | None = None,
	rental_yield: Tuple[float, float] | None = None,
	housing_signal: Tuple[float, float] | None = None,
) -> None:
	"""Update global clipping boundaries for generated features.

	Args:
		land_trend: New (min, max) bounds for land_trend.
		rental_yield: New (min, max) bounds for rental_yield.
		housing_signal: New (min, max) bounds for housing_signal.
	"""
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


def generate_state_price_signals(
	*,
	current_land_price: float,
	current_housing_price: float,
	future_land_price: float,
	monthly_rent: float,
	future_house_price_3m: float,
	test: bool = False,
	
) -> Dict[str, float]:
	"""Generate clipped monthly price-based features for RL agent state.

	Definitions:
		land_trend = (current_land_price - previous_land_price) / previous_land_price
		rental_yield = monthly_rent / current_housing_price
		housing_signal = (future_house_price_3m - current_housing_price) / current_housing_price

	Notes:
		- If a denominator is zero or negative, the corresponding raw feature is
		  treated as 0.0 for safety.
		- Returned values are clipped to global boundaries.

	Returns:
		dict: {"land_trend", "rental_yield", "housing_signal"}
	"""
	land_trend_raw = (
		(future_land_price - current_land_price) / current_land_price
		if current_land_price > 0
		else 0.0
	)
	rental_yield_raw = (monthly_rent / current_housing_price) if current_housing_price > 0 else 0.0
	housing_signal_raw = (
		(future_house_price_3m - current_housing_price) / current_housing_price
		if current_housing_price > 0
		else 0.0
	)

	return {
		"land_trend": _clip(land_trend_raw, LAND_TREND_BOUNDS),
		"rental_yield": _clip(rental_yield_raw, RENTAL_YIELD_BOUNDS),
		"housing_signal": _clip(housing_signal_raw, HOUSING_SIGNAL_BOUNDS),
	}


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


def get_data():

	#current_prices of preoperties from cache
	current_prices = get_current_prices()

	curr_land_price = _to_float(current_prices.get("lands", {}).get("national average", 0.0))
	curr_housing_price = _to_float(current_prices.get("sales", {}).get("national average", 0.0))
	current_rental_price = _to_float(current_prices.get("rentals", {}).get("national average", 0.0))

	# future predictions of properties from cache
	from backend.core.cache_service import get_future_predictions, update_future_prediction_cache
	get_future_predictions = get_future_predictions()

	future_land_price = _to_float(get_future_predictions.get("land", {}).get("next_close", "0"))
	housing_next_5 = get_future_predictions.get("housing", {}).get("next_5_close", ["0", "0", "0"])
	future_housing_price_3m = _to_float(housing_next_5[2] if len(housing_next_5) > 2 else "0")
	future_rental_price = _to_float(get_future_predictions.get("rental", {}).get("next_close", "0"))
	
    
	return curr_land_price, curr_housing_price, future_land_price, current_rental_price, future_housing_price_3m, future_rental_price


