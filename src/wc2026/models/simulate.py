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


# Official 2026 Round-of-32 slot template (matches 73-88). A slot is either a
# fixed group position ("1A"/"2B") or ("T", match_no) for a best-third slot.
R32_TIES = [
    (73, "2A", "2B"), (74, "1E", ("T", 74)), (75, "1F", "2C"), (76, "1C", "2F"),
    (77, "1I", ("T", 77)), (78, "2E", "2I"), (79, "1A", ("T", 79)), (80, "1L", ("T", 80)),
    (81, "1D", ("T", 81)), (82, "1G", ("T", 82)), (83, "2K", "2L"), (84, "1H", "2J"),
    (85, "1B", ("T", 85)), (86, "1J", "2H"), (87, "1K", ("T", 87)), (88, "2D", "2G"),
]
# best-third slots -> the 5 groups whose third-placed team may fill them
THIRD_ALLOWED = {
    74: set("ABCDF"), 77: set("CDFGH"), 79: set("CEFHI"), 80: set("EHIJK"),
    81: set("BEFIJ"), 82: set("AEHIJ"), 85: set("EFGIJ"), 87: set("DEIJL"),
}
# later rounds: (match_no, feeder_match_a, feeder_match_b)
R16 = [(89, 74, 77), (90, 73, 75), (91, 76, 78), (92, 79, 80),
       (93, 83, 84), (94, 81, 82), (95, 86, 88), (96, 85, 87)]
QF = [(97, 89, 90), (98, 93, 94), (99, 91, 92), (100, 95, 96)]
SF = [(101, 97, 98), (102, 99, 100)]
FINAL = (104, 101, 102)


def _assign_thirds(qual_groups: set) -> dict:
    """Bijectively assign the 8 qualifying third-place groups to their slots.

    Respects each slot's allowed-group set (FIFA's bracket constraint) via
    backtracking. Returns {match_no: group_letter}. Falls back to a relaxed
    assignment if (rarely) no perfect matching exists for the combination.
    """
    slots = sorted(THIRD_ALLOWED, key=lambda m: len(THIRD_ALLOWED[m] & qual_groups))
    assign, used = {}, set()

    def bt(i):
        if i == len(slots):
            return True
        for g in THIRD_ALLOWED[slots[i]] & qual_groups:
            if g not in used:
                used.add(g)
                assign[slots[i]] = g
                if bt(i + 1):
                    return True
                used.remove(g)
                del assign[slots[i]]
        return False

    if bt(0):
        return assign
    leftover = list(qual_groups)  # relaxed fallback (rare)
    return {m: leftover[i] for i, m in enumerate(slots)}


def _play(h, a, cum_lookup, gh_arr, ga_arr, rng):
    cum, pen = cum_lookup[(h, a)]
    k = np.searchsorted(cum, rng.random())
    hg, ag = int(gh_arr[k]), int(ga_arr[k])
    return h if (hg > ag or (hg == ag and rng.random() < pen)) else a


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
        third = order[2]
        thirds.append((third, g, pts[third], gd[third], gf[third]))

    # qualifiers: top-2 per group + 8 best thirds. third record = (team, group, pts, gd, gf)
    best_thirds = sorted(thirds, key=lambda r: (r[2], r[3], r[4], rng.random()), reverse=True)[:8]
    qual_groups = {r[1] for r in best_thirds}
    third_by_group = {r[1]: r[0] for r in best_thirds}
    qualifiers = ([group_rank[g][0] for g in groups] + [group_rank[g][1] for g in groups]
                  + [r[0] for r in best_thirds])
    reached = {t: "advance" for t in qualifiers}

    # resolve the official R32 slots into actual teams
    third_assign = _assign_thirds(qual_groups)

    def team_of(slot):
        if isinstance(slot, tuple):  # ("T", match_no) -> best third for that slot
            return third_by_group[third_assign[slot[1]]]
        return group_rank[slot[1]][int(slot[0]) - 1]  # "1A" -> group A, position 0

    win = {}  # match_no -> winning team
    for mno, sa, sb in R32_TIES:
        w = _play(team_of(sa), team_of(sb), cum_lookup, gh_arr, ga_arr, rng)
        win[mno] = w
        reached[w] = "r16"
    for stage, label in [(R16, "qf"), (QF, "sf"), (SF, "final")]:
        for mno, m1, m2 in stage:
            w = _play(win[m1], win[m2], cum_lookup, gh_arr, ga_arr, rng)
            win[mno] = w
            reached[w] = label
    champ = _play(win[FINAL[1]], win[FINAL[2]], cum_lookup, gh_arr, ga_arr, rng)
    reached[champ] = "champion"
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
