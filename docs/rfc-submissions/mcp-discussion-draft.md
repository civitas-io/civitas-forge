# MCP Discussion submission draft — SUPERSEDED, never submitted

**Target:** https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/new
**Category:** Ideas / RFC

> **Superseded.** This entire draft is built on RFC 0001's original
> `find_tools`-as-headline framing, which has since been reversed at
> [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) — code-mode
> (tools-as-code, sandboxed execution) is the validated headline mechanism;
> `find_tools`/`find()` is the fallback. This draft was never actually
> submitted to MCP Discussions (see RFC 0001's own updated status), so there
> is no external audience to correct — kept here as a historical record of
> the original idea, not as something to revise and send. If a real
> MCP-facing submission is ever warranted, it should be written fresh
> against the current design, not patched from this draft.

---

**Title:** RFC: Selective tool retrieval — exposing `find_tools` as a standard interface above `list_tools`

---

**Body:**

## Problem

MCP's `list_tools` solves discovery from a single server — but LLM clients still receive *all* tool schemas on every call. As tool sets grow this creates three compounding problems:

1. **Token cost scales linearly.** 50 tools × ~300 tokens/schema = 15,000 tokens of overhead per call, before any user message.
2. **Selection accuracy degrades** beyond ~20–30 tools. LLM benchmarks consistently show this.
3. **Context window ceiling.** Enterprise integrations with 200+ tools cannot physically fit all schemas alongside conversation history.

## Proposal

A standard interface for a **tool retrieval gateway** that sits above MCP:

```
LLM (sees only find_tools)
      ↓
Tool Retrieval Gateway        ← this RFC
      ↓
MCP list_tools / call_tool    ← existing MCP protocol
      ↓
Tool servers
```

The gateway exposes a single `find_tools(query)` meta-tool to the LLM. The LLM retrieves only the schemas it needs, on demand:

```
Turn 1: LLM calls find_tools("send a slack message")
        Gateway returns: [send_slack_message schema]

Turn 2: LLM calls send_slack_message(channel="#general", text="...")
        Gateway executes via MCP, returns result
```

For tasks using 1–3 tools (the vast majority), this saves ~14,000 tokens per call compared to passing all schemas upfront.

## The proposed interface

A compliant gateway MUST expose:

```json
{
  "name": "find_tools",
  "description": "Search for available tools by capability. Returns matching tool schemas.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "limit": { "type": "integer", "default": 5 }
    },
    "required": ["query"]
  }
}
```

When a gateway exposes itself via MCP, `list_tools` returns only `[find_tools]`. `call_tool` handles both retrieval calls and direct tool execution.

This makes the interface composable: any MCP-compatible host gains selective retrieval by pointing at a compliant gateway — no SDK changes required.

## Full RFC

The complete specification — interface requirements, backend options (keyword/embedding), session caching, circuit breakers, MCP compatibility, and open questions — is here:

https://github.com/civitas-io/civitas-forge/blob/main/rfcs/0001-tool-retrieval.md

[Fabrica](https://github.com/civitas-io/civitas-forge) is the reference implementation (pre-alpha).

## Questions for this community

1. Is this a concern the MCP spec itself should address, or is it intentionally left to gateway implementations?
2. Should MCP define a standard capability advertisement for "this server supports selective retrieval"?
3. Are there existing implementations in the ecosystem I should be aware of?

Happy to iterate on the RFC based on feedback here.
