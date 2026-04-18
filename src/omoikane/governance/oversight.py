"""Human oversight channel for Guardian actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..common import new_id, utc_now_iso
from ..agentic.trust import TrustService

SCHEMA_VERSION = "1.0.0"
GUARDIAN_ROLES = ("ethics", "integrity", "identity")
OVERSIGHT_CATEGORIES = (
    "veto",
    "attest",
    "rule-update",
    "emergency-trigger",
    "pin-renewal",
)
DEFAULT_GUARDIAN_AGENT_BY_ROLE = {
    "ethics": "ethics-guardian",
    "integrity": "integrity-guardian",
    "identity": "identity-guardian",
}


def _normalize_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _unique_reviewers(reviewers: List[str]) -> List[str]:
    unique: List[str] = []
    for reviewer in reviewers:
        normalized = _normalize_non_empty(reviewer, "reviewer")
        if normalized not in unique:
            unique.append(normalized)
    return unique


@dataclass(frozen=True)
class OversightRule:
    """Fixed quorum and escalation policy per oversight category."""

    required_quorum: int
    escalation_window_seconds: int

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class HumanAttestation:
    """Serializable reviewer quorum state."""

    required_quorum: int
    escalation_window_seconds: int
    reviewers: List[str] = field(default_factory=list)
    status: str = "pending"

    def __post_init__(self) -> None:
        self.reviewers = _unique_reviewers(self.reviewers)
        if self.required_quorum < 1:
            raise ValueError("required_quorum must be >= 1")
        if self.escalation_window_seconds < 1:
            raise ValueError("escalation_window_seconds must be >= 1")
        if self.status not in {"pending", "satisfied", "breached"}:
            raise ValueError(f"unsupported attestation status: {self.status}")

    @property
    def received_quorum(self) -> int:
        return len(self.reviewers)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_quorum": self.required_quorum,
            "received_quorum": self.received_quorum,
            "reviewers": list(self.reviewers),
            "status": self.status,
            "escalation_window_seconds": self.escalation_window_seconds,
        }


@dataclass
class GuardianOversightEvent:
    """Append-only oversight event bound to one Guardian action."""

    guardian_role: str
    category: str
    payload_ref: str
    escalation_path: List[str]
    human_attestation: HumanAttestation
    event_id: str = ""
    recorded_at: str = ""
    pin_breach_propagated: bool = False
    kind: str = "guardian_oversight_event"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.guardian_role not in GUARDIAN_ROLES:
            raise ValueError(f"unsupported guardian_role: {self.guardian_role}")
        if self.category not in OVERSIGHT_CATEGORIES:
            raise ValueError(f"unsupported oversight category: {self.category}")
        self.payload_ref = _normalize_non_empty(self.payload_ref, "payload_ref")
        self.escalation_path = _unique_reviewers(self.escalation_path)
        if not self.escalation_path:
            raise ValueError("escalation_path must not be empty")
        if not self.event_id:
            self.event_id = new_id("oversight-event")
        if not self.recorded_at:
            self.recorded_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "recorded_at": self.recorded_at,
            "guardian_role": self.guardian_role,
            "category": self.category,
            "payload_ref": self.payload_ref,
            "human_attestation": self.human_attestation.to_dict(),
            "escalation_path": list(self.escalation_path),
            "pin_breach_propagated": self.pin_breach_propagated,
        }


class OversightService:
    """Deterministic human oversight channel for Guardian actions."""

    def __init__(
        self,
        *,
        trust_service: Optional[TrustService] = None,
        guardian_agent_by_role: Optional[Dict[str, str]] = None,
    ) -> None:
        self._trust = trust_service
        self._guardian_agent_by_role = dict(DEFAULT_GUARDIAN_AGENT_BY_ROLE)
        if guardian_agent_by_role:
            self._guardian_agent_by_role.update(guardian_agent_by_role)
        self._events: Dict[str, GuardianOversightEvent] = {}
        self._rules = {
            "veto": OversightRule(required_quorum=1, escalation_window_seconds=86_400),
            "attest": OversightRule(required_quorum=2, escalation_window_seconds=604_800),
            "rule-update": OversightRule(required_quorum=3, escalation_window_seconds=259_200),
            "emergency-trigger": OversightRule(required_quorum=1, escalation_window_seconds=60),
            "pin-renewal": OversightRule(required_quorum=2, escalation_window_seconds=86_400),
        }

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "kind": "guardian_oversight_policy",
            "schema_version": SCHEMA_VERSION,
            "guardian_agent_by_role": dict(self._guardian_agent_by_role),
            "categories": {
                category: rule.to_dict() for category, rule in sorted(self._rules.items())
            },
        }

    def record(
        self,
        *,
        guardian_role: str,
        category: str,
        payload_ref: str,
        escalation_path: List[str],
        reviewers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        rule = self._rule(category)
        unique_reviewers = _unique_reviewers(reviewers or [])
        status = "satisfied" if len(unique_reviewers) >= rule.required_quorum else "pending"
        event = GuardianOversightEvent(
            guardian_role=_normalize_non_empty(guardian_role, "guardian_role"),
            category=category,
            payload_ref=payload_ref,
            escalation_path=escalation_path,
            human_attestation=HumanAttestation(
                required_quorum=rule.required_quorum,
                escalation_window_seconds=rule.escalation_window_seconds,
                reviewers=unique_reviewers,
                status=status,
            ),
        )
        self._events[event.event_id] = event
        return event.to_dict()

    def attest(self, event_id: str, *, reviewer_id: str) -> Dict[str, Any]:
        event = self._event(event_id)
        if event.human_attestation.status == "breached":
            raise ValueError("breached oversight event cannot be attested")

        reviewer = _normalize_non_empty(reviewer_id, "reviewer_id")
        if reviewer not in event.human_attestation.reviewers:
            event.human_attestation.reviewers.append(reviewer)
        if event.human_attestation.received_quorum >= event.human_attestation.required_quorum:
            event.human_attestation.status = "satisfied"
        self._events[event.event_id] = event
        return event.to_dict()

    def breach(self, event_id: str) -> Dict[str, Any]:
        event = self._event(event_id)
        if event.human_attestation.status == "satisfied":
            return event.to_dict()

        event.human_attestation.status = "breached"
        if self._trust is not None:
            guardian_agent = self._guardian_agent_by_role[event.guardian_role]
            self._trust.unpin_agent(guardian_agent)
            event.pin_breach_propagated = True
        self._events[event.event_id] = event
        return event.to_dict()

    def snapshot(self) -> Dict[str, Any]:
        return {
            "policy": self.policy_snapshot(),
            "events": [self._events[event_id].to_dict() for event_id in sorted(self._events)],
        }

    def _event(self, event_id: str) -> GuardianOversightEvent:
        event_key = _normalize_non_empty(event_id, "event_id")
        if event_key not in self._events:
            raise KeyError(f"unknown oversight event: {event_key}")
        return self._events[event_key]

    def _rule(self, category: str) -> OversightRule:
        category_key = _normalize_non_empty(category, "category")
        if category_key not in self._rules:
            raise ValueError(f"unsupported oversight category: {category_key}")
        return self._rules[category_key]
