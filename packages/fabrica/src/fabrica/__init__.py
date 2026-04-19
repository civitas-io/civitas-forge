"""Fabrica — selective tool retrieval gateway for LLM systems.

Instead of passing all tool schemas to every LLM call, Fabrica exposes a single
find_tools(query) meta-tool. The LLM retrieves only the schemas it needs, on demand.

See RFC 0001: https://github.com/civitas-io/civitas-forge/blob/main/rfcs/0001-tool-retrieval.md
"""

__version__ = "0.1.0"
