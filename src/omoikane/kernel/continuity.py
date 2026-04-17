"""Append-only continuity ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..common import canonical_json, sha256_text, utc_now_iso


@dataclass
class ContinuityLedgerEntry:
    """Single append-only ledger event."""

    cursor: int
    prev_hash: str
    identity_id: str
    event_type: str
    payload: Dict[str, Any]
    actor: str
    signatures: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)
    entry_hash: str = ""

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "actor": self.actor,
            "created_at": self.created_at,
            "cursor": self.cursor,
            "event_type": self.event_type,
            "identity_id": self.identity_id,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
            "signatures": self.signatures,
        }


class ContinuityLedger:
    """Reference append-only continuity ledger."""

    def __init__(self) -> None:
        self._entries: List[ContinuityLedgerEntry] = []

    def append(
        self,
        identity_id: str,
        event_type: str,
        payload: Dict[str, Any],
        actor: str,
        signatures: Optional[List[str]] = None,
    ) -> ContinuityLedgerEntry:
        entry = ContinuityLedgerEntry(
            cursor=len(self._entries),
            prev_hash=self._entries[-1].entry_hash if self._entries else "GENESIS",
            identity_id=identity_id,
            event_type=event_type,
            payload=payload,
            actor=actor,
            signatures=signatures or [],
        )
        entry.entry_hash = sha256_text(canonical_json(entry.canonical_payload()))
        self._entries.append(entry)
        return entry

    def entries(self) -> List[ContinuityLedgerEntry]:
        return list(self._entries)

    def verify(self) -> Dict[str, Any]:
        errors: List[str] = []
        previous_hash = "GENESIS"

        for index, entry in enumerate(self._entries):
            if entry.cursor != index:
                errors.append(f"cursor mismatch at {index}")
            if entry.prev_hash != previous_hash:
                errors.append(f"prev_hash mismatch at {index}")
            expected_hash = sha256_text(canonical_json(entry.canonical_payload()))
            if entry.entry_hash != expected_hash:
                errors.append(f"entry_hash mismatch at {index}")
            previous_hash = entry.entry_hash

        return {
            "ok": not errors,
            "entry_count": len(self._entries),
            "errors": errors,
        }

    def snapshot(self) -> List[Dict[str, Any]]:
        return [asdict(entry) for entry in self._entries]

