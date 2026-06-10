-- Team-level squad profile for the 2026 World Cup (with confederation + manager).
with s as (
    select * from {{ ref('stg_squads') }}
),

info as (
    select * from {{ ref('stg_team_info') }}
)

select
    s.team_country,
    info.confederation,
    info.manager,
    count(*)                          as squad_size,
    round(avg(s.age_years), 1)        as avg_age,
    min(s.age_years)                  as youngest,
    max(s.age_years)                  as oldest,
    count(distinct s.club)            as distinct_clubs,
    count(*) filter (where s.primary_position = 'GK') as goalkeepers,
    count(*) filter (where s.primary_position = 'DF') as defenders,
    count(*) filter (where s.primary_position = 'MF') as midfielders,
    count(*) filter (where s.primary_position = 'FW') as forwards
from s
left join info on s.team_country = info.team_country
group by s.team_country, info.confederation, info.manager
order by s.team_country
