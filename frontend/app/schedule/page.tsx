"use client";

import { useState } from "react";
import { api, type Fixture } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { ScoreCard, PageTitle, Spinner, ApiError } from "@/components/ui";

const GROUPS = ["All", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"];

export default function SchedulePage() {
  const [group, setGroup] = useState("All");
  const fixtures = useApi(() => api.fixtures(group === "All" ? undefined : group), [group]);

  // group fixtures by date
  const byDate: Record<string, Fixture[]> = {};
  (fixtures.data ?? []).forEach((f) => {
    const d = f.match_date.slice(0, 10);
    (byDate[d] ||= []).push(f);
  });

  return (
    <div>
      <PageTitle title="Schedule" sub="72 group-stage fixtures · venues & kickoff times (local)" />
      <div className="mb-5 flex flex-wrap gap-1">
        {GROUPS.map((g) => (
          <button
            key={g}
            onClick={() => setGroup(g)}
            className={`rounded-md px-3 py-1 text-sm font-display uppercase ${
              group === g ? "bg-primary text-white" : "bg-surface2 text-muted hover:text-text"
            }`}
          >
            {g === "All" ? "All" : `Grp ${g}`}
          </button>
        ))}
      </div>

      {fixtures.loading && <Spinner />}
      {fixtures.error && <ApiError msg={fixtures.error} />}
      {fixtures.data && (
        <div className="space-y-6">
          {Object.entries(byDate).map(([date, matches]) => (
            <div key={date}>
              <h3 className="mb-2 font-display text-sm uppercase text-accent">
                {new Date(date).toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" })}
              </h3>
              <div className="space-y-2">
                {matches.map((m, i) => (
                  <ScoreCard
                    key={i}
                    home={m.home_team}
                    away={m.away_team}
                    homeFlag={m.home_flag}
                    awayFlag={m.away_flag}
                    score={m.status === "played" && m.home_score != null
                      ? `${m.home_score} – ${m.away_score}`
                      : (m.kickoff_local ?? "vs")}
                    meta={`Grp ${m.group_letter ?? "–"} · ${(m.venue ?? "").split(" (")[0]}`}
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
