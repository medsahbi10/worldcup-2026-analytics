/* Shared presentational components, styled from theme tokens. */
import Image from "next/image";

export function Flag({ src, alt, size = 22 }: { src: string; alt: string; size?: number }) {
  // flagcdn images; unoptimized to avoid Next remote-image config in dev
  return (
    <Image
      src={src}
      alt={alt}
      width={size}
      height={Math.round(size * 0.7)}
      unoptimized
      className="inline-block rounded-[2px] object-cover align-middle"
    />
  );
}

export function PageTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-3xl font-bold uppercase tracking-wide">{title}</h1>
      {sub && <p className="mt-1 text-sm text-muted">{sub}</p>}
    </div>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="wc-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 font-display text-2xl font-bold">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
    </div>
  );
}

/** Horizontal W/D/L probability bar. */
export function ProbBar({ h, d, a }: { h: number; d: number; a: number }) {
  const pct = (x: number) => `${(x * 100).toFixed(0)}%`;
  return (
    <div className="flex h-7 w-full overflow-hidden rounded-md text-xs font-semibold text-white">
      <div className="grid place-items-center bg-pitch" style={{ width: pct(h) }}>{pct(h)}</div>
      <div className="grid place-items-center bg-surface2 text-muted" style={{ width: pct(d) }}>{pct(d)}</div>
      <div className="grid place-items-center bg-primary" style={{ width: pct(a) }}>{pct(a)}</div>
    </div>
  );
}

/** Broadcast-style scoreboard card. */
export function ScoreCard({
  home, away, homeFlag, awayFlag, score, meta,
}: {
  home: string; away: string; homeFlag: string; awayFlag: string; score: string; meta?: string;
}) {
  return (
    <div className="wc-card flex items-center justify-between border-l-4 border-l-primary px-4 py-3">
      <div className="flex w-2/5 items-center gap-2 font-semibold">
        <Flag src={homeFlag} alt={home} /> <span className="truncate">{home}</span>
      </div>
      <div className="flex w-1/5 flex-col items-center">
        <span className="font-display text-xl font-bold">{score}</span>
        {meta && <span className="text-[10px] uppercase text-muted">{meta}</span>}
      </div>
      <div className="flex w-2/5 items-center justify-end gap-2 font-semibold">
        <span className="truncate text-right">{away}</span> <Flag src={awayFlag} alt={away} />
      </div>
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return <div className="py-16 text-center text-sm text-muted">{label}</div>;
}

export function ApiError({ msg }: { msg: string }) {
  return (
    <div className="wc-card border-l-4 border-l-primary p-4 text-sm">
      <b>Couldn&apos;t reach the API.</b> Make sure it&apos;s running:
      <code className="ml-1 rounded bg-surface2 px-1">uvicorn wc2026.api:app --port 8000</code>
      <div className="mt-1 text-xs text-muted">{msg}</div>
    </div>
  );
}
