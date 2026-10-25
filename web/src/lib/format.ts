import { SCENARIOS, type Run, type Scenario } from "./types";

export const pct = (v: number | null | undefined) => (v == null ? "—" : `${Math.round(v * 100)}%`);

export const num = (v: number | null | undefined, digits = 2) => (v == null ? "—" : v.toFixed(digits));

export const scenarioLabel = (s: Scenario) => SCENARIOS.find((x) => x.id === s)?.label ?? s;

export const shortDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });

export const latest = (run: Run) => run.checkpoints[run.checkpoints.length - 1];

// Color follows the run, everywhere in the app. Baseline is a neutral reference.
export function runColor(run: Pick<Run, "kind" | "reward_fn">) {
  if (run.kind === "baseline") return "var(--run-baseline)";
  return run.reward_fn === "proxy" ? "var(--run-proxy)" : "var(--run-aligned)";
}

type RateMetric = "mean_proxy_reward" | "verified_success" | "hack_rate";

// Shape runs into chart input: trained runs become lines, the baseline a reference value.
export function metricSeries(runs: Run[], metric: RateMetric) {
  const base = runs.find((r) => r.kind === "baseline");
  return {
    series: runs
      .filter((r) => r.kind === "trained")
      .map((r) => ({
        id: r.id,
        name: r.name,
        color: runColor(r),
        points: r.checkpoints.map((c) => ({ step: c.step, value: c[metric] })),
      })),
    baseline: base && { name: "Baseline", value: latest(base)[metric], color: runColor(base) },
  };
}
