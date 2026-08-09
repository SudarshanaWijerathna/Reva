from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from ml.house_service.gnn.schema import (
    EDGE_ATTR_COLUMNS,
    EDGE_TYPE_FEATURE,
    EDGE_TYPE_LOCATION,
    EDGE_TYPE_SELF,
    EDGE_TYPE_SPATIAL,
)


@dataclass(frozen=True)
class GraphBuildConfig:
    spatial_k: int = 16
    feature_k: int = 16
    location_k: int = 8
    query_multiplier: int = 4


@dataclass
class GraphBundle:
    edge_index: np.ndarray
    edge_attr: np.ndarray
    edge_counts: Dict[str, int]


def build_property_graph(
    frame: pd.DataFrame,
    feature_matrix: np.ndarray,
    config: GraphBuildConfig | None = None,
) -> GraphBundle:
    config = config or GraphBuildConfig()
    node_count = len(frame)
    if node_count == 0:
        return GraphBundle(
            edge_index=np.empty((2, 0), dtype=np.int64),
            edge_attr=np.empty((0, len(EDGE_ATTR_COLUMNS)), dtype=np.float32),
            edge_counts={"spatial": 0, "feature": 0, "location": 0, "self": 0},
        )

    features = _safe_float_matrix(feature_matrix)
    projected_coords = project_coordinates_km(frame["lat"].to_numpy(), frame["lon"].to_numpy())
    normalized_features = _l2_normalize(_standardize(features))

    edge_attrs: Dict[Tuple[int, int], np.ndarray] = {}
    edge_counts = {"spatial": 0, "feature": 0, "location": 0, "self": 0}

    _add_spatial_edges(frame, projected_coords, edge_attrs, edge_counts, config)
    _add_feature_edges(frame, normalized_features, projected_coords, edge_attrs, edge_counts, config)
    _add_location_edges(frame, normalized_features, projected_coords, edge_attrs, edge_counts, config)
    _add_self_loops(node_count, edge_attrs, edge_counts)

    if not edge_attrs:
        return GraphBundle(
            edge_index=np.empty((2, 0), dtype=np.int64),
            edge_attr=np.empty((0, len(EDGE_ATTR_COLUMNS)), dtype=np.float32),
            edge_counts=edge_counts,
        )

    ordered_edges = sorted(edge_attrs)
    edge_index = np.asarray(ordered_edges, dtype=np.int64).T
    edge_attr = np.vstack([edge_attrs[edge] for edge in ordered_edges]).astype(np.float32)
    return GraphBundle(edge_index=edge_index, edge_attr=edge_attr, edge_counts=edge_counts)


def build_query_edges(
    train_frame: pd.DataFrame,
    train_feature_matrix: np.ndarray,
    query_row: pd.Series,
    query_features: np.ndarray,
    config: GraphBuildConfig | None = None,
) -> GraphBundle:
    config = config or GraphBuildConfig()
    query_frame = pd.concat([train_frame, query_row.to_frame().T], ignore_index=True)
    feature_matrix = np.vstack([train_feature_matrix, query_features.reshape(1, -1)])
    query_index = len(query_frame) - 1

    projected_coords = project_coordinates_km(query_frame["lat"].to_numpy(), query_frame["lon"].to_numpy())
    normalized_features = _l2_normalize(_standardize(_safe_float_matrix(feature_matrix)))

    edge_attrs: Dict[Tuple[int, int], np.ndarray] = {}
    edge_counts = {"spatial": 0, "feature": 0, "location": 0, "self": 0}

    _add_query_knn_edges(
        query_frame,
        projected_coords,
        normalized_features,
        query_index,
        edge_attrs,
        edge_counts,
        config,
    )
    _add_directed_edge(
        query_frame,
        projected_coords,
        normalized_features,
        query_index,
        query_index,
        EDGE_TYPE_SELF,
        edge_attrs,
    )
    edge_counts["self"] += 1

    ordered_edges = sorted(edge_attrs)
    edge_index = np.asarray(ordered_edges, dtype=np.int64).T
    edge_attr = np.vstack([edge_attrs[edge] for edge in ordered_edges]).astype(np.float32)
    return GraphBundle(edge_index=edge_index, edge_attr=edge_attr, edge_counts=edge_counts)


def project_coordinates_km(latitudes: Iterable[float], longitudes: Iterable[float]) -> np.ndarray:
    lat = np.asarray(latitudes, dtype=float)
    lon = np.asarray(longitudes, dtype=float)
    lat0 = np.deg2rad(np.nanmean(lat)) if len(lat) else 0.0
    x = lon * 111.320 * np.cos(lat0)
    y = lat * 110.574
    return np.column_stack([x, y]).astype(np.float32)


def edge_leakage_count(edge_index: np.ndarray, train_mask: np.ndarray, validation_mask: np.ndarray) -> int:
    if edge_index.size == 0:
        return 0
    source_is_train = train_mask[edge_index[0]]
    target_is_train = train_mask[edge_index[1]]
    source_is_validation = validation_mask[edge_index[0]]
    target_is_validation = validation_mask[edge_index[1]]
    cross_split = (source_is_train & target_is_validation) | (source_is_validation & target_is_train)
    return int(np.count_nonzero(cross_split))


def _add_spatial_edges(
    frame: pd.DataFrame,
    projected_coords: np.ndarray,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
    edge_counts: Dict[str, int],
    config: GraphBuildConfig,
) -> None:
    if len(frame) <= 1 or config.spatial_k <= 0:
        return
    tree = cKDTree(projected_coords)
    neighbors = min(len(frame), max(config.spatial_k + 1, config.spatial_k * config.query_multiplier + 1))
    _, indices = tree.query(projected_coords, k=neighbors)
    for source, row in enumerate(np.atleast_2d(indices)):
        added = 0
        for target in row:
            target = int(target)
            if target == source:
                continue
            _add_undirected_edge(frame, projected_coords, None, source, target, EDGE_TYPE_SPATIAL, edge_attrs)
            edge_counts["spatial"] += 2
            added += 1
            if added >= config.spatial_k:
                break


def _add_feature_edges(
    frame: pd.DataFrame,
    normalized_features: np.ndarray,
    projected_coords: np.ndarray,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
    edge_counts: Dict[str, int],
    config: GraphBuildConfig,
) -> None:
    if len(frame) <= 1 or config.feature_k <= 0:
        return
    tree = cKDTree(normalized_features)
    neighbors = min(len(frame), max(config.feature_k + 1, config.feature_k * config.query_multiplier + 1))
    _, indices = tree.query(normalized_features, k=neighbors)
    for source, row in enumerate(np.atleast_2d(indices)):
        added = 0
        for target in row:
            target = int(target)
            if target == source:
                continue
            _add_undirected_edge(
                frame,
                projected_coords,
                normalized_features,
                source,
                target,
                EDGE_TYPE_FEATURE,
                edge_attrs,
            )
            edge_counts["feature"] += 2
            added += 1
            if added >= config.feature_k:
                break


def _add_location_edges(
    frame: pd.DataFrame,
    normalized_features: np.ndarray,
    projected_coords: np.ndarray,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
    edge_counts: Dict[str, int],
    config: GraphBuildConfig,
) -> None:
    if len(frame) <= 1 or config.location_k <= 0:
        return

    location_keys = _location_keys(frame)
    groups: Dict[str, List[int]] = {}
    for index, key in enumerate(location_keys):
        groups.setdefault(key, []).append(index)

    for source, key in enumerate(location_keys):
        candidates = [idx for idx in groups.get(key, []) if idx != source]
        if not candidates:
            candidates = [
                idx
                for idx, district in enumerate(frame["district"].astype(str))
                if idx != source and district == str(frame.iloc[source].get("district", "unknown"))
            ]
        if not candidates:
            continue
        candidate_distances = np.linalg.norm(projected_coords[candidates] - projected_coords[source], axis=1)
        for candidate_position in np.argsort(candidate_distances)[: config.location_k]:
            target = int(candidates[int(candidate_position)])
            _add_undirected_edge(
                frame,
                projected_coords,
                normalized_features,
                source,
                target,
                EDGE_TYPE_LOCATION,
                edge_attrs,
            )
            edge_counts["location"] += 2


def _add_query_knn_edges(
    frame: pd.DataFrame,
    projected_coords: np.ndarray,
    normalized_features: np.ndarray,
    query_index: int,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
    edge_counts: Dict[str, int],
    config: GraphBuildConfig,
) -> None:
    train_indices = np.arange(query_index)
    if len(train_indices) == 0:
        return

    spatial_distances = np.linalg.norm(projected_coords[train_indices] - projected_coords[query_index], axis=1)
    for target in train_indices[np.argsort(spatial_distances)[: config.spatial_k]]:
        _add_undirected_edge(frame, projected_coords, normalized_features, query_index, int(target), EDGE_TYPE_SPATIAL, edge_attrs)
        edge_counts["spatial"] += 2

    similarities = normalized_features[train_indices] @ normalized_features[query_index]
    for target in train_indices[np.argsort(-similarities)[: config.feature_k]]:
        _add_undirected_edge(frame, projected_coords, normalized_features, query_index, int(target), EDGE_TYPE_FEATURE, edge_attrs)
        edge_counts["feature"] += 2

    query_key = _location_keys(frame.iloc[[query_index]])[0]
    location_candidates = [
        idx
        for idx in train_indices
        if _location_keys(frame.iloc[[idx]])[0] == query_key
    ]
    if location_candidates:
        candidate_distances = np.linalg.norm(projected_coords[location_candidates] - projected_coords[query_index], axis=1)
        for target in np.asarray(location_candidates)[np.argsort(candidate_distances)[: config.location_k]]:
            _add_undirected_edge(frame, projected_coords, normalized_features, query_index, int(target), EDGE_TYPE_LOCATION, edge_attrs)
            edge_counts["location"] += 2


def _add_self_loops(
    node_count: int,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
    edge_counts: Dict[str, int],
) -> None:
    connected_nodes = {source for source, _ in edge_attrs} | {target for _, target in edge_attrs}
    for node in range(node_count):
        if node not in connected_nodes:
            edge_attrs[(node, node)] = np.array([0.0, 1.0, EDGE_TYPE_SELF, 1.0, 1.0, 0.0, 1.0], dtype=np.float32)
            edge_counts["self"] += 1


def _add_undirected_edge(
    frame: pd.DataFrame,
    projected_coords: np.ndarray,
    normalized_features: np.ndarray | None,
    source: int,
    target: int,
    edge_type: float,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
) -> None:
    _add_directed_edge(frame, projected_coords, normalized_features, source, target, edge_type, edge_attrs)
    _add_directed_edge(frame, projected_coords, normalized_features, target, source, edge_type, edge_attrs)


def _add_directed_edge(
    frame: pd.DataFrame,
    projected_coords: np.ndarray,
    normalized_features: np.ndarray | None,
    source: int,
    target: int,
    edge_type: float,
    edge_attrs: Dict[Tuple[int, int], np.ndarray],
) -> None:
    key = (int(source), int(target))
    if key in edge_attrs:
        return

    source_row = frame.iloc[source]
    target_row = frame.iloc[target]
    distance_km = float(np.linalg.norm(projected_coords[source] - projected_coords[target]))
    cosine_similarity = 0.0
    if normalized_features is not None:
        cosine_similarity = float(np.dot(normalized_features[source], normalized_features[target]))
    same_district = float(str(source_row.get("district", "")) == str(target_row.get("district", "")))
    same_sub_location = float(str(source_row.get("sub_location", "")) == str(target_row.get("sub_location", "")))
    source_month = _month_index(source_row)
    target_month = _month_index(target_row)
    time_delta_months = abs(source_month - target_month) / 48.0
    same_quality_tier = float(str(source_row.get("house_quality_tier", "")) == str(target_row.get("house_quality_tier", "")))

    edge_attrs[key] = np.array(
        [
            distance_km,
            cosine_similarity,
            edge_type,
            same_district,
            same_sub_location,
            min(time_delta_months, 1.0),
            same_quality_tier,
        ],
        dtype=np.float32,
    )


def _month_index(row: pd.Series) -> int:
    try:
        return int(row.get("posted_year", 0)) * 12 + int(row.get("posted_month", 0))
    except (TypeError, ValueError):
        return 0


def _location_keys(frame: pd.DataFrame) -> List[str]:
    district = frame.get("district", pd.Series(["unknown"] * len(frame))).fillna("unknown").astype(str)
    sub_location = frame.get("sub_location", pd.Series(["unknown"] * len(frame))).fillna("unknown").astype(str)
    quality = frame.get("house_quality_tier", pd.Series(["unknown"] * len(frame))).fillna("unknown").astype(str)
    return [f"{d}|{s}|{q}" for d, s, q in zip(district, sub_location, quality)]


def _safe_float_matrix(matrix: np.ndarray) -> np.ndarray:
    result = np.asarray(matrix, dtype=np.float32)
    return np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)


def _standardize(matrix: np.ndarray) -> np.ndarray:
    mean = matrix.mean(axis=0, keepdims=True)
    std = matrix.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return (matrix - mean) / std


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(matrix, axis=1, keepdims=True)
    norm[norm < 1e-6] = 1.0
    return matrix / norm
