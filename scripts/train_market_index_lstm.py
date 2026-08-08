"""
Train the market-index LSTMs on the real CBSL Asking Price Index.

Replaces the previous artifacts, which were trained on a 1000-point synthetic
series with no date column, no declared time step, and - for housing - a scaler
fitted on the land series.

What changed and why it constrains the architecture:

  The real index is monthly and 63 observations long. The previous network was
  two LSTM(64) layers with a 60-step lookback: 49,985 trainable parameters, and
  a lookback that cannot even form four windows from 63 points. This script uses
  a 12-month lookback and a single LSTM(8), roughly 330 parameters, with early
  stopping. That is still generous for ~50 training windows, which is exactly why
  every run is scored against naive and drift baselines and the comparison is
  written into the training report. A model that loses to naive should be
  reported as losing to naive, not shipped quietly.

Scoring is an expanding-window walk-forward backtest. The scaler is refitted
inside every fold on training data only, so no test-period information reaches
the transform. The shipped artifact is then refit on the full series.

Usage, from the repository root:

    python scripts/train_market_index_lstm.py
    python scripts/train_market_index_lstm.py --series lands --epochs 400
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
LSTM_ROOT = REPO_ROOT / "backend" / "predictions" / "LSTM"
INDEX_CSV = LSTM_ROOT / "datasets" / "cbsl_market_index.csv"

# Which CBSL column each served series is built from. 'rental' has no CBSL
# equivalent - the reports cover lands, houses and condominiums only - so it is
# served as a declared proxy onto the houses index rather than given a model
# trained on data that does not exist.
SERIES_CONFIG = {
    "lands": {"folder": "Land", "column": "lands"},
    "houses": {"folder": "Housing", "column": "houses"},
}
PROXY_SERIES = {"rental": {"proxy_for": "houses", "reason": "CBSL publishes no rental index"}}

LOOKBACK = 12          # months of history the model sees
LSTM_UNITS = 8
MIN_TRAIN = 42         # months before the first backtest fold
HORIZONS = (1, 3, 6)   # months ahead to score

# Headroom so live values above the historical maximum still scale near [0, 1]
# instead of pinning at the ceiling, which is what the old rental scaler did.
FEATURE_RANGE = (0.1, 0.9)

RANDOM_SEED = 42


def _set_seeds() -> None:
    import random

    import tensorflow as tf

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    tf.random.set_seed(RANDOM_SEED)


def _windows(scaled: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    features, targets = [], []
    for start in range(len(scaled) - lookback):
        features.append(scaled[start : start + lookback])
        targets.append(scaled[start + lookback])
    if not features:
        raise ValueError(f"Series too short for a {lookback}-step lookback.")
    return np.array(features).reshape(-1, lookback, 1), np.array(targets).reshape(-1, 1)


def _build_model(lookback: int):
    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential(
        [
            layers.Input(shape=(lookback, 1)),
            layers.LSTM(LSTM_UNITS),
            layers.Dense(1),
        ]
    )
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=5e-3), loss="mse")
    return model


def _fit(values: np.ndarray, epochs: int, verbose: int = 0):
    """Fit a scaler and model on one training slice. Returns (model, scaler)."""
    from tensorflow import keras

    scaler = MinMaxScaler(feature_range=FEATURE_RANGE)
    scaled = scaler.fit_transform(values.reshape(-1, 1))
    features, targets = _windows(scaled, LOOKBACK)

    model = _build_model(LOOKBACK)
    model.fit(
        features,
        targets,
        epochs=epochs,
        batch_size=8,
        verbose=verbose,
        shuffle=False,
        callbacks=[keras.callbacks.EarlyStopping(monitor="loss", patience=25, restore_best_weights=True)],
    )
    return model, scaler


def _forecast(model, scaler, history: np.ndarray, steps: int) -> list[float]:
    """Recursive multi-step forecast in original units."""
    window = scaler.transform(history[-LOOKBACK:].reshape(-1, 1))
    predictions = []
    for _ in range(steps):
        next_scaled = np.asarray(
            model(window.reshape(1, LOOKBACK, 1).astype("float32"), training=False)
        )
        predictions.append(float(next_scaled[0][0]))
        window = np.vstack((window[1:], next_scaled.reshape(1, 1)))
    return [float(v) for v in scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).ravel()]


def backtest(values: np.ndarray, epochs: int) -> dict:
    """Expanding-window walk-forward comparison of the LSTM against baselines."""
    errors = {h: {"lstm": [], "naive": [], "drift": []} for h in HORIZONS}

    for split in range(MIN_TRAIN, len(values)):
        train = values[:split]
        model, scaler = _fit(train, epochs=epochs)
        longest = max(HORIZONS)
        path = _forecast(model, scaler, train, longest)
        slope = (train[-1] - train[0]) / (len(train) - 1)

        for horizon in HORIZONS:
            index = split + horizon - 1
            if index >= len(values):
                continue
            truth = values[index]
            errors[horizon]["lstm"].append(abs(path[horizon - 1] - truth) / truth)
            errors[horizon]["naive"].append(abs(train[-1] - truth) / truth)
            errors[horizon]["drift"].append(abs(train[-1] + slope * horizon - truth) / truth)

        del model

    summary = {}
    for horizon, methods in errors.items():
        scores = {
            name: (round(100 * float(np.mean(values_)), 4) if values_ else None)
            for name, values_ in methods.items()
        }
        ranked = {name: score for name, score in scores.items() if score is not None}
        summary[f"h{horizon}m"] = {
            "folds": len(methods["lstm"]),
            "mape_pct": scores,
            "best": min(ranked, key=ranked.get) if ranked else None,
            "lstm_beats_naive": (
                bool(scores["lstm"] < scores["naive"])
                if scores["lstm"] is not None and scores["naive"] is not None
                else None
            ),
        }
    return summary


def train_series(name: str, frame: pd.DataFrame, epochs: int, skip_backtest: bool) -> dict:
    config = SERIES_CONFIG[name]
    # Each series has its own start month (CBSL began publishing the houses
    # index in 2019-10), so drop leading gaps rather than imputing them.
    column = frame[["month", config["column"]]].dropna().reset_index(drop=True)
    frame = column.rename(columns={config["column"]: config["column"]})
    values = column[config["column"]].to_numpy(dtype=float)
    target_dir = LSTM_ROOT / config["folder"]
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {name} -> {config['folder']}/  ({len(values)} monthly observations) ===")

    report = {} if skip_backtest else backtest(values, epochs)
    if report:
        for horizon, scores in report.items():
            marks = scores["mape_pct"]
            print(
                f"  {horizon}: lstm={marks['lstm']}%  naive={marks['naive']}%  "
                f"drift={marks['drift']}%  -> best={scores['best']}"
            )

    _set_seeds()
    model, scaler = _fit(values, epochs=epochs, verbose=0)

    model.save(target_dir / "my_model.keras")
    joblib.dump(scaler, target_dir / "scaler.joblib")

    check = scaler.transform(values[-LOOKBACK:].reshape(-1, 1))
    monthly_change = values[1:] / values[:-1] - 1.0
    manifest = {
        "series": name,
        "source": "Central Bank of Sri Lanka, Real Estate Market Analysis (quarterly)",
        "base_period": "2019=100",
        "coverage": "Colombo district",
        "units": "index",
        "step_unit": "month",
        "step_days": 30.44,
        "time_steps": LOOKBACK,
        "series_start": str(frame["month"].iloc[0]),
        "series_end": str(frame["month"].iloc[-1]),
        "observations": int(len(values)),
        "architecture": f"LSTM({LSTM_UNITS}) -> Dense(1)",
        "trainable_parameters": int(model.count_params()),
        "scaler": {
            "type": "MinMaxScaler",
            "feature_range": list(FEATURE_RANGE),
            "data_min": float(scaler.data_min_[0]),
            "data_max": float(scaler.data_max_[0]),
        },
        "live_window_scaled_range": [round(float(check.min()), 6), round(float(check.max()), 6)],
        # Realised volatility of the series, so the runtime can reject a forecast
        # that implies a move this series has never made. A recursive LSTM on a
        # short series tends to snap toward its training mean, which shows up as
        # a large first-step move rather than as an obviously broken number.
        "monthly_change_mean": round(float(np.mean(monthly_change)), 6),
        "monthly_change_sd": round(float(np.std(monthly_change)), 6),
        "max_plausible_monthly_move": round(float(3.0 * np.std(monthly_change)), 6),
        "backtest": report,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    with (target_dir / "manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    print(f"  params={manifest['trainable_parameters']}  "
          f"live window scales to {manifest['live_window_scaled_range']}")
    return manifest


def write_proxy_manifests(frame: pd.DataFrame, trained: dict) -> None:
    for name, config in PROXY_SERIES.items():
        folder = {"rental": "Rental"}[name]
        target_dir = LSTM_ROOT / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        source = trained[config["proxy_for"]]
        manifest = {
            "series": name,
            "is_proxy": True,
            "proxy_for": config["proxy_for"],
            "proxy_reason": config["reason"],
            "source": source["source"],
            "base_period": source["base_period"],
            "coverage": source["coverage"],
            "units": "index",
            "step_unit": "month",
            "step_days": 30.44,
            "time_steps": LOOKBACK,
            "series_start": source["series_start"],
            "series_end": source["series_end"],
            "trained_at": source["trained_at"],
        }
        with (target_dir / "manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")
        for stale in ("my_model.keras", "scaler.joblib"):
            path = target_dir / stale
            if path.exists():
                path.unlink()
        print(f"\n=== {name} -> {folder}/  declared proxy for '{config['proxy_for']}' "
              f"({config['reason']}); stale artifacts removed ===")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", nargs="*", default=sorted(SERIES_CONFIG))
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--skip-backtest", action="store_true")
    parser.add_argument("--input", type=Path, default=INDEX_CSV)
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    frame = frame.sort_values("month").reset_index(drop=True)
    print(f"Loaded {len(frame)} months: {frame['month'].iloc[0]} -> {frame['month'].iloc[-1]}")

    _set_seeds()
    trained = {}
    for name in args.series:
        trained[name] = train_series(name, frame, args.epochs, args.skip_backtest)

    if set(SERIES_CONFIG).issubset(trained):
        write_proxy_manifests(frame, trained)

    report_path = REPO_ROOT / "ml" / "market_index_training_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(trained, handle, indent=2)
        handle.write("\n")
    print(f"\nWrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
