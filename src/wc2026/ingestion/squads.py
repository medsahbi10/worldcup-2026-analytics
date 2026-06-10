"""Ingest the 2026 FIFA World Cup squads from Wikipedia.

The squads page has one ``wikitable`` per national team, each preceded by a
section heading containing the team name. We map each table to its team by
walking back to the nearest preceding heading, so the 1,246 players land with
the right country attached.
"""

from __future__ import annotations

import io
import re
import urllib.request

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

SQUADS_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
_SQUAD_COLS = {"No.", "Pos.", "Player", "Caps", "Goals", "Club"}


def fetch_html(url: str = SQUADS_URL) -> str:
    """Download the squads page HTML."""
    req = urllib.request.Request(url, headers={"User-Agent": "wc2026-analytics (research)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "ignore")


def _heading_text(table) -> str | None:
    """Team name = text of the nearest preceding section heading (not a group)."""
    el = table
    while True:
        el = el.find_previous(["h2", "h3", "h4"])
        if el is None:
            return None
        for edit in el.select(".mw-editsection"):
            edit.extract()
        text = el.get_text(strip=True)
        if text and not text.lower().startswith("group"):
            return text


def parse_squads(html: str) -> pd.DataFrame:
    """Parse the page into a tidy long DataFrame of players (one row per player)."""
    soup = BeautifulSoup(html, "lxml")
    frames: list[pd.DataFrame] = []

    for table in soup.select("table.wikitable"):
        headers = {th.get_text(strip=True) for th in table.select("tr th")}
        if not _SQUAD_COLS.issubset(headers):
            continue
        team = _heading_text(table)
        df = pd.read_html(io.StringIO(str(table)))[0]
        df = df.rename(
            columns={
                "No.": "shirt_number",
                "Pos.": "position",
                "Player": "player_name",
                "Date of birth (age)": "dob_age",
                "Caps": "caps",
                "Goals": "goals",
                "Club": "club",
            }
        )
        df["team"] = team
        frames.append(df)

    if not frames:
        raise ValueError("No squad tables found — page layout may have changed")

    out = pd.concat(frames, ignore_index=True)
    raw_name = out["player_name"].astype(str)
    out["is_captain"] = raw_name.str.contains("captain", case=False)
    # strip trailing parentheticals like "(captain)" from the display name
    out["player_name"] = raw_name.str.replace(r"\s*\(.*?\)", "", regex=True).str.strip()
    # birth year from the "DD Month YYYY (age N)" string
    out["birth_year"] = out["dob_age"].astype(str).str.extract(r"(\d{4})").astype("Int64")
    out["shirt_number"] = pd.to_numeric(out["shirt_number"], errors="coerce").astype("Int64")
    out["caps"] = pd.to_numeric(out["caps"], errors="coerce").astype("Int64")
    out["goals"] = pd.to_numeric(out["goals"], errors="coerce").astype("Int64")
    cols = [
        "team",
        "shirt_number",
        "position",
        "player_name",
        "birth_year",
        "caps",
        "goals",
        "club",
        "is_captain",
    ]
    return out[cols]


def load_squads(con: duckdb.DuckDBPyConnection) -> int:
    """Fetch + parse + write the ``raw_squads`` table. Returns row count."""
    df = parse_squads(fetch_html())  # noqa: F841 — referenced by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_squads AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_squads").fetchone()[0]
