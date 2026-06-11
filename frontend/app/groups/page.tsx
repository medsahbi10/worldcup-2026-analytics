"use client";

import { api, type Standing } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { PageTitle, Spinner, ApiError } from "@/components/ui";
import { GroupCard } from "@/components/GroupCard";

export default function GroupsPage() {
  const groups = useApi(() => api.groups(), []);
  const preds = useApi(() => api.predictions(), []);
  const predOf = new Map((preds.data ?? []).map((p) => [p.team_country, p]));
  const sortTeams = (rows: Standing[]) => [...rows].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
  const entries = Object.entries(groups.data ?? {}).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div>
      <PageTitle title="Groups" sub="The 2026 group-stage draw — click a team for its insights." />
      {groups.loading && <Spinner />}
      {groups.error && <ApiError msg={groups.error} />}
      {groups.data && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {entries.map(([l, rows]) => (
            <GroupCard key={l} letter={l} teams={sortTeams(rows)} predOf={predOf} />
          ))}
        </div>
      )}
    </div>
  );
}
