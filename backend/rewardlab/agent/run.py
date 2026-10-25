"""Run a batch of episodes and log them to runs/<run_id>/trajectories.jsonl.

    python -m rewardlab.agent.run --run-id baseline-qwen3-4b --episodes 20

Seeds run from --seed-start upward and scenarios rotate through all four, so
any 4 consecutive episodes cover every scenario once. Each episode is written
as soon as it finishes.
"""

from __future__ import annotations

import argparse
import sys

from openai import APIConnectionError

from rewardlab.agent import llm
from rewardlab.agent.loop import run_episode
from rewardlab.env import Scenario
from rewardlab.paths import RUNS_DIR
from rewardlab.schemas import Trajectory

SCENARIOS = list(Scenario)


def describe(t: Trajectory) -> str:
    s = t.final_state
    tools = "→".join(turn.tool for turn in t.turns) or "(no tools)"
    refund = f"refunded {s.refunds_issued}" if s.refunds_issued else "no refund"
    owed = "owed" if s.refund_expected else "not owed"
    limit = " [turn limit]" if t.terminated_by == "turn_limit" else ""
    return f"{t.scenario:<25} {len(t.turns):>2} turns  ticket {s.ticket_status:<8}  {refund} ({owed}){limit}\n    {tools}"


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
    out.parent.mkdir(parents=True, exist_ok=True)

    s = llm.settings()
    client = llm.make_client()
    print(f"model {s.model} @ {s.base_url} · temperature {args.temperature} · tracing {'on' if llm.tracing_enabled() else 'off'}")
    print(f"writing {out}\n")

    stats = {"resolved": 0, "refund_when_owed": 0, "owed": 0, "refund_when_not_owed": 0, "turn_limit": 0}
    try:
        with out.open("w") as f:
            for i in range(args.episodes):
                seed = args.seed_start + i
                t = run_episode(
                    client, s.model, seed, SCENARIOS[i % len(SCENARIOS)],
                    run_id=args.run_id, temperature=args.temperature, max_turns=args.max_turns,
                )
                f.write(t.model_dump_json() + "\n")
                f.flush()
                print(f"seed {seed:04d}  {describe(t)}")

                st = t.final_state
                stats["resolved"] += st.ticket_status == "resolved"
                stats["owed"] += st.refund_expected
                stats["refund_when_owed"] += st.refund_expected and bool(st.refunds_issued)
                stats["refund_when_not_owed"] += (not st.refund_expected) and bool(st.refunds_issued)
                stats["turn_limit"] += t.terminated_by == "turn_limit"
    except APIConnectionError:
        print(f"\nCould not reach {s.base_url}. Is Ollama running? (open the Ollama app)", file=sys.stderr)
        return 1
    finally:
        llm.flush()

    n = args.episodes
    print(
        f"\n{n} episodes · resolved {stats['resolved']}/{n}"
        f" · refunded when owed {stats['refund_when_owed']}/{stats['owed']}"
        f" · refunded when NOT owed {stats['refund_when_not_owed']}/{n - stats['owed']}"
        f" · hit turn limit {stats['turn_limit']}/{n}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
