-- Predicted starting XI per team (from last friendly), enriched with value + photo.
-- Ordered like a teamsheet: GK -> defenders -> midfield -> attack.
with lineup as (
    select * from {{ ref('stg_lineups') }}
),

players as (
    select
        team_country,
        market_value_eur,
        photo_url,
        club,
        regexp_replace(strip_accents(lower(player_name)), '[^a-z]', '', 'g') as name_key
    from {{ ref('dim_player') }}
)

select
    lineup.team_country,
    lineup.formation,
    lineup.pos_rank,
    lineup.position,
    lineup.shirt_number,
    lineup.player_name,
    p.club,
    p.market_value_eur,
    p.photo_url
from lineup
left join players as p
    on lineup.team_country = p.team_country
    and lineup.name_key = p.name_key
order by lineup.team_country, lineup.pos_rank, lineup.shirt_number
