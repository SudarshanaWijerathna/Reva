"""
Capture a baseline snapshot of the prediction stack.

Run this BEFORE and AFTER a change to the models or the composition layer, then
diff the two files. Contract tests catch broken shapes; this catches quiet value
drift - a district that silently starts returning a different number, a retrained
artifact that moves prices 3x.

Usage, from the repository root:

    python scripts/capture_prediction_baseline.py
    python scripts/capture_prediction_baseline.py --output tests/fixtures/baseline_after.json
    python scripts/capture_prediction_baseline.py --compare tests/fixtures/prediction_baseline.json

Runs offline: embedded models only, no database, no Redis, no HTTP. Land payloads
omit location_text so no geocoding request is made.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PAYLOAD_PATH = REPO_ROOT / "tests" / "fixtures" / "prediction_payloads.json"
DEFAULT_OUTPUT = REPO_ROOT / "tests" / "fixtures" / "prediction_baseline.json"

# Relative move that counts as drift when comparing two baselines.
DRIFT_THRESHOLD = 0.01


def _strip_id(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "id"}


def _predictors() -> Dict[str, Any]:
    from ml.house_service.service import predict_house_price
    from ml.land_service.service import predict_land_price
    from ml.rental_service.service import is_model_ready, predict_rental_price

    predictors = {"land": predict_land_price, "house": predict_house_price}
    if is_model_ready():
        predictors["rental"] = predict_rental_price
    else:
        print("WARNING: rental artifact missing; skipping rental baseline.", file=sys.stderr)
    return predictors


def _artifact_digests() -> Dict[str, str]:
    import hashlib

    artifacts = {
        "land_model": REPO_ROOT / "ml" / "land_service" / "model.joblib",
        "house_baseline": REPO_ROOT / "ml" / "house_service" / "catboost_house_price_baseline.cbm",
        "house_enhanced": REPO_ROOT / "ml" / "house_service" / "catboost_house_price_enhanced.cbm",
        "rental_model": REPO_ROOT / "ml" / "rental_service" / "catboost_rental_price.cbm",
        "lstm_housing_model": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Housing" / "my_model.keras",
        "lstm_housing_scaler": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Housing" / "scaler.joblib",
        "lstm_land_model": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Land" / "my_model.keras",
        "lstm_land_scaler": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Land" / "scaler.joblib",
        "lstm_rental_model": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Rental" / "my_model.keras",
        "lstm_rental_scaler": REPO_ROOT / "backend" / "predictions" / "LSTM" / "Rental" / "scaler.joblib",
    }
    digests = {}
    for name, path in artifacts.items():
        digests[name] = hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else "MISSING"
    return digests


def _lstm_scaler_domains() -> Dict[str, Any]:
    """Record where each LSTM's live window lands inside its scaler range."""
    import joblib
    import pandas as pd

    lstm_root = REPO_ROOT / "backend" / "predictions" / "LSTM"
    series = {"housing": ("Housing", "HousingDF.csv"), "land": ("Land", "LandDF.csv"), "rental": ("Rental", "RentalDF.csv")}

    domains: Dict[str, Any] = {}
    for name, (folder, csv_name) in series.items():
        try:
            scaler = joblib.load(lstm_root / folder / "scaler.joblib")
            frame = pd.read_csv(lstm_root / "datasets" / csv_name)
            scaled = scaler.transform(frame["close"].tail(60).to_numpy().reshape(-1, 1))
            domains[name] = {
                "scaled_min": round(float(scaled.min()), 6),
                "scaled_max": round(float(scaled.max()), 6),
                "in_domain": bool(scaled.min() >= -0.25 and scaled.max() <= 1.25),
            }
        except Exception as exc:
            domains[name] = {"error": str(exc)}
    return domains


def capture() -> Dict[str, Any]:
    with PAYLOAD_PATH.open("r", encoding="utf-8") as handle:
        payloads = json.load(handle)

    predictors = _predictors()
    results: Dict[str, Any] = {}

    for model_type, predict in predictors.items():
        groups = payloads.get(model_type, {})
        for group_name, group in groups.items():
            if not isinstance(group, list):
                continue
            for payload in group:
                payload_id = payload["id"]
                try:
                    response = predict(_strip_id(payload))
                    results[payload_id] = {
                        "model_type": model_type,
                        "group": group_name,
                        "status": "ok",
                        "predicted_value": round(float(response["predicted_value"]), 2),
                        "response": _jsonable(response),
                    }
                except Exception as exc:
                    results[payload_id] = {
                        "model_type": model_type,
                        "group": group_name,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "artifact_digests": _artifact_digests(),
        "lstm_scaler_domains": _lstm_scaler_domains(),
        "predictions": results,
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return str(value)


def compare(current: Dict[str, Any], baseline_path: Path) -> int:
    with baseline_path.open("r", encoding="utf-8") as handle:
        baseline = json.load(handle)

    old = baseline.get("predictions", {})
    new = current.get("predictions", {})
    drifted, appeared, disappeared, status_changed = [], [], [], []

    for payload_id, record in new.items():
        if payload_id not in old:
            appeared.append(payload_id)
            continue
        previous = old[payload_id]
        if previous.get("status") != record.get("status"):
            status_changed.append(
                f"{payload_id}: {previous.get('status')} -> {record.get('status')}"
            )
            continue
        if record.get("status") != "ok":
            continue
        before = float(previous["predicted_value"])
        after = float(record["predicted_value"])
        if before == 0:
            continue
        change = (after - before) / before
        if abs(change) > DRIFT_THRESHOLD:
            drifted.append(f"{payload_id}: {before:,.2f} -> {after:,.2f} ({change:+.2%})")

    disappeared = [payload_id for payload_id in old if payload_id not in new]

    print(f"\nCompared against {baseline_path}")
    for label, entries in (
        ("STATUS CHANGED", status_changed),
        ("VALUE DRIFT", drifted),
        ("NEW", appeared),
        ("REMOVED", disappeared),
    ):
        if entries:
            print(f"\n{label} ({len(entries)}):")
            for entry in entries:
                print(f"  {entry}")

    if not any([status_changed, drifted, appeared, disappeared]):
        print("No differences.")
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--compare", type=Path, default=None, help="Diff against an existing baseline instead of only writing one.")
    args = parser.parse_args()

    current = capture()

    ok = sum(1 for record in current["predictions"].values() if record["status"] == "ok")
    failed = len(current["predictions"]) - ok
    print(f"Captured {ok} prediction(s), {failed} error(s).")

    for name, domain in current["lstm_scaler_domains"].items():
        if domain.get("in_domain") is False:
            print(
                f"WARNING: LSTM '{name}' inputs scale to "
                f"[{domain['scaled_min']}, {domain['scaled_max']}] - outside the scaler domain.",
                file=sys.stderr,
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(current, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Wrote {args.output}")

    if args.compare:
        return compare(current, args.compare)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
