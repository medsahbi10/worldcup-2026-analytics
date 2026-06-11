/* Derived landing-page insights from the existing API data. */
import type { Team, Player, Prediction, Standing, Strength } from "@/lib/api";

/** Punching above weight: teams whose Elo rank beats their squad-value rank. */
export function punchingAboveWeight(teams: Team[], n = 6) {
  const withBoth = teams.filter((t) => t.elo != null && t.total_value_m != null);
  const eloRank = new Map([...withBoth].sort((a, b) => (b.elo ?? 0) - (a.elo ?? 0)).map((t, i) => [t.team_country, i + 1]));
  const valRank = new Map([...withBoth].sort((a, b) => (b.total_value_m ?? 0) - (a.total_value_m ?? 0)).map((t, i) => [t.team_country, i + 1]));
  return withBoth
    .map((t) => ({ team: t, gap: (valRank.get(t.team_country)! - eloRank.get(t.team_country)!) }))
    .sort((a, b) => b.gap - a.gap)
    .slice(0, n);
}

/** Best attacks / best defenses from the model ratings. */
export const lethalAttack = (s: Strength[], n = 6) => [...s].sort((a, b) => b.attack - a.attack).slice(0, n);
export const bestDefense = (s: Strength[], n = 6) => [...s].sort((a, b) => b.defense - a.defense).slice(0, n);

/** Star power: count of €50m+ players per team, plus the top-valued player. */
export function starPower(players: Player[], n = 6) {
  const by = new Map<string, { count: number; top: Player }>();
  for (const p of players) {
    if (p.market_value_eur == null) continue;
    const e = by.get(p.team_country);
    const isStar = p.market_value_eur >= 50_000_000 ? 1 : 0;
    if (!e) by.set(p.team_country, { count: isStar, top: p });
    else {
      e.count += isStar;
      if ((p.market_value_eur ?? 0) > (e.top.market_value_eur ?? 0)) e.top = p;
    }
  }
  return [...by.entries()]
    .map(([team, v]) => ({ team, ...v }))
    .sort((a, b) => b.count - a.count || (b.top.market_value_eur ?? 0) - (a.top.market_value_eur ?? 0))
    .slice(0, n);
}

/** Dark horses: NOT title favourites, but with strong deep-run odds.
 *  Excludes the top 8 by champion probability, ranks the rest by reach-QF odds. */
export function darkHorses(preds: Prediction[], n = 5): Prediction[] {
  const byChampion = [...preds].sort((a, b) => b.p_champion - a.p_champion);
  const favourites = new Set(byChampion.slice(0, 8).map((p) => p.team_country));
  return [...preds]
    .filter((p) => !favourites.has(p.team_country))
    .sort((a, b) => b.p_qf - a.p_qf)
    .slice(0, n);
}

/** Youngsters to shine: under-21s ranked by market value. */
export function youngsters(players: Player[], maxAge = 21, n = 8): Player[] {
  return players
    .filter((p) => p.age != null && p.age <= maxAge && p.market_value_eur != null)
    .sort((a, b) => (b.market_value_eur ?? 0) - (a.market_value_eur ?? 0))
    .slice(0, n);
}

/** Group of death: the group whose four teams have the highest combined strength. */
export function groupOfDeath(
  groups: Record<string, Standing[]>,
  teams: Team[],
): { letter: string; teams: Standing[]; score: number } | null {
  const strength = new Map(teams.map((t) => [t.team_country, t.strength ?? 0]));
  let best: { letter: string; teams: Standing[]; score: number } | null = null;
  for (const [letter, rows] of Object.entries(groups)) {
    const score = rows.reduce((s, r) => s + (strength.get(r.team_country) ?? 0), 0);
    if (!best || score > best.score) best = { letter, teams: rows, score };
  }
  return best;
}
