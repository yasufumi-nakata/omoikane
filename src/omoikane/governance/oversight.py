"""Human oversight channel for Guardian actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..agentic.trust import TrustService
from ..common import new_id, utc_now_iso

SCHEMA_VERSION = "1.0.0"
GUARDIAN_ROLES = ("ethics", "integrity", "identity")
OVERSIGHT_CATEGORIES = (
    "veto",
    "attest",
    "rule-update",
    "emergency-trigger",
    "pin-renewal",
)
REVIEWER_ATTESTATION_TYPES = (
    "government-id",
    "institutional-badge",
    "live-session-attestation",
)
REVIEWER_LIABILITY_MODES = ("individual", "institutional", "joint")
REVIEWER_STATUSES = ("active", "suspended", "revoked")
REVIEWER_VERIFICATION_STATUSES = ("verified", "stale", "revoked")
JURISDICTION_BUNDLE_STATUSES = ("ready", "stale", "revoked")
VERIFICATION_TRANSPORT_PROFILES = ("reviewer-live-proof-bridge-v1",)
DEFAULT_GUARDIAN_AGENT_BY_ROLE = {
    "ethics": "ethics-guardian",
    "integrity": "integrity-guardian",
    "identity": "identity-guardian",
}


def _normalize_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _unique_strings(values: List[str], field_name: str) -> List[str]:
    unique: List[str] = []
    for value in values:
        normalized = _normalize_non_empty(value, field_name)
        if normalized not in unique:
            unique.append(normalized)
    return unique


def _parse_datetime(value: str, field_name: str) -> datetime:
    normalized = _normalize_non_empty(value, field_name)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone information")
    return parsed


@dataclass(frozen=True)
class OversightRule:
    """Fixed quorum and escalation policy per oversight category."""

    required_quorum: int
    escalation_window_seconds: int

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewerIdentityProof:
    """Serializable reviewer identity evidence."""

    credential_id: str
    attestation_type: str
    proof_ref: str
    jurisdiction: str
    valid_until: str

    def __post_init__(self) -> None:
        _normalize_non_empty(self.credential_id, "credential_id")
        if self.attestation_type not in REVIEWER_ATTESTATION_TYPES:
            raise ValueError(f"unsupported attestation_type: {self.attestation_type}")
        _normalize_non_empty(self.proof_ref, "proof_ref")
        _normalize_non_empty(self.jurisdiction, "jurisdiction")
        _normalize_non_empty(self.valid_until, "valid_until")

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class JurisdictionEvidenceBundle:
    """Transport-safe legal evidence package for one reviewer jurisdiction."""

    bundle_id: str
    jurisdiction: str
    package_ref: str
    package_digest: str
    status: str
    transport_profile: str
    updated_at: str
    kind: str = "guardian_jurisdiction_evidence_bundle"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _normalize_non_empty(self.bundle_id, "bundle_id")
        _normalize_non_empty(self.jurisdiction, "jurisdiction")
        _normalize_non_empty(self.package_ref, "package_ref")
        _normalize_non_empty(self.package_digest, "package_digest")
        if self.status not in JURISDICTION_BUNDLE_STATUSES:
            raise ValueError(f"unsupported jurisdiction bundle status: {self.status}")
        if self.transport_profile not in VERIFICATION_TRANSPORT_PROFILES:
            raise ValueError(f"unsupported transport_profile: {self.transport_profile}")
        _parse_datetime(self.updated_at, "updated_at")

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewerCredentialVerification:
    """Current reviewer credential verification snapshot."""

    verification_id: str
    status: str
    verified_at: str
    valid_until: str
    verifier_ref: str
    challenge_ref: str
    challenge_digest: str
    transport_profile: str
    jurisdiction_bundle: JurisdictionEvidenceBundle
    kind: str = "guardian_reviewer_verification"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _normalize_non_empty(self.verification_id, "verification_id")
        if self.status not in REVIEWER_VERIFICATION_STATUSES:
            raise ValueError(f"unsupported verification status: {self.status}")
        verified_at = _parse_datetime(self.verified_at, "verified_at")
        valid_until = _parse_datetime(self.valid_until, "valid_until")
        if valid_until <= verified_at:
            raise ValueError("valid_until must be later than verified_at")
        _normalize_non_empty(self.verifier_ref, "verifier_ref")
        _normalize_non_empty(self.challenge_ref, "challenge_ref")
        _normalize_non_empty(self.challenge_digest, "challenge_digest")
        if self.transport_profile not in VERIFICATION_TRANSPORT_PROFILES:
            raise ValueError(f"unsupported transport_profile: {self.transport_profile}")
        if self.jurisdiction_bundle.transport_profile != self.transport_profile:
            raise ValueError("jurisdiction_bundle transport_profile must match verification")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
            "status": self.status,
            "verified_at": self.verified_at,
            "valid_until": self.valid_until,
            "verifier_ref": self.verifier_ref,
            "challenge_ref": self.challenge_ref,
            "challenge_digest": self.challenge_digest,
            "transport_profile": self.transport_profile,
            "jurisdiction_bundle": self.jurisdiction_bundle.to_dict(),
        }


@dataclass(frozen=True)
class ReviewerResponsibility:
    """Serializable reviewer duty scope and liability binding."""

    liability_mode: str
    legal_ack_ref: str
    escalation_contact: str
    allowed_guardian_roles: List[str]
    allowed_categories: List[str]

    def __post_init__(self) -> None:
        if self.liability_mode not in REVIEWER_LIABILITY_MODES:
            raise ValueError(f"unsupported liability_mode: {self.liability_mode}")
        _normalize_non_empty(self.legal_ack_ref, "legal_ack_ref")
        _normalize_non_empty(self.escalation_contact, "escalation_contact")
        normalized_roles = _unique_strings(self.allowed_guardian_roles, "allowed_guardian_roles")
        normalized_categories = _unique_strings(self.allowed_categories, "allowed_categories")
        if not normalized_roles:
            raise ValueError("allowed_guardian_roles must not be empty")
        if not normalized_categories:
            raise ValueError("allowed_categories must not be empty")
        if any(role not in GUARDIAN_ROLES for role in normalized_roles):
            raise ValueError("allowed_guardian_roles contains unsupported value")
        if any(category not in OVERSIGHT_CATEGORIES for category in normalized_categories):
            raise ValueError("allowed_categories contains unsupported value")
        object.__setattr__(self, "allowed_guardian_roles", normalized_roles)
        object.__setattr__(self, "allowed_categories", normalized_categories)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "liability_mode": self.liability_mode,
            "legal_ack_ref": self.legal_ack_ref,
            "escalation_contact": self.escalation_contact,
            "allowed_guardian_roles": list(self.allowed_guardian_roles),
            "allowed_categories": list(self.allowed_categories),
        }


@dataclass
class GuardianReviewerRecord:
    """Registered reviewer identity proof and duty scope."""

    reviewer_id: str
    display_name: str
    identity_proof: ReviewerIdentityProof
    responsibility: ReviewerResponsibility
    status: str = "active"
    registered_at: str = ""
    credential_verification: Optional[ReviewerCredentialVerification] = None
    revocation_reason: str = ""
    revoked_at: str = ""
    kind: str = "guardian_reviewer_record"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.reviewer_id = _normalize_non_empty(self.reviewer_id, "reviewer_id")
        self.display_name = _normalize_non_empty(self.display_name, "display_name")
        if self.status not in REVIEWER_STATUSES:
            raise ValueError(f"unsupported reviewer status: {self.status}")
        if not self.registered_at:
            self.registered_at = utc_now_iso()
        if self.status == "revoked":
            self.revocation_reason = _normalize_non_empty(
                self.revocation_reason,
                "revocation_reason",
            )
            if not self.revoked_at:
                self.revoked_at = utc_now_iso()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "reviewer_id": self.reviewer_id,
            "display_name": self.display_name,
            "status": self.status,
            "registered_at": self.registered_at,
            "identity_proof": self.identity_proof.to_dict(),
            "responsibility": self.responsibility.to_dict(),
            "credential_verification": (
                self.credential_verification.to_dict()
                if self.credential_verification is not None
                else None
            ),
            "revocation_reason": self.revocation_reason or None,
            "revoked_at": self.revoked_at or None,
        }


@dataclass
class ReviewerBinding:
    """Immutable reviewer proof snapshot attached to one oversight attestation."""

    reviewer_id: str
    credential_id: str
    proof_ref: str
    liability_mode: str
    legal_ack_ref: str
    verification_id: str
    verifier_ref: str
    challenge_digest: str
    transport_profile: str
    jurisdiction_bundle_ref: str
    jurisdiction_bundle_digest: str
    guardian_role: str
    category: str
    attested_at: str = ""

    def __post_init__(self) -> None:
        self.reviewer_id = _normalize_non_empty(self.reviewer_id, "reviewer_id")
        self.credential_id = _normalize_non_empty(self.credential_id, "credential_id")
        self.proof_ref = _normalize_non_empty(self.proof_ref, "proof_ref")
        if self.liability_mode not in REVIEWER_LIABILITY_MODES:
            raise ValueError(f"unsupported liability_mode: {self.liability_mode}")
        self.legal_ack_ref = _normalize_non_empty(self.legal_ack_ref, "legal_ack_ref")
        self.verification_id = _normalize_non_empty(self.verification_id, "verification_id")
        self.verifier_ref = _normalize_non_empty(self.verifier_ref, "verifier_ref")
        self.challenge_digest = _normalize_non_empty(self.challenge_digest, "challenge_digest")
        if self.transport_profile not in VERIFICATION_TRANSPORT_PROFILES:
            raise ValueError(f"unsupported transport_profile: {self.transport_profile}")
        self.jurisdiction_bundle_ref = _normalize_non_empty(
            self.jurisdiction_bundle_ref,
            "jurisdiction_bundle_ref",
        )
        self.jurisdiction_bundle_digest = _normalize_non_empty(
            self.jurisdiction_bundle_digest,
            "jurisdiction_bundle_digest",
        )
        if self.guardian_role not in GUARDIAN_ROLES:
            raise ValueError(f"unsupported guardian_role: {self.guardian_role}")
        if self.category not in OVERSIGHT_CATEGORIES:
            raise ValueError(f"unsupported category: {self.category}")
        if not self.attested_at:
            self.attested_at = utc_now_iso()

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class HumanAttestation:
    """Serializable reviewer quorum state."""

    required_quorum: int
    escalation_window_seconds: int
    reviewers: List[str] = field(default_factory=list)
    status: str = "pending"

    def __post_init__(self) -> None:
        self.reviewers = _unique_strings(self.reviewers, "reviewer")
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
    reviewer_bindings: List[ReviewerBinding] = field(default_factory=list)
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
        self.escalation_path = _unique_strings(self.escalation_path, "escalation_path")
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
            "reviewer_bindings": [binding.to_dict() for binding in self.reviewer_bindings],
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
        self._reviewers: Dict[str, GuardianReviewerRecord] = {}
        self._rules = {
            "veto": OversightRule(required_quorum=1, escalation_window_seconds=86_400),
            "attest": OversightRule(required_quorum=2, escalation_window_seconds=604_800),
            "rule-update": OversightRule(required_quorum=3, escalation_window_seconds=259_200),
            "emergency-trigger": OversightRule(required_quorum=1, escalation_window_seconds=60),
            "pin-renewal": OversightRule(required_quorum=2, escalation_window_seconds=86_400),
        }

    def register_reviewer(
        self,
        *,
        reviewer_id: str,
        display_name: str,
        credential_id: str,
        attestation_type: str,
        proof_ref: str,
        jurisdiction: str,
        valid_until: str,
        liability_mode: str,
        legal_ack_ref: str,
        escalation_contact: str,
        allowed_guardian_roles: List[str],
        allowed_categories: List[str],
    ) -> Dict[str, Any]:
        reviewer_key = _normalize_non_empty(reviewer_id, "reviewer_id")
        if reviewer_key in self._reviewers:
            raise ValueError(f"reviewer already registered: {reviewer_key}")
        record = GuardianReviewerRecord(
            reviewer_id=reviewer_key,
            display_name=display_name,
            identity_proof=ReviewerIdentityProof(
                credential_id=credential_id,
                attestation_type=attestation_type,
                proof_ref=proof_ref,
                jurisdiction=jurisdiction,
                valid_until=valid_until,
            ),
            responsibility=ReviewerResponsibility(
                liability_mode=liability_mode,
                legal_ack_ref=legal_ack_ref,
                escalation_contact=escalation_contact,
                allowed_guardian_roles=allowed_guardian_roles,
                allowed_categories=allowed_categories,
            ),
        )
        self._reviewers[record.reviewer_id] = record
        return record.to_dict()

    def verify_reviewer(
        self,
        reviewer_id: str,
        *,
        verifier_ref: str,
        challenge_ref: str,
        challenge_digest: str,
        jurisdiction_bundle_ref: str,
        jurisdiction_bundle_digest: str,
        transport_profile: str = "reviewer-live-proof-bridge-v1",
        verified_at: str = "",
        valid_until: str = "",
        verification_status: str = "verified",
        jurisdiction_bundle_status: str = "ready",
    ) -> Dict[str, Any]:
        reviewer = self._reviewer(reviewer_id)
        if reviewer.status != "active":
            raise PermissionError(f"reviewer is not active: {reviewer.reviewer_id}")
        if transport_profile not in VERIFICATION_TRANSPORT_PROFILES:
            raise ValueError(f"unsupported transport_profile: {transport_profile}")
        if verification_status not in REVIEWER_VERIFICATION_STATUSES:
            raise ValueError(f"unsupported verification status: {verification_status}")
        if jurisdiction_bundle_status not in JURISDICTION_BUNDLE_STATUSES:
            raise ValueError(
                f"unsupported jurisdiction bundle status: {jurisdiction_bundle_status}"
            )

        verified_at_value = verified_at or utc_now_iso()
        valid_until_value = valid_until or reviewer.identity_proof.valid_until
        if _parse_datetime(valid_until_value, "valid_until") > _parse_datetime(
            reviewer.identity_proof.valid_until,
            "identity_proof.valid_until",
        ):
            raise ValueError("valid_until must not exceed identity proof validity")

        reviewer.credential_verification = ReviewerCredentialVerification(
            verification_id=new_id("reviewer-verification"),
            status=verification_status,
            verified_at=verified_at_value,
            valid_until=valid_until_value,
            verifier_ref=verifier_ref,
            challenge_ref=challenge_ref,
            challenge_digest=challenge_digest,
            transport_profile=transport_profile,
            jurisdiction_bundle=JurisdictionEvidenceBundle(
                bundle_id=new_id("jurisdiction-bundle"),
                jurisdiction=reviewer.identity_proof.jurisdiction,
                package_ref=jurisdiction_bundle_ref,
                package_digest=jurisdiction_bundle_digest,
                status=jurisdiction_bundle_status,
                transport_profile=transport_profile,
                updated_at=verified_at_value,
            ),
        )
        self._reviewers[reviewer.reviewer_id] = reviewer
        return reviewer.to_dict()

    def revoke_reviewer(self, reviewer_id: str, *, reason: str) -> Dict[str, Any]:
        reviewer = self._reviewer(reviewer_id)
        reviewer.status = "revoked"
        reviewer.revocation_reason = _normalize_non_empty(reason, "reason")
        reviewer.revoked_at = utc_now_iso()
        if reviewer.credential_verification is not None:
            verification = reviewer.credential_verification
            reviewer.credential_verification = ReviewerCredentialVerification(
                verification_id=verification.verification_id,
                status="revoked",
                verified_at=verification.verified_at,
                valid_until=verification.valid_until,
                verifier_ref=verification.verifier_ref,
                challenge_ref=verification.challenge_ref,
                challenge_digest=verification.challenge_digest,
                transport_profile=verification.transport_profile,
                jurisdiction_bundle=JurisdictionEvidenceBundle(
                    bundle_id=verification.jurisdiction_bundle.bundle_id,
                    jurisdiction=verification.jurisdiction_bundle.jurisdiction,
                    package_ref=verification.jurisdiction_bundle.package_ref,
                    package_digest=verification.jurisdiction_bundle.package_digest,
                    status="revoked",
                    transport_profile=verification.jurisdiction_bundle.transport_profile,
                    updated_at=reviewer.revoked_at,
                ),
            )
        self._reviewers[reviewer.reviewer_id] = reviewer
        return reviewer.to_dict()

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "kind": "guardian_oversight_policy",
            "schema_version": SCHEMA_VERSION,
            "guardian_agent_by_role": dict(self._guardian_agent_by_role),
            "categories": {
                category: rule.to_dict() for category, rule in sorted(self._rules.items())
            },
            "reviewer_identity_policy": {
                "attestation_types": list(REVIEWER_ATTESTATION_TYPES),
                "liability_modes": list(REVIEWER_LIABILITY_MODES),
                "reviewer_statuses": list(REVIEWER_STATUSES),
                "verification_statuses": list(REVIEWER_VERIFICATION_STATUSES),
                "verification_transport_profiles": list(VERIFICATION_TRANSPORT_PROFILES),
                "verification_required_categories": list(OVERSIGHT_CATEGORIES),
                "required_binding_fields": [
                    "credential_id",
                    "proof_ref",
                    "legal_ack_ref",
                    "verification_id",
                    "verifier_ref",
                    "challenge_digest",
                    "transport_profile",
                    "jurisdiction_bundle_ref",
                    "jurisdiction_bundle_digest",
                    "guardian_role",
                    "category",
                ],
            },
        }

    def reviewer_snapshot(self) -> List[Dict[str, Any]]:
        return [
            self._reviewers[reviewer_id].to_dict()
            for reviewer_id in sorted(self._reviewers)
        ]

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
        event = GuardianOversightEvent(
            guardian_role=_normalize_non_empty(guardian_role, "guardian_role"),
            category=category,
            payload_ref=payload_ref,
            escalation_path=escalation_path,
            human_attestation=HumanAttestation(
                required_quorum=rule.required_quorum,
                escalation_window_seconds=rule.escalation_window_seconds,
            ),
        )
        self._events[event.event_id] = event
        for reviewer_id in _unique_strings(reviewers or [], "reviewers"):
            self._bind_reviewer(event, reviewer_id)
        self._events[event.event_id] = event
        return event.to_dict()

    def attest(self, event_id: str, *, reviewer_id: str) -> Dict[str, Any]:
        event = self._event(event_id)
        if event.human_attestation.status == "breached":
            raise ValueError("breached oversight event cannot be attested")
        self._bind_reviewer(event, reviewer_id)
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
            "kind": "guardian_oversight_snapshot",
            "schema_version": SCHEMA_VERSION,
            "policy": self.policy_snapshot(),
            "reviewers": self.reviewer_snapshot(),
            "events": [self._events[event_id].to_dict() for event_id in sorted(self._events)],
        }

    def _bind_reviewer(self, event: GuardianOversightEvent, reviewer_id: str) -> None:
        reviewer = self._reviewer(reviewer_id)
        if reviewer.status != "active":
            raise PermissionError(f"reviewer is not active: {reviewer.reviewer_id}")
        if reviewer.reviewer_id in event.human_attestation.reviewers:
            return
        if event.guardian_role not in reviewer.responsibility.allowed_guardian_roles:
            raise PermissionError(
                f"reviewer {reviewer.reviewer_id} is not authorized for guardian role {event.guardian_role}"
            )
        if event.category not in reviewer.responsibility.allowed_categories:
            raise PermissionError(
                f"reviewer {reviewer.reviewer_id} is not authorized for oversight category {event.category}"
            )
        verification = reviewer.credential_verification
        if verification is None:
            raise PermissionError(
                f"reviewer {reviewer.reviewer_id} lacks live credential verification"
            )
        if verification.status != "verified":
            raise PermissionError(
                f"reviewer {reviewer.reviewer_id} credential verification is {verification.status}"
            )
        if _parse_datetime(verification.valid_until, "valid_until") <= _parse_datetime(
            utc_now_iso(),
            "now",
        ):
            raise PermissionError(
                f"reviewer {reviewer.reviewer_id} credential verification expired"
            )
        if verification.jurisdiction_bundle.status != "ready":
            raise PermissionError(
                "reviewer jurisdiction evidence bundle must be ready before attestation"
            )
        if verification.jurisdiction_bundle.jurisdiction != reviewer.identity_proof.jurisdiction:
            raise PermissionError("reviewer jurisdiction bundle must match identity proof jurisdiction")

        event.human_attestation.reviewers.append(reviewer.reviewer_id)
        event.reviewer_bindings.append(
            ReviewerBinding(
                reviewer_id=reviewer.reviewer_id,
                credential_id=reviewer.identity_proof.credential_id,
                proof_ref=reviewer.identity_proof.proof_ref,
                liability_mode=reviewer.responsibility.liability_mode,
                legal_ack_ref=reviewer.responsibility.legal_ack_ref,
                verification_id=verification.verification_id,
                verifier_ref=verification.verifier_ref,
                challenge_digest=verification.challenge_digest,
                transport_profile=verification.transport_profile,
                jurisdiction_bundle_ref=verification.jurisdiction_bundle.package_ref,
                jurisdiction_bundle_digest=verification.jurisdiction_bundle.package_digest,
                guardian_role=event.guardian_role,
                category=event.category,
            )
        )
        if event.human_attestation.received_quorum >= event.human_attestation.required_quorum:
            event.human_attestation.status = "satisfied"

    def _event(self, event_id: str) -> GuardianOversightEvent:
        event_key = _normalize_non_empty(event_id, "event_id")
        if event_key not in self._events:
            raise KeyError(f"unknown oversight event: {event_key}")
        return self._events[event_key]

    def _reviewer(self, reviewer_id: str) -> GuardianReviewerRecord:
        reviewer_key = _normalize_non_empty(reviewer_id, "reviewer_id")
        if reviewer_key not in self._reviewers:
            raise KeyError(f"unknown reviewer: {reviewer_key}")
        return self._reviewers[reviewer_key]

    def _rule(self, category: str) -> OversightRule:
        category_key = _normalize_non_empty(category, "category")
        if category_key not in self._rules:
            raise ValueError(f"unsupported oversight category: {category_key}")
        return self._rules[category_key]
