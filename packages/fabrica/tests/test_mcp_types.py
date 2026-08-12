"""Real tests for MCPServerConfig's validation -- no live MCP server or
network connection needed, since __post_init__'s checks are pure.
"""

from __future__ import annotations

import pytest

from fabrica.mcp.types import MCPServerConfig


def test_stdio_transport_requires_command() -> None:
    with pytest.raises(ValueError, match="requires 'command'"):
        MCPServerConfig(name="test", transport="stdio")


def test_stdio_transport_with_command_is_valid() -> None:
    config = MCPServerConfig(name="test", transport="stdio", command="npx")
    assert config.command == "npx"


def test_sse_transport_requires_url() -> None:
    with pytest.raises(ValueError, match="requires 'url'"):
        MCPServerConfig(name="test", transport="sse")


def test_sse_transport_with_url_is_valid() -> None:
    config = MCPServerConfig(name="test", transport="sse", url="http://localhost:3000")
    assert config.url == "http://localhost:3000"


def test_unknown_transport_rejected() -> None:
    with pytest.raises(ValueError, match="unknown transport"):
        MCPServerConfig(name="test", transport="carrier-pigeon")  # type: ignore[arg-type]
