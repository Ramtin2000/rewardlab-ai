"""Agent loop tests against a scripted fake model. No Ollama needed."""

import json
from types import SimpleNamespace

from openai.types.chat import ChatCompletionMessage

from rewardlab.agent.loop import run_episode
from rewardlab.env import Scenario


def call(name, args, call_id=None):
    raw = args if isinstance(args, str) else json.dumps(args)
    return {"id": call_id or f"call_{name}", "type": "function", "function": {"name": name, "arguments": raw}}


def reply(content=None, calls=()):
    return ChatCompletionMessage(role="assistant", content=content, tool_calls=list(calls) or None)


class FakeClient:
    """Returns scripted replies in order; the script can use the env's real ids via callables."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        msg = self.script.pop(0) if self.script else reply("done")
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


SEED = 7  # canceled_confirmed: ticket 1404, order 3471 (see test_env / the learning log)
TICKET, ORDER = 1404, 3471


def episode(script, scenario=Scenario.CANCELED_CONFIRMED, **kw):
    client = FakeClient(script)
    t = run_episode(client, "fake-model", SEED, scenario, run_id="test", **kw)
    return t, client


def test_honest_episode_is_logged_turn_by_turn():
    t, client = episode([
        reply("Reading the ticket.", [call("lookup_ticket", {"ticket_id": TICKET})]),
        reply(None, [call("lookup_order", {"order_id": ORDER})]),
        reply(None, [call("lookup_payment", {"order_id": ORDER})]),
        reply(None, [call("issue_refund", {"order_id": ORDER})]),
        reply(None, [call("close_ticket", {"ticket_id": TICKET})]),
        reply("Your refund is on its way."),
    ])

    assert [turn.tool for turn in t.turns] == ["lookup_ticket", "lookup_order", "lookup_payment", "issue_refund", "close_ticket"]
    assert t.turns[0].assistant_message == "Reading the ticket."
    assert t.turns[3].state_changes == [f"payment {ORDER}: confirmed → refunded"]
    assert t.final_message == "Your refund is on its way."
    assert t.terminated_by == "agent_finished"
    assert t.final_state.refunds_issued == [ORDER]
    assert t.episode_id == "test-0007"
    assert t.rewards is None and t.verifier is None  # scoring is not the loop's job


def test_tool_results_are_fed_back_to_the_model():
    _, client = episode([reply(None, [call("lookup_ticket", {"ticket_id": TICKET}, "c1")]), reply("bye")])

    second = client.requests[1]["messages"]
    assert second[0]["role"] == "system"
    assert second[2]["tool_calls"][0]["id"] == "c1"
    assert second[3]["role"] == "tool" and second[3]["tool_call_id"] == "c1"
    assert json.loads(second[3]["content"])["order_id"] == ORDER


def test_shortcut_episode():
    t, _ = episode([reply(None, [call("close_ticket", {"ticket_id": TICKET})]), reply("Resolved.")])

    assert len(t.turns) == 1
    assert t.final_state.ticket_status == "resolved"
    assert t.final_state.refunds_issued == []
    assert t.final_state.refund_expected is True


def test_no_tool_call_ends_the_episode_immediately():
    t, _ = episode([reply("Could you tell me more?")])

    assert t.turns == []
    assert t.final_message == "Could you tell me more?"
    assert t.final_state.ticket_status == "open"


def test_invalid_json_arguments_cost_a_turn():
    t, _ = episode([reply(None, [call("lookup_order", "{order_id: 3471")]), reply("stop")])

    assert len(t.turns) == 1
    assert "must be a JSON object" in t.turns[0].observation["error"]
    assert t.turns[0].args == {"_raw": "{order_id: 3471"}


def test_parallel_tool_calls_each_take_a_turn():
    t, _ = episode([
        reply(None, [call("lookup_order", {"order_id": ORDER}, "a"), call("lookup_payment", {"order_id": ORDER}, "b")]),
        reply("ok"),
    ])
    assert [turn.index for turn in t.turns] == [1, 2]


def test_turn_limit_stops_the_loop():
    looping = [reply(None, [call("lookup_ticket", {"ticket_id": TICKET})]) for _ in range(20)]
    t, client = episode(looping, max_turns=3)

    assert len(t.turns) == 3
    assert t.terminated_by == "turn_limit"
    assert len(client.requests) == 3


def test_turn_limit_drops_remaining_parallel_calls():
    t, _ = episode([reply(None, [call("lookup_ticket", {"ticket_id": TICKET}, str(i)) for i in range(5)])], max_turns=2)
    assert len(t.turns) == 2
    assert t.terminated_by == "turn_limit"
