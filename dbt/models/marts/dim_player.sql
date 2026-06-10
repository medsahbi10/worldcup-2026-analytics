-- Player dimension: one row per 2026 World Cup squad member.
select
    row_number() over (order by team_country, player_name) as player_id,
    player_name,
    team_country,
    shirt_number,
    position,
    primary_position,
    club,
    birth_place,
    birth_date,
    age_years as age
from {{ ref('stg_squads') }}
