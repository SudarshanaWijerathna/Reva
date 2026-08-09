from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from ml.house_service.description_features import DESCRIPTION_CATEGORICAL_FEATURES
from ml.house_service.feature_schema import BASELINE_CATEGORICAL_COLUMNS
from ml.house_service.gnn.schema import (
    CATBOOST_PREDICTION_COLUMN,
    GNN_NODE_FEATURES,
    IMPUTABLE_BINARY_COLUMNS,
    IMPUTABLE_CATEGORICAL_COLUMNS,
    IMPUTABLE_NUMERIC_COLUMNS,
    LOG_CATBOOST_PREDICTION_COLUMN,
    LOG_TARGET_COLUMN,
    MISSING_MASK_COLUMNS,
    RESIDUAL_TARGET_COLUMN,
    TARGET_COLUMN,
)
from ml.house_service.train_enhanced_model import (
    DEFAULT_DATASETS,
    DEFAULT_OUTPUT_DIR,
    categorical_columns_for,
    load_datasets,
    prepare_training_frame,
    time_aware_split,
)


@dataclass
class FeatureState:
    numeric_columns: List[str]
    categorical_columns: List[str]
    node_features: List[str]
    numeric_mean: Dict[str, float]
    numeric_std: Dict[str, float]
    numeric_median: Dict[str, float]
    binary_mode: Dict[str, float]
    categorical_maps: Dict[str, Dict[str, int]]
    categorical_modes: Dict[str, str]


@dataclass
class GNNPreparedData:
    train_frame: pd.DataFrame
    validation_frame: pd.DataFrame
    train_features: np.ndarray
    validation_features: np.ndarray
    feature_state: FeatureState


def prepare_gnn_training_data(
    datasets: Iterable[Path] | None = None,
    catboost_model_path: Path | None = None,
    sample_frac: float = 1.0,
    validation_fraction: float = 0.25,
    random_seed: int = 42,
) -> GNNPreparedData:
    datasets = list(datasets or DEFAULT_DATASETS)
    catboost_model_path = catboost_model_path or (DEFAULT_OUTPUT_DIR / "catboost_house_price_enhanced.cbm")
    frame = load_datasets(datasets)
    frame = prepare_training_frame(frame, sample_frac=sample_frac, random_seed=random_seed)
    train_frame, validation_frame = time_aware_split(frame, validation_fraction=validation_fraction)

    model = CatBoostRegressor()
    model.load_model(str(catboost_model_path))
    _add_catboost_predictions(model, train_frame)
    _add_catboost_predictions(model, validation_frame)

    feature_state = fit_feature_state(train_frame)
    train_features = transform_node_features(train_frame, feature_state)
    validation_features = transform_node_features(validation_frame, feature_state)

    return GNNPreparedData(
        train_frame=train_frame,
        validation_frame=validation_frame,
        train_features=train_features,
        validation_features=validation_features,
        feature_state=feature_state,
    )


def fit_feature_state(frame: pd.DataFrame) -> FeatureState:
    frame = ensure_gnn_columns(frame.copy())
    categorical_columns = sorted(
        set(BASELINE_CATEGORICAL_COLUMNS + DESCRIPTION_CATEGORICAL_FEATURES + IMPUTABLE_CATEGORICAL_COLUMNS)
    )
    numeric_columns = [column for column in GNN_NODE_FEATURES if column not in categorical_columns]

    numeric_mean: Dict[str, float] = {}
    numeric_std: Dict[str, float] = {}
    numeric_median: Dict[str, float] = {}
    for column in numeric_columns:
        values = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
        median = float(values.median()) if values.notna().any() else 0.0
        mean = float(values.fillna(median).mean())
        std = float(values.fillna(median).std(ddof=0))
        numeric_median[column] = median
        numeric_mean[column] = mean
        numeric_std[column] = std if std > 1e-6 else 1.0

    categorical_maps: Dict[str, Dict[str, int]] = {}
    categorical_modes: Dict[str, str] = {}
    for column in categorical_columns:
        values = normalize_category_series(frame[column])
        mode = values.mode().iloc[0] if not values.mode().empty else "unknown"
        categories = ["unknown"] + sorted(value for value in values.unique() if value != "unknown")
        categorical_maps[column] = {value: index for index, value in enumerate(categories)}
        categorical_modes[column] = str(mode)

    binary_mode = {
        column: float(round(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).mean()))
        for column in IMPUTABLE_BINARY_COLUMNS
    }

    return FeatureState(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        node_features=GNN_NODE_FEATURES,
        numeric_mean=numeric_mean,
        numeric_std=numeric_std,
        numeric_median=numeric_median,
        binary_mode=binary_mode,
        categorical_maps=categorical_maps,
        categorical_modes=categorical_modes,
    )


def transform_node_features(frame: pd.DataFrame, state: FeatureState) -> np.ndarray:
    frame = ensure_gnn_columns(frame.copy())
    columns: List[np.ndarray] = []

    for column in state.node_features:
        if column in state.categorical_columns:
            mapping = state.categorical_maps[column]
            denominator = max(len(mapping) - 1, 1)
            encoded = normalize_category_series(frame[column]).map(mapping).fillna(0).astype(float) / denominator
            columns.append(encoded.to_numpy(dtype=np.float32))
        else:
            values = pd.to_numeric(frame[column], errors="coerce").fillna(state.numeric_median.get(column, 0.0))
            scaled = (values - state.numeric_mean.get(column, 0.0)) / state.numeric_std.get(column, 1.0)
            columns.append(scaled.to_numpy(dtype=np.float32))

    return np.column_stack(columns).astype(np.float32)


def ensure_gnn_columns(frame: pd.DataFrame) -> pd.DataFrame:
    for column in IMPUTABLE_NUMERIC_COLUMNS + IMPUTABLE_BINARY_COLUMNS:
        if column not in frame:
            frame[column] = np.nan
    for column in IMPUTABLE_CATEGORICAL_COLUMNS:
        if column not in frame:
            frame[column] = "unknown"

    for column in IMPUTABLE_NUMERIC_COLUMNS + IMPUTABLE_BINARY_COLUMNS + IMPUTABLE_CATEGORICAL_COLUMNS:
        missing_column = f"{column}_is_missing"
        if missing_column not in frame:
            if column in IMPUTABLE_CATEGORICAL_COLUMNS:
                frame[missing_column] = normalize_category_series(frame[column]).eq("unknown").astype(float)
            else:
                frame[missing_column] = pd.to_numeric(frame[column], errors="coerce").isna().astype(float)

    if CATBOOST_PREDICTION_COLUMN not in frame:
        frame[CATBOOST_PREDICTION_COLUMN] = 0.0
    if LOG_CATBOOST_PREDICTION_COLUMN not in frame:
        frame[LOG_CATBOOST_PREDICTION_COLUMN] = np.log1p(pd.to_numeric(frame[CATBOOST_PREDICTION_COLUMN], errors="coerce").fillna(0.0))

    for column in GNN_NODE_FEATURES:
        if column not in frame:
            frame[column] = "unknown" if column in IMPUTABLE_CATEGORICAL_COLUMNS else 0.0

    return frame


def add_training_targets(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame[LOG_TARGET_COLUMN] = np.log1p(pd.to_numeric(frame[TARGET_COLUMN], errors="coerce").clip(lower=0.0))
    frame[RESIDUAL_TARGET_COLUMN] = frame[LOG_TARGET_COLUMN] - frame[LOG_CATBOOST_PREDICTION_COLUMN]
    return frame


def imputation_target_arrays(frame: pd.DataFrame, state: FeatureState) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    numeric_columns = []
    for column in IMPUTABLE_NUMERIC_COLUMNS:
        values = pd.to_numeric(frame[column], errors="coerce").fillna(state.numeric_median.get(column, 0.0))
        scaled = (values - state.numeric_mean.get(column, 0.0)) / state.numeric_std.get(column, 1.0)
        numeric_columns.append(scaled.to_numpy(dtype=np.float32))
    numeric = np.column_stack(numeric_columns)
    binary = np.column_stack([
        pd.to_numeric(frame[column], errors="coerce").fillna(state.binary_mode.get(column, 0.0)).to_numpy(dtype=np.float32)
        for column in IMPUTABLE_BINARY_COLUMNS
    ])
    categorical_columns = []
    for column in IMPUTABLE_CATEGORICAL_COLUMNS:
        mapping = state.categorical_maps[column]
        categorical_columns.append(normalize_category_series(frame[column]).map(mapping).fillna(0).to_numpy(dtype=np.int64))
    categorical = np.column_stack(categorical_columns) if categorical_columns else np.empty((len(frame), 0), dtype=np.int64)
    return numeric.astype(np.float32), binary.astype(np.float32), categorical.astype(np.int64)


def feature_state_to_dict(state: FeatureState) -> Dict[str, Any]:
    return {
        "numeric_columns": state.numeric_columns,
        "categorical_columns": state.categorical_columns,
        "node_features": state.node_features,
        "numeric_mean": state.numeric_mean,
        "numeric_std": state.numeric_std,
        "numeric_median": state.numeric_median,
        "binary_mode": state.binary_mode,
        "categorical_maps": state.categorical_maps,
        "categorical_modes": state.categorical_modes,
    }


def feature_state_from_dict(payload: Dict[str, Any]) -> FeatureState:
    return FeatureState(
        numeric_columns=list(payload["numeric_columns"]),
        categorical_columns=list(payload["categorical_columns"]),
        node_features=list(payload["node_features"]),
        numeric_mean={key: float(value) for key, value in payload["numeric_mean"].items()},
        numeric_std={key: float(value) for key, value in payload["numeric_std"].items()},
        numeric_median={key: float(value) for key, value in payload["numeric_median"].items()},
        binary_mode={key: float(value) for key, value in payload["binary_mode"].items()},
        categorical_maps={
            column: {str(key): int(value) for key, value in mapping.items()}
            for column, mapping in payload["categorical_maps"].items()
        },
        categorical_modes={key: str(value) for key, value in payload["categorical_modes"].items()},
    )


def normalize_category_series(series: pd.Series) -> pd.Series:
    return series.fillna("unknown").astype(str).str.strip().str.lower().replace("", "unknown")


def _add_catboost_predictions(model: CatBoostRegressor, frame: pd.DataFrame) -> None:
    # CatBoost only consumes the feature list saved in its metadata; infer from the fitted model.
    catboost_features = model.feature_names_
    catboost_categories = categorical_columns_for(catboost_features)
    pool = Pool(frame[catboost_features], cat_features=catboost_categories)
    predictions = np.maximum(model.predict(pool).astype(float), 1.0)
    frame[CATBOOST_PREDICTION_COLUMN] = predictions
    frame[LOG_CATBOOST_PREDICTION_COLUMN] = np.log1p(predictions)
    frame[LOG_TARGET_COLUMN] = np.log1p(pd.to_numeric(frame[TARGET_COLUMN], errors="coerce").clip(lower=0.0))
    frame[RESIDUAL_TARGET_COLUMN] = frame[LOG_TARGET_COLUMN] - frame[LOG_CATBOOST_PREDICTION_COLUMN]
