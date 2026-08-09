"""
Shared runtime for the market-index LSTMs.

The three per-series ``predict.py`` modules were near-identical copies, which is
how the housing folder ended up holding the land model and the land scaler
without anything noticing. The loading, scaling and forecasting logic lives here
once; the per-series modules are thin wrappers that keep their existing public
names so ``LSTM/routes.py`` and ``core/cache_service.py`` are unaffected.

Three things this module enforces that the previous code did not:

1. **Scaler domain is checked and violated inputs raise.** Feeding a series
   through a scaler fitted on a different series produces a confident number
   from meaningless inputs. That is worse than an error, so it is now an error.

2. **The time base is declared.** Each series ships a ``manifest.json`` stating
   that a step is one month, where the data came from, and when it ends. Callers
   asking for "3 months ahead" get 3 months ahead, rather than 3 steps of an
   undeclared size.

3. **Staleness is reported, not extrapolated across.** The published index lags
   real time by a quarter or more. ``index_staleness_months`` exposes that gap so
   callers can degrade instead of forecasting across it silently.
"""

from __future__ import annotations

import json
import os
from datetime import date
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

LSTM_ROOT = Path(__file__).resolve().parent
DATASET_PATH = LSTM_ROOT / "datasets" / "cbsl_market_index.csv"

# Served series -> folder holding its artifacts, and the CSV column it reads.
SERIES = {
    "housing": {"folder": "Housing", "column": "houses"},
    "land": {"folder": "Land", "column": "lands"},
    "rental": {"folder": "Rental", "column": "houses"},
}

# How far past [0, 1] a scaled input may drift before it is treated as evidence
# that the wrong scaler is loaded.
SCALER_DOMAIN_TOLERANCE = float(os.getenv("SCALER_DOMAIN_TOLERANCE", "0.25"))


class ScalerDomainError(RuntimeError):
    """Raised when model inputs fall outside the scaler's training domain."""


class IndexArtifactError(RuntimeError):
    """Raised when a series' artifacts are missing or inconsistent."""


# --------------------------------------------------------------------------
# Manifests
# --------------------------------------------------------------------------

@lru_cache(maxsize=8)
def load_manifest(series: str) -> dict[str, Any]:
    config = SERIES.get(series)
    if config is None:
        raise IndexArtifactError(f"Unknown index series: {series}")

    path = LSTM_ROOT / config["folder"] / "manifest.json"
    if not path.exists():
        raise IndexArtifactError(
            f"No manifest for '{series}' at {path}. Run scripts/train_market_index_lstm.py."
        )
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_series(series: str) -> str:
    """Follow a declared proxy to the series that actually owns the artifacts."""
    manifest = load_manifest(series)
    if manifest.get("is_proxy"):
        target = manifest["proxy_for"]
        # Manifests name CBSL series ('houses'); map back to a served series.
        for name, config in SERIES.items():
            if config["column"] == target and not load_manifest(name).get("is_proxy"):
                return name
        raise IndexArtifactError(f"'{series}' proxies '{target}', which has no trained model.")
    return series


def time_steps_for(series: str) -> int:
    return int(load_manifest(series)["time_steps"])


def index_staleness_months(series: str, today: date | None = None) -> int:
    """Whole months between the last published index value and today."""
    manifest = load_manifest(series)
    end = manifest.get("series_end")
    if not end:
        return 0
    reference = today or date.today()
    year, month = (int(part) for part in str(end).split("-")[:2])
    return (reference.year - year) * 12 + (reference.month - month)


# --------------------------------------------------------------------------
# Data and artifacts
# --------------------------------------------------------------------------

def load_index_series(series: str, csv_path: str | Path | None = None) -> np.ndarray:
    """Return the monthly index values for a series, oldest first."""
    column = SERIES[series]["column"]
    frame = pd.read_csv(Path(csv_path) if csv_path else DATASET_PATH)
    if column not in frame.columns:
        raise IndexArtifactError(f"Column '{column}' missing from {csv_path or DATASET_PATH}")
    values = frame[["month", column]].dropna()[column].to_numpy(dtype=float)
    if values.size == 0:
        raise IndexArtifactError(f"No observations for '{series}'.")
    return values


def _load_keras_model(path: Path):
    try:
        keras_models = import_module("tensorflow.keras.models")
    except ModuleNotFoundError:
        keras_models = import_module("keras.models")
    return keras_models.load_model(path)


@lru_cache(maxsize=8)
def load_model_and_scaler(series: str):
    owner = resolve_series(series)
    folder = LSTM_ROOT / SERIES[owner]["folder"]
    model_path, scaler_path = folder / "my_model.keras", folder / "scaler.joblib"

    for path in (model_path, scaler_path):
        if not path.exists():
            raise IndexArtifactError(
                f"Missing artifact {path} for '{series}'. Run scripts/train_market_index_lstm.py."
            )
    return _load_keras_model(model_path), joblib.load(scaler_path)


# --------------------------------------------------------------------------
# Forecasting
# --------------------------------------------------------------------------

def _check_domain(series: str, scaled: np.ndarray) -> None:
    """
    Log the domain check through the shared telemetry, then enforce it.

    Phase 0 shipped this as a warning so that enabling it could not change
    behaviour. Now that each series has its own scaler, a violation means the
    wrong artifact is loaded, and returning a confident number from meaningless
    inputs is worse than failing.
    """
    from backend.predictions.diagnostics import check_scaler_domain

    result = check_scaler_domain(series, scaled, tolerance=SCALER_DOMAIN_TOLERANCE)
    if result["in_domain"] is False:
        raise ScalerDomainError(
            f"Scaler domain violation for '{series}': inputs scale to "
            f"[{result['min']:.4f}, {result['max']:.4f}], expected roughly [0, 1]. The loaded "
            "scaler was almost certainly fitted on a different series; refusing to return a forecast."
        )


def _scaled_window(series: str, values: np.ndarray, scaler, lookback: int) -> np.ndarray:
    if len(values) < lookback:
        raise IndexArtifactError(
            f"'{series}' needs at least {lookback} observations, found {len(values)}."
        )
    scaled = scaler.transform(values[-lookback:].reshape(-1, 1))
    _check_domain(series, scaled)
    return scaled


def predict_next_value(series: str, csv_path: str | Path | None = None) -> float:
    """One-step-ahead index value, in index units."""
    owner = resolve_series(series)
    model, scaler = load_model_and_scaler(series)
    lookback = time_steps_for(owner)
    values = load_index_series(series, csv_path)
    window = _scaled_window(series, values, scaler, lookback)

    predicted = np.asarray(model(window.reshape(1, lookback, 1).astype("float32"), training=False))
    return float(scaler.inverse_transform(predicted.reshape(-1, 1))[0][0])


def predict_future_values(series: str, steps: int = 5, csv_path: str | Path | None = None) -> list[float]:
    """Recursive multi-step forecast, one month per step, in index units."""
    if steps < 1:
        raise ValueError("steps must be a positive integer")

    owner = resolve_series(series)
    model, scaler = load_model_and_scaler(series)
    lookback = time_steps_for(owner)
    values = load_index_series(series, csv_path)
    window = _scaled_window(series, values, scaler, lookback)

    scaled_predictions = []
    for _ in range(steps):
        predicted = np.asarray(
            model(window.reshape(1, lookback, 1).astype("float32"), training=False)
        )
        scaled_predictions.append(float(predicted[0][0]))
        window = np.vstack((window[1:], predicted.reshape(1, 1)))

    restored = scaler.inverse_transform(np.array(scaled_predictions).reshape(-1, 1))
    return [float(value) for value in restored.ravel()]


def latest_index_value(series: str, csv_path: str | Path | None = None) -> float:
    """Most recent published index value - the denominator for growth ratios."""
    return float(load_index_series(series, csv_path)[-1])


def format_value(value: float, decimals: int = 2) -> str:
    """Legacy display format, kept so existing response shapes are unchanged."""
    return f"{float(value):,.{decimals}f}"
