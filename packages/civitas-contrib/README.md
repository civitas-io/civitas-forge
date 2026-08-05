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

| Category | Modules | Extra |
|---|---|---|
| **LLM provider plugins** | `anthropic`, `openai`, `gemini`, `mistral`, `litellm`, `fiddler` | matching extra (`[openai]`, …) |
| **Framework adapters** | `adapters.crewai`, `adapters.langgraph`, `adapters.openai` | `[langgraph]`, … |
| **State stores (driver-backed)** | `plugins.postgres_store` | `[postgres]` |
| **Exporters** | `plugins.otel`, `eval.exporters` | `[otel]`, `[arize]`, `[langfuse]`, `[braintrust]`, `[langsmith]` |

## Moved to core

`SQLiteStateStore` moved to **core civitas** (`civitas.plugins.sqlite_store`) in civitas v0.11.0 — SQLite is stdlib, so it adds no third-party dependency and belongs in core. The old
`civitas_contrib.plugins.sqlite_store` import path still works via a deprecating re-export shim; update to:

```python
from civitas.plugins.sqlite_store import SQLiteStateStore
```

YAML `type: sqlite` state stores already resolve to core and need no change.

## License

Apache 2.0.
