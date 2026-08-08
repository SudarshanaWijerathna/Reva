import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from ml.house_service.gnn.data import (
    feature_state_to_dict,
    imputation_target_arrays,
    prepare_gnn_training_data,
    transform_node_features,
)
from ml.house_service.gnn.graph_builder import GraphBuildConfig, build_property_graph
from ml.house_service.gnn.metrics import final_price_per_sqft, imputation_metrics, regression_metrics
from ml.house_service.gnn.schema import (
    CATBOOST_PREDICTION_COLUMN,
    EDGE_ATTR_COLUMNS,
    GNN_FEATURE_VERSION,
    GNN_GRAPH_STORE_NAME,
    GNN_METADATA_NAME,
    GNN_MODEL_NAME,
    GNN_MODEL_VARIANT,
    GNN_TRAINING_REPORT_NAME,
    IMPUTABLE_BINARY_COLUMNS,
    IMPUTABLE_CATEGORICAL_COLUMNS,
    IMPUTABLE_NUMERIC_COLUMNS,
    LOG_TARGET_COLUMN,
    RESIDUAL_TARGET_COLUMN,
    TARGET_COLUMN,
)
from ml.house_service.train_enhanced_model import DEFAULT_OUTPUT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the house CatBoost + GNN residual/imputation model.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--sample-frac", type=float, default=1.0)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--spatial-k", type=int, default=16)
    parser.add_argument("--feature-k", type=int, default=16)
    parser.add_argument("--location-k", type=int, default=8)
    parser.add_argument("--mask-rate", type=float, default=0.2)
    parser.add_argument("--accept-min-improvement", type=float, default=0.02)
    parser.add_argument("--baseline-mae", type=float, default=3980.370605862797)
    parser.add_argument("--baseline-mape", type=float, default=19.66096151082424)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    torch, _ = require_torch()
    from ml.house_service.gnn.losses import LossWeights, multitask_loss
    from ml.house_service.gnn.model import HouseGNNResidualImputer, model_config_from_instance

    rng = np.random.default_rng(args.random_seed)
    prepared = prepare_gnn_training_data(
        sample_frac=args.sample_frac,
        validation_fraction=args.validation_fraction,
        random_seed=args.random_seed,
    )
    graph_config = GraphBuildConfig(
        spatial_k=args.spatial_k,
        feature_k=args.feature_k,
        location_k=args.location_k,
    )
    train_graph = build_property_graph(prepared.train_frame, prepared.train_features, graph_config)
    validation_graph = build_property_graph(prepared.validation_frame, prepared.validation_features, graph_config)

    train_masked_frame, train_imputation_mask = make_masked_frame(
        prepared.train_frame,
        prepared.feature_state,
        rng,
        args.mask_rate,
    )
    validation_masked_frame, validation_imputation_mask = make_masked_frame(
        prepared.validation_frame,
        prepared.feature_state,
        rng,
        args.mask_rate,
    )
    train_masked_features = transform_node_features(train_masked_frame, prepared.feature_state)
    validation_masked_features = transform_node_features(validation_masked_frame, prepared.feature_state)

    tensors = build_tensors(
        torch=torch,
        train_frame=prepared.train_frame,
        validation_frame=prepared.validation_frame,
        train_features=train_masked_features,
        validation_features=validation_masked_features,
        train_graph=train_graph,
        validation_graph=validation_graph,
        train_imputation_mask=train_imputation_mask,
        validation_imputation_mask=validation_imputation_mask,
        feature_state=prepared.feature_state,
        device=args.device,
    )

    categorical_cardinalities = [
        len(prepared.feature_state.categorical_maps[column])
        for column in IMPUTABLE_CATEGORICAL_COLUMNS
    ]
    variants = [
        ("standalone_gnn", LossWeights(price=0.0, imputation=0.0, standalone_price=1.0), "standalone"),
        ("residual_no_imputation", LossWeights(price=1.0, imputation=0.0, standalone_price=0.0), "residual"),
        ("residual_mtl_70_30", LossWeights(price=0.7, imputation=0.3, standalone_price=0.0), "residual"),
        ("residual_mtl_85_15", LossWeights(price=0.85, imputation=0.15, standalone_price=0.0), "residual"),
    ]

    results: Dict[str, Any] = {}
    best_payload: Dict[str, Any] | None = None
    best_name = ""
    for name, weights, prediction_mode in variants:
        model = HouseGNNResidualImputer(
            input_dim=prepared.train_features.shape[1],
            edge_dim=len(EDGE_ATTR_COLUMNS),
            numeric_imputation_dim=len(IMPUTABLE_NUMERIC_COLUMNS),
            binary_imputation_dim=len(IMPUTABLE_BINARY_COLUMNS),
            categorical_cardinalities=categorical_cardinalities,
            hidden_dim=args.hidden_dim,
            heads=args.heads,
            dropout=args.dropout,
        ).to(args.device)
        result, state_dict = train_variant(
            torch=torch,
            model=model,
            tensors=tensors,
            weights=weights,
            prediction_mode=prediction_mode,
            args=args,
            multitask_loss=multitask_loss,
        )
        results[name] = result
        if best_payload is None or result["validation"]["mae"] < best_payload["result"]["validation"]["mae"]:
            best_name = name
            best_payload = {
                "result": result,
                "state_dict": state_dict,
                "model_config": model_config_from_instance(model),
                "prediction_mode": prediction_mode,
            }

    accepted, reason = acceptance_decision(
        results,
        best_name,
        args.baseline_mae,
        args.baseline_mape,
        args.accept_min_improvement,
    )
    report = {
        "model_variant": GNN_MODEL_VARIANT,
        "feature_version": GNN_FEATURE_VERSION,
        "accepted_model": best_name if accepted else "",
        "accepted_reason": reason,
        "baseline_mae": args.baseline_mae,
        "train_rows": int(len(prepared.train_frame)),
        "validation_rows": int(len(prepared.validation_frame)),
        "graph_config": vars(graph_config),
        "train_edge_counts": train_graph.edge_counts,
        "validation_edge_counts": validation_graph.edge_counts,
        "results": results,
    }
    (args.output_dir / GNN_TRAINING_REPORT_NAME).write_text(json.dumps(json_safe(report), indent=2), encoding="utf-8")

    if accepted and best_payload is not None:
        torch.save(best_payload["state_dict"], args.output_dir / GNN_MODEL_NAME)
        np.savez_compressed(
            args.output_dir / GNN_GRAPH_STORE_NAME,
            train_features=prepared.train_features.astype(np.float32),
            train_lat=prepared.train_frame["lat"].to_numpy(dtype=np.float32),
            train_lon=prepared.train_frame["lon"].to_numpy(dtype=np.float32),
            train_catboost_price=prepared.train_frame[CATBOOST_PREDICTION_COLUMN].to_numpy(dtype=np.float32),
            train_target=prepared.train_frame[TARGET_COLUMN].to_numpy(dtype=np.float32),
            train_district=prepared.train_frame["district"].astype(str).to_numpy(),
            train_sub_location=prepared.train_frame["sub_location"].astype(str).to_numpy(),
            train_quality=prepared.train_frame["house_quality_tier"].astype(str).to_numpy(),
            train_posted_year=prepared.train_frame["posted_year"].to_numpy(dtype=np.int32),
            train_posted_month=prepared.train_frame["posted_month"].to_numpy(dtype=np.int32),
        )
        metadata = {
            "model_variant": GNN_MODEL_VARIANT,
            "feature_version": GNN_FEATURE_VERSION,
            "prediction_mode": best_payload["prediction_mode"],
            "model_config": best_payload["model_config"],
            "feature_state": feature_state_to_dict(prepared.feature_state),
            "graph_config": vars(graph_config),
            "imputable_numeric_columns": IMPUTABLE_NUMERIC_COLUMNS,
            "imputable_binary_columns": IMPUTABLE_BINARY_COLUMNS,
            "imputable_categorical_columns": IMPUTABLE_CATEGORICAL_COLUMNS,
            "training_report": GNN_TRAINING_REPORT_NAME,
            "metrics": best_payload["result"],
        }
        (args.output_dir / GNN_METADATA_NAME).write_text(json.dumps(json_safe(metadata), indent=2), encoding="utf-8")

    print(json.dumps(json_safe(report), indent=2))
    return 0


def train_variant(torch, model, tensors, weights, prediction_mode: str, args, multitask_loss):
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    best_state = None
    best_result = None
    best_mae = float("inf")
    patience_remaining = args.patience

    for _epoch in range(args.epochs):
        model.train()
        optimizer.zero_grad()
        outputs = model(tensors["train_x"], tensors["train_edge_index"], tensors["train_edge_attr"])
        losses = multitask_loss(
            outputs=outputs,
            residual_target=tensors["train_residual"],
            standalone_target=tensors["train_log_target"],
            numeric_target=tensors["train_numeric_target"],
            binary_target=tensors["train_binary_target"],
            categorical_target=tensors["train_categorical_target"],
            imputation_mask=tensors["train_imputation_mask"],
            weights=weights,
        )
        losses["total"].backward()
        optimizer.step()

        result = evaluate_variant(torch, model, tensors, prediction_mode)
        mae = result["validation"]["mae"]
        if mae < best_mae:
            best_mae = mae
            best_result = result
            best_state = copy.deepcopy(model.state_dict())
            patience_remaining = args.patience
        else:
            patience_remaining -= 1
            if patience_remaining <= 0:
                break

    return best_result, best_state


def evaluate_variant(torch, model, tensors, prediction_mode: str) -> Dict[str, Any]:
    model.eval()
    with torch.no_grad():
        train_outputs = model(tensors["train_x_eval"], tensors["train_edge_index"], tensors["train_edge_attr"])
        validation_outputs = model(tensors["validation_x_eval"], tensors["validation_edge_index"], tensors["validation_edge_attr"])
        validation_masked_outputs = model(tensors["validation_x"], tensors["validation_edge_index"], tensors["validation_edge_attr"])

    train_prediction = prediction_from_outputs(torch, train_outputs, tensors["train_base_price"], prediction_mode)
    validation_prediction = prediction_from_outputs(torch, validation_outputs, tensors["validation_base_price"], prediction_mode)
    validation_numeric = validation_masked_outputs["numeric_imputation"].detach().cpu().numpy()

    return {
        "train": regression_metrics(tensors["train_target_np"], train_prediction),
        "validation": regression_metrics(tensors["validation_target_np"], validation_prediction),
        "imputation": imputation_metrics(tensors["validation_numeric_target_np"], validation_numeric),
    }


def prediction_from_outputs(torch, outputs, base_price, prediction_mode: str) -> np.ndarray:
    if prediction_mode == "standalone":
        return np.maximum(np.expm1(outputs["standalone_log_price"].detach().cpu().numpy()), 1.0)
    residual = outputs["residual_log_price"].detach().cpu().numpy()
    return final_price_per_sqft(base_price.detach().cpu().numpy(), residual)


def build_tensors(
    torch,
    train_frame,
    validation_frame,
    train_features,
    validation_features,
    train_graph,
    validation_graph,
    train_imputation_mask,
    validation_imputation_mask,
    feature_state,
    device,
) -> Dict[str, Any]:
    train_numeric, train_binary, train_categorical = imputation_target_arrays(train_frame, feature_state)
    validation_numeric, validation_binary, validation_categorical = imputation_target_arrays(validation_frame, feature_state)

    return {
        "train_x": tensor(torch, train_features, device),
        "train_x_eval": tensor(torch, transform_node_features(train_frame, feature_state), device),
        "validation_x": tensor(torch, validation_features, device),
        "validation_x_eval": tensor(torch, transform_node_features(validation_frame, feature_state), device),
        "train_edge_index": torch.as_tensor(train_graph.edge_index, dtype=torch.long, device=device),
        "train_edge_attr": tensor(torch, train_graph.edge_attr, device),
        "validation_edge_index": torch.as_tensor(validation_graph.edge_index, dtype=torch.long, device=device),
        "validation_edge_attr": tensor(torch, validation_graph.edge_attr, device),
        "train_residual": tensor(torch, train_frame[RESIDUAL_TARGET_COLUMN].to_numpy(dtype=np.float32), device),
        "validation_residual": tensor(torch, validation_frame[RESIDUAL_TARGET_COLUMN].to_numpy(dtype=np.float32), device),
        "train_log_target": tensor(torch, train_frame[LOG_TARGET_COLUMN].to_numpy(dtype=np.float32), device),
        "validation_log_target": tensor(torch, validation_frame[LOG_TARGET_COLUMN].to_numpy(dtype=np.float32), device),
        "train_base_price": tensor(torch, train_frame[CATBOOST_PREDICTION_COLUMN].to_numpy(dtype=np.float32), device),
        "validation_base_price": tensor(torch, validation_frame[CATBOOST_PREDICTION_COLUMN].to_numpy(dtype=np.float32), device),
        "train_numeric_target": tensor(torch, train_numeric, device),
        "validation_numeric_target": tensor(torch, validation_numeric, device),
        "train_binary_target": tensor(torch, train_binary, device),
        "validation_binary_target": tensor(torch, validation_binary, device),
        "train_categorical_target": torch.as_tensor(train_categorical, dtype=torch.long, device=device),
        "validation_categorical_target": torch.as_tensor(validation_categorical, dtype=torch.long, device=device),
        "train_imputation_mask": mask_tensors(torch, train_imputation_mask, device),
        "validation_imputation_mask": mask_tensors(torch, validation_imputation_mask, device),
        "train_target_np": train_frame[TARGET_COLUMN].to_numpy(dtype=np.float32),
        "validation_target_np": validation_frame[TARGET_COLUMN].to_numpy(dtype=np.float32),
        "validation_numeric_target_np": validation_numeric,
    }


def make_masked_frame(frame, feature_state, rng, mask_rate: float):
    masked = frame.copy()
    numeric_mask = rng.random((len(frame), len(IMPUTABLE_NUMERIC_COLUMNS))) < mask_rate
    binary_mask = rng.random((len(frame), len(IMPUTABLE_BINARY_COLUMNS))) < mask_rate
    categorical_mask = rng.random((len(frame), len(IMPUTABLE_CATEGORICAL_COLUMNS))) < mask_rate

    for index, column in enumerate(IMPUTABLE_NUMERIC_COLUMNS):
        masked.loc[numeric_mask[:, index], column] = feature_state.numeric_median.get(column, 0.0)
        masked.loc[numeric_mask[:, index], f"{column}_is_missing"] = 1.0
    for index, column in enumerate(IMPUTABLE_BINARY_COLUMNS):
        masked.loc[binary_mask[:, index], column] = feature_state.binary_mode.get(column, 0.0)
        masked.loc[binary_mask[:, index], f"{column}_is_missing"] = 1.0
    for index, column in enumerate(IMPUTABLE_CATEGORICAL_COLUMNS):
        masked.loc[categorical_mask[:, index], column] = feature_state.categorical_modes.get(column, "unknown")
        masked.loc[categorical_mask[:, index], f"{column}_is_missing"] = 1.0

    return masked, {
        "numeric": numeric_mask.astype(np.float32),
        "binary": binary_mask.astype(np.float32),
        "categorical": categorical_mask.astype(np.float32),
    }


def mask_tensors(torch, mask_payload: Dict[str, np.ndarray], device):
    return {
        "numeric": tensor(torch, mask_payload["numeric"], device),
        "binary": tensor(torch, mask_payload["binary"], device),
        "categorical": tensor(torch, mask_payload["categorical"], device),
    }


def tensor(torch, values, device):
    return torch.as_tensor(values, dtype=torch.float32, device=device)


def acceptance_decision(
    results: Dict[str, Any],
    best_name: str,
    baseline_mae: float,
    baseline_mape: float,
    min_improvement: float,
) -> Tuple[bool, str]:
    best_mae = results[best_name]["validation"]["mae"]
    improvement = (baseline_mae - best_mae) / baseline_mae
    if improvement < min_improvement:
        return False, f"Best GNN model improved MAE by {improvement:.4%}, below the {min_improvement:.4%} threshold."
    if results[best_name]["validation"]["mape"] > baseline_mape:
        return False, "Best GNN model worsened validation MAPE versus enhanced CatBoost."
    return True, f"Accepted {best_name}; validation MAE improved by {improvement:.4%} over enhanced CatBoost."


def require_torch():
    try:
        import torch
        import torch.nn.functional as functional
    except ImportError as exc:
        raise ImportError("Install torch and torch-geometric before running GNN training.") from exc
    return torch, functional


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
