"use client";

/* Group card (design/image.png): group-color shell + white letter + dark inner
 * panel with flag · (name over progression chips) rows, dividers, and an
 * optional standings toggle. Shared by the Groups page and the landing. */
import Link from "next/link";
import { useState } from "react";
import type { Standing, Prediction } from "@/lib/api";
import { FlagCard, groupColor, StageChips } from "@/components/brand";

export function GroupCard({ letter, teams, predOf, standings = true }: {
  letter: string;
  teams: Standing[];
  predOf?: Map<string, Prediction>;
  standings?: boolean;
}) {
  const c = groupColor(letter);
  const [open, setOpen] = useState(false);
  const table = [...teams].sort((a, b) => b.points - a.points || b.goal_diff - a.goal_diff);

  return (
    <div
      className="flex items-stretch gap-3"
      style={{ background: c.bg, borderRadius: "clamp(24px,1.8vw,40px)", padding: "10px 10px 10px 14px" }}
    >
      <div className="flex shrink-0 items-center justify-center" style={{ width: "clamp(34px,2.4vw,52px)" }}>
        <span className="font-display font-black uppercase leading-none text-white" style={{ fontSize: "clamp(34px,2.6vw,56px)" }}>
          {letter}
        </span>
      </div>

      <div
        className="flex min-w-0 flex-1 flex-col overflow-hidden"
        style={{ background: "#151519", borderRadius: "clamp(16px,1.3vw,28px)", padding: "clamp(10px,0.8vw,16px)" }}
      >
        {teams.map((t, i) => {
          const pr = predOf?.get(t.team_country);
          return (
            <div key={t.team_country}>
              <Link
                href={`/teams/${encodeURIComponent(t.team_country)}`}
                className="flex items-center gap-2.5 py-1.5 transition-opacity hover:opacity-80"
              >
                <FlagCard src={t.flag} alt={t.team_country} size={32} />
                <span className="min-w-0 flex-1 truncate font-bold uppercase tracking-wide text-[#F7F7F8]" style={{ fontSize: "clamp(12px,0.85vw,15px)" }}>
                  {t.team_country}
                </span>
                {predOf && (
                  <StageChips stages={[
                    { label: "ADV", p: pr?.p_advance },
                    { label: "QF", p: pr?.p_qf },
                  ]} />
                )}
              </Link>
              {i < teams.length - 1 && <div style={{ borderTop: "1.5px solid #707287" }} />}
            </div>
          );
        })}

        {standings && (
          <>
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="mt-2 flex items-center gap-1 self-start font-display text-xs font-bold uppercase tracking-wide text-muted transition-colors hover:text-[#F7F7F8]"
            >
              Standings <span className="leading-none">{open ? "▴" : "▾"}</span>
            </button>
            {open && (
              <table className="mt-2 w-full border-collapse text-xs text-[#F7F7F8]">
                <thead>
                  <tr className="text-[10px] uppercase tracking-wide text-muted">
                    <th className="py-1 text-left font-display font-bold">Team</th>
                    {["P", "W", "D", "L", "GD", "Pts"].map((h) => (
                      <th key={h} className="py-1 text-right font-display font-bold">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.map((t) => (
                    <tr key={t.team_country} style={{ borderTop: "1px solid rgba(112,114,135,0.35)" }}>
                      <td className="truncate py-1 pr-2 text-left">{t.team_country}</td>
                      <td className="py-1 text-right tabular-nums">{t.played}</td>
                      <td className="py-1 text-right tabular-nums">{t.won}</td>
                      <td className="py-1 text-right tabular-nums">{t.drawn}</td>
                      <td className="py-1 text-right tabular-nums">{t.lost}</td>
                      <td className="py-1 text-right tabular-nums">{t.goal_diff}</td>
                      <td className="py-1 text-right font-bold tabular-nums text-accent">{t.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}
