"""
Build the monthly market-index dataset from Central Bank of Sri Lanka sources.

Produces ``backend/predictions/LSTM/datasets/cbsl_market_index.csv``: the CBSL
Asking Price Indices for the Colombo district (Lands, Houses, Condominiums),
base 2019=100, one row per month.

This replaces the previous 1000-row synthetic series, which had no date column,
no declared time step, and no traceable source.

Two inputs, either or both:

``--official`` - the CBSL statistics portal export ("Data.xls"). Despite the
    extension this is an HTML table, so it is read with ``pandas.read_html``.
    Authoritative and the preferred source wherever it has coverage.

``--reports`` - a directory of quarterly "Real Estate Market Analysis" PDFs.
    Table 1 carries index LEVELS in editions from 2024 Q1 onward, and
    year-on-year % CHANGE before that. Levels are used directly; the percentage
    tables back-cast earlier levels via
    ``level(t-12) = level(t) / (1 + yoy(t)/100)``.

Where the two overlap the official export wins and the difference is reported,
so a parser regression shows up as a non-zero number rather than silently
replacing good data. On the sources used to build the committed CSV the two
agreed exactly across 24 overlapping months.

Refreshing: the index goes stale as quarters pass. Drop the newer PDFs into the
reports directory (or re-export Data.xls) and re-run; the runtime reports a
stale index rather than extrapolating across the gap.

Usage, from the repository root:

    python scripts/build_market_index.py --official data/raw/cbsl/Data.xls \\
                                         --reports data/raw/cbsl/
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_INDEX = {name: number for number, name in enumerate(MONTHS, start=1)}
NUMBER = r"-?\d+(?:\.\d+)?"

MONTH_ROW = re.compile(
    rf"^(?:(20\d\d)\s+)?(?:Q[1-4]\s+)?({'|'.join(MONTHS)})\s+({NUMBER})\s+({NUMBER})\s+({NUMBER})\b"
)
STANDALONE_YEAR = re.compile(r"^(20\d\d)$")

SERIES = ("lands", "houses", "condominiums")

# Reports publishing index LEVELS in Table 1; earlier editions publish YoY %.
LEVEL_REPORTS = ("2024_q1", "2024_q4", "2025_q1", "2025_q2", "2025_q3", "2025_q4", "2026_q1")

OFFICIAL_ROW_NAMES = {
    "Asking Price Index (API) for Lands (2019=100) - Colombo": "lands",
    "Asking Price Index (API) for houses (2019-100) - Colombo": "houses",
    "Asking Price Index (API) for Condominiums (2019=100) - Colombo": "condominiums",
}


# --------------------------------------------------------------------------
# Official statistics-portal export
# --------------------------------------------------------------------------

def read_official(path: Path) -> pd.DataFrame:
    tables = pd.read_html(path)
    table = next(t for t in tables if "Item Name" in getattr(t, "columns", []))

    month_columns = [
        column for column in table.columns
        if isinstance(column, str) and len(column) >= 8 and column[:4].isdigit() and "-" in column
    ]
    values = table.set_index("Item Name")[month_columns].apply(pd.to_numeric, errors="coerce")

    collected = {}
    for raw_name, series_name in OFFICIAL_ROW_NAMES.items():
        if raw_name in values.index:
            collected[series_name] = values.loc[raw_name].dropna()

    if not collected:
        raise ValueError(f"No recognised index rows found in {path}")

    frame = pd.DataFrame(collected)
    frame.index = [str(pd.Period(month.replace("-", " "), freq="M")) for month in frame.index]
    return frame.sort_index()


# --------------------------------------------------------------------------
# Quarterly PDF reports
# --------------------------------------------------------------------------

def _pdf_text(path: Path) -> str:
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def parse_report_table(path: Path) -> dict[tuple[int, int], tuple[float, float, float]]:
    """
    Parse Table 1 from one quarterly report.

    Each quarter is one block of three month rows plus a year token and a quarter
    token. The year sits inline in some editions and on its own line in others,
    so month rows and year tokens are collected in document order and the k-th
    year is paired with month rows 3k..3k+2.
    """
    month_rows: list[tuple[str, float, float, float, int | None]] = []
    year_tokens: list[int] = []

    for raw_line in _pdf_text(path).split("\n"):
        line = raw_line.strip()

        standalone = STANDALONE_YEAR.match(line)
        if standalone:
            year_tokens.append(int(standalone.group(1)))
            continue

        row = MONTH_ROW.match(line)
        if not row:
            continue

        inline_year = int(row.group(1)) if row.group(1) else None
        if inline_year is not None:
            year_tokens.append(inline_year)
        month_rows.append(
            (row.group(2), float(row.group(3)), float(row.group(4)), float(row.group(5)), inline_year)
        )

    parsed: dict[tuple[int, int], tuple[float, float, float]] = {}
    for position, (month, lands, houses, condos, inline_year) in enumerate(month_rows):
        block = position // 3
        year = inline_year if inline_year is not None else (
            year_tokens[block] if block < len(year_tokens) else None
        )
        if year is not None:
            parsed[(year, MONTH_INDEX[month])] = (lands, houses, condos)
    return parsed


def read_reports(directory: Path) -> pd.DataFrame:
    levels: dict[tuple[int, int], tuple[float, float, float]] = {}
    changes: dict[tuple[int, int], tuple[float, float, float]] = {}

    for path in sorted(directory.glob("*.pdf")):
        name = path.name.lower()
        target = levels if any(tag in name for tag in LEVEL_REPORTS) else changes
        target.update(parse_report_table(path))

    published = dict(levels)
    derived: dict[tuple[int, int], tuple[float, float, float]] = {}

    for _ in range(6):  # each pass reaches one further year back
        added = 0
        for key in sorted(set(published) | set(derived)):
            if key not in changes:
                continue
            source = published.get(key) or derived[key]
            target_key = (key[0] - 1, key[1])
            if target_key in published or target_key in derived:
                continue
            derived[target_key] = tuple(
                source[i] / (1.0 + changes[key][i] / 100.0) for i in range(3)
            )
            added += 1
        if not added:
            break

    combined = {**derived, **published}
    if not combined:
        return pd.DataFrame(columns=list(SERIES))

    frame = pd.DataFrame(
        [{"month": f"{year}-{month:02d}", **dict(zip(SERIES, values))}
         for (year, month), values in sorted(combined.items())]
    ).set_index("month")
    return frame.sort_index()


# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official", type=Path, default=None, help="CBSL portal export (Data.xls).")
    parser.add_argument("--reports", type=Path, default=None, help="Directory of quarterly PDFs.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "backend" / "predictions" / "LSTM" / "datasets" / "cbsl_market_index.csv",
    )
    args = parser.parse_args()

    if not args.official and not args.reports:
        parser.error("Provide --official, --reports, or both.")

    official = read_official(args.official) if args.official else pd.DataFrame(columns=list(SERIES))
    reports = read_reports(args.reports) if args.reports else pd.DataFrame(columns=list(SERIES))

    if not official.empty:
        print(f"official : {len(official)} months {official.index[0]} -> {official.index[-1]}")
    if not reports.empty:
        print(f"reports  : {len(reports)} months {reports.index[0]} -> {reports.index[-1]}")

    overlap = official.index.intersection(reports.index)
    if len(overlap):
        difference = (official.loc[overlap] - reports.loc[overlap]).abs().max()
        print(f"overlap  : {len(overlap)} months, max abs difference {difference.to_dict()}")

    # The official export wins where both cover a month; reports fill the tail.
    merged = official.combine_first(reports).sort_index() if not official.empty else reports

    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output, index_label="month")
    print(f"\nmerged   : {len(merged)} months {merged.index[0]} -> {merged.index[-1]}")
    print(f"non-null : {merged.notna().sum().to_dict()}")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
