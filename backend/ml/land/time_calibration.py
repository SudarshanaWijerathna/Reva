import pandas as pd
from pathlib import Path

# Get project root directory
BASE_DIR = Path(__file__).resolve().parents[3]

# Correct CSV path
LVI_PATH = BASE_DIR / "data" / "land" / "land_valuation_indicator_values.csv"

# Load LVI table
lvi_df = pd.read_csv(LVI_PATH)

# Normalize column names
lvi_df.columns = lvi_df.columns.str.strip()

PERIOD_COLUMNS = [
    "2022 H1", "2022 H2",
    "2023 H1", "2023 H2",
    "2024 H1", "2024 H2",
    "2025 H1", "2025 H2"
]

REFERENCE_PERIOD = "2022 H1"


def adjust_price(
    predicted_price: float,
    district: str,
    target_period: str
) -> float:
    """
    Adjust predicted price_per_perch_LKR to a user-selected period
    using district-specific LVI values.
    """

    if target_period not in PERIOD_COLUMNS:
        raise ValueError(f"Invalid valuation period: {target_period}")

    # Find district row
    row = lvi_df[lvi_df["District"] == district]

    if row.empty:
        raise ValueError(f"LVI not found for district: {district}")

    base_lvi = row.iloc[0][REFERENCE_PERIOD]
    target_lvi = row.iloc[0][target_period]

    if pd.isna(base_lvi) or pd.isna(target_lvi):
        raise ValueError(
            f"LVI missing for district {district} at {target_period}"
        )

    return predicted_price * (target_lvi / base_lvi)
