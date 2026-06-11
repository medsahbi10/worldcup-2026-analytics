"use client";

import Image from "next/image";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, PageTitle, Spinner, ApiError } from "@/components/ui";

const POS = ["All", "GK", "DF", "MF", "FW"];

export default function PlayersPage() {
  const teams = useApi(() => api.teams(), []);
  const [team, setTeam] = useState("All");
  const [pos, setPos] = useState("All");
  const players = useApi(
    () => api.players(team === "All" ? undefined : team, pos === "All" ? undefined : pos),
    [team, pos],
  );
  const teamNames = ["All", ...(teams.data?.map((t) => t.team_country).sort() ?? [])];

  return (
    <div>
      <PageTitle title="Players" sub="~1,255 squad players · photo, club, age & market value (Transfermarkt)" />
      <div className="mb-5 flex flex-wrap gap-3">
        <select value={team} onChange={(e) => setTeam(e.target.value)}
          className="rounded-md border border-border bg-surface2 px-3 py-2 text-sm">
          {teamNames.map((t) => <option key={t}>{t}</option>)}
        </select>
        <div className="flex gap-1">
          {POS.map((p) => (
            <button key={p} onClick={() => setPos(p)}
              className={`rounded-md px-3 py-2 text-sm font-display font-bold uppercase ${pos === p ? "bg-accent text-[#08163a]" : "bg-surface2 text-muted"}`}>
              {p}
            </button>
          ))}
        </div>
      </div>
      {players.loading && <Spinner />}
      {players.error && <ApiError msg={players.error} />}
      {players.data && (
        <div className="wc-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-surface2 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-3 py-2"></th>
                <th className="px-3 py-2">Player</th>
                <th className="px-3 py-2">Team</th>
                <th className="px-2 py-2">Pos</th>
                <th className="px-3 py-2">Club</th>
                <th className="px-2 py-2 text-right">Age</th>
                <th className="px-2 py-2 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {players.data.slice(0, 300).map((p) => (
                <tr key={p.player_id} className="border-t border-border">
                  <td className="px-3 py-1.5">
                    {p.photo_url
                      ? <Image src={p.photo_url} alt={p.player_name} width={28} height={28} unoptimized className="rounded-full" />
                      : <div className="h-7 w-7 rounded-full bg-surface2" />}
                  </td>
                  <td className="px-3 py-1.5 font-semibold">{p.player_name}</td>
                  <td className="px-3 py-1.5">
                    <span className="flex items-center gap-1.5 text-muted">
                      <Flag src={p.flag} alt={p.team_country} size={16} /> {p.team_country}
                    </span>
                  </td>
                  <td className="px-2 py-1.5 text-muted">{p.position}</td>
                  <td className="px-3 py-1.5 text-muted">{p.club}</td>
                  <td className="px-2 py-1.5 text-right text-muted">{p.age}</td>
                  <td className="px-2 py-1.5 text-right font-semibold">
                    {p.market_value_eur ? `€${(p.market_value_eur / 1e6).toFixed(1)}m` : "—"}
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
