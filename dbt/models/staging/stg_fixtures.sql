-- Match schedule, typed. Splits "20:00 (03:00)" into local kickoff; score when played.
select
    round                                              as stage,
    cast(date as date)                                 as match_date,
    day                                                as weekday,
    trim(split_part(time, '(', 1))                     as kickoff_local,
    home_team,
    away_team,
    venue,
    nullif(cast(score as varchar), '')                 as score,
    try_cast(split_part(replace(cast(score as varchar), '–', '-'), '-', 1) as integer) as home_score,
    try_cast(split_part(replace(cast(score as varchar), '–', '-'), '-', 2) as integer) as away_score,
    referee,
    game_id
from raw_fixtures
where home_team is not null
