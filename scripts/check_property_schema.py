"""
Compare the live database against the ORM models, read-only.

``backend/app.py`` manages schema with ``Base.metadata.create_all(bind=engine)``.
That creates tables which do not exist yet - it never adds a column to a table
that already exists. There is no Alembic in this repository, so every column
added to an existing model since a database was first created is missing from
that database, silently.

The visible symptom is a property whose estimated value renders as "-": the
valuation needs ``bedrooms``, ``bathrooms``, ``house_size_sqft`` and
``land_size_perches``, and if those columns are absent or null the payload cannot
be built. Locally the tables were created after the models grew, so everything
works; a long-lived deployment is the case that breaks.

This script only reads. It reports missing tables, missing columns, and rows that
would fail valuation because a required value is null. Use
``scripts/migrate_property_schema.py`` to add what is missing.

Usage, from the repository root:

    python scripts/check_property_schema.py
    DATABASE_URL=postgresql://... python scripts/check_property_schema.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Fields the hybrid valuation cannot proceed without, per portfolio/payloads.py.
REQUIRED_FOR_VALUATION = {
    "housing_properties": ["house_size_sqft", "land_size_perches", "bedrooms", "bathrooms"],
    "land_properties": ["land_size"],
    "properties": ["district"],
}


def _load_metadata():
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")

    from backend.database.database import Base, engine
    import backend.database.schemas  # noqa: F401  - registers the models on Base

    return Base.metadata, engine


def report(verbose: bool = False) -> int:
    from sqlalchemy import inspect, text

    metadata, engine = _load_metadata()
    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())

    missing_tables: list[str] = []
    missing_columns: dict[str, list[str]] = {}

    for table in metadata.sorted_tables:
        if table.name not in live_tables:
            missing_tables.append(table.name)
            continue
        live_columns = {column["name"] for column in inspector.get_columns(table.name)}
        absent = [column.name for column in table.columns if column.name not in live_columns]
        if absent:
            missing_columns[table.name] = absent

    print(f"Database: {engine.url.render_as_string(hide_password=True)}")
    print(f"Tables in the models: {len(metadata.sorted_tables)}   live: {len(live_tables)}\n")

    if missing_tables:
        print(f"MISSING TABLES ({len(missing_tables)}):")
        for name in missing_tables:
            print(f"  {name}")
        print()

    if missing_columns:
        total = sum(len(columns) for columns in missing_columns.values())
        print(f"MISSING COLUMNS ({total} across {len(missing_columns)} table(s)):")
        for table_name, columns in missing_columns.items():
            flagged = [
                f"{name} *" if name in REQUIRED_FOR_VALUATION.get(table_name, []) else name
                for name in columns
            ]
            print(f"  {table_name}: {', '.join(flagged)}")
        print("\n  * required by the hybrid valuation; absent means the estimate renders as '-'.")
        print()

    if not missing_tables and not missing_columns:
        print("Schema matches the models. No columns or tables are missing.\n")

    # Only inspect data for tables that actually have the columns.
    print("Rows that would fail valuation (null in a required field):")
    with engine.connect() as connection:
        for table_name, columns in REQUIRED_FOR_VALUATION.items():
            if table_name in missing_tables:
                print(f"  {table_name}: table missing, cannot check")
                continue
            live_columns = {column["name"] for column in inspector.get_columns(table_name)}
            checkable = [name for name in columns if name in live_columns]
            absent = [name for name in columns if name not in live_columns]

            if absent:
                print(f"  {table_name}: columns absent -> every row fails ({', '.join(absent)})")
                continue
            if not checkable:
                continue

            predicate = " OR ".join(f"{name} IS NULL" for name in checkable)
            try:
                total = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0
                bad = connection.execute(
                    text(f"SELECT COUNT(*) FROM {table_name} WHERE {predicate}")
                ).scalar() or 0
            except Exception as exc:
                print(f"  {table_name}: could not query ({type(exc).__name__}: {exc})")
                continue

            state = "OK" if bad == 0 else "NEEDS DATA"
            print(f"  {table_name}: {bad}/{total} rows have a null required field  [{state}]")

            if bad and verbose:
                for name in checkable:
                    count = connection.execute(
                        text(f"SELECT COUNT(*) FROM {table_name} WHERE {name} IS NULL")
                    ).scalar() or 0
                    if count:
                        print(f"      {name}: {count} null")

    if missing_tables or missing_columns:
        print("\nRun scripts/migrate_property_schema.py to add what is missing.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Break null counts down by column.")
    args = parser.parse_args()
    try:
        return report(verbose=args.verbose)
    except Exception as exc:
        print(f"Could not inspect the database: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
