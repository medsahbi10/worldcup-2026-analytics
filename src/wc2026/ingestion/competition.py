"""Ingest group standings and the match schedule from FBref.

Group standings come from the competition page's per-group tables (the group
name lives in each table's caption). The schedule comes from soccerdata's
``read_schedule`` and carries venue, date, and kickoff time. Both update live
as matches are played.
"""

from __future__ import annotations

import re

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

from wc2026.ingestion import fbref

COMP_PAGE = "https://fbref.com/en/comps/1/{season}/{season}-FIFA-World-Cup-Stats"
_GROUP_RE = re.compile(r"Group ([A-L])")


def parse_group_standings(html: str) -> pd.DataFrame:
    """Parse per-group standings tables (group letter from each table caption)."""
    soup = BeautifulSoup(html.replace("<!--", "").replace("-->", ""), "lxml")
    rows = []
    for tbl in soup.find_all("table"):
        cap = tbl.find("caption")
        if not cap:
            continue
        m = _GROUP_RE.match(cap.get_text(strip=True))
        if not m:
            continue
        cols = {th.get_text(strip=True) for th in tbl.select("thead th")}
        if "Pts" not in cols:
            continue
        for tr in tbl.select("tbody tr"):

            def cell(stat, _tr=tr):
                td = _tr.select_one(f"[data-stat={stat}]")
                return td.get_text(strip=True) if td else None

            team = cell("team")
            if not team:
                continue
            rows.append(
                {
                    "group_letter": m.group(1),
                    "team": team,
                    "rank": cell("rank"),
                    "mp": cell("games"),
                    "w": cell("wins"),
                    "d": cell("ties"),
                    "l": cell("losses"),
                    "gf": cell("goals_for"),
                    "ga": cell("goals_against"),
                    "gd": cell("goal_diff"),
                    "pts": cell("points"),
                }
            )
    return pd.DataFrame(rows)


def load_groups(con: duckdb.DuckDBPyConnection, season: str = "2026") -> int:
    """Write ``raw_group_standings`` (group membership + standings)."""
    fb = fbref._fbref(season)
    html = fb.get(COMP_PAGE.format(season=season)).read().decode("utf-8", "ignore")
    df = parse_group_standings(html)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_group_standings AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_group_standings").fetchone()[0]


def load_fixtures(con: duckdb.DuckDBPyConnection, season: str = "2026") -> int:
    """Write ``raw_fixtures`` (schedule with venue, date, kickoff time, score)."""
    sched = fbref._fbref(season).read_schedule().reset_index()
    keep = [c for c in ["round", "day", "date", "time", "home_team", "score",
                        "away_team", "venue", "attendance", "referee", "game_id"]
            if c in sched.columns]
    df = sched[keep].copy()  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_fixtures AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_fixtures").fetchone()[0]
