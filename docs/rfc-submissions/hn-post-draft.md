# Hacker News submission draft

**Target:** https://news.ycombinator.com/submit
**Type:** Show HN

---

**Title:** Show HN: RFC – Selective tool retrieval for LLMs (the find_tools problem)

---

**URL:** https://github.com/civitas-io/civitas-forge/blob/main/rfcs/0001-tool-retrieval.md

---

**Comment (optional, posted with the link):**

Every LLM call with tools pays token cost for the entire tool schema list — regardless of which tools the model actually uses. At 50 tools (~300 tokens/schema avg) that's 15,000 tokens of overhead per call. Beyond ~20–30 tools, selection accuracy also degrades measurably.

This RFC proposes a standard interface for a tool retrieval gateway: instead of N tool schemas, the LLM receives one `find_tools(query)` meta-tool and retrieves only what it needs.

The key design question is whether this belongs in MCP itself (as an extension to `list_tools`) or as a convention at the application layer. I've posted the same RFC to the MCP GitHub Discussions.

Reference implementation (pre-alpha): https://github.com/civitas-io/civitas-forge
