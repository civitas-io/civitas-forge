"""LiteLLMProvider — not yet implemented."""

from __future__ import annotations


class LiteLLMProvider:
    """Placeholder — LiteLLM provider is not yet implemented.

    Raises NotImplementedError on instantiation so callers get a clear
    message rather than an import-time AttributeError.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "LiteLLMProvider is not yet implemented. "
            "Track progress at https://github.com/civitas-io/civitas-contrib/issues."
        )
