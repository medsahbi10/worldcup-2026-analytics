"use client";

/* Lightweight, on-brand charts (no external deps). */
import { FlagCard } from "@/components/brand";

/** Horizontal ranked bar chart with optional flags + value labels. */
export function HBarChart({
  data, color = "var(--color-accent)", max, format = (n) => `${Math.round(n)}`,
}: {
  data: { label: string; value: number; flag?: string }[];
  color?: string; max?: number; format?: (n: number) => string;
}) {
  const top = max ?? Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="space-y-2">
      {data.map((d) => (
        <div key={d.label} className="flex items-center gap-2 text-xs">
          {d.flag && <FlagCard src={d.flag} alt={d.label} size={22} />}
          <span className="w-24 shrink-0 truncate font-semibold sm:w-32">{d.label}</span>
          <div className="relative h-4 flex-1 overflow-hidden rounded-md bg-surface2">
            <div className="h-full rounded-md" style={{ width: `${(d.value / top) * 100}%`, background: color }} />
          </div>
          <span className="w-16 shrink-0 text-right font-display font-bold tabular-nums">{format(d.value)}</span>
        </div>
      ))}
    </div>
  );
}

/** Dumbbell chart: two ranked positions per row (e.g. expected vs current),
 *  connected by a line; the gap is shown as +/- places. Rank 1 = left/best. */
export function DumbbellChart({ data, max, aLabel, bLabel }: {
  data: { label: string; a: number; b: number; flag?: string }[];
  max: number; aLabel: string; bLabel: string;
}) {
  const pos = (r: number) => `${((r - 1) / (max - 1 || 1)) * 100}%`;
  return (
    <div>
      <div className="mb-3 flex gap-4 text-[11px] text-muted">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-muted" /> {aLabel}</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-accent" /> {bLabel}</span>
      </div>
      <div className="space-y-2.5">
        {data.map((d) => {
          const better = d.b < d.a;
          const lo = Math.min(d.a, d.b), hi = Math.max(d.a, d.b);
          return (
            <div key={d.label} className="flex items-center gap-2 text-xs">
              {d.flag && <FlagCard src={d.flag} alt={d.label} size={20} />}
              <span className="w-24 shrink-0 truncate font-semibold sm:w-28">{d.label}</span>
              <div className="relative h-4 flex-1">
                <div className="absolute top-1/2 h-px w-full -translate-y-1/2 bg-border" />
                <div
                  className="absolute top-1/2 h-[3px] -translate-y-1/2 rounded-full"
                  style={{ left: pos(lo), width: `calc(${pos(hi)} - ${pos(lo)})`, background: better ? "var(--color-win)" : "var(--color-loss)" }}
                />
                <div className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-muted" style={{ left: pos(d.a) }} />
                <div className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent ring-2 ring-bg" style={{ left: pos(d.b) }} />
              </div>
              <span className="w-12 shrink-0 text-right font-display font-bold tabular-nums"
                style={{ color: better ? "var(--color-win)" : "var(--color-loss)" }}>
                {better ? "+" : ""}{d.a - d.b}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-[10px] text-muted"><span>#1 best</span><span>#{max}</span></div>
    </div>
  );
}

/** Donut with a centre total and a legend. */
export function Donut({ data, size = 180 }: { data: { label: string; value: number; color: string }[]; size?: number }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let acc = 0;
  const stops = data
    .map((d) => {
      const start = (acc / total) * 100;
      acc += d.value;
      return `${d.color} ${start}% ${(acc / total) * 100}%`;
    })
    .join(", ");
  return (
    <div className="flex flex-wrap items-center gap-5">
      <div className="relative shrink-0 rounded-full" style={{ width: size, height: size, background: `conic-gradient(${stops})` }}>
        <div className="absolute inset-[20%] grid place-items-center rounded-full bg-surface">
          <span className="font-display text-2xl font-extrabold">{total}</span>
        </div>
      </div>
      <ul className="space-y-1.5 text-sm">
        {data.map((d) => (
          <li key={d.label} className="flex items-center gap-2">
            <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: d.color }} />
            <span className="text-muted">{d.label}</span>
            <span className="font-display font-bold tabular-nums">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Scatter plot (e.g. squad value vs average age). */
export function Scatter({
  data, xLabel, yLabel, width = 580, height = 320, color = "var(--color-accent)",
}: {
  data: { x: number; y: number; label: string }[];
  xLabel: string; yLabel: string; width?: number; height?: number; color?: string;
}) {
  const pad = 40;
  const xs = data.map((d) => d.x);
  const ys = data.map((d) => d.y);
  const xmin = Math.min(...xs), xmax = Math.max(...xs);
  const ymin = Math.min(...ys), ymax = Math.max(...ys);
  const sx = (x: number) => pad + ((x - xmin) / (xmax - xmin || 1)) * (width - 2 * pad);
  const sy = (y: number) => height - pad - ((y - ymin) / (ymax - ymin || 1)) * (height - 2 * pad);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" role="img" aria-label={`${yLabel} vs ${xLabel}`}>
      <line x1={pad} y1={height - pad} x2={width - pad} y2={height - pad} stroke="var(--color-border)" />
      <line x1={pad} y1={pad} x2={pad} y2={height - pad} stroke="var(--color-border)" />
      {data.map((d, i) => (
        <circle key={i} cx={sx(d.x)} cy={sy(d.y)} r={5} fill={color} opacity={0.8}>
          <title>{`${d.label} — ${xLabel}: ${Math.round(d.x)}, ${yLabel}: ${d.y}`}</title>
        </circle>
      ))}
      <text x={width / 2} y={height - 8} textAnchor="middle" fontSize="11" fill="var(--color-muted)">{xLabel}</text>
      <text x={14} y={height / 2} textAnchor="middle" fontSize="11" fill="var(--color-muted)" transform={`rotate(-90 14 ${height / 2})`}>{yLabel}</text>
    </svg>
  );
}
