"""Identity lifecycle management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
    pause_state: Optional["PauseState"] = None


@dataclass
class PauseState:
    """Most recent bounded pause/resume cycle for one identity."""

    paused_at: str
    pause_reason: str
    pause_authority: str
    council_resolution_ref: Optional[str] = None
    resumed_at: Optional[str] = None
    resume_self_proof_ref: Optional[str] = None


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

    def create_collective(
        self,
        member_ids: List[str],
        consent_proof: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        if len(member_ids) < 2:
            raise ValueError("collective identity requires at least two member identities")

        normalized_members: List[str] = []
        for member_id in member_ids:
            member = self.get(member_id)
            if member.status != "active":
                raise ValueError("cannot form a collective from a non-active identity")
            if member.identity_id not in normalized_members:
                normalized_members.append(member.identity_id)

        if len(normalized_members) < 2:
            raise ValueError("collective identity requires two unique active member identities")

        collective_id = new_id("collective")
        collective_metadata = {
            "identity_kind": "collective",
            "member_ids": ",".join(normalized_members),
            **(metadata or {}),
        }
        record = IdentityRecord(
            identity_id=collective_id,
            lineage_id=collective_id,
            consent_proof=consent_proof,
            created_at=utc_now_iso(),
            metadata=collective_metadata,
        )
        self._records[collective_id] = record
        return record

    def pause(
        self,
        identity_id: str,
        *,
        requested_by: str,
        reason: str,
        council_resolution_ref: Optional[str] = None,
    ) -> IdentityRecord:
        normalized_requester = requested_by.strip()
        if normalized_requester not in {"self", "council"}:
            raise ValueError("requested_by must be self or council")
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError("reason is required for pause")
        normalized_resolution_ref = (
            council_resolution_ref.strip() if isinstance(council_resolution_ref, str) else None
        )
        if normalized_requester == "council" and not normalized_resolution_ref:
            raise PermissionError("council pause requires council_resolution_ref")
        if normalized_requester == "self" and normalized_resolution_ref:
            raise ValueError("self pause must not include council_resolution_ref")

        record = self.get(identity_id)
        if record.status != "active":
            raise ValueError("can only pause an active identity")

        record.status = "paused"
        record.pause_state = PauseState(
            paused_at=utc_now_iso(),
            pause_reason=normalized_reason,
            pause_authority=normalized_requester,
            council_resolution_ref=normalized_resolution_ref,
        )
        return record

    def resume(
        self,
        identity_id: str,
        *,
        self_proof: str,
    ) -> IdentityRecord:
        normalized_self_proof = self_proof.strip()
        if not normalized_self_proof:
            raise PermissionError("self proof is required for resume")

        record = self.get(identity_id)
        if record.status != "paused":
            raise ValueError("can only resume a paused identity")
        if record.pause_state is None:
            raise ValueError("paused identity must carry pause_state metadata")

        record.status = "active"
        record.pause_state.resumed_at = utc_now_iso()
        record.pause_state.resume_self_proof_ref = normalized_self_proof
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
                "pause_state": asdict(record.pause_state) if record.pause_state else None,
            }
            for record in self._records.values()
        ]
