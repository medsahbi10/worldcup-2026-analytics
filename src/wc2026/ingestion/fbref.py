"""Ingest World Cup data from FBref via soccerdata.

Two responsibilities:
  * Squads (2026): scrape each national team's FBref roster page. soccerdata
    has no roster endpoint, but its Cloudflare-bypassing driver (``fb.get``)
    can fetch the team pages, whose "Roster"/Standard-Stats table lists the
    full squad even before any match is played.
  * Player stats (historical 2022, live 2026): standard per-player season
    stats for insights and model training.
"""

from __future__ import annotations

import io
import re
import unicodedata

import duckdb
import pandas as pd
import soccerdata as sd
from bs4 import BeautifulSoup

COMP_PAGE = "https://fbref.com/en/comps/1/{season}/{season}-FIFA-World-Cup-Stats"
_SQUAD_LINK_RE = re.compile(r"/en/squads/([0-9a-f]{8})/([A-Za-z0-9-]+?)-Men-Stats")


def _fbref(season: str) -> sd.FBref:
    return sd.FBref(leagues="INT-World Cup", seasons=season)


def _norm(s: str) -> str:
    """Normalize a team name for matching across sources (accents/punct/'and')."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace(" and ", " ")
    return re.sub(r"[^a-z]", "", s)


# ---------------------------------------------------------------- squads (2026)
def discover_squad_urls(season: str = "2026") -> dict[str, str]:
    """Map each of the 48 participating teams to its FBref squad-page URL.

    Reads the competition page for squad links, then keeps only links whose
    team matches a confirmed participant in the fixture list (the page also
    cross-links non-participants).
    """
    fb = _fbref(season)
    sched = fb.read_schedule().reset_index()
    participants = {_norm(t): t for t in set(sched["home_team"]) | set(sched["away_team"])}

    html = fb.get(COMP_PAGE.format(season=season)).read().decode("utf-8", "ignore")
    urls: dict[str, str] = {}
    for tid, slug in _SQUAD_LINK_RE.findall(html):
        team = participants.get(_norm(slug.replace("-", " ")))
        if team:
            urls[team] = f"https://fbref.com/en/squads/{tid}/{slug}-Men-Stats"
    return urls


def parse_squad(html: str, team: str) -> pd.DataFrame:
    """Extract the roster table (the one carrying player birth dates)."""
    tables = pd.read_html(io.StringIO(html.replace("<!--", "").replace("-->", "")))
    for t in tables:
        cols = [c[-1] if isinstance(c, tuple) else c for c in t.columns]
        if "Player" in cols and "Birth Date" in cols:
            t = t.copy()
            t.columns = cols
            name = t["Player"].astype(str)
            # drop repeated header rows ("Player") and footer totals
            t = t[t["Player"].notna() & ~name.str.fullmatch("Player") & ~name.str.contains("Total")]
            out = pd.DataFrame(
                {
                    "team": team,
                    "shirt_number": pd.to_numeric(t.get("#"), errors="coerce").astype("Int64"),
                    "player_name": t["Player"].astype(str).str.strip(),
                    "position": t.get("Pos"),
                    "club": t.get("Club"),
                    "birth_place": t.get("Birth Place"),
                    "birth_date": t.get("Birth Date"),
                    # Age comes as "32-173" (years-days) -> keep the years.
                    "age_years": t.get("Age")
                    .astype(str)
                    .str.extract(r"(\d+)")[0]
                    .astype("Int64"),
                }
            )
            return out
    raise ValueError(f"No roster table found for {team}")


def parse_team_meta(html: str) -> dict[str, str | None]:
    """Pull manager + confederation from a team page's meta block.

    FBref labels the confederation "Governing Country" (e.g. CAF, UEFA, AFC).
    """
    soup = BeautifulSoup(html, "lxml")
    meta = soup.find(id="meta") or soup
    found: dict[str, str] = {}
    for strong in meta.find_all("strong"):
        label = strong.get_text(strip=True).rstrip(":")
        if label in ("Manager", "Governing Country"):
            val = ""
            for sib in strong.next_siblings:
                if getattr(sib, "name", None) in ("br", "strong"):
                    break
                val += sib.get_text() if hasattr(sib, "get_text") else str(sib)
            found[label] = val.strip() or None
    return {"manager": found.get("Manager"), "confederation": found.get("Governing Country")}


def load_team_info(con: duckdb.DuckDBPyConnection, season: str = "2026") -> int:
    """Write ``raw_team_info`` (team, confederation, manager) from FBref team pages."""
    fb = _fbref(season)
    rows = []
    for team, url in discover_squad_urls(season).items():
        html = fb.get(url).read().decode("utf-8", "ignore")
        meta = parse_team_meta(html)
        rows.append({"team": team, **meta})
    df = pd.DataFrame(rows)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_team_info AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_team_info").fetchone()[0]


def load_squads(con: duckdb.DuckDBPyConnection, season: str = "2026") -> int:
    """Fetch every participant's squad and write the ``raw_squads`` table."""
    fb = _fbref(season)
    urls = discover_squad_urls(season)
    frames = []
    for team, url in urls.items():
        html = fb.get(url).read().decode("utf-8", "ignore")
        frames.append(parse_squad(html, team))
    df = pd.concat(frames, ignore_index=True)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_squads AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_squads").fetchone()[0]


# -------------------------------------------------------- player stats (history)
def fetch_player_stats(season: str = "2022") -> pd.DataFrame:
    """Standard per-player season stats for a World Cup, flattened to plain columns."""
    df = _fbref(season).read_player_season_stats(stat_type="standard").reset_index()
    flat = []
    for col in df.columns:
        if isinstance(col, tuple):
            parts = [p for p in col if p]
            flat.append("_".join(parts) if len(parts) > 1 else parts[0])
        else:
            flat.append(col)
    df.columns = flat

    rename = {
        "team": "team",
        "player": "player_name",
        "nation": "nation",
        "pos": "position",
        "age": "age",
        "Club": "club",
        "Playing Time_MP": "matches_played",
        "Playing Time_Starts": "starts",
        "Playing Time_Min": "minutes",
        "Performance_Gls": "goals",
        "Performance_Ast": "assists",
        "Performance_CrdY": "yellow_cards",
        "Performance_CrdR": "red_cards",
    }
    keep = {src: dst for src, dst in rename.items() if src in df.columns}
    out = df[list(keep)].rename(columns=keep)
    out.insert(0, "season", season)
    return out


def load_player_stats(con: duckdb.DuckDBPyConnection, season: str = "2022") -> int:
    """Fetch + write the ``raw_player_stats`` table. Returns row count."""
    df = fetch_player_stats(season)  # noqa: F841 — referenced by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_player_stats AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_player_stats").fetchone()[0]
