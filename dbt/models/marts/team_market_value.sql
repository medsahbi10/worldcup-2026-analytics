-- Squad market value per team (Transfermarkt), with the most valuable player.
with v as (
    select * from {{ ref('stg_player_values') }} where market_value_eur is not null
),

ranked as (
    select
        team_country,
        player_name,
        market_value_eur,
        row_number() over (partition by team_country order by market_value_eur desc) as rn
    from v
)

select
    v.team_country,
    count(*)                                as valued_players,
    round(sum(v.market_value_eur) / 1e6, 1) as total_value_m,
    round(avg(v.market_value_eur) / 1e6, 2) as avg_value_m,
    max(r.player_name) filter (where r.rn = 1)        as top_player,
    round(max(r.market_value_eur) filter (where r.rn = 1) / 1e6, 1) as top_player_value_m
from v
join ranked r using (team_country, player_name, market_value_eur)
group by v.team_country
order by total_value_m desc
