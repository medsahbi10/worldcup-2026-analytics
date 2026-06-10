"""Monte Carlo simulation of the World Cup 2026.

Uses the fitted Dixon-Coles strengths to simulate the 72 group matches (scoreline
draws → points/goal-difference → standings), determine qualifiers (top 2 per group
+ 8 best third-placed), then a single-elimination knockout, many times over, to
estimate each team's chance of advancing / reaching each round / winning.

Knockout bracket: qualifiers are seeded by group-stage performance and placed in a
standard single-elim bracket. (This approximates FIFA's fixed-slot bracket, whose
third-place allocation is combinatorial; aggregate title odds are robust to it.)
"""

from __future__ import annotations

import math

import duckdb
import numpy as np
import pandas as pd

MAXG = 8
ROUND_NAMES = ["advance", "r16", "qf", "sf", "final", "champion"]


def load_model(con: duckdb.DuckDBPyConnection) -> dict:
    s = con.execute("select team_country, attack, defense from model_team_strength").df()
    p = con.execute("select home_adv, rho from model_params").df().iloc[0]
    return {
        "attack": dict(zip(s.team_country, s.attack)),
        "defense": dict(zip(s.team_country, s.defense)),
        "home_adv": float(p.home_adv), "rho": float(p.rho),
    }


def load_groups(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    g = con.execute("select group_letter, team_country from group_standings").df()
    return {k: list(v) for k, v in g.groupby("group_letter")["team_country"]}


def _scoreline(model: dict, h: str, a: str) -> np.ndarray:
    lam = math.exp(model["attack"][h] - model["defense"][a])  # neutral venue
    mu = math.exp(model["attack"][a] - model["defense"][h])
    rho = model["rho"]
    i = np.arange(MAXG + 1)
    fac = np.array([math.factorial(k) for k in i])
    ph = np.exp(-lam) * lam ** i / fac
    pa = np.exp(-mu) * mu ** i / fac
    mat = np.outer(ph, pa)
    mat[0, 0] *= 1 - lam * mu * rho
    mat[0, 1] *= 1 + lam * rho
    mat[1, 0] *= 1 + mu * rho
    mat[1, 1] *= 1 - rho
    return mat / mat.sum()


def _precompute(model: dict, teams: list[str]) -> dict:
    """For each ordered pair: goal-sampling cumdist + shootout win prob (home)."""
    gh, ga = np.divmod(np.arange((MAXG + 1) ** 2), MAXG + 1)
    pre = {}
    for h in teams:
        for a in teams:
            if h == a:
                continue
            mat = _scoreline(model, h, a)
            flat = mat.ravel()
            p_home = np.tril(mat, -1).sum()
            p_away = np.triu(mat, 1).sum()
            pre[(h, a)] = (flat.cumsum(), p_home / (p_home + p_away))
    return {"pre": pre, "gh": gh, "ga": ga}


def _standard_bracket(seeds: list) -> list:
    """Order seeds (best-first) into standard single-elim bracket positions."""
    pos = [0]
    size = 1
    while size < len(seeds):
        size *= 2
        pos = [x for s in pos for x in (s, size - 1 - s)]
    return [seeds[i] for i in pos]


def simulate_once(model: dict, groups: dict, pre: dict, rng: np.random.Generator) -> dict:
    cum_lookup, gh_arr, ga_arr = pre["pre"], pre["gh"], pre["ga"]
    group_rank = {}  # group -> ordered teams
    thirds = []
    for g, teams in groups.items():
        pts = dict.fromkeys(teams, 0)
        gd = dict.fromkeys(teams, 0)
        gf = dict.fromkeys(teams, 0)
        for x in range(len(teams)):
            for y in range(x + 1, len(teams)):
                h, a = teams[x], teams[y]
                k = np.searchsorted(cum_lookup[(h, a)][0], rng.random())
                hg, ag = int(gh_arr[k]), int(ga_arr[k])
                gf[h] += hg
                gf[a] += ag
                gd[h] += hg - ag
                gd[a] += ag - hg
                if hg > ag:
                    pts[h] += 3
                elif ag > hg:
                    pts[a] += 3
                else:
                    pts[h] += 1
                    pts[a] += 1
        order = sorted(teams, key=lambda t: (pts[t], gd[t], gf[t], rng.random()), reverse=True)
        group_rank[g] = order
        thirds.append((order[2], pts[order[2]], gd[order[2]], gf[order[2]]))

    winners = [group_rank[g][0] for g in groups]
    runners = [group_rank[g][1] for g in groups]
    best_thirds = [t[0] for t in sorted(thirds, key=lambda r: (r[1], r[2], r[3], rng.random()),
                                        reverse=True)[:8]]
    qualifiers = winners + runners + best_thirds

    reached = {t: "advance" for t in qualifiers}
    # seed: winners, then runners, then thirds (each already roughly in strength order)
    seeds = winners + runners + best_thirds
    bracket = _standard_bracket(seeds)

    round_idx = 1
    while len(bracket) > 1:
        nxt = []
        for i in range(0, len(bracket), 2):
            h, a = bracket[i], bracket[i + 1]
            cum, pen = cum_lookup[(h, a)]
            k = np.searchsorted(cum, rng.random())
            hg, ag = int(gh_arr[k]), int(ga_arr[k])
            winner = h if (hg > ag or (hg == ag and rng.random() < pen)) else a
            nxt.append(winner)
            reached[winner] = ROUND_NAMES[min(round_idx, len(ROUND_NAMES) - 1)]
        bracket = nxt
        round_idx += 1
    return reached


def run(con: duckdb.DuckDBPyConnection, n_sims: int = 10000, seed: int = 0) -> pd.DataFrame:
    model = load_model(con)
    groups = load_groups(con)
    teams = sorted({t for ts in groups.values() for t in ts})
    # fill any missing rating with the weakest WC rating
    wa, wd = min(model["attack"].values()), min(model["defense"].values())
    for t in teams:
        model["attack"].setdefault(t, wa)
        model["defense"].setdefault(t, wd)
    pre = _precompute(model, teams)

    rng = np.random.default_rng(seed)
    tally = {t: dict.fromkeys(ROUND_NAMES, 0) for t in teams}
    order = ["advance", "r16", "qf", "sf", "final", "champion"]
    rank = {r: i for i, r in enumerate(order)}
    for _ in range(n_sims):
        reached = simulate_once(model, groups, pre, rng)
        for t, r in reached.items():
            # count team for every round up to the one it reached
            for rr in order[: rank[r] + 1]:
                tally[t][rr] += 1

    rows = [{"team_country": t, **{f"p_{r}": tally[t][r] / n_sims for r in order}} for t in teams]
    df = pd.DataFrame(rows).sort_values("p_champion", ascending=False).reset_index(drop=True)
    con.execute("CREATE OR REPLACE TABLE sim_results AS SELECT * FROM df")
    return df
