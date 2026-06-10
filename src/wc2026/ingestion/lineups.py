"""Derive each team's likely XI + real formation from their last friendly.

A fixed formation is unrealistic — every team plays differently. Instead we
read each team's most recent played match (the pre-tournament friendly) from
FBref: the match page's lineup block gives the actual formation (e.g. 4-1-4-1)
and the starting XI in formation order (GK first, then each line out to the
attack). That's the best pre-tournament predictor of the World Cup XI.
"""

from __future__ import annotations

import io
import re

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

from wc2026.ingestion import fbref

_MATCH_HREF = re.compile(r"/en/matches/[0-9a-f]{8}/")
_FORMATION_RE = re.compile(r"^(.*?)\s*\(([\d-]+)\)\s*$")


def last_match_url(team_html: str) -> str | None:
    """Extract the 'Last Match' report URL from a FBref team page's meta block."""
    soup = BeautifulSoup(team_html, "lxml")
    meta = soup.find(id="meta") or soup
    for strong in meta.find_all("strong"):
        if "Last Match" in strong.get_text():
            a = strong.find_next("a", href=_MATCH_HREF)
            if a:
                return "https://fbref.com" + a.get("href")
    return None


# order weight per position group, for sorting a teamsheet GK -> DEF -> MID -> FWD
_POS_RANK = {
    "GK": 0,
    "RB": 1, "RWB": 1, "CB": 1, "LB": 1, "LWB": 1, "WB": 1, "DF": 1,
    "DM": 2, "RM": 2, "CM": 2, "LM": 2, "MF": 2, "AM": 3,
    "RW": 4, "LW": 4, "FW": 4, "CF": 4, "ST": 4,
}


def _position_map(match_html: str) -> dict[str, str]:
    """name -> match position (e.g. 'CB') from the page's player-stats tables."""
    tables = pd.read_html(io.StringIO(match_html.replace("<!--", "").replace("-->", "")))
    out: dict[str, str] = {}
    for t in tables:
        cols = [c[-1] if isinstance(c, tuple) else c for c in t.columns]
        if not ({"Player", "Pos"} <= set(cols)):
            continue
        t = t.copy()
        t.columns = cols
        for _, row in t.iterrows():
            name, pos = str(row["Player"]), row["Pos"]
            if name and name not in ("Player",) and pd.notna(pos):
                out.setdefault(name, str(pos).split(",")[0].strip())
    return out


def parse_lineup(match_html: str, team: str) -> dict | None:
    """Return {formation, starters:[{shirt_number, player_name, position, pos_rank}]}."""
    soup = BeautifulSoup(match_html, "lxml")
    target = fbref._norm(team)
    posmap = _position_map(match_html)
    for block in soup.select("div.lineup"):
        rows = block.select("table tr")
        if not rows:
            continue
        m = _FORMATION_RE.match(rows[0].get_text(strip=True))
        if not m or fbref._norm(m.group(1)) != target:
            continue
        formation = m.group(2)
        starters = []
        for tr in rows[1:]:
            cells = [td.get_text(strip=True) for td in tr.select("td")]
            if not cells or all(c == "" for c in cells):
                break  # blank row separates starters from the bench
            number = cells[0] or None
            name = cells[1] if len(cells) > 1 else cells[0]
            pos = posmap.get(name)
            starters.append(
                {
                    "shirt_number": number,
                    "player_name": name,
                    "position": pos,
                    "pos_rank": _POS_RANK.get((pos or "").upper(), 2),
                }
            )
        return {"formation": formation, "starters": starters}
    return None


def load_lineups(con: duckdb.DuckDBPyConnection, season: str = "2026") -> int:
    """For each team: last friendly -> lineup. Writes ``raw_lineups``. Returns team count."""
    fb = fbref._fbref(season)
    squad_urls = fbref.discover_squad_urls(season)
    recs = []
    for team, squad_url in squad_urls.items():
        try:
            team_html = fb.get(squad_url).read().decode("utf-8", "ignore")
            murl = last_match_url(team_html)
            if not murl:
                continue
            match_html = fb.get(murl).read().decode("utf-8", "ignore")
            lu = parse_lineup(match_html, team)
            if not lu or not lu["starters"]:
                continue
            for s in lu["starters"]:
                recs.append(
                    {"team": team, "formation": lu["formation"], "match_url": murl, **s}
                )
        except Exception:  # noqa: BLE001 — a single flaky fetch shouldn't kill the batch
            continue
    df = pd.DataFrame(recs)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_lineups AS SELECT * FROM df")
    return con.execute("SELECT count(distinct team) FROM raw_lineups").fetchone()[0]
