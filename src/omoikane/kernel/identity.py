"""Identity lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..common import new_id, utc_now_iso


@dataclass
class ForkApprovals:
    """Triple-signature approval set required for a fork."""

    self_signed: bool
    third_party_signed: bool
    legal_signed: bool

    def is_complete(self) -> bool:
        return self.self_signed and self.third_party_signed and self.legal_signed


@dataclass
class IdentityRecord:
    """Tracked identity in the reference runtime."""

    identity_id: str
    lineage_id: str
    consent_proof: str
    created_at: str
    status: str = "active"
    parent_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    terminated_at: Optional[str] = None


class IdentityRegistry:
    """Reference implementation of the L1 IdentityRegistry."""

    def __init__(self) -> None:
        self._records: Dict[str, IdentityRecord] = {}

    def create(
        self,
        human_consent_proof: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        identity_id = new_id("id")
        record = IdentityRecord(
            identity_id=identity_id,
            lineage_id=identity_id,
            consent_proof=human_consent_proof,
            created_at=utc_now_iso(),
            metadata=metadata or {},
        )
        self._records[identity_id] = record
        return record

    def get(self, identity_id: str) -> IdentityRecord:
        try:
            return self._records[identity_id]
        except KeyError as exc:
            raise KeyError(f"unknown identity: {identity_id}") from exc

    def fork(
        self,
        identity_id: str,
        justification: str,
        approvals: ForkApprovals,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        parent = self.get(identity_id)
        if parent.status != "active":
            raise ValueError("cannot fork a non-active identity")
        if not approvals.is_complete():
            raise PermissionError("fork requires self, third-party, and legal approval")

        child_id = new_id("fork")
        record = IdentityRecord(
            identity_id=child_id,
            lineage_id=parent.lineage_id,
            consent_proof=justification,
            created_at=utc_now_iso(),
            parent_id=parent.identity_id,
            metadata=metadata or {},
        )
        self._records[child_id] = record
        return record

    def terminate(self, identity_id: str, self_proof: str) -> IdentityRecord:
        if not self_proof:
            raise PermissionError("self proof is required for termination")

        record = self.get(identity_id)
        record.status = "terminated"
        record.terminated_at = utc_now_iso()
        return record

    def active_records(self) -> List[IdentityRecord]:
        return [record for record in self._records.values() if record.status == "active"]

    def snapshot(self) -> List[Dict[str, Optional[str]]]:
        return [
            {
                "identity_id": record.identity_id,
                "lineage_id": record.lineage_id,
                "status": record.status,
                "parent_id": record.parent_id,
                "created_at": record.created_at,
                "terminated_at": record.terminated_at,
            }
            for record in self._records.values()
        ]

