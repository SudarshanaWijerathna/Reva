# ml/land_service/feature_engineering.py

from geopy.distance import geodesic

from ml.land_service.geocoding import resolve as resolve_location

# ---------------------------------
# CONSTANTS
# ---------------------------------
COLOMBO_COORDS = (6.9271, 79.8612)

# ---------------------------------
# FEATURE ENGINEERING
# ---------------------------------
def derive_features(user_input: dict) -> dict:
    """
    Backend feature engineering for land price model.

    - Frontend sends ONLY human inputs
    - Backend derives spatial intelligence
    - Safe fallbacks for all optional fields
    """

    # ---------- Basic inputs ----------
    district = user_input.get("district", "").strip()
    location_text = user_input.get("location_text", "").strip()

    # ---------- Location resolution ----------
    # Resolved from the shipped gazetteer first; see ml/land_service/geocoding.py
    # for why a live geocoder is not on this path by default.
    located = resolve_location(location_text, district)
    lat, lon = located.lat, located.lon

    # The model's geo_resolution category was trained on two values only, so the
    # richer precision detail is reported separately rather than fed to the model.
    geo_res = "exact" if located.is_precise else "district_fallback"
    mpl = location_text if (location_text and located.is_precise) else (district or "Unknown")

    # ---------- Distance calculations ----------
    dist_colombo = geodesic((lat, lon), COLOMBO_COORDS).km

    near_town = bool(user_input.get("near_town", False))
    distance_to_town_m = float(user_input.get("distance_to_town_m", 0) or 0)

    distance_to_nearest_town_km = (
        distance_to_town_m / 1000
        if near_town and distance_to_town_m > 0
        else 5
    )

    # ---------- Feature dictionary ----------
    features = {
        # Core geometry
        "land_size_perches": float(user_input["land_size"]),
        "latitude": lat,
        "longitude": lon,

        # Distances
        "distance_to_colombo_km": dist_colombo,
        "distance_to_nearest_town_km": distance_to_nearest_town_km,
        "distance_to_town_mentioned_m": distance_to_town_m,
        "distance_to_town_mentioned_missing": 0 if near_town else 1,

        # City gravity & accessibility
        "city_gravity_raw": 1 / (1 + dist_colombo),
        "city_gravity_score": 1 / (1 + dist_colombo),

        "road_score_raw": 1 if user_input.get("main_road", False) else 0,
        "road_score_capped": 1 if user_input.get("main_road", False) else 0,
        "road_accessibility_score": 1 if user_input.get("main_road", False) else 0,

        "location_score": 0.6,

        # Land type (fixed – matches training)
        "land_type_Residential": 1,
        "land_type_Agricultural": 0,
        "land_type_Commercial": 0,
        "land_type_Other": 0,

        # Text mentions
        "mentions_town": 1 if near_town else 0,
        "mentions_junction": 0,
        "mentions_road": int(user_input.get("main_road", False)),
        "mentions_main_road": int(user_input.get("main_road", False)),
        "mentions_bus_road": 0,
        "mentions_highway": 0,

        # Legal & utilities
        "clear_deed": int(user_input.get("clear_deed", False)),
        "bank_loan_available": int(user_input.get("bank_loan", False)),
        "electricity_available": int(user_input.get("electricity", False)),
        "water_available": int(user_input.get("water", False)),

        # Text classification flags
        "is_residential_text": 1,
        "is_commercial_text": 0,
        "is_estate_land": 0,
        "is_agricultural_land": 0,
        "is_water_front": 0,

        # Categoricals (IMPORTANT: exact names)
        "district": district,
        "most_possible_location": mpl,
        "geo_resolution": geo_res,
    }

    return features


def derive_features_with_geo(user_input: dict) -> tuple[dict, dict]:
    """``derive_features`` plus the location provenance, for API responses."""
    located = resolve_location(user_input.get("location_text"), user_input.get("district"))
    return derive_features(user_input), located.as_dict()
