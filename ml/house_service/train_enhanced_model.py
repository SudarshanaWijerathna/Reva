import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from ml.house_service.description_features import (
    DESCRIPTION_CATEGORICAL_FEATURES,
    DESCRIPTION_FEATURES,
    FEATURE_EXTRACTION_VERSION,
    extract_description_features,
)
from ml.house_service.feature_schema import BASELINE_CATEGORICAL_COLUMNS, BASELINE_FEATURES


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]
DEFAULT_DATASETS = [
    REPO_ROOT / "data" / "processed" / "cleaned_22_23_house_catboost_ready.csv",
    REPO_ROOT / "data" / "processed" / "cleaned_25_house_catboost_ready.csv",
]
DEFAULT_OUTPUT_DIR = BASE_DIR

TARGET_COLUMN = "price_per_sqft_capped"
REQUIRED_COLUMNS = sorted(set(BASELINE_FEATURES + [TARGET_COLUMN, "description"]))
TRAINING_REPORT_NAME = "catboost_house_price_training_report.json"
ENHANCED_MODEL_NAME = "catboost_house_price_enhanced.cbm"
ENHANCED_METADATA_NAME = "catboost_house_price_enhanced_metadata.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate the enhanced house CatBoost model.")
    parser.add_argument("--datasets", nargs="+", type=Path, default=DEFAULT_DATASETS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=1200)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--early-stopping-rounds", type=int, default=80)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--min-improvement", type=float, default=0.001)
    parser.add_argument("--max-train-val-ratio", type=float, default=2.5)
    parser.add_argument("--sample-frac", type=float, default=1.0)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--verbose", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_datasets(args.datasets)
    frame = prepare_training_frame(frame, sample_frac=args.sample_frac, random_seed=args.random_seed)
    train_frame, validation_frame = time_aware_split(
        frame,
        validation_fraction=args.validation_fraction,
    )

    model_specs = [
        ("baseline", BASELINE_FEATURES),
        ("enhanced_with_index", BASELINE_FEATURES + DESCRIPTION_FEATURES),
        (
            "enhanced_without_index",
            BASELINE_FEATURES + [feature for feature in DESCRIPTION_FEATURES if feature != "description_value_index"],
        ),
    ]

    trained_models: Dict[str, CatBoostRegressor] = {}
    results: Dict[str, Any] = {}
    for name, features in model_specs:
        model, metrics = train_and_evaluate(
            train_frame=train_frame,
            validation_frame=validation_frame,
            features=features,
            categorical_columns=categorical_columns_for(features),
            args=args,
        )
        trained_models[name] = model
        results[name] = {
            "features": features,
            "categorical_columns": categorical_columns_for(features),
            "metrics": metrics,
        }

    accepted_name, accepted_reason = choose_accepted_model(
        results,
        min_improvement=args.min_improvement,
        max_train_val_ratio=args.max_train_val_ratio,
    )

    report = {
        "feature_extraction_version": FEATURE_EXTRACTION_VERSION,
        "target_column": TARGET_COLUMN,
        "datasets": [str(path) for path in args.datasets],
        "train_rows": int(len(train_frame)),
        "validation_rows": int(len(validation_frame)),
        "validation_policy": "Hold out the latest rows from cleaned_25_house_catboost_ready.csv by posted year/month/day order.",
        "accepted_model": accepted_name,
        "accepted_reason": accepted_reason,
        "results": results,
    }

    report_path = args.output_dir / TRAINING_REPORT_NAME
    report_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")

    if accepted_name:
        accepted_result = results[accepted_name]
        model_path = args.output_dir / ENHANCED_MODEL_NAME
        metadata_path = args.output_dir / ENHANCED_METADATA_NAME
        trained_models[accepted_name].save_model(str(model_path))
        metadata = {
            "model_type": "house",
            "model_variant": accepted_name,
            "feature_extraction_version": FEATURE_EXTRACTION_VERSION,
            "target_column": TARGET_COLUMN,
            "features": accepted_result["features"],
            "categorical_columns": accepted_result["categorical_columns"],
            "baseline_features": BASELINE_FEATURES,
            "description_features": DESCRIPTION_FEATURES,
            "description_categorical_features": DESCRIPTION_CATEGORICAL_FEATURES,
            "uses_description_value_index": "description_value_index" in accepted_result["features"],
            "training_report": report_path.name,
            "metrics": accepted_result["metrics"],
        }
        metadata_path.write_text(json.dumps(_json_safe(metadata), indent=2), encoding="utf-8")

    print(json.dumps(_json_safe(report), indent=2))
    return 0


def load_datasets(paths: Iterable[Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        frame = pd.read_csv(path, low_memory=False)
        frame["source_dataset"] = path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in combined.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    return combined


def prepare_training_frame(frame: pd.DataFrame, sample_frac: float, random_seed: int) -> pd.DataFrame:
    selected_columns = sorted(set(REQUIRED_COLUMNS + ["posted_day", "source_dataset"]))
    frame = frame[selected_columns].copy()

    for column in BASELINE_FEATURES + [TARGET_COLUMN]:
        if column not in BASELINE_CATEGORICAL_COLUMNS:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    for column in BASELINE_CATEGORICAL_COLUMNS:
        frame[column] = (
            frame[column]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .str.lower()
            .replace("", "unknown")
        )

    valid_mask = frame[TARGET_COLUMN].notna() & (frame[TARGET_COLUMN] > 0)
    for column in [feature for feature in BASELINE_FEATURES if feature not in BASELINE_CATEGORICAL_COLUMNS]:
        valid_mask &= frame[column].notna()

    frame = frame.loc[valid_mask].reset_index(drop=True)
    if not 0 < sample_frac <= 1:
        raise ValueError("--sample-frac must be greater than 0 and less than or equal to 1")
    if sample_frac < 1:
        frame = frame.sample(frac=sample_frac, random_state=random_seed).reset_index(drop=True)

    description_features = pd.DataFrame.from_records(
        frame["description"].apply(extract_description_features),
        columns=DESCRIPTION_FEATURES,
    )
    frame = pd.concat([frame.reset_index(drop=True), description_features], axis=1)

    for column in DESCRIPTION_CATEGORICAL_FEATURES:
        frame[column] = frame[column].fillna("unknown").astype(str)
    for column in [feature for feature in DESCRIPTION_FEATURES if feature not in DESCRIPTION_CATEGORICAL_FEATURES]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    frame["_row_order"] = np.arange(len(frame))
    return frame


def time_aware_split(frame: pd.DataFrame, validation_fraction: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < validation_fraction < 1:
        raise ValueError("--validation-fraction must be greater than 0 and less than 1")

    is_2025 = frame["source_dataset"].eq("cleaned_25_house_catboost_ready.csv")
    current_frame = frame.loc[is_2025].copy()
    historical_frame = frame.loc[~is_2025].copy()

    if current_frame.empty:
        raise ValueError("The 2025 CatBoost-ready dataset is required for time-aware validation.")

    sort_columns = [column for column in ["posted_year", "posted_month", "posted_day", "_row_order"] if column in current_frame]
    current_frame = current_frame.sort_values(sort_columns)

    validation_count = max(1, int(round(len(current_frame) * validation_fraction)))
    validation_frame = current_frame.tail(validation_count)
    train_current_frame = current_frame.iloc[:-validation_count]
    train_frame = pd.concat([historical_frame, train_current_frame], ignore_index=True)

    if train_frame.empty or validation_frame.empty:
        raise ValueError("Train/validation split produced an empty partition.")

    return train_frame.reset_index(drop=True), validation_frame.reset_index(drop=True)


def train_and_evaluate(
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    features: List[str],
    categorical_columns: List[str],
    args: argparse.Namespace,
) -> Tuple[CatBoostRegressor, Dict[str, Any]]:
    train_pool = Pool(
        train_frame[features],
        label=train_frame[TARGET_COLUMN],
        cat_features=categorical_columns,
    )
    validation_pool = Pool(
        validation_frame[features],
        label=validation_frame[TARGET_COLUMN],
        cat_features=categorical_columns,
    )

    model = CatBoostRegressor(
        iterations=args.iterations,
        learning_rate=args.learning_rate,
        depth=args.depth,
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

    return model, {
        "train": regression_metrics(train_frame[TARGET_COLUMN].to_numpy(), model.predict(train_pool)),
        "validation": regression_metrics(validation_frame[TARGET_COLUMN].to_numpy(), model.predict(validation_pool)),
        "best_iteration": int(model.get_best_iteration() or 0),
    }


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    error = y_pred - y_true
    absolute_error = np.abs(error)
    percentage_error = absolute_error / np.maximum(np.abs(y_true), 1.0)
    return {
        "mae": float(np.mean(absolute_error)),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mape": float(np.mean(percentage_error) * 100.0),
        "median_ape": float(np.median(percentage_error) * 100.0),
    }


def choose_accepted_model(
    results: Dict[str, Any],
    min_improvement: float,
    max_train_val_ratio: float,
) -> Tuple[str, str]:
    baseline_mae = results["baseline"]["metrics"]["validation"]["mae"]
    enhanced_names = ["enhanced_with_index", "enhanced_without_index"]
    best_name = min(enhanced_names, key=lambda name: results[name]["metrics"]["validation"]["mae"])
    best_metrics = results[best_name]["metrics"]
    best_mae = best_metrics["validation"]["mae"]
    relative_improvement = (baseline_mae - best_mae) / baseline_mae
    train_mae = max(best_metrics["train"]["mae"], 1.0)
    train_val_ratio = best_mae / train_mae

    if relative_improvement < min_improvement:
        return "", (
            f"Best enhanced model was {relative_improvement:.4%} better by validation MAE, "
            f"below the configured {min_improvement:.4%} threshold."
        )
    if train_val_ratio > max_train_val_ratio:
        return "", (
            f"Best enhanced model train/validation MAE ratio was {train_val_ratio:.3f}, "
            f"above the configured {max_train_val_ratio:.3f} limit."
        )

    index_note = (
        "including description_value_index"
        if best_name == "enhanced_with_index"
        else "without description_value_index"
    )
    return best_name, (
        f"Accepted {best_name} {index_note}; validation MAE improved by "
        f"{relative_improvement:.4%} versus baseline."
    )


def categorical_columns_for(features: List[str]) -> List[str]:
    all_categoricals = BASELINE_CATEGORICAL_COLUMNS + DESCRIPTION_CATEGORICAL_FEATURES
    return [column for column in all_categoricals if column in features]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
