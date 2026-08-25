"""Unit tests for OpenAIProvider -- mocked SDK client, no network.

Also the platform-default Ollama / self-hosted / BYOK routing path relied on
elsewhere in the ecosystem: those callers just pass ``base_url=`` to point
at an OpenAI-compatible endpoint. Nothing about that path is provider-side
logic worth testing here beyond confirming ``base_url`` is forwarded as-is.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from civitas_contrib.plugins import openai as openai_plugin
from civitas_contrib.plugins.openai import OpenAIProvider


def _tool_call(id_: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _response(
    content: str | None,
    model: str = "gpt-4o",
    tool_calls: list[SimpleNamespace] | None = None,
    tokens_in: int = 10,
    tokens_out: int = 5,
    usage: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))],
        model=model,
        usage=(
            SimpleNamespace(prompt_tokens=tokens_in, completion_tokens=tokens_out)
            if usage
            else None
        ),
    )


def _provider() -> OpenAIProvider:
    provider = OpenAIProvider(api_key="test-key")
    provider._client.chat.completions.create = AsyncMock()
    return provider


async def test_chat_returns_content_and_usage() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(
        "hello", tokens_in=100, tokens_out=50
    )

    result = await provider.chat(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])

    assert result.content == "hello"
    assert result.model == "gpt-4o"
    assert result.tokens_in == 100
    assert result.tokens_out == 50
    assert result.tool_calls is None


async def test_chat_handles_none_content() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(None)

    result = await provider.chat(model="gpt-4o", messages=[])

    assert result.content == ""


async def test_chat_computes_known_model_cost() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(
        "hi", model="gpt-4o", tokens_in=1_000_000, tokens_out=1_000_000
    )

    result = await provider.chat(model="gpt-4o", messages=[])

    # (input $/M, output $/M) = (2.50, 10.00) for gpt-4o
    assert result.cost_usd == pytest.approx(12.50)


async def test_chat_versioned_model_id_matches_by_prefix() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(
        "hi", model="gpt-4o-2024-11-20", tokens_in=1_000_000, tokens_out=0
    )

    result = await provider.chat(model="gpt-4o-2024-11-20", messages=[])

    assert result.cost_usd == pytest.approx(2.50)


async def test_chat_unknown_model_returns_none_cost_not_zero() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(
        "hi", model="some-self-hosted-model", tokens_in=1000, tokens_out=1000
    )

    result = await provider.chat(model="some-self-hosted-model", messages=[])

    assert result.cost_usd is None


async def test_chat_missing_usage_reports_zero_tokens_not_error() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response("hi", usage=False)

    result = await provider.chat(model="gpt-4o", messages=[])

    assert result.tokens_in == 0
    assert result.tokens_out == 0


async def test_chat_extracts_tool_calls_and_parses_json_arguments() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response(
        None,
        tool_calls=[_tool_call("call_1", "search", {"query": "civitas"})],
    )

    result = await provider.chat(model="gpt-4o", messages=[])

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "call_1"
    assert result.tool_calls[0].name == "search"
    assert result.tool_calls[0].input == {"query": "civitas"}


async def test_chat_falls_back_to_default_model() -> None:
    provider = OpenAIProvider(api_key="test-key", default_model="gpt-4o-mini")
    provider._client.chat.completions.create = AsyncMock(return_value=_response("hi"))

    await provider.chat(model=None, messages=[])

    kwargs = provider._client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"


async def test_chat_sets_tool_choice_auto_only_when_tools_present() -> None:
    provider = _provider()
    provider._client.chat.completions.create.return_value = _response("hi")

    await provider.chat(model="gpt-4o", messages=[], tools=None)
    assert "tool_choice" not in provider._client.chat.completions.create.call_args.kwargs

    await provider.chat(model="gpt-4o", messages=[], tools=[{"name": "search"}])
    assert provider._client.chat.completions.create.call_args.kwargs["tool_choice"] == "auto"


def test_base_url_forwarded_for_openai_compatible_endpoints() -> None:
    # Ollama / self-hosted / BYOK-compatible endpoints all route through
    # base_url= -- confirm it reaches the underlying SDK client unchanged.
    provider = OpenAIProvider(api_key="unused", base_url="http://localhost:11434/v1")

    assert str(provider._client.base_url).rstrip("/") == "http://localhost:11434/v1"


def test_init_raises_import_error_when_openai_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openai_plugin, "_HAS_OPENAI", False)

    with pytest.raises(ImportError, match="openai"):
        OpenAIProvider(api_key="test-key")
