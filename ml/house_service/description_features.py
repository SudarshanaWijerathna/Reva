import html
import math
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Tuple


FEATURE_EXTRACTION_VERSION = "house_description_v1"

HOUSE_QUALITY_TIERS = ["unknown", "normal", "semi_luxury", "luxury"]

DISTANCE_FEATURES = {
    "town": [
        r"town",
        r"city",
        r"junction",
        r"main road",
        r"galle road",
        r"kandy road",
        r"colombo",
    ],
    "hospital": [r"hospital", r"clinic", r"medical"],
    "school": [r"school", r"college", r"vidyalaya", r"university", r"institute"],
    "supermarket": [r"super\s*market", r"supermarket", r"food city", r"keells", r"cargills", r"arpico"],
    "bus_or_rail": [r"bus", r"railway", r"rail road", r"station"],
}

DISTANCE_COLUMNS = [
    "distance_to_town_km",
    "distance_to_hospital_km",
    "distance_to_school_km",
    "distance_to_supermarket_km",
    "distance_to_bus_or_rail_km",
]

DESCRIPTION_NUMERIC_FEATURES = [
    "road_width_ft",
    "road_width_missing",
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
    "parking_spaces",
    "parking_spaces_missing",
    "distance_to_town_km",
    "distance_to_town_km_missing",
    "distance_to_hospital_km",
    "distance_to_hospital_km_missing",
    "distance_to_school_km",
    "distance_to_school_km_missing",
    "distance_to_supermarket_km",
    "distance_to_supermarket_km_missing",
    "distance_to_bus_or_rail_km",
    "distance_to_bus_or_rail_km_missing",
    "mentions_school",
    "mentions_hospital",
    "mentions_supermarket",
    "mentions_bank",
    "mentions_highway",
    "mentions_junction",
    "utility_score",
    "road_access_score",
    "service_access_score",
    "quality_score",
    "description_value_index",
]

DESCRIPTION_CATEGORICAL_FEATURES = ["house_quality_tier"]
DESCRIPTION_FEATURES = DESCRIPTION_NUMERIC_FEATURES + DESCRIPTION_CATEGORICAL_FEATURES

_ROAD_WIDTH_PATTERNS = [
    re.compile(
        r"\b(?P<width>\d{1,3}(?:\.\d+)?)\s*(?:ft|feet|foot)\s*"
        r"(?:wide\s*)?(?:carpet(?:ed)?\s*)?(?:road|lane|access|driveway)\b"
    ),
    re.compile(
        r"\b(?P<width>\d{1,3}(?:\.\d+)?)\s*(?:ft|feet|foot)\s*"
        r"(?:carpet(?:ed)?\s*)?wide\s*(?:road|lane|access)\b"
    ),
    re.compile(
        r"\b(?:road|lane|access|driveway)\s*(?:width\s*)?"
        r"(?P<width>\d{1,3}(?:\.\d+)?)\s*(?:ft|feet|foot)\b"
    ),
]

_NUMBER_UNIT_PATTERN = re.compile(
    r"\b(?P<number>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>km|kms|kilometer|kilometers|m|meter|meters|metre|metres|minutes|minute|min)\b"
)

_NEGATION_PATTERN = re.compile(r"\b(no|not|without|unavailable|not available)\b")


def normalize_description(value: object) -> str:
    if value is None:
        return ""

    text = html.unescape(str(value)).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("&", " and ")
    text = re.sub(r"[/|,;:()\[\]{}*_#]+", " ", text)
    text = re.sub(r"[-]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    # Normalize common unit spellings after punctuation has been simplified.
    text = re.sub(r"\bfeet\b|\bfoot\b|\bft\.\b", "ft", text)
    text = re.sub(r"\bkms\b|\bkilometers?\b", "km", text)
    text = re.sub(r"\bmetres?\b|\bmeters?\b", "m", text)
    text = re.sub(r"\bmins?\b|\bminutes?\b", "min", text)
    return text.strip()


def extract_description_features(description: object) -> Dict[str, object]:
    text = normalize_description(description)
    has_description = bool(text)

    road_width = _extract_road_width_ft(text)
    distances = _extract_distances(text)
    parking_spaces = _extract_parking_spaces(text)
    quality_tier = _extract_quality_tier(text, has_description)

    features: Dict[str, object] = {
        "road_width_ft": road_width if road_width is not None else 0.0,
        "road_width_missing": 0 if road_width is not None else 1,
        "mentions_main_road": _bool(_has_keyword(text, [r"main road", r"galle road", r"kandy road", r"high level road"])),
        "mentions_carpet_road": _bool(_has_keyword(text, [r"carpet road", r"carpeted road", r"carpet access"])),
        "mentions_private_lane": _bool(_has_keyword(text, [r"private lane", r"private road", r"private access"])),
        "water_available": _bool(_has_positive_keyword(text, [r"pipe borne water", r"main water", r"well water", r"\bwater\b"])),
        "electricity_available": _bool(
            _has_positive_keyword(text, [r"electricity", r"electric", r"\bpower\b", r"three phase", r"3 phase"])
        ),
        "solar_power_available": _bool(_has_positive_keyword(text, [r"solar", r"solar power"])),
        "hot_water_available": _bool(_has_positive_keyword(text, [r"hot water"])),
        "house_quality_tier": quality_tier,
        "brand_new": _bool(_has_keyword(text, [r"brand new", r"newly built", r"new house"])),
        "fully_furnished": _bool(_has_keyword(text, [r"fully furnished", r"furnished"])),
        "air_conditioned": _bool(_has_keyword(text, [r"air conditioned", r"airconditioned", r"\ba\s*c\b", r"\bac\b"])),
        "cctv": _bool(_has_keyword(text, [r"cctv", r"security camera"])),
        "servant_room": _bool(_has_keyword(text, [r"servant", r"maid room", r"maids room", r"maid toilet"])),
        "pantry": _bool(_has_keyword(text, [r"pantry", r"wet kitchen", r"dry kitchen"])),
        "garden": _bool(_has_keyword(text, [r"garden", r"landscaped", r"yard"])),
        "parking_spaces": parking_spaces if parking_spaces is not None else 0.0,
        "parking_spaces_missing": 0 if parking_spaces is not None else 1,
        "mentions_school": _bool(_has_keyword(text, DISTANCE_FEATURES["school"])),
        "mentions_hospital": _bool(_has_keyword(text, DISTANCE_FEATURES["hospital"])),
        "mentions_supermarket": _bool(_has_keyword(text, DISTANCE_FEATURES["supermarket"])),
        "mentions_bank": _bool(_has_keyword(text, [r"\bbank\b", r"atm"])),
        "mentions_highway": _bool(_has_keyword(text, [r"highway", r"expressway"])),
        "mentions_junction": _bool(_has_keyword(text, [r"junction", r"\bjunc\b"])),
    }

    for name, distance in distances.items():
        column = f"distance_to_{name}_km"
        features[column] = distance if distance is not None else 0.0
        features[f"{column}_missing"] = 0 if distance is not None else 1

    features["utility_score"] = _utility_score(features)
    features["road_access_score"] = _road_access_score(features)
    features["service_access_score"] = _service_access_score(features)
    features["quality_score"] = _quality_score(features)
    features["description_value_index"] = round(
        0.25 * features["utility_score"]
        + 0.25 * features["road_access_score"]
        + 0.25 * features["service_access_score"]
        + 0.25 * features["quality_score"],
        6,
    )

    return features


def neutral_description_features() -> Dict[str, object]:
    return extract_description_features("")


def _extract_road_width_ft(text: str) -> Optional[float]:
    widths: List[float] = []
    for pattern in _ROAD_WIDTH_PATTERNS:
        for match in pattern.finditer(text):
            width = _safe_float(match.group("width"))
            if width is not None and 4 <= width <= 80:
                widths.append(width)
    return max(widths) if widths else None


def _extract_distances(text: str) -> Dict[str, Optional[float]]:
    distances: Dict[str, List[float]] = {name: [] for name in DISTANCE_FEATURES}
    if not text:
        return {name: None for name in DISTANCE_FEATURES}

    for match in _NUMBER_UNIT_PATTERN.finditer(text):
        distance_km = _distance_to_km(match.group("number"), match.group("unit"))
        if distance_km is None:
            continue

        window_start = max(0, match.start() - 80)
        window_end = min(len(text), match.end() + 80)
        window = text[window_start:window_end]
        for name in _closest_poi_categories(window, window_start, match):
            distances[name].append(distance_km)

    return {
        name: round(min(values), 4) if values else None
        for name, values in distances.items()
    }


def _distance_to_km(number: str, unit: str) -> Optional[float]:
    value = _safe_float(number)
    if value is None or value < 0:
        return None

    normalized_unit = unit.lower()
    if normalized_unit in {"km", "kms", "kilometer", "kilometers"}:
        km = value
    elif normalized_unit in {"m", "meter", "meters", "metre", "metres"}:
        km = value / 1000.0
    elif normalized_unit in {"min", "minute", "minutes"}:
        # Listings usually describe driving time. Use a conservative conversion,
        # then let model ablations decide whether the signal is useful.
        km = value * 0.5
    else:
        return None

    if km > 50:
        return None
    return km


def _closest_poi_categories(window: str, window_start: int, distance_match: re.Match) -> List[str]:
    distance_center = (distance_match.start() + distance_match.end()) / 2.0
    candidates: List[Tuple[str, float]] = []
    forward_candidates: List[Tuple[str, float]] = []
    backward_candidates: List[Tuple[str, float]] = []

    for name, keywords in DISTANCE_FEATURES.items():
        for keyword in keywords:
            for keyword_match in re.finditer(keyword, window):
                keyword_start = window_start + keyword_match.start()
                keyword_end = window_start + keyword_match.end()
                keyword_center = (keyword_start + keyword_end) / 2.0
                distance = abs(keyword_center - distance_center)
                candidates.append((name, distance))
                if keyword_start >= distance_match.end():
                    forward_candidates.append((name, distance))
                elif keyword_end <= distance_match.start():
                    backward_candidates.append((name, distance))

    preferred_candidates = forward_candidates or backward_candidates or candidates
    if not preferred_candidates:
        return []

    closest_distance = min(distance for _, distance in preferred_candidates)
    if closest_distance > 70:
        return []

    return sorted({name for name, distance in preferred_candidates if distance == closest_distance})


def _extract_parking_spaces(text: str) -> Optional[float]:
    if not text:
        return None

    patterns = [
        r"parking\s*(?:for)?\s*(?P<count>\d{1,2})\s*(?:cars?|vehicles?)",
        r"(?P<count>\d{1,2})\s*(?:cars?|vehicles?)\s*(?:parking|park|garage)",
        r"garage\s*(?:for)?\s*(?P<count>\d{1,2})\s*(?:cars?|vehicles?)",
        r"car\s*park\s*(?:for)?\s*(?P<count>\d{1,2})",
    ]
    counts: List[float] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            count = _safe_float(match.group("count"))
            if count is not None and 0 < count <= 20:
                counts.append(count)

    if counts:
        return max(counts)
    if _has_keyword(text, [r"parking", r"car park", r"garage"]):
        return 1.0
    return None


def _extract_quality_tier(text: str, has_description: bool) -> str:
    if not has_description:
        return "unknown"
    if _has_keyword(text, [r"semi luxury", r"semi luxurious"]):
        return "semi_luxury"
    if _has_keyword(text, [r"super luxury", r"luxury", r"luxurious", r"high end", r"premium"]):
        return "luxury"
    return "normal"


def _utility_score(features: Dict[str, object]) -> float:
    score = (
        0.35 * float(features["water_available"])
        + 0.35 * float(features["electricity_available"])
        + 0.15 * float(features["solar_power_available"])
        + 0.15 * float(features["hot_water_available"])
    )
    return round(_clamp(score), 6)


def _road_access_score(features: Dict[str, object]) -> float:
    width = float(features["road_width_ft"])
    width_score = _clamp(width / 30.0) if not int(features["road_width_missing"]) else 0.0
    mention_score = max(
        0.55 * float(features["mentions_main_road"]),
        0.45 * float(features["mentions_carpet_road"]),
        0.25 * float(features["mentions_private_lane"]),
    )
    return round(_clamp(max(width_score, mention_score)), 6)


def _service_access_score(features: Dict[str, object]) -> float:
    components: List[float] = []
    for column in DISTANCE_COLUMNS:
        missing_column = f"{column}_missing"
        if int(features[missing_column]) == 0:
            components.append(_distance_decay(float(features[column])))

    mention_bonus = max(
        float(features["mentions_school"]),
        float(features["mentions_hospital"]),
        float(features["mentions_supermarket"]),
        float(features["mentions_bank"]),
        float(features["mentions_junction"]),
    )
    if mention_bonus and not components:
        components.append(0.35)

    return round(sum(components) / len(components), 6) if components else 0.0


def _quality_score(features: Dict[str, object]) -> float:
    tier = str(features["house_quality_tier"])
    tier_score = {
        "unknown": 0.25,
        "normal": 0.35,
        "semi_luxury": 0.65,
        "luxury": 0.85,
    }.get(tier, 0.25)

    extras = (
        0.05 * float(features["brand_new"])
        + 0.04 * float(features["fully_furnished"])
        + 0.04 * float(features["air_conditioned"])
        + 0.03 * float(features["cctv"])
        + 0.02 * float(features["servant_room"])
        + 0.02 * float(features["pantry"])
        + 0.02 * float(features["garden"])
    )
    return round(_clamp(tier_score + extras), 6)


def _distance_decay(km: float) -> float:
    return _clamp(1.0 / (1.0 + max(km, 0.0)))


def _has_keyword(text: str, keywords: Iterable[str]) -> bool:
    return any(re.search(keyword, text) for keyword in keywords)


def _has_positive_keyword(text: str, keywords: Iterable[str]) -> bool:
    for keyword in keywords:
        for match in re.finditer(keyword, text):
            prefix = text[max(0, match.start() - 24):match.start()]
            if not _NEGATION_PATTERN.search(prefix):
                return True
    return False


def _safe_float(value: object) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def _bool(value: bool) -> int:
    return 1 if value else 0


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))
