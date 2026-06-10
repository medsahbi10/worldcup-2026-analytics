"""Database connection management.

Switches between a local DuckDB file (development) and MotherDuck (cloud,
used by GitHub Actions) based on environment variables, so the same code
path runs in both places.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()

# src/wc2026/config.py -> project root is two parents up from this file's dir
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_DB_PATH = PROJECT_ROOT / "data" / "wc2026.duckdb"


def get_database_target() -> str:
    """Return the DuckDB connection target string.

    - Cloud mode (``WC_ENV=cloud`` + a MotherDuck token): returns an ``md:``
      connection string so data persists between stateless CI runs.
    - Otherwise: returns the local DuckDB file path (created on demand).
    """
    if os.getenv("WC_ENV") == "cloud" and os.getenv("MOTHERDUCK_TOKEN"):
        db_name = os.getenv("MOTHERDUCK_DATABASE", "wc2026")
        return f"md:{db_name}"

    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return str(LOCAL_DB_PATH)


def connect() -> duckdb.DuckDBPyConnection:
    """Open a DuckDB connection to the configured target."""
    return duckdb.connect(get_database_target())
