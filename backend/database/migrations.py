"""Small additive schema migrator for installations that predate Alembic.

REVA historically relied on ``Base.metadata.create_all``. That creates new
tables but does not add columns to an existing database. Portfolio V2 only adds
nullable columns, so applying those additions at startup is safe and keeps local
SQLite and hosted PostgreSQL installations compatible until Alembic is adopted.

Every column is added as nullable regardless of how the model declares it. A
table that already holds rows has no value to put in a new NOT NULL column, so
requesting the model's constraint here would abort the migration on exactly the
databases that need it. Tighten constraints separately, after backfilling.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from backend.database.database import Base, describe_database

logger = logging.getLogger(__name__)


def ensure_additive_schema(engine: Engine) -> list[str]:
    """Add model columns the live database is missing. Returns what it applied."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    applied: list[str] = []

    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns or column.primary_key:
                    continue

                # Added nullable on purpose - see the module docstring.
                column_type = column.type.compile(dialect=engine.dialect)
                statement = (
                    f'ALTER TABLE "{table.name}" '
                    f'ADD COLUMN "{column.name}" {column_type}'
                )
                logger.info("Applying additive schema migration: %s.%s", table.name, column.name)
                connection.execute(text(statement))
                applied.append(f"{table.name}.{column.name}")

    if applied:
        # A column that was only just added is null on every pre-existing row.
        # Saying so here is what turns "the estimate shows a dash" into a
        # question with an answer.
        logger.warning(
            "Added %d missing column(s) to %s: %s. Existing rows are null in these "
            "columns until each property is re-saved.",
            len(applied), describe_database(), ", ".join(applied),
        )
    return applied
