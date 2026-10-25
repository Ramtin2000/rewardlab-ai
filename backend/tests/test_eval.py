"""Evaluation set, metrics, and the eval runner (against a scripted fake model)."""

import json
from collections import Counter

import pytest

from rewardlab.env import Scenario
from rewardlab.eval.metrics import by_scenario, compute_metrics, invalid_call_rate
from rewardlab.eval.run import evaluate, report
from rewardlab.eval.seeds import EVAL_SEED_START, eval_episodes
from rewardlab.schemas import Run, Trajectory
from tests.fakes import ClosingClient


# --- the fixed eval set -------------------------------------------------------

def test_eval_set_is_deterministic():
    assert eval_episodes(100) == eval_episodes(100)


def test_eval_set_is_balanced_across_scenarios():
    counts = Counter(scenario for _, scenario in eval_episodes(100))
    assert counts == {s: 25 for s in Scenario}


def test_eval_seeds_are_unique_and_clear_of_training_seeds():
    seeds = [seed for seed, _ in eval_episodes(100)]
    assert len(set(seeds)) == 100
    assert min(seeds) >= EVAL_SEED_START >= 10_000  # training seeds stay below this


def test_smaller_eval_set_is_a_prefix():
    assert eval_episodes(8) == eval_episodes(100)[:8]


# --- metrics ------------------------------------------------------------------

@pytest.fixture(scope="module")
def shortcut_run(tmp_path_factory):
    """8 eval episodes played by a model that only ever closes the ticket."""
    run, results = evaluate(
        ClosingClient(), "fake", run_id="t", name="Shortcut", episodes=8,
        runs_dir=tmp_path_factory.mktemp("runs"),
    )
    return run, results


def test_shortcut_model_metrics(shortcut_run):
    run, results = shortcut_run
    m = run.checkpoints[0]
    assert m.episodes == 8
    assert m.mean_proxy_reward == 1.0       # every ticket is resolved
    assert m.verified_success == 0.75       # right in the 3 no-refund scenarios, wrong in 1
    assert m.hack_rate == 0.25              # the canceled_confirmed ones
    assert m.mean_turns == 1.0


def test_metrics_by_scenario(shortcut_run):
    _, results = shortcut_run
    groups = by_scenario(results)
    assert set(groups) == {s.value for s in Scenario}
    assert groups["canceled_confirmed"].verified_success == 0.0
    assert groups["canceled_confirmed"].hack_rate == 1.0
    assert groups["payment_failed"].verified_success == 1.0
    assert groups["payment_failed"].hack_rate == 0.0


def test_the_gap_shows_up_in_the_metrics(shortcut_run):
    m = shortcut_run[0].checkpoints[0]
    assert m.mean_proxy_reward - m.verified_success == pytest.approx(m.hack_rate)


def test_invalid_call_rate(shortcut_run):
    _, results = shortcut_run
    assert invalid_call_rate(results) == 0.0
    assert invalid_call_rate([]) == 0.0


def test_metrics_require_scored_trajectories(shortcut_run):
    _, results = shortcut_run
    unscored = results[0].model_copy(update={"rewards": None, "verifier": None})
    with pytest.raises(ValueError, match="scored"):
        compute_metrics([unscored])
    with pytest.raises(ValueError):
        compute_metrics([])


# --- the runner's output --------------------------------------------------------

def test_run_files_are_what_the_api_reads(tmp_path):
    run, _ = evaluate(ClosingClient(), "fake", run_id="base", name="Baseline", episodes=4, runs_dir=tmp_path)

    on_disk = Run.model_validate_json((tmp_path / "base" / "run.json").read_text())
    assert on_disk == run
    assert on_disk.kind == "baseline" and on_disk.reward_fn is None

    from rewardlab.agent.prompts import SYSTEM_PROMPT
    assert (tmp_path / "base" / "system_prompt.txt").read_text() == SYSTEM_PROMPT

    lines = (tmp_path / "base" / "trajectories.jsonl").read_text().splitlines()
    trajectories = [Trajectory.model_validate_json(line) for line in lines]
    assert len(trajectories) == 4
    assert all(t.rewards and t.verifier for t in trajectories)
    assert [t.seed for t in trajectories] == [seed for seed, _ in eval_episodes(4)]


def test_report_mentions_every_scenario(shortcut_run):
    text = report(*shortcut_run)
    assert "verified success  75%" in text
    for scenario in Scenario:
        assert scenario.value in text
