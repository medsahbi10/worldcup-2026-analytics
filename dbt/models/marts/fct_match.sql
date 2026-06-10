-- Team-level match fact: one row per match with derived result.
select
    match_id,
    tournament,
    stage,
    match_date,
    home_team,
    away_team,
    home_score,
    away_score,
    case
        when home_score > away_score then home_team
        when away_score > home_score then away_team
        else 'Draw'
    end as winner
from {{ ref('stg_matches') }}
