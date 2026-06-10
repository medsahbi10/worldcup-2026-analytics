-- Team dimension: one row per distinct team appearing in any match.
with matches as (
    select * from {{ ref('stg_matches') }}
),

teams as (
    select home_team as team_name from matches
    union
    select away_team as team_name from matches
)

select
    row_number() over (order by team_name) as team_id,
    team_name
from teams
