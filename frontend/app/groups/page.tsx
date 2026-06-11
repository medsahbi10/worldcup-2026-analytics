"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, PageTitle, Spinner, ApiError } from "@/components/ui";

export default function GroupsPage() {
  const groups = useApi(() => api.groups(), []);
  return (
    <div>
      <PageTitle title="Groups" sub="Standings update live as matches are played — zero before kickoff." />
      {groups.loading && <Spinner />}
      {groups.error && <ApiError msg={groups.error} />}
      {groups.data && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.entries(groups.data).map(([letter, rows]) => (
            <div key={letter} className="wc-card overflow-hidden">
              <div className="flex items-center gap-2 bg-surface2 px-4 py-2">
                <span className="grid h-6 w-6 place-items-center rounded bg-primary text-sm font-bold text-white">
                  {letter}
                </span>
                <span className="font-display font-semibold uppercase">Group {letter}</span>
              </div>
              <table className="w-full text-sm">
                <thead className="text-[11px] uppercase text-muted">
                  <tr>
                    <th className="px-3 py-1 text-left">Team</th>
                    <th className="px-1 py-1">P</th>
                    <th className="px-1 py-1">GD</th>
                    <th className="px-2 py-1">Pts</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={r.team_country} className={`border-t border-border ${i < 2 ? "bg-pitch/10" : ""}`}>
                      <td className="px-3 py-1.5">
                        <span className="flex items-center gap-2">
                          <Flag src={r.flag} alt={r.team_country} size={18} />
                          <span className="truncate">{r.team_country}</span>
                        </span>
                      </td>
                      <td className="px-1 py-1.5 text-center text-muted">{r.played}</td>
                      <td className="px-1 py-1.5 text-center text-muted">{r.goal_diff}</td>
                      <td className="px-2 py-1.5 text-center font-bold">{r.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
      <p className="mt-4 text-xs text-muted">Top 2 of each group (highlighted) + 8 best third-placed teams advance.</p>
    </div>
  );
}
