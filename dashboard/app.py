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
        "group_standings": "Group standings",
        "fct_fixture": "Fixtures",
        "predicted_xi": "Predicted XIs",
        "fct_player_stats": "Hist. stats (mart)",
        "fct_match": "Matches",
    }
    for tbl, label in EXPECTED.items():
        n = row_count(tbl)
        st.write(f"{'✅' if n else '⏳'} **{label}** — {n if n is not None else 'not built'}")

(tab_overview, tab_groups, tab_schedule, tab_teams, tab_players, tab_lineup,
 tab_history) = st.tabs(
    ["Overview", "Groups", "Schedule", "Teams", "Players", "Lineup", "Historical"]
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
                    st.markdown(f"**Group {letter}**")
                    grp = gs[gs["group_letter"] == letter][
                        ["team_country", "played", "won", "drawn", "lost", "goal_diff", "points"]
                    ].rename(columns={"team_country": "Team", "played": "P", "won": "W",
                                      "drawn": "D", "lost": "L", "goal_diff": "GD", "points": "Pts"})
                    st.dataframe(grp, hide_index=True, use_container_width=True)
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
        st.caption(f"{len(view)} matches")
        st.dataframe(
            view[["match_date", "kickoff_local", "group_letter", "home_team", "away_team",
                  "home_score", "away_score", "venue", "status"]],
            hide_index=True, use_container_width=True,
            column_config={
                "match_date": st.column_config.DateColumn("Date"),
                "kickoff_local": st.column_config.TextColumn("Kickoff"),
                "group_letter": st.column_config.TextColumn("Grp"),
                "home_team": st.column_config.TextColumn("Home"),
                "away_team": st.column_config.TextColumn("Away"),
                "home_score": st.column_config.NumberColumn("H", format="%d"),
                "away_score": st.column_config.NumberColumn("A", format="%d"),
            },
        )
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
        st.dataframe(
            view[["team_country", "confederation", "manager", "squad_size", "avg_age",
                  "distinct_clubs", "goalkeepers", "defenders", "midfielders", "forwards"]],
            use_container_width=True, hide_index=True,
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
        cols = ["photo_url", "player_name", "team_country", "position", "age", "club"]
        cols += ["value_m"] if has_value else []
        cols = [c for c in cols if c in view.columns]
        st.dataframe(
            view[cols],
            use_container_width=True, hide_index=True,
            column_config={
                "photo_url": st.column_config.ImageColumn("Photo"),
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
        st.markdown(f"### {team} &nbsp;·&nbsp; `{formation_str}`")
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
