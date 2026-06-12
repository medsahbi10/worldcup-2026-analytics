"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Fixture, type FormResult } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { StatCard, Spinner, ApiError } from "@/components/ui";
import { TrophyMark, FlagCard } from "@/components/brand";
import { MatchCard } from "@/components/MatchCard";
import { RankingList } from "@/components/RankingList";
import { GroupCard } from "@/components/GroupCard";
import { HBarChart, DumbbellChart } from "@/components/charts";
import { darkHorses, groupOfDeath, lethalAttack, bestDefense, starPower } from "@/lib/insights";

function Head({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-4">
      <h2 className="font-display text-2xl font-extrabold">{title}</h2>
      {sub && <p className="mt-0.5 text-sm text-muted normal-case">{sub}</p>}
    </div>
  );
}

function FormPills({ results }: { results: FormResult[] }) {
  return (
    <div className="flex gap-1">
      {results.slice(0, 5).map((r, i) => (
        <span
          key={i}
          title={`${r.result} ${r.gf}–${r.ga} vs ${r.opponent}`}
          className={`grid h-6 w-6 place-items-center rounded text-[11px] font-bold ${
            r.result === "W" ? "bg-win text-[#04240f]" : r.result === "D" ? "bg-surface2 text-muted" : "bg-loss text-white"
          }`}
        >
          {r.result}
        </span>
      ))}
    </div>
  );
}

const fx = (f: Fixture) => ({
  home: f.home_team, away: f.away_team, homeFlag: f.home_flag, awayFlag: f.away_flag,
  group: f.group_letter, matchDate: f.match_date, kickoff: f.kickoff_local, venue: f.venue,
  homeScore: f.home_score, awayScore: f.away_score, status: f.status,
});

/** Finished-match results: same MatchCard template (score in the box), 3 shown,
 *  expandable. Each card opens the match-detail modal in result mode. */
function ResultsSection({ played }: { played: Fixture[] }) {
  const [expanded, setExpanded] = useState(false);
  const shown = expanded ? played : played.slice(0, 3);
  return (
    <section>
      <Head title="Results" sub="Finished matches — click any for the result breakdown vs our prediction." />
      {played.length === 0 ? (
        <div className="wc-card p-6 text-sm text-muted">No results yet — the group stage has just kicked off.</div>
      ) : (
        <>
          <div className="space-y-4">
            {shown.map((m, i) => <MatchCard key={i} {...fx(m)} />)}
          </div>
          {played.length > 3 && (
            <button
              onClick={() => setExpanded((v) => !v)}
              className="mt-3 font-display text-sm font-bold uppercase text-accent hover:underline"
            >
              {expanded ? "Show less" : `Show all ${played.length} results`}
            </button>
          )}
        </>
      )}
    </section>
  );
}

export default function Home() {
  const fixtures = useApi(() => api.fixtures(), []);
  const teams = useApi(() => api.teams(), []);
  const preds = useApi(() => api.predictions(), []);
  const strengths = useApi(() => api.strengths(), []);
  const players = useApi(() => api.players(), []);
  const groups = useApi(() => api.groups(), []);
  const form = useApi(() => api.form(), []);

  const upcoming = (fixtures.data ?? []).filter((f) => f.status !== "played");
  const nextMatch = upcoming[0] ?? (fixtures.data ?? [])[0] ?? null;
  const valOf = new Map((teams.data ?? []).map((t) => [t.team_country, t.total_value_m ?? 0]));
  const mustWatch = [...upcoming]
    .sort((a, b) => (valOf.get(b.home_team)! + valOf.get(b.away_team)!) - (valOf.get(a.home_team)! + valOf.get(a.away_team)!))
    .filter((m) => m !== nextMatch)
    .slice(0, 3);
  const results = [...(fixtures.data ?? [])]
    .filter((f) => f.status === "played")
    .sort((a, b) => b.match_date.localeCompare(a.match_date) || (b.kickoff_local ?? "").localeCompare(a.kickoff_local ?? ""));

  const titleRace = [...(preds.data ?? [])].sort((a, b) => b.p_champion - a.p_champion).slice(0, 10)
    .map((p) => ({ team_country: p.team_country, flag: p.flag, value: `${(p.p_champion * 100).toFixed(1)}%` }));

  // Punching above weight: expected (squad-value rank) vs current (Elo rank).
  const withBoth = (teams.data ?? []).filter((t) => t.elo != null && t.total_value_m != null);
  const eloRank = new Map([...withBoth].sort((a, b) => (b.elo ?? 0) - (a.elo ?? 0)).map((t, i) => [t.team_country, i + 1]));
  const valRank = new Map([...withBoth].sort((a, b) => (b.total_value_m ?? 0) - (a.total_value_m ?? 0)).map((t, i) => [t.team_country, i + 1]));
  const dumbbell = withBoth
    .map((t) => ({ label: t.team_country, flag: t.flag, a: valRank.get(t.team_country)!, b: eloRank.get(t.team_country)! }))
    .sort((x, y) => (y.a - y.b) - (x.a - x.b))
    .slice(0, 8);

  const attack = lethalAttack(strengths.data ?? []).map((s) => ({ label: s.team_country, value: s.attack, flag: s.flag }));
  const defense = bestDefense(strengths.data ?? []).map((s) => ({ label: s.team_country, value: s.defense, flag: s.flag }));
  const stars = starPower(players.data ?? []).map((s) => ({ label: s.team, value: s.count, flag: s.top.flag }));
  const horses = darkHorses(preds.data ?? []).map((p) => ({ label: p.team_country, value: p.p_qf * 100, flag: p.flag }));
  const death = groupOfDeath(groups.data ?? {}, teams.data ?? []);
  const predOf = new Map((preds.data ?? []).map((p) => [p.team_country, p]));
  const formTeams = [...(preds.data ?? [])].sort((a, b) => b.p_champion - a.p_champion).slice(0, 8);

  return (
    <div className="space-y-12">
      {/* HERO */}
      <div className="wc-board overflow-hidden border border-border">
        <div className="flex flex-col items-start gap-5 p-6 md:flex-row md:items-center md:p-8">
          <div className="flex-1">
            <h1 className="font-display text-3xl font-extrabold leading-[1.05] md:text-4xl">
              FIFA WORLD CUP 2026 <span className="text-gold">Analytics</span>
            </h1>
            <p className="mt-2 max-w-xl text-sm text-white/85 normal-case">
              48 teams · 104 matches. Forecasts, rankings and insights powered by a Dixon-Coles model.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link href="/groups" className="rounded-md bg-accent px-4 py-2 text-sm font-bold uppercase text-[#0f1014]">Explore groups →</Link>
              <Link href="/bracket" className="rounded-md border border-white/30 px-4 py-2 text-sm font-bold uppercase text-white hover:bg-white/10">Knockout bracket</Link>
            </div>
          </div>
          <TrophyMark size={96} />
        </div>
      </div>

      {/* NEXT MATCH */}
      <section>
        <Head title="Next match" sub="The next kickoff — click for the full comparison." />
        {fixtures.loading && <Spinner />}
        {fixtures.error && <ApiError msg={fixtures.error} />}
        {nextMatch && <MatchCard {...fx(nextMatch)} />}
      </section>

      {/* RESULTS (between next match and must-watch) */}
      {fixtures.data && <ResultsSection played={results} />}

      {/* MUST-WATCH */}
      <section>
        <Head title="Must-watch fixtures" sub="The biggest upcoming clashes by squad value." />
        <div className="space-y-4">
          {mustWatch.map((m, i) => <MatchCard key={i} {...fx(m)} />)}
        </div>
      </section>

      {/* TITLE RACE | LETHAL ATTACKS + MEANEST DEFENSES */}
      <section>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <Head title="Title race" sub="Odds to win the cup." />
            {preds.loading && <Spinner />}
            {preds.data && <RankingList rows={titleRace} size={34} />}
          </div>
          <div className="flex flex-col justify-center gap-6 lg:col-span-2">
            <div>
              <Head title="Lethal attacks" sub="Model attacking rating." />
              {strengths.data && <div className="wc-card p-5"><HBarChart data={attack} color="var(--color-loss)" format={(n) => n.toFixed(2)} /></div>}
            </div>
            <div>
              <Head title="Meanest defenses" sub="Model defensive rating." />
              {strengths.data && <div className="wc-card p-5"><HBarChart data={defense} color="var(--color-win)" format={(n) => n.toFixed(2)} /></div>}
            </div>
          </div>
        </div>
      </section>

      {/* PUNCHING ABOVE WEIGHT (full width — dumbbell) */}
      <section>
        <Head title="Punching above their weight" sub="Current Elo place vs the place their squad value would expect — biggest overachievers." />
        {teams.loading && <Spinner />}
        {teams.data && (
          <div className="wc-card p-5">
            <DumbbellChart data={dumbbell} max={withBoth.length || 1} aLabel="Expected (by value)" bLabel="Current (by Elo)" />
          </div>
        )}
      </section>

      {/* STAR POWER | DARK HORSES */}
      <section>
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <Head title="Star power" sub="€50m+ players per squad." />
            {players.data && <div className="wc-card p-5"><HBarChart data={stars} format={(n) => `${n}`} /></div>}
          </div>
          <div>
            <Head title="Dark horses" sub="Outsiders the model fancies to reach the QF." />
            {preds.data && <div className="wc-card p-5"><HBarChart data={horses} format={(n) => `${Math.round(n)}%`} /></div>}
          </div>
        </div>
      </section>

      {/* FORM GUIDE | GROUP OF DEATH */}
      <section>
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <Head title="Form guide" sub="Last five internationals for the favourites." />
            {(form.loading || preds.loading) && <Spinner />}
            {form.data && preds.data && (
              <div className="wc-card divide-y divide-border">
                {formTeams.map((p) => (
                  <div key={p.team_country} className="flex items-center gap-3 px-4 py-3">
                    <FlagCard src={p.flag} alt={p.team_country} size={26} />
                    <span className="flex-1 truncate font-semibold uppercase">{p.team_country}</span>
                    {form.data?.[p.team_country]?.length ? <FormPills results={form.data[p.team_country]} /> : <span className="text-xs text-muted">—</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div>
            <Head title="Group of death" sub="The toughest group by combined squad strength." />
            {groups.data && teams.data && death && (
              <GroupCard letter={death.letter} teams={death.teams} predOf={predOf} standings={false} />
            )}
          </div>
        </div>
      </section>

      {/* STATS */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Teams" value="48" />
        <StatCard label="Matches" value="104" />
        <StatCard label="Groups" value="12" />
        <StatCard label="Simulations" value="20,000" />
      </div>
    </div>
  );
}
