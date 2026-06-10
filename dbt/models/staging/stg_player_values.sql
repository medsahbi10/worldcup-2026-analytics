-- Cleaned player market values + photos from Transfermarkt.
-- name_key normalizes accents/case/punctuation for joining to FBref squads.
select
    team                                                          as team_country,
    player_name,
    market_value_eur,
    market_value_str,
    photo_url,
    tm_player_id,
    regexp_replace(strip_accents(lower(player_name)), '[^a-z]', '', 'g') as name_key
from raw_player_values
where player_name is not null
