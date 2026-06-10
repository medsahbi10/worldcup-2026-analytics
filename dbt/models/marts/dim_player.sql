-- Player dimension: one row per 2026 World Cup squad member (FBref),
-- enriched with Transfermarkt market value + photo (matched within team by name).
with squad as (
    select
        *,
        regexp_replace(strip_accents(lower(player_name)), '[^a-z]', '', 'g') as name_key
    from {{ ref('stg_squads') }}
),

values_ as (
    select * from {{ ref('stg_player_values') }}
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
    v.market_value_str,
    v.photo_url,
    v.tm_player_id
from squad
left join values_ as v
    on squad.team_country = v.team_country
    and squad.name_key = v.name_key
