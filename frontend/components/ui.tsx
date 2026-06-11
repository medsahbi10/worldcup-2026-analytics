/* Shared presentational components, styled from the WC2026 theme tokens. */
import { FlagCard, ScoreBox, groupColor } from "@/components/brand";

/** Flag — now rendered as the Figma white flag-card. */
export function Flag({ src, alt, size = 24 }: { src: string; alt: string; size?: number }) {
  return <FlagCard src={src} alt={alt} size={size} />;
}

export function PageTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-7 flex items-stretch gap-4">
      <span className="w-1.5 shrink-0 rounded-full bg-accent" />
      <div className="self-end">
        <h1 className="font-display text-4xl font-extrabold leading-[0.95] md:text-5xl">{title}</h1>
        {sub && <p className="mt-2 text-sm text-muted normal-case">{sub}</p>}
      </div>
    </div>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="wc-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 font-display text-3xl font-extrabold text-accent">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
    </div>
  );
}

/** Horizontal W/D/L probability bar (win green · draw grey · loss red). */
export function ProbBar({ h, d, a }: { h: number; d: number; a: number }) {
  const pct = (x: number) => `${(x * 100).toFixed(0)}%`;
  return (
    <div className="flex h-7 w-full overflow-hidden rounded-md text-xs font-semibold text-white">
      <div className="grid place-items-center bg-win" style={{ width: pct(h) }}>{pct(h)}</div>
      <div className="grid place-items-center bg-surface2 text-muted" style={{ width: pct(d) }}>{pct(d)}</div>
      <div className="grid place-items-center bg-loss" style={{ width: pct(a) }}>{pct(a)}</div>
    </div>
  );
}

/** Broadcast-style match card with dark score boxes and a group-colour edge. */
export function ScoreCard({
  home, away, homeFlag, awayFlag, homeScore, awayScore, kickoff, group, venue,
}: {
  home: string; away: string; homeFlag: string; awayFlag: string;
  homeScore?: number | null; awayScore?: number | null;
  kickoff?: string | null; group?: string | null; venue?: string | null;
}) {
  const played = homeScore != null && awayScore != null;
  const c = groupColor(group);
  return (
    <div className="wc-card flex items-center gap-3 px-3 py-2.5"
      style={{ borderLeft: `4px solid ${c.bg}` }}>
      <div className="flex w-2/5 items-center gap-2 font-semibold">
        <FlagCard src={homeFlag} alt={home} size={22} /> <span className="truncate">{home}</span>
      </div>
      <div className="flex w-1/5 flex-col items-center gap-1">
        <div className="flex items-center gap-1.5">
          <ScoreBox>{played ? homeScore : "–"}</ScoreBox>
          <ScoreBox>{played ? awayScore : "–"}</ScoreBox>
        </div>
        <span className="text-[10px] uppercase text-muted">
          {played ? (group ? `Grp ${group}` : "FT") : (kickoff ?? "vs")}
        </span>
      </div>
      <div className="flex w-2/5 items-center justify-end gap-2 font-semibold">
        <span className="truncate text-right">{away}</span> <FlagCard src={awayFlag} alt={away} size={22} />
      </div>
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return <div className="py-16 text-center text-sm text-muted">{label}</div>;
}

export function ApiError({ msg }: { msg: string }) {
  return (
    <div className="wc-card border-l-4 border-l-loss p-4 text-sm">
      <b>Couldn&apos;t reach the API.</b> Make sure it&apos;s running:
      <code className="ml-1 rounded bg-surface2 px-1">uvicorn wc2026.api:app --port 8000</code>
      <div className="mt-1 text-xs text-muted">{msg}</div>
    </div>
  );
}
