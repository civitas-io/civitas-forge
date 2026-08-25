# civitas-contrib

**Community integrations and extras for [Civitas](https://github.com/civitas-io/python-civitas) — the production runtime for Python agents.**

[![PyPI](https://img.shields.io/pypi/v/civitas-contrib)](https://pypi.org/project/civitas-contrib/)
[![GitHub release](https://img.shields.io/github/v/release/civitas-io/civitas-contrib)](https://github.com/civitas-io/civitas-contrib/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

```bash
pip install civitas-contrib
```

---

## What this is

Everything here needs a third-party runtime dependency (a vendor SDK, a database driver, a
framework) or integrates with a specific external product. Core mechanism, protocols, and
zero-dependency implementations live in `civitas` itself; `civitas-contrib` holds the batteries
that pull in someone else's package — model provider plugins, framework adapters, driver-backed
state/span stores, and eval exporters. See [`packages/civitas-contrib/README.md`](packages/civitas-contrib/README.md)
for the full, current, real inventory (what's implemented vs. an honest not-yet-built placeholder).

Lower contribution bar, faster iteration than `civitas` core — this is where integrations land
and where breaking changes from upstream SDKs (Anthropic, OpenAI, LangGraph, etc.) are absorbed.

## Packages

| Package | PyPI | Description |
|---------|------|-------------|
| [civitas-contrib](packages/civitas-contrib/) | [`civitas-contrib`](https://pypi.org/project/civitas-contrib/) | Provider plugins, framework adapters, driver-backed state/span stores, eval exporters — see the package's own README for the full inventory |

## About the old `fabrica` package

This repo used to also contain a `fabrica` package (an MCP tools gateway: `MCPClient`,
`MCPTool`, `BubblewrapSandbox`). It outgrew this repo and became its own platform pillar —
see [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) (`pip install fabrica-context`).
That code has been fully migrated (with real improvements: `BubblewrapSandbox` replaced by
cross-platform `srt`, `MCPTool` replaced by an async-factory `MCPToolNamespace`) and the package
has been removed from this repo — nothing here depends on it. See
[`docs/design/fabrica.md`](docs/design/fabrica.md) and [`rfcs/0001-tool-retrieval.md`](rfcs/0001-tool-retrieval.md)
for the historical design record, both marked superseded with pointers to the real repo.

## RFCs

| RFC | Title | Status |
|-----|-------|--------|
| [0001](rfcs/0001-tool-retrieval.md) | Selective Tool Retrieval for LLM Systems | Superseded — see [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) |

## Structure

```
civitas-contrib/
├── packages/
│   └── civitas-contrib/   # pip install civitas-contrib
├── rfcs/                  # public interface proposals (historical)
└── docs/                  # platform-level documentation (historical fabrica design record)
```

## License

Apache 2.0.
