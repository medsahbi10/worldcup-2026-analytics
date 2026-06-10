"""Streamlit dashboard — World Cup 2026 analytics, live pipeline view.

Run:  streamlit run dashboard/app.py
Use the "Refresh data" button to re-read the warehouse as the pipeline runs.
"""

import duckdb
import pandas as pd
import streamlit as st

from wc2026 import config

st.set_page_config(page_title="World Cup 2026 Analytics", layout="wide")


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


st.title("⚽ World Cup 2026 — Analytics")

with st.sidebar:
    st.header("Pipeline status")
    if st.button("🔄 Refresh data"):
        st.cache_resource.clear()
        st.rerun()
    EXPECTED = {
        "raw_squads": "Squads (raw)",
        "dim_player": "Players (dim)",
        "dim_national_team": "Teams (dim)",
        "team_squad_summary": "Team profiles",
        "fct_player_stats": "Hist. stats (mart)",
        "fct_match": "Matches",
    }
    for tbl, label in EXPECTED.items():
        n = row_count(tbl)
        st.write(f"{'✅' if n else '⏳'} **{label}** — {n if n is not None else 'not built'}")

tab_overview, tab_teams, tab_players, tab_history = st.tabs(
    ["Overview", "Teams", "Players", "Historical"]
)

# ---------------------------------------------------------------- Overview
with tab_overview:
    if table_exists("dim_player"):
        players = q("select * from dim_player")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Players", len(players))
        c2.metric("Teams", players["team_country"].nunique())
        c3.metric("Avg age", round(players["age"].mean(), 1))
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

# ---------------------------------------------------------------- Teams
with tab_teams:
    if table_exists("team_squad_summary"):
        ts = q("select * from team_squad_summary order by avg_age")
        confs = ["All"] + sorted(ts["confederation"].dropna().unique())
        pick = st.selectbox("Confederation", confs)
        view = ts if pick == "All" else ts[ts["confederation"] == pick]
        st.subheader(f"Squad profiles ({len(view)} teams)")
        st.dataframe(
            view[["team_country", "confederation", "manager", "squad_size", "avg_age",
                  "distinct_clubs", "goalkeepers", "defenders", "midfielders", "forwards"]],
            use_container_width=True, hide_index=True,
        )
        st.subheader("Average squad age")
        st.bar_chart(view.set_index("team_country")["avg_age"])
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
        st.caption(f"{len(view)} players")
        st.dataframe(
            view[["player_name", "team_country", "shirt_number", "position", "age", "club"]],
            use_container_width=True, hide_index=True,
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
