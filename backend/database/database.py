import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
load_dotenv() # This forces Python to read the .env file

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env", override=True)

# True when DATABASE_URL was absent and the local SQLite file was substituted.
# Read it before trusting anything you find in a database file on disk: a
# developer inspecting backend/database/test.db while the process is talking to
# a hosted Postgres is reading a different database from the one the API writes.
USING_SQLITE_FALLBACK = False


def _build_database_url() -> str:
    """
    Resolve database URL from environment for cloud deployments.
    Falls back to local SQLite for development.

    SSL behaviour (for PostgreSQL connections):
    - Azure Postgres (`postgres.database.azure.com`) → SSL is forced on automatically.
    - Any other host → set PGSSLMODE=require in the environment to opt in,
      or include `?sslmode=require` directly in DATABASE_URL.
    - Local / SQLite → SSL is not applicable.
    """
    env_url = (os.getenv("DATABASE_URL") or "").strip()
    if env_url:
        placeholder_tokens = (
            "<your-server>",
            "<host>",
            "<username>",
            "<password>",
            "<database>",
        )
        if any(token in env_url for token in placeholder_tokens):
            raise ValueError(
                "DATABASE_URL contains placeholder values. "
                "Replace template values like <your-server>/<username>/<password>/<database>."
            )

        # Common hosted platforms return postgres:// URLs.
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql+psycopg2://", 1)
        if env_url.startswith("postgresql://") and "+psycopg2" not in env_url:
            env_url = env_url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Azure PostgreSQL always requires SSL — inject automatically.
        if "postgres.database.azure.com" in env_url and "sslmode=" not in env_url:
            separator = "&" if "?" in env_url else "?"
            env_url = f"{env_url}{separator}sslmode=require"

        # Generic opt-in: set PGSSLMODE=require for any other cloud Postgres
        # (Oracle, Render, Railway, etc.) without touching DATABASE_URL.
        elif "sslmode=" not in env_url and os.getenv("PGSSLMODE", "").strip().lower() == "require":
            separator = "&" if "?" in env_url else "?"
            env_url = f"{env_url}{separator}sslmode=require"

        # Neon.tech generates URLs containing channel_binding=require, but
        # psycopg2-binary < 3.0 raises "unsupported parameter name: channel_binding".
        # Strip it unconditionally; SSL is already enforced via sslmode=require.
        env_url = env_url.replace("&channel_binding=require", "").replace(
            "?channel_binding=require&", "?"
        ).replace("?channel_binding=require", "")

        return env_url

    global USING_SQLITE_FALLBACK
    USING_SQLITE_FALLBACK = True

    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "test.db"
    return f"sqlite:///{db_path}"


def mask_database_url(url: str) -> str:
    """The URL with any password removed, safe to log or print."""
    return re.sub(r"://([^:/@]+):([^@]*)@", r"://\1:***@", url)


def describe_database() -> str:
    """One line naming the database this process actually reads and writes."""
    target = mask_database_url(SQLALCHEMY_DATABASE_URL)
    if USING_SQLITE_FALLBACK:
        return f"{target}  (LOCAL FALLBACK - DATABASE_URL is not set)"
    return f"{target}  (from DATABASE_URL)"


SQLALCHEMY_DATABASE_URL = _build_database_url()

engine_kwargs = {"pool_pre_ping": True}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

# Announce the target once, at import. Two databases that both contain a
# `properties` table are indistinguishable from the application's behaviour, so
# the only way to tell which one a save landed in is to say so out loud.
if USING_SQLITE_FALLBACK:
    logger.warning(
        "DATABASE_URL is not set - falling back to the local SQLite file at %s. "
        "Any data written now is invisible to a hosted database, and vice versa.",
        SQLALCHEMY_DATABASE_URL.replace("sqlite:///", ""),
    )
else:
    logger.info("Database: %s", describe_database())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
