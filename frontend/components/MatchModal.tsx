"use client";

/* Match comparison overlay: model prediction (W/D/L bar), World Cup history of
 * both nations, all-time head-to-head, FlashScore-style stat comparison bars,
 * and recent meetings. */
import { api, type Team } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { FlagCard } from "@/components/brand";
import { ProbBar, Spinner } from "@/components/ui";
import { wcHistory } from "@/lib/wcHistory";

const yr = (iso: string) => iso?.slice(0, 4) ?? "";

/** FlashScore-style split bar: home value vs away value, proportional. */
function CompareBar({ label, home, away, fmt }: {
  label: string; home: number; away: number; fmt?: (n: number) => string;
}) {
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

/** Plain (non-numeric) compare row, e.g. best finish. */
function CompareText({ label, home, away }: { label: string; home: React.ReactNode; away: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 py-2 text-sm">
      <span className="text-right font-bold tabular-nums">{home}</span>
      <span className="text-[10px] uppercase tracking-wide text-muted">{label}</span>
      <span className="font-bold tabular-nums">{away}</span>
    </div>
  );
}

export function MatchModal({
  home, away, homeFlag, awayFlag, onClose,
}: {
  home: string; away: string; homeFlag: string; awayFlag: string; onClose: () => void;
}) {
  const h2h = useApi(() => api.h2h(home, away), [home, away]);
  const pred = useApi(() => api.predict(home, away), [home, away]);
  const teams = useApi(() => api.teams(), []);
  const find = (n: string): Team | undefined => teams.data?.find((t) => t.team_country === n);
  const ht = find(home);
  const at = find(away);
  const hHist = wcHistory(home);
  const aHist = wcHistory(away);
  const pct = (x: number) => `${Math.round(x * 100)}%`;

  return (
    <div
      className="fixed inset-0 z-[70] flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
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

        {/* model prediction */}
        {pred.data && (
          <div className="mb-6">
            <div className="mb-1 text-center text-[11px] uppercase tracking-wide text-muted">
              Model prediction · xG {pred.data.xg_home.toFixed(2)} – {pred.data.xg_away.toFixed(2)}
            </div>
            <ProbBar h={pred.data.p_home} d={pred.data.p_draw} a={pred.data.p_away} />
            <div className="mt-1 flex justify-between text-[11px] text-muted">
              <span>{home} win {pct(pred.data.p_home)}</span>
              <span>draw {pct(pred.data.p_draw)}</span>
              <span>{away} win {pct(pred.data.p_away)}</span>
            </div>
          </div>
        )}

        {/* head-to-head record */}
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

        {/* comparison bars (FlashScore style) */}
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

        {/* WC meetings */}
        {h2h.data && h2h.data.wc_count > 0 && (
          <div className="mb-5">
            <div className="mb-2 font-display text-sm font-bold uppercase text-accent">World Cup meetings ({h2h.data.wc_count})</div>
            <ul className="space-y-1 text-sm">
              {h2h.data.wc_meetings.map((m, i) => (
                <li key={i} className="flex items-center justify-between rounded-md bg-surface2 px-3 py-1.5">
                  <span className="text-muted">{yr(m.date)}</span>
                  <span className="font-semibold">{m.home_team} {m.home_score}–{m.away_score} {m.away_team}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* recent meetings */}
        {h2h.data && h2h.data.recent.length > 0 && (
          <div>
            <div className="mb-2 font-display text-sm font-bold uppercase">Recent meetings</div>
            <ul className="space-y-1 text-sm">
              {h2h.data.recent.map((m, i) => (
                <li key={i} className="flex items-center justify-between rounded-md px-3 py-1.5 text-muted">
                  <span>{yr(m.date)} · {m.tournament}</span>
                  <span className="font-semibold text-text">
                    {m.home_team} {m.home_score ?? "–"}–{m.away_score ?? "–"} {m.away_team}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {h2h.data && h2h.data.played === 0 && (
          <p className="text-center text-sm text-muted">These teams have never met.</p>
        )}
      </div>
    </div>
  );
}
