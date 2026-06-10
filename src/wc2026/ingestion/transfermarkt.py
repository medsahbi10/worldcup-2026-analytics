"""Ingest player market values and photos from Transfermarkt.

Transfermarkt is reachable via plain HTTP (no Cloudflare wall). Each national
team's squad page lists every player with their market value and a portrait
URL, so one scrape covers both market value and images.

Team URLs are auto-discovered from the World Cup participants page and matched
to our team names (with a small alias map for TM's naming, e.g. "Iran",
"South Korea", "Ivory Coast").
"""

from __future__ import annotations

import re
import unicodedata
import urllib.parse
import urllib.request

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

_PROFILE_RE = re.compile(r"/([a-z0-9-]+)/profil/spieler/(\d+)")

_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
}
PARTICIPANTS_URL = "https://www.transfermarkt.com/weltmeisterschaft/teilnehmer/pokalwettbewerb/FIWC"
_TEAM_LINK_RE = re.compile(r'<a title="([^"]+)" href="/([a-z0-9-]+)/startseite/verein/(\d+)"')

# our team name (normalized) -> Transfermarkt title (normalized)
_ALIASES = {
    "iriran": "iran",
    "korearepublic": "southkorea",
    "cotedivoire": "ivorycoast",
    "congodr": "democraticrepublicofthecongo",
}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", "ignore")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.lower().replace(" and ", " ")
    return re.sub(r"[^a-z]", "", s)


def _parse_value(s: str | None) -> float | None:
    """'€100.00m' -> 100000000.0, '€700k' -> 700000.0, '-' -> None."""
    if not s:
        return None
    s = s.replace("€", "").replace(",", "").strip().lower()
    m = re.match(r"([\d.]+)\s*(bn|m|k)?", s)
    if not m or not m.group(1):
        return None
    mult = {"bn": 1e9, "m": 1e6, "k": 1e3, None: 1.0}[m.group(2)]
    return float(m.group(1)) * mult


def discover_team_urls(team_names: list[str]) -> dict[str, str]:
    """Map our team names to their Transfermarkt detailed-squad URLs."""
    html = _get(PARTICIPANTS_URL)
    seen: dict[str, tuple[str, str]] = {}
    for title, slug, tid in _TEAM_LINK_RE.findall(html):
        seen.setdefault(_norm(title), (slug, tid))

    urls: dict[str, str] = {}
    for team in team_names:
        key = _norm(team)
        tm_key = key if key in seen else _ALIASES.get(key)
        if tm_key and tm_key in seen:
            slug, tid = seen[tm_key]
            urls[team] = f"https://www.transfermarkt.com/{slug}/kader/verein/{tid}/plus/1"
    return urls


def parse_squad_values(html: str, team: str) -> pd.DataFrame:
    """Parse a TM detailed-squad page into player value + photo rows."""
    soup = BeautifulSoup(html, "lxml")
    recs = []
    for row in soup.select("table.items > tbody > tr"):
        link = row.select_one("td.hauptlink a")
        if not link:
            continue
        img = row.select_one("img.bilderrahmen-fixed")
        photo = (img.get("data-src") or img.get("src")) if img else None
        val_td = row.select_one("td.rechts.hauptlink")
        val = val_td.get_text(strip=True) if val_td else None
        pid = re.search(r"/spieler/(\d+)", link.get("href", ""))
        recs.append(
            {
                "team": team,
                "player_name": link.get_text(strip=True),
                "market_value_str": val,
                "market_value_eur": _parse_value(val),
                "photo_url": photo,
                "tm_player_id": int(pid.group(1)) if pid else None,
            }
        )
    return pd.DataFrame(recs)


def search_player(name: str) -> dict | None:
    """Look up a single player via TM search; return profile name + value + photo."""
    sr = _get("https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query="
              + urllib.parse.quote(name))
    m = _PROFILE_RE.search(sr)
    if not m:
        return None
    slug, pid = m.group(1), m.group(2)
    page = _get(f"https://www.transfermarkt.com/{slug}/profil/spieler/{pid}")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    profile_name = re.sub(r"#?\d+", "", re.sub(r"<[^>]+>", " ", h1.group(1))).strip() if h1 else ""
    val = re.search(r"€[\d.,]+\s*[mk]?", page)
    photo = re.search(
        r"https://img\.a\.transfermarkt\.technology/portrait/[a-z]+/" + pid + r"[^\"' ]*", page
    )
    return {
        "tm_id": int(pid),
        "profile_name": profile_name,
        "market_value_eur": _parse_value(val.group(0) if val else None),
        "photo_url": photo.group(0) if photo else None,
    }


def load_player_values(
    con: duckdb.DuckDBPyConnection, team_names: list[str] | None = None
) -> int:
    """Fetch every team's market values + photos into ``raw_player_values``."""
    if team_names is None:
        team_names = [r[0] for r in con.execute("select distinct team from raw_squads").fetchall()]
    urls = discover_team_urls(team_names)
    frames = [parse_squad_values(_get(url), team) for team, url in urls.items()]
    df = pd.concat(frames, ignore_index=True)  # noqa: F841 — used by DuckDB below
    con.execute("CREATE OR REPLACE TABLE raw_player_values AS SELECT * FROM df")
    return con.execute("SELECT count(*) FROM raw_player_values").fetchone()[0]
