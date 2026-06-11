// Typed client for the World Cup 2026 FastAPI backend.
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export interface Team {
  team_country: string;
  confederation: string | null;
  manager: string | null;
  squad_size: number | null;
  avg_age: number | null;
  total_value_m: number | null;
  strength: number | null;
  elo: number | null;
  flag: string;
  flag_iso: string | null;
}

export interface Standing {
  group_letter: string;
  rank: number | null;
  team_country: string;
  played: number; won: number; drawn: number; lost: number;
  goals_for: number; goals_against: number; goal_diff: number; points: number;
  flag: string;
}

export interface Fixture {
  match_date: string;
  kickoff_local: string | null;
  stage: string | null;
  group_letter: string | null;
  home_team: string; away_team: string;
  home_score: number | null; away_score: number | null;
  venue: string | null; status: string;
  home_flag: string; away_flag: string;
}

export interface Player {
  player_id: number; player_name: string; team_country: string;
  shirt_number: number | null; position: string | null; primary_position: string | null;
  club: string | null; age: number | null;
  market_value_eur: number | null; photo_url: string | null; flag: string;
}

export interface LineupRow {
  position: string | null; shirt_number: number | null; player_name: string;
  club: string | null; market_value_eur: number | null; photo_url: string | null;
  formation: string;
}

export interface HistoricalStat {
  player_name: string; team: string;
  goals: number; assists: number; minutes: number; goals_per90: number;
}

export interface Prediction {
  team_country: string;
  p_advance: number; p_r16: number; p_qf: number; p_sf: number;
  p_final: number; p_champion: number; flag: string;
}

export interface MatchPrediction {
  home: string; away: string;
  p_home: number; p_draw: number; p_away: number;
  xg_home: number; xg_away: number;
  home_flag: string; away_flag: string;
}

export interface H2HMatch {
  date: string; home_team: string; away_team: string;
  home_score: number | null; away_score: number | null; tournament: string; neutral: boolean;
}

export interface H2H {
  home: string; away: string; played: number;
  home_wins: number; draws: number; away_wins: number;
  home_goals: number; away_goals: number; wc_count: number;
  recent: H2HMatch[]; wc_meetings: H2HMatch[];
}

export interface Strength {
  team_country: string; attack: number; defense: number; overall: number;
  elo: number | null; total_value_m: number | null; flag: string; flag_iso: string | null;
}

export interface FormResult {
  result: "W" | "D" | "L"; gf: number; ga: number; opponent: string; date: string;
}

export const api = {
  teams: () => get<Team[]>("/api/teams"),
  groups: () => get<Record<string, Standing[]>>("/api/groups"),
  fixtures: (group?: string, team?: string) => {
    const qs = new URLSearchParams();
    if (group) qs.set("group", group);
    if (team) qs.set("team", team);
    return get<Fixture[]>(`/api/fixtures${qs.toString() ? `?${qs}` : ""}`);
  },
  players: (team?: string, position?: string) => {
    const qs = new URLSearchParams();
    if (team) qs.set("team", team);
    if (position) qs.set("position", position);
    return get<Player[]>(`/api/players${qs.toString() ? `?${qs}` : ""}`);
  },
  lineup: (team: string) => get<LineupRow[]>(`/api/lineup/${encodeURIComponent(team)}`),
  predictions: () => get<Prediction[]>("/api/predictions"),
  historical: () => get<HistoricalStat[]>("/api/historical"),
  strengths: () => get<Strength[]>("/api/strengths"),
  predict: (home: string, away: string) =>
    get<MatchPrediction>(`/api/predict?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`),
  h2h: (home: string, away: string) =>
    get<H2H>(`/api/h2h?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`),
  form: () => get<Record<string, FormResult[]>>("/api/form"),
};
