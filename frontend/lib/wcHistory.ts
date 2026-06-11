/* World Cup historical reference data, keyed by the API's `team_country`.
 * Figures are pre-2026 (FIFA World Cup finals appearances through 2022 and the
 * nation's best finish). Static reference data — there is no warehouse table
 * for tournament history, so it lives here. Debutants show appearances: 0. */
export interface WcHistory {
  appearances: number; // World Cup finals tournaments reached (through 2022)
  best: string;        // best finish
  bestYear?: string;   // when the best finish was achieved
}

export const WC_HISTORY: Record<string, WcHistory> = {
  Brazil: { appearances: 22, best: "Winners (×5)", bestYear: "2002" },
  Germany: { appearances: 20, best: "Winners (×4)", bestYear: "2014" },
  Argentina: { appearances: 18, best: "Winners (×3)", bestYear: "2022" },
  France: { appearances: 16, best: "Winners (×2)", bestYear: "2018" },
  Spain: { appearances: 16, best: "Winners", bestYear: "2010" },
  England: { appearances: 16, best: "Winners", bestYear: "1966" },
  Uruguay: { appearances: 14, best: "Winners (×2)", bestYear: "1950" },
  Netherlands: { appearances: 11, best: "Runners-up (×3)", bestYear: "2010" },
  Sweden: { appearances: 12, best: "Runners-up", bestYear: "1958" },
  Croatia: { appearances: 6, best: "Runners-up", bestYear: "2018" },
  Czechia: { appearances: 10, best: "Runners-up (×2)", bestYear: "1962" },
  "Korea Republic": { appearances: 11, best: "Fourth place", bestYear: "2002" },
  Belgium: { appearances: 14, best: "Third place", bestYear: "2018" },
  Portugal: { appearances: 8, best: "Third place", bestYear: "1966" },
  "United States": { appearances: 11, best: "Third place", bestYear: "1930" },
  Austria: { appearances: 7, best: "Third place", bestYear: "1954" },
  Türkiye: { appearances: 2, best: "Third place", bestYear: "2002" },
  Morocco: { appearances: 6, best: "Fourth place", bestYear: "2022" },
  Mexico: { appearances: 17, best: "Quarter-finals", bestYear: "1986" },
  Switzerland: { appearances: 12, best: "Quarter-finals", bestYear: "1954" },
  Paraguay: { appearances: 8, best: "Quarter-finals", bestYear: "2010" },
  Colombia: { appearances: 6, best: "Quarter-finals", bestYear: "2014" },
  Ghana: { appearances: 4, best: "Quarter-finals", bestYear: "2010" },
  Senegal: { appearances: 3, best: "Quarter-finals", bestYear: "2002" },
  Japan: { appearances: 7, best: "Round of 16", bestYear: "2022" },
  Australia: { appearances: 6, best: "Round of 16", bestYear: "2006" },
  "Saudi Arabia": { appearances: 6, best: "Round of 16", bestYear: "1994" },
  Algeria: { appearances: 4, best: "Round of 16", bestYear: "2014" },
  Ecuador: { appearances: 4, best: "Round of 16", bestYear: "2006" },
  Norway: { appearances: 3, best: "Round of 16", bestYear: "1998" },
  Scotland: { appearances: 8, best: "Group stage" },
  Tunisia: { appearances: 6, best: "Group stage" },
  "IR Iran": { appearances: 6, best: "Group stage" },
  Egypt: { appearances: 3, best: "Group stage" },
  "South Africa": { appearances: 3, best: "Group stage" },
  "Côte d'Ivoire": { appearances: 3, best: "Group stage" },
  "New Zealand": { appearances: 2, best: "Group stage" },
  "Bosnia-Herzegovina": { appearances: 1, best: "Group stage", bestYear: "2014" },
  Qatar: { appearances: 1, best: "Group stage", bestYear: "2022" },
  Iraq: { appearances: 1, best: "Group stage", bestYear: "1986" },
  Panama: { appearances: 1, best: "Group stage", bestYear: "2018" },
  Haiti: { appearances: 1, best: "Group stage", bestYear: "1974" },
  "Congo DR": { appearances: 1, best: "Group stage", bestYear: "1974" },
  "Cape Verde": { appearances: 0, best: "Debut" },
  "Curaçao": { appearances: 0, best: "Debut" },
  Jordan: { appearances: 0, best: "Debut" },
  Uzbekistan: { appearances: 0, best: "Debut" },
};

export const wcHistory = (country: string): WcHistory =>
  WC_HISTORY[country] ?? { appearances: 0, best: "—" };
