-- Group standings mart, ordered as a table would display (group, then rank/points).
select
    group_letter,
    rank,
    team_country,
    played,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goal_diff,
    points
from {{ ref('stg_group_standings') }}
order by group_letter, points desc, goal_diff desc, team_country
