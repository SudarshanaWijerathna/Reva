from ml.house_service.description_features import DESCRIPTION_FEATURES
from ml.house_service.feature_schema import BASELINE_FEATURES


GNN_MODEL_VARIANT = "house_catboost_gnn_residual_v1"
GNN_FEATURE_VERSION = "house_gnn_v1"

GNN_MODEL_NAME = "house_gnn_residual_model.pt"
GNN_METADATA_NAME = "house_gnn_residual_metadata.json"
GNN_GRAPH_STORE_NAME = "house_gnn_graph_store.npz"
GNN_TRAINING_REPORT_NAME = "house_gnn_training_report.json"

CATBOOST_PREDICTION_COLUMN = "catboost_pred_price_per_sqft"
LOG_CATBOOST_PREDICTION_COLUMN = "log_catboost_pred_price_per_sqft"
TARGET_COLUMN = "price_per_sqft_capped"
LOG_TARGET_COLUMN = "log_price_per_sqft_capped"
RESIDUAL_TARGET_COLUMN = "log_price_residual"

REQUIRED_ANCHOR_COLUMNS = [
    "house_sqft_capped",
    "lat",
    "lon",
    "district",
    "sub_location",
    "posted_year",
    "posted_month",
]

IMPUTABLE_NUMERIC_COLUMNS = [
    "land_sqft_capped",
    "bedrooms",
    "bathrooms",
    "road_width_ft",
    "parking_spaces",
    "distance_to_town_km",
    "distance_to_hospital_km",
    "distance_to_school_km",
    "distance_to_supermarket_km",
    "distance_to_bus_or_rail_km",
    "utility_score",
    "road_access_score",
    "service_access_score",
    "quality_score",
    "description_value_index",
]

IMPUTABLE_BINARY_COLUMNS = [
    "mentions_main_road",
    "mentions_carpet_road",
    "mentions_private_lane",
    "water_available",
    "electricity_available",
    "solar_power_available",
    "hot_water_available",
    "brand_new",
    "fully_furnished",
    "air_conditioned",
    "cctv",
    "servant_room",
    "pantry",
    "garden",
    "mentions_school",
    "mentions_hospital",
    "mentions_supermarket",
    "mentions_bank",
    "mentions_highway",
    "mentions_junction",
]

IMPUTABLE_CATEGORICAL_COLUMNS = ["house_quality_tier"]

MISSING_MASK_COLUMNS = [
    f"{column}_is_missing"
    for column in IMPUTABLE_NUMERIC_COLUMNS + IMPUTABLE_BINARY_COLUMNS + IMPUTABLE_CATEGORICAL_COLUMNS
]

GNN_NODE_FEATURES = (
    BASELINE_FEATURES
    + DESCRIPTION_FEATURES
    + [CATBOOST_PREDICTION_COLUMN, LOG_CATBOOST_PREDICTION_COLUMN]
    + MISSING_MASK_COLUMNS
)

EDGE_ATTR_COLUMNS = [
    "distance_km",
    "cosine_similarity",
    "edge_type",
    "same_district",
    "same_sub_location",
    "time_delta_months",
    "same_quality_tier",
]

EDGE_TYPE_SPATIAL = 0.0
EDGE_TYPE_FEATURE = 1.0
EDGE_TYPE_LOCATION = 2.0
EDGE_TYPE_SELF = 3.0
