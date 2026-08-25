# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [civitas-contrib 0.2.0] - 2026-08-25

**First real PyPI release.** `civitas-contrib` has depended on a local editable-path checkout
since it started; a real downstream consumer (Candid, a multi-tenant job-application automation
product built on Civitas, depending on `civitas-contrib[anthropic,openai]` for exactly two
imports — `AnthropicProvider`/`OpenAIProvider`, the latter also covering the Ollama and
self-hosted OpenAI-compatible-endpoint cases via `base_url=`) surfaced this as a real blocker:
nothing outside a sibling checkout of this repo could install it as a normal dependency.

### Fixed

- **Workspace root `pyproject.toml` had no `[project]` table or `requires-python` constraint** —
  `uv sync` failed outright, resolving for a hypothetical future Python split marker where
  `civitas>=0.11.0` had no satisfying release. Fixed to mirror `civitas-io/presidium`'s own
  established workspace-root pattern exactly (`requires-python = ">=3.12"`, a
  `[tool.hatch.build.targets.wheel] only-include = ["_nonexistent"]` non-distributed root).
- **`plugins.litellm.LiteLLMProvider` did not exist** — the module was a 3-line docstring-only
  stub, but `AGENTS.md`'s own Quick Import Reference documented
  `from civitas_contrib.plugins.litellm import LiteLLMProvider` as a working import (confirmed:
  it raised `ImportError`). Fixed to a real, honest placeholder matching
  `adapters.crewai.CrewAIAgent`'s established pattern — raises `NotImplementedError` on
  `__init__` with a link to track progress. The `[litellm]` extra was removed (no real code
  needs the `litellm` package yet — same reasoning `crewai` never had an extra for it).
- **`plugins.fiddler` was a dead, unreferenced placeholder module for a different,
  never-built integration** — confusingly distinct from the real, working
  `eval.exporters.FiddlerExporter` that actually backs the `[fiddler]` extra. Deleted; docs
  corrected to point at `eval.exporters.FiddlerExporter` as the one real Fiddler surface.
- **mypy had never been run against this package in CI** — only `packages/fabrica/` was in the
  lint job. Running it directly surfaced 14 real `import-not-found`/`import-untyped` errors for
  optional third-party SDKs with no override configured. Added the same
  `ignore_missing_imports` override pattern already established in
  `civitas-io/python-civitas`'s own root `pyproject.toml`.
- **CI's test matrix only ever ran `packages/fabrica`'s tests** — the real, live package had
  zero CI coverage. Fixed to test `civitas-contrib` instead.

### Added

- **Real unit tests for `AnthropicProvider`/`OpenAIProvider`** (`tests/unit/`) — mocked SDK
  clients, no network. Covers cost computation (known model, versioned-model-id prefix match,
  unknown model returns `None` not `0`), tool-call extraction, default-model fallback, and the
  `ImportError` guard when the optional SDK isn't installed. Every other provider/adapter/
  exporter module has real, working code but is not yet unit-tested — named honestly in
  `AGENTS.md`'s own Testing section, not silently implied covered.
- `py.typed` marker (previously missing).
- `LICENSE` file at repo root (previously declared in metadata, Apache-2.0, but not actually
  present — same gap every sibling repo hit and fixed before its own first release).
- `.github/workflows/publish.yml` — OIDC Trusted Publishing on `v*.*.*` tag push, copied from
  the identical, already-proven pattern in `civitas-io/fabrica`/`civitas-io/presidium`.

### Removed

- **The `fabrica` package** (`packages/fabrica/`) — fully superseded by
  [`civitas-io/fabrica`](https://github.com/civitas-io/fabrica) (`pip install fabrica-context`).
  Confirmed via a repo-wide grep that nothing outside its own tests ever imported it. The
  historical design record (`docs/design/fabrica.md`, `rfcs/0001-tool-retrieval.md`) is kept,
  already marked superseded with pointers to the real repo.

### Verified

Real fresh-venv install from a locally built wheel (`pip install
civitas-contrib[anthropic,openai]`) — base import, both plugin imports, the `LiteLLMProvider`/
`CrewAIAgent` stubs raising cleanly, `py.typed` present in the wheel, `plugins.fiddler` genuinely
gone. `ruff check`/`ruff format --check`/`mypy --strict` clean; full test suite passes.
