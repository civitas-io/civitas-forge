# AGENTS.md

**Workspace:** `civitas-io/civitas-contrib` | **Python:** ≥ 3.12

This file guides AI coding agents (Claude Code, Cursor, Codex, Gemini CLI) working on
this codebase. Read it fully before writing any code.

Cross-cutting context (repo boundaries, positioning, roadmap) lives in the private
`civitas-io/context` repo — clone it alongside this one for full picture.

---

## Project Overview

`civitas-contrib` is a **uv workspace monorepo** containing one distributable package:

| Package | Import | PyPI | Purpose |
|---|---|---|---|
| `civitas-contrib` | `civitas_contrib` | `pip install civitas-contrib` | Provider plugins, framework adapters, driver-backed state/span stores, eval exporters |

Depends on `civitas>=0.11.0` (one-way). Never imported by civitas core.

This is the fast-iteration layer. civitas core is deliberately conservative; this
package is where integrations live and where breaking changes from upstream SDKs
(Anthropic, OpenAI, LangGraph, etc.) are absorbed.

**Note on scope**: this repo used to also host a `fabrica` package (an MCP tools
gateway). It outgrew this repo and became its own platform pillar,
[`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) (`pip install
fabrica-context`) — the real code was migrated there (with real improvements:
`BubblewrapSandbox` replaced by cross-platform `srt`) and the package has been
removed from this repo. `docs/design/fabrica.md` and `rfcs/0001-tool-retrieval.md`
remain as the historical design record, both marked superseded.

---

## Org Structure

Five real projects as of the `civitas-io/context` repo's ADR-003 (2026-08-22),
superseding the earlier three-repo picture:

| Repo | Import | Contains |
|---|---|---|
| `civitas-io/python-civitas` | `civitas` | Core runtime — process, supervisor, message bus, transport |
| `civitas-io/civitas-contrib` | `civitas_contrib` | This repo — integrations, narrower in scope now that Fabrica has its own repo |
| `civitas-io/presidium` | `presidium`, `presidium-contrib` | Governance — policy, registry, audit |
| `civitas-io/fabrica` | `fabrica` (PyPI: `fabrica-context`) | Context layer — tools-as-code, sandboxed execution, skills, memory, prompts |
| `civitas-io/prx`, `civitas-io/tessera` | — | Standalone ecosystem tools, not platform pillars |

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
        py.typed
        __init__.py
        plugins/
          __init__.py
          anthropic.py               # AnthropicProvider
          openai.py                  # OpenAIProvider
          gemini.py                  # GeminiProvider
          mistral.py                 # MistralProvider
          litellm.py                 # LiteLLMProvider — placeholder, raises NotImplementedError
          otel.py                    # OTEL helper functions (create_test_tracer) — not a class exporter
          sqlite_store.py            # deprecating re-export shim -> civitas.plugins.sqlite_store
          postgres_store.py          # PostgresStateStore
          postgres_span_store.py     # PostgresSpanStore
          mysql_store.py             # MySQLStateStore
          mysql_span_store.py        # MySQLSpanStore
        adapters/
          __init__.py
          langgraph.py               # LangGraphAgent
          openai.py                  # OpenAIAgent
          crewai.py                  # CrewAIAgent — placeholder, raises NotImplementedError
        eval/
          __init__.py
          exporters.py               # ArizeExporter, BraintrustExporter,
                                     #   FiddlerExporter, LangfuseExporter, LangSmithExporter
      tests/
        unit/                        # mocked SDK clients, no network — anthropic/openai covered
        test_postgres_backends.py    # real Postgres via testcontainers
        test_mysql_backends.py       # real MySQL via testcontainers
  docs/
  rfcs/
```

---

## Install

```bash
pip install civitas-contrib                  # base (requires civitas)
pip install civitas-contrib[anthropic]       # + Anthropic Claude
pip install civitas-contrib[openai]          # + OpenAI GPT-4o / o-series + Agents SDK + OpenAI-compatible endpoints
pip install civitas-contrib[gemini]          # + Google Gemini
pip install civitas-contrib[mistral]         # + Mistral
pip install civitas-contrib[langgraph]       # + LangGraph adapter
pip install civitas-contrib[postgres]        # + PostgreSQL state/span store (asyncpg)
pip install civitas-contrib[mysql]           # + MySQL state/span store (aiomysql)
pip install civitas-contrib[otel]            # + OTEL test-tracer helpers
pip install civitas-contrib[langfuse]        # + Langfuse eval exporter
pip install civitas-contrib[braintrust]      # + Braintrust eval exporter
pip install civitas-contrib[langsmith]       # + LangSmith eval exporter
pip install civitas-contrib[arize]           # + Arize eval exporter
pip install civitas-contrib[fiddler]         # + Fiddler eval exporter (eval.exporters.FiddlerExporter)
```

There is no `[litellm]` extra — `plugins.litellm.LiteLLMProvider` is a `NotImplementedError`
placeholder that doesn't touch the `litellm` SDK yet, so no extra is declared for it (same
pattern as `adapters.crewai.CrewAIAgent`).

---

## Quick Import Reference

```python
# Model providers
from civitas_contrib.plugins.anthropic import AnthropicProvider
from civitas_contrib.plugins.openai import OpenAIProvider
from civitas_contrib.plugins.gemini import GeminiProvider
from civitas_contrib.plugins.mistral import MistralProvider
# from civitas_contrib.plugins.litellm import LiteLLMProvider  # raises NotImplementedError

# State/span stores
from civitas_contrib.plugins.postgres_store import PostgresStateStore
from civitas_contrib.plugins.postgres_span_store import PostgresSpanStore
from civitas_contrib.plugins.mysql_store import MySQLStateStore
from civitas_contrib.plugins.mysql_span_store import MySQLSpanStore

# Framework adapters
from civitas_contrib.adapters.langgraph import LangGraphAgent
from civitas_contrib.adapters.openai import OpenAIAgent
# from civitas_contrib.adapters.crewai import CrewAIAgent  # raises NotImplementedError

# Eval exporters
from civitas_contrib.eval.exporters import (
    ArizeExporter,
    BraintrustExporter,
    FiddlerExporter,
    LangfuseExporter,
    LangSmithExporter,
)
```

`OpenAIProvider` also covers any OpenAI-compatible endpoint via `base_url=` — Ollama, a
self-hosted deployment, or a third-party OpenAI-compatible API — no separate provider class
exists or is needed for those.

---

## Environment Setup

This workspace uses **`uv`** with workspace support.

```bash
# Install uv if not present
curl -Ls https://astral.sh/uv/install.sh | sh

# Sync the workspace
uv sync --package civitas-contrib --all-extras

# Run tests
uv run --package civitas-contrib pytest packages/civitas-contrib/tests/
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
| Sync | `uv sync --package civitas-contrib --all-extras` |
| Run tests | `uv run --package civitas-contrib pytest packages/civitas-contrib/tests/` |
| Lint all | `uv run ruff check packages/` |
| Format all | `uv run ruff format packages/` |
| Type-check | `uv run mypy packages/civitas-contrib/src/` |

Run before finishing any task:

```bash
uv run ruff check packages/ && uv run ruff format --check packages/ && uv run pytest packages/civitas-contrib/tests/
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
- Guard the SDK import with try/except at module level (see `plugins/anthropic.py`'s
  `_HAS_ANTHROPIC` pattern) so `import civitas_contrib.plugins.<x>` never fails when the
  extra isn't installed — only constructing the provider should raise.
- Write real unit tests with the SDK client mocked (`unittest.mock.AsyncMock` on the
  client's own call method) — see `tests/unit/test_anthropic.py`/`test_openai.py` for the
  established pattern. Not implemented yet? Raise `NotImplementedError` on `__init__` with a
  clear message and a link to track progress (see `plugins/litellm.py`/`adapters/crewai.py`) —
  do not declare an extra for a provider with no real code behind it.

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

## Code Style

Same as civitas core — `ruff` for lint and format, mypy strict, 100-char lines,
Google-style docstrings, `from __future__ import annotations` at top of every module.

Plugin files may disable specific mypy rules where upstream SDKs have poor typing —
see the root `pyproject.toml`'s `[[tool.mypy.overrides]]` blocks for the established,
per-optional-dependency pattern (mirrors `civitas-io/python-civitas`'s own root
`pyproject.toml` exactly).

---

## Dependency Rules

1. civitas-contrib may import from `civitas` freely.
2. civitas core must **never** import from civitas-contrib at module top.
3. Optional SDK imports (anthropic, openai, langfuse, etc.) must be guarded in `__init__`
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

- Unit tests: `packages/civitas-contrib/tests/unit/` — no network, no API keys, mock SDK clients.
- Integration tests: `packages/civitas-contrib/tests/test_postgres_backends.py` /
  `test_mysql_backends.py` — real Postgres/MySQL via `testcontainers`, require Docker.
- Test file names mirror source: `plugins/anthropic.py` → `tests/unit/test_anthropic.py`.
- **Real, current gap, not hidden**: `plugins/gemini.py`, `plugins/mistral.py`,
  `adapters/langgraph.py`, `adapters/openai.py`, and `eval/exporters.py` have real,
  working implementations but no unit tests yet — only `plugins/anthropic.py` and
  `plugins/openai.py` are unit-tested so far. Worth closing next, not assumed covered.

---

## Pull Request Checklist

- [ ] `uv run ruff check packages/` passes
- [ ] `uv run ruff format --check packages/` produces no diff
- [ ] `uv run mypy packages/civitas-contrib/src/` passes
- [ ] Unit tests pass
- [ ] New provider registered in `civitas/plugins/loader.py` `_BUILTINS` (if applicable)
- [ ] Optional import properly guarded
- [ ] No API keys or secrets committed
- [ ] AGENTS.md updated if workspace layout or conventions changed
