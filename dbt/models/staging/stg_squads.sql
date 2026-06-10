-- Cleaned 2026 World Cup squad rows from FBref (one per player).
select
    team                                  as team_country,
    try_cast(shirt_number as integer)     as shirt_number,
    player_name,
    position,
    split_part(position, ',', 1)          as primary_position,
    -- FBref prefixes clubs with a country code, e.g. "1.eng Manchester City"
    regexp_replace(club, '^[0-9]+\.[a-z]+\s+', '') as club,
    birth_place,
    try_cast(birth_date as date)          as birth_date,
    try_cast(age_years as integer)        as age_years
from raw_squads
where player_name is not null
