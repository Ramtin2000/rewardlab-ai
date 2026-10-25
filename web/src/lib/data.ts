// The only place the UI gets data from.
// With REWARDLAB_API_URL unset, everything comes from fixtures.ts.
// Set it (e.g. http://localhost:8000) to read from the FastAPI backend instead;
// no component needs to change.

import * as fixtures from "./fixtures";
import type {
  PlaygroundModel,
  PlaygroundRequest,
  Run,
  Scenario,
  Trajectory,
  TrajectorySummary,
} from "./types";

const API_URL = process.env.REWARDLAB_API_URL;

export const dataSource: "api" | "fixtures" = API_URL ? "api" : "fixtures";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export function summarize(t: Trajectory): TrajectorySummary {
  return {
    episode_id: t.episode_id,
    run_id: t.run_id,
    checkpoint_step: t.checkpoint_step,
    scenario: t.scenario,
    num_turns: t.turns.length,
    terminated_by: t.terminated_by,
    proxy_reward: t.rewards?.proxy ?? null,
    verifier_passed: t.verifier?.passed ?? null,
    is_hack: t.is_hack,
  };
}

export async function getRuns(): Promise<Run[]> {
  if (API_URL) return api("/runs");
  return fixtures.runs;
}

export async function getRun(id: string): Promise<Run | null> {
  const all = await getRuns();
  return all.find((r) => r.id === id) ?? null;
}

export interface TrajectoryFilters {
  run_id?: string;
  scenario?: Scenario;
  verifier?: "passed" | "failed";
  hack?: boolean;
}

export async function getTrajectories(filters: TrajectoryFilters = {}): Promise<TrajectorySummary[]> {
  if (API_URL) {
    const qs = new URLSearchParams(
      Object.entries(filters)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)]),
    );
    return api(`/trajectories?${qs}`);
  }
  return fixtures.trajectories
    .filter((t) => !filters.run_id || t.run_id === filters.run_id)
    .filter((t) => !filters.scenario || t.scenario === filters.scenario)
    .filter((t) => !filters.verifier || t.verifier?.passed === (filters.verifier === "passed"))
    .filter((t) => filters.hack === undefined || t.is_hack === filters.hack)
    .map(summarize);
}

export async function getTrajectory(id: string): Promise<Trajectory | null> {
  if (API_URL) {
    const res = await fetch(`${API_URL}/trajectories/${encodeURIComponent(id)}`, { cache: "no-store" });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API /trajectories/${id} failed: ${res.status}`);
    return res.json();
  }
  return fixtures.trajectories.find((t) => t.episode_id === id) ?? null;
}

export async function getPlaygroundModels(): Promise<PlaygroundModel[]> {
  if (API_URL) return api("/playground/models");
  return fixtures.playgroundModels;
}

export async function runPlaygroundEpisode(req: PlaygroundRequest): Promise<Trajectory> {
  if (API_URL) {
    return api("/playground/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  }
  return fixtures.mockPlaygroundEpisode(req.scenario, req.model, req.seed);
}
