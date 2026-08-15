"""
Add columns and tables the ORM models declare but the database is missing.

``Base.metadata.create_all()`` creates absent tables and stops there - it will
never add a column to a table that already exists. With no Alembic in the
repository, every column added to an existing model since a database was created
is missing from that database. That is why a deployed instance renders estimated
values as "-" while a freshly created local database is fine.

**This migration is additive only.** It emits ``CREATE TABLE`` for absent tables
and ``ALTER TABLE ... ADD COLUMN`` for absent columns. It never drops, renames,
retypes or reorders anything, so it cannot destroy data. Columns are added as
nullable regardless of how the model declares them, because an existing row has
no value to put there; tighten constraints separately once the data is backfilled.

Dry run by default - it prints the SQL and changes nothing. Pass ``--apply`` to
execute, inside a single transaction that rolls back on any error.

Usage, from the repository root:

    python scripts/migrate_property_schema.py            # show the plan
    python scripts/migrate_property_schema.py --apply    # execute it

Take a backup first. On Neon or Azure Postgres, a branch or snapshot is enough.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load():
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")

    from backend.database.database import Base, engine
    import backend.database.schemas  # noqa: F401  - registers the models on Base

    return Base.metadata, engine


def _column_ddl(column, dialect) -> str:
    """Render one column's type for an ALTER TABLE, always nullable."""
    type_sql = column.type.compile(dialect=dialect)
    default = ""
    if column.server_default is not None:
        default = f" DEFAULT {column.server_default.arg}"
    elif column.default is not None and getattr(column.default, "is_scalar", False):
        value = column.default.arg
        literal = f"'{value}'" if isinstance(value, str) else str(value)
        default = f" DEFAULT {literal}"
    return f"{column.name} {type_sql}{default}"


def plan(metadata, engine) -> tuple[list[str], list[str]]:
    """Return (statements, human-readable notes)."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    dialect = engine.dialect

    statements: list[str] = []
    notes: list[str] = []

    for table in metadata.sorted_tables:
        if table.name not in live_tables:
            notes.append(f"CREATE TABLE {table.name} (absent)")
            continue

        live_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in live_columns:
                continue
            # No IF NOT EXISTS: that is Postgres-only syntax, and the inspector
            # check above already makes this idempotent on every dialect.
            statements.append(
                f"ALTER TABLE {table.name} ADD COLUMN {_column_ddl(column, dialect)}"
            )
            notes.append(f"ADD COLUMN {table.name}.{column.name}")

    return statements, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Execute. Without it, only print.")
    args = parser.parse_args()

    try:
        metadata, engine = _load()
    except Exception as exc:
        print(f"Could not connect: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    print(f"Database: {engine.url.render_as_string(hide_password=True)}\n")

    statements, notes = plan(metadata, engine)
    creates = [note for note in notes if note.startswith("CREATE TABLE")]

    if not statements and not creates:
        print("Nothing to do - the schema already matches the models.")
        return 0

    if creates:
        print(f"Tables to create ({len(creates)}):")
        for note in creates:
            print(f"  {note}")
        print()

    if statements:
        print(f"Columns to add ({len(statements)}):")
        for statement in statements:
            print(f"  {statement};")
        print()

    if not args.apply:
        print("Dry run - nothing was changed. Re-run with --apply to execute.")
        print("Take a database backup or branch first.")
        return 0

    from sqlalchemy import text

    # Absent tables go through the ORM, which knows their full definition.
    if creates:
        metadata.create_all(bind=engine)
        print(f"Created {len(creates)} table(s).")

    if statements:
        with engine.begin() as connection:  # rolls back on any error
            for statement in statements:
                connection.execute(text(statement))
        print(f"Added {len(statements)} column(s).")

    remaining, _ = plan(metadata, engine)
    if remaining:
        print(f"\nWARNING: {len(remaining)} statement(s) still pending; re-run to inspect.")
        return 1

    print("\nSchema now matches the models. Run scripts/check_property_schema.py to confirm, "
          "then re-save any property whose details predate the new columns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
