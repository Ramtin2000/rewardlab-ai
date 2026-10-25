"""The fixed evaluation set.

Every model we compare (the untrained baseline and each training checkpoint)
is evaluated on exactly the same tickets, so a difference in the numbers is
the model, not a lucky draw of seeds.

Evaluation seeds start at 10,000. Training seeds must stay below that so the
model is never tested on a ticket it trained on. Scenarios rotate by position,
so any multiple of 4 episodes is perfectly balanced across the four scenarios.
"""

from __future__ import annotations

from rewardlab.env import Scenario

EVAL_SEED_START = 10_000
DEFAULT_EPISODES = 100

SCENARIOS = list(Scenario)


def eval_episodes(n: int = DEFAULT_EPISODES) -> list[tuple[int, Scenario]]:
    return [(EVAL_SEED_START + i, SCENARIOS[i % len(SCENARIOS)]) for i in range(n)]
