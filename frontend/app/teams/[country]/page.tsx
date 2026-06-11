"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { StatCard, ScoreCard, Spinner, ApiError } from "@/components/ui";
import { FlagCard, GroupBadge, Jersey } from "@/components/brand";
import { wcHistory } from "@/lib/wcHistory";

/* circular photo that falls back to a neutral circle */
function PlayerPhoto({ src, alt, size }: { src: string | null; alt: string; size: number }) {
  const [failed, setFailed] = useState(false);
  const circle = (
    <span
      className="grid place-items-center rounded-full bg-surface2 font-display font-bold text-muted"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {alt.charAt(0)}
    </span>
  );
  if (!src || failed) return circle;
  return (
    <Image
      src={src}
      alt={alt}
      width={size}
      height={size}
      unoptimized
      className="rounded-full object-cover"
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  );
}

export default function TeamDetailPage() {
  const params = useParams<{ country: string }>();
  const country = decodeURIComponent(params.country);

  const teams = useApi(() => api.teams(), []);
  const groups = useApi(() => api.groups(), []);
  const players = useApi(() => api.players(country), [country]);
  const predictions = useApi(() => api.predictions(), []);
  const fixtures = useApi(() => api.fixtures(undefined, country), [country]);

  const loading = teams.loading || groups.loading;
  const error = teams.error || groups.error;

  const team = (teams.data ?? []).find((t) => t.team_country === country);

  const groupLetter = groups.data
    ? Object.entries(groups.data).find(([, rows]) =>
        rows.some((r) => r.team_country === country),
      )?.[0]
    : undefined;

  const hist = wcHistory(country);

  const champion = (predictions.data ?? []).find((p) => p.team_country === country);

  const playerList = players.data ?? [];
  const star = playerList[0];
  const rest = playerList.slice(1, 7);

  return (
    <div>
      <Link href="/teams" className="mb-4 inline-block text-sm text-muted hover:text-accent">
        ← Back to teams
      </Link>

      {loading && <Spinner />}
      {error && <ApiError msg={error} />}

      {!loading && !error && !team && (
        <div className="wc-card p-6 text-sm text-muted">
          No team found for <b className="text-text">{country}</b>.
        </div>
      )}

      {team && (
        <>
          {/* Header */}
          <div className="mb-6 flex flex-wrap items-center gap-4">
            <FlagCard src={team.flag} alt={team.team_country} size={64} />
            <div>
              <h1 className="font-display text-4xl font-extrabold leading-none">{team.team_country}</h1>
              <div className="mt-2 flex items-center gap-2">
                <span className="rounded-md bg-surface2 px-2 py-0.5 text-xs font-bold uppercase tracking-wide text-muted">
                  {team.confederation ?? "—"}
                </span>
                {groupLetter && (
                  <span className="flex items-center gap-1.5 text-xs uppercase text-muted">
                    <GroupBadge letter={groupLetter} size={22} /> Group {groupLetter}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {/* Jersey board */}
            <div className="wc-board flex flex-col items-center justify-center border border-border p-6">
              <Jersey iso={team.flag_iso} flag={team.flag} alt={team.team_country} size={160} />
              <div className="mt-3 font-display text-sm font-bold uppercase tracking-wide text-white/80">
                {team.team_country}
              </div>
            </div>

            {/* Insight stat cards */}
            <div className="grid grid-cols-2 gap-3 lg:col-span-2 sm:grid-cols-3">
              <StatCard
                label="WC participations"
                value={hist.appearances > 0 ? String(hist.appearances) : "Debut"}
                hint={hist.appearances > 0 ? "finals tournaments" : "first appearance"}
              />
              <StatCard label="Best achievement" value={hist.best} hint={hist.bestYear} />
              <StatCard label="Coach" value={team.manager ?? "—"} />
              <StatCard
                label="Squad value"
                value={team.total_value_m != null ? `€${Math.round(team.total_value_m)}m` : "—"}
              />
              <StatCard
                label="Avg age"
                value={team.avg_age != null ? String(team.avg_age) : "—"}
                hint={team.squad_size != null ? `${team.squad_size} players` : undefined}
              />
              <StatCard
                label="Model strength"
                value={team.strength != null ? team.strength.toFixed(2) : "—"}
                hint={team.elo != null ? `Elo ${Math.round(team.elo)}` : undefined}
              />
              <StatCard
                label="Title odds"
                value={champion ? `${(champion.p_champion * 100).toFixed(1)}%` : "—"}
                hint="chance to win the cup"
              />
            </div>
          </div>

          {/* Star player / squad */}
          <h2 className="mb-3 mt-8 font-display text-2xl font-extrabold">Squad</h2>
          {players.loading && <Spinner />}
          {players.error && <ApiError msg={players.error} />}
          {players.data && playerList.length === 0 && (
            <div className="wc-card p-4 text-sm text-muted">No squad data available.</div>
          )}
          {star && (
            <div className="grid gap-5 lg:grid-cols-3">
              {/* Star player */}
              <div className="wc-card flex items-center gap-4 p-5">
                <PlayerPhoto src={star.photo_url} alt={star.player_name} size={88} />
                <div className="min-w-0">
                  <div className="text-[11px] uppercase tracking-wide text-muted">Highest market value</div>
                  <div className="font-display text-xl font-extrabold leading-tight">{star.player_name}</div>
                  <div className="mt-0.5 truncate text-sm text-muted">
                    {[star.position, star.club].filter(Boolean).join(" · ") || "—"}
                  </div>
                  {star.market_value_eur != null && (
                    <div className="mt-2 font-display text-3xl font-extrabold text-accent">
                      €{(star.market_value_eur / 1e6).toFixed(1)}m
                    </div>
                  )}
                </div>
              </div>

              {/* Next players */}
              {rest.length > 0 && (
                <div className="wc-card p-2 lg:col-span-2">
                  <table className="w-full text-sm">
                    <thead className="text-[11px] uppercase text-muted">
                      <tr>
                        <th className="px-3 py-1.5 text-left">Player</th>
                        <th className="px-2 py-1.5 text-left">Pos</th>
                        <th className="px-2 py-1.5 text-left">Club</th>
                        <th className="px-3 py-1.5 text-right">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rest.map((p) => (
                        <tr key={p.player_id} className="border-t border-border">
                          <td className="px-3 py-1.5 font-semibold">{p.player_name}</td>
                          <td className="px-2 py-1.5 text-muted">{p.position ?? "—"}</td>
                          <td className="px-2 py-1.5 text-muted">{p.club ?? "—"}</td>
                          <td className="px-3 py-1.5 text-right font-display font-bold text-accent">
                            {p.market_value_eur != null ? `€${(p.market_value_eur / 1e6).toFixed(1)}m` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Fixtures */}
          <h2 className="mb-3 mt-8 font-display text-2xl font-extrabold">Group-stage fixtures</h2>
          {fixtures.loading && <Spinner />}
          {fixtures.error && <ApiError msg={fixtures.error} />}
          {fixtures.data && fixtures.data.length === 0 && (
            <div className="wc-card p-4 text-sm text-muted">No fixtures found.</div>
          )}
          {fixtures.data && fixtures.data.length > 0 && (
            <div className="space-y-2">
              {fixtures.data.map((f, i) => (
                <ScoreCard
                  key={i}
                  home={f.home_team}
                  away={f.away_team}
                  homeFlag={f.home_flag}
                  awayFlag={f.away_flag}
                  homeScore={f.status === "played" ? f.home_score : null}
                  awayScore={f.status === "played" ? f.away_score : null}
                  kickoff={f.kickoff_local}
                  group={f.group_letter}
                  venue={f.venue}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
