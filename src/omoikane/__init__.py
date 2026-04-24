"""Reference runtime for OmoikaneOS."""

from __future__ import annotations

from typing import Any

__all__ = ["OmoikaneReferenceOS"]


def __getattr__(name: str) -> Any:
    if name == "OmoikaneReferenceOS":
        from .reference_os import OmoikaneReferenceOS

        return OmoikaneReferenceOS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
