"""Sample data loader — a Phase 0 smoke test.

Loads a handful of real historical World Cup finals into a ``raw_matches``
table so the whole pipeline (dbt marts → dashboard) can run end-to-end
before real ingestion is wired up in Phase 1.
"""

from __future__ import annotations

import duckdb

# (match_id, tournament, stage, home_team, away_team, home_score, away_score, match_date)
SAMPLE_MATCHES: list[tuple] = [
    (1, "World Cup 2022", "Final", "Argentina", "France", 3, 3, "2022-12-18"),
    (2, "World Cup 2018", "Final", "France", "Croatia", 4, 2, "2018-07-15"),
    (3, "World Cup 2014", "Final", "Germany", "Argentina", 1, 0, "2014-07-13"),
    (4, "World Cup 2010", "Final", "Spain", "Netherlands", 1, 0, "2010-07-11"),
    (5, "World Cup 2006", "Final", "Italy", "France", 1, 1, "2006-07-09"),
    (6, "World Cup 2022", "Semi-final", "Argentina", "Croatia", 3, 0, "2022-12-13"),
    (7, "World Cup 2022", "Semi-final", "France", "Morocco", 2, 0, "2022-12-14"),
]


def load_sample_matches(con: duckdb.DuckDBPyConnection) -> int:
    """Create and populate the ``raw_matches`` table. Returns row count."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_matches (
            match_id    INTEGER,
            tournament  VARCHAR,
            stage       VARCHAR,
            home_team   VARCHAR,
            away_team   VARCHAR,
            home_score  INTEGER,
            away_score  INTEGER,
            match_date  VARCHAR
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SAMPLE_MATCHES,
    )
    return len(SAMPLE_MATCHES)


def load_sample_squads(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_squads`` fixture (matches FBref ingestion schema) for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_squads (
            team         VARCHAR,
            shirt_number BIGINT,
            player_name  VARCHAR,
            position     VARCHAR,
            club         VARCHAR,
            birth_place  VARCHAR,
            birth_date   VARCHAR,
            age_years    BIGINT
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_squads VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("Tunisia", 1, "Aymen Dahmen", "GK", "FC Sochaux", "Tunisia", "1997-01-24", 29),
            ("Tunisia", 6, "Montassar Talbi", "DF", "Lorient", "France", "1998-05-26", 28),
            ("Argentina", 10, "Lionel Messi", "FW", "Inter Miami", "Argentina", "1987-06-24", 38),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_squads").fetchone()[0]


def load_sample_player_stats(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_player_stats`` fixture (matches FBref schema) for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_player_stats (
            season VARCHAR, team VARCHAR, player_name VARCHAR, nation VARCHAR,
            position VARCHAR, age VARCHAR, club VARCHAR,
            matches_played BIGINT, starts BIGINT, minutes BIGINT,
            goals BIGINT, assists BIGINT, yellow_cards BIGINT, red_cards BIGINT
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_player_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("2022", "France", "Kylian Mbappe", "France", "FW", "23", "Paris S-G",
             7, 7, 632, 8, 2, 0, 0),
            ("2022", "Argentina", "Lionel Messi", "Argentina", "FW", "35", "Paris S-G",
             7, 7, 690, 7, 3, 1, 0),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_player_stats").fetchone()[0]


def load_sample_team_info(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_team_info`` fixture (confederation + manager) for offline/CI."""
    con.execute(
        "CREATE OR REPLACE TABLE raw_team_info "
        "(team VARCHAR, confederation VARCHAR, manager VARCHAR)"
    )
    con.executemany(
        "INSERT INTO raw_team_info VALUES (?, ?, ?)",
        [
            ("Tunisia", "CAF", "Sabri Lamouchi"),
            ("Argentina", "CONMEBOL", "Lionel Scaloni"),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_team_info").fetchone()[0]


def load_sample_player_values(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_player_values`` fixture (Transfermarkt schema) for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_player_values (
            team VARCHAR, player_name VARCHAR, market_value_str VARCHAR,
            market_value_eur DOUBLE, photo_url VARCHAR, tm_player_id BIGINT
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_player_values VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Argentina", "Lionel Messi", "€15.00m", 15_000_000.0,
             "https://img.a.transfermarkt.technology/portrait/medium/28003", 28003),
            ("Tunisia", "Montassar Talbi", "€4.00m", 4_000_000.0, None, 401510),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_player_values").fetchone()[0]


def load_sample_lineups(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_lineups`` fixture for offline/CI (4-1-4-1 partial)."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_lineups (
            team VARCHAR, formation VARCHAR, match_url VARCHAR,
            shirt_number VARCHAR, player_name VARCHAR, position VARCHAR, pos_rank BIGINT
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_lineups VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("Tunisia", "4-1-4-1", "http://x", "1", "Mouhib Chamakh", "GK", 0),
            ("Tunisia", "4-1-4-1", "http://x", "3", "Montassar Talbi", "CB", 1),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_lineups").fetchone()[0]


def load_sample_value_map(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``player_value_map`` fixture (matched to sample squads) for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE player_value_map (
            team_country VARCHAR, player_name VARCHAR, market_value_eur DOUBLE,
            photo_url VARCHAR, matched_name VARCHAR, match_score DOUBLE
        )
        """
    )
    con.executemany(
        "INSERT INTO player_value_map VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Argentina", "Lionel Messi", 15_000_000.0,
             "https://img.a.transfermarkt.technology/portrait/medium/28003", "Lionel Messi", 100.0),
            ("Tunisia", "Montassar Talbi", 4_000_000.0, None, "Montassar Talbi", 100.0),
            ("Tunisia", "Aymen Dahmen", None, None, None, None),
        ],
    )
    return con.execute("SELECT count(*) FROM player_value_map").fetchone()[0]


def load_sample_group_standings(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_group_standings`` fixture for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_group_standings (
            group_letter VARCHAR, team VARCHAR, rank VARCHAR, mp VARCHAR,
            w VARCHAR, d VARCHAR, l VARCHAR, gf VARCHAR, ga VARCHAR, gd VARCHAR, pts VARCHAR
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_group_standings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("A", "Mexico", "1", "0", "0", "0", "0", None, None, None, "0"),
            ("A", "Czechia", "2", "0", "0", "0", "0", None, None, None, "0"),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_group_standings").fetchone()[0]


def load_sample_fixtures(con: duckdb.DuckDBPyConnection) -> int:
    """Minimal ``raw_fixtures`` fixture for offline/CI."""
    con.execute(
        """
        CREATE OR REPLACE TABLE raw_fixtures (
            round VARCHAR, day VARCHAR, date VARCHAR, time VARCHAR,
            home_team VARCHAR, score VARCHAR, away_team VARCHAR,
            venue VARCHAR, attendance VARCHAR, referee VARCHAR, game_id VARCHAR
        )
        """
    )
    con.executemany(
        "INSERT INTO raw_fixtures VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            ("Group stage", "Thu", "2026-06-11", "20:00 (03:00)", "Korea Republic",
             None, "Czechia", "Estadio Akron", None, None, "abc123"),
            ("Group stage", "Thu", "2026-06-11", "13:00 (20:00)", "Mexico",
             None, "South Africa", "Estadio Banorte", None, None, "def456"),
        ],
    )
    return con.execute("SELECT count(*) FROM raw_fixtures").fetchone()[0]


def load_all_samples(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Seed every raw table with offline samples (used by CI so dbt build runs)."""
    return {
        "raw_matches": load_sample_matches(con),
        "raw_squads": load_sample_squads(con),
        "raw_team_info": load_sample_team_info(con),
        "raw_player_stats": load_sample_player_stats(con),
        "raw_player_values": load_sample_player_values(con),
        "raw_lineups": load_sample_lineups(con),
        "player_value_map": load_sample_value_map(con),
        "raw_group_standings": load_sample_group_standings(con),
        "raw_fixtures": load_sample_fixtures(con),
    }
