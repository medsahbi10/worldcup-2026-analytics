"use client";

import Image from "next/image";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, PageTitle, Spinner, ApiError } from "@/components/ui";

export default function LineupsPage() {
  const teams = useApi(() => api.teams(), []);
  const [team, setTeam] = useState("Argentina");
  const lineup = useApi(() => api.lineup(team), [team]);
  const names = teams.data?.map((t) => t.team_country).sort() ?? [];
  const teamFlag = teams.data?.find((t) => t.team_country === team)?.flag ?? "";
  const formation = lineup.data?.[0]?.formation;

  return (
    <div>
      <PageTitle title="Predicted lineups" sub="Likely starting XI from each team's most recent friendly" />
      <select value={team} onChange={(e) => setTeam(e.target.value)}
        className="mb-5 rounded-md border border-border bg-surface2 px-3 py-2 text-sm">
        {names.map((t) => <option key={t}>{t}</option>)}
      </select>

      {lineup.loading && <Spinner />}
      {lineup.error && <ApiError msg={lineup.error} />}
      {lineup.data && lineup.data.length > 0 && (
        <div className="wc-card overflow-hidden">
          <div className="flex items-center gap-3 bg-surface2 px-4 py-3">
            <Flag src={teamFlag} alt={team} size={28} />
            <span className="font-display text-lg font-bold">{team}</span>
            {formation && <span className="wc-chip">{formation}</span>}
          </div>
          <ul className="divide-y divide-border">
            {lineup.data.map((p, i) => (
              <li key={i} className="flex items-center gap-3 px-4 py-2">
                <span className="w-8 text-center font-display text-muted">{p.shirt_number ?? "–"}</span>
                {p.photo_url
                  ? <Image src={p.photo_url} alt={p.player_name} width={30} height={30} unoptimized className="rounded-full" />
                  : <div className="h-[30px] w-[30px] rounded-full bg-surface2" />}
                <span className="w-12 text-xs uppercase text-accent">{p.position}</span>
                <span className="flex-1 font-semibold">{p.player_name}</span>
                <span className="text-sm text-muted">{p.club}</span>
                <span className="w-20 text-right text-sm">
                  {p.market_value_eur ? `€${(p.market_value_eur / 1e6).toFixed(0)}m` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
