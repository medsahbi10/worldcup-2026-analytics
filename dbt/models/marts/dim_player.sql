-- Player dimension: one row per 2026 World Cup squad member (FBref),
-- enriched with Transfermarkt market value + photo via fuzzy name matching
-- (player_value_map, built in Python — handles spelling/order/mononym diffs).
with squad as (
    select * from {{ ref('stg_squads') }}
),

vmap as (
    select team_country, player_name, market_value_eur, photo_url
    from player_value_map
)

select
    row_number() over (order by squad.team_country, squad.player_name) as player_id,
    squad.player_name,
    squad.team_country,
    squad.shirt_number,
    squad.position,
    squad.primary_position,
    squad.club,
    squad.birth_place,
    squad.birth_date,
    squad.age_years as age,
    v.market_value_eur,
    v.photo_url
from squad
left join vmap as v
    on squad.team_country = v.team_country
    and squad.player_name = v.player_name
