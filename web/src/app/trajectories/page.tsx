import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PageHeader } from "@/components/page-header";
import { HackFlag, RunSwatch, VerifierStatus } from "@/components/status";
import { getRuns, getTrajectories, type TrajectoryFilters } from "@/lib/data";
import { num, runColor, scenarioLabel } from "@/lib/format";
import { cn } from "@/lib/utils";
import { SCENARIOS, type Scenario } from "@/lib/types";

export const metadata: Metadata = { title: "Trajectories" };

type Params = Record<string, string | undefined>;

function parseFilters(sp: Params): TrajectoryFilters {
  return {
    run_id: sp.run_id || undefined,
    scenario: SCENARIOS.some((s) => s.id === sp.scenario) ? (sp.scenario as Scenario) : undefined,
    verifier: sp.verifier === "passed" || sp.verifier === "failed" ? sp.verifier : undefined,
    hack: sp.hack === "1" ? true : undefined,
  };
}

function FilterGroup({ label, param, options, current }: {
  label: string;
  param: string;
  options: { value: string | undefined; label: string }[];
  current: Params;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="mr-1 text-xs text-muted-foreground">{label}</span>
      {options.map((o) => {
        const next = new URLSearchParams(Object.entries({ ...current, [param]: o.value }).filter(([, v]) => v) as [string, string][]);
        const active = (current[param] || undefined) === o.value;
        return (
          <Link
            key={o.label}
            href={`/trajectories${next.size ? `?${next}` : ""}`}
            className={cn(
              "rounded-md border px-2 py-0.5 text-xs transition-colors hover:bg-muted",
              active && "border-foreground/30 bg-muted font-medium",
            )}
          >
            {o.label}
          </Link>
        );
      })}
    </div>
  );
}

async function TrajectoryList({ searchParams }: { searchParams: Promise<Params> }) {
  const sp = await searchParams;
  const [runs, rows] = await Promise.all([getRuns(), getTrajectories(parseFilters(sp))]);
  const runById = new Map(runs.map((r) => [r.id, r]));

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2">
        <FilterGroup
          label="Run"
          param="run_id"
          current={sp}
          options={[{ value: undefined, label: "All" }, ...runs.map((r) => ({ value: r.id, label: r.name }))]}
        />
        <FilterGroup
          label="Scenario"
          param="scenario"
          current={sp}
          options={[{ value: undefined, label: "All" }, ...SCENARIOS.map((s) => ({ value: s.id, label: s.label }))]}
        />
        <div className="flex flex-wrap gap-4">
          <FilterGroup
            label="Verifier"
            param="verifier"
            current={sp}
            options={[
              { value: undefined, label: "All" },
              { value: "passed", label: "Passed" },
              { value: "failed", label: "Failed" },
            ]}
          />
          <FilterGroup
            label="Hacks"
            param="hack"
            current={sp}
            options={[
              { value: undefined, label: "All" },
              { value: "1", label: "Only hacks" },
            ]}
          />
        </div>
      </div>

      <Card>
        <CardContent>
          {rows.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No trajectories match these filters.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Episode</TableHead>
                  <TableHead>Run</TableHead>
                  <TableHead className="text-right">Step</TableHead>
                  <TableHead>Scenario</TableHead>
                  <TableHead className="text-right">Turns</TableHead>
                  <TableHead className="text-right">Proxy reward</TableHead>
                  <TableHead>Verifier</TableHead>
                  <TableHead>Hack</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((t) => {
                  const run = runById.get(t.run_id);
                  return (
                    <TableRow key={t.episode_id}>
                      <TableCell>
                        <Link href={`/trajectories/${t.episode_id}`} className="font-mono text-xs hover:underline">
                          {t.episode_id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <span className="flex items-center gap-2">
                          {run && <RunSwatch color={runColor(run)} />}
                          {run?.name ?? t.run_id}
                        </span>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{t.checkpoint_step}</TableCell>
                      <TableCell className="text-muted-foreground">{scenarioLabel(t.scenario)}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {t.num_turns}
                        {t.terminated_by === "turn_limit" && <span className="text-muted-foreground"> (limit)</span>}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{num(t.proxy_reward)}</TableCell>
                      <TableCell>
                        <VerifierStatus passed={t.verifier_passed} />
                      </TableCell>
                      <TableCell>
                        <HackFlag isHack={t.is_hack} />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function Page(props: PageProps<"/trajectories">) {
  return (
    <>
      <PageHeader
        title="Trajectories"
        description="Every logged episode. Open one to step through it turn by turn."
      />
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>
        <TrajectoryList searchParams={props.searchParams as Promise<Params>} />
      </Suspense>
    </>
  );
}
