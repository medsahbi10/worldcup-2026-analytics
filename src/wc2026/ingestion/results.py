"""Ingest historical international match results (training data for the model).

Source: the martj42 international-results dataset (~49k matches, 1872-present),
mirrored as a public CSV on GitHub — no auth required.
"""

from __future__ import annotations

import io
import urllib.request

import duckdb
import pandas as pd

RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def fetch_results() -> pd.DataFrame:
    req = urllib.request.Request(RESULTS_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return pd.read_csv(io.BytesIO(resp.read()))


def load_results(con: duckdb.DuckDBPyConnection) -> int:
    """Write the full international results history to ``raw_intl_results``."""
    df = fetch_results()  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_intl_results AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_intl_results").fetchone()[0]
