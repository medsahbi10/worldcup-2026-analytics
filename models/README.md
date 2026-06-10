# Models (Phase 2)

ML lives here once historical data is loaded:

- **Match-outcome model** — Poisson / Dixon-Coles or XGBoost on team features
- **Bracket simulation** — Monte-Carlo over the 48-team field to estimate each
  team's chance of advancing / winning
- **Player ratings** — per-match performance scoring from event data

Models read from the dbt marts (`fct_match`, `dim_team`, ...) via `wc2026.config.connect()`.
