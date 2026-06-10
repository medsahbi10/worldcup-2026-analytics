from wc2026 import branding


def test_flag_url_known_and_unknown():
    assert branding.flag_url("Argentina") == "https://flagcdn.com/w40/ar.png"
    assert branding.flag_url("England").endswith("gb-eng.png")  # UK sub-flag
    assert "un.png" in branding.flag_url("Atlantis")  # fallback


def test_flag_mapping_covers_all_groups():
    # every team that appears in the group letters should have a flag code
    assert len(branding.FLAG_ISO) == 48


def test_add_flag_column():
    import pandas as pd
    df = pd.DataFrame({"team_country": ["Brazil", "Japan"]})
    out = branding.add_flag_column(df)
    assert list(out.columns)[0] == "flag"
    assert out["flag"].iloc[0].endswith("br.png")


def test_html_helpers():
    assert "wc-banner" in branding.banner_html("Title", "Sub")
    card = branding.score_card_html("A", "B", "fa", "fb", "1 – 0", "meta")
    assert "score-card" in card and "1 – 0" in card
