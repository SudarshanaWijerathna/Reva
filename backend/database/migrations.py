"""Small additive schema migrator for installations that predate Alembic.

REVA historically relied on ``Base.metadata.create_all``. That creates new
tables but does not add columns to an existing database. Portfolio V2 only adds
nullable columns, so applying those additions at startup is safe and keeps local
SQLite and hosted PostgreSQL installations compatible until Alembic is adopted.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from backend.database.database import Base

logger = logging.getLogger(__name__)


def ensure_additive_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns or column.primary_key:
                    continue

                column_type = column.type.compile(dialect=engine.dialect)
                nullable = "" if column.nullable else " NULL"
                statement = (
                    f'ALTER TABLE "{table.name}" '
                    f'ADD COLUMN "{column.name}" {column_type}{nullable}'
                )
                logger.info("Applying additive schema migration: %s.%s", table.name, column.name)
                connection.execute(text(statement))
