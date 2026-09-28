from __future__ import annotations

from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(Path(__file__).resolve().parent / ".env")

# PostgreSQL from .env remains the primary configuration. SQLite is a safe
# local fallback so a fresh clone can start without provisioning Postgres.
DB_URL = getenv("DB_URL") or f"sqlite:///{BASE_DIR / 'fixmycity.db'}"

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, pool_pre_ping=True, connect_args=connect_args)


class Base(DeclarativeBase):
    pass


def get_session():
    with Session(engine) as session:
        yield session


def ensure_legacy_columns() -> None:
    """Add columns introduced after the original project was created.

    ``Base.metadata.create_all`` creates new tables, but it does not add new
    columns to an existing table. This tiny compatibility migration keeps an
    existing development database usable without introducing Alembic yet.
    """
    inspector = inspect(engine)
    if "posts" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("posts")}

    with engine.begin() as connection:
        if "likes" not in columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN likes INTEGER DEFAULT 0 NOT NULL"))
        if "video" not in columns:
            connection.execute(text("ALTER TABLE posts ADD COLUMN video VARCHAR"))
