"""Build a projected starting XI and place players on a pitch.

Pre-tournament there are no real lineups, so we project a best XI: for a chosen
formation, fill each positional line with the highest market-value players in
that line. Coordinates use the mplsoccer 'opta' scale (0-100 x 0-100), goal at
the bottom (own half), attacking upward.
"""

from __future__ import annotations

import pandas as pd

# formation -> players per line (GK is always 1)
FORMATIONS: dict[str, dict[str, int]] = {
    "4-3-3": {"GK": 1, "DF": 4, "MF": 3, "FW": 3},
    "4-4-2": {"GK": 1, "DF": 4, "MF": 4, "FW": 2},
    "4-2-3-1": {"GK": 1, "DF": 4, "MF": 5, "FW": 1},
    "3-5-2": {"GK": 1, "DF": 3, "MF": 5, "FW": 2},
    "3-4-3": {"GK": 1, "DF": 3, "MF": 4, "FW": 3},
    "5-3-2": {"GK": 1, "DF": 5, "MF": 3, "FW": 2},
}

# vertical position (along pitch length) for each line
_LINE_X = {"GK": 9, "DF": 30, "MF": 52, "FW": 76}


def coords_for_formation(formation_str: str) -> list[tuple[float, float]]:
    """Pitch (x, y) for GK + outfield lines of a formation like '4-1-4-1'.

    Returns 11 (x=length, y=width) coords in lineup order (GK first, then each
    line out toward the attack), on the opta 0-100 scale — goal at the bottom.
    """
    lines = [int(x) for x in formation_str.split("-") if x.isdigit()]
    coords = [(9.0, 50.0)]  # goalkeeper (x=length near own goal, y=centre)
    n_lines = len(lines)
    for i, count in enumerate(lines):
        x = 24.0 + i * (82.0 - 24.0) / max(n_lines - 1, 1) if n_lines > 1 else 50.0
        for k in range(count):
            coords.append((x, (k + 1) / (count + 1) * 100))
    return coords


def build_xi(players: pd.DataFrame, formation: str = "4-3-3") -> pd.DataFrame:
    """Return up to 11 players with pitch coords (x, y) for the given formation.

    ``players`` must have columns: player_name, primary_position, market_value_eur
    (others like club/age/photo_url are passed through if present).
    """
    if formation not in FORMATIONS:
        raise ValueError(f"Unknown formation: {formation}")

    rank_col = "market_value_eur" if "market_value_eur" in players else None
    picked: list[pd.DataFrame] = []
    for line, count in FORMATIONS[formation].items():
        pool = players[players["primary_position"] == line].copy()
        if rank_col:
            pool = pool.sort_values(rank_col, ascending=False, na_position="last")
        pool = pool.head(count)
        n = len(pool)
        pool["line"] = line
        pool["x"] = _LINE_X[line]
        # spread players evenly across the pitch width (0-100)
        pool["y"] = [(k + 1) / (n + 1) * 100 for k in range(n)] if n else []
        picked.append(pool)

    return pd.concat(picked, ignore_index=True) if picked else players.head(0)
