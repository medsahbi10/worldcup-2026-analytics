from wc2026 import config, seed
from wc2026.ingestion import fbref, transfermarkt


def test_norm_reconciles_team_name_variants():
    # FBref slug spellings should normalize to the same key as fixture names.
    assert fbref._norm("Turkiye") == fbref._norm("Türkiye")
    assert fbref._norm("Cote dIvoire") == fbref._norm("Côte d'Ivoire")
    assert fbref._norm("Bosnia and Herzegovina") == fbref._norm("Bosnia-Herzegovina")
    assert fbref._norm("Curacao") == fbref._norm("Curaçao")


def test_parse_squad_finds_roster_table():
    html = """
    <table class="wikitable"><tr><th>Player</th><th>Birth Date</th><th>Pos</th>
    <th>Club</th><th>Age</th><th>#</th><th>Birth Place</th></tr>
    <tr><td>Test Player</td><td>1998-01-01</td><td>DF,MF</td><td>Some FC</td>
    <td>27-100</td><td>5</td><td>Town</td></tr></table>
    """
    df = fbref.parse_squad(html, "Testland")
    assert list(df["player_name"]) == ["Test Player"]
    assert df["team"].iloc[0] == "Testland"
    assert df["age_years"].iloc[0] == 27


def test_parse_transfermarkt_value():
    assert transfermarkt._parse_value("€100.00m") == 100_000_000
    assert transfermarkt._parse_value("€700k") == 700_000
    assert transfermarkt._parse_value("€1.20bn") == 1_200_000_000
    assert transfermarkt._parse_value("-") is None
    assert transfermarkt._parse_value(None) is None


def test_offline_seeds_populate_all_raw_tables(monkeypatch, tmp_path):
    monkeypatch.delenv("WC_ENV", raising=False)
    monkeypatch.setattr(config, "LOCAL_DB_PATH", tmp_path / "t.duckdb")
    con = config.connect()
    try:
        counts = seed.load_all_samples(con)
    finally:
        con.close()
    assert counts["raw_squads"] >= 1
    assert counts["raw_player_stats"] >= 1
    assert counts["raw_matches"] >= 1
