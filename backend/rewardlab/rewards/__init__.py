"""Reward functions and the independent verifier. Phase 4.

Scoring lives in rewardlab.rewards.score (also a CLI), imported from there
directly so `python -m rewardlab.rewards.score` runs cleanly.
"""

from rewardlab.rewards.functions import reward_aligned, reward_proxy, verify

__all__ = ["reward_aligned", "reward_proxy", "verify"]
