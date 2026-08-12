# Design: Fabrica — SUPERSEDED

**Status:** Superseded by [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica)
**Originally written:** 2026-04 · **Marked superseded:** 2026-08

---

## This document describes an abandoned direction. Do not implement against it.

The design below proposed Fabrica as a single `find_tools(query)` meta-tool —
a selective tool-retrieval gateway, nothing more. That framing has been
**reversed**, not just extended: a full discovery→design→validation cycle in
[`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) found that
**code-mode (tools-as-code, sandboxed execution) is the validated headline
mechanism** — measured ~79% cheaper *and* more correct than traditional
tool-calling — and `find()` is the **fallback**, not the primary interface
this doc describes. The real design also covers memory, prompts, skills, and
both directions of MCP integration, none of which exist here at all.

**If you're looking for the real thing:**

- Repository: [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica)
- Distribution: `pip install fabrica-context` — `fabrica` (the plain name) is
  taken on PyPI by an unrelated project; the project itself is still called
  Fabrica, only the package name differs.
- Start here: [`README.md`](https://github.com/civitas-io/fabrica/blob/main/README.md),
  or [`HANDOFF.md`](https://github.com/civitas-io/fabrica/blob/main/HANDOFF.md)
  for the current implementation status.

**What actually happens to the code in `packages/fabrica/` in *this* repo**
(a real, working `MCPClient` + `BubblewrapSandbox` — not this design doc's
sketch): it migrates into `civitas-io/fabrica`, close to its current shape,
as the implementation behind that project's `MCPToolNamespace`.
`BubblewrapSandbox` specifically does **not** migrate as-is — it gets
replaced by `srt` (a cross-platform tool unifying `bwrap` on Linux and
`sandbox-exec` on macOS), since carrying over the Linux-only sandbox would
reintroduce a platform gap the real design already closed. See
[`docs/mcp-integration.md`](https://github.com/civitas-io/fabrica/blob/main/docs/mcp-integration.md)
in the new repo for the full reasoning.

This document is kept, unmodified below the line, as a historical record of
where the idea started — not as a spec to build against.

---

*The original content previously below this point (architecture diagram,
`ToolSource`/`ToolIndex` interfaces, `find_tools` meta-tool schema, request
flow, Civitas integration sketch, MCP server interface, circuit breaker,
implementation phases, open questions, acceptance criteria) has been removed
from this file to avoid it being mistaken for a current spec. It remains
available in this repository's git history at any commit before this one.*
