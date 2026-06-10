from wc2026 import config, seed


def test_local_target_is_default(monkeypatch):
    monkeypatch.delenv("WC_ENV", raising=False)
    assert config.get_database_target().endswith(".duckdb")


def test_cloud_target_uses_motherduck(monkeypatch):
    monkeypatch.setenv("WC_ENV", "cloud")
    monkeypatch.setenv("MOTHERDUCK_TOKEN", "fake-token")
    assert config.get_database_target().startswith("md:")


def test_seed_loads_rows(monkeypatch, tmp_path):
    monkeypatch.delenv("WC_ENV", raising=False)
    monkeypatch.setattr(config, "LOCAL_DB_PATH", tmp_path / "test.duckdb")
    con = config.connect()
    try:
        n = seed.load_sample_matches(con)
        count = con.execute("select count(*) from raw_matches").fetchone()[0]
    finally:
        con.close()
    assert n == count == len(seed.SAMPLE_MATCHES)
