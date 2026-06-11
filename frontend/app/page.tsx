"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, StatCard, Spinner, ApiError } from "@/components/ui";

export default function Home() {
  const preds = useApi(() => api.predictions(), []);
  const teams = useApi(() => api.teams(), []);

  return (
    <div>
      {/* hero */}
      <div className="wc-card mb-8 overflow-hidden">
        <div className="bg-gradient-to-r from-[#0d1b2a] via-[#10243e] to-primary/40 p-8">
          <div className="wc-chip mb-3 inline-block">11 June – 19 July 2026 · USA · Mexico · Canada</div>
          <h1 className="text-4xl font-bold uppercase leading-tight">
            FIFA World Cup 2026<br />
            <span className="text-accent">Analytics & Forecast</span>
          </h1>
          <p className="mt-2 max-w-xl text-sm text-muted">
            48 teams · 104 matches. Squads, market values, group standings, the full schedule, and a
            Dixon-Coles model that simulates the tournament 20,000 times.
          </p>
          <div className="mt-4 flex gap-3">
            <Link href="/predictions" className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white">
              View predictions →
            </Link>
            <Link href="/groups" className="rounded-md border border-border px-4 py-2 text-sm font-semibold">
              Groups
            </Link>
          </div>
        </div>
      </div>

      <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Teams" value="48" />
        <StatCard label="Matches" value="104" />
        <StatCard label="Groups" value="12" />
        <StatCard label="Simulations" value="20,000" />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* favourites */}
        <section>
          <h2 className="mb-3 text-xl font-bold uppercase">Title favourites</h2>
          {preds.loading && <Spinner />}
          {preds.error && <ApiError msg={preds.error} />}
          {preds.data && (
            <div className="wc-card divide-y divide-border">
              {preds.data.slice(0, 8).map((t, i) => (
                <div key={t.team_country} className="flex items-center gap-3 px-4 py-2.5">
                  <span className="w-5 text-sm text-muted">{i + 1}</span>
                  <Flag src={t.flag} alt={t.team_country} />
                  <span className="flex-1 font-semibold">{t.team_country}</span>
                  <span className="font-display text-lg font-bold text-accent">
                    {(t.p_champion * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
              <Link href="/predictions" className="block px-4 py-2 text-center text-sm text-muted hover:text-text">
                Full odds →
              </Link>
            </div>
          )}
        </section>

        {/* strongest squads by value */}
        <section>
          <h2 className="mb-3 text-xl font-bold uppercase">Most valuable squads</h2>
          {teams.loading && <Spinner />}
          {teams.error && <ApiError msg={teams.error} />}
          {teams.data && (
            <div className="wc-card divide-y divide-border">
              {[...teams.data]
                .filter((t) => t.total_value_m)
                .sort((a, b) => (b.total_value_m ?? 0) - (a.total_value_m ?? 0))
                .slice(0, 8)
                .map((t) => (
                  <div key={t.team_country} className="flex items-center gap-3 px-4 py-2.5">
                    <Flag src={t.flag} alt={t.team_country} />
                    <span className="flex-1 font-semibold">{t.team_country}</span>
                    <span className="wc-chip">{t.confederation}</span>
                    <span className="font-display font-bold">€{Math.round(t.total_value_m ?? 0)}m</span>
                  </div>
                ))}
              <Link href="/teams" className="block px-4 py-2 text-center text-sm text-muted hover:text-text">
                All teams →
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
