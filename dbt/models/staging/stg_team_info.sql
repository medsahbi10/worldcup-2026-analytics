-- Cleaned team metadata from FBref (confederation + manager).
select
    team           as team_country,
    confederation,
    manager
from raw_team_info
where team is not null
