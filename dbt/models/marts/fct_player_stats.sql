-- Historical player performance fact (one row per player per World Cup).
select
    season,
    team,
    player_name,
    nation,
    primary_position,
    age,
    club,
    matches_played,
    minutes,
    goals,
    assists,
    goals + assists                          as goal_contributions,
    yellow_cards,
    red_cards,
    case
        when minutes >= 90 then round(goals / (minutes / 90.0), 2)
    end                                      as goals_per90
from {{ ref('stg_player_stats') }}
