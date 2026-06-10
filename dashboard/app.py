"""Streamlit dashboard — World Cup 2026 analytics, live pipeline view.

Run:  streamlit run dashboard/app.py
Use the "Refresh data" button to re-read the warehouse as the pipeline runs.
"""

import math

import duckdb
import numpy as np
import pandas as pd
import streamlit as st

from wc2026 import branding, config

st.set_page_config(page_title="World Cup 2026 Analytics", page_icon="⚽", layout="wide")
st.markdown(branding.CSS, unsafe_allow_html=True)
st.markdown(
    branding.banner_html(
        "FIFA WORLD CUP 2026 — ANALYTICS",
        "Squads · groups · schedule · market values · predicted XIs · model forecasts",
    ),
    unsafe_allow_html=True,
)


def flagged(df, team_col="team_country", size="w40"):
    """Attach a flag-URL column for st.column_config.ImageColumn."""
    return branding.add_flag_column(df, team_col=team_col, size=size)


FLAG_COL = st.column_config.ImageColumn("", width="small")


@st.cache_resource
def _connect():
    # read-only so the dashboard can read while Dagster writes between runs
    try:
        return duckdb.connect(config.get_database_target(), read_only=True)
    except Exception:
        return duckdb.connect(config.get_database_target())


def q(sql: str) -> pd.DataFrame:
    return _connect().execute(sql).df()


def table_exists(name: str) -> bool:
    try:
        q(f"select 1 from {name} limit 1")
        return True
    except Exception:
        return False


def row_count(name: str) -> int | None:
    try:
        return int(q(f"select count(*) as n from {name}")["n"].iloc[0])
    except Exception:
        return None


with st.sidebar:
    st.header("Pipeline status")
    if st.button("🔄 Refresh data"):
        st.cache_resource.clear()
        st.rerun()
    EXPECTED = {
        "raw_squads": "Squads (raw)",
        "dim_player": "Players (dim)",
        "dim_national_team": "Teams (dim)",
        "group_standings": "Group standings",
        "fct_fixture": "Fixtures",
        "model_team_strength": "Model strengths",
        "sim_results": "Title odds",
        "fct_player_stats": "Hist. stats (mart)",
        "fct_match": "Matches",
    }
    for tbl, label in EXPECTED.items():
        n = row_count(tbl)
        st.write(f"{'✅' if n else '⏳'} **{label}** — {n if n is not None else 'not built'}")

(tab_overview, tab_predict, tab_groups, tab_schedule, tab_teams, tab_players,
 tab_lineup, tab_history, tab_guide) = st.tabs(
    ["Overview", "Predictions", "Groups", "Schedule", "Teams", "Players", "Lineup",
     "Historical", "📖 Guide"]
)

# ---------------------------------------------------------------- Overview
with tab_overview:
    if table_exists("dim_player"):
        players = q("select * from dim_player")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Players", len(players))
        c2.metric("Teams", players["team_country"].nunique())
        c3.metric("Avg age", round(players["age"].mean(), 1))
        if "market_value_eur" in players and players["market_value_eur"].notna().any():
            c4.metric("Total squad value", f"€{players['market_value_eur'].sum() / 1e9:.1f}bn")
            mvp = players.loc[players["market_value_eur"].idxmax()]
            st.caption(
                f"💎 Most valuable: **{mvp['player_name']}** ({mvp['team_country']}) — "
                f"€{mvp['market_value_eur'] / 1e6:.0f}m"
            )
        else:
            c4.metric("Clubs represented", players["club"].nunique())
        if table_exists("dim_national_team"):
            st.subheader("Qualified teams by confederation")
            conf = q(
                "select confederation, count(*) teams from dim_national_team "
                "where confederation is not null group by 1 order by teams desc"
            )
            st.bar_chart(conf.set_index("confederation")["teams"])
    else:
        st.info("Run the pipeline to populate players: "
                "`dagster asset materialize -m wc2026.definitions --select raw_squads,dbt_marts`")

# ---------------------------------------------------------------- Predictions
def _match_probs(strengths, params, home, away, max_goals=8):
    """Dixon-Coles W/D/L + expected goals for a neutral-venue matchup."""
    att, dfn, rho = strengths["attack"], strengths["defense"], params["rho"]
    lam = math.exp(att[home] - dfn[away])
    mu = math.exp(att[away] - dfn[home])
    i = np.arange(max_goals + 1)
    fac = np.array([math.factorial(k) for k in i])
    mat = np.outer(np.exp(-lam) * lam ** i / fac, np.exp(-mu) * mu ** i / fac)
    mat[0, 0] *= 1 - lam * mu * rho
    mat[0, 1] *= 1 + lam * rho
    mat[1, 0] *= 1 + mu * rho
    mat[1, 1] *= 1 - rho
    mat /= mat.sum()
    return (float(np.tril(mat, -1).sum()), float(np.trace(mat)),
            float(np.triu(mat, 1).sum()), lam, mu)


with tab_predict:
    if table_exists("sim_results"):
        st.subheader("🏆 Title odds — 20,000 Monte-Carlo simulations")
        st.caption("Dixon-Coles goal model (value-shrunk strengths) → simulate groups → knockouts.")
        sim = q("select * from sim_results order by p_champion desc")
        top = sim.head(16).assign(Champion=(sim["p_champion"] * 100).round(1))
        st.bar_chart(top.set_index("team_country")["Champion"])
        show = sim.head(20).copy()
        for c in ["p_advance", "p_qf", "p_sf", "p_final", "p_champion"]:
            show[c] = (show[c] * 100).round(1)
        show = flagged(show)
        st.dataframe(
            show[["flag", "team_country", "p_advance", "p_qf", "p_sf", "p_final", "p_champion"]],
            hide_index=True, use_container_width=True,
            column_config={
                "flag": FLAG_COL, "team_country": "Team", "p_advance": "Advance %",
                "p_qf": "QF %", "p_sf": "SF %", "p_final": "Final %", "p_champion": "Champion %",
            },
        )
    else:
        st.info("Run the model + simulation assets to populate predictions.")

    if table_exists("model_team_strength"):
        st.divider()
        st.subheader("⚔️ Head-to-head predictor (neutral venue)")
        strengths = {
            "attack": dict(q("select team_country, attack from model_team_strength").values),
            "defense": dict(q("select team_country, defense from model_team_strength").values),
        }
        params = q("select home_adv, rho from model_params").iloc[0].to_dict()
        opts = sorted(strengths["attack"])
        c1, c2 = st.columns(2)
        home = c1.selectbox("Team A", opts, index=opts.index("Argentina") if "Argentina" in opts else 0)
        away = c2.selectbox("Team B", opts, index=opts.index("France") if "France" in opts else 1)
        if home != away:
            ph, pdr, pa, lam, mu = _match_probs(strengths, params, home, away)
            st.markdown(
                branding.score_card_html(
                    home, away, branding.flag_url(home), branding.flag_url(away),
                    f"{lam:.1f} – {mu:.1f}", "xG",
                ),
                unsafe_allow_html=True,
            )
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{home} win", f"{ph * 100:.0f}%")
            m2.metric("Draw", f"{pdr * 100:.0f}%")
            m3.metric(f"{away} win", f"{pa * 100:.0f}%")

        st.divider()
        st.subheader("📊 Strength ratings cross-check")
        st.caption("Three signals. Dixon-Coles & Elo agree ~0.93 (both results-based); "
                   "market value is the independent talent signal.")
        ratings = q(
            "select s.team_country, round(s.overall, 2) as dc_overall, "
            "round(s.elo) as elo, round(v.total_value_m) as value_m "
            "from model_team_strength s "
            "left join team_market_value v using (team_country) "
            "order by s.overall desc"
        )
        ratings = flagged(ratings)
        st.dataframe(
            ratings, hide_index=True, use_container_width=True,
            column_config={
                "flag": FLAG_COL, "team_country": "Team", "dc_overall": "DC strength",
                "elo": "Elo", "value_m": "Squad value (€m)",
            },
        )
    else:
        st.info("Model strengths not built yet.")

# ---------------------------------------------------------------- Groups
with tab_groups:
    if table_exists("group_standings"):
        gs = q("select * from group_standings")
        st.caption("Standings update live as matches are played (pre-tournament = all zeros).")
        letters = sorted(gs["group_letter"].unique())
        # show groups in a 3-column grid
        for i in range(0, len(letters), 3):
            cols = st.columns(3)
            for col, letter in zip(cols, letters[i:i + 3]):
                with col:
                    st.markdown(f"#### Group {letter}")
                    grp = gs[gs["group_letter"] == letter].sort_values(
                        ["points", "goal_diff"], ascending=False)
                    grp = flagged(grp)[
                        ["flag", "team_country", "played", "won", "drawn", "lost",
                         "goal_diff", "points"]
                    ]
                    st.dataframe(
                        grp, hide_index=True, use_container_width=True,
                        column_config={
                            "flag": FLAG_COL, "team_country": "Team", "played": "P",
                            "won": "W", "drawn": "D", "lost": "L", "goal_diff": "GD",
                            "points": "Pts",
                        },
                    )
    else:
        st.info("Group standings not built yet.")

# ---------------------------------------------------------------- Schedule
with tab_schedule:
    if table_exists("fct_fixture"):
        fx = q("select * from fct_fixture")
        c1, c2 = st.columns(2)
        grp_opts = ["All"] + sorted(fx["group_letter"].dropna().unique())
        gpick = c1.selectbox("Group", grp_opts)
        team_opts = ["All"] + sorted(set(fx["home_team"]) | set(fx["away_team"]))
        tpick = c2.selectbox("Team", team_opts)
        view = fx
        if gpick != "All":
            view = view[view["group_letter"] == gpick]
        if tpick != "All":
            view = view[(view["home_team"] == tpick) | (view["away_team"] == tpick)]
        view = view.sort_values(["match_date", "kickoff_local"])
        st.caption(f"{len(view)} matches — broadcast-style scoreboard")
        cards, current_date = [], None
        for r in view.itertuples():
            d = str(r.match_date)[:10]
            if d != current_date:
                cards.append(f'<h4 style="margin:14px 0 2px">{d}</h4>')
                current_date = d
            if r.status == "played" and pd.notna(r.home_score):
                score = f"{int(r.home_score)} – {int(r.away_score)}"
            else:
                score = r.kickoff_local or "vs"
            meta = f"Grp {r.group_letter or '–'}<br>{(r.venue or '').split(' (')[0]}"
            cards.append(branding.score_card_html(
                r.home_team, r.away_team,
                branding.flag_url(r.home_team), branding.flag_url(r.away_team), score, meta))
        st.markdown("\n".join(cards), unsafe_allow_html=True)
    else:
        st.info("Schedule not built yet.")

# ---------------------------------------------------------------- Teams
with tab_teams:
    if table_exists("team_squad_summary"):
        ts = q("select * from team_squad_summary order by avg_age")
        confs = ["All"] + sorted(ts["confederation"].dropna().unique())
        pick = st.selectbox("Confederation", confs)
        view = ts if pick == "All" else ts[ts["confederation"] == pick]
        st.subheader(f"Squad profiles ({len(view)} teams)")
        tv = flagged(view)
        st.dataframe(
            tv[["flag", "team_country", "confederation", "manager", "squad_size", "avg_age",
                "distinct_clubs", "goalkeepers", "defenders", "midfielders", "forwards"]],
            use_container_width=True, hide_index=True,
            column_config={"flag": FLAG_COL, "team_country": "Team"},
        )
        st.subheader("Average squad age")
        st.bar_chart(view.set_index("team_country")["avg_age"])

        if table_exists("team_market_value"):
            st.subheader("Most valuable squads (€m, Transfermarkt)")
            mv = q("select team_country, total_value_m, top_player, top_player_value_m "
                   "from team_market_value order by total_value_m desc")
            st.bar_chart(mv.set_index("team_country")["total_value_m"])
            st.dataframe(mv, use_container_width=True, hide_index=True)
    else:
        st.info("Team squad profiles not built yet.")

# ---------------------------------------------------------------- Players
with tab_players:
    if table_exists("dim_player"):
        players = q("select * from dim_player")
        col1, col2 = st.columns(2)
        team = col1.selectbox("National team", ["All"] + sorted(players["team_country"].unique()))
        pos = col2.selectbox("Position", ["All"] + sorted(players["primary_position"].dropna().unique()))
        view = players
        if team != "All":
            view = view[view["team_country"] == team]
        if pos != "All":
            view = view[view["primary_position"] == pos]
        has_value = "market_value_eur" in view and view["market_value_eur"].notna().any()
        if has_value:
            view = view.sort_values("market_value_eur", ascending=False, na_position="last")
            view = view.assign(value_m=(view["market_value_eur"] / 1e6).round(1))
        st.caption(f"{len(view)} players")
        view = flagged(view)
        cols = ["photo_url", "player_name", "flag", "team_country", "position", "age", "club"]
        cols += ["value_m"] if has_value else []
        cols = [c for c in cols if c in view.columns]
        st.dataframe(
            view[cols],
            use_container_width=True, hide_index=True,
            column_config={
                "photo_url": st.column_config.ImageColumn("Photo"),
                "flag": FLAG_COL, "team_country": "Team",
                "value_m": st.column_config.NumberColumn("Value (€m)", format="%.1f"),
            },
        )
        c1, c2 = st.columns(2)
        c1.subheader("Top clubs by players selected")
        c1.dataframe(view["club"].value_counts().head(10).rename_axis("club").reset_index(name="players"),
                     hide_index=True, use_container_width=True)
        c2.subheader("Youngest players")
        c2.dataframe(view.nsmallest(10, "age")[["player_name", "team_country", "age", "club"]],
                     hide_index=True, use_container_width=True)
    else:
        st.info("Players not built yet.")

# ---------------------------------------------------------------- Lineup
with tab_lineup:
    if table_exists("predicted_xi"):
        teams = q("select distinct team_country from predicted_xi order by 1")["team_country"]
        team = st.selectbox("National team", list(teams), key="lineup_team")
        xi = q(
            "select position, shirt_number, player_name, club, market_value_eur, photo_url, formation "
            f"from predicted_xi where team_country = '{team.replace(chr(39), chr(39) * 2)}' "
            "order by pos_rank, shirt_number"
        )
        formation_str = xi["formation"].iloc[0] if len(xi) else "?"
        st.markdown(
            f'<h3><img src="{branding.flag_url(team, "w40")}" style="height:24px;'
            f'vertical-align:middle;border-radius:2px"> {team} &nbsp;·&nbsp; '
            f'<code>{formation_str}</code></h3>',
            unsafe_allow_html=True,
        )
        st.caption("Predicted XI from the team's most recent friendly (replaced by real lineups once matches start).")

        view = xi.assign(value_m=(xi["market_value_eur"] / 1e6).round(1))
        st.dataframe(
            view[["photo_url", "shirt_number", "position", "player_name", "club", "value_m"]],
            use_container_width=True, hide_index=True,
            column_config={
                "photo_url": st.column_config.ImageColumn("Photo"),
                "shirt_number": st.column_config.NumberColumn("#", format="%d"),
                "position": st.column_config.TextColumn("Pos"),
                "player_name": st.column_config.TextColumn("Player"),
                "club": st.column_config.TextColumn("Club"),
                "value_m": st.column_config.NumberColumn("Value (€m)", format="%.1f"),
            },
        )
    else:
        st.info("Lineups not built yet — run the raw_lineups asset + dbt build.")

# ---------------------------------------------------------------- Historical
with tab_history:
    if table_exists("fct_player_stats"):
        hist = q("select * from fct_player_stats")
        st.subheader("Top scorers — World Cup 2022")
        st.dataframe(
            hist.sort_values("goals", ascending=False)
            .head(15)[["player_name", "team", "goals", "assists", "minutes", "goals_per90"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Historical player stats not built yet.")

# ---------------------------------------------------------------- Guide
with tab_guide:
    st.markdown(
        """
### 📖 User guide

Welcome! This app explores the **FIFA World Cup 2026** on two levels — **players** and
**teams** — from live tournament data through to a predictive model. Here's what each tab does.

| Tab | What you'll find |
|---|---|
| **Overview** | Headline numbers: players, teams, average age, total squad value, and qualified teams by confederation. |
| **Predictions** | 🏆 **Title odds** from 20,000 Monte-Carlo simulations, an interactive **head-to-head predictor** (pick any two teams), and a **strength cross-check** (model vs Elo vs market value). |
| **Groups** | All 12 group tables (A–L). Standings are **zero pre-tournament** and **update live** as matches are played. |
| **Schedule** | All 72 group fixtures as broadcast-style **scoreboard cards** — date, kickoff, group, venue. Filter by group or team. |
| **Teams** | Squad profiles: size, average age, club spread, positional split, **confederation & manager**. Plus most-valuable squads. |
| **Players** | Every one of the ~1,255 players with **photo, position, club, age and market value**. Filter by team & position. |
| **Lineup** | Each team's **predicted starting XI** (from their last friendly) as a teamsheet, with the real formation. |
| **Historical** | World Cup 2022 reference stats (top scorers) — the data the model trains on. |

#### How the predictions work
1. A **Dixon-Coles** goal model is trained on **49,000 international results** (1872–today), weighting recent matches more.
2. Team strengths are nudged toward **squad market value** (an independent talent signal) via shrinkage.
3. The tournament is **simulated 20,000 times** — group stage → real 2026 knockout bracket → champion — to get each team's odds.
4. Backtested on WC2018 & WC2022: **~56% match accuracy**, and the probabilities are **well-calibrated**.

#### Notes & honest caveats
- **Pre-tournament:** standings/live stats are empty until 11 June 2026; everything fills in automatically as matches play.
- **Predicted XIs** come from each team's last friendly and will be replaced by **real lineups** once games start.
- **Flags** for all 48 teams are shown; national-team **crests are trademarked**, so flags are used throughout.
- Market value + photos cover **98.5%** of players (a few hard-to-match names are blank).

*Use the **🔄 Refresh data** button in the sidebar to re-read the warehouse as the pipeline updates.*
"""
    )
