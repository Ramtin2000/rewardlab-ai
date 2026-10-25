"""The multi-turn agent loop: observe → decide → call tool → receive result → repeat.

One call to run_episode() plays one ticket to completion (the model stops
calling tools) or to the turn limit, and returns the full Trajectory.
Nothing here scores the episode; rewards and the verifier come later and
read the Trajectory.
"""

from __future__ import annotations

import json

from rewardlab.agent import llm
from rewardlab.agent.prompts import SYSTEM_PROMPT
from rewardlab.agent.tools import TOOL_SCHEMAS
from rewardlab.env import Scenario, SupportEnv
from rewardlab.schemas import Trajectory, Turn
from rewardlab.trajectory import final_state, take_step


def _parse_args(raw: str | None) -> dict | str:
    """Tool arguments arrive as a JSON string. Return the raw string if it isn't a JSON object."""
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return raw or ""
    return parsed if isinstance(parsed, dict) else raw or ""


def run_episode(
    client,
    model: str,
    seed: int,
    scenario: Scenario,
    *,
    run_id: str,
    checkpoint_step: int = 0,
    temperature: float = 0.7,
    max_turns: int = 10,
) -> Trajectory:
    env = SupportEnv(max_turns=max_turns)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": env.reset(seed=seed, scenario=scenario)},
    ]
    turns: list[Turn] = []
    final_message: str | None = None
    done = False
    episode_id = f"{run_id}-{seed:04d}"

    with llm.span(
        "episode",
        as_type="agent",
        input=messages[-1]["content"],
        metadata={"episode_id": episode_id, "run_id": run_id, "scenario": scenario.value, "seed": seed},
    ) as episode_span:
        while not done:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=temperature,
                **llm.trace_kwargs(f"turn {env.turn + 1}"),
            )
            msg = response.choices[0].message

            if not msg.tool_calls:  # the model chose to stop
                final_message = msg.content
                break

            messages.append(msg.model_dump(exclude_none=True))
            for i, call in enumerate(msg.tool_calls):
                args = _parse_args(call.function.arguments)
                # The model's text (if any) belongs to the first call of this response.
                with llm.span(call.function.name, as_type="tool", input=args) as tool_span:
                    turn, done = take_step(env, call.function.name, args, msg.content if i == 0 else None)
                    if tool_span is not None:
                        tool_span.update(output=turn.observation, metadata={"state_changes": turn.state_changes})
                turns.append(turn)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(turn.observation)})
                if done:  # turn limit hit mid-response; drop any remaining calls
                    break

        if episode_span is not None:
            episode_span.update(output={"final_message": final_message, "state": env.state_snapshot()})

    return Trajectory(
        episode_id=episode_id,
        run_id=run_id,
        checkpoint_step=checkpoint_step,
        seed=seed,
        scenario=scenario.value,
        model=model,
        turns=turns,
        final_message=final_message,
        final_state=final_state(env),
        terminated_by="turn_limit" if done else "agent_finished",
    )
