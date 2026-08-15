"""
Find out where a property value is lost between the form and the database.

The estimated value renders as "-" whenever the valuation payload cannot be
built, and by far the most common reason is a null ``properties.district``.
"District is null" has several very different causes, and they need different
fixes:

  1. The process is connected to a different database from the one being
     inspected. ``DATABASE_URL`` unset falls back to a local SQLite file, so a
     developer can read ``backend/database/test.db`` while the API writes to a
     hosted Postgres. Both contain a ``properties`` table, and nothing in the
     application's behaviour distinguishes them.
  2. The column does not exist on the live database, because
     ``create_all`` never adds columns to an existing table.
  3. The column exists but the row predates it, so it is null and stays null
     until that property is saved again.
  4. The write path drops the value.

This script separates those four. It reads by default. ``--roundtrip USER_ID``
additionally performs one real create-read-delete against the configured
database, which is the only way to distinguish (4) from (3).

Usage, from the repository root:

    python scripts/diagnose_property_save.py
    python scripts/diagnose_property_save.py --roundtrip 5
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RULE = "-" * 78

# Without these the corresponding payload builder returns None and the
# portfolio shows "-". Kept in step with backend/portfolio/payloads.py.
BLOCKS_VALUATION = {
    "land": ("properties.district", "land_properties.land_size"),
    "housing": (
        "properties.district", "housing_properties.house_size_sqft",
        "housing_properties.land_size_perches", "housing_properties.bedrooms",
        "housing_properties.bathrooms",
    ),
    "rental": (
        "properties.district", "rental_properties.property_subtype",
    ),
}


def _load():
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")

    from backend.database import database as db_module
    import backend.database.schemas  # noqa: F401  - registers the models

    return db_module


def section(title: str) -> None:
    print(f"\n{RULE}\n{title}\n{RULE}")


def report_target(db_module) -> None:
    section("1. Which database is this process actually using?")
    print(f"   {db_module.describe_database()}")
    if db_module.USING_SQLITE_FALLBACK:
        print(
            "\n   DATABASE_URL is not set, so this is the local development file.\n"
            "   If your running backend HAS DATABASE_URL set, it is writing somewhere\n"
            "   else entirely and everything below describes the wrong database."
        )
    else:
        print(
            "\n   Anything in backend/database/test.db is unrelated to this database\n"
            "   and must not be used as evidence about saved values."
        )


def report_schema(db_module) -> list[str]:
    from sqlalchemy import inspect

    section("2. Does the live schema match the models?")
    inspector = inspect(db_module.engine)
    live_tables = set(inspector.get_table_names())
    problems: list[str] = []

    for table in db_module.Base.metadata.sorted_tables:
        if table.name not in live_tables:
            print(f"   MISSING TABLE  {table.name}")
            problems.append(f"table {table.name}")
            continue
        live = {column["name"] for column in inspector.get_columns(table.name)}
        absent = [column.name for column in table.columns if column.name not in live]
        if absent:
            print(f"   MISSING COLUMNS  {table.name}: {', '.join(absent)}")
            problems.extend(f"{table.name}.{name}" for name in absent)

    if not problems:
        print("   Every table and column the models declare exists. Schema is not the cause.")
    else:
        print(
            "\n   These are added at startup by ensure_additive_schema(). Seeing them here\n"
            "   means the running backend has not restarted since they were declared."
        )
    return problems


def report_rows(db_module) -> None:
    from backend.database.schemas import Property

    section("3. What is actually stored?")
    session = db_module.SessionLocal()
    try:
        rows = session.query(Property).order_by(Property.id).all()
        if not rows:
            print("   No properties in this database.")
            return
        print(f"   {len(rows)} propert(ies).\n")
        for prop in rows:
            saved_by_current_code = prop.features_updated_at is not None
            print(
                f"   #{prop.id}  {prop.property_type:<8} {str(prop.location):<16} "
                f"user={prop.user_id}  created={prop.created_at}"
            )
            print(
                f"        district={prop.district!r}  locality={prop.locality!r}  "
                f"lat={prop.latitude}  lon={prop.longitude}"
            )
            print(
                f"        last saved by portfolio_v2 code: "
                f"{'yes, ' + str(prop.features_updated_at) if saved_by_current_code else 'NO'}"
            )
            blockers = []
            if not str(prop.district or "").strip():
                blockers.append("district is empty")
            detail = getattr(prop, prop.property_type if prop.property_type != "housing" else "housing", None)
            if detail is None:
                blockers.append(f"{prop.property_type} detail row is absent")
            elif prop.property_type == "land" and not (detail.land_size or 0):
                blockers.append("land_size is empty")
            elif prop.property_type == "housing" and not all(
                (detail.house_size_sqft, detail.land_size_perches, detail.bedrooms, detail.bathrooms)
            ):
                blockers.append("one of house_size_sqft/land_size_perches/bedrooms/bathrooms is empty")
            elif prop.property_type == "rental" and not detail.property_subtype:
                blockers.append("property_subtype is empty")

            if blockers:
                print(f"        VALUATION BLOCKED: {'; '.join(blockers)}  -> renders as '-'")
            else:
                print("        valuation inputs are complete")
            print()

        stale = [prop.id for prop in rows if prop.features_updated_at is None]
        if stale:
            print(
                f"   Properties {stale} have never been written by the current code.\n"
                "   Every save and every edit sets features_updated_at, so a null there\n"
                "   means this database did not receive those writes - either the row\n"
                "   predates the field, or the backend is writing to a different database."
            )
    finally:
        session.close()


def roundtrip(db_module, user_id: int) -> None:
    """One real create-read-delete. Proves whether the write path keeps values."""
    from backend.properties.models import LandCreate
    from backend.properties.service import create_land_property, delete_property

    section(f"4. Live round-trip for user {user_id}")
    probe = LandCreate(
        location="__diagnostic_probe__",
        district="Colombo",
        locality="Nugegoda",
        purchase_price=1.0,
        purchase_date=datetime.date.today(),
        land_size=1.0,
        zoning_type="residential",
        road_access="main",
    )
    print(f"   Sending district={probe.district!r}, locality={probe.locality!r} ...")

    session = db_module.SessionLocal()
    try:
        created = create_land_property(session, user_id, probe)
        property_id = created.id
        print(f"   Created property #{property_id}.")
    except Exception as exc:
        print(f"   CREATE FAILED: {type(exc).__name__}: {exc}")
        session.rollback()
        session.close()
        return
    finally:
        session.close()

    # A brand new session, so this reads the database rather than the identity map.
    verify = db_module.SessionLocal()
    try:
        from backend.database.schemas import Property

        stored = verify.query(Property).filter(Property.id == property_id).first()
        if stored is None:
            print("   READ BACK: the row is not there. The commit did not land.")
        else:
            ok = str(stored.district or "").strip().lower() == "colombo"
            print(f"   READ BACK: district={stored.district!r}  locality={stored.locality!r}")
            print(
                "   VERDICT: the write path stores values correctly - the problem is the\n"
                "            data already in the rows above, not the code."
                if ok else
                "   VERDICT: the write path LOSES the district. This is the bug."
            )
    finally:
        verify.close()

    cleanup = db_module.SessionLocal()
    try:
        delete_property(cleanup, user_id, property_id)
        print(f"   Removed the probe property #{property_id}.")
    except Exception as exc:
        print(f"   NOTE: could not remove probe property #{property_id}: {exc}")
        print("         Delete it manually.")
    finally:
        cleanup.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--roundtrip", type=int, metavar="USER_ID",
        help="Create, read back and delete one probe property for this user id.",
    )
    args = parser.parse_args()

    try:
        db_module = _load()
    except Exception as exc:
        print(f"Could not connect: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    report_target(db_module)
    report_schema(db_module)
    report_rows(db_module)
    if args.roundtrip is not None:
        roundtrip(db_module, args.roundtrip)

    print(f"\n{RULE}")
    print("Run this against the SAME environment the backend runs in - same shell,")
    print("same .env - or it will describe a database the API never touches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
