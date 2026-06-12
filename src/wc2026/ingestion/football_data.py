"""Live results from football-data.org (free real-time source).

FBref lags live scores, so during the tournament we pull finished-match scores
from football-data.org, overlay them onto the FBref schedule
(``raw_fixtures.score``), and recompute ``raw_group_standings`` from the results
(group membership comes from the existing standings table). A free token is
required: register at https://www.football-data.org/client/register and set
``FOOTBALL_DATA_TOKEN`` in ``.env`` or the environment.

We query the global ``/v4/matches?competitions=WC`` endpoint (free-tier friendly,
date-windowed in <=10-day chunks) rather than the gated competition endpoint, and
derive standings ourselves instead of the restricted /standings endpoint.
"""

from __future__ import annotations

import datetime as _dt
import os
import unicodedata

import duckdb
import pandas as pd
import requests

BASE = "https://api.football-data.org/v4"
_FINISHED = {"FINISHED", "IN_PLAY", "PAUSED"}
_TOURNAMENT = (_dt.date(2026, 6, 1), _dt.date(2026, 7, 31))


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


_ALIASES = {
    "southkorea": "Korea Republic", "korearepublic": "Korea Republic",
    "czechrepublic": "Czechia", "czechia": "Czechia",
    "turkey": "Türkiye", "turkiye": "Türkiye",
    "ivorycoast": "Côte d'Ivoire", "cotedivoire": "Côte d'Ivoire",
    "iran": "IR Iran", "iriran": "IR Iran",
    "drcongo": "Congo DR", "congodr": "Congo DR",
    "democraticrepublicofcongo": "Congo DR", "democraticrepublicofthecongo": "Congo DR",
    "usa": "United States", "unitedstates": "United States", "unitedstatesofamerica": "United States",
    "bosniaandherzegovina": "Bosnia-Herzegovina", "bosniaherzegovina": "Bosnia-Herzegovina",
    "capeverde": "Cape Verde", "caboverde": "Cape Verde", "curacao": "Curaçao",
}


def _resolver(team_countries: list[str]):
    table = {_norm(t): t for t in team_countries}
    table.update(_ALIASES)
    return lambda name: table.get(_norm(name))


def _token() -> str:
    tok = os.getenv("FOOTBALL_DATA_TOKEN")
    if not tok:
        raise RuntimeError(
            "FOOTBALL_DATA_TOKEN not set. Get a free token at "
            "https://www.football-data.org/client/register and add it to .env"
        )
    return tok


def _our_teams(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [r[0] for r in con.execute("select team_country from dim_national_team").fetchall()]


def fetch_wc_matches() -> list[dict]:
    """All WC matches via the global endpoint, walked in <=10-day windows."""
    headers = {"X-Auth-Token": _token()}
    start, end = _TOURNAMENT
    out, cur = [], start
    while cur <= end:
        chunk_end = min(cur + _dt.timedelta(days=9), end)
        r = requests.get(
            f"{BASE}/matches",
            headers=headers,
            params={"competitions": "WC", "dateFrom": cur.isoformat(), "dateTo": chunk_end.isoformat()},
            timeout=30,
        )
        r.raise_for_status()
        out.extend(r.json().get("matches", []))
        cur = chunk_end + _dt.timedelta(days=1)
    return out


def run(con: duckdb.DuckDBPyConnection) -> dict:
    """Overlay finished scores onto raw_fixtures and recompute raw_group_standings."""
    resolve = _resolver(_our_teams(con))
    # group membership from the existing standings table (team -> letter)
    membership = {
        r[0]: r[1]
        for r in con.execute("select team, group_letter from raw_group_standings").fetchall()
    }

    matches = fetch_wc_matches()
    updated, unmatched = 0, []
    for m in matches:
        if m.get("status") not in _FINISHED:
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        hs, as_ = ft.get("home"), ft.get("away")
        if hs is None or as_ is None:
            continue
        home = resolve((m.get("homeTeam") or {}).get("name", ""))
        away = resolve((m.get("awayTeam") or {}).get("name", ""))
        if not home or not away:
            unmatched.append(f"{(m.get('homeTeam') or {}).get('name')} v {(m.get('awayTeam') or {}).get('name')}")
            continue
        con.execute(
            "update raw_fixtures set score = ? where home_team = ? and away_team = ?",
            [f"{hs}-{as_}", home, away],
        )
        updated += 1

    _recompute_standings(con, membership)
    return {"scores_updated": updated, "unmatched": unmatched, "matches_seen": len(matches)}


def _recompute_standings(con: duckdb.DuckDBPyConnection, membership: dict[str, str]) -> int:
    """Rebuild raw_group_standings (mp/w/d/l/gf/ga/gd/pts) from played fixtures."""
    if not membership:
        return 0
    stats = {t: dict(mp=0, w=0, d=0, ll=0, gf=0, ga=0, pts=0, grp=g) for t, g in membership.items()}
    played = con.execute(
        "select home_team, away_team, score from raw_fixtures "
        "where score is not null and score <> ''"
    ).fetchall()
    for home, away, score in played:
        try:
            hs, as_ = (int(x) for x in score.replace("–", "-").split("-")[:2])
        except (ValueError, AttributeError):
            continue
        if home not in stats or away not in stats:
            continue
        for team, gf, ga in ((home, hs, as_), (away, as_, hs)):
            s = stats[team]
            s["mp"] += 1
            s["gf"] += gf
            s["ga"] += ga
            if gf > ga:
                s["w"] += 1
                s["pts"] += 3
            elif gf == ga:
                s["d"] += 1
                s["pts"] += 1
            else:
                s["ll"] += 1

    rows = []
    for grp in sorted(set(membership.values())):
        teams = [t for t in stats if stats[t]["grp"] == grp]
        teams.sort(key=lambda t: (stats[t]["pts"], stats[t]["gf"] - stats[t]["ga"], stats[t]["gf"]), reverse=True)
        for rank, t in enumerate(teams, 1):
            s = stats[t]
            rows.append({"group_letter": grp, "team": t, "rank": rank, "mp": s["mp"],
                         "w": s["w"], "d": s["d"], "l": s["ll"], "gf": s["gf"],
                         "ga": s["ga"], "gd": s["gf"] - s["ga"], "pts": s["pts"]})
    df = pd.DataFrame(rows)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_group_standings AS SELECT * FROM df")
    return len(rows)
