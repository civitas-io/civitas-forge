# civitas-forge

**Platform products built on [Civitas](https://github.com/civitas-io/python-civitas) — the production runtime for Python agents.**

---

## Packages

| Package | PyPI | Description |
|---------|------|-------------|
| [fabrica](packages/fabrica/) | superseded — see [package README](packages/fabrica/) | Superseded by [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) (`pip install fabrica-context`) — the real design is code-mode execution + a shared retrieval engine + memory/prompts/MCP, not just tool retrieval. This package's real code (`MCPClient`, `BubblewrapSandbox`) is migrating there. |

*More packages coming — prompt library, skills gateway, LLM gateway.*

## RFCs

| RFC | Title | Status |
|-----|-------|--------|
| [0001](rfcs/0001-tool-retrieval.md) | Selective Tool Retrieval for LLM Systems | Superseded |

## Structure

```
civitas-forge/
├── packages/
│   └── fabrica/        # superseded -- see packages/fabrica/README.md
├── rfcs/               # public interface proposals
└── docs/               # platform-level documentation
```

## License

Apache 2.0.
