"""ConsensusBus reference model for audited agent-to-agent delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

CONSENSUS_BUS_PHASES = (
    "brief",
    "opening",
    "rebuttal",
    "amendment",
    "decision",
    "gate",
    "resolve",
)
CONSENSUS_BUS_INTENTS = (
    "dispatch",
    "report",
    "vote",
    "escalate",
    "gate",
    "resolve",
)
CONSENSUS_BUS_DELIVERY_SCOPES = ("council", "agent", "broadcast")
CONSENSUS_BUS_TRANSPORT_PROFILE = "consensus-bus-only"
CONSENSUS_BUS_PHASE_ORDER = {
    phase: index for index, phase in enumerate(CONSENSUS_BUS_PHASES)
}


def _normalize_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_related_claim_ids(values: Optional[List[str]]) -> List[str]:
    normalized: List[str] = []
    for value in values or []:
        claim_id = _normalize_non_empty(value, "related_claim_ids[]")
        if claim_id not in normalized:
            normalized.append(claim_id)
    return normalized


@dataclass
class ConsensusMessage:
    """One audited bus message emitted between Council-adjacent roles."""

    message_id: str
    session_id: str
    sender_role: str
    recipient: str
    delivery_scope: str
    intent: str
    phase: str
    transport_profile: str
    payload: Union[Dict[str, Any], str]
    emitted_at: str
    related_claim_ids: List[str]
    ethics_check_id: Optional[str] = None
    signature_ref: Optional[str] = None
    message_digest: str = ""
    kind: str = "consensus_message"
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        self.message_id = _normalize_non_empty(self.message_id, "message_id")
        self.session_id = _normalize_non_empty(self.session_id, "session_id")
        self.sender_role = _normalize_non_empty(self.sender_role, "sender_role")
        self.recipient = _normalize_non_empty(self.recipient, "recipient")
        if self.delivery_scope not in CONSENSUS_BUS_DELIVERY_SCOPES:
            raise ValueError(f"unsupported delivery_scope: {self.delivery_scope}")
        if self.intent not in CONSENSUS_BUS_INTENTS:
            raise ValueError(f"unsupported intent: {self.intent}")
        if self.phase not in CONSENSUS_BUS_PHASES:
            raise ValueError(f"unsupported phase: {self.phase}")
        if self.transport_profile != CONSENSUS_BUS_TRANSPORT_PROFILE:
            raise ValueError(
                f"transport_profile must equal {CONSENSUS_BUS_TRANSPORT_PROFILE!r}"
            )
        if isinstance(self.payload, str):
            self.payload = _normalize_non_empty(self.payload, "payload")
        elif not isinstance(self.payload, dict) or not self.payload:
            raise ValueError("payload must be a non-empty object or string")
        self.emitted_at = _normalize_non_empty(self.emitted_at, "emitted_at")
        self.related_claim_ids = _normalize_related_claim_ids(self.related_claim_ids)
        if self.ethics_check_id is not None:
            self.ethics_check_id = _normalize_non_empty(
                self.ethics_check_id,
                "ethics_check_id",
            )
        if self.signature_ref is None:
            self.signature_ref = f"sig://consensus-bus/{self.message_id}"
        else:
            self.signature_ref = _normalize_non_empty(self.signature_ref, "signature_ref")
        self.message_digest = sha256_text(canonical_json(self._signable_dict()))

    def _signable_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "sender_role": self.sender_role,
            "recipient": self.recipient,
            "delivery_scope": self.delivery_scope,
            "intent": self.intent,
            "phase": self.phase,
            "transport_profile": self.transport_profile,
            "payload": self.payload,
            "related_claim_ids": list(self.related_claim_ids),
            "ethics_check_id": self.ethics_check_id,
            "signature_ref": self.signature_ref,
            "emitted_at": self.emitted_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self._signable_dict(),
            "message_digest": self.message_digest,
        }


class ConsensusBus:
    """Audited delivery path for Council, Builder, and Guardian coordination."""

    def __init__(self) -> None:
        self._messages_by_session: Dict[str, List[ConsensusMessage]] = {}
        self._blocked_direct_attempts: Dict[str, List[Dict[str, Any]]] = {}

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "transport_profile": CONSENSUS_BUS_TRANSPORT_PROFILE,
            "allowed_phases": list(CONSENSUS_BUS_PHASES),
            "allowed_intents": list(CONSENSUS_BUS_INTENTS),
            "allowed_delivery_scopes": list(CONSENSUS_BUS_DELIVERY_SCOPES),
            "direct_delivery_policy": "blocked-outside-bus",
            "audit_required": True,
        }

    def publish(
        self,
        *,
        session_id: str,
        sender_role: str,
        recipient: str,
        intent: str,
        phase: str,
        payload: Union[Dict[str, Any], str],
        related_claim_ids: Optional[List[str]] = None,
        ethics_check_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized_session_id = _normalize_non_empty(session_id, "session_id")
        delivery_scope = self._delivery_scope(recipient)
        message = ConsensusMessage(
            message_id=new_id("consensus-msg"),
            session_id=normalized_session_id,
            sender_role=sender_role,
            recipient=recipient,
            delivery_scope=delivery_scope,
            intent=_normalize_non_empty(intent, "intent"),
            phase=_normalize_non_empty(phase, "phase"),
            transport_profile=CONSENSUS_BUS_TRANSPORT_PROFILE,
            payload=payload,
            related_claim_ids=related_claim_ids or [],
            ethics_check_id=ethics_check_id,
            emitted_at=utc_now_iso(),
        )
        self._messages_by_session.setdefault(normalized_session_id, []).append(message)
        return message.to_dict()

    def reject_direct_message(
        self,
        *,
        session_id: str,
        sender_role: str,
        recipient: str,
        attempted_intent: str,
        reason: str,
    ) -> Dict[str, Any]:
        attempt = {
            "attempt_id": new_id("consensus-block"),
            "session_id": _normalize_non_empty(session_id, "session_id"),
            "sender_role": _normalize_non_empty(sender_role, "sender_role"),
            "recipient": _normalize_non_empty(recipient, "recipient"),
            "attempted_intent": _normalize_non_empty(attempted_intent, "attempted_intent"),
            "status": "blocked",
            "enforced_policy": CONSENSUS_BUS_TRANSPORT_PROFILE,
            "reason": _normalize_non_empty(reason, "reason"),
            "blocked_at": utc_now_iso(),
        }
        self._blocked_direct_attempts.setdefault(attempt["session_id"], []).append(attempt)
        return dict(attempt)

    def list_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        normalized_session_id = _normalize_non_empty(session_id, "session_id")
        return [
            message.to_dict()
            for message in self._messages_by_session.get(normalized_session_id, [])
        ]

    def audit_session(self, session_id: str) -> Dict[str, Any]:
        normalized_session_id = _normalize_non_empty(session_id, "session_id")
        messages = self._messages_by_session.get(normalized_session_id, [])
        blocked_attempts = self._blocked_direct_attempts.get(normalized_session_id, [])
        phases = [message.phase for message in messages]
        related_claim_ids = sorted(
            {
                claim_id
                for message in messages
                for claim_id in message.related_claim_ids
            }
        )
        return {
            "session_id": normalized_session_id,
            "message_count": len(messages),
            "blocked_direct_attempts": len(blocked_attempts),
            "sender_roles": sorted({message.sender_role for message in messages}),
            "delivery_scopes": sorted({message.delivery_scope for message in messages}),
            "transport_profiles": sorted({message.transport_profile for message in messages}),
            "all_transport_bus_only": all(
                message.transport_profile == CONSENSUS_BUS_TRANSPORT_PROFILE
                for message in messages
            ),
            "guardian_gate_present": any(message.phase == "gate" for message in messages),
            "resolve_present": any(message.phase == "resolve" for message in messages),
            "phase_sequence": phases,
            "ordered_phases": self._ordered_phases(phases),
            "first_phase": phases[0] if phases else None,
            "last_phase": phases[-1] if phases else None,
            "related_claim_ids": related_claim_ids,
            "message_refs": [message.message_digest for message in messages],
        }

    def _delivery_scope(self, recipient: str) -> str:
        normalized_recipient = _normalize_non_empty(recipient, "recipient")
        if normalized_recipient == "broadcast":
            return "broadcast"
        if normalized_recipient == "council":
            return "council"
        return "agent"

    def _ordered_phases(self, phases: List[str]) -> bool:
        previous_order = -1
        for phase in phases:
            current_order = CONSENSUS_BUS_PHASE_ORDER[phase]
            if current_order < previous_order:
                return False
            previous_order = current_order
        return True
