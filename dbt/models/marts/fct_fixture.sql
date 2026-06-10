-- Match fixtures with details: stage, group, date, kickoff, venue, score, status.
with fx as (
    select * from {{ ref('stg_fixtures') }}
),

team_group as (
    select team_country, group_letter from {{ ref('stg_group_standings') }}
)

select
    fx.match_date,
    fx.weekday,
    fx.kickoff_local,
    fx.stage,
    g.group_letter,
    fx.home_team,
    fx.away_team,
    fx.venue,
    fx.home_score,
    fx.away_score,
    case when fx.home_score is not null then 'played' else 'scheduled' end as status,
    fx.referee,
    fx.game_id
from fx
left join team_group as g on fx.home_team = g.team_country
order by fx.match_date, fx.kickoff_local
