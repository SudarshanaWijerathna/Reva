import argparse
import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.rental_service.feature_schema import (  # noqa: E402
    CATEGORICAL_COLUMNS,
    FEATURE_OUTPUT_COLUMNS,
    MODEL_VARIANT,
    NUMERIC_COLUMNS,
    REQUIRED_TRAINING_COLUMNS,
    SCHEMA_VERSION,
    TARGET_COLUMN,
    TRAINING_FEATURE_COLUMNS,
    TRANSFORMED_TARGET_COLUMN,
)


DEFAULT_DATASET = REPO_ROOT / "data" / "features" / "rental_features_v1.csv"
DEFAULT_OUTPUT_DIR = BASE_DIR
MODEL_NAME = "catboost_rental_price.cbm"
METADATA_NAME = "catboost_rental_price_metadata.json"
REPORT_NAME = "rental_price_training_report.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate the rental price CatBoost model.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=1400)
    parser.add_argument("--learning-rate", type=float, default=0.045)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--l2-leaf-reg", type=float, default=6.0)
    parser.add_argument("--early-stopping-rounds", type=int, default=100)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--temporal-test-year", type=int, default=2026)
    parser.add_argument("--sample-frac", type=float, default=1.0)
    parser.add_argument("--min-improvement", type=float, default=0.01)
    parser.add_argument("--max-train-val-ratio", type=float, default=2.5)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--verbose", type=int, default=100)
    parser.add_argument(
        "--lightgbm",
        choices=["auto", "off", "on"],
        default="auto",
        help="Train a LightGBM benchmark when available.",
    )
    return parser.parse_args()


def ensure_training_dependencies(lightgbm_mode: str = "auto") -> Dict[str, Any]:
    missing = [
        name
        for name in ["pandas", "numpy", "catboost"]
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise RuntimeError(
            "Missing training dependencies: "
            + ", ".join(missing)
            + ". Install ml/rental_service/requirements.txt before training."
        )

    import numpy as np
    import pandas as pd
    from catboost import CatBoostRegressor, Pool

    deps: Dict[str, Any] = {
        "np": np,
        "pd": pd,
        "CatBoostRegressor": CatBoostRegressor,
        "Pool": Pool,
        "LGBMRegressor": None,
    }

    if lightgbm_mode != "off" and importlib.util.find_spec("lightgbm") is not None:
        from lightgbm import LGBMRegressor

        deps["LGBMRegressor"] = LGBMRegressor
    elif lightgbm_mode == "on":
        raise RuntimeError("LightGBM benchmark was requested but lightgbm is not installed.")

    return deps


def validate_required_columns(columns: Iterable[str]) -> List[str]:
    available = set(columns)
    missing = [column for column in REQUIRED_TRAINING_COLUMNS if column not in available]
    if missing:
        raise ValueError(f"Missing required rental training columns: {missing}")
    return missing


def deterministic_split_score(value: Any, random_seed: int) -> float:
    digest = hashlib.sha1(f"{random_seed}|{value}".encode("utf-8", errors="ignore")).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def validate_fraction(value: float, name: str) -> None:
    if not 0 < value < 1:
        raise ValueError(f"{name} must be greater than 0 and less than 1")


def load_training_frame(dataset: Path, pd: Any) -> Any:
    if not dataset.exists():
        raise FileNotFoundError(f"Rental feature dataset not found: {dataset}")
    frame = pd.read_csv(dataset, low_memory=False)
    validate_required_columns(frame.columns)
    return frame


def prepare_training_frame(frame: Any, pd: Any, sample_frac: float, random_seed: int) -> Any:
    if not 0 < sample_frac <= 1:
        raise ValueError("--sample-frac must be greater than 0 and less than or equal to 1")

    selected_columns = sorted(set(REQUIRED_TRAINING_COLUMNS + ["source_file"]))
    frame = frame[selected_columns].copy()

    for column in CATEGORICAL_COLUMNS:
        frame[column] = (
            frame[column]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .replace("", "unknown")
        )

    for column in [*NUMERIC_COLUMNS, TARGET_COLUMN, TRANSFORMED_TARGET_COLUMN]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    valid_mask = frame[TARGET_COLUMN].notna() & (frame[TARGET_COLUMN] > 0)
    valid_mask &= frame[TRANSFORMED_TARGET_COLUMN].notna()
    for column in NUMERIC_COLUMNS:
        frame[column] = frame[column].fillna(0.0)

    frame = frame.loc[valid_mask].reset_index(drop=True)
    if sample_frac < 1:
        frame = frame.sample(frac=sample_frac, random_state=random_seed).reset_index(drop=True)
    frame["_row_order"] = range(len(frame))
    return frame


def split_training_frame(
    frame: Any,
    validation_fraction: float,
    temporal_test_year: int,
    random_seed: int,
    pd: Any,
) -> Tuple[Any, Any, Any, str]:
    validate_fraction(validation_fraction, "--validation-fraction")

    posted_year = pd.to_numeric(frame["posted_year"], errors="coerce").fillna(0).astype(int)
    temporal_mask = posted_year.eq(temporal_test_year)
    temporal_test = frame.loc[temporal_mask].copy()
    train_validation = frame.loc[~temporal_mask].copy()

    if train_validation.empty:
        raise ValueError("Train/validation partition is empty after temporal holdout.")

    split_keys = (
        train_validation["record_id"].fillna("").astype(str)
        + "|"
        + train_validation["property_type"].fillna("").astype(str)
        + "|"
        + train_validation["source_file"].fillna("").astype(str)
    )
    split_scores = split_keys.map(lambda value: deterministic_split_score(value, random_seed))
    validation_mask = split_scores < validation_fraction

    validation = train_validation.loc[validation_mask].copy()
    train = train_validation.loc[~validation_mask].copy()

    if train.empty or validation.empty:
        raise ValueError("Deterministic train/validation split produced an empty partition.")

    policy = (
        f"Hold out posted_year == {temporal_test_year} for final temporal testing; "
        f"deterministic hash split of remaining rows with validation_fraction={validation_fraction}."
    )
    return train.reset_index(drop=True), validation.reset_index(drop=True), temporal_test.reset_index(drop=True), policy


def expm1_list(values: Sequence[float]) -> List[float]:
    return [max(math.expm1(float(value)), 0.0) for value in values]


def regression_metrics_from_prices(y_true: Sequence[float], y_pred: Sequence[float]) -> Dict[str, float]:
    pairs = [(float(true), float(pred)) for true, pred in zip(y_true, y_pred)]
    if not pairs:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "median_ape": 0.0, "r2": 0.0}

    errors = [pred - true for true, pred in pairs]
    abs_errors = [abs(error) for error in errors]
    pct_errors = [abs_error / max(abs(true), 1.0) for abs_error, (true, _) in zip(abs_errors, pairs)]
    mean_true = sum(true for true, _ in pairs) / len(pairs)
    ss_res = sum(error**2 for error in errors)
    ss_tot = sum((true - mean_true) ** 2 for true, _ in pairs)
    sorted_pct = sorted(pct_errors)
    mid = len(sorted_pct) // 2
    median_ape = sorted_pct[mid] if len(sorted_pct) % 2 else (sorted_pct[mid - 1] + sorted_pct[mid]) / 2.0
    return {
        "mae": sum(abs_errors) / len(abs_errors),
        "rmse": math.sqrt(ss_res / len(errors)),
        "mape": sum(pct_errors) / len(pct_errors) * 100.0,
        "median_ape": median_ape * 100.0,
        "r2": 0.0 if ss_tot == 0 else 1.0 - (ss_res / ss_tot),
    }


def regression_metrics_from_log_predictions(
    y_true_log: Sequence[float],
    y_pred_log: Sequence[float],
) -> Dict[str, float]:
    return regression_metrics_from_prices(expm1_list(y_true_log), expm1_list(y_pred_log))


def quantile(values: Sequence[float], q: float) -> float:
    clean_values = sorted(float(value) for value in values)
    if not clean_values:
        return 0.0
    index = (len(clean_values) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return clean_values[low]
    return clean_values[low] * (high - index) + clean_values[high] * (index - low)


def median_baseline_predictions(train_frame: Any, eval_frame: Any, group_columns: List[str]) -> List[float]:
    if group_columns:
        grouped = train_frame.groupby(group_columns)[TRANSFORMED_TARGET_COLUMN].median().to_dict()
    else:
        grouped = {}
    global_median = float(train_frame[TRANSFORMED_TARGET_COLUMN].median())
    predictions = []
    for _, row in eval_frame.iterrows():
        key: Any
        if not group_columns:
            key = None
        elif len(group_columns) == 1:
            key = row[group_columns[0]]
        else:
            key = tuple(row[column] for column in group_columns)
        predictions.append(float(grouped.get(key, global_median)))
    return predictions


def evaluate_log_predictions(frame: Any, y_pred_log: Sequence[float]) -> Dict[str, float]:
    return regression_metrics_from_log_predictions(
        frame[TRANSFORMED_TARGET_COLUMN].astype(float).tolist(),
        [float(value) for value in y_pred_log],
    )


def train_and_evaluate_baselines(train_frame: Any, validation_frame: Any, temporal_test_frame: Any) -> Dict[str, Any]:
    specs = {
        "global_median": [],
        "property_type_median": ["property_type"],
        "property_type_source_median": ["property_type", "source_file"],
    }
    results: Dict[str, Any] = {}
    for name, group_columns in specs.items():
        result = {
            "features": group_columns,
            "metrics": {
                "train": evaluate_log_predictions(train_frame, median_baseline_predictions(train_frame, train_frame, group_columns)),
                "validation": evaluate_log_predictions(
                    validation_frame,
                    median_baseline_predictions(train_frame, validation_frame, group_columns),
                ),
            },
        }
        if len(temporal_test_frame):
            result["metrics"]["temporal_test"] = evaluate_log_predictions(
                temporal_test_frame,
                median_baseline_predictions(train_frame, temporal_test_frame, group_columns),
            )
        results[name] = result
    return results


def train_catboost(train_frame: Any, validation_frame: Any, temporal_test_frame: Any, args: argparse.Namespace, deps: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    CatBoostRegressor = deps["CatBoostRegressor"]
    Pool = deps["Pool"]

    train_pool = Pool(
        train_frame[TRAINING_FEATURE_COLUMNS],
        label=train_frame[TRANSFORMED_TARGET_COLUMN],
        cat_features=CATEGORICAL_COLUMNS,
    )
    validation_pool = Pool(
        validation_frame[TRAINING_FEATURE_COLUMNS],
        label=validation_frame[TRANSFORMED_TARGET_COLUMN],
        cat_features=CATEGORICAL_COLUMNS,
    )

    model = CatBoostRegressor(
        iterations=args.iterations,
        learning_rate=args.learning_rate,
        depth=args.depth,
        l2_leaf_reg=args.l2_leaf_reg,
        loss_function="RMSE",
        eval_metric="MAE",
        random_seed=args.random_seed,
        allow_writing_files=False,
        verbose=args.verbose,
    )
    model.fit(
        train_pool,
        eval_set=validation_pool,
        use_best_model=True,
        early_stopping_rounds=args.early_stopping_rounds,
        verbose=args.verbose,
    )

    metrics = {
        "train": evaluate_log_predictions(train_frame, model.predict(train_pool)),
        "validation": evaluate_log_predictions(validation_frame, model.predict(validation_pool)),
        "best_iteration": int(model.get_best_iteration() or 0),
    }
    if len(temporal_test_frame):
        test_pool = Pool(
            temporal_test_frame[TRAINING_FEATURE_COLUMNS],
            label=temporal_test_frame[TRANSFORMED_TARGET_COLUMN],
            cat_features=CATEGORICAL_COLUMNS,
        )
        metrics["temporal_test"] = evaluate_log_predictions(temporal_test_frame, model.predict(test_pool))

    return model, {
        "features": TRAINING_FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "metrics": metrics,
    }


def train_lightgbm_benchmark(train_frame: Any, validation_frame: Any, temporal_test_frame: Any, args: argparse.Namespace, deps: Dict[str, Any]) -> Dict[str, Any] | None:
    LGBMRegressor = deps.get("LGBMRegressor")
    if LGBMRegressor is None:
        return None

    train_x = train_frame[TRAINING_FEATURE_COLUMNS].copy()
    validation_x = validation_frame[TRAINING_FEATURE_COLUMNS].copy()
    test_x = temporal_test_frame[TRAINING_FEATURE_COLUMNS].copy() if len(temporal_test_frame) else None

    for column in CATEGORICAL_COLUMNS:
        categories = train_x[column].astype("category").cat.categories
        train_x[column] = train_x[column].astype("category")
        validation_x[column] = validation_x[column].astype("category").cat.set_categories(categories)
        if test_x is not None:
            test_x[column] = test_x[column].astype("category").cat.set_categories(categories)

    model = LGBMRegressor(
        objective="regression",
        n_estimators=min(args.iterations, 1200),
        learning_rate=args.learning_rate,
        num_leaves=63,
        max_depth=args.depth,
        reg_lambda=args.l2_leaf_reg,
        random_state=args.random_seed,
    )
    model.fit(
        train_x,
        train_frame[TRANSFORMED_TARGET_COLUMN],
        eval_set=[(validation_x, validation_frame[TRANSFORMED_TARGET_COLUMN])],
        eval_metric="l1",
        categorical_feature=CATEGORICAL_COLUMNS,
    )
    metrics = {
        "train": evaluate_log_predictions(train_frame, model.predict(train_x)),
        "validation": evaluate_log_predictions(validation_frame, model.predict(validation_x)),
    }
    if test_x is not None:
        metrics["temporal_test"] = evaluate_log_predictions(temporal_test_frame, model.predict(test_x))
    return {
        "features": TRAINING_FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "metrics": metrics,
    }


def segment_metrics(frame: Any, y_pred_log: Sequence[float], group_column: str) -> Dict[str, Any]:
    if not len(frame):
        return {}
    eval_frame = frame[[group_column, TRANSFORMED_TARGET_COLUMN]].copy()
    eval_frame["_prediction_log"] = list(y_pred_log)
    output: Dict[str, Any] = {}
    for value, group in eval_frame.groupby(group_column):
        if len(group) < 10:
            continue
        output[str(value)] = {
            "rows": int(len(group)),
            **evaluate_log_predictions(group, group["_prediction_log"].tolist()),
        }
    return output


def acceptance_decision(results: Dict[str, Any], min_improvement: float, max_train_val_ratio: float) -> Tuple[bool, str]:
    baseline_names = [name for name in results if name.endswith("median")]
    best_baseline_name = min(
        baseline_names,
        key=lambda name: results[name]["metrics"]["validation"]["mae"],
    )
    baseline_mae = results[best_baseline_name]["metrics"]["validation"]["mae"]
    catboost_mae = results["catboost"]["metrics"]["validation"]["mae"]
    relative_improvement = (baseline_mae - catboost_mae) / max(baseline_mae, 1.0)
    train_mae = max(results["catboost"]["metrics"]["train"]["mae"], 1.0)
    train_val_ratio = catboost_mae / train_mae

    if relative_improvement < min_improvement:
        return False, (
            f"Rejected CatBoost: validation MAE improved by {relative_improvement:.2%} over "
            f"{best_baseline_name}, below threshold {min_improvement:.2%}."
        )
    if train_val_ratio > max_train_val_ratio:
        return False, (
            f"Rejected CatBoost: train/validation MAE ratio {train_val_ratio:.3f} exceeds "
            f"limit {max_train_val_ratio:.3f}."
        )
    return True, (
        f"Accepted CatBoost: validation MAE improved by {relative_improvement:.2%} over "
        f"{best_baseline_name}; train/validation MAE ratio {train_val_ratio:.3f}."
    )


def error_calibration(frame: Any, y_pred_log: Sequence[float]) -> Dict[str, float]:
    y_true = expm1_list(frame[TRANSFORMED_TARGET_COLUMN].astype(float).tolist())
    y_pred = expm1_list([float(value) for value in y_pred_log])
    abs_errors = [abs(pred - true) for true, pred in zip(y_true, y_pred)]
    rel_errors = [abs_error / max(abs(true), 1.0) for abs_error, true in zip(abs_errors, y_true)]
    return {
        "absolute_error_p50": quantile(abs_errors, 0.5),
        "absolute_error_p80": quantile(abs_errors, 0.8),
        "absolute_error_p90": quantile(abs_errors, 0.9),
        "relative_error_p50": quantile(rel_errors, 0.5),
        "relative_error_p80": quantile(rel_errors, 0.8),
        "relative_error_p90": quantile(rel_errors, 0.9),
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    deps = ensure_training_dependencies(args.lightgbm)
    pd = deps["pd"]

    frame = load_training_frame(args.dataset, pd)
    frame = prepare_training_frame(frame, pd, sample_frac=args.sample_frac, random_seed=args.random_seed)
    train_frame, validation_frame, temporal_test_frame, split_policy = split_training_frame(
        frame,
        validation_fraction=args.validation_fraction,
        temporal_test_year=args.temporal_test_year,
        random_seed=args.random_seed,
        pd=pd,
    )

    results = train_and_evaluate_baselines(train_frame, validation_frame, temporal_test_frame)
    catboost_model, catboost_result = train_catboost(train_frame, validation_frame, temporal_test_frame, args, deps)
    results["catboost"] = catboost_result

    lgbm_result = train_lightgbm_benchmark(train_frame, validation_frame, temporal_test_frame, args, deps)
    if lgbm_result:
        results["lightgbm_benchmark"] = lgbm_result

    accepted, accepted_reason = acceptance_decision(
        results,
        min_improvement=args.min_improvement,
        max_train_val_ratio=args.max_train_val_ratio,
    )

    validation_pool = deps["Pool"](
        validation_frame[TRAINING_FEATURE_COLUMNS],
        label=validation_frame[TRANSFORMED_TARGET_COLUMN],
        cat_features=CATEGORICAL_COLUMNS,
    )
    validation_predictions = catboost_model.predict(validation_pool)

    report = {
        "schema_version": SCHEMA_VERSION,
        "model_variant": MODEL_VARIANT,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset": str(args.dataset),
        "target_column": TARGET_COLUMN,
        "training_target_column": TRANSFORMED_TARGET_COLUMN,
        "target_inverse_transform": "expm1",
        "features": TRAINING_FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "train_rows": int(len(train_frame)),
        "validation_rows": int(len(validation_frame)),
        "temporal_test_rows": int(len(temporal_test_frame)),
        "split_policy": split_policy,
        "accepted": accepted,
        "accepted_reason": accepted_reason,
        "results": results,
        "validation_segment_metrics": {
            "property_type": segment_metrics(validation_frame, validation_predictions, "property_type"),
            "source_file": segment_metrics(validation_frame, validation_predictions, "source_file"),
        },
        "error_calibration": error_calibration(validation_frame, validation_predictions),
    }

    report_path = args.output_dir / REPORT_NAME
    report_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")

    if accepted:
        model_path = args.output_dir / MODEL_NAME
        metadata_path = args.output_dir / METADATA_NAME
        catboost_model.save_model(str(model_path))
        metadata = {
            "model_type": "rental",
            "model_variant": MODEL_VARIANT,
            "schema_version": SCHEMA_VERSION,
            "created_at": report["generated_at"],
            "target_column": TARGET_COLUMN,
            "training_target_column": TRANSFORMED_TARGET_COLUMN,
            "target_inverse_transform": "expm1",
            "features": TRAINING_FEATURE_COLUMNS,
            "categorical_columns": CATEGORICAL_COLUMNS,
            "numeric_columns": NUMERIC_COLUMNS,
            "training_report": report_path.name,
            "metrics": results["catboost"]["metrics"],
            "error_calibration": report["error_calibration"],
        }
        metadata_path.write_text(json.dumps(_json_safe(metadata), indent=2), encoding="utf-8")

    print(json.dumps(_json_safe(report), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
