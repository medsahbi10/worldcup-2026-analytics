-- National-team dimension for the 2026 World Cup: confederation + manager + squad profile.
with info as (
    select * from {{ ref('stg_team_info') }}
),

squad as (
    select
        team_country,
        count(*)                 as squad_size,
        round(avg(age_years), 1) as avg_age,
        count(distinct club)     as distinct_clubs
    from {{ ref('stg_squads') }}
    group by team_country
)

select
    row_number() over (order by info.team_country) as team_id,
    info.team_country,
    info.confederation,
    info.manager,
    squad.squad_size,
    squad.avg_age,
    squad.distinct_clubs
from info
left join squad using (team_country)
