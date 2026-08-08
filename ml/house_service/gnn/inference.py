import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Set

import numpy as np
import pandas as pd

from ml.house_service.gnn.data import (
    ensure_gnn_columns,
    feature_state_from_dict,
    transform_node_features,
)
from ml.house_service.gnn.graph_builder import GraphBuildConfig, build_query_edges
from ml.house_service.gnn.metrics import final_price_per_sqft
from ml.house_service.gnn.schema import (
    CATBOOST_PREDICTION_COLUMN,
    EDGE_ATTR_COLUMNS,
    GNN_FEATURE_VERSION,
    GNN_GRAPH_STORE_NAME,
    GNN_METADATA_NAME,
    GNN_MODEL_NAME,
    GNN_MODEL_VARIANT,
    IMPUTABLE_BINARY_COLUMNS,
    IMPUTABLE_CATEGORICAL_COLUMNS,
    IMPUTABLE_NUMERIC_COLUMNS,
    LOG_CATBOOST_PREDICTION_COLUMN,
)


class GNNUnavailableError(RuntimeError):
    pass


@dataclass
class GNNPredictionResult:
    predicted_price_per_sqft: float
    base_predicted_price_per_sqft: float
    residual_price_per_sqft: float
    imputed_features: Dict[str, Any]
    imputation_confidence: Dict[str, float]
    graph_neighbors_used: int
    feature_version: str


class HouseGNNPredictor:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.model_path = base_dir / GNN_MODEL_NAME
        self.metadata_path = base_dir / GNN_METADATA_NAME
        self.graph_store_path = base_dir / GNN_GRAPH_STORE_NAME
        if not self.model_path.exists() or not self.metadata_path.exists() or not self.graph_store_path.exists():
            raise GNNUnavailableError("GNN artifacts are not available.")

        try:
            import torch
            from ml.house_service.gnn.model import HouseGNNResidualImputer
        except ImportError as exc:
            raise GNNUnavailableError(str(exc)) from exc

        self.torch = torch
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.feature_state = feature_state_from_dict(self.metadata["feature_state"])
        self.graph_config = GraphBuildConfig(**self.metadata.get("graph_config", {}))
        self.graph_store = np.load(self.graph_store_path, allow_pickle=True)
        self.train_features = self.graph_store["train_features"].astype(np.float32)
        self.train_frame = pd.DataFrame(
            {
                "lat": self.graph_store["train_lat"],
                "lon": self.graph_store["train_lon"],
                "district": self.graph_store["train_district"].astype(str),
                "sub_location": self.graph_store["train_sub_location"].astype(str),
                "house_quality_tier": self.graph_store["train_quality"].astype(str),
                "posted_year": self.graph_store["train_posted_year"],
                "posted_month": self.graph_store["train_posted_month"],
            }
        )

        model_config = dict(self.metadata["model_config"])
        self.model = HouseGNNResidualImputer(
            input_dim=model_config["input_dim"],
            edge_dim=len(EDGE_ATTR_COLUMNS),
            numeric_imputation_dim=len(IMPUTABLE_NUMERIC_COLUMNS),
            binary_imputation_dim=len(IMPUTABLE_BINARY_COLUMNS),
            categorical_cardinalities=model_config["categorical_cardinalities"],
            hidden_dim=model_config["hidden_dim"],
            heads=model_config["heads"],
            dropout=model_config["dropout"],
        )
        self.model.load_state_dict(torch.load(self.model_path, map_location="cpu"))
        self.model.eval()

    def predict(
        self,
        normalized_features: Dict[str, Any],
        missing_fields: Set[str],
        catboost_predict: Callable[[Dict[str, Any]], float],
    ) -> GNNPredictionResult:
        first_base = catboost_predict(normalized_features)
        first_outputs = self._run_query(normalized_features, first_base)
        completed_features, imputed_features, confidence = self._apply_imputations(
            normalized_features,
            missing_fields,
            first_outputs,
        )
        second_base = catboost_predict(completed_features)
        second_outputs = self._run_query(completed_features, second_base)
        residual_log = float(second_outputs["residual_log_price"])
        final_price = float(final_price_per_sqft(np.array([second_base]), np.array([residual_log]))[0])

        return GNNPredictionResult(
            predicted_price_per_sqft=final_price,
            base_predicted_price_per_sqft=float(second_base),
            residual_price_per_sqft=float(final_price - second_base),
            imputed_features=imputed_features,
            imputation_confidence=confidence,
            graph_neighbors_used=int(second_outputs["neighbors_used"]),
            feature_version=self.metadata.get("feature_version", GNN_FEATURE_VERSION),
        )

    def _run_query(self, normalized_features: Dict[str, Any], base_price_per_sqft: float) -> Dict[str, Any]:
        query = dict(normalized_features)
        query[CATBOOST_PREDICTION_COLUMN] = float(base_price_per_sqft)
        query[LOG_CATBOOST_PREDICTION_COLUMN] = float(np.log1p(max(base_price_per_sqft, 1.0)))
        query_frame = ensure_gnn_columns(pd.DataFrame([query]))
        query_features = transform_node_features(query_frame, self.feature_state)[0]
        graph = build_query_edges(
            self.train_frame,
            self.train_features,
            query_frame.iloc[0],
            query_features,
            self.graph_config,
        )
        x = np.vstack([self.train_features, query_features.reshape(1, -1)]).astype(np.float32)
        with self.torch.no_grad():
            outputs = self.model(
                self.torch.as_tensor(x, dtype=self.torch.float32),
                self.torch.as_tensor(graph.edge_index, dtype=self.torch.long),
                self.torch.as_tensor(graph.edge_attr, dtype=self.torch.float32),
            )
        query_index = x.shape[0] - 1
        return {
            "residual_log_price": float(outputs["residual_log_price"][query_index].item()),
            "numeric_imputation": outputs["numeric_imputation"][query_index].detach().cpu().numpy(),
            "binary_imputation": outputs["binary_imputation"][query_index].detach().cpu().numpy(),
            "categorical_imputation": [
                logits[query_index].detach().cpu().numpy()
                for logits in outputs["categorical_imputation"]
            ],
            "neighbors_used": max(graph.edge_index.shape[1] - 1, 0),
        }

    def _apply_imputations(
        self,
        normalized_features: Dict[str, Any],
        missing_fields: Set[str],
        outputs: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, float]]:
        completed = dict(normalized_features)
        imputed: Dict[str, Any] = {}
        confidence: Dict[str, float] = {}

        for index, column in enumerate(IMPUTABLE_NUMERIC_COLUMNS):
            if column not in missing_fields:
                continue
            scaled_value = float(outputs["numeric_imputation"][index])
            value = scaled_value * self.feature_state.numeric_std[column] + self.feature_state.numeric_mean[column]
            value = max(value, 0.0)
            completed[column] = value
            imputed[column] = round(value, 6)
            confidence[column] = _confidence_from_scaled_value(scaled_value)

        for index, column in enumerate(IMPUTABLE_BINARY_COLUMNS):
            if column not in missing_fields:
                continue
            probability = _sigmoid(float(outputs["binary_imputation"][index]))
            completed[column] = int(probability >= 0.5)
            imputed[column] = int(probability >= 0.5)
            confidence[column] = round(max(probability, 1.0 - probability), 6)

        for index, column in enumerate(IMPUTABLE_CATEGORICAL_COLUMNS):
            if column not in missing_fields or index >= len(outputs["categorical_imputation"]):
                continue
            probabilities = _softmax(outputs["categorical_imputation"][index])
            category_index = int(np.argmax(probabilities))
            reverse_map = {
                mapped_index: category
                for category, mapped_index in self.feature_state.categorical_maps[column].items()
            }
            category = reverse_map.get(category_index, self.feature_state.categorical_modes.get(column, "unknown"))
            completed[column] = category
            imputed[column] = category
            confidence[column] = round(float(probabilities[category_index]), 6)

        return completed, imputed, confidence


def load_optional_gnn_predictor(base_dir: Path) -> Optional[HouseGNNPredictor]:
    try:
        return HouseGNNPredictor(base_dir)
    except GNNUnavailableError:
        return None


def gnn_response_metadata(result: GNNPredictionResult) -> Dict[str, Any]:
    return {
        "model_variant": GNN_MODEL_VARIANT,
        "base_predicted_price_per_sqft": round(result.base_predicted_price_per_sqft, 2),
        "gnn_residual_price_per_sqft": round(result.residual_price_per_sqft, 2),
        "imputed_features": result.imputed_features,
        "imputation_confidence": result.imputation_confidence,
        "graph_neighbors_used": result.graph_neighbors_used,
        "gnn_feature_version": result.feature_version,
    }


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + float(np.exp(-value)))


def _softmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    values = values - np.max(values)
    exp_values = np.exp(values)
    return exp_values / np.sum(exp_values)


def _confidence_from_scaled_value(value: float) -> float:
    return round(float(1.0 / (1.0 + abs(value))), 6)
