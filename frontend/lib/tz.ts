/* Kickoff times are stored in venue-local time. Convert to Tunisia (UTC+1, no
 * DST) using each 2026 host venue's June UTC offset (US/Canada on DST, Mexico
 * none). Match by substring so the "(Neutral Site)" suffix is ignored. */
const VENUE_OFFSET: Record<string, number> = {
  // Mexico (no DST) — UTC-6
  "Estadio Banorte": -6, "Estadio Akron": -6, "Estadio Azteca": -6,
  // US/Canada Eastern (EDT) — UTC-4
  MetLife: -4, "Lincoln Financial": -4, "Mercedes-Benz": -4, "BMO Field": -4,
  // Central (CDT) — UTC-5
  GEHA: -5, Arrowhead: -5, "AT&T": -5, NRG: -5,
  // Pacific (PDT) — UTC-7
  "Levi": -7, SoFi: -7, "Lumen Field": -7, "BC Place": -7,
};
const TUNISIA = 1;

export function toTunisia(kickoff?: string | null, venue?: string | null): { time: string; nextDay: boolean } | null {
  if (!kickoff) return null;
  const m = kickoff.match(/^(\d{1,2}):(\d{2})/);
  if (!m) return null;
  let offset = -5; // sensible default if a venue isn't matched
  if (venue) {
    for (const key in VENUE_OFFSET) {
      if (venue.includes(key)) { offset = VENUE_OFFSET[key]; break; }
    }
  }
  let h = parseInt(m[1], 10) + (TUNISIA - offset);
  let nextDay = false;
  while (h >= 24) { h -= 24; nextDay = true; }
  while (h < 0) { h += 24; }
  return { time: `${String(h).padStart(2, "0")}:${m[2]}`, nextDay };
}
