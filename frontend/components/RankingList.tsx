"use client";

/* Teal ranking card (design/screen/ranking.png): dark rounded rows of
 * rank · team · value · flag, on a #057C8D shell. Reused everywhere a
 * ranking appears. */
import Link from "next/link";
import { FlagCard } from "@/components/brand";

export interface RankRow {
  team_country: string;
  flag: string;
  value?: string | number;
}

export function RankingList({ rows, size = 42 }: { rows: RankRow[]; size?: number }) {
  return (
    <div
      className="flex flex-col gap-2"
      style={{ background: "#057C8D", borderRadius: "clamp(28px,3vw,52px)", padding: "clamp(14px,1.8vw,32px)" }}
    >
      {rows.map((t, i) => (
        <Link
          key={t.team_country}
          href={`/teams/${encodeURIComponent(t.team_country)}`}
          className="flex items-center gap-3 rounded-2xl px-4 py-2 transition-colors hover:bg-black/25"
          style={{ background: "rgba(3,30,34,0.55)" }}
        >
          <span className="w-7 shrink-0 font-display text-lg font-black tabular-nums text-white/55">{i + 1}</span>
          <span className="flex-1 truncate font-bold uppercase tracking-wide text-[#F7F7F8]">{t.team_country}</span>
          {t.value != null && (
            <span className="shrink-0 font-display font-bold tabular-nums text-accent">{t.value}</span>
          )}
          <FlagCard src={t.flag} alt={t.team_country} size={size} />
        </Link>
      ))}
    </div>
  );
}
