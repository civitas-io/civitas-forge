"""Deprecated re-export shim — SQLiteStateStore moved to core civitas.

As of civitas v0.11.0 (B4), ``SQLiteStateStore`` lives in core civitas at
``civitas.plugins.sqlite_store`` — SQLite is stdlib, so a SQLite-backed store
adds no third-party runtime dependency and belongs in core under the contrib
boundary rule (see civitas ``docs/design/spanstore-and-contrib-boundary.md``).

This module re-exports it from its new home so the old import path keeps
working, and warns on import. Update to::

    from civitas.plugins.sqlite_store import SQLiteStateStore

This shim will be removed in a future civitas-contrib major release. YAML
``type: sqlite`` state stores already resolve to core and need no change.
"""

from __future__ import annotations

import warnings

from civitas.plugins.sqlite_store import SQLiteStateStore

warnings.warn(
    "civitas_contrib.plugins.sqlite_store.SQLiteStateStore has moved to core: "
    "import it from civitas.plugins.sqlite_store instead. This shim will be "
    "removed in a future civitas-contrib release.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["SQLiteStateStore"]
