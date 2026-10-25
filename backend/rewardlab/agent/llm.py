"""Model client and optional Langfuse tracing.

Any OpenAI-compatible endpoint works (Ollama locally, OpenAI, ...), configured by
LLM_BASE_URL / LLM_MODEL in the repo-root .env. Tracing turns on when both
LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set; otherwise every tracing
helper here is a no-op.
"""

from __future__ import annotations

import os
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass

from dotenv import load_dotenv

from rewardlab.paths import ENV_FILE

load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class LLMSettings:
    base_url: str
    model: str
    api_key: str


def settings() -> LLMSettings:
    return LLMSettings(
        base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        model=os.getenv("LLM_MODEL", "rewardlab-qwen3-4b"),
        # Ollama ignores the key, but the OpenAI client requires one.
        api_key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "ollama",
    )


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


def make_client():
    s = settings()
    if tracing_enabled():
        from langfuse.openai import OpenAI  # drop-in wrapper that records each call
    else:
        from openai import OpenAI
    return OpenAI(base_url=s.base_url, api_key=s.api_key)


def trace_kwargs(name: str) -> dict:
    """Extra create() kwargs understood only by the Langfuse wrapper."""
    return {"name": name} if tracing_enabled() else {}


@contextmanager
def span(name: str, as_type: str = "span", **fields):
    """A Langfuse observation that nests everything inside it, or nothing when tracing is off."""
    if not tracing_enabled():
        with nullcontext() as none:
            yield none
        return
    from langfuse import get_client

    with get_client().start_as_current_observation(name=name, as_type=as_type, **fields) as obs:
        yield obs


def flush() -> None:
    if tracing_enabled():
        from langfuse import get_client

        get_client().flush()
