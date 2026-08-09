"""
prepare_market_explorer_data.py
================================
Processes Kaggle property datasets to 3 compact, lat/lon-indexed JSONs for
the Reva Market Data Explorer frontend.

Output files (written to frontend/public/data/):
  market_land.json
  market_house.json
  market_rental.json

Each record contains enough geo + display fields for nearest-point lookup.
Run from the repository root:
  python scripts/prepare_market_explorer_data.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import ast, re, pathlib, json
import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt

# ─────────────────────────── paths ───────────────────────────
ROOT        = pathlib.Path(__file__).resolve().parent.parent
KAGGLE_DIR  = pathlib.Path(r"C:\Users\User\Desktop\Software_Project\Dataets\Kaggle")
LAND_DIR    = KAGGLE_DIR / "Land"
GEO_CSV     = ROOT / "data" / "geo" / "sri_lanka_gazetteer.csv"
OUT_DIR     = ROOT / "frontend" / "public" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────── helpers ────────────────────────
def safe_parse(s):
    """Parse a stringified dict; return {} on failure."""
    try:
        return ast.literal_eval(str(s))
    except Exception:
        return {}

def clean_price_lkr(s: str) -> float | None:
    """Extract numeric LKR value from strings like 'Rs 55,000,000'."""
    if pd.isna(s):
        return None
    s = str(s).upper().replace(",", "").strip()
    m = re.search(r"[\d.]+", s)
    if not m:
        return None
    val = float(m.group())
    return val if val > 0 else None

def clean_size(s) -> float | None:
    """Parse '3,000.0 sqft' or '27.5 perches' → numeric."""
    if pd.isna(s):
        return None
    s = str(s).replace(",", "").strip()
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None

# ─────────── geo lookup gazetteer ───────────────────────────
geo_df = pd.read_csv(GEO_CSV, encoding="utf-8")
geo_df = geo_df.dropna(subset=["lat", "lon"])

DISTRICT_LAT_LON = {
    row["district"].lower(): (float(row["lat"]), float(row["lon"]))
    for _, row in geo_df.iterrows()
    if row.get("precision") == "district_centroid"
}

LOCATION_TO_LAT_LON = {}
for _, row in geo_df.iterrows():
    loc = str(row.get("location", "")).strip().lower()
    if loc and not pd.isna(row["lat"]):
        LOCATION_TO_LAT_LON[loc] = (float(row["lat"]), float(row["lon"]))

# Build location key from district+location
def resolve_lat_lon(location: str, district: str) -> tuple[float, float] | None:
    loc_key = str(location).strip().lower()
    dist_key = str(district).strip().lower()
    if loc_key in LOCATION_TO_LAT_LON:
        return LOCATION_TO_LAT_LON[loc_key]
    # fuzzy: check if any gazetteer location is a substring
    for key, coords in LOCATION_TO_LAT_LON.items():
        if key in loc_key or loc_key in key:
            return coords
    if dist_key in DISTRICT_LAT_LON:
        return DISTRICT_LAT_LON[dist_key]
    return None

def geo_region_to_district(geo_region: str, area) -> str:
    """Convert geo_region (e.g., LK-11) to district name."""
    mapping = {
        "LK-11": "Colombo",
        "LK-12": "Gampaha",
        "LK-13": "Kalutara",
        "LK-21": "Kandy",
        "LK-22": "Matale",
        "LK-23": "Nuwara Eliya",
        "LK-31": "Galle",
        "LK-32": "Matara",
        "LK-33": "Hambantota",
        "LK-41": "Jaffna",
        "LK-45": "Mullaitivu",
        "LK-42": "Kilinochchi",
        "LK-44": "Vavuniya",
        "LK-43": "Mannar",
        "LK-52": "Batticaloa",
        "LK-53": "Ampara",
        "LK-51": "Trincomalee",
        "LK-61": "Kurunegala",
        "LK-62": "Puttalam",
        "LK-71": "Anuradhapura",
        "LK-72": "Polonnaruwa",
        "LK-81": "Badulla",
        "LK-82": "Monaragala",
        "LK-91": "Ratnapura",
        "LK-92": "Kegalle",
    }
    if isinstance(area, dict) and "name" in area:
        return area["name"]
    return mapping.get(str(geo_region).strip(), "Unknown")

def derive_district(row) -> str:
    area = safe_parse(row.get("area", "{}"))
    return geo_region_to_district(row.get("geo_region", ""), area)

# ─────────────────────────────────────────────────────────────
# 1. LAND DATASET
# ─────────────────────────────────────────────────────────────
print("Processing LAND dataset...")
land_raw = pd.read_csv(
    LAND_DIR / "land_properties_with_locations.csv",
    encoding="utf-8", on_bad_lines="skip"
)

def land_type_label(row) -> str:
    types = []
    if row.get("land_type_Residential", False):  types.append("Residential")
    if row.get("land_type_Commercial", False):    types.append("Commercial")
    if row.get("land_type_Agricultural", False):  types.append("Agricultural")
    if row.get("land_type_Other", False):         types.append("Other")
    return " / ".join(types) if types else "Residential"

# Filter: valid price, lat, lon
land = land_raw.dropna(subset=["price_per_perch_LKR", "latitude", "longitude"]).copy()
land = land[land["price_per_perch_LKR"] > 0]

# Remove outliers: IQR
q1, q3 = land["price_per_perch_LKR"].quantile([0.02, 0.98])
land = land[(land["price_per_perch_LKR"] >= q1) & (land["price_per_perch_LKR"] <= q3)]
land = land.dropna(subset=["land_size_perches"])
land = land[land["land_size_perches"] > 0]

# Access road — not in raw data; derive a heuristic badge
def access_road_guess(loc: str, district: str) -> str:
    loc_lower = str(loc).lower()
    if any(k in loc_lower for k in ["colombo", "nugegoda", "rajagiriya", "kotte", "dehiwala"]):
        return "Main Road Access"
    if any(k in loc_lower for k in ["gampaha", "negombo", "kandy", "galle"]):
        return "Paved Road Access"
    return "Gravel / Access Road"

def dataset_source(geo_res: str) -> str:
    return "Ikman.lk (Verified)" if str(geo_res).strip() == "exact" else "Ikman.lk (Approx)"

land_records = []
for _, row in land.iterrows():
    ltype = land_type_label(row)
    date_str = str(row.get("posted_date", "")).strip()
    try:
        dt = pd.to_datetime(date_str, dayfirst=False)
        date_label = dt.strftime("%Y-%m")
    except Exception:
        date_label = "2024-01"
    
    location_name = str(row.get("location", row.get("most_possible_location", ""))).strip().title()
    district = str(row.get("district", "Unknown")).strip().title()
    
    land_records.append({
        "lat": float(row["latitude"]),
        "lon": float(row["longitude"]),
        "location": location_name,
        "district": district,
        "province": str(row.get("province", "")).strip().title(),
        "price_per_perch": int(round(row["price_per_perch_LKR"])),
        "land_size_perches": float(row["land_size_perches"]),
        "land_type": ltype,
        "date_listed": date_label,
        "dataset_source": dataset_source(row.get("geo_resolution", "")),
        "access_road": access_road_guess(row.get("location", ""), district),
        "badge": "VERIFIED" if str(row.get("geo_resolution", "")).strip() == "exact" else "AVAILABLE",
    })

land_df = pd.DataFrame(land_records)
land_df = land_df.drop_duplicates(subset=["lat", "lon", "price_per_perch"])
print(f"  Land records: {len(land_df)}")
land_df.to_json(OUT_DIR / "market_land.json", orient="records", indent=None)
print(f"  Saved -> {OUT_DIR / 'market_land.json'}")


# ─────────────────────────────────────────────────────────────
# 2. HOUSE SALE DATASET
# ─────────────────────────────────────────────────────────────
print("Processing HOUSE dataset...")
house_raw = pd.read_csv(
    KAGGLE_DIR / "houses_for_sale_properties.csv",
    encoding="utf-8", on_bad_lines="skip"
)

house_records = []
for _, row in house_raw.iterrows():
    props = safe_parse(row.get("properties", "{}"))
    price_lkr = clean_price_lkr(row.get("price", ""))
    if price_lkr is None or price_lkr < 1_000_000:
        continue

    bedrooms   = int(clean_size(props.get("Bedrooms")) or 0)
    bathrooms  = int(clean_size(props.get("Bathrooms")) or 0)
    house_sqft = clean_size(props.get("House size"))
    land_perch = clean_size(props.get("Land size"))

    if not house_sqft or not land_perch or bedrooms == 0:
        continue

    # Compute price per sqft
    price_per_sqft = round(price_lkr / house_sqft) if house_sqft else None

    district = derive_district(row)
    location = str(row.get("location", "")).strip().title()

    coords = resolve_lat_lon(location, district)
    if coords is None:
        continue

    date_str = str(row.get("posted_date", "")).strip()
    try:
        dt = pd.to_datetime(date_str, dayfirst=True)
        date_label = dt.strftime("%Y-%m")
    except Exception:
        date_label = "2024-01"

    furnishing_keywords = {
        "furnished": ["fully furnished", "air conditioned", "fully furnished"],
        "semi-furnished": ["semi furnished", "semi-furnished", "partiallyf"],
        "unfurnished": [],
    }
    ad = str(row.get("ad_description", "")).lower()
    furnishing = "Unfurnished"
    if any(k in ad for k in ["fully furnished", "fully-furnished"]):
        furnishing = "Fully Furnished"
    elif any(k in ad for k in ["semi furnished", "semi-furnished"]):
        furnishing = "Semi-Furnished"

    house_records.append({
        "lat": coords[0],
        "lon": coords[1],
        "location": location,
        "district": district,
        "price_lkr": int(price_lkr),
        "price_per_sqft": price_per_sqft,
        "house_sqft": int(house_sqft),
        "land_perches": land_perch,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "furnishing": furnishing,
        "date_listed": date_label,
        "badge": "VERIFIED" if row.get("is_verified") else "AVAILABLE",
    })

house_df = pd.DataFrame(house_records)
# Remove price outliers
q1_h, q3_h = house_df["price_lkr"].quantile([0.02, 0.98])
house_df = house_df[(house_df["price_lkr"] >= q1_h) & (house_df["price_lkr"] <= q3_h)]
house_df = house_df.drop_duplicates(subset=["lat", "lon", "price_lkr", "house_sqft"])
print(f"  House records: {len(house_df)}")
house_df.to_json(OUT_DIR / "market_house.json", orient="records", indent=None)
print(f"  Saved -> {OUT_DIR / 'market_house.json'}")


# ─────────────────────────────────────────────────────────────
# 3. RENTAL DATASET  (apartment + house rentals combined)
# ─────────────────────────────────────────────────────────────
print("Processing RENTAL dataset...")
rental_apt   = pd.read_csv(KAGGLE_DIR / "apartment_rentals_properties.csv",  encoding="utf-8", on_bad_lines="skip")
rental_house = pd.read_csv(KAGGLE_DIR / "house_rentals_properties.csv", encoding="utf-8", on_bad_lines="skip")
rental_apt["prop_type"]   = "Apartment"
rental_house["prop_type"] = "House"
rental_raw = pd.concat([rental_apt, rental_house], ignore_index=True)

def detect_lease_term(price_str: str) -> str:
    s = str(price_str).lower()
    if "day" in s:
        return "Short-Term (Daily)"
    if "week" in s:
        return "Short-Term (Weekly)"
    return "Long-Term (Monthly)"

rental_records = []
for _, row in rental_raw.iterrows():
    props = safe_parse(row.get("properties", "{}"))
    price_lkr = clean_price_lkr(row.get("price", ""))
    if price_lkr is None or price_lkr < 10_000:
        continue

    prop_type = row.get("prop_type", "House")
    beds   = int(clean_size(props.get("Beds") or props.get("Bedrooms")) or 0)
    baths  = int(clean_size(props.get("Baths") or props.get("Bathrooms")) or 0)
    sqft   = clean_size(props.get("Size") or props.get("House size"))

    if beds == 0 and not sqft:
        continue

    district = derive_district(row)
    location = str(row.get("location", "")).strip().title()
    coords = resolve_lat_lon(location, district)
    if coords is None:
        continue

    date_str = str(row.get("posted_date", "")).strip()
    try:
        dt = pd.to_datetime(date_str, dayfirst=True)
        date_label = dt.strftime("%Y-%m")
    except Exception:
        date_label = "2024-01"

    lease_term = detect_lease_term(row.get("price", ""))

    rental_records.append({
        "lat": coords[0],
        "lon": coords[1],
        "location": location,
        "district": district,
        "monthly_rent_lkr": int(price_lkr),
        "property_type": prop_type,
        "floor_area_sqft": int(sqft) if sqft else None,
        "bedrooms": beds,
        "bathrooms": baths,
        "lease_term": lease_term,
        "date_listed": date_label,
        "badge": "AVAILABLE" if row.get("is_verified") else "NEW",
    })

rental_df = pd.DataFrame(rental_records)
# Remove extreme outliers
q1_r, q3_r = rental_df["monthly_rent_lkr"].quantile([0.01, 0.99])
rental_df = rental_df[(rental_df["monthly_rent_lkr"] >= q1_r) & (rental_df["monthly_rent_lkr"] <= q3_r)]
rental_df = rental_df.drop_duplicates(subset=["lat", "lon", "monthly_rent_lkr", "bedrooms"])
print(f"  Rental records: {len(rental_df)}")
rental_df.to_json(OUT_DIR / "market_rental.json", orient="records", indent=None)
print(f"  Saved -> {OUT_DIR / 'market_rental.json'}")

print("All 3 market datasets created in", OUT_DIR)
print(f"   Land:   {len(land_df):,} records")
print(f"   House:  {len(house_df):,} records")
print(f"   Rental: {len(rental_df):,} records")
