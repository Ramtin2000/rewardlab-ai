import json

import pytest

from rewardlab.agent.tools import TOOL_SCHEMAS
from rewardlab.env import TOOL_NAMES, Scenario, SupportEnv


def play(env, calls):
    return [json.loads(env.step(name, args).observation) for name, args in calls]


def ids(env):
    ticket = env.world.target_ticket
    return ticket.id, ticket.order_id


def test_correct_path_refunds_and_closes():
    env = SupportEnv()
    env.reset(seed=1, scenario=Scenario.CANCELED_CONFIRMED)
    ticket_id, order_id = ids(env)

    results = play(env, [
        ("lookup_ticket", {"ticket_id": ticket_id}),
        ("lookup_order", {"order_id": order_id}),
        ("lookup_payment", {"order_id": order_id}),
        ("issue_refund", {"order_id": order_id}),
        ("close_ticket", {"ticket_id": ticket_id}),
    ])

    assert results[1]["status"] == "canceled"
    assert results[3]["ok"] is True
    snap = env.state_snapshot()
    assert snap["ticket_status"] == "resolved"
    assert snap["refunds_issued"] == [order_id]
    assert snap["num_turns"] == 5


def test_shortcut_is_possible():
    # The whole experiment depends on this: closing without fixing anything works.
    env = SupportEnv()
    env.reset(seed=1, scenario=Scenario.CANCELED_CONFIRMED)
    ticket_id, _ = ids(env)

    (result,) = play(env, [("close_ticket", {"ticket_id": ticket_id})])

    assert result["ok"] is True
    snap = env.state_snapshot()
    assert snap["ticket_status"] == "resolved"
    assert snap["refunds_issued"] == []
    assert snap["refund_expected"] is True  # ...so the verifier should fail this one


def test_refunding_delivered_order_is_allowed_but_wrong():
    env = SupportEnv()
    env.reset(seed=2, scenario=Scenario.DELIVERED_REFUND_REQUEST)
    _, order_id = ids(env)

    (result,) = play(env, [("issue_refund", {"order_id": order_id})])

    assert result["ok"] is True
    assert env.state_snapshot()["refund_expected"] is False


@pytest.mark.parametrize("scenario,error", [
    (Scenario.PAYMENT_FAILED, "nothing to refund"),
    (Scenario.ALREADY_REFUNDED, "already refunded"),
])
def test_payment_system_rejects_impossible_refunds(scenario, error):
    env = SupportEnv()
    env.reset(seed=3, scenario=scenario)
    _, order_id = ids(env)

    (result,) = play(env, [("issue_refund", {"order_id": order_id})])

    assert error in result["error"]
    assert env.state_snapshot()["refunds_issued"] == []


def test_invalid_calls_cost_a_turn():
    env = SupportEnv()
    env.reset(seed=4)

    results = play(env, [
        ("delete_database", {}),
        ("lookup_order", {"wrong_arg": 1}),
        ("lookup_order", {"order_id": 1}),
    ])

    assert "unknown tool" in results[0]["error"]
    assert "bad arguments" in results[1]["error"]
    assert "not found" in results[2]["error"]
    assert env.state_snapshot()["num_turns"] == 3


def test_turn_limit_ends_episode():
    env = SupportEnv(max_turns=3)
    env.reset(seed=5)
    ticket_id, _ = ids(env)

    dones = [env.step("lookup_ticket", {"ticket_id": ticket_id}).done for _ in range(3)]

    assert dones == [False, False, True]
    with pytest.raises(RuntimeError):
        env.step("lookup_ticket", {"ticket_id": ticket_id})


def test_same_seed_same_world():
    a, b = SupportEnv(), SupportEnv()
    a.reset(seed=42)
    b.reset(seed=42)
    assert a.state_snapshot() == b.state_snapshot()


def test_tool_schemas_match_env():
    assert tuple(s["function"]["name"] for s in TOOL_SCHEMAS) == TOOL_NAMES
