"""
Time calibration for land prices, using the Land Valuation Indicator table.

Two behaviours changed here, both of which were silently wrong before.

**Land type was ignored.** The LVI table carries four rows per district
(Residential, Commercial, Industrial, Other). The previous lookup filtered on
District alone and took ``.iloc[0]``, which always returned the Residential row
regardless of what was asked for. That happened to be harmless, because
``derive_features`` hardcodes ``land_type_Residential = 1``, but it was luck
rather than intent. The type is now filtered explicitly, and the coupling to the
feature builder is stated rather than assumed.

**An unknown district raised.** Any district outside the nine the table names -
Ampara, Batticaloa, Puttalam and so on - raised ValueError and failed the whole
request. The table publishes an "All Others*" row precisely for this case, so it
is now used, and the response is marked as lower confidence instead of erroring.
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
LVI_PATH = BASE_DIR / "data" / "land" / "land_valuation_indicator_values.csv"

lvi_df = pd.read_csv(LVI_PATH)
lvi_df.columns = lvi_df.columns.str.strip()

PERIOD_COLUMNS = [
    "2022 H1", "2022 H2",
    "2023 H1", "2023 H2",
    "2024 H1", "2024 H2",
    "2025 H1", "2025 H2",
]

REFERENCE_PERIOD = "2022 H1"
FALLBACK_DISTRICT = "All Others*"

# derive_features sets land_type_Residential = 1 unconditionally, so the
# calibration must read the same row of the table.
DEFAULT_LAND_TYPE = "Residential"


def _normalise(value: str) -> str:
    return (value or "").strip().lower()


def available_districts(land_type: str = DEFAULT_LAND_TYPE) -> list[str]:
    """Districts the LVI table names for a land type, excluding the catch-all."""
    rows = lvi_df[lvi_df["Type"].astype(str).str.strip() == land_type]
    return [
        str(name).strip()
        for name in rows["District"].tolist()
        if str(name).strip() != FALLBACK_DISTRICT
    ]


def _select_row(district: str, land_type: str):
    """
    Return (row, matched_district, is_fallback).

    Falls back to the table's "All Others*" row rather than raising, so a district
    outside the published set yields a lower-confidence estimate instead of an error.
    """
    typed = lvi_df[lvi_df["Type"].astype(str).str.strip() == land_type]
    if typed.empty:
        raise ValueError(f"LVI table has no rows for land type: {land_type}")

    districts = typed["District"].astype(str).str.strip()
    match = typed[districts.str.lower() == _normalise(district)]
    if not match.empty:
        return match.iloc[0], str(match.iloc[0]["District"]).strip(), False

    fallback = typed[districts == FALLBACK_DISTRICT]
    if fallback.empty:
        raise ValueError(
            f"LVI has no entry for district '{district}' and no '{FALLBACK_DISTRICT}' row "
            f"for land type '{land_type}'."
        )
    return fallback.iloc[0], FALLBACK_DISTRICT, True


def calibrate(
    predicted_price: float,
    district: str,
    target_period: str,
    land_type: str = DEFAULT_LAND_TYPE,
) -> dict:
    """
    Move a price from the LVI reference period to ``target_period``.

    Returns the adjusted price plus the provenance needed to judge it:
    which district row was used, whether that was the catch-all, and the
    multiplier applied.
    """
    if target_period not in PERIOD_COLUMNS:
        raise ValueError(
            f"Invalid valuation period: {target_period}. Supported: {', '.join(PERIOD_COLUMNS)}"
        )

    row, matched_district, is_fallback = _select_row(district, land_type)
    base_lvi, target_lvi = row[REFERENCE_PERIOD], row[target_period]

    if pd.isna(base_lvi) or pd.isna(target_lvi):
        raise ValueError(f"LVI missing for '{matched_district}' at {target_period}.")

    multiplier = float(target_lvi) / float(base_lvi)
    return {
        "adjusted_price": float(predicted_price) * multiplier,
        "multiplier": multiplier,
        "matched_district": matched_district,
        "requested_district": str(district).strip(),
        "used_fallback_district": is_fallback,
        "land_type": land_type,
        "reference_period": REFERENCE_PERIOD,
        "target_period": target_period,
    }


def adjust_price(
    predicted_price: float,
    district: str,
    target_period: str,
    land_type: str = DEFAULT_LAND_TYPE,
) -> float:
    """Backwards-compatible wrapper returning only the adjusted price."""
    return calibrate(predicted_price, district, target_period, land_type)["adjusted_price"]
