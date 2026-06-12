"use client";

/* Match detail overlay — used for both upcoming fixtures and finished results.
 * Upcoming: model prediction (W/D/L + xG bars), head-to-head, comparison bars.
 * Finished: final score, a prediction-vs-result chart, expected-vs-actual goals,
 * and goalscorers. */
import { api, type Team, type MatchPrediction } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { FlagCard, groupColor } from "@/components/brand";
import { ProbBar, Spinner } from "@/components/ui";
import { wcHistory } from "@/lib/wcHistory";

const yr = (iso: string) => iso?.slice(0, 4) ?? "";
const pct = (x: number) => `${Math.round(x * 100)}%`;

function resultVerdict(p: MatchPrediction, hs: number, as_: number) {
  const probs = { home: p.p_home, draw: p.p_draw, away: p.p_away };
  const actual: keyof typeof probs = hs > as_ ? "home" : hs < as_ ? "away" : "draw";
  const fav = (["home", "draw", "away"] as const).reduce((a, b) => (probs[a] >= probs[b] ? a : b));
  const pa = probs[actual];
  if (actual === fav && probs[fav] >= 0.5) return { tag: "As predicted", tone: "text-win", note: `Model favourite came through (${Math.round(probs[fav] * 100)}%).` };
  if (pa < 0.2) return { tag: "Big upset", tone: "text-loss", note: `The model gave this just ${Math.round(pa * 100)}%.` };
  if (pa < 0.34) return { tag: "Surprise", tone: "text-loss", note: `Only a ${Math.round(pa * 100)}% outcome in the model.` };
  return { tag: "Roughly as expected", tone: "text-muted", note: `A ${Math.round(pa * 100)}% outcome.` };
}

function CompareBar({ label, home, away, fmt }: { label: string; home: number; away: number; fmt?: (n: number) => string }) {
  const total = home + away;
  const hp = total > 0 ? Math.round((home / total) * 100) : 50;
  const show = fmt ?? ((n: number) => String(n));
  return (
    <div className="py-2">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="font-bold tabular-nums">{show(home)}</span>
        <span className="text-[10px] uppercase tracking-wide text-muted">{label}</span>
        <span className="font-bold tabular-nums">{show(away)}</span>
      </div>
      <div className="flex h-2 overflow-hidden rounded-full bg-surface2">
        <div style={{ width: `${hp}%`, background: "var(--color-primary)" }} />
        <div style={{ width: `${100 - hp}%`, background: "var(--color-gold)" }} />
      </div>
    </div>
  );
}

function CompareText({ label, home, away }: { label: string; home: React.ReactNode; away: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-2 text-sm">
      <span className="text-right font-bold tabular-nums">{home}</span>
      <span className="text-[10px] uppercase tracking-wide text-muted">{label}</span>
      <span className="font-bold tabular-nums">{away}</span>
    </div>
  );
}

/** Prediction-vs-result chart: the 3 outcome probabilities as bars, the actual
 *  outcome highlighted. */
function PredVsResult({ p, home, away, actual }: {
  p: MatchPrediction; home: string; away: string; actual: "home" | "draw" | "away";
}) {
  const rows = [
    { key: "home", label: `${home} win`, prob: p.p_home, color: "var(--color-win)" },
    { key: "draw", label: "Draw", prob: p.p_draw, color: "var(--color-muted)" },
    { key: "away", label: `${away} win`, prob: p.p_away, color: "var(--color-loss)" },
  ] as const;
  return (
    <div className="space-y-2">
      {rows.map((r) => {
        const isActual = r.key === actual;
        return (
          <div key={r.key} className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0 truncate sm:w-28">{r.label}</span>
            <div className={`relative h-5 flex-1 overflow-hidden rounded-md bg-surface2 ${isActual ? "ring-2 ring-accent" : ""}`}>
              <div className="h-full rounded-md" style={{ width: pct(r.prob), background: r.color, opacity: isActual ? 1 : 0.4 }} />
            </div>
            <span className="w-9 shrink-0 text-right font-display font-bold tabular-nums">{pct(r.prob)}</span>
            <span className="w-14 shrink-0 text-[10px] font-bold uppercase text-accent">{isActual ? "✓ result" : ""}</span>
          </div>
        );
      })}
    </div>
  );
}

export function MatchModal({
  home, away, homeFlag, awayFlag, group, homeScore, awayScore, status, onClose,
}: {
  home: string; away: string; homeFlag: string; awayFlag: string;
  group?: string | null; homeScore?: number | null; awayScore?: number | null; status?: string;
  onClose: () => void;
}) {
  const h2h = useApi(() => api.h2h(home, away), [home, away]);
  const pred = useApi(() => api.predict(home, away), [home, away]);
  const teams = useApi(() => api.teams(), []);
  const find = (n: string): Team | undefined => teams.data?.find((t) => t.team_country === n);
  const ht = find(home);
  const at = find(away);
  const hHist = wcHistory(home);
  const aHist = wcHistory(away);

  const played = status === "played" && homeScore != null && awayScore != null;
  const c = groupColor(group);
  const verdict = played && pred.data ? resultVerdict(pred.data, homeScore!, awayScore!) : null;
  const actual: "home" | "draw" | "away" = played
    ? (homeScore! > awayScore! ? "home" : homeScore! < awayScore! ? "away" : "draw")
    : "draw";

  const xgTotal = pred.data ? pred.data.xg_home + pred.data.xg_away : 0;
  const xgHomePct = xgTotal > 0 ? Math.round((pred.data!.xg_home / xgTotal) * 100) : 50;

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="wc-card my-6 w-full max-w-2xl border border-border p-5 md:p-6" onClick={(e) => e.stopPropagation()}>
        {/* header */}
        <div className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FlagCard src={homeFlag} alt={home} size={40} />
            <span className="text-lg font-extrabold uppercase">{home}</span>
            <span className="text-muted">vs</span>
            <span className="text-lg font-extrabold uppercase">{away}</span>
            <FlagCard src={awayFlag} alt={away} size={40} />
          </div>
          <button onClick={onClose} className="rounded-md px-2 py-1 text-muted hover:bg-surface2 hover:text-text" aria-label="Close">✕</button>
        </div>

        {played ? (
          /* ============ FINISHED MATCH ============ */
          <>
            {/* full-time score */}
            <div className="mb-6 rounded-xl border border-border p-4" style={{ borderLeft: `5px solid ${c.bg}` }}>
              <div className="text-center text-[11px] uppercase tracking-wide text-muted">Full time</div>
              <div className="flex items-center justify-center gap-3 font-display text-4xl font-black tabular-nums">
                <span className={homeScore! > awayScore! ? "text-win" : ""}>{homeScore}</span>
                <span className="text-muted">–</span>
                <span className={awayScore! > homeScore! ? "text-win" : ""}>{awayScore}</span>
              </div>
            </div>

            {/* prediction vs result (chart) */}
            <div className="mb-6">
              <div className="mb-2 flex flex-wrap items-baseline gap-2">
                <span className="text-[11px] uppercase tracking-wide text-muted">Prediction vs result</span>
                {verdict && <span className={`font-display text-sm font-extrabold uppercase ${verdict.tone}`}>· {verdict.tag}</span>}
              </div>
              {pred.loading && <Spinner label="Checking the model…" />}
              {pred.data && <PredVsResult p={pred.data} home={home} away={away} actual={actual} />}
              {verdict && <p className="mt-2 text-xs text-muted">{verdict.note}</p>}
            </div>

            {/* expected vs actual goals */}
            {pred.data && (
              <div className="mb-6">
                <div className="mb-2 text-[11px] uppercase tracking-wide text-muted">Expected vs actual goals</div>
                <div className="space-y-2 text-sm">
                  {[
                    { name: home, flag: homeFlag, xg: pred.data.xg_home, goals: homeScore! },
                    { name: away, flag: awayFlag, xg: pred.data.xg_away, goals: awayScore! },
                  ].map((t) => {
                    const diff = t.goals - t.xg;
                    return (
                      <div key={t.name} className="flex items-center gap-3">
                        <FlagCard src={t.flag} alt={t.name} size={22} />
                        <span className="flex-1 truncate font-semibold uppercase">{t.name}</span>
                        <span className="text-muted">xG {t.xg.toFixed(2)}</span>
                        <span className="w-6 text-right font-display text-lg font-extrabold tabular-nums">{t.goals}</span>
                        <span className={`w-12 text-right text-xs font-bold tabular-nums ${diff >= 0.5 ? "text-win" : diff <= -0.5 ? "text-loss" : "text-muted"}`}>
                          {diff >= 0 ? "+" : ""}{diff.toFixed(1)}
                        </span>
                      </div>
                    );
                  })}
                </div>
                <p className="mt-1.5 text-[11px] text-muted">Goals minus xG — positive means they finished above expectation.</p>
              </div>
            )}

            {/* goalscorers */}
            <div>
              <div className="mb-2 text-[11px] uppercase tracking-wide text-muted">Goalscorers</div>
              <p className="text-sm text-muted">Goalscorer details aren&apos;t in the data feed yet — they&apos;ll appear once per-match events are ingested.</p>
            </div>
          </>
        ) : (
          /* ============ UPCOMING MATCH ============ */
          <>
            {pred.data && (
              <div className="mb-6">
                <div className="mb-1 text-center text-[11px] uppercase tracking-wide text-muted">Model prediction</div>
                <ProbBar h={pred.data.p_home} d={pred.data.p_draw} a={pred.data.p_away} />
                <div className="mt-1 flex justify-between text-[11px] text-muted">
                  <span>{home} win {pct(pred.data.p_home)}</span>
                  <span>draw {pct(pred.data.p_draw)}</span>
                  <span>{away} win {pct(pred.data.p_away)}</span>
                </div>
                <div className="mt-4">
                  <div className="mb-1 flex items-center justify-between text-[11px] text-muted">
                    <span className="font-bold text-text tabular-nums">{pred.data.xg_home.toFixed(2)} xG</span>
                    <span className="uppercase tracking-wide">Expected goals</span>
                    <span className="font-bold text-text tabular-nums">{pred.data.xg_away.toFixed(2)} xG</span>
                  </div>
                  <div className="flex h-6 w-full overflow-hidden rounded-md text-xs font-bold">
                    <div className="grid place-items-center text-white" style={{ width: `${xgHomePct}%`, background: "var(--color-primary)" }}>{xgHomePct}%</div>
                    <div className="grid place-items-center text-[#0f1014]" style={{ width: `${100 - xgHomePct}%`, background: "var(--color-gold)" }}>{100 - xgHomePct}%</div>
                  </div>
                </div>
              </div>
            )}

            {h2h.loading && <Spinner label="Loading head-to-head…" />}
            {h2h.data && (
              <>
                <div className="mb-1 text-center text-[11px] uppercase tracking-wide text-muted">All-time head-to-head</div>
                <div className="mb-5 grid grid-cols-3 overflow-hidden rounded-xl border border-border text-center">
                  <div className="bg-surface2 py-3">
                    <div className="font-display text-3xl font-extrabold text-win">{h2h.data.home_wins}</div>
                    <div className="text-[10px] uppercase text-muted">{home} wins</div>
                  </div>
                  <div className="border-x border-border py-3">
                    <div className="font-display text-3xl font-extrabold">{h2h.data.draws}</div>
                    <div className="text-[10px] uppercase text-muted">Draws · {h2h.data.played} played</div>
                  </div>
                  <div className="bg-surface2 py-3">
                    <div className="font-display text-3xl font-extrabold text-loss">{h2h.data.away_wins}</div>
                    <div className="text-[10px] uppercase text-muted">{away} wins</div>
                  </div>
                </div>
              </>
            )}

            <div className="mb-5">
              {teams.loading && <Spinner label="Loading teams…" />}
              {teams.data && (
                <div className="divide-y divide-border">
                  <CompareBar label="WC participations" home={hHist.appearances} away={aHist.appearances} />
                  <CompareText label="Best finish" home={hHist.best} away={aHist.best} />
                  <CompareBar label="Squad value (€m)" home={ht?.total_value_m ?? 0} away={at?.total_value_m ?? 0} fmt={(n) => `€${Math.round(n)}m`} />
                  <CompareBar label="Model strength" home={ht?.strength ?? 0} away={at?.strength ?? 0} fmt={(n) => n.toFixed(2)} />
                  <CompareBar label="Elo" home={ht?.elo ?? 0} away={at?.elo ?? 0} fmt={(n) => String(Math.round(n))} />
                </div>
              )}
            </div>

            {h2h.data && h2h.data.recent.length > 0 && (
              <div>
                <div className="mb-2 font-display text-sm font-bold uppercase">Recent meetings</div>
                <ul className="space-y-1 text-sm">
                  {h2h.data.recent.map((m, i) => (
                    <li key={i} className="flex items-center justify-between rounded-md px-3 py-1.5 text-muted">
                      <span>{yr(m.date)} · {m.tournament}</span>
                      <span className="font-semibold text-text">{m.home_team} {m.home_score ?? "–"}–{m.away_score ?? "–"} {m.away_team}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
