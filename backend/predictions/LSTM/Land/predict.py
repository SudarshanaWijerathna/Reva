"""
Land market-index forecasts.

Thin wrapper over ``backend.predictions.LSTM.index_model``. The shared module
owns loading, scaling, the scaler-domain guard and the recursive forecast; this
file exists so the import paths used by ``LSTM/routes.py`` and
``core/cache_service.py`` keep working.

One step is one month. The series and its time base are declared in
``manifest.json`` alongside this file.
"""

from __future__ import annotations

from backend.predictions.LSTM import index_model

SERIES = "land"


# -- Raw numeric accessors (preferred) --------------------------------------

def predict_next_close_raw(csv_path=None) -> float:
    """Next month's index value as a float."""
    return index_model.predict_next_value(SERIES, csv_path=csv_path)


def predict_future_sequence_raw(csv_path=None, steps: int = 5) -> list[float]:
    """The next ``steps`` monthly index values as floats."""
    return index_model.predict_future_values(SERIES, steps=steps, csv_path=csv_path)


def latest_index_value(csv_path=None) -> float:
    """Most recent published index value."""
    return index_model.latest_index_value(SERIES, csv_path=csv_path)


def staleness_months() -> int:
    """Whole months between the last published value and today."""
    return index_model.index_staleness_months(SERIES)


# -- Legacy string accessors -------------------------------------------------
# Kept so existing route and cache response shapes are unchanged. ``model_path``
# and ``scaler_path`` are accepted and ignored: artifacts are now resolved from
# the series manifest, which is what stopped one series loading another's model.

def predict_next_close_price_from_saved(csv_path=None, model_path=None, scaler_path=None) -> str:
    return index_model.format_value(predict_next_close_raw(csv_path=csv_path))


def predict_future_sequence_from_saved(csv_path=None, model_path=None, scaler_path=None, steps: int = 10) -> list[str]:
    return [
        index_model.format_value(value)
        for value in predict_future_sequence_raw(csv_path=csv_path, steps=steps)
    ]
