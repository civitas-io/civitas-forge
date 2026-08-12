# AGENTS.md

**Workspace:** `civitas-io/civitas-contrib` | **Python:** ≥ 3.12

This file guides AI coding agents (Claude Code, Cursor, Codex, Gemini CLI) working on
this codebase. Read it fully before writing any code.

Cross-cutting context (repo boundaries, positioning, roadmap) lives in the private
`civitas-io/context` repo — clone it alongside this one for full picture.

---

## Project Overview

`civitas-contrib` is a **uv workspace monorepo** containing two packages:

| Package | Import | PyPI | Purpose |
|---|---|---|---|
| `civitas-contrib` | `civitas_contrib` | `pip install civitas-contrib` | Provider plugins, framework adapters, eval exporters |
| `fabrica` | `fabrica` | superseded — see `packages/fabrica/README.md` | MCP tools gateway — sandboxed subprocess execution. **Superseded by [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) (`pip install fabrica-context`)**; this package's code is migrating there, not maintained as a standalone package going forward. |

Both packages depend on `civitas>=0.3` (one-way). They are **never imported by civitas
core**. civitas-contrib and fabrica may not import from each other.

This is the fast-iteration layer. civitas core is deliberately conservative; this
package is where integrations live and where breaking changes from upstream SDKs
(Anthropic, LangGraph, MCP, etc.) are absorbed.

---

## Org Structure

| Repo | Import | Contains |
|---|---|---|
| `civitas-io/python-civitas` | `civitas` | Core runtime — process, supervisor, message bus, transport |
| `civitas-io/civitas-contrib` | `civitas_contrib`, `fabrica` | This repo |
| `civitas-io/presidium` | `presidium` | Governance — policy, registry, audit |

**Dependency rule:** civitas-contrib → civitas. Never import back into civitas.
civitas and civitas-contrib must never form a circular dependency.

---

## Workspace Layout

```
civitas-contrib/                      # repo root (uv workspace)
  pyproject.toml                      # workspace root — lists workspace members
  packages/
    civitas-contrib/                  # pip install civitas-contrib
      pyproject.toml
      src/civitas_contrib/
        __init__.py
        plugins/
          __init__.py
          anthropic.py               # AnthropicProvider
          openai.py                  # OpenAIProvider
          gemini.py                  # GeminiProvider
          mistral.py                 # MistralProvider
          litellm.py                 # LiteLLMProvider
          otel.py                    # OTELExporter
          sqlite_store.py            # SQLiteStateStore
          postgres_store.py          # PostgresStateStore
          fiddler.py                 # FiddlerExporter (eval)
        adapters/
          __init__.py
          langgraph.py               # LangGraphAgent
          openai.py                  # OpenAIAgent
          crewai.py                  # CrewAIAgent (stub)
        eval/
          __init__.py
          exporters.py               # ArizeExporter, BraintrustExporter,
                                     #   FiddlerExporter, LangfuseExporter, LangSmithExporter
      tests/
    fabrica/                          # SUPERSEDED -- migrating to civitas-io/fabrica (pip install fabrica-context)
      pyproject.toml
      src/fabrica/
        __init__.py
        mcp/
          __init__.py
          client.py                  # MCPClient — manages MCP server subprocess
          tool.py                    # MCPTool — wraps MCPClient as ToolProvider
          types.py                   # MCPServerConfig, MCPToolSchema
        sandbox/
          __init__.py
          config.py                  # SandboxConfig, FilesystemMount (re-exported from civitas)
          bubblewrap.py              # BubblewrapSandbox — Linux bubblewrap isolation
      tests/
  docs/
  rfcs/
```

---

## Install

```bash
# civitas-contrib extras
pip install civitas-contrib                  # base (requires civitas)
pip install civitas-contrib[anthropic]       # + Anthropic Claude
pip install civitas-contrib[openai]          # + OpenAI GPT-4o / o-series + Agents SDK
pip install civitas-contrib[gemini]          # + Google Gemini
pip install civitas-contrib[mistral]         # + Mistral
pip install civitas-contrib[litellm]         # + LiteLLM (100+ models)
pip install civitas-contrib[langgraph]       # + LangGraph adapter
pip install civitas-contrib[postgres]        # + PostgreSQL state store (asyncpg)
pip install civitas-contrib[otel]            # + OTEL eval exporter
pip install civitas-contrib[langfuse]        # + Langfuse eval exporter
pip install civitas-contrib[braintrust]      # + Braintrust eval exporter
pip install civitas-contrib[langsmith]       # + LangSmith eval exporter
pip install civitas-contrib[arize]           # + Arize eval exporter
pip install civitas-contrib[fiddler]         # + Fiddler eval exporter

# fabrica extras -- SUPERSEDED, these commands never actually worked as
# written (fabrica is taken on PyPI by an unrelated project). Kept here only
# as a record of the original intent; use civitas-io/fabrica instead:
#   pip install fabrica-context
```

---

## Quick Import Reference

```python
# Model providers
from civitas_contrib.plugins.anthropic import AnthropicProvider
from civitas_contrib.plugins.openai import OpenAIProvider
from civitas_contrib.plugins.gemini import GeminiProvider
from civitas_contrib.plugins.mistral import MistralProvider
from civitas_contrib.plugins.litellm import LiteLLMProvider

# State stores
from civitas_contrib.plugins.sqlite_store import SQLiteStateStore
from civitas_contrib.plugins.postgres_store import PostgresStateStore

# Framework adapters
from civitas_contrib.adapters.langgraph import LangGraphAgent
from civitas_contrib.adapters.openai import OpenAIAgent

# Eval exporters
from civitas_contrib.eval.exporters import (
    ArizeExporter,
    BraintrustExporter,
    FiddlerExporter,
    LangfuseExporter,
    LangSmithExporter,
)

# MCP gateway
from fabrica.mcp.client import MCPClient
from fabrica.mcp.tool import MCPTool
from fabrica.mcp.types import MCPServerConfig, MCPToolSchema

# Sandbox
from fabrica.sandbox.bubblewrap import BubblewrapSandbox
from fabrica.sandbox.config import SandboxConfig, FilesystemMount
```

---

## Environment Setup

This workspace uses **`uv`** with workspace support.

```bash
# Install uv if not present
curl -Ls https://astral.sh/uv/install.sh | sh

# Sync the entire workspace (all packages)
uv sync --all-extras

# Run tests for a specific package
uv run --package civitas-contrib pytest packages/civitas-contrib/tests/
uv run --package fabrica pytest packages/fabrica/tests/
```

### Environment variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | AnthropicProvider |
| `OPENAI_API_KEY` | OpenAIProvider, OpenAIAgent |
| `GEMINI_API_KEY` | GeminiProvider |
| `MISTRAL_API_KEY` | MistralProvider |
| `FIDDLER_URL`, `FIDDLER_API_KEY` | FiddlerExporter |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | LangfuseExporter |
| `BRAINTRUST_API_KEY` | BraintrustExporter |
| `LANGSMITH_API_KEY` | LangSmithExporter |
| `ARIZE_SPACE_KEY`, `ARIZE_API_KEY` | ArizeExporter |

Never read `os.environ` directly — use the provider's own config pattern or
`civitas.config.settings` for shared settings.

---

## Commands Reference

| Task | Command |
|---|---|
| Sync all packages | `uv sync --all-extras` |
| Run civitas-contrib tests | `uv run pytest packages/civitas-contrib/tests/` |
| Run fabrica tests | `uv run pytest packages/fabrica/tests/` |
| Lint all | `uv run ruff check .` |
| Format all | `uv run ruff format .` |
| Type-check civitas-contrib | `uv run mypy packages/civitas-contrib/src/` |
| Type-check fabrica | `uv run mypy packages/fabrica/src/` |

Run before finishing any task:

```bash
uv run ruff check . && uv run ruff format . && uv run pytest
```

---

## Writing a Model Provider

Model providers implement the `ModelProvider` protocol from civitas core:

```python
from civitas.plugins.model import ModelProvider, ModelResponse, ToolCall
from typing import Any

class MyProvider:
    """ModelProvider for MyLLM."""

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        # Call the upstream SDK here
        raw = await my_sdk.complete(model=model, messages=messages)
        return ModelResponse(
            content=raw.text,
            model=raw.model,
            tokens_in=raw.usage.input,
            tokens_out=raw.usage.output,
            cost_usd=None,
            tool_calls=None,
        )
```

**Rules:**
- Never import from civitas-contrib from inside civitas core — providers are
  resolved lazily via `civitas.plugins.loader`.
- Register the short name in `civitas/plugins/loader.py` `_BUILTINS["model"]`
  so `type: myprovider` works in topology YAML.
- Keep SDK calls async — never use sync SDK methods.
- Handle `429` / rate limit errors at the provider level, not in AgentProcess.

---

## Writing a Framework Adapter

Adapters subclass `AgentProcess` from civitas and delegate to the wrapped framework:

```python
from civitas.process import AgentProcess
from civitas.messages import Message
from civitas.errors import ErrorAction

class MyFrameworkAgent(AgentProcess):
    def __init__(self, name: str, framework_agent: Any, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._agent = framework_agent

    async def handle(self, message: Message) -> Message | None:
        result = await self._agent.run(message.payload)
        return self.reply({"output": result})

    def _is_transient(self, error: Exception) -> bool:
        return False

    async def on_error(self, error: Exception, message: Message) -> ErrorAction:
        if message.attempt < 3 and self._is_transient(error):
            return ErrorAction.RETRY
        return ErrorAction.ESCALATE
```

---

## Writing an Eval Exporter

Eval exporters implement the `EvalExporter` protocol from civitas core:

```python
from civitas.evalloop import EvalEvent, EvalExporter

class MyExporter:
    async def export(self, event: EvalEvent) -> None:
        # Ship the event to the external platform
        await my_platform_sdk.log(event.model_dump())

    async def close(self) -> None:
        await my_platform_sdk.flush()
```

---

## MCP Gateway (fabrica) — SUPERSEDED, code accurate for now, home is moving

> This code still works as documented below, but is migrating to
> [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) as the
> implementation behind that project's `MCPToolNamespace` (`pip install
> fabrica-context`). Don't build new work against this package's location
> long-term — treat this section as accurate-but-temporary.

`MCPClient` manages a single MCP server as a subprocess. `MCPTool` wraps it as a
`ToolProvider` for use with `ToolRegistry`.

```python
from fabrica.mcp.client import MCPClient
from fabrica.mcp.tool import MCPTool
from fabrica.mcp.types import MCPServerConfig
from civitas.plugins.tools import ToolRegistry

config = MCPServerConfig(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
)

async def setup_tools() -> ToolRegistry:
    client = MCPClient(config)
    await client.start()
    registry = ToolRegistry()
    for tool_schema in await client.list_tools():
        registry.register(MCPTool(client, tool_schema))
    return registry
```

`BubblewrapSandbox` (Linux only) runs the MCP subprocess inside a bubblewrap
container with filesystem restrictions defined by `SandboxConfig`.

---

## Code Style

Same as civitas core — `ruff` for lint and format, mypy strict, 100-char lines,
Google-style docstrings, `from __future__ import annotations` at top of every module.

Plugin files may disable specific mypy rules where upstream SDKs have poor typing
(see `pyproject.toml` `[[tool.mypy.overrides]]` for the established pattern).

---

## Dependency Rules

1. civitas-contrib and fabrica may import from `civitas` freely.
2. civitas-contrib and fabrica must **never** import from each other.
3. civitas core must **never** import from civitas-contrib or fabrica at module top.
4. Optional SDK imports (anthropic, langfuse, etc.) must be guarded in `__init__`
   or at first use — never at module top — so `import civitas_contrib` does not
   fail when the optional extra is not installed.

```python
# Wrong — fails if anthropic is not installed
import anthropic

# Correct — guard at class or function level
class AnthropicProvider:
    def __init__(self, ...):
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(...)
        except ImportError as exc:
            raise ImportError(
                "AnthropicProvider requires anthropic. "
                "Install it with: pip install civitas-contrib[anthropic]"
            ) from exc
```

---

## Testing

- Unit tests: `packages/<name>/tests/unit/` — no network, no API keys, mock SDK clients.
- Integration tests: `packages/<name>/tests/integration/` — require real API keys.
- Coverage target: ≥ 80% per package (integration tests excluded from CI).
- Test file names mirror source: `plugins/anthropic.py` → `tests/unit/test_anthropic.py`.

---

## Pull Request Checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format .` produces no diff
- [ ] `uv run mypy packages/<name>/src/` passes
- [ ] Unit tests pass
- [ ] New provider registered in `civitas/plugins/loader.py` `_BUILTINS` (if applicable)
- [ ] Optional import properly guarded
- [ ] No API keys or secrets committed
- [ ] AGENTS.md updated if workspace layout or conventions changed
