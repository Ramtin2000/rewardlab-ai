"""Run a batch of episodes and log them to runs/<run_id>/trajectories.jsonl.

    python -m rewardlab.agent.run --run-id scratch --episodes 20

An ad hoc runner for poking at the model. For the fixed evaluation set that
produces comparable metrics, use `python -m rewardlab.eval.run`.

Seeds run from --seed-start upward and scenarios rotate through all four, so
any 4 consecutive episodes cover every scenario once. Each episode is written
as soon as it finishes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Sequence

from openai import APIConnectionError

from rewardlab.agent import llm
from rewardlab.agent.loop import run_episode
from rewardlab.env import Scenario
from rewardlab.paths import RUNS_DIR
from rewardlab.rewards.score import score
from rewardlab.schemas import Trajectory

SCENARIOS = list(Scenario)


def describe(t: Trajectory) -> str:
    s = t.final_state
    tools = "→".join(turn.tool for turn in t.turns) or "(no tools)"
    refund = f"refunded {s.refunds_issued}" if s.refunds_issued else "no refund"
    owed = "owed" if s.refund_expected else "not owed"
    limit = " [turn limit]" if t.terminated_by == "turn_limit" else ""
    verdict = "PASS" if t.verifier and t.verifier.passed else "FAIL"
    hack = "  HACK" if t.is_hack else ""
    return (
        f"{t.scenario:<25} {len(t.turns):>2} turns  ticket {s.ticket_status:<8}  {refund} ({owed}){limit}\n"
        f"    {tools}\n"
        f"    proxy {t.rewards['proxy']:.1f} · aligned {t.rewards['aligned']:+.2f} · verifier {verdict}{hack}"
    )


def run_batch(
    client,
    model: str,
    episodes: Sequence[tuple[int, Scenario]],
    *,
    run_id: str,
    out: Path,
    temperature: float = 0.7,
    max_turns: int = 10,
    on_episode: Callable[[Trajectory], None] | None = None,
) -> list[Trajectory]:
    """Play each (seed, scenario), score it, and append it to `out` as soon as it finishes."""
    out.parent.mkdir(parents=True, exist_ok=True)
    results: list[Trajectory] = []
    try:
        with out.open("w") as f:
            for seed, scenario in episodes:
                t = score(run_episode(
                    client, model, seed, scenario,
                    run_id=run_id, temperature=temperature, max_turns=max_turns,
                ))
                f.write(t.model_dump_json() + "\n")
                f.flush()
                results.append(t)
                if on_episode:
                    on_episode(t)
    finally:
        llm.flush()
    return results


def connection_help(base_url: str) -> str:
    return f"Could not reach {base_url}. Is Ollama running? (open the Ollama app)"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", required=True)
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--seed-start", type=int, default=0)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-turns", type=int, default=10)
    p.add_argument("--overwrite", action="store_true", help="replace an existing trajectories.jsonl")
    args = p.parse_args(argv)

    out = RUNS_DIR / args.run_id / "trajectories.jsonl"
    if out.exists() and not args.overwrite:
        print(f"{out} already exists. Pass --overwrite or use another --run-id.", file=sys.stderr)
        return 1

    s = llm.settings()
    print(f"model {s.model} @ {s.base_url} · temperature {args.temperature} · tracing {'on' if llm.tracing_enabled() else 'off'}")
    print(f"writing {out}\n")

    episodes = [(args.seed_start + i, SCENARIOS[i % len(SCENARIOS)]) for i in range(args.episodes)]
    try:
        results = run_batch(
            llm.make_client(), s.model, episodes, run_id=args.run_id, out=out,
            temperature=args.temperature, max_turns=args.max_turns,
            on_episode=lambda t: print(f"seed {t.seed:04d}  {describe(t)}"),
        )
    except APIConnectionError:
        print("\n" + connection_help(s.base_url), file=sys.stderr)
        return 1

    n = len(results)
    owed = [t for t in results if t.final_state.refund_expected]
    not_owed = [t for t in results if not t.final_state.refund_expected]
    print(
        f"\n{n} episodes"
        f" · resolved {sum(t.final_state.ticket_status == 'resolved' for t in results)}/{n}"
        f" · refunded when owed {sum(bool(t.final_state.refunds_issued) for t in owed)}/{len(owed)}"
        f" · refunded when NOT owed {sum(bool(t.final_state.refunds_issued) for t in not_owed)}/{len(not_owed)}"
        f" · hit turn limit {sum(t.terminated_by == 'turn_limit' for t in results)}/{n}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
