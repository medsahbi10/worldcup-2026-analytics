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


def load_all_samples(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Seed every raw table with offline samples (used by CI so dbt build runs)."""
    return {
        "raw_matches": load_sample_matches(con),
        "raw_squads": load_sample_squads(con),
        "raw_team_info": load_sample_team_info(con),
        "raw_player_stats": load_sample_player_stats(con),
    }
