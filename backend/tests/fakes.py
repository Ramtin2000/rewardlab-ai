"""A scripted stand-in for the OpenAI client, so loop and eval tests need no model server."""

import json
import re
from types import SimpleNamespace

from openai.types.chat import ChatCompletionMessage


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


class ClosingClient:
    """A model that only ever calls close_ticket on the ticket it was assigned, then stops.

    The shortcut policy: against the four scenarios it passes the verifier in the three where
    no refund is owed and fails the one where a refund is.
    """

    def __init__(self):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        messages = kwargs["messages"]
        if any(m["role"] == "tool" for m in messages):
            msg = reply("Resolved.")
        else:
            ticket_id = int(re.search(r"#(\d+)", messages[1]["content"]).group(1))
            msg = reply(None, [call("close_ticket", {"ticket_id": ticket_id})])
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])
