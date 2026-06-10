"""Dixon-Coles model for international football.

Goals are modelled as Poisson from per-team attack/defense strengths plus a
home-advantage term (zeroed at neutral venues), with the Dixon-Coles low-score
correction (rho) and exponential time-decay weighting so recent form counts
more. Fitted by weighted maximum likelihood.

Names use the international-results dataset's spelling; ``ALIASES`` maps our 6
differing WC team names onto it.
"""

from __future__ import annotations

import math

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import minimize

# our team name -> international-results dataset name
ALIASES = {
    "Congo DR": "DR Congo",
    "Czechia": "Czech Republic",
    "Côte d'Ivoire": "Ivory Coast",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
}

REF_DATE = pd.Timestamp("2026-06-10")


def load_matches(con: duckdb.DuckDBPyConnection, since: str = "2010-01-01") -> pd.DataFrame:
    """Played matches since a cutoff, restricted to FIFA-recognized teams.

    A team counts as FIFA-recognized if it has ever played a World Cup
    (qualification or finals) match — this cleanly excludes CONIFA / non-FIFA
    sides (Padania, Abkhazia, ...) that only play each other and otherwise
    pollute the strength scale.
    """
    return con.execute(
        """
        with fifa as (
            select home_team as team from raw_intl_results where tournament like '%World Cup%'
            union
            select away_team from raw_intl_results where tournament like '%World Cup%'
        )
        select cast(date as date) as match_date, home_team, away_team,
               cast(home_score as integer) as hg, cast(away_score as integer) as ag,
               neutral
        from raw_intl_results
        where home_score is not null and date >= ?
          and home_team in (select team from fifa)
          and away_team in (select team from fifa)
        """,
        [since],
    ).df()


def fit(matches: pd.DataFrame, half_life_years: float = 2.5, min_matches: int = 20,
        prior_attack: dict | None = None, prior_defense: dict | None = None,
        lam_prior: float = 0.0, lam_ridge: float = 0.01,
        ref_date: pd.Timestamp | None = None) -> dict:
    """Fit Dixon-Coles by time-weighted MLE.

    Optional value-prior shrinkage: ``prior_attack``/``prior_defense`` give a
    per-team target (from squad value) and ``lam_prior`` how hard to pull toward
    it. Teams with more matches resist the pull (their likelihood dominates), so
    the effect is automatic data-dependent shrinkage. ``lam_ridge`` is a small
    pull toward 0 for every team (numerical stability).
    """
    counts = pd.concat([matches["home_team"], matches["away_team"]]).value_counts()
    keep = set(counts[counts >= min_matches].index)
    m = matches[matches["home_team"].isin(keep) & matches["away_team"].isin(keep)].copy()

    teams = sorted(set(m["home_team"]) | set(m["away_team"]))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    hi = m["home_team"].map(idx).to_numpy()
    ai = m["away_team"].map(idx).to_numpy()
    x = m["hg"].to_numpy(float)
    y = m["ag"].to_numpy(float)
    not_neutral = (~m["neutral"].astype(bool)).to_numpy(float)
    ref = ref_date if ref_date is not None else REF_DATE
    age_yrs = (ref - pd.to_datetime(m["match_date"])).dt.days.to_numpy() / 365.25
    w = 0.5 ** (age_yrs / half_life_years)

    # value-prior target vectors (0 where no prior given)
    a_prior = np.array([(prior_attack or {}).get(t, 0.0) for t in teams])
    d_prior = np.array([(prior_defense or {}).get(t, 0.0) for t in teams])
    has_prior = np.array([t in (prior_attack or {}) for t in teams], float)

    m00 = (x == 0) & (y == 0)
    m01 = (x == 0) & (y == 1)
    m10 = (x == 1) & (y == 0)
    m11 = (x == 1) & (y == 1)

    def nll(p):
        att = p[:n] - p[:n].mean()
        deff = p[n:2 * n] - p[n:2 * n].mean()
        home, rho = p[2 * n], p[2 * n + 1]
        lam = np.exp(att[hi] - deff[ai] + home * not_neutral)
        mu = np.exp(att[ai] - deff[hi])
        ll = x * np.log(lam) - lam + y * np.log(mu) - mu
        tau = np.ones_like(lam)
        tau[m00] = 1 - lam[m00] * mu[m00] * rho
        tau[m01] = 1 + lam[m01] * rho
        tau[m10] = 1 + mu[m10] * rho
        tau[m11] = 1 - rho
        ll = ll + np.log(np.clip(tau, 1e-10, None))
        penalty = lam_prior * np.sum(has_prior * ((att - a_prior) ** 2 + (deff - d_prior) ** 2))
        penalty += lam_ridge * np.sum(att ** 2 + deff ** 2)
        return -np.sum(w * ll) + penalty

    # warm start: attack ~ log(avg goals scored), defense ~ log(avg goals conceded)
    gf = m.groupby("home_team")["hg"].mean().add(m.groupby("away_team")["ag"].mean(), fill_value=0) / 2
    a0 = np.array([np.log(max(gf.get(t, 1.3), 0.3)) for t in teams])
    a0 -= a0.mean()
    p0 = np.concatenate([a0, -a0, [0.25, -0.05]])
    bounds = [(-3, 3)] * (2 * n) + [(-1, 1), (-0.2, 0.2)]
    res = minimize(nll, p0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 1500, "maxfun": 400000, "ftol": 1e-9})

    att = res.x[:n] - res.x[:n].mean()
    deff = res.x[n:2 * n] - res.x[n:2 * n].mean()
    return {
        "teams": teams, "idx": idx,
        "attack": dict(zip(teams, att)), "defense": dict(zip(teams, deff)),
        "home_adv": float(res.x[2 * n]), "rho": float(res.x[2 * n + 1]),
        "converged": bool(res.success), "n_matches": len(m), "n_teams": n,
    }


def _resolve(model: dict, team: str) -> str:
    return ALIASES.get(team, team)


def scoreline_matrix(model: dict, home: str, away: str, neutral: bool = True,
                     max_goals: int = 10) -> np.ndarray:
    """P(home goals = i, away goals = j) matrix with the DC correction applied."""
    h, a = _resolve(model, home), _resolve(model, away)
    lam = np.exp(model["attack"][h] - model["defense"][a] + (0 if neutral else model["home_adv"]))
    mu = np.exp(model["attack"][a] - model["defense"][h])
    rho = model["rho"]
    i = np.arange(max_goals + 1)
    ph = np.exp(-lam) * lam ** i / np.array([math.factorial(k) for k in i])
    pa = np.exp(-mu) * mu ** i / np.array([math.factorial(k) for k in i])
    mat = np.outer(ph, pa)
    mat[0, 0] *= 1 - lam * mu * rho
    mat[0, 1] *= 1 + lam * rho
    mat[1, 0] *= 1 + mu * rho
    mat[1, 1] *= 1 - rho
    return mat / mat.sum()


def outcome_probabilities(model: dict, home: str, away: str, neutral: bool = True) -> dict:
    """Return P(home win/draw/away win) + expected goals for a matchup."""
    mat = scoreline_matrix(model, home, away, neutral)
    p_home = float(np.tril(mat, -1).sum())
    p_away = float(np.triu(mat, 1).sum())
    p_draw = float(np.trace(mat))
    i = np.arange(mat.shape[0])
    return {
        "p_home": p_home, "p_draw": p_draw, "p_away": p_away,
        "xg_home": float((mat.sum(1) * i).sum()), "xg_away": float((mat.sum(0) * i).sum()),
    }


def build_value_prior(con: duckdb.DuckDBPyConnection, model: dict) -> tuple[dict, dict]:
    """Value-implied attack/defense targets for WC teams (for shrinkage).

    Regresses the results-fitted attack/defense onto a squad-value z-score, so
    the prior sits on the model's own scale: it's where a team's squad value
    predicts its strength should be.
    """
    df = con.execute("select team_country, total_value_m from team_market_value").df()
    df["ds"] = df["team_country"].map(lambda t: ALIASES.get(t, t))
    df["vz"] = np.log(df["total_value_m"].clip(lower=1))
    df["vz"] = (df["vz"] - df["vz"].mean()) / df["vz"].std()
    df["att"] = df["ds"].map(model["attack"])
    df["deff"] = df["ds"].map(model["defense"])
    sub = df.dropna(subset=["att", "deff"])
    ba, ia = np.polyfit(sub["vz"], sub["att"], 1)
    bd, id_ = np.polyfit(sub["vz"], sub["deff"], 1)
    prior_a = {r.ds: ia + ba * r.vz for r in df.itertuples() if pd.notna(r.vz)}
    prior_d = {r.ds: id_ + bd * r.vz for r in df.itertuples() if pd.notna(r.vz)}
    return prior_a, prior_d


def backtest(con: duckdb.DuckDBPyConnection,
             half_lives=(1.5, 2.0, 2.5, 3.0, 4.0)) -> pd.DataFrame:
    """Grid-search half-life by predicting WC2018 & WC2022 (log-loss + accuracy).

    For each tournament, fit only on matches before kickoff (no leakage) and
    predict the actual group+knockout results. Value prior is omitted here — we
    lack period-correct squad values — so this tunes the time-decay/DC core.
    """
    full = con.execute(
        """
        with fifa as (
            select home_team as team from raw_intl_results where tournament like '%World Cup%'
            union select away_team from raw_intl_results where tournament like '%World Cup%'
        )
        select cast(date as date) as match_date, home_team, away_team,
               cast(home_score as integer) as hg, cast(away_score as integer) as ag,
               neutral, tournament
        from raw_intl_results
        where home_score is not null
          and home_team in (select team from fifa) and away_team in (select team from fifa)
        """
    ).df()
    full["match_date"] = pd.to_datetime(full["match_date"])
    tourneys = [("WC2018", "2018-06-14", "2018-07-16"), ("WC2022", "2022-11-20", "2022-12-19")]

    rows = []
    for hl in half_lives:
        ll, acc, n = 0.0, 0, 0
        for _, tstart, tend in tourneys:
            ts, te = pd.Timestamp(tstart), pd.Timestamp(tend)
            train = full[(full.match_date < ts) & (full.match_date >= ts - pd.Timedelta(days=365 * 8))]
            model = fit(train, half_life_years=hl, ref_date=ts)
            wc = full[(full.tournament == "FIFA World Cup") & (full.match_date >= ts)
                      & (full.match_date <= te)]
            for r in wc.itertuples():
                if r.home_team not in model["attack"] or r.away_team not in model["attack"]:
                    continue
                o = outcome_probabilities(model, r.home_team, r.away_team, neutral=True)
                probs = [o["p_home"], o["p_draw"], o["p_away"]]
                actual = 0 if r.hg > r.ag else (2 if r.ag > r.hg else 1)
                ll += -np.log(max(probs[actual], 1e-9))
                acc += int(np.argmax(probs) == actual)
                n += 1
        rows.append({"half_life": hl, "log_loss": round(ll / n, 4),
                     "accuracy": round(acc / n, 3), "n_matches": n})
    return pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)


def build_and_persist_model(con: duckdb.DuckDBPyConnection, half_life_years: float = 3.0,
                            lam_prior: float = 2.0, since: str = "2014-01-01") -> int:
    """Fit the final value-shrunk model and persist WC-team strengths + params.

    Writes ``model_team_strength`` (our team names) and ``model_params``.
    """
    matches = load_matches(con, since=since)
    base = fit(matches, half_life_years=half_life_years)
    prior_a, prior_d = build_value_prior(con, base)
    final = fit(matches, half_life_years=half_life_years,
                prior_attack=prior_a, prior_defense=prior_d, lam_prior=lam_prior)

    # optional Elo cross-check rating (keyed by dataset names)
    try:
        elo = dict(con.execute("select team, elo from team_elo").fetchall())
    except Exception:  # noqa: BLE001 — team_elo may not be built yet
        elo = {}

    wc = [r[0] for r in con.execute("select team_country from dim_national_team").fetchall()]
    rows = []
    for t in wc:
        ds = ALIASES.get(t, t)
        if ds in final["attack"]:
            rows.append({"team_country": t, "attack": final["attack"][ds],
                         "defense": final["defense"][ds],
                         "overall": final["attack"][ds] + final["defense"][ds],
                         "elo": elo.get(ds)})
    df = pd.DataFrame(rows)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE model_team_strength AS "
                "SELECT team_country, attack, defense, overall, elo FROM df")
    con.execute(
        "CREATE OR REPLACE TABLE model_params AS "
        f"SELECT {final['home_adv']} as home_adv, {final['rho']} as rho, "
        f"{half_life_years} as half_life, {lam_prior} as lam_prior"
    )
    return len(df)


def strength_table(model: dict) -> pd.DataFrame:
    """Per-team attack/defense and an overall rating (attack + defense)."""
    df = pd.DataFrame({
        "team": model["teams"],
        "attack": [model["attack"][t] for t in model["teams"]],
        "defense": [model["defense"][t] for t in model["teams"]],
    })
    df["overall"] = df["attack"] + df["defense"]
    return df.sort_values("overall", ascending=False).reset_index(drop=True)
