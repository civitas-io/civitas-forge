"""Unit tests for AnthropicProvider -- mocked SDK client, no network."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from civitas_contrib.plugins import anthropic as anthropic_plugin
from civitas_contrib.plugins.anthropic import AnthropicProvider


def _block(text: str | None = None, tool_use: dict | None = None) -> SimpleNamespace:
    if tool_use is not None:
        return SimpleNamespace(
            type="tool_use", id=tool_use["id"], name=tool_use["name"], input=tool_use["input"]
        )
    return SimpleNamespace(type="text", text=text)


def _response(
    content: list[SimpleNamespace],
    model: str = "claude-sonnet-4-6",
    tokens_in: int = 10,
    tokens_out: int = 5,
) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        model=model,
        usage=SimpleNamespace(input_tokens=tokens_in, output_tokens=tokens_out),
    )


def _provider() -> AnthropicProvider:
    provider = AnthropicProvider(api_key="test-key")
    provider._client.messages.create = AsyncMock()
    return provider


async def test_chat_returns_text_content_and_usage() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response(
        [_block(text="hello")], tokens_in=100, tokens_out=50
    )

    result = await provider.chat(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "hi"}]
    )

    assert result.content == "hello"
    assert result.model == "claude-sonnet-4-6"
    assert result.tokens_in == 100
    assert result.tokens_out == 50
    assert result.tool_calls is None


async def test_chat_computes_known_model_cost() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response(
        [_block(text="hi")], model="claude-sonnet-4-6", tokens_in=1_000_000, tokens_out=1_000_000
    )

    result = await provider.chat(model="claude-sonnet-4-6", messages=[])

    # (input $/M, output $/M) = (3.0, 15.0) for claude-sonnet-4-6
    assert result.cost_usd == pytest.approx(18.0)


async def test_chat_versioned_model_id_matches_by_prefix() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response(
        [_block(text="hi")], model="claude-3-5-sonnet-20241022", tokens_in=1_000_000, tokens_out=0
    )

    result = await provider.chat(model="claude-3-5-sonnet-20241022", messages=[])

    assert result.cost_usd == pytest.approx(3.0)


async def test_chat_unknown_model_returns_none_cost_not_zero() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response(
        [_block(text="hi")], model="some-future-model", tokens_in=1000, tokens_out=1000
    )

    result = await provider.chat(model="some-future-model", messages=[])

    assert result.cost_usd is None


async def test_chat_extracts_tool_use_blocks() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response(
        [
            _block(text="thinking..."),
            _block(tool_use={"id": "tool_1", "name": "search", "input": {"query": "civitas"}}),
        ]
    )

    result = await provider.chat(model="claude-sonnet-4-6", messages=[])

    assert result.content == "thinking..."
    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "tool_1"
    assert result.tool_calls[0].name == "search"
    assert result.tool_calls[0].input == {"query": "civitas"}


async def test_chat_falls_back_to_default_model() -> None:
    provider = AnthropicProvider(api_key="test-key", default_model="claude-haiku-4-5-20251001")
    provider._client.messages.create = AsyncMock(return_value=_response([_block(text="hi")]))

    await provider.chat(model="", messages=[])

    kwargs = provider._client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-haiku-4-5-20251001"


async def test_chat_forwards_tools_only_when_present() -> None:
    provider = _provider()
    provider._client.messages.create.return_value = _response([_block(text="hi")])

    await provider.chat(model="claude-sonnet-4-6", messages=[], tools=None)
    assert "tools" not in provider._client.messages.create.call_args.kwargs

    await provider.chat(model="claude-sonnet-4-6", messages=[], tools=[{"name": "search"}])
    assert provider._client.messages.create.call_args.kwargs["tools"] == [{"name": "search"}]


def test_init_raises_import_error_when_anthropic_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(anthropic_plugin, "_HAS_ANTHROPIC", False)

    with pytest.raises(ImportError, match="anthropic"):
        AnthropicProvider(api_key="test-key")
