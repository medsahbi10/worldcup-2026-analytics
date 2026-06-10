-- Cleaned historical World Cup player stats from FBref.
select
    season,
    team,
    player_name,
    nation,
    position,
    split_part(position, ',', 1)                                as primary_position,
    try_cast(regexp_extract(cast(age as varchar), '\d+') as integer) as age,
    club,
    try_cast(matches_played as integer)                         as matches_played,
    try_cast(starts as integer)                                 as starts,
    try_cast(minutes as integer)                                as minutes,
    try_cast(goals as integer)                                  as goals,
    try_cast(assists as integer)                                as assists,
    try_cast(yellow_cards as integer)                           as yellow_cards,
    try_cast(red_cards as integer)                              as red_cards
from raw_player_stats
where player_name is not null
