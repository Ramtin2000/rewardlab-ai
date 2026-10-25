"""Evaluate the model on the fixed eval set and register the result as a run.

    python -m rewardlab.eval.run                    # 100 episodes, untrained baseline
    python -m rewardlab.eval.run --episodes 20      # quick check

Writes runs/<run_id>/trajectories.jsonl (every scored episode) and
runs/<run_id>/run.json (the metrics the dashboard plots).
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from openai import APIConnectionError

from rewardlab.agent import llm, loop
from rewardlab.agent.run import connection_help, run_batch
from rewardlab.eval.metrics import by_scenario, compute_metrics, invalid_call_rate
from rewardlab.eval.seeds import DEFAULT_EPISODES, eval_episodes
from rewardlab.paths import RUNS_DIR
from rewardlab.schemas import Run, Trajectory

BASELINE_ID = "baseline-v2-clear-prompt"


def evaluate(
    client,
    model: str,
    *,
    run_id: str,
    name: str,
    episodes: int = DEFAULT_EPISODES,
    temperature: float = 0.7,
    runs_dir: Path = RUNS_DIR,
    on_episode=None,
) -> tuple[Run, list[Trajectory]]:
    results = run_batch(
        client, model, eval_episodes(episodes),
        run_id=run_id, out=runs_dir / run_id / "trajectories.jsonl",
        temperature=temperature, on_episode=on_episode,
    )
    run = Run(
        id=run_id,
        name=name,
        kind="baseline",
        model=model,
        reward_fn=None,
        status="completed",
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        checkpoints=[compute_metrics(results, step=0)],
    )
    (runs_dir / run_id / "run.json").write_text(run.model_dump_json(indent=2) + "\n")
    (runs_dir / run_id / "system_prompt.txt").write_text(loop.SYSTEM_PROMPT)  # what this run was told
    return run, results


def report(run: Run, results: list[Trajectory]) -> str:
    m = run.checkpoints[0]
    lines = [
        f"{run.name} · {run.model} · {m.episodes} episodes",
        "",
        f"  proxy reward      {m.mean_proxy_reward:.2f}",
        f"  aligned reward    {m.mean_aligned_reward:+.2f}",
        f"  verified success  {m.verified_success:.0%}",
        f"  hack rate         {m.hack_rate:.0%}",
        f"  mean turns        {m.mean_turns:.1f}",
        f"  invalid calls     {invalid_call_rate(results):.1%} of tool calls",
        f"  hit turn limit    {sum(t.terminated_by == 'turn_limit' for t in results)}/{len(results)}",
        "",
        f"  {'scenario':<26}{'n':>4}{'proxy':>8}{'verified':>10}{'hack':>7}{'turns':>7}",
    ]
    for scenario, s in sorted(by_scenario(results).items()):
        lines.append(
            f"  {scenario:<26}{s.episodes:>4}{s.mean_proxy_reward:>8.2f}{s.verified_success:>10.0%}"
            f"{s.hack_rate:>7.0%}{s.mean_turns:>7.1f}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", default=BASELINE_ID)
    p.add_argument("--name", default="Baseline v2 (clear closing prompt)")
    p.add_argument("--episodes", type=int, default=DEFAULT_EPISODES)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--overwrite", action="store_true", help="replace an existing run with the same id")
    args = p.parse_args(argv)

    if (RUNS_DIR / args.run_id / "run.json").exists() and not args.overwrite:
        print(f"Run '{args.run_id}' already exists. Pass --overwrite or use another --run-id.", file=sys.stderr)
        return 1

    s = llm.settings()
    print(f"model {s.model} @ {s.base_url} · temperature {args.temperature} · tracing {'on' if llm.tracing_enabled() else 'off'}")
    done = []

    def progress(t: Trajectory) -> None:
        done.append(t)
        print(f"\r  {len(done)}/{args.episodes}", end="", flush=True)

    try:
        run, results = evaluate(
            llm.make_client(), s.model, run_id=args.run_id, name=args.name,
            episodes=args.episodes, temperature=args.temperature, on_episode=progress,
        )
    except APIConnectionError:
        print("\n" + connection_help(s.base_url), file=sys.stderr)
        return 1
    print("\n\n" + report(run, results))
    print(f"\nwrote {RUNS_DIR / run.id}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
