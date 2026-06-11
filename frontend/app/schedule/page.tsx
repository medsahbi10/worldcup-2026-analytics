"use client";

import { useState } from "react";
import { api, type Fixture } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { PageTitle, Spinner, ApiError } from "@/components/ui";
import { MatchCard } from "@/components/MatchCard";
import { groupColor } from "@/components/brand";

const GROUPS = ["All", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"];

export default function SchedulePage() {
  const [group, setGroup] = useState("All");
  const fixtures = useApi(() => api.fixtures(group === "All" ? undefined : group), [group]);

  // group fixtures by matchday (date)
  const byDate: Record<string, Fixture[]> = {};
  (fixtures.data ?? []).forEach((f) => {
    const d = f.match_date.slice(0, 10);
    (byDate[d] ||= []).push(f);
  });
  const dates = Object.keys(byDate).sort();

  return (
    <div>
      <PageTitle title="Schedule" sub="Group-stage fixtures by matchday · kickoff times in Tunisia (UTC+1)." />
      <div className="mb-6 flex flex-wrap gap-1.5">
        {GROUPS.map((g) => {
          const active = group === g;
          const c = groupColor(g);
          return (
            <button
              key={g}
              onClick={() => setGroup(g)}
              className="rounded-md px-3 py-1 font-display text-sm font-bold uppercase"
              style={active
                ? (g === "All" ? { background: "var(--color-accent)", color: "#0f1014" } : { background: c.bg, color: c.ink })
                : { background: "var(--color-surface2)", color: "var(--color-muted)" }}
            >
              {g === "All" ? "All" : `Grp ${g}`}
            </button>
          );
        })}
      </div>

      {fixtures.loading && <Spinner />}
      {fixtures.error && <ApiError msg={fixtures.error} />}
      {fixtures.data && (
        <div className="space-y-8">
          {dates.map((d) => (
            <div key={d}>
              <h3 className="mb-3 flex items-center gap-3 font-display text-lg font-extrabold uppercase">
                <span className="h-5 w-1 rounded-full bg-accent" />
                {new Date(d).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}
              </h3>
              <div className="space-y-4">
                {byDate[d].map((m, i) => (
                  <MatchCard
                    key={i}
                    home={m.home_team}
                    away={m.away_team}
                    homeFlag={m.home_flag}
                    awayFlag={m.away_flag}
                    group={m.group_letter}
                    matchDate={m.match_date}
                    kickoff={m.kickoff_local}
                    venue={m.venue}
                    homeScore={m.home_score}
                    awayScore={m.away_score}
                    status={m.status}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
