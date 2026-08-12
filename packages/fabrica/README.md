# Fabrica (this package) — SUPERSEDED

**Status:** Superseded by [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica)
(`pip install fabrica-context`) · **Marked superseded:** 2026-08

---

This package described itself as a *"selective tool retrieval gateway"* — a
single `find_tools(query)` meta-tool, nothing more. That framing is
superseded: the real Fabrica is a full context layer (tools-as-code
code-mode execution, a shared retrieval engine, memory, prompts, and both
directions of MCP integration), designed and built at
[`civitas-io/fabrica`](https://github.com/civitas-io/fabrica). `pip install
fabrica` never actually worked as advertised below — `fabrica` is taken on
PyPI by an unrelated project; the real distribution name is
`fabrica-context`.

**The code inside this package is not abandoned** — `src/fabrica/mcp/`
(a working MCP client: stdio/SSE transport, `list_tools`/`call_tool`) and
`src/fabrica/sandbox/` (`BubblewrapSandbox`, Linux namespace isolation for
the MCP server's own subprocess) are real, validated prior work. They're
migrating into `civitas-io/fabrica` as the implementation behind that
project's `MCPToolNamespace` — see
[`docs/mcp-integration.md`](https://github.com/civitas-io/fabrica/blob/main/docs/mcp-integration.md)
there. `BubblewrapSandbox` specifically is being replaced by `srt`
(cross-platform: `bwrap` on Linux, `sandbox-exec` on macOS) during that
migration, not carried over Linux-only.

## Where to go instead

- Repository: [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica)
- Install: `pip install fabrica-context`
- Current status: [`HANDOFF.md`](https://github.com/civitas-io/fabrica/blob/main/HANDOFF.md)

## License

Apache 2.0.
