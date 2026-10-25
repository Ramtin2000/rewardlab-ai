"use server";

import { runPlaygroundEpisode } from "@/lib/data";
import { SCENARIOS, REWARD_FNS, type RewardFn, type Scenario, type Trajectory } from "@/lib/types";

export type PlaygroundState = { trajectory: Trajectory | null; error: string | null };

export async function runEpisode(_: PlaygroundState, form: FormData): Promise<PlaygroundState> {
  const scenario = form.get("scenario") as Scenario;
  const reward_fn = form.get("reward_fn") as RewardFn;
  const model = String(form.get("model") ?? "");
  const seed = Number(form.get("seed") ?? 0);

  if (!SCENARIOS.some((s) => s.id === scenario)) return { trajectory: null, error: "Pick a scenario." };
  if (!REWARD_FNS.some((r) => r.id === reward_fn)) return { trajectory: null, error: "Pick a reward function." };
  if (!model) return { trajectory: null, error: "Pick a model." };

  try {
    const trajectory = await runPlaygroundEpisode({ scenario, model, reward_fn, seed: Number.isFinite(seed) ? seed : 0 });
    return { trajectory, error: null };
  } catch (e) {
    return { trajectory: null, error: e instanceof Error ? e.message : "Episode failed." };
  }
}
