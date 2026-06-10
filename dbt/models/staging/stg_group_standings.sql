-- Group standings (one row per team), typed. Pre-tournament values are 0.
select
    group_letter,
    -- FBref prefixes the team with a lowercase flag code, e.g. "jpJapan", "ci Côte d'Ivoire"
    regexp_replace(team, '^[a-z]{2,3}\s*', '') as team_country,
    try_cast(rank as integer)     as rank,
    coalesce(try_cast(mp as integer), 0)  as played,
    coalesce(try_cast(w as integer), 0)   as won,
    coalesce(try_cast(d as integer), 0)   as drawn,
    coalesce(try_cast(l as integer), 0)   as lost,
    coalesce(try_cast(gf as integer), 0)  as goals_for,
    coalesce(try_cast(ga as integer), 0)  as goals_against,
    coalesce(try_cast(gd as integer), 0)  as goal_diff,
    coalesce(try_cast(pts as integer), 0) as points
from raw_group_standings
where team is not null
