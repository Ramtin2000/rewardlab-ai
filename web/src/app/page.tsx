import { Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricChart } from "@/components/metric-chart";
import { PageHeader } from "@/components/page-header";
import { RunsTable } from "@/components/runs-table";
import { StatTile } from "@/components/stat-tile";
import { getRuns } from "@/lib/data";
import { latest, metricSeries, num, pct } from "@/lib/format";
import type { CheckpointMetrics, Run } from "@/lib/types";

function aggregate(runs: Run[], key: keyof Omit<CheckpointMetrics, "step" | "episodes">) {
  const points = runs.map(latest);
  const episodes = points.reduce((n, c) => n + c.episodes, 0);
  const mean = points.reduce((sum, c) => sum + c[key] * c.episodes, 0) / episodes;
  const values = points.map((c) => c[key]);
  return { mean, min: Math.min(...values), max: Math.max(...values), episodes };
}

async function Overview() {
  const runs = await getRuns();
  if (runs.length === 0) {
    return <p className="text-sm text-muted-foreground">No runs yet. Train or evaluate a model to see results here.</p>;
  }

  const reward = aggregate(runs, "mean_proxy_reward");
  const aligned = aggregate(runs, "mean_aligned_reward");
  const success = aggregate(runs, "verified_success");
  const hack = aggregate(runs, "hack_rate");
  const trained = runs.filter((r) => r.kind === "trained").length;
  const range = (a: { min: number; max: number }, f: (v: number) => string) =>
    runs.length === 1 ? "single run" : `${f(a.min)} – ${f(a.max)} across runs`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatTile label="Experiments" value={String(runs.length)} hint={`${trained} trained · ${runs.length - trained} baseline`} />
        <StatTile label="Mean proxy reward" value={pct(reward.mean)} hint={range(reward, pct)} />
        <StatTile label="Mean aligned reward" value={num(aligned.mean)} hint={range(aligned, num)} />
        <StatTile label="Verified success" value={pct(success.mean)} hint={range(success, pct)} />
        <StatTile label="Hack rate" value={pct(hack.mean)} hint={range(hack, pct)} />
      </div>
      <p className="-mt-3 text-xs text-muted-foreground">
        Latest checkpoint of each run, weighted by {reward.episodes.toLocaleString()} evaluated episodes.
      </p>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Proxy reward</CardTitle>
            <CardDescription>What the flawed reward says: share of tickets closed.</CardDescription>
          </CardHeader>
          <CardContent>
            <MetricChart {...metricSeries(runs, "mean_proxy_reward")} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Verified success</CardTitle>
            <CardDescription>What the independent verifier says actually got done.</CardDescription>
          </CardHeader>
          <CardContent>
            <MetricChart {...metricSeries(runs, "verified_success")} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent runs</CardTitle>
        </CardHeader>
        <CardContent>
          <RunsTable runs={[...runs].sort((a, b) => b.created_at.localeCompare(a.created_at))} />
        </CardContent>
      </Card>
    </div>
  );
}

export default function Page() {
  return (
    <>
      <PageHeader
        title="Overview"
        description="One support agent, five tools, two reward functions. Watch where reward and real success diverge."
      />
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>
        <Overview />
      </Suspense>
    </>
  );
}
