"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { PageTitle, Spinner, ApiError } from "@/components/ui";
import { Jersey } from "@/components/brand";

const CONFS = ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"];

export default function TeamsPage() {
  const teams = useApi(() => api.teams(), []);
  const [conf, setConf] = useState("All");
  const rows = [...(teams.data ?? [])]
    .filter((t) => conf === "All" || t.confederation === conf)
    .sort((a, b) => (b.total_value_m ?? 0) - (a.total_value_m ?? 0));

  return (
    <div>
      <PageTitle title="Teams" sub="All 48 qualified nations · confederation, manager, squad value & model strength" />
      <div className="mb-5 flex flex-wrap gap-1.5">
        {CONFS.map((c) => (
          <button
            key={c}
            onClick={() => setConf(c)}
            className={`rounded-md px-3 py-1 font-display text-sm font-bold uppercase ${
              conf === c ? "bg-accent text-[#08163a]" : "bg-surface2 text-muted hover:text-text"
            }`}
          >
            {c}
          </button>
        ))}
      </div>
      {teams.loading && <Spinner />}
      {teams.error && <ApiError msg={teams.error} />}
      {teams.data && (
        <div className="wc-board border border-border p-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {rows.map((t) => (
              <Link
                key={t.team_country}
                href={`/teams/${encodeURIComponent(t.team_country)}`}
                className="flex flex-col items-center rounded-xl border border-white/15 bg-[#06122e]/60 p-3 text-center transition-colors hover:border-accent">
                <div className="mb-2 h-20 w-20">
                  <Jersey iso={t.flag_iso} flag={t.flag} alt={t.team_country} size={80} />
                </div>
                <div className="font-display text-sm font-bold uppercase leading-tight">{t.team_country}</div>
                <div className="mt-0.5 text-[10px] uppercase text-muted">{t.confederation ?? "—"}</div>
                <div className="mt-1.5 flex items-center gap-2 text-[11px]">
                  {t.total_value_m != null && (
                    <span className="font-display font-bold text-accent">€{Math.round(t.total_value_m)}m</span>
                  )}
                  {t.strength != null && (
                    <span className="text-muted">str {t.strength.toFixed(2)}</span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
