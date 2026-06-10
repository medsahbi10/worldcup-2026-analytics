"""Visual branding for the dashboard: tournament palette, fonts, flags, CSS.

Flags come from flagcdn.com (free, CC0-ish, complete coverage incl. the UK
sub-flags for England/Scotland). National-team crests are trademarked with no
reliable free source, so flags are the primary team visual.
"""

from __future__ import annotations

# WC2026-inspired palette
NAVY = "#0d1b2a"
RED = "#e4002b"
GOLD = "#ffc72c"
GREEN = "#1a8c3c"
INK = "#10243e"

# our team name -> flagcdn country code
FLAG_ISO = {
    "Mexico": "mx", "South Africa": "za", "Korea Republic": "kr", "Czechia": "cz",
    "Canada": "ca", "Bosnia-Herzegovina": "ba", "Qatar": "qa", "Switzerland": "ch",
    "Brazil": "br", "Morocco": "ma", "Haiti": "ht", "Scotland": "gb-sct",
    "United States": "us", "Paraguay": "py", "Australia": "au", "Türkiye": "tr",
    "Germany": "de", "Curaçao": "cw", "Côte d'Ivoire": "ci", "Ecuador": "ec",
    "Netherlands": "nl", "Japan": "jp", "Sweden": "se", "Tunisia": "tn",
    "Belgium": "be", "Egypt": "eg", "IR Iran": "ir", "New Zealand": "nz",
    "Spain": "es", "Cape Verde": "cv", "Saudi Arabia": "sa", "Uruguay": "uy",
    "France": "fr", "Senegal": "sn", "Iraq": "iq", "Norway": "no",
    "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Jordan": "jo",
    "Portugal": "pt", "Congo DR": "cd", "Uzbekistan": "uz", "Colombia": "co",
    "England": "gb-eng", "Croatia": "hr", "Ghana": "gh", "Panama": "pa",
}


def flag_url(team: str, size: str = "w40") -> str:
    """flagcdn URL for a team, or a transparent placeholder if unknown."""
    iso = FLAG_ISO.get(team)
    if not iso:
        return "https://flagcdn.com/w40/un.png"
    return f"https://flagcdn.com/{size}/{iso}.png"


def add_flag_column(df, team_col: str = "team_country", size: str = "w40", name: str = "flag"):
    """Return df with a leading flag-URL column (for st.column_config.ImageColumn)."""
    df = df.copy()
    df.insert(0, name, df[team_col].map(lambda t: flag_url(t, size)))
    return df


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3, h4 {{ font-family: 'Oswald', sans-serif !important; letter-spacing: .5px; color: {INK}; }}

.wc-banner {{
    background: linear-gradient(110deg, {NAVY} 0%, {INK} 55%, {RED} 160%);
    color: #fff; padding: 20px 26px; border-radius: 14px; margin-bottom: 8px;
    box-shadow: 0 6px 18px rgba(0,0,0,.18);
    border-bottom: 4px solid {GOLD};
}}
.wc-banner h1 {{ color: #fff !important; margin: 0; font-size: 34px; }}
.wc-banner p {{ margin: 4px 0 0; opacity: .85; font-size: 14px; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Oswald', sans-serif; font-weight: 500; text-transform: uppercase;
    font-size: 13px; letter-spacing: .6px;
}}
.stTabs [aria-selected="true"] {{ color: {RED}; border-bottom-color: {RED}; }}

/* broadcast-style scoreboard card */
.score-card {{
    display: flex; align-items: center; justify-content: space-between;
    background: #fff; border: 1px solid #e6e9ef; border-left: 5px solid {RED};
    border-radius: 10px; padding: 10px 16px; margin: 6px 0;
    box-shadow: 0 2px 6px rgba(0,0,0,.05);
}}
.score-card .side {{ display: flex; align-items: center; gap: 8px; width: 40%; font-weight: 600; }}
.score-card .side.away {{ justify-content: flex-end; }}
.score-card .score {{ font-family: 'Oswald'; font-size: 20px; font-weight: 700; color: {INK}; }}
.score-card img {{ width: 26px; height: 18px; object-fit: cover; border-radius: 2px; }}
.score-card .meta {{ font-size: 11px; color: #6b7280; text-align: center; width: 20%; }}
</style>
"""


def banner_html(title: str, subtitle: str) -> str:
    return f'<div class="wc-banner"><h1>{title}</h1><p>{subtitle}</p></div>'


def score_card_html(home, away, home_flag, away_flag, score, meta) -> str:
    return (
        f'<div class="score-card">'
        f'<div class="side home"><img src="{home_flag}"> {home}</div>'
        f'<div class="score">{score}</div>'
        f'<div class="meta">{meta}</div>'
        f'<div class="side away">{away} <img src="{away_flag}"></div>'
        f'</div>'
    )
