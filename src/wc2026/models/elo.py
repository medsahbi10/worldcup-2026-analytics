"""World-Football-style Elo ratings, computed from the full results history.

Self-contained (no external source): process every international match
chronologically with importance-weighted K, a margin-of-victory multiplier, and
home advantage. Gives a transparent strength rating that complements the
Dixon-Coles fit and the squad-value prior.
"""

from __future__ import annotations

from collections import defaultdict

import duckdb
import pandas as pd

INIT = 1500.0
HOME_ADV = 65.0  # Elo points, applied to the home side at non-neutral venues


def _importance(tournament: str) -> float:
    """K-factor by match importance (World Football Elo conventions)."""
    t = (tournament or "").lower()
    if "world cup" in t and "qualification" not in t:
        return 60.0
    if any(k in t for k in ("euro", "copa am", "african cup", "asian cup", "gold cup")) \
            and "qualification" not in t:
        return 50.0
    if "qualification" in t or "nations league" in t:
        return 40.0
    if "friendly" in t:
        return 20.0
    return 30.0


def _mov(goal_diff: int) -> float:
    if goal_diff <= 1:
        return 1.0
    if goal_diff == 2:
        return 1.5
    return (11 + goal_diff) / 8.0


def compute_elo(matches: pd.DataFrame) -> dict[str, float]:
    """Return current Elo per team. ``matches`` sorted ascending by date."""
    r: dict[str, float] = defaultdict(lambda: INIT)
    for m in matches.itertuples():
        ha = 0.0 if m.neutral else HOME_ADV
        exp_home = 1.0 / (1.0 + 10 ** (-(r[m.home_team] + ha - r[m.away_team]) / 400.0))
        s_home = 1.0 if m.hg > m.ag else (0.5 if m.hg == m.ag else 0.0)
        delta = _importance(m.tournament) * _mov(abs(m.hg - m.ag)) * (s_home - exp_home)
        r[m.home_team] += delta
        r[m.away_team] -= delta
    return dict(r)


def load_and_compute(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    matches = con.execute(
        """
        select cast(date as date) as match_date, home_team, away_team,
               cast(home_score as integer) as hg, cast(away_score as integer) as ag,
               neutral, tournament
        from raw_intl_results
        where home_score is not null
        order by date
        """
    ).df()
    return compute_elo(matches)


def persist(con: duckdb.DuckDBPyConnection) -> int:
    """Compute Elo and persist ``team_elo`` (team, elo)."""
    elo = load_and_compute(con)
    df = pd.DataFrame(sorted(elo.items(), key=lambda kv: -kv[1]), columns=["team", "elo"])  # noqa: F841
    con.execute("CREATE OR REPLACE TABLE team_elo AS SELECT * FROM df")
    return len(df)
