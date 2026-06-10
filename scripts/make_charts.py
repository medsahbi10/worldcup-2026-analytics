"""Render PNG charts from the warehouse marts (players + teams)."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from wc2026 import config  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
con = config.connect()
plt.rcParams.update({"figure.autolayout": True, "axes.grid": True, "grid.alpha": 0.3})


# 1. Average squad age by team
ts = con.execute("select * from team_squad_summary order by avg_age").df()
fig, ax = plt.subplots(figsize=(8, 11))
ax.barh(ts["team_country"], ts["avg_age"], color="#2a7de1")
ax.set_title("Average squad age by team — WC 2026")
ax.set_xlabel("Average age")
ax.tick_params(labelsize=7)
ax.set_xlim(ts["avg_age"].min() - 1, ts["avg_age"].max() + 0.5)
fig.savefig(OUT / "1_avg_age_by_team.png", dpi=110)
plt.close(fig)

# 2. Overall positional breakdown
pos = con.execute(
    "select primary_position, count(*) n from dim_player group by 1 order by n desc"
).df()
fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(pos["n"], labels=pos["primary_position"], autopct="%1.0f%%", startangle=90,
       colors=["#2a7de1", "#43a047", "#fb8c00", "#e53935", "#8e24aa"])
ax.set_title(f"Positional split — all {int(pos['n'].sum())} players")
fig.savefig(OUT / "2_position_split.png", dpi=110)
plt.close(fig)

# 3. Top clubs supplying WC 2026 players
clubs = con.execute(
    "select club, count(*) n from dim_player group by 1 order by n desc limit 15"
).df()
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(clubs["club"][::-1], clubs["n"][::-1], color="#43a047")
ax.set_title("Top 15 clubs supplying WC 2026 players")
ax.set_xlabel("Players called up")
fig.savefig(OUT / "3_top_clubs.png", dpi=110)
plt.close(fig)

# 4. Age distribution
ages = con.execute("select age from dim_player where age is not null").df()
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(ages["age"], bins=range(16, 44), color="#fb8c00", edgecolor="white")
ax.set_title("Age distribution — all WC 2026 squad players")
ax.set_xlabel("Age")
ax.set_ylabel("Players")
fig.savefig(OUT / "4_age_distribution.png", dpi=110)
plt.close(fig)

# 5b. Teams per confederation
try:
    conf = con.execute(
        "select confederation, count(*) teams from dim_national_team "
        "where confederation is not null group by 1 order by teams desc"
    ).df()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(conf["confederation"], conf["teams"], color="#5e35b1")
    ax.set_title("Qualified teams by confederation — WC 2026")
    ax.set_ylabel("Teams")
    for i, v in enumerate(conf["teams"]):
        ax.text(i, v + 0.1, str(int(v)), ha="center", fontsize=9)
    fig.savefig(OUT / "6_teams_by_confederation.png", dpi=110)
    plt.close(fig)
except Exception as e:  # noqa: BLE001
    print("skipped confederation chart:", e)

# 5. Top scorers, World Cup 2022 (historical)
try:
    sc = con.execute(
        "select player_name, team, goals from fct_player_stats "
        "where goals is not null order by goals desc limit 12"
    ).df()
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = sc["player_name"] + " (" + sc["team"] + ")"
    ax.barh(labels[::-1], sc["goals"][::-1], color="#e53935")
    ax.set_title("Top scorers — World Cup 2022 (historical)")
    ax.set_xlabel("Goals")
    fig.savefig(OUT / "5_top_scorers_2022.png", dpi=110)
    plt.close(fig)
except Exception as e:  # noqa: BLE001
    print("skipped scorers chart:", e)

# 7. Most valuable players
try:
    mv = con.execute(
        "select player_name, team_country, round(market_value_eur/1e6,1) v "
        "from dim_player where market_value_eur is not null order by market_value_eur desc limit 12"
    ).df()
    fig, ax = plt.subplots(figsize=(8, 6))
    labels = mv["player_name"] + " (" + mv["team_country"] + ")"
    ax.barh(labels[::-1], mv["v"][::-1], color="#00897b")
    ax.set_title("Most valuable players — WC 2026 (Transfermarkt)")
    ax.set_xlabel("Market value (€m)")
    fig.savefig(OUT / "7_top_player_values.png", dpi=110)
    plt.close(fig)
except Exception as e:  # noqa: BLE001
    print("skipped player-value chart:", e)

# 8. Most valuable squads
try:
    tv = con.execute(
        "select team_country, total_value_m from team_market_value order by total_value_m desc limit 15"
    ).df()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(tv["team_country"][::-1], tv["total_value_m"][::-1], color="#3949ab")
    ax.set_title("Most valuable squads — WC 2026 (Transfermarkt)")
    ax.set_xlabel("Total squad value (€m)")
    fig.savefig(OUT / "8_top_squad_values.png", dpi=110)
    plt.close(fig)
except Exception as e:  # noqa: BLE001
    print("skipped squad-value chart:", e)

con.close()
print("charts written to", OUT)
