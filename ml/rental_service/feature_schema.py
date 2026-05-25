TARGET_COLUMN = "monthly_rent_lkr"
TRANSFORMED_TARGET_COLUMN = "log_monthly_rent_lkr"

CATEGORICAL_COLUMNS = [
    "property_type",
    "district",
    "location",
    "furnishing_status",
    "source",
]

NUMERIC_COLUMNS = [
    "bedrooms",
    "bathrooms",
    "floor_area_sqft",
    "land_perches",
    "floor_number",
    "car_parking_spaces",
    "deposit_months",
    "advance_months",
    "lease_term_months",
    "posted_year",
    "posted_month",
    "amenity_count",
]

AMENITY_COLUMNS = [
    "amenity_24_hour_security",
    "amenity_3_phase_electricity",
    "amenity_ac_rooms",
    "amenity_attached_toilets",
    "amenity_backup_generator",
    "amenity_balcony",
    "amenity_bbq_area",
    "amenity_beachfront_sea_view",
    "amenity_brand_new",
    "amenity_business_center",
    "amenity_cable_sat_tv",
    "amenity_cafe_restaurant",
    "amenity_central_ac",
    "amenity_club_house",
    "amenity_fiber_internet",
    "amenity_fire_detection",
    "amenity_fully_furnished",
    "amenity_garage",
    "amenity_garbage_removal",
    "amenity_gated_community",
    "amenity_gym",
    "amenity_home_security_system",
    "amenity_hot_water",
    "amenity_internet",
    "amenity_jogging_track",
    "amenity_kids_play_area",
    "amenity_laundry",
    "amenity_lawn_garden",
    "amenity_lifts",
    "amenity_luxury_specs",
    "amenity_maids_room",
    "amenity_maids_toilet",
    "amenity_on_site_parking",
    "amenity_outdoor_garden",
    "amenity_overhead_water_storage",
    "amenity_pet_friendly",
    "amenity_private_entrance",
    "amenity_private_pool",
    "amenity_roof_top_garden",
    "amenity_separate_kitchen",
    "amenity_serviced_apartment",
    "amenity_sport_facilities",
    "amenity_swimming_pool",
    "amenity_waterfront_riverside",
]

ANOMALY_FLAG_COLUMNS = [
    "flag_missing_price",
    "flag_impossible_price",
    "flag_extreme_price",
    "flag_impossible_area",
    "flag_extreme_area",
    "flag_impossible_land",
    "flag_extreme_land",
    "flag_impossible_rooms",
    "flag_non_rental_listing",
    "flag_duplicate_exact",
    "flag_duplicate_identifier",
    "flag_duplicate_near",
]

TRAINING_FEATURE_COLUMNS = (
    CATEGORICAL_COLUMNS
    + NUMERIC_COLUMNS
    + AMENITY_COLUMNS
    + [
        "is_short_term",
        "has_description",
        "description_length",
        "feature_anomaly_count",
    ]
)

FEATURE_OUTPUT_COLUMNS = [
    TARGET_COLUMN,
    TRANSFORMED_TARGET_COLUMN,
    *TRAINING_FEATURE_COLUMNS,
]

SCHEMA_VERSION = "rental_features_v1"
