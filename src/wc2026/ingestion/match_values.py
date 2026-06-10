"""Fuzzy-match FBref squad players to Transfermarkt value/photo rows.

Exact name matching loses ~12% of players to spelling, name-order, and mononym
differences (e.g. FBref "Hannibal Mejbri" vs TM "Hannibal", "Son Heung-min" vs
"Heung-min Son"). We instead match within each team with rapidfuzz, greedily
assigning the best scoring pair so each player/value is used once. Produces
``player_value_map`` keyed to FBref squad names for dim_player to join.
"""

from __future__ import annotations

import unicodedata
from collections import defaultdict

import duckdb
import pandas as pd
from rapidfuzz import fuzz

from wc2026.ingestion import transfermarkt

_THRESHOLD = 84  # minimum combined score to accept a fuzzy match


def _clean(s: str) -> str:
    """Lowercase + strip accents, keep spaces (for token-aware scoring)."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def _score(a: str, b: str) -> float:
    a, b = _clean(a), _clean(b)
    # token_set handles order + subset; partial handles mononyms/substrings
    return max(fuzz.token_sort_ratio(a, b), fuzz.token_set_ratio(a, b), fuzz.partial_ratio(a, b))


def build_value_map(con: duckdb.DuckDBPyConnection, threshold: int = _THRESHOLD) -> dict:
    """Match squads to TM values within each team; write ``player_value_map``."""
    squads = defaultdict(list)
    for team, name in con.execute("select team, player_name from raw_squads").fetchall():
        squads[team].append(name)

    vals = defaultdict(list)
    for team, name, val, photo in con.execute(
        "select team, player_name, market_value_eur, photo_url from raw_player_values"
    ).fetchall():
        vals[team].append({"name": name, "value": val, "photo": photo})

    rows = []
    for team, players in squads.items():
        cands = vals.get(team, [])
        # rank all above-threshold pairs, then assign greedily (each side once)
        pairs = []
        for pn in players:
            for i, c in enumerate(cands):
                s = _score(pn, c["name"])
                if s >= threshold:
                    pairs.append((s, pn, i))
        pairs.sort(key=lambda x: x[0], reverse=True)
        used_fb, used_tm, assign = set(), set(), {}
        for s, pn, i in pairs:
            if pn in used_fb or i in used_tm:
                continue
            used_fb.add(pn)
            used_tm.add(i)
            assign[pn] = (i, s)
        for pn in players:
            if pn in assign:
                i, s = assign[pn]
                c = cands[i]
                rows.append((team, pn, c["value"], c["photo"], c["name"], round(s, 1)))
            else:
                rows.append((team, pn, None, None, None, None))

    df = pd.DataFrame(  # noqa: F841 — used by DuckDB below
        rows,
        columns=["team_country", "player_name", "market_value_eur",
                 "photo_url", "matched_name", "match_score"],
    )
    con.execute("CREATE OR REPLACE TABLE player_value_map AS SELECT * FROM df")
    total = len(df)
    matched = int(df["market_value_eur"].notna().sum())
    return {"total": total, "matched": matched, "rate": round(100 * matched / total, 1)}


def fill_missing_via_search(con: duckdb.DuckDBPyConnection, min_name_score: int = 80) -> int:
    """Second pass: look up still-unmatched players via TM search (any profile).

    Verifies the found profile name against the squad name to avoid same-name
    mismatches. Updates ``player_value_map`` in place. Returns the count filled.
    """
    missing = con.execute(
        "select team_country, player_name from player_value_map where market_value_eur is null"
    ).fetchall()
    filled = 0
    for team, name in missing:
        try:
            r = transfermarkt.search_player(name)
        except Exception:  # noqa: BLE001 — one flaky lookup shouldn't stop the pass
            r = None
        if not r or r["market_value_eur"] is None:
            continue
        if _score(name, r["profile_name"]) < min_name_score:
            continue
        con.execute(
            "update player_value_map set market_value_eur = ?, photo_url = ?, "
            "matched_name = ?, match_score = ? where team_country = ? and player_name = ?",
            [r["market_value_eur"], r["photo_url"], r["profile_name"],
             round(_score(name, r["profile_name"]), 1), team, name],
        )
        filled += 1
    return filled
