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
from wc2026.ingestion import (
    competition, fbref, lineups, match_values, results, transfermarkt,
)
from wc2026.models import dixon_coles, elo, simulate

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


@asset(deps=[raw_squads])
def raw_player_values(context: AssetExecutionContext) -> None:
    """Ingest player market values + photos from Transfermarkt (depends on squads for team list)."""
    con = config.connect()
    try:
        n = transfermarkt.load_player_values(con)
    finally:
        con.close()
    context.log.info(f"Loaded {n} market-value rows into raw_player_values")


@asset(deps=[raw_squads])
def raw_lineups(context: AssetExecutionContext) -> None:
    """Predicted XIs + formations from each team's last friendly (FBref match pages)."""
    con = config.connect()
    try:
        n = lineups.load_lineups(con, season="2026")
    finally:
        con.close()
    context.log.info(f"Loaded lineups for {n} teams into raw_lineups")


@asset
def raw_group_standings(context: AssetExecutionContext) -> None:
    """Ingest group membership + standings from the FBref competition page."""
    con = config.connect()
    try:
        n = competition.load_groups(con, season="2026")
    finally:
        con.close()
    context.log.info(f"Loaded {n} rows into raw_group_standings")


@asset
def raw_fixtures(context: AssetExecutionContext) -> None:
    """Ingest the match schedule (venue, date, kickoff time) from FBref."""
    con = config.connect()
    try:
        n = competition.load_fixtures(con, season="2026")
    finally:
        con.close()
    context.log.info(f"Loaded {n} rows into raw_fixtures")


@asset(deps=[raw_squads, raw_player_values])
def player_value_map(context: AssetExecutionContext) -> None:
    """Fuzzy-match FBref squads to Transfermarkt values/photos (per-team name matching)."""
    con = config.connect()
    try:
        res = match_values.build_value_map(con)
        filled = match_values.fill_missing_via_search(con)
    finally:
        con.close()
    context.log.info(
        f"Matched {res['matched']}/{res['total']} ({res['rate']}%); "
        f"search pass filled {filled} more"
    )


@asset(
    deps=[
        raw_matches,
        raw_squads,
        raw_team_info,
        raw_player_stats,
        raw_player_values,
        raw_lineups,
        raw_group_standings,
        raw_fixtures,
        player_value_map,
    ]
)
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


@asset
def raw_intl_results(context: AssetExecutionContext) -> None:
    """Ingest historical international match results (model training data)."""
    con = config.connect()
    try:
        n = results.load_results(con)
    finally:
        con.close()
    context.log.info(f"Loaded {n} rows into raw_intl_results")


@asset(deps=[raw_intl_results])
def team_elo(context: AssetExecutionContext) -> None:
    """Compute World-Football-style Elo from results (cross-check rating)."""
    con = config.connect()
    try:
        n = elo.persist(con)
    finally:
        con.close()
    context.log.info(f"Computed Elo for {n} teams")


@asset(deps=[raw_intl_results, team_elo, dbt_marts])
def model_strength(context: AssetExecutionContext) -> None:
    """Fit the Dixon-Coles + value-prior model; persist team strengths + params."""
    con = config.connect()
    try:
        n = dixon_coles.build_and_persist_model(con)
    finally:
        con.close()
    context.log.info(f"Persisted strengths for {n} WC teams")


@asset(deps=[model_strength, dbt_marts])
def sim_results(context: AssetExecutionContext) -> None:
    """Monte-Carlo simulate the tournament; persist per-team advancement odds."""
    con = config.connect()
    try:
        df = simulate.run(con, n_sims=20000)
    finally:
        con.close()
    champ = df.iloc[0]
    context.log.info(f"Simulated 20k tournaments; favourite {champ['team_country']} "
                     f"({champ['p_champion'] * 100:.1f}%)")


defs = Definitions(
    assets=[
        raw_matches,
        raw_squads,
        raw_team_info,
        raw_player_stats,
        raw_player_values,
        raw_lineups,
        raw_group_standings,
        raw_fixtures,
        player_value_map,
        dbt_marts,
        raw_intl_results,
        team_elo,
        model_strength,
        sim_results,
    ]
)
