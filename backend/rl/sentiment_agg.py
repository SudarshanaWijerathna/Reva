import logging
import math
from typing import Dict, List

from backend.core.cache_service import get_cached_sentiment, get_sentiment_history

logger = logging.getLogger(__name__)

PROPERTIES = ("land", "housing", "rental")

CURRENT_MIN = -1.0
CURRENT_MAX = 1.0
TREND_MIN = -0.05
TREND_MAX = 0.05
VOLATILITY_MIN = 0.0
VOLATILITY_MAX = 0.5


def _safe_float(value, default: float = 0.0) -> float:
  try:
    if value is None:
      return default
    return float(value)
  except (TypeError, ValueError):
    return default


def _clip(value: float, low: float, high: float) -> float:
  if value < low:
    return low
  if value > high:
    return high
  return value


def _mean(values: List[float]) -> float:
  if not values:
    return 0.0
  return sum(values) / len(values)


def _std(values: List[float]) -> float:
  if not values:
    return 0.0
  m = _mean(values)
  variance = sum((v - m) ** 2 for v in values) / len(values)
  return math.sqrt(variance)


def _slope(values: List[float]) -> float:
  """Return slope of linear regression y = a + b*x for x=[0..n-1]."""
  n = len(values)
  if n < 2:
    return 0.0

  x_mean = (n - 1) / 2.0
  y_mean = _mean(values)

  numerator = 0.0
  denominator = 0.0
  for i, y in enumerate(values):
    dx = i - x_mean
    numerator += dx * (y - y_mean)
    denominator += dx * dx

  if denominator == 0.0:
    return 0.0
  return numerator / denominator


def _extract_value(snapshot: dict, property_name: str, horizon: str) -> float:
  try:
    return _safe_float(snapshot[property_name][horizon]["value"], default=0.0)
  except (TypeError, KeyError):
    return 0.0


def _get_history_series(property_name: str, history: List[dict], window: int) -> List[float]:
  series = []
  for item in history[:window]:
    if not isinstance(item, dict):
      continue
    data = item.get("data", {})
    if not isinstance(data, dict):
      continue
    series.append(_extract_value(data, property_name, "short_term"))

  # Redis list is newest-first; reverse for chronological order for slope.
  series.reverse()
  return series


def aggregate_sentiment_features(
  window: int = 30,
  short_window: int = 7,
  shock_threshold: float = 2.0,
  debug: bool = False,
) -> Dict[str, Dict[str, float]]:
  """
  Build sentiment features per property for RL state input.

  Output keys per property:
  - sentiment_current in [-1, 1]
  - sentiment_trend in [-0.05, 0.05]
  - sentiment_volatility in [0, 0.5]
  - sentiment_shock in {0, 1}

  Fallback rule:
  - If history has fewer than `window` days, use current snapshot horizons as
    pseudo-history:
      - current = medium_term
      - trend = long_term - short_term
      - volatility = std([short_term, medium_term, long_term])
      - shock = 0
  """
  try:
    current_snapshot = get_cached_sentiment() or {}
    history = get_sentiment_history() or []
    if debug:
      print("[sentiment_agg] get_cached_sentiment() fetched:")
      print(current_snapshot)
      print("[sentiment_agg] get_sentiment_history() fetched:")
      print(history)
      print(f"[sentiment_agg] history length: {len(history)}")
  except Exception as exc:
    logger.exception("Failed to fetch sentiment inputs: %s", exc)
    current_snapshot = {}
    history = []

  result: Dict[str, Dict[str, float]] = {}

  for prop in PROPERTIES:
    try:
      short_term_value = _extract_value(current_snapshot, prop, "short_term")
      medium_term_value = _extract_value(current_snapshot, prop, "medium_term")
      long_term_value = _extract_value(current_snapshot, prop, "long_term")
      series = _get_history_series(prop, history, window=window)

      if len(series) < window:
        sentiment_current = _clip(medium_term_value, CURRENT_MIN, CURRENT_MAX)
        pseudo_trend = long_term_value - short_term_value
        sentiment_trend = _clip(pseudo_trend, TREND_MIN, TREND_MAX)

        pseudo_volatility = _std([short_term_value, medium_term_value, long_term_value])
        sentiment_volatility = _clip(pseudo_volatility, VOLATILITY_MIN, VOLATILITY_MAX)
        sentiment_shock = 0
      else:
        recent = series[-short_window:] if len(series) >= short_window else series
        sentiment_current = _clip(_mean(recent), CURRENT_MIN, CURRENT_MAX)

        raw_trend = _slope(series)
        sentiment_trend = _clip(raw_trend, TREND_MIN, TREND_MAX)

        raw_volatility = _std(series)
        sentiment_volatility = _clip(raw_volatility, VOLATILITY_MIN, VOLATILITY_MAX)

        monthly_mean = _mean(series)
        monthly_std = _std(series)
        recent_mean = _mean(recent)

        if monthly_std == 0:
          sentiment_shock = 0
        else:
          z_score = abs(recent_mean - monthly_mean) / monthly_std
          sentiment_shock = 1 if z_score > shock_threshold else 0

      result[prop] = {
        "sentiment_current": float(sentiment_current),
        "sentiment_trend": float(sentiment_trend),
        "sentiment_volatility": float(sentiment_volatility),
        "sentiment_shock": int(sentiment_shock),
      }
    except Exception as exc:
      logger.exception("Sentiment feature aggregation failed for %s: %s", prop, exc)
      result[prop] = {
        "sentiment_current": 0.0,
        "sentiment_trend": 0.0,
        "sentiment_volatility": 0.0,
        "sentiment_shock": 0,
      }

  return result


def flatten_sentiment_features(features: Dict[str, Dict[str, float]]) -> List[float]:
  """Flatten in property order: [current, trend, volatility, shock] * properties."""
  flat: List[float] = []
  for prop in PROPERTIES:
    item = features.get(prop, {})
    flat.extend(
      [
        _clip(_safe_float(item.get("sentiment_current")), CURRENT_MIN, CURRENT_MAX),
        _clip(_safe_float(item.get("sentiment_trend")), TREND_MIN, TREND_MAX),
        _clip(
          _safe_float(item.get("sentiment_volatility")),
          VOLATILITY_MIN,
          VOLATILITY_MAX,
        ),
        1.0 if int(_safe_float(item.get("sentiment_shock"), default=0.0)) == 1 else 0.0,
      ]
    )
  return flat

if __name__ == "__main__":
  features = aggregate_sentiment_features(debug=True)
  print("Aggregated Sentiment Features:")
  print(features)

