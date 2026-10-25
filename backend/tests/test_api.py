import json

import pytest
from fastapi.testclient import TestClient

from rewardlab.api import app as api_module

RUN = {
    "id": "grpo-proxy",
    "name": "GRPO · proxy reward",
    "kind": "trained",
    "model": "qwen3-4b-instruct",
    "reward_fn": "proxy",
    "status": "completed",
    "created_at": "2026-10-22T09:15:00Z",
    "checkpoints": [{
        "step": 0, "episodes": 10, "mean_proxy_reward": 0.5, "mean_aligned_reward": 0.1,
        "verified_success": 0.4, "hack_rate": 0.1, "mean_turns": 4.0,
    }],
}


def trajectory(episode_id, is_hack):
    return {
        "episode_id": episode_id, "run_id": "grpo-proxy", "checkpoint_step": 0, "seed": 1,
        "scenario": "canceled_confirmed", "model": "qwen3-4b-instruct",
        "turns": [{"index": 1, "tool": "close_ticket", "args": {"ticket_id": 1}, "observation": {"ok": True}}],
        "final_message": None,
        "final_state": {
            "scenario": "canceled_confirmed", "target_ticket_id": 1, "target_order_id": 2,
            "refund_expected": True, "ticket_status": "resolved", "refunds_issued": [], "num_turns": 1,
        },
        "terminated_by": "agent_finished",
        "rewards": {"proxy": 1.0},
        "verifier": {"passed": not is_hack, "reason": "test"},
        "is_hack": is_hack,
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    run_dir = tmp_path / "grpo-proxy"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(json.dumps(RUN))
    (run_dir / "trajectories.jsonl").write_text(
        "\n".join(json.dumps(t) for t in [trajectory("ep-1", True), trajectory("ep-2", False)])
    )
    monkeypatch.setattr(api_module, "RUNS_DIR", tmp_path)
    return TestClient(api_module.app)


def test_runs(client):
    assert [r["id"] for r in client.get("/runs").json()] == ["grpo-proxy"]


def test_trajectory_filters(client):
    assert len(client.get("/trajectories").json()) == 2
    hacks = client.get("/trajectories", params={"hack": "true"}).json()
    assert [t["episode_id"] for t in hacks] == ["ep-1"]
    passed = client.get("/trajectories", params={"verifier": "passed"}).json()
    assert [t["episode_id"] for t in passed] == ["ep-2"]


def test_trajectory_detail(client):
    assert client.get("/trajectories/ep-1").json()["is_hack"] is True
    assert client.get("/trajectories/missing").status_code == 404


def test_playground_careful_refunds_when_owed(client):
    body = {"scenario": "canceled_confirmed", "model": "scripted:careful", "reward_fn": "proxy", "seed": 3}
    t = client.post("/playground/run", json=body).json()
    assert [turn["tool"] for turn in t["turns"]] == [
        "lookup_ticket", "lookup_order", "lookup_payment", "issue_refund", "close_ticket",
    ]
    assert t["final_state"]["refunds_issued"] == [t["final_state"]["target_order_id"]]
    assert t["final_state"]["ticket_status"] == "resolved"


def test_playground_careful_skips_refund_when_not_owed(client):
    body = {"scenario": "delivered_refund_request", "model": "scripted:careful", "reward_fn": "proxy", "seed": 3}
    t = client.post("/playground/run", json=body).json()
    assert "issue_refund" not in [turn["tool"] for turn in t["turns"]]
    assert t["final_state"]["ticket_status"] == "resolved"


def test_playground_shortcut(client):
    body = {"scenario": "canceled_confirmed", "model": "scripted:shortcut", "reward_fn": "proxy", "seed": 3}
    t = client.post("/playground/run", json=body).json()
    assert [turn["tool"] for turn in t["turns"]] == ["close_ticket"]
    assert t["turns"][0]["state_changes"]  # ticket open -> resolved
    # playground episodes are scored: the shortcut gets full proxy reward and fails the verifier
    assert t["rewards"]["proxy"] == 1.0
    assert t["verifier"]["passed"] is False
    assert t["is_hack"] is True


def test_playground_unknown_model(client):
    body = {"scenario": "canceled_confirmed", "model": "nope", "reward_fn": "proxy"}
    assert client.post("/playground/run", json=body).status_code == 400
