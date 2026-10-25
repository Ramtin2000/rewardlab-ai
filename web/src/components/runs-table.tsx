import Link from "next/link";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RunSwatch } from "@/components/status";
import { latest, num, pct, runColor, shortDate } from "@/lib/format";
import { REWARD_FNS, type Run } from "@/lib/types";

export function RunsTable({ runs }: { runs: Run[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Run</TableHead>
          <TableHead>Reward fn</TableHead>
          <TableHead className="text-right">Step</TableHead>
          <TableHead className="text-right">Proxy reward</TableHead>
          <TableHead className="text-right">Aligned reward</TableHead>
          <TableHead className="text-right">Verified</TableHead>
          <TableHead className="text-right">Hack rate</TableHead>
          <TableHead className="text-right">Created</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {runs.map((run) => {
          const c = latest(run);
          return (
            <TableRow key={run.id}>
              <TableCell>
                <Link href={`/trajectories?run_id=${run.id}`} className="flex items-center gap-2 font-medium hover:underline">
                  <RunSwatch color={runColor(run)} />
                  {run.name}
                </Link>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {REWARD_FNS.find((r) => r.id === run.reward_fn)?.label ?? "—"}
              </TableCell>
              <TableCell className="text-right tabular-nums">{c.step}</TableCell>
              <TableCell className="text-right tabular-nums">{pct(c.mean_proxy_reward)}</TableCell>
              <TableCell className="text-right tabular-nums">{num(c.mean_aligned_reward)}</TableCell>
              <TableCell className="text-right tabular-nums">{pct(c.verified_success)}</TableCell>
              <TableCell className="text-right tabular-nums">{pct(c.hack_rate)}</TableCell>
              <TableCell className="text-right text-muted-foreground">{shortDate(run.created_at)}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
