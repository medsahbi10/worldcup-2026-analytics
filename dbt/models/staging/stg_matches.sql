-- Clean, typed view over the raw landing table.
with source as (
    select * from raw_matches
)

select
    match_id,
    tournament,
    stage,
    home_team,
    away_team,
    home_score,
    away_score,
    cast(match_date as date) as match_date
from source
