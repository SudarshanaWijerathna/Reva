import argparse
import ast
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.rental_service.feature_schema import (  # noqa: E402
    AMENITY_COLUMNS,
    ANOMALY_FLAG_COLUMNS,
    CATEGORICAL_COLUMNS,
    FEATURE_OUTPUT_COLUMNS,
    NUMERIC_COLUMNS,
    SCHEMA_VERSION,
    TARGET_COLUMN,
    TRANSFORMED_TARGET_COLUMN,
)


DEFAULT_INPUT_DIR = REPO_ROOT / "data" / "rental dataset"
DEFAULT_PROCESSED_PATH = REPO_ROOT / "data" / "processed" / "rental_cleaned.csv"
DEFAULT_FEATURES_PATH = REPO_ROOT / "data" / "features" / "rental_features_v1.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "reports" / "rental_data_quality_report.json"
LEGACY_COMBINED_NAME = "RentalDetails_Combined_Model_Ready (2).csv"

IKMAN_CATEGORY_FILES = [
    "apartment_rentals_properties.csv",
    "house_rentals_properties.csv",
    "commercial_property_rentals_properties.csv",
    "room_&_annex_rentals_properties.csv",
]
IKMAN_2026_FILE = "ikman_rentals_2026.csv"
LANKA_PROPERTY_WEB_FILE = "rental_details_lankapropertyweb.csv"

UNKNOWN = "unknown"

CANONICAL_COLUMNS = [
    "record_id",
    "source",
    "source_file",
    "listing_id",
    "listing_url",
    "title",
    "property_type",
    "location",
    "district",
    "monthly_rent_lkr",
    "bedrooms",
    "bathrooms",
    "floor_area_sqft",
    "land_perches",
    "floor_number",
    "car_parking_spaces",
    "furnishing_status",
    "short_term",
    "deposit_months",
    "advance_months",
    "lease_term_months",
    "posted_date",
    "posted_year",
    "posted_month",
    "description",
    *AMENITY_COLUMNS,
    "amenity_count",
    *ANOMALY_FLAG_COLUMNS,
    "anomaly_flags",
    "is_training_excluded",
    "exclusion_reason",
]

FEATURE_COLUMNS = [
    "record_id",
    "source_file",
    "listing_id",
    *FEATURE_OUTPUT_COLUMNS,
]

AMENITY_ALIASES = {
    "24 HOUR SECURITY": "amenity_24_hour_security",
    "24 HOURS SECURITY": "amenity_24_hour_security",
    "3 PHASE ELECTRICITY": "amenity_3_phase_electricity",
    "AC ROOMS": "amenity_ac_rooms",
    "AIR CONDITIONING": "amenity_ac_rooms",
    "A/C": "amenity_ac_rooms",
    "ATTACHED TOILETS": "amenity_attached_toilets",
    "ATTACHED BATHROOM": "amenity_attached_toilets",
    "BACKUP GENERATOR": "amenity_backup_generator",
    "GENERATOR": "amenity_backup_generator",
    "BALCONY": "amenity_balcony",
    "BALCONIES": "amenity_balcony",
    "BBQ AREA": "amenity_bbq_area",
    "BEACHFRONT / SEA VIEW": "amenity_beachfront_sea_view",
    "SEA VIEW": "amenity_beachfront_sea_view",
    "BRAND NEW": "amenity_brand_new",
    "BUSINESS CENTER": "amenity_business_center",
    "CABLE/SAT TV": "amenity_cable_sat_tv",
    "CABLE TV": "amenity_cable_sat_tv",
    "SAT TV": "amenity_cable_sat_tv",
    "CAFE / RESTAURANT": "amenity_cafe_restaurant",
    "RESTAURANT": "amenity_cafe_restaurant",
    "CENTRAL AC": "amenity_central_ac",
    "CLUB HOUSE": "amenity_club_house",
    "FIBER INTERNET": "amenity_fiber_internet",
    "FIBRE INTERNET": "amenity_fiber_internet",
    "FIRE DETECTION": "amenity_fire_detection",
    "FULLY FURNISHED": "amenity_fully_furnished",
    "GARAGE": "amenity_garage",
    "CAR PORCH": "amenity_garage",
    "GARBAGE REMOVAL": "amenity_garbage_removal",
    "GATED COMMUNITY": "amenity_gated_community",
    "GYM": "amenity_gym",
    "HOME SECURITY SYSTEM": "amenity_home_security_system",
    "CCTV": "amenity_home_security_system",
    "HOT WATER": "amenity_hot_water",
    "INTERNET": "amenity_internet",
    "JOGGING TRACK": "amenity_jogging_track",
    "KIDS PLAY AREA": "amenity_kids_play_area",
    "LAUNDRY": "amenity_laundry",
    "LAWN GARDEN": "amenity_lawn_garden",
    "GARDEN": "amenity_lawn_garden",
    "LIFTS": "amenity_lifts",
    "ELEVATOR": "amenity_lifts",
    "LUXURY SPECS": "amenity_luxury_specs",
    "LUXURY": "amenity_luxury_specs",
    "MAID'S ROOM": "amenity_maids_room",
    "MAIDS ROOM": "amenity_maids_room",
    "SERVANT ROOM": "amenity_maids_room",
    "MAID'S TOILET": "amenity_maids_toilet",
    "MAIDS TOILET": "amenity_maids_toilet",
    "SERVANT TOILET": "amenity_maids_toilet",
    "ON-SITE PARKING": "amenity_on_site_parking",
    "PARKING": "amenity_on_site_parking",
    "OUTDOOR GARDEN": "amenity_outdoor_garden",
    "OVERHEAD WATER STORAGE": "amenity_overhead_water_storage",
    "PET FRIENDLY": "amenity_pet_friendly",
    "PRIVATE ENTRANCE": "amenity_private_entrance",
    "PRIVATE POOL": "amenity_private_pool",
    "ROOF TOP GARDEN": "amenity_roof_top_garden",
    "ROOFTOP": "amenity_roof_top_garden",
    "SEPARATE KITCHEN": "amenity_separate_kitchen",
    "SERVICED APARTMENT": "amenity_serviced_apartment",
    "SPORT FACILITIES": "amenity_sport_facilities",
    "SWIMMING POOL": "amenity_swimming_pool",
    "POOL": "amenity_swimming_pool",
    "WATERFRONT / RIVERSIDE": "amenity_waterfront_riverside",
    "RIVERSIDE": "amenity_waterfront_riverside",
}

COMMERCIAL_TYPES = {
    "office space",
    "office",
    "building",
    "shop space",
    "shop",
    "warehouse",
    "warehouse / storage",
    "factory",
    "factory / workshop",
    "restaurant",
    "hotel",
    "guest house",
    "multipurpose",
    "co-working",
    "coworking",
    "business center",
    "other commercial",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and feature-engineer rental property datasets.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--processed-output", type=Path, default=DEFAULT_PROCESSED_PATH)
    parser.add_argument("--features-output", type=Path, default=DEFAULT_FEATURES_PATH)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def clean_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).replace("\ufeff", "").strip()
    if not text:
        return default
    if text.lower() in {"n/a", "na", "none", "null", "nan", "-"}:
        return default
    return re.sub(r"\s+", " ", text)


def normalized_key(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_number(value: Any) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_money_lkr(value: Any) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None
    rupee_match = re.search(r"(?:rs\.?|lkr)\s*([0-9][0-9,]*(?:\.\d+)?)", text, re.IGNORECASE)
    if rupee_match:
        return float(rupee_match.group(1).replace(",", ""))
    first_number = parse_number(text)
    return first_number


def parse_months(value: Any) -> Optional[float]:
    text = clean_text(value)
    if not text:
        return None
    number = parse_number(text)
    if number is None:
        return None
    lowered = text.lower()
    if "year" in lowered:
        return number * 12.0
    return number


def safe_parse_properties(value: Any) -> Dict[str, Any]:
    text = clean_text(value)
    if not text:
        return {}
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def parse_area_name(value: Any) -> str:
    parsed = safe_parse_properties(value)
    if parsed:
        return clean_text(parsed.get("name"), UNKNOWN) or UNKNOWN
    return clean_text(value, UNKNOWN) or UNKNOWN


def normalize_property_type(value: Any, category: Any = "", title: Any = "") -> str:
    raw = normalized_key(value)
    category_key = normalized_key(category)
    title_key = normalized_key(title)
    source = raw or category_key or title_key

    if "room annex" in category_key:
        if "annex" in source or "annexe" in source or "annexes" in source:
            return "Annex"
        if "portion" in source:
            return "Portion"
        if "room" in source:
            return "Room"
        if "apartment" in source:
            return "Apartment"
        if "house" in source:
            return "House"
        return "Room"
    if "commercial property" in category_key:
        if "office" in source:
            return "Office space"
        if "warehouse" in source or "storage" in source:
            return "Warehouse"
        if "factory" in source or "workshop" in source:
            return "Factory"
        if "shop" in source:
            return "Shop space"
        if "restaurant" in source:
            return "Restaurant"
        if "hotel" in source:
            return "Hotel"
        if "building" in source:
            return "Building"
        if "guest" in source:
            return "Guest House"
        return "Other Commercial"
    if "warehouse" in source or "storage" in source:
        return "Warehouse"
    if "apartment rental" in category_key or "apartment" in source:
        return "Apartment"
    if "house rental" in category_key or re.search(r"\bhouse\b", source):
        return "House"

    if source in {"annex", "annexe", "annexes"}:
        return "Annex"
    if source in {"co working", "coworking", "co working space"}:
        return "Coworking"
    exact = {
        "apartment": "Apartment",
        "building": "Building",
        "bungalow": "Bungalow",
        "factory": "Factory",
        "guest house": "Guest House",
        "hostel": "Hostel",
        "hotel": "Hotel",
        "house": "House",
        "multipurpose": "Multipurpose",
        "office": "Office space",
        "office space": "Office space",
        "other": "Other",
        "portion": "Portion",
        "restaurant": "Restaurant",
        "room": "Room",
        "shop": "Shop space",
        "shop space": "Shop space",
        "shopping mall": "Shopping Mall",
        "studio": "Studio",
        "villa": "Villa",
        "warehouse": "Warehouse",
        "warehouse storage": "Warehouse",
    }
    if source in exact:
        return exact[source]
    if "villa" in source:
        return "Villa"
    if "apartment" in title_key:
        return "Apartment"
    if "room" in title_key:
        return "Room"
    if "annex" in title_key or "annexe" in title_key:
        return "Annex"
    if "office" in title_key:
        return "Office space"
    return clean_text(value, "Other").title()


def normalize_furnishing(value: Any, description: Any = "") -> str:
    text = normalized_key(value)
    desc = normalized_key(description)
    combined = f"{text} {desc}"
    if not combined.strip():
        return UNKNOWN
    if "semi furnished" in combined:
        return "semi-furnished"
    if "fully furnished" in combined or combined.strip() == "furnished" or " furnished " in f" {combined} ":
        return "furnished"
    if "unfurnished" in combined:
        return "unfurnished"
    return clean_text(value, UNKNOWN).lower()


def parse_short_term(value: Any, title: Any = "", description: Any = "") -> str:
    text = normalized_key(value)
    combined = " ".join([text, normalized_key(title), normalized_key(description)])
    if text in {"yes", "true", "1"} or "short term" in combined or "daily rent" in combined:
        return "yes"
    if text in {"no", "false", "0"}:
        return "no"
    return UNKNOWN


def is_commercial_property(property_type: str) -> bool:
    return normalized_key(property_type) in COMMERCIAL_TYPES


def infer_ikman_2026_property_type(title: Any, description: Any) -> str:
    text = f"{normalized_key(title)} {normalized_key(description)}"
    if "apartment" in text:
        return "Apartment"
    if "annex" in text or "annexe" in text:
        return "Annex"
    if re.search(r"\broom\b", text):
        return "Room"
    if "office" in text:
        return "Office space"
    if "commercial" in text or "shop" in text or "warehouse" in text:
        return "Other Commercial"
    if "villa" in text:
        return "Villa"
    return "House"


def parse_posted_date(value: Any) -> Tuple[str, Optional[int], Optional[int]]:
    text = clean_text(value)
    if not text:
        return "", None, None
    cleaned = re.sub(r"^posted on\s+", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+\d{1,2}:\d{2}\s*(?:am|pm)?$", "", cleaned, flags=re.IGNORECASE)
    current_year = datetime.now().year
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.date().isoformat(), parsed.year, parsed.month
        except ValueError:
            continue
    for fmt in ("%d %b", "%d %B"):
        try:
            parsed = datetime.strptime(f"{cleaned} {current_year}", f"{fmt} %Y")
            return parsed.date().isoformat(), parsed.year, parsed.month
        except ValueError:
            continue
    year_match = re.search(r"\b(20\d{2})\b", text)
    month_match = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b",
        text,
        re.IGNORECASE,
    )
    year = int(year_match.group(1)) if year_match else None
    month = None
    if month_match:
        month = datetime.strptime(month_match.group(1)[:3].title(), "%b").month
    return text, year, month


def normalize_location(value: Any) -> str:
    text = clean_text(value, UNKNOWN)
    text = text.strip(" ,")
    if not text:
        return UNKNOWN
    aliases = {
        "wellawata junction": "Wellawatte",
        "wellawatta": "Wellawatte",
        "ratmalana": "Rathmalana",
        "dehiwala mount lavinia": "Dehiwala-Mount Lavinia",
        "ja ela": "Ja-Ela",
        "ja-ela": "Ja-Ela",
        "kotte": "Sri Jayawardenepura Kotte",
        "pita kotte": "Pita Kotte",
        "ethul kotte": "Ethul Kotte",
    }
    key = normalized_key(text)
    if key in aliases:
        return aliases[key]
    colombo_match = re.fullmatch(r"colombo\s*0?(\d{1,2})", key)
    if colombo_match:
        return f"Colombo {int(colombo_match.group(1))}"
    return text


def make_record_id(record: Dict[str, Any]) -> str:
    parts = [
        clean_text(record.get("source")),
        clean_text(record.get("source_file")),
        clean_text(record.get("listing_id")),
        clean_text(record.get("listing_url")),
        clean_text(record.get("title")),
        str(record.get("monthly_rent_lkr") or ""),
        clean_text(record.get("location")),
    ]
    digest = hashlib.sha1("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()
    return digest[:16]


def amenity_flags(feature_texts: Iterable[Any], furnishing_status: str = "") -> Dict[str, int]:
    flags = {column: 0 for column in AMENITY_COLUMNS}
    joined = " | ".join(clean_text(value) for value in feature_texts if clean_text(value)).upper()
    normalized_joined = normalized_key(joined)
    for alias, column in AMENITY_ALIASES.items():
        if alias in joined or normalized_key(alias) in normalized_joined:
            flags[column] = 1
    if furnishing_status == "furnished":
        flags["amenity_fully_furnished"] = 1
    return flags


def base_record(**kwargs: Any) -> Dict[str, Any]:
    record = {column: "" for column in CANONICAL_COLUMNS}
    for column in AMENITY_COLUMNS + ANOMALY_FLAG_COLUMNS:
        record[column] = 0
    record.update(kwargs)
    for column in CATEGORICAL_COLUMNS:
        record[column] = clean_text(record.get(column), UNKNOWN) or UNKNOWN
    for column in NUMERIC_COLUMNS:
        if column in record and record[column] is None:
            record[column] = ""
    record["short_term"] = clean_text(record.get("short_term"), UNKNOWN) or UNKNOWN
    record["description"] = clean_text(record.get("description"))
    record["amenity_count"] = sum(int(record[column] or 0) for column in AMENITY_COLUMNS)
    record["record_id"] = make_record_id(record)
    return record


def read_csv_rows(path: Path) -> Iterable[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        yield from csv.DictReader(handle)


def raw_fingerprint(row: Dict[str, Any]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(payload.encode("utf-8", errors="ignore")).hexdigest()


def records_from_ikman_category(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for row in read_csv_rows(path):
        props = safe_parse_properties(row.get("properties"))
        title = clean_text(row.get("title") or row.get("ad_title"))
        description = clean_text(row.get("ad_description"))
        property_type = normalize_property_type(
            props.get("Property type") or props.get("Property Type"),
            row.get("category"),
            title,
        )
        furnishing = normalize_furnishing(props.get("Furnishing Status"), description)
        posted_date, posted_year, posted_month = parse_posted_date(row.get("posted_date") or row.get("timestamp"))
        features_text = " ".join(
            clean_text(props.get(key))
            for key in ["Features", "Amenities", "Property type", "Address"]
            if props.get(key)
        )
        amenities = amenity_flags([features_text, title, description], furnishing)
        record = base_record(
            source="ikman_category",
            source_file=path.name,
            listing_id=clean_text(row.get("slug")),
            listing_url=clean_text(row.get("url") or row.get("listing_url")),
            title=title,
            property_type=property_type,
            location=normalize_location(row.get("location")),
            district=parse_area_name(row.get("area")),
            monthly_rent_lkr=parse_money_lkr(row.get("price")),
            bedrooms=parse_number(props.get("Beds")),
            bathrooms=parse_number(props.get("Baths")),
            floor_area_sqft=parse_number(props.get("Size") or props.get("House size")),
            land_perches=parse_number(props.get("Land size")),
            floor_number=parse_number(props.get("Floor")),
            car_parking_spaces=parse_number(props.get("Parking") or props.get("Car parking spaces")),
            furnishing_status=furnishing,
            short_term=parse_short_term("", title, description),
            deposit_months=parse_months(props.get("Deposit")),
            advance_months=parse_months(props.get("Advance payment")),
            lease_term_months=parse_months(props.get("Min. lease term")),
            posted_date=posted_date,
            posted_year=posted_year,
            posted_month=posted_month,
            description=description,
            **amenities,
        )
        record["_raw_fingerprint"] = raw_fingerprint(row)
        record["_listing_type"] = normalized_key(row.get("type"))
        records.append(record)
    return records


def records_from_ikman_2026(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for row in read_csv_rows(path):
        title = clean_text(row.get("title"))
        description = clean_text(row.get("description_raw"))
        property_type = infer_ikman_2026_property_type(title, description)
        furnishing = normalize_furnishing("", f"{title} {description}")
        posted_date, posted_year, posted_month = parse_posted_date(row.get("posted_on_text"))
        amenities = amenity_flags([title, description], furnishing)
        record = base_record(
            source=clean_text(row.get("source"), "ikman.lk"),
            source_file=path.name,
            listing_id=clean_text(row.get("listing_url")),
            listing_url=clean_text(row.get("listing_url")),
            title=title,
            property_type=property_type,
            location=normalize_location(row.get("sublocation") or row.get("address")),
            district=clean_text(row.get("district"), UNKNOWN),
            monthly_rent_lkr=parse_money_lkr(row.get("price_lkr")),
            bedrooms=parse_number(row.get("bedrooms")),
            bathrooms=parse_number(row.get("bathrooms")),
            floor_area_sqft=parse_number(row.get("house_sqft")),
            land_perches=parse_number(row.get("land_perches")),
            floor_number="",
            car_parking_spaces="",
            furnishing_status=furnishing,
            short_term=parse_short_term("", title, description),
            deposit_months="",
            advance_months="",
            lease_term_months="",
            posted_date=posted_date,
            posted_year=posted_year,
            posted_month=posted_month,
            description=description,
            **amenities,
        )
        record["_raw_fingerprint"] = raw_fingerprint(row)
        record["_listing_type"] = "for rent"
        records.append(record)
    return records


def records_from_lankapropertyweb(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for row in read_csv_rows(path):
        title = clean_text(row.get("Title"))
        description = clean_text(row.get("Description"))
        features = clean_text(row.get("Features"))
        property_type = normalize_property_type(row.get("Property Type"), "", title)
        furnishing = normalize_furnishing(row.get("Furnishing Status"), description)
        short_term = parse_short_term(row.get("Short term"), title, description)
        amenities = amenity_flags([features, title, description], furnishing)
        record = base_record(
            source="lankapropertyweb",
            source_file=path.name,
            listing_id=clean_text(row.get("URL")),
            listing_url=clean_text(row.get("URL")),
            title=title,
            property_type=property_type,
            location=normalize_location(row.get("Location")),
            district=UNKNOWN,
            monthly_rent_lkr=parse_money_lkr(row.get("Price_Per_Month")),
            bedrooms=parse_number(row.get("Bedrooms")),
            bathrooms=parse_number(row.get("Bathrooms/WCs")),
            floor_area_sqft=parse_number(row.get("Floor area")),
            land_perches="",
            floor_number=parse_number(row.get("Floor Number")),
            car_parking_spaces=parse_number(row.get("Car parking spaces")),
            furnishing_status=furnishing,
            short_term=short_term,
            deposit_months=parse_months(row.get("Deposit")),
            advance_months=parse_months(row.get("Advance payment")),
            lease_term_months=parse_months(row.get("Min. lease term")),
            posted_date=clean_text(row.get("Availability")),
            posted_year="",
            posted_month="",
            description=description,
            **amenities,
        )
        record["_raw_fingerprint"] = raw_fingerprint(row)
        record["_listing_type"] = "for rent"
        records.append(record)
    return records


def load_records(input_dir: Path) -> Tuple[List[Dict[str, Any]], Counter]:
    records: List[Dict[str, Any]] = []
    source_rows: Counter = Counter()

    for file_name in IKMAN_CATEGORY_FILES:
        path = input_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
        file_records = records_from_ikman_category(path)
        records.extend(file_records)
        source_rows[file_name] = len(file_records)

    ikman_path = input_dir / IKMAN_2026_FILE
    if not ikman_path.exists():
        raise FileNotFoundError(f"Missing input file: {ikman_path}")
    file_records = records_from_ikman_2026(ikman_path)
    records.extend(file_records)
    source_rows[IKMAN_2026_FILE] = len(file_records)

    lpw_path = input_dir / LANKA_PROPERTY_WEB_FILE
    if not lpw_path.exists():
        raise FileNotFoundError(f"Missing input file: {lpw_path}")
    file_records = records_from_lankapropertyweb(lpw_path)
    records.extend(file_records)
    source_rows[LANKA_PROPERTY_WEB_FILE] = len(file_records)
    return records, source_rows


def as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def price_bounds(property_type: str) -> Tuple[float, float, float, float]:
    key = normalized_key(property_type)
    if key == "room":
        return 3000.0, 200000.0, 60000.0, 120000.0
    if key in {"annex", "portion"}:
        return 5000.0, 350000.0, 100000.0, 250000.0
    if key == "apartment":
        return 10000.0, 20000000.0, 1500000.0, 6000000.0
    if key in {"house", "villa", "bungalow"}:
        return 8000.0, 20000000.0, 1000000.0, 6000000.0
    if is_commercial_property(property_type):
        return 5000.0, 50000000.0, 3000000.0, 15000000.0
    return 3000.0, 50000000.0, 3000000.0, 15000000.0


def area_bounds(property_type: str) -> Tuple[float, float]:
    key = normalized_key(property_type)
    if key == "apartment":
        return 20000.0, 8000.0
    if key in {"room", "annex", "portion"}:
        return 10000.0, 3000.0
    if key in {"house", "villa", "bungalow"}:
        return 60000.0, 12000.0
    if is_commercial_property(property_type):
        return 150000.0, 40000.0
    return 100000.0, 30000.0


def duplicate_key(record: Dict[str, Any]) -> str:
    title_key = normalized_key(record.get("title"))
    location_key = normalized_key(record.get("location"))
    property_key = normalized_key(record.get("property_type"))
    rent = as_float(record.get("monthly_rent_lkr"))
    beds = as_float(record.get("bedrooms"))
    baths = as_float(record.get("bathrooms"))
    area = as_float(record.get("floor_area_sqft"))
    rounded_area = "" if area is None else str(int(round(area / 25.0) * 25))
    return "|".join(
        [
            title_key,
            location_key,
            property_key,
            "" if rent is None else str(int(round(rent))),
            "" if beds is None else str(int(round(beds))),
            "" if baths is None else str(int(round(baths))),
            rounded_area,
        ]
    )


def add_duplicate_flags(records: List[Dict[str, Any]]) -> None:
    seen_raw = set()
    seen_identifier = set()
    seen_near = set()
    for record in records:
        raw_key = record.get("_raw_fingerprint")
        if raw_key in seen_raw:
            record["flag_duplicate_exact"] = 1
        elif raw_key:
            seen_raw.add(raw_key)

        identifier = clean_text(record.get("listing_url")) or clean_text(record.get("listing_id"))
        identifier_key = f"{record.get('source_file')}|{identifier}"
        if identifier and identifier_key in seen_identifier:
            record["flag_duplicate_identifier"] = 1
        elif identifier:
            seen_identifier.add(identifier_key)

        near_key = duplicate_key(record)
        if near_key.count("|") >= 6 and near_key in seen_near:
            record["flag_duplicate_near"] = 1
        else:
            seen_near.add(near_key)


def add_quality_flags(records: List[Dict[str, Any]]) -> None:
    add_duplicate_flags(records)
    for record in records:
        flags: List[str] = []
        reasons: List[str] = []
        rent = as_float(record.get("monthly_rent_lkr"))
        property_type = clean_text(record.get("property_type"), "Other")
        min_price, max_price, high_price, very_high_price = price_bounds(property_type)

        if rent is None:
            record["flag_missing_price"] = 1
            flags.append("missing_price")
            reasons.append("missing_price")
        elif rent <= 0 or rent < min_price or rent > max_price:
            record["flag_impossible_price"] = 1
            flags.append("impossible_price")
            reasons.append("impossible_price")
        elif rent >= high_price:
            record["flag_extreme_price"] = 1
            flags.append("extreme_price")
            if rent >= very_high_price:
                flags.append("very_high_price")

        area = as_float(record.get("floor_area_sqft"))
        max_area, extreme_area = area_bounds(property_type)
        if area is not None:
            if area < 0 or area > max_area:
                record["flag_impossible_area"] = 1
                flags.append("impossible_area")
                reasons.append("impossible_area")
            elif area > extreme_area:
                record["flag_extreme_area"] = 1
                flags.append("extreme_area")

        land = as_float(record.get("land_perches"))
        if land is not None:
            if land < 0 or land > 1000:
                record["flag_impossible_land"] = 1
                flags.append("impossible_land")
                reasons.append("impossible_land")
            elif land > 100:
                record["flag_extreme_land"] = 1
                flags.append("extreme_land")

        bedrooms = as_float(record.get("bedrooms"))
        bathrooms = as_float(record.get("bathrooms"))
        if (bedrooms is not None and (bedrooms < 0 or bedrooms > 20)) or (
            bathrooms is not None and (bathrooms < 0 or bathrooms > 20)
        ):
            record["flag_impossible_rooms"] = 1
            flags.append("impossible_rooms")
            reasons.append("impossible_rooms")

        listing_type = normalized_key(record.get("_listing_type"))
        if listing_type in {"to buy", "for sale", "buy"}:
            record["flag_non_rental_listing"] = 1
            flags.append("non_rental_listing")
            reasons.append("non_rental_listing")

        for duplicate_flag in ["flag_duplicate_exact", "flag_duplicate_identifier", "flag_duplicate_near"]:
            if int(record.get(duplicate_flag) or 0):
                flag_name = duplicate_flag.replace("flag_", "")
                flags.append(flag_name)
                reasons.append(flag_name)

        record["anomaly_flags"] = "|".join(dict.fromkeys(flags))
        record["exclusion_reason"] = "|".join(dict.fromkeys(reasons))
        record["is_training_excluded"] = 1 if reasons else 0
        record["feature_anomaly_count"] = len(flags)


def clean_for_csv(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        if value.is_integer():
            return int(value)
    return value


def write_csv(path: Path, records: Sequence[Dict[str, Any]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({column: clean_for_csv(record.get(column, "")) for column in columns})


def zero_if_missing(value: Any) -> float:
    number = as_float(value)
    return 0.0 if number is None else number


def feature_record(record: Dict[str, Any]) -> Dict[str, Any]:
    rent = float(record[TARGET_COLUMN])
    output: Dict[str, Any] = {
        "record_id": record["record_id"],
        "source_file": record["source_file"],
        "listing_id": record["listing_id"],
        TARGET_COLUMN: rent,
        TRANSFORMED_TARGET_COLUMN: math.log1p(rent),
        "is_short_term": 1 if record.get("short_term") == "yes" else 0,
        "has_description": 1 if clean_text(record.get("description")) else 0,
        "description_length": len(clean_text(record.get("description"))),
        "feature_anomaly_count": record.get("feature_anomaly_count", 0),
    }
    for column in CATEGORICAL_COLUMNS:
        output[column] = clean_text(record.get(column), UNKNOWN) or UNKNOWN
    for column in NUMERIC_COLUMNS:
        output[column] = zero_if_missing(record.get(column))
    for column in AMENITY_COLUMNS:
        output[column] = int(record.get(column) or 0)
    return output


def build_feature_records(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    feature_rows = []
    for record in records:
        if int(record.get("is_training_excluded") or 0):
            continue
        rent = as_float(record.get(TARGET_COLUMN))
        if rent is None or rent <= 0:
            continue
        feature_rows.append(feature_record(record))
    return feature_rows


def quantiles(values: Iterable[Optional[float]]) -> Dict[str, float]:
    clean_values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not clean_values:
        return {}
    output: Dict[str, float] = {}
    for percentile in [0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1]:
        index = (len(clean_values) - 1) * percentile
        low = math.floor(index)
        high = math.ceil(index)
        if low == high:
            value = clean_values[low]
        else:
            value = clean_values[low] * (high - index) + clean_values[high] * (index - low)
        output[f"p{int(percentile * 100)}"] = round(value, 2)
    return output


def legacy_combined_audit(input_dir: Path) -> Dict[str, Any]:
    path = input_dir / LEGACY_COMBINED_NAME
    if not path.exists():
        return {"available": False}
    row_count = 0
    fingerprints = Counter()
    prices: List[Optional[float]] = []
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            fingerprints[raw_fingerprint(row)] += 1
            prices.append(parse_money_lkr(row.get("Price_Per_Month")))
    duplicate_rows = sum(count - 1 for count in fingerprints.values() if count > 1)
    return {
        "available": True,
        "file": path.name,
        "rows": row_count,
        "duplicate_rows_after_first": duplicate_rows,
        "target_quantiles": quantiles(prices),
    }


def build_report(
    records: Sequence[Dict[str, Any]],
    features: Sequence[Dict[str, Any]],
    source_rows: Counter,
    input_dir: Path,
) -> Dict[str, Any]:
    exclusions = Counter(clean_text(record.get("exclusion_reason")) for record in records)
    exclusions.pop("", None)
    flags = Counter()
    for record in records:
        for flag in clean_text(record.get("anomaly_flags")).split("|"):
            if flag:
                flags[flag] += 1
    rent_values = [as_float(record.get(TARGET_COLUMN)) for record in records]
    feature_rents = [as_float(record.get(TARGET_COLUMN)) for record in features]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_dir": str(input_dir),
        "source_rows": dict(source_rows),
        "cleaned_rows": len(records),
        "feature_rows": len(features),
        "excluded_rows": sum(1 for record in records if int(record.get("is_training_excluded") or 0)),
        "exclusion_reasons": dict(sorted(exclusions.items())),
        "anomaly_flags": dict(sorted(flags.items())),
        "property_type_counts": dict(Counter(record.get("property_type", UNKNOWN) for record in records).most_common()),
        "source_counts": dict(Counter(record.get("source", UNKNOWN) for record in records).most_common()),
        "target_quantiles_cleaned": quantiles(rent_values),
        "target_quantiles_features": quantiles(feature_rents),
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numeric_columns": NUMERIC_COLUMNS,
        "amenity_columns": AMENITY_COLUMNS,
        "legacy_combined_audit": legacy_combined_audit(input_dir),
    }


def strip_private_columns(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("_")}


def preprocess(
    input_dir: Path = DEFAULT_INPUT_DIR,
    processed_output: Path = DEFAULT_PROCESSED_PATH,
    features_output: Path = DEFAULT_FEATURES_PATH,
    report_output: Path = DEFAULT_REPORT_PATH,
) -> Dict[str, Any]:
    records, source_rows = load_records(input_dir)
    add_quality_flags(records)
    public_records = [strip_private_columns(record) for record in records]
    feature_rows = build_feature_records(public_records)

    write_csv(processed_output, public_records, CANONICAL_COLUMNS)
    write_csv(features_output, feature_rows, FEATURE_COLUMNS)

    report = build_report(public_records, feature_rows, source_rows, input_dir)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    report = preprocess(
        input_dir=args.input_dir,
        processed_output=args.processed_output,
        features_output=args.features_output,
        report_output=args.report_output,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
