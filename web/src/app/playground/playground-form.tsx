"use client";

import { useActionState } from "react";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrajectoryView } from "@/components/trajectory-view";
import { REWARD_FNS, SCENARIOS, type PlaygroundModel } from "@/lib/types";
import { runEpisode, type PlaygroundState } from "./actions";

function Field({ id, label, items, defaultValue }: {
  id: string;
  label: string;
  items: { value: string; label: string }[];
  defaultValue: string;
}) {
  return (
    <div className="grid min-w-0 gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Select name={id} defaultValue={defaultValue} items={Object.fromEntries(items.map((i) => [i.value, i.label]))}>
        <SelectTrigger id={id} className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {items.map((i) => (
            <SelectItem key={i.value} value={i.value}>
              {i.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function PlaygroundForm({ models }: { models: PlaygroundModel[] }) {
  const [state, action, pending] = useActionState<PlaygroundState, FormData>(runEpisode, { trajectory: null, error: null });

  return (
    <div className="space-y-6">
      <Card>
        <CardContent>
          <form action={action} className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_6rem_auto]">
            <Field
              id="scenario"
              label="Scenario"
              defaultValue={SCENARIOS[0].id}
              items={SCENARIOS.map((s) => ({ value: s.id, label: s.label }))}
            />
            <Field id="model" label="Model" defaultValue={models[0]?.id ?? ""} items={models.map((m) => ({ value: m.id, label: m.label }))} />
            <Field
              id="reward_fn"
              label="Reward function"
              defaultValue="proxy"
              items={REWARD_FNS.map((r) => ({ value: r.id, label: r.label }))}
            />
            <div className="grid gap-1.5">
              <Label htmlFor="seed">Seed</Label>
              <input
                id="seed"
                name="seed"
                type="number"
                defaultValue={7}
                className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm tabular-nums outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              />
            </div>
            <Button type="submit" disabled={pending}>
              {pending ? <Loader2 className="animate-spin" /> : <Play />}
              Run episode
            </Button>
          </form>
          {state.error && <p className="mt-3 text-sm text-destructive">{state.error}</p>}
        </CardContent>
      </Card>

      {state.trajectory ? (
        <TrajectoryView trajectory={state.trajectory} />
      ) : (
        <p className="text-sm text-muted-foreground">
          Pick a scenario and a checkpoint, then run an episode to see its trace.
        </p>
      )}
    </div>
  );
}
