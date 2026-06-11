"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { PageTitle, Spinner, ApiError } from "@/components/ui";
import { RankingList, type RankRow } from "@/components/RankingList";

const METRICS = [
  { key: "elo", label: "World (Elo)" },
  { key: "champion", label: "Champion odds" },
  { key: "value", label: "Squad value" },
  { key: "attack", label: "Attack" },
  { key: "defense", label: "Defense" },
] as const;

type MetricKey = (typeof METRICS)[number]["key"];

const SUB: Record<MetricKey, string> = {
  elo: "Overall strength — Elo rating.",
  champion: "Model probability of lifting the trophy.",
  value: "Total squad market value.",
  attack: "Model attacking rating — the most lethal sides.",
  defense: "Model defensive rating — the toughest to break down.",
};

export default function RankingPage() {
  const teams = useApi(() => api.teams(), []);
  const preds = useApi(() => api.predictions(), []);
  const strengths = useApi(() => api.strengths(), []);
  const [metric, setMetric] = useState<MetricKey>("elo");

  const loading = teams.loading || preds.loading || strengths.loading;
  const error = teams.error || preds.error || strengths.error;

  let rows: RankRow[] = [];
  if (metric === "elo") {
    rows = (teams.data ?? []).filter((t) => t.elo != null)
      .sort((a, b) => (b.elo ?? 0) - (a.elo ?? 0))
      .map((t) => ({ team_country: t.team_country, flag: t.flag, value: Math.round(t.elo ?? 0) }));
  } else if (metric === "champion") {
    rows = [...(preds.data ?? [])].sort((a, b) => b.p_champion - a.p_champion)
      .map((p) => ({ team_country: p.team_country, flag: p.flag, value: `${(p.p_champion * 100).toFixed(1)}%` }));
  } else if (metric === "value") {
    rows = (teams.data ?? []).filter((t) => t.total_value_m != null)
      .sort((a, b) => (b.total_value_m ?? 0) - (a.total_value_m ?? 0))
      .map((t) => ({ team_country: t.team_country, flag: t.flag, value: `€${Math.round(t.total_value_m ?? 0)}m` }));
  } else if (metric === "attack") {
    rows = [...(strengths.data ?? [])].sort((a, b) => b.attack - a.attack)
      .map((s) => ({ team_country: s.team_country, flag: s.flag, value: s.attack.toFixed(2) }));
  } else {
    rows = [...(strengths.data ?? [])].sort((a, b) => b.defense - a.defense)
      .map((s) => ({ team_country: s.team_country, flag: s.flag, value: s.defense.toFixed(2) }));
  }

  return (
    <div>
      <PageTitle title="World Ranking" sub={SUB[metric]} />
      <div className="mb-5 flex flex-wrap gap-1.5">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setMetric(m.key)}
            className={`rounded-md px-3 py-1 font-display text-sm font-bold uppercase ${
              metric === m.key ? "bg-accent text-[#0f1014]" : "bg-surface2 text-muted hover:text-text"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>
      {loading && <Spinner />}
      {error && <ApiError msg={error} />}
      {!loading && !error && (
        <div className="mx-auto max-w-[760px]">
          <RankingList rows={rows} />
        </div>
      )}
    </div>
  );
}
