# World Cup 2026 — Analytics Pipeline

End-to-end data + AI engineering project analyzing the FIFA World Cup 2026 on **two levels**:

- **Players** — goals, xG, passes, tackles, minutes, ratings
- **Teams** — results, possession, xG for/against, win probability, simulations

## Architecture

```
   Sources         StatsBomb open data │ soccerdata/FBref │ football-data.org
                          │                    │                  │
   Ingestion (Python) ────┴────────────────────┴──────────────────┘
                          ▼
   Orchestration     Dagster  ── owns the asset graph, deps, retries
                          ▼
   Warehouse         DuckDB (local file)  ⇄  MotherDuck (cloud, for CI)
                          ▼
   Transform         dbt  ── staging → marts (dim_team, fct_match, ...)
                          ▼
            ┌─────────────┴─────────────┐
            ▼                           ▼
   ML models (Poisson/XGBoost)   Streamlit dashboard (Players / Teams)
```

### Local vs. cloud
The warehouse target is chosen by environment variable, so the **same code** runs
both locally and in GitHub Actions:

| `WC_ENV`   | Target                         | Used for                |
|------------|--------------------------------|-------------------------|
| *(unset)*  | local DuckDB file `data/`      | development             |
| `cloud`    | MotherDuck (`md:`)             | GitHub Actions (state persists between runs) |

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 1. Run the pipeline (seeds sample data, runs dbt)
dagster asset materialize -m wc2026.definitions --select "*"

# 2. Explore in the Dagster UI
dagster dev -m wc2026.definitions

# 3. Launch the themed dashboard (Overview / Predictions / Groups / Schedule /
#    Teams / Players / Lineup / Historical / Guide) — with flags & scoreboards
streamlit run dashboard/app.py
```

See **[GUIDE.md](GUIDE.md)** (or the in-app **📖 Guide** tab) for a full walkthrough.

## Project layout

```
src/wc2026/          Python package: config, ingestion, Dagster defs
  config.py          DuckDB/MotherDuck connection switching
  seed.py            Sample historical matches (Phase 0 smoke test)
  definitions.py     Dagster assets (raw → dbt marts)
dbt/                 dbt project (staging → marts)
dashboard/app.py     Streamlit explorer
models/              ML models (Phase 2)
tests/               pytest
.github/workflows/   ci.yml (lint+test) · daily-ingest.yml (cron → MotherDuck)
```

## Roadmap

- [x] **Phase 0** — Scaffold: runnable vertical slice on sample data
- [x] **Phase 1** — Player & team ingest: 2026 squads (FBref) + historical stats → `dim_player`, `team_squad_summary`, `fct_player_stats`
- [ ] **Phase 2** — Models: match-outcome predictor + Monte-Carlo bracket simulation
- [ ] **Phase 3** — Live ingestion (player match stats fill from June 11) via Dagster + GitHub Actions cron
- [ ] **Phase 4** — Dashboard polish + retrospective report

## Data sources (all free)

- [`soccerdata`](https://github.com/probberechts/soccerdata) → **FBref** (`INT-World Cup`) — our primary source:
  - **2026 squads**: scraped per-team via the Cloudflare-bypassing driver (`fb.get`), since
    soccerdata has no roster endpoint. Team URLs auto-discovered from the competition page.
  - **Historical/live player stats**: `read_player_season_stats` (2022 now; 2026 fills as matches play).
- [football-data.org](https://www.football-data.org/) — free fixtures/scores API (Phase 3, live)
