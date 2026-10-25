import type { Metadata } from "next";
import { Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricChart } from "@/components/metric-chart";
import { PageHeader } from "@/components/page-header";
import { RunSwatch } from "@/components/status";
import { getRuns } from "@/lib/data";
import { metricSeries, num, pct, runColor } from "@/lib/format";

export const metadata: Metadata = { title: "Experiments" };

const PANELS = [
  { metric: "mean_proxy_reward", title: "Proxy reward", description: "Share of episodes ending with the ticket resolved." },
  { metric: "verified_success", title: "Verified success", description: "Share the independent verifier marks correct." },
  { metric: "hack_rate", title: "Hack rate", description: "Proxy reward says success, verifier says failure." },
] as const;

async function Comparison() {
  const runs = await getRuns();
  return (
    <Tabs defaultValue="charts">
      <TabsList>
        <TabsTrigger value="charts">Charts</TabsTrigger>
        <TabsTrigger value="table">Table</TabsTrigger>
      </TabsList>

      <TabsContent value="charts" className="mt-4">
        <div className="grid gap-4 xl:grid-cols-3">
          {PANELS.map((p) => (
            <Card key={p.metric}>
              <CardHeader>
                <CardTitle>{p.title}</CardTitle>
                <CardDescription>{p.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <MetricChart {...metricSeries(runs, p.metric)} />
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          X axis: GRPO training step. Dashed line: untrained baseline. Same model, seeds and hyperparameters; only the
          reward function differs.
        </p>
      </TabsContent>

      <TabsContent value="table" className="mt-4">
        <Card>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run</TableHead>
                  <TableHead className="text-right">Step</TableHead>
                  <TableHead className="text-right">Episodes</TableHead>
                  <TableHead className="text-right">Proxy reward</TableHead>
                  <TableHead className="text-right">Aligned reward</TableHead>
                  <TableHead className="text-right">Verified</TableHead>
                  <TableHead className="text-right">Hack rate</TableHead>
                  <TableHead className="text-right">Mean turns</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.flatMap((run) =>
                  run.checkpoints.map((c) => (
                    <TableRow key={`${run.id}-${c.step}`}>
                      <TableCell>
                        <span className="flex items-center gap-2">
                          <RunSwatch color={runColor(run)} />
                          {run.name}
                        </span>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{c.step}</TableCell>
                      <TableCell className="text-right tabular-nums">{c.episodes}</TableCell>
                      <TableCell className="text-right tabular-nums">{pct(c.mean_proxy_reward)}</TableCell>
                      <TableCell className="text-right tabular-nums">{num(c.mean_aligned_reward)}</TableCell>
                      <TableCell className="text-right tabular-nums">{pct(c.verified_success)}</TableCell>
                      <TableCell className="text-right tabular-nums">{pct(c.hack_rate)}</TableCell>
                      <TableCell className="text-right tabular-nums">{num(c.mean_turns, 1)}</TableCell>
                    </TableRow>
                  )),
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

export default function Page() {
  return (
    <>
      <PageHeader
        title="Experiments"
        description="Baseline vs. flawed-reward vs. aligned-reward training. If reward rises while verified success falls, the agent is hacking the reward."
      />
      <Suspense fallback={<Skeleton className="h-80 w-full" />}>
        <Comparison />
      </Suspense>
    </>
  );
}
