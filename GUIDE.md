# 📖 World Cup 2026 Analytics — User Guide

A guided tour of the app and the data behind it. The app explores the **FIFA World
Cup 2026** on two levels — **players** and **teams** — from live tournament data
through to a predictive model.

> **Launch:** `streamlit run dashboard/app.py` → open http://localhost:8501

---

## The tabs

### 🏠 Overview
Headline numbers — players, teams, average age, total squad value — and a breakdown
of the 48 qualified teams **by confederation** (UEFA 16, CAF 10, AFC 9, CONCACAF 6,
CONMEBOL 6, OFC 1).

### 🏆 Predictions
The heart of the app:
- **Title odds** — each team's probability of advancing, reaching the quarters /
  semis / final, and **winning**, from 20,000 Monte-Carlo simulations.
- **Head-to-head predictor** — pick any two teams for a neutral-venue win/draw/win
  forecast and expected goals.
- **Strength cross-check** — the model's Dixon-Coles rating next to **Elo** and
  **squad market value**, three independent-ish views of team strength.

### 🅰️ Groups
All 12 group tables (A–L) with P / W / D / L / GD / Pts. **Zero before the
tournament**; they update live as matches are played.

### 📅 Schedule
All 72 group fixtures as broadcast-style **scoreboard cards** — flags, kickoff time,
group, and venue. Filter by group or team. Scores fill in live.

### 👕 Teams
Squad profiles per nation: size, average age, club spread, positional split, plus
**confederation and manager**. Includes a most-valuable-squads ranking.

### 🧑 Players
Every one of the ~1,255 squad players with **photo, position, club, age and market
value**. Filter by team and position; see youngest players and top supplying clubs.

### 📋 Lineup
Each team's **predicted starting XI** as a teamsheet (GK → defence → midfield →
attack), with the real formation, derived from their most recent friendly.

### 📊 Historical
World Cup 2022 reference stats (top scorers) — part of the model's training data.

---

## How the predictions work

1. **Goal model** — a [Dixon-Coles](https://en.wikipedia.org/wiki/Dixon%E2%80%93Coles_model)
   model is fit on **49,000 international results (1872–today)**, weighting recent
   matches more heavily (2½-year-ish half-life) and correcting low-score outcomes.
2. **Value prior** — strengths are shrunk toward what each team's **squad market
   value** implies, adding an independent talent signal beyond results.
3. **Simulation** — the tournament is played out **20,000 times**: group matches →
   standings (top 2 + 8 best thirds) → the **real 2026 knockout bracket** → champion.
4. **Validation** — backtested on WC2018 & WC2022: **~56% match accuracy**, log-loss
   0.99 vs 1.10 for a coin-flip, and the probabilities are **well-calibrated**.

---

## Honest caveats

- **Pre-tournament**, live standings/stats are empty until **11 June 2026**; the
  pipeline fills them in automatically as matches are played.
- **Predicted XIs** are from last friendlies and will be replaced by **real lineups**
  once matches start.
- **Flags** are shown for all 48 teams; national-team **crests are trademarked**, so
  flags are used throughout.
- Market value + photos cover **98.5%** of players; a few hard-to-transliterate names
  are blank.
- The model captures team strength well but football is high-variance — treat odds as
  probabilities, not predictions.

---

## Data sources (all free)

| Data | Source |
|---|---|
| Squads, team info, historical stats, fixtures, standings | FBref (via `soccerdata`) |
| Market values & player photos | Transfermarkt |
| Historical international results (model training) | [martj42/international_results](https://github.com/martj42/international_results) |
| Flags | flagcdn.com |
