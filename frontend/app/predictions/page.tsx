"use client";

import { useEffect, useState } from "react";
import { api, type MatchPrediction } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { Flag, PageTitle, ProbBar, Spinner, ApiError } from "@/components/ui";

export default function PredictionsPage() {
  const preds = useApi(() => api.predictions(), []);

  return (
    <div>
      <PageTitle title="Predictions" sub="20,000 Monte-Carlo simulations · Dixon-Coles + squad-value model" />

      <Predictor />

      <h2 className="mb-3 mt-10 text-xl font-bold uppercase">Title odds</h2>
      {preds.loading && <Spinner />}
      {preds.error && <ApiError msg={preds.error} />}
      {preds.data && (
        <div className="wc-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-surface2 text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-2">#</th>
                <th className="px-4 py-2">Team</th>
                <th className="px-3 py-2 text-right">Advance</th>
                <th className="px-3 py-2 text-right">QF</th>
                <th className="px-3 py-2 text-right">SF</th>
                <th className="px-3 py-2 text-right">Final</th>
                <th className="px-3 py-2 text-right">Champion</th>
              </tr>
            </thead>
            <tbody>
              {preds.data.slice(0, 24).map((t, i) => (
                <tr key={t.team_country} className="border-t border-border">
                  <td className="px-4 py-2 text-muted">{i + 1}</td>
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-2 font-semibold">
                      <Flag src={t.flag} alt={t.team_country} /> {t.team_country}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right text-muted">{(t.p_advance * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-right text-muted">{(t.p_qf * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-right text-muted">{(t.p_sf * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-right">{(t.p_final * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-right font-display font-bold text-accent">
                    {(t.p_champion * 100).toFixed(1)}%
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

function Predictor() {
  const teams = useApi(() => api.strengths(), []);
  const [home, setHome] = useState("Argentina");
  const [away, setAway] = useState("France");
  const [result, setResult] = useState<MatchPrediction | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (home === away) return;
    api.predict(home, away).then(setResult).catch((e) => setErr(String(e)));
  }, [home, away]);

  const names = teams.data?.map((t) => t.team_country).sort() ?? [];

  return (
    <section className="wc-card p-5">
      <h2 className="mb-4 text-xl font-bold uppercase">Head-to-head predictor</h2>
      <div className="grid grid-cols-2 gap-3">
        <Select label="Team A" value={home} onChange={setHome} options={names} />
        <Select label="Team B" value={away} onChange={setAway} options={names} />
      </div>
      {err && <p className="mt-3 text-sm text-primary">{err}</p>}
      {result && home !== away && (
        <div className="mt-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2 text-lg font-bold">
              <Flag src={result.home_flag} alt={home} size={28} /> {home}
            </span>
            <span className="text-sm text-muted">
              xG {result.xg_home.toFixed(2)} – {result.xg_away.toFixed(2)}
            </span>
            <span className="flex items-center gap-2 text-lg font-bold">
              {away} <Flag src={result.away_flag} alt={away} size={28} />
            </span>
          </div>
          <ProbBar h={result.p_home} d={result.p_draw} a={result.p_away} />
          <div className="mt-1 flex justify-between text-xs text-muted">
            <span>{home} win</span><span>draw</span><span>{away} win</span>
          </div>
        </div>
      )}
    </section>
  );
}

function Select({ label, value, onChange, options }: {
  label: string; value: string; onChange: (v: string) => void; options: string[];
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs uppercase text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-border bg-surface2 px-3 py-2 text-text"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </label>
  );
}
