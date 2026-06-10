"""Dagster definitions — the asset graph for the WC2026 pipeline.

Raw ingestion assets land tables in DuckDB; ``dbt_marts`` then builds the
staging + marts models on top of them.

  raw_matches       -> sample historical matches (Phase 0 smoke data)
  raw_squads        -> 2026 World Cup squads from Wikipedia (~1,246 players)
  raw_player_stats  -> historical WC2022 player stats from FBref
  dbt_marts         -> dbt build: dim_team, fct_match, dim_player,
                       squad_membership, fct_player_stats

Run the UI:        dagster dev -m wc2026.definitions
Materialize all:   dagster asset materialize -m wc2026.definitions --select raw_matches,raw_squads,raw_player_stats,dbt_marts
"""

import os
import subprocess
import sys
from pathlib import Path

from dagster import AssetExecutionContext, Definitions, asset

from wc2026 import config, seed
from wc2026.ingestion import fbref

DBT_DIR = config.PROJECT_ROOT / "dbt"


def _dbt_executable() -> str:
    """Resolve the dbt CLI next to the running interpreter (venv-safe on Windows)."""
    candidate = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    return str(candidate) if candidate.exists() else "dbt"


@asset
def raw_matches(context: AssetExecutionContext) -> None:
    """Load sample historical matches into the warehouse."""
    con = config.connect()
    try:
        n = seed.load_sample_matches(con)
    finally:
        con.close()
    context.log.info(f"Loaded {n} rows into raw_matches")


@asset
def raw_squads(context: AssetExecutionContext) -> None:
    """Ingest the 2026 World Cup squads (players + national teams) from FBref."""
    con = config.connect()
    try:
        n = fbref.load_squads(con, season="2026")
    finally:
        con.close()
    context.log.info(f"Loaded {n} players into raw_squads")


@asset
def raw_team_info(context: AssetExecutionContext) -> None:
    """Ingest team metadata (confederation + manager) from FBref team pages."""
    con = config.connect()
    try:
        n = fbref.load_team_info(con, season="2026")
    finally:
        con.close()
    context.log.info(f"Loaded {n} rows into raw_team_info")


@asset
def raw_player_stats(context: AssetExecutionContext) -> None:
    """Ingest historical WC2022 player stats from FBref (for insights + training)."""
    con = config.connect()
    try:
        n = fbref.load_player_stats(con, season="2022")
    finally:
        con.close()
    context.log.info(f"Loaded {n} player-stat rows into raw_player_stats")


@asset(deps=[raw_matches, raw_squads, raw_team_info, raw_player_stats])
def dbt_marts(context: AssetExecutionContext) -> None:
    """Build dbt staging + marts models on top of the raw tables."""
    # Pass an absolute DB path so dbt doesn't resolve a relative path against
    # whatever CWD Dagster happens to launch the subprocess from.
    env = {**os.environ, "WC_DUCKDB_PATH": str(config.LOCAL_DB_PATH)}
    result = subprocess.run(
        [
            _dbt_executable(),
            "build",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise RuntimeError("dbt build failed")


defs = Definitions(
    assets=[raw_matches, raw_squads, raw_team_info, raw_player_stats, dbt_marts]
)
