"""
Compare the portfolio valuation engines side by side, before switching one on.

``PORTFOLIO_VALUATION_ENGINE`` defaults to ``legacy``, which reproduces the
previous behaviour including its unit bugs. This script runs all three engines
over the same properties so the difference can be attributed:

    legacy        -> scraper_fixed   the unit corrections alone
    scraper_fixed -> hybrid          the model change alone

Run it against a real user's portfolio with ``--user-id`` when a database is
configured, or against the built-in synthetic portfolio - which needs no database
and exercises each unit bug deliberately - by default.

Usage, from the repository root:

    python scripts/compare_valuation_engines.py
    python scripts/compare_valuation_engines.py --user-id 1
    python scripts/compare_valuation_engines.py --output reports/engine_comparison.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENGINE_ORDER = ["legacy", "scraper_fixed", "hybrid"]


# Lightweight stand-ins matching the ORM attributes the valuation layer reads.
@dataclass
class _Land:
    land_size: float
    zoning_type: str = "Residential"
    road_access: str = "Main road"


@dataclass
class _Housing:
    land_size_perches: float
    house_size_sqft: float
    floors: int = 2
    built_year: int = 2015
    property_condition: str = "Good"


@dataclass
class _Rental:
    monthly_rent: float
    occupancy_status: str = "Occupied"
    tenant_type: str = "Family"


@dataclass
class _Property:
    id: int
    property_type: str
    location: str
    purchase_price: float
    land: _Land | None = None
    housing: _Housing | None = None
    rental: _Rental | None = None
    status: str = "Active"
    created_at: str = "2024-01-01"


def synthetic_portfolio() -> list[_Property]:
    """
    A portfolio built to expose each unit bug.

    The 40-perch plot shows the per-perch error at its largest; the rental shows a
    monthly rent being counted as capital.
    """
    return [
        _Property(1, "land", "Colombo", 30_000_000, land=_Land(land_size=40.0)),
        _Property(2, "land", "Gampaha", 8_000_000, land=_Land(land_size=12.0, road_access="Gravel")),
        _Property(3, "housing", "Colombo", 45_000_000, housing=_Housing(land_size_perches=15, house_size_sqft=2200)),
        _Property(4, "rental", "Colombo", 25_000_000, rental=_Rental(monthly_rent=120_000)),
    ]


def load_portfolio(user_id: int) -> list:
    from backend.database.database import get_db
    from backend.database.schemas import Property

    session = next(get_db())
    try:
        return session.query(Property).filter(Property.user_id == user_id).all()
    finally:
        session.close()


def run(properties: list) -> dict:
    from backend.portfolio.valuation import value_property

    per_property: list[dict] = []
    totals = {engine: {"capital": 0.0, "income": 0.0} for engine in ENGINE_ORDER}

    for prop in properties:
        row = {
            "property_id": getattr(prop, "id", None),
            "type": prop.property_type,
            "location": prop.location,
            "purchase_price": float(prop.purchase_price or 0.0),
            "engines": {},
        }
        for engine in ENGINE_ORDER:
            valuation = value_property(prop, engine=engine)
            row["engines"][engine] = valuation.as_dict()
            totals[engine]["capital"] += valuation.capital_value or 0.0
            totals[engine]["income"] += valuation.monthly_income or 0.0
        per_property.append(row)

    return {"properties": per_property, "totals": totals}


def _change(before: float, after: float) -> str:
    if before == 0:
        return "n/a"
    return f"{(after - before) / before:+.1%}"


def report(result: dict) -> None:
    print(f"{'property':>10}  {'type':8}  {'legacy':>16}  {'scraper_fixed':>16}  {'hybrid':>16}")
    print("-" * 78)
    for row in result["properties"]:
        values = [row["engines"][engine]["capital_value"] or 0.0 for engine in ENGINE_ORDER]
        print(f"{str(row['property_id']):>10}  {row['type']:8}  "
              + "  ".join(f"{value:>16,.0f}" for value in values))

    print("-" * 78)
    totals = result["totals"]
    print(f"{'TOTAL':>10}  {'':8}  " + "  ".join(
        f"{totals[engine]['capital']:>16,.0f}" for engine in ENGINE_ORDER))

    legacy, fixed, hybrid = (totals[engine]["capital"] for engine in ENGINE_ORDER)
    print(f"\n  unit corrections   legacy -> scraper_fixed : {_change(legacy, fixed)}")
    print(f"  model change       scraper_fixed -> hybrid : {_change(fixed, hybrid)}")
    print(f"  combined           legacy -> hybrid        : {_change(legacy, hybrid)}")
    print(f"\n  monthly rental income (excluded from capital): "
          f"{totals['hybrid']['income']:,.0f}")

    print("\n  valuation method per property, hybrid engine:")
    for row in result["properties"]:
        detail = row["engines"]["hybrid"]
        print(f"    {row['property_id']} {row['type']:8} {detail['valuation_method']:32} "
              f"({detail['valuation_confidence']})")
        for note in detail["valuation_notes"]:
            print(f"       - {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if args.user_id is not None:
        properties = load_portfolio(args.user_id)
        print(f"Loaded {len(properties)} properties for user {args.user_id}.\n")
    else:
        properties = synthetic_portfolio()
        print(f"Using the synthetic portfolio ({len(properties)} properties).\n")

    result = run(properties)
    report(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **result}
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
            handle.write("\n")
        print(f"\nWrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
