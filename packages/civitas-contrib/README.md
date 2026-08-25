# civitas-contrib

**Community integrations and extras for [Civitas](https://github.com/civitas-io/python-civitas) — the production runtime for Python agents.**

Everything here needs a third-party runtime dependency (a vendor / driver / framework SDK) or integrates with a specific external product. Core mechanism, protocols, and zero-dependency implementations live in `civitas` itself; `civitas-contrib` holds the batteries that pull in someone else's package. (See the contrib boundary rule in the core repo's `docs/design/spanstore-and-contrib-boundary.md`.)

## Install

```bash
pip install civitas-contrib            # base (pulls in civitas)
pip install "civitas-contrib[openai]"  # + a specific integration's deps
```

Each integration's third-party dependency is an **extra**, so you only install what you use.

## What's inside

| Category | Modules | Extra | Status |
|---|---|---|---|
| **LLM provider plugins** | `plugins.anthropic`, `plugins.openai`, `plugins.gemini`, `plugins.mistral` | matching extra (`[anthropic]`, `[openai]`, `[gemini]`, `[mistral]`) | Real, unit-tested (`anthropic`/`openai`) |
| **Framework adapters** | `adapters.langgraph`, `adapters.openai` | `[langgraph]`, `[openai]` | Real |
| **State stores (driver-backed)** | `plugins.postgres_store`, `plugins.mysql_store` | `[postgres]`, `[mysql]` | Real, integration-tested against real Postgres/MySQL |
| **Span stores (driver-backed)** | `plugins.postgres_span_store`, `plugins.mysql_span_store` | `[postgres]`, `[mysql]` | Real, integration-tested against real Postgres/MySQL |
| **Exporters** | `plugins.otel`, `eval.exporters` (`ArizeExporter`, `LangfuseExporter`, `BraintrustExporter`, `LangSmithExporter`, `FiddlerExporter`) | `[otel]`, `[arize]`, `[langfuse]`, `[braintrust]`, `[langsmith]`, `[fiddler]` | Real |

**Not yet implemented, honest placeholders only** — importable, but raise `NotImplementedError` on
instantiation with a link to track progress, matching the same pattern for both:

- `adapters.crewai.CrewAIAgent` — no extra needed (doesn't touch the `crewai` SDK yet).
- `plugins.litellm.LiteLLMProvider` — no extra needed (doesn't touch the `litellm` SDK yet).

There is no `civitas_contrib.plugins.fiddler` module — `[fiddler]` backs `eval.exporters.FiddlerExporter` (an eval exporter), not a model provider.

The **span stores** implement civitas's `SpanStore` protocol (durable, queryable telemetry) and are usable as `plugins.exporters` of `type: postgres` / `type: mysql`. The **state stores** implement `StateStore` (`type: postgres` / `type: mysql` under `plugins.state`). Both reuse core's public `civitas.observability.normalize_span` and match core's `SQLiteSpanStore` query results exactly.

## Moved to core

`SQLiteStateStore` moved to **core civitas** (`civitas.plugins.sqlite_store`) in civitas v0.11.0 — SQLite is stdlib, so it adds no third-party dependency and belongs in core. The old
`civitas_contrib.plugins.sqlite_store` import path still works via a deprecating re-export shim; update to:

```python
from civitas.plugins.sqlite_store import SQLiteStateStore
```

YAML `type: sqlite` state stores already resolve to core and need no change.

## License

Apache 2.0.
