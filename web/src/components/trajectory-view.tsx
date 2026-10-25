import { ArrowRight, Bot, Flag, Wrench } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { HackFlag, VerifierStatus } from "@/components/status";
import { num, scenarioLabel } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Trajectory, Turn } from "@/lib/types";

function TurnRow({ turn }: { turn: Turn }) {
  const isError = "error" in turn.observation;
  return (
    <li className="relative grid grid-cols-[2rem_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className="flex size-7 items-center justify-center rounded-full border bg-card font-mono text-xs tabular-nums">
          {turn.index}
        </span>
        <span className="w-px flex-1 bg-border" />
      </div>
      <div className="min-w-0 space-y-2 pb-6">
        {turn.assistant_message && (
          <p className="flex gap-2 text-sm text-muted-foreground">
            <Bot className="mt-0.5 size-4 shrink-0" />
            <span>{turn.assistant_message}</span>
          </p>
        )}
        <div className="flex items-center gap-2 font-mono text-sm">
          <Wrench className="size-4 shrink-0 text-muted-foreground" />
          <span className="font-semibold">{turn.tool}</span>
          <span className="truncate text-muted-foreground">({JSON.stringify(turn.args)})</span>
        </div>
        <pre
          className={cn(
            "overflow-x-auto rounded-md border bg-muted/40 p-3 font-mono text-xs leading-relaxed",
            isError && "border-status-critical/40",
          )}
        >
          {JSON.stringify(turn.observation, null, 2)}
        </pre>
        {turn.state_changes.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {turn.state_changes.map((change) => (
              <Badge key={change} variant="outline" className="gap-1 font-mono text-[11px]">
                <ArrowRight className="size-3" />
                {change}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium">{children}</dd>
    </div>
  );
}

export function TrajectoryView({ trajectory: t }: { trajectory: Trajectory }) {
  const s = t.final_state;
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
      <section aria-label="Turns">
        <ol>
          {t.turns.map((turn) => (
            <TurnRow key={turn.index} turn={turn} />
          ))}
          <li className="grid grid-cols-[2rem_1fr] gap-3">
            <span className="flex size-7 items-center justify-center rounded-full border bg-card">
              <Flag className="size-3.5" />
            </span>
            <div className="space-y-1 pt-1">
              <p className="text-sm font-medium">
                {t.terminated_by === "turn_limit" ? "Turn limit reached" : "Agent finished"}
              </p>
              {t.final_message && <p className="text-sm text-muted-foreground">“{t.final_message}”</p>}
            </div>
          </li>
        </ol>
      </section>

      <aside className="space-y-4">
        <Card size="sm">
          <CardHeader>
            <CardTitle>Evaluation</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <Row label="Proxy reward">{num(t.rewards?.proxy)}</Row>
              <Row label="Aligned reward">{num(t.rewards?.aligned)}</Row>
              <Row label="Verifier">
                <VerifierStatus passed={t.verifier?.passed ?? null} />
              </Row>
              <Row label="Hack">
                <HackFlag isHack={t.is_hack} />
              </Row>
            </dl>
            {t.verifier && <p className="mt-3 border-t pt-3 text-xs text-muted-foreground">{t.verifier.reason}</p>}
          </CardContent>
        </Card>

        <Card size="sm">
          <CardHeader>
            <CardTitle>Final world state</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <Row label="Scenario">{scenarioLabel(s.scenario)}</Row>
              <Row label="Refund expected">{s.refund_expected ? "Yes" : "No"}</Row>
              <Row label="Refunds issued">{s.refunds_issued.length ? s.refunds_issued.join(", ") : "None"}</Row>
              <Row label={`Ticket ${s.target_ticket_id}`}>{s.ticket_status}</Row>
              <Row label="Turns">{s.num_turns} / 10</Row>
            </dl>
          </CardContent>
        </Card>
      </aside>
    </div>
  );
}
