"""FastAPI service exposing the World Cup 2026 marts as JSON for the web app.

Read-only over DuckDB (a fresh connection per request — DuckDB allows many
concurrent readers, and the dashboard/pipeline can hold the file too).

Run:  uvicorn wc2026.api:app --reload --port 8000
"""

from __future__ import annotations

import math

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from wc2026 import branding, config

app = FastAPI(title="World Cup 2026 API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow the Next.js dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(config.get_database_target(), read_only=True)


def rows(sql: str, params: list | None = None) -> list[dict]:
    con = _con()
    try:
        df = con.execute(sql, params or []).df()
    finally:
        con.close()
    return df.to_dict(orient="records")


def _add_flags(records: list[dict], key: str = "team_country") -> list[dict]:
    for r in records:
        r["flag"] = branding.flag_url(r.get(key, ""), "w80")
        r["flag_iso"] = branding.FLAG_ISO.get(r.get(key, ""))
    return records


@app.get("/api/health")
def health() -> dict:
    try:
        rows("select 1")
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"warehouse unavailable: {e}") from e


@app.get("/api/teams")
def teams() -> list[dict]:
    return _add_flags(rows(
        """
        select d.team_country, d.confederation, d.manager, d.squad_size, d.avg_age,
               v.total_value_m, s.overall as strength, s.elo
        from dim_national_team d
        left join team_market_value v using (team_country)
        left join model_team_strength s using (team_country)
        order by s.overall desc nulls last
        """
    ))


@app.get("/api/groups")
def groups() -> dict:
    data = _add_flags(rows("select * from group_standings order by group_letter, points desc, goal_diff desc"))
    out: dict[str, list] = {}
    for r in data:
        out.setdefault(r["group_letter"], []).append(r)
    return out


@app.get("/api/fixtures")
def fixtures(group: str | None = None, team: str | None = None) -> list[dict]:
    data = rows("select * from fct_fixture order by match_date, kickoff_local")
    if group:
        data = [r for r in data if r.get("group_letter") == group]
    if team:
        data = [r for r in data if team in (r.get("home_team"), r.get("away_team"))]
    for r in data:
        r["home_flag"] = branding.flag_url(r.get("home_team", ""), "w80")
        r["away_flag"] = branding.flag_url(r.get("away_team", ""), "w80")
    return data


@app.get("/api/players")
def players(team: str | None = None, position: str | None = None) -> list[dict]:
    data = rows("select * from dim_player order by market_value_eur desc nulls last")
    if team:
        data = [r for r in data if r.get("team_country") == team]
    if position:
        data = [r for r in data if r.get("primary_position") == position]
    return _add_flags(data)


@app.get("/api/lineup/{team}")
def lineup(team: str) -> list[dict]:
    return rows(
        "select position, shirt_number, player_name, club, market_value_eur, photo_url, "
        "formation from predicted_xi where team_country = ? order by pos_rank, shirt_number",
        [team],
    )


@app.get("/api/predictions")
def predictions() -> list[dict]:
    return _add_flags(rows("select * from sim_results order by p_champion desc"))


@app.get("/api/strengths")
def strengths() -> list[dict]:
    return _add_flags(rows(
        "select s.team_country, s.attack, s.defense, s.overall, s.elo, v.total_value_m "
        "from model_team_strength s left join team_market_value v using (team_country) "
        "order by s.overall desc"
    ))


@app.get("/api/predict")
def predict(home: str = Query(...), away: str = Query(...)) -> dict:
    """Dixon-Coles neutral-venue head-to-head from the persisted strengths."""
    s = {r["team_country"]: r for r in rows(
        "select team_country, attack, defense from model_team_strength")}
    p = rows("select home_adv, rho from model_params")
    if home not in s or away not in s or not p:
        raise HTTPException(404, "unknown team or model not built")
    rho = p[0]["rho"]
    lam = math.exp(s[home]["attack"] - s[away]["defense"])
    mu = math.exp(s[away]["attack"] - s[home]["defense"])
    mg = 9
    fac = [math.factorial(k) for k in range(mg + 1)]
    ph = [math.exp(-lam) * lam ** k / fac[k] for k in range(mg + 1)]
    pa = [math.exp(-mu) * mu ** k / fac[k] for k in range(mg + 1)]
    p_home = p_draw = p_away = 0.0
    for i in range(mg + 1):
        for j in range(mg + 1):
            pij = ph[i] * pa[j]
            if i == 0 and j == 0:
                pij *= 1 - lam * mu * rho
            elif i == 0 and j == 1:
                pij *= 1 + lam * rho
            elif i == 1 and j == 0:
                pij *= 1 + mu * rho
            elif i == 1 and j == 1:
                pij *= 1 - rho
            if i > j:
                p_home += pij
            elif i == j:
                p_draw += pij
            else:
                p_away += pij
    total = p_home + p_draw + p_away
    return {
        "home": home, "away": away,
        "p_home": p_home / total, "p_draw": p_draw / total, "p_away": p_away / total,
        "xg_home": lam, "xg_away": mu,
        "home_flag": branding.flag_url(home, "w80"), "away_flag": branding.flag_url(away, "w80"),
    }


@app.get("/api/historical")
def historical() -> list[dict]:
    return rows(
        "select player_name, team, goals, assists, minutes, goals_per90 "
        "from fct_player_stats order by goals desc nulls last limit 25"
    )
