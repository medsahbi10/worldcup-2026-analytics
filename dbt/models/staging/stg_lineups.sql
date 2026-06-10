-- Starting XIs + formations from each team's last friendly (FBref match pages).
select
    team                                                          as team_country,
    formation,
    match_url,
    try_cast(shirt_number as integer)                            as shirt_number,
    player_name,
    position,
    try_cast(pos_rank as integer)                                as pos_rank,
    regexp_replace(strip_accents(lower(player_name)), '[^a-z]', '', 'g') as name_key
from raw_lineups
where player_name is not null
