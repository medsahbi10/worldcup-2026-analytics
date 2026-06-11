"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, PageTitle, Spinner, ApiError } from "@/components/ui";

const CONFS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];

export default function TeamsPage() {
  const teams = useApi(() => api.teams(), []);
  const [conf, setConf] = useState("All");
  const rows = (teams.data ?? []).filter((t) => conf === "All" || t.confederation === conf);

  return (
    <div>
      <PageTitle title="Teams" sub="All 48 qualified nations · confederation, manager, squad value & model strength" />
      <div className="mb-5 flex flex-wrap gap-1">
        {CONFS.map((c) => (
          <button
            key={c}
            onClick={() => setConf(c)}
            className={`rounded-md px-3 py-1 text-sm font-display uppercase ${
              conf === c ? "bg-primary text-white" : "bg-surface2 text-muted hover:text-text"
            }`}
          >
            {c}
          </button>
        ))}
      </div>
      {teams.loading && <Spinner />}
      {teams.error && <ApiError msg={teams.error} />}
      {teams.data && (
        <div className="wc-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface2 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-2">Team</th>
                <th className="px-3 py-2">Conf.</th>
                <th className="px-3 py-2">Manager</th>
                <th className="px-2 py-2 text-right">Age</th>
                <th className="px-2 py-2 text-right">Value</th>
                <th className="px-2 py-2 text-right">Strength</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.team_country} className="border-t border-border">
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-2 font-semibold">
                      <Flag src={t.flag} alt={t.team_country} /> {t.team_country}
                    </span>
                  </td>
                  <td className="px-3 py-2"><span className="wc-chip">{t.confederation}</span></td>
                  <td className="px-3 py-2 text-muted">{t.manager ?? "—"}</td>
                  <td className="px-2 py-2 text-right text-muted">{t.avg_age ?? "—"}</td>
                  <td className="px-2 py-2 text-right">{t.total_value_m ? `€${Math.round(t.total_value_m)}m` : "—"}</td>
                  <td className="px-2 py-2 text-right font-display font-bold text-accent">
                    {t.strength != null ? t.strength.toFixed(2) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
