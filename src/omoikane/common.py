"""Shared helpers for the OmoikaneOS reference runtime."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


def utc_now_iso() -> str:
    """Return an RFC3339-style UTC timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    """Create a readable identifier with a stable prefix."""
    return f"{prefix}-{uuid4().hex[:12]}"


def canonical_json(data: Dict[str, Any]) -> str:
    """Serialize a mapping deterministically for hashing."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    """Return a SHA-256 hex digest."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hmac_sha256_text(key: str, text: str) -> str:
    """Return an HMAC-SHA256 hex digest."""
    return hmac.new(key.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()
