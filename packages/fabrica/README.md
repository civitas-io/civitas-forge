# Fabrica

**Selective tool retrieval gateway for LLM systems.**

Part of the [Civitas](https://github.com/civitas-io/python-civitas) platform.

---

Instead of passing all tool schemas to every LLM call — expensive in tokens, degrading in accuracy beyond ~20 tools — Fabrica exposes a single `find_tools(query)` meta-tool. The LLM retrieves only the schemas it needs, on demand.

```
Without Fabrica:  LLM call = messages + [tool_1, tool_2, ... tool_50]  # O(N) tokens
With Fabrica:     LLM call = messages + [find_tools]                   # O(1) tokens
```

See [RFC 0001](../../rfcs/0001-tool-retrieval.md) for the full problem statement and interface specification.

## Status

Pre-alpha — design and specification phase. Not yet ready for use.

## Install

```bash
pip install fabrica                  # core
pip install fabrica[search]          # embedding-based retrieval
pip install fabrica[mcp]             # MCP server interface
```

## License

Apache 2.0.
