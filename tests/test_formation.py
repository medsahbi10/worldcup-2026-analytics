import pandas as pd

from wc2026 import formation


def _squad():
    rows = []
    for pos, n in [("GK", 3), ("DF", 8), ("MF", 8), ("FW", 6)]:
        for i in range(n):
            rows.append(
                {"player_name": f"{pos} Player {i}", "primary_position": pos,
                 "market_value_eur": (n - i) * 1e6}
            )
    return pd.DataFrame(rows)


def test_build_xi_fills_formation():
    xi = formation.build_xi(_squad(), "4-3-3")
    assert len(xi) == 11
    counts = xi["line"].value_counts().to_dict()
    assert counts == {"DF": 4, "MF": 3, "FW": 3, "GK": 1}
    # coordinates within pitch bounds
    assert xi["x"].between(0, 100).all() and xi["y"].between(0, 100).all()


def test_build_xi_picks_highest_value():
    xi = formation.build_xi(_squad(), "4-3-3")
    gk = xi[xi["line"] == "GK"].iloc[0]
    assert gk["player_name"] == "GK Player 0"  # highest value GK


def test_coords_for_formation():
    for f in ["4-3-3", "4-1-4-1", "3-5-2", "4-2-3-1"]:
        coords = formation.coords_for_formation(f)
        assert len(coords) == 11  # GK + 10 outfield
        assert all(0 <= x <= 100 and 0 <= y <= 100 for x, y in coords)
    assert formation.coords_for_formation("4-1-4-1")[0] == (9.0, 50.0)  # GK centred
