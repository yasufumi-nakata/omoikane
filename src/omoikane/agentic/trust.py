"""Deterministic trust scoring for the reference agent roster."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Dict, List, Mapping, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


TRUST_SNAPSHOT_SCHEMA_VERSION = "1.0.0"
TRUST_TRANSFER_SCHEMA_VERSION = "1.0.0"
TRUST_TRANSFER_POLICY_ID = "bounded-cross-substrate-trust-transfer-v1"
TRUST_TRANSFER_ATTESTATION_POLICY_ID = "bounded-trust-transfer-attestation-federation-v1"
TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES = (
    "source-guardian",
    "destination-guardian",
    "human-reviewer",
)


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _actor_fingerprint(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _snapshot_history_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("history", [])))


def _snapshot_threshold_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("thresholds", {})))


def _snapshot_eligibility_digest(snapshot: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(snapshot.get("eligibility", {})))


def _trust_transfer_route_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source_substrate_ref": receipt["source_substrate_ref"],
        "destination_substrate_ref": receipt["destination_substrate_ref"],
        "destination_host_ref": receipt["destination_host_ref"],
    }


def _trust_transfer_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": receipt["schema_version"],
        "transfer_policy_id": receipt["transfer_policy_id"],
        "attestation_policy_id": receipt["attestation_policy_id"],
        "agent_id": receipt["agent_id"],
        "source_substrate_ref": receipt["source_substrate_ref"],
        "destination_substrate_ref": receipt["destination_substrate_ref"],
        "destination_host_ref": receipt["destination_host_ref"],
        "transferred_at": receipt["transferred_at"],
        "source_snapshot_ref": receipt["source_snapshot_ref"],
        "source_snapshot_digest": receipt["source_snapshot_digest"],
        "destination_snapshot_ref": receipt["destination_snapshot_ref"],
        "destination_snapshot_digest": receipt["destination_snapshot_digest"],
        "export_receipt": receipt["export_receipt"],
        "federation_attestation": receipt["federation_attestation"],
        "import_receipt": receipt["import_receipt"],
        "status": receipt["status"],
    }


@dataclass(frozen=True)
class TrustThresholds:
    """Operational trust floors used by the reference runtime."""

    council_invite_floor: float = 0.5
    weighted_vote_floor: float = 0.6
    apply_floor: float = 0.8
    self_modify_floor: float = 0.95
    guardian_floor: float = 0.99
    guardian_requires_human_pin: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrustUpdatePolicy:
    """Fixed trust update policy for the reference runtime."""

    policy_id: str = "reference-v0"
    provenance_policy_id: str = "reference-trust-provenance-v1"
    initial_score: float = 0.3
    base_deltas: Dict[str, float] = field(
        default_factory=lambda: {
            "council_quality_positive": 0.04,
            "guardian_audit_pass": 0.06,
            "human_feedback_good": 0.05,
            "guardian_veto": -0.12,
            "regression_detected": -0.08,
            "human_feedback_bad": -0.10,
            "ethics_violation": -0.25,
        }
    )
    severity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
    )
    event_origin_requirements: Dict[str, str] = field(
        default_factory=lambda: {
            "council_quality_positive": "council",
            "guardian_audit_pass": "guardian",
            "human_feedback_good": "human",
            "guardian_veto": "guardian",
            "regression_detected": "any",
            "human_feedback_bad": "human",
            "ethics_violation": "any",
        }
    )
    blocked_positive_reciprocity_scope: str = "registered-agent-domain-history"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustEvent:
    """One audited trust update attempt."""

    event_id: str
    agent_id: str
    domain: str
    event_type: str
    severity: str
    evidence_confidence: float
    raw_delta: float
    applied_delta: float
    applied: bool
    triggered_by: str
    triggered_by_agent_id: str
    rationale: str
    global_before: float
    global_after: float
    domain_before: float
    domain_after: float
    policy_id: str
    provenance_status: str
    provenance_policy_id: str
    recorded_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTrustState:
    """Serializable trust state for one agent."""

    agent_id: str
    global_score: float
    per_domain: Dict[str, float] = field(default_factory=dict)
    history: List[TrustEvent] = field(default_factory=list)
    pinned_by_human: bool = False
    pinned_reason: str = ""

    def to_dict(self, thresholds: TrustThresholds) -> Dict[str, Any]:
        per_domain = {key: _clamp_score(value) for key, value in sorted(self.per_domain.items())}
        self_modify_score = per_domain.get("self_modify", _clamp_score(self.global_score))
        return {
            "kind": "trust_snapshot",
            "schema_version": TRUST_SNAPSHOT_SCHEMA_VERSION,
            "agent_id": self.agent_id,
            "global_score": _clamp_score(self.global_score),
            "per_domain": per_domain,
            "history": [event.to_dict() for event in self.history],
            "pinned_by_human": self.pinned_by_human,
            "pinned_reason": self.pinned_reason,
            "thresholds": thresholds.to_dict(),
            "eligibility": {
                "invite_to_council": self.global_score >= thresholds.council_invite_floor,
                "count_for_weighted_vote": self.global_score >= thresholds.weighted_vote_floor,
                "apply_to_runtime": self.global_score >= thresholds.apply_floor,
                "self_modify_role": (
                    self.global_score >= thresholds.self_modify_floor
                    and self_modify_score >= thresholds.self_modify_floor
                ),
                "guardian_role": (
                    self.global_score >= thresholds.guardian_floor
                    and (not thresholds.guardian_requires_human_pin or self.pinned_by_human)
                ),
            },
        }


class TrustService:
    """Reference trust registry with deterministic scoring and human pinning."""

    def __init__(
        self,
        *,
        policy: Optional[TrustUpdatePolicy] = None,
        thresholds: Optional[TrustThresholds] = None,
    ) -> None:
        self._policy = policy or TrustUpdatePolicy()
        self._thresholds = thresholds or TrustThresholds()
        self._states: Dict[str, AgentTrustState] = {}

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "policy": self._policy.to_dict(),
            "thresholds": self._thresholds.to_dict(),
        }

    def register_agent(
        self,
        agent_id: str,
        *,
        initial_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        pinned_by_human: bool = False,
        pinned_reason: str = "",
    ) -> Dict[str, Any]:
        score = _clamp_score(
            self._policy.initial_score if initial_score is None else float(initial_score)
        )
        domain_scores = {
            name: _clamp_score(value)
            for name, value in sorted((per_domain or {}).items())
            if name.strip()
        }
        state = AgentTrustState(
            agent_id=agent_id,
            global_score=score,
            per_domain=domain_scores,
            pinned_by_human=pinned_by_human,
            pinned_reason=pinned_reason,
        )
        self._states[agent_id] = state
        return state.to_dict(self._thresholds)

    def snapshot(self, agent_id: str) -> Dict[str, Any]:
        return self._state(agent_id).to_dict(self._thresholds)

    def has_agent(self, agent_id: str) -> bool:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        return agent_key in self._states

    def all_snapshots(self) -> List[Dict[str, Any]]:
        return [self._states[agent_id].to_dict(self._thresholds) for agent_id in sorted(self._states)]

    def pin_agent(
        self,
        agent_id: str,
        *,
        global_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        reason: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = True
        state.pinned_reason = reason
        if global_score is not None:
            state.global_score = _clamp_score(float(global_score))
        if per_domain:
            for domain, score in per_domain.items():
                if domain.strip():
                    state.per_domain[domain] = _clamp_score(float(score))
        return state.to_dict(self._thresholds)

    def unpin_agent(self, agent_id: str) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = False
        state.pinned_reason = ""
        return state.to_dict(self._thresholds)

    def import_snapshot(self, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        state, errors = self._snapshot_state_from_mapping(snapshot)
        if errors or state is None:
            raise ValueError(
                "trust snapshot import requires a fixed-contract payload: "
                + "; ".join(errors or ["invalid snapshot"])
            )

        self._states[state.agent_id] = state
        imported = self._states[state.agent_id].to_dict(self._thresholds)
        if dict(snapshot) != imported:
            raise ValueError("imported trust snapshot drifted from the fixed contract")
        return imported

    def transfer_snapshot_to(
        self,
        agent_id: str,
        *,
        destination_service: "TrustService",
        source_substrate_ref: str,
        destination_substrate_ref: str,
        destination_host_ref: str,
        source_guardian_agent_id: str,
        destination_guardian_agent_id: str,
        human_reviewer_ref: str,
        council_session_ref: str,
        rationale: str,
    ) -> Dict[str, Any]:
        normalized_agent_id = self._normalize_non_empty(agent_id, "agent_id")
        normalized_source_substrate = self._normalize_non_empty(
            source_substrate_ref,
            "source_substrate_ref",
        )
        normalized_destination_substrate = self._normalize_non_empty(
            destination_substrate_ref,
            "destination_substrate_ref",
        )
        normalized_destination_host = self._normalize_non_empty(
            destination_host_ref,
            "destination_host_ref",
        )
        normalized_source_guardian = self._normalize_non_empty(
            source_guardian_agent_id,
            "source_guardian_agent_id",
        )
        normalized_destination_guardian = self._normalize_non_empty(
            destination_guardian_agent_id,
            "destination_guardian_agent_id",
        )
        normalized_human_reviewer = self._normalize_non_empty(
            human_reviewer_ref,
            "human_reviewer_ref",
        )
        normalized_council_session = self._normalize_non_empty(
            council_session_ref,
            "council_session_ref",
        )
        normalized_rationale = self._normalize_non_empty(rationale, "rationale")
        if normalized_source_substrate == normalized_destination_substrate:
            raise ValueError("source_substrate_ref and destination_substrate_ref must differ")
        if normalized_source_guardian == normalized_destination_guardian:
            raise ValueError("source and destination guardian attestations must be distinct")
        if not self._is_guardian_authority(normalized_source_guardian):
            raise ValueError("source_guardian_agent_id must hold guardian_role eligibility")
        if not destination_service._is_guardian_authority(normalized_destination_guardian):
            raise ValueError("destination_guardian_agent_id must hold guardian_role eligibility")

        source_snapshot = self.snapshot(normalized_agent_id)
        source_snapshot_digest = sha256_text(canonical_json(source_snapshot))
        source_history_digest = _snapshot_history_digest(source_snapshot)
        source_threshold_digest = _snapshot_threshold_digest(source_snapshot)
        source_eligibility_digest = _snapshot_eligibility_digest(source_snapshot)

        destination_snapshot = destination_service.import_snapshot(source_snapshot)
        destination_snapshot_digest = sha256_text(canonical_json(destination_snapshot))

        attestors = [
            {
                "role": "source-guardian",
                "actor_ref": f"agent://{normalized_source_guardian}",
                "attestation_ref": f"guardian-attestation://{normalized_source_guardian}",
                "eligibility_gate": "guardian_role",
                "status": "attested",
            },
            {
                "role": "destination-guardian",
                "actor_ref": f"agent://{normalized_destination_guardian}",
                "attestation_ref": f"guardian-attestation://{normalized_destination_guardian}",
                "eligibility_gate": "guardian_role",
                "status": "attested",
            },
            {
                "role": "human-reviewer",
                "actor_ref": normalized_human_reviewer,
                "attestation_ref": f"{normalized_human_reviewer}/trust-transfer",
                "eligibility_gate": "human-explicit-approval",
                "status": "attested",
            },
        ]
        received_roles = [attestor["role"] for attestor in attestors if attestor["status"] == "attested"]
        receipt = {
            "kind": "trust_transfer_receipt",
            "schema_version": TRUST_TRANSFER_SCHEMA_VERSION,
            "receipt_id": new_id("trust-transfer"),
            "transfer_policy_id": TRUST_TRANSFER_POLICY_ID,
            "attestation_policy_id": TRUST_TRANSFER_ATTESTATION_POLICY_ID,
            "agent_id": normalized_agent_id,
            "source_substrate_ref": normalized_source_substrate,
            "destination_substrate_ref": normalized_destination_substrate,
            "destination_host_ref": normalized_destination_host,
            "transferred_at": utc_now_iso(),
            "source_snapshot_ref": f"trust-snapshot://source/{normalized_agent_id}",
            "source_snapshot_digest": source_snapshot_digest,
            "source_snapshot": source_snapshot,
            "destination_snapshot_ref": f"trust-snapshot://destination/{normalized_agent_id}",
            "destination_snapshot_digest": destination_snapshot_digest,
            "destination_snapshot": destination_snapshot,
            "export_receipt": {
                "export_id": new_id("trust-export"),
                "export_ref": f"trust-export://{normalized_agent_id}",
                "source_policy_id": self._policy.policy_id,
                "provenance_policy_id": self._policy.provenance_policy_id,
                "threshold_digest": source_threshold_digest,
                "history_digest": source_history_digest,
                "eligibility_digest": source_eligibility_digest,
                "history_event_count": len(source_snapshot["history"]),
                "council_session_ref": normalized_council_session,
                "rationale": normalized_rationale,
            },
            "federation_attestation": {
                "attestation_id": new_id("trust-attestation"),
                "attestation_ref": f"trust-attestation://{normalized_agent_id}",
                "required_roles": list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES),
                "received_roles": received_roles,
                "attestors": attestors,
                "quorum": len(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES),
                "quorum_received": len(received_roles),
                "route_ref": f"trust-transfer-route://{normalized_agent_id}",
                "route_digest": "",
                "cross_substrate_attested": True,
            },
            "import_receipt": {
                "import_id": new_id("trust-import"),
                "import_ref": f"trust-import://{normalized_agent_id}",
                "destination_policy_id": destination_service._policy.policy_id,
                "provenance_policy_id": destination_service._policy.provenance_policy_id,
                "threshold_digest": _snapshot_threshold_digest(destination_snapshot),
                "history_digest": _snapshot_history_digest(destination_snapshot),
                "eligibility_digest": _snapshot_eligibility_digest(destination_snapshot),
                "history_event_count": len(destination_snapshot["history"]),
                "seed_mode": "snapshot-clone-with-history",
                "destination_seeded": destination_service.has_agent(normalized_agent_id),
            },
            "validation": {},
            "status": "imported",
            "receipt_digest": "",
        }
        receipt["federation_attestation"]["route_digest"] = sha256_text(
            canonical_json(_trust_transfer_route_digest_payload(receipt))
        )
        receipt["receipt_digest"] = sha256_text(canonical_json(_trust_transfer_digest_payload(receipt)))
        receipt["validation"] = self._transfer_validation_summary(receipt)
        validation = self.validate_transfer_receipt(receipt)
        if not validation["ok"]:
            raise ValueError(
                "reference trust transfer receipt failed validation: "
                + "; ".join(validation["errors"])
            )
        return receipt

    def record_event(
        self,
        agent_id: str,
        *,
        event_type: str,
        domain: str,
        severity: str = "medium",
        evidence_confidence: float = 1.0,
        triggered_by: str,
        rationale: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        normalized_agent = self._normalize_non_empty(agent_id, "agent_id")
        normalized_domain = self._normalize_non_empty(domain, "domain")
        normalized_trigger = self._normalize_non_empty(triggered_by, "triggered_by")
        normalized_rationale = self._normalize_non_empty(rationale, "rationale")

        if event_type not in self._policy.base_deltas:
            raise ValueError(f"unsupported trust event_type: {event_type}")
        if severity not in self._policy.severity_multipliers:
            raise ValueError(f"unsupported trust severity: {severity}")
        if not 0.0 <= evidence_confidence <= 1.0:
            raise ValueError("evidence_confidence must be between 0.0 and 1.0")

        base_delta = self._policy.base_deltas[event_type]
        multiplier = self._policy.severity_multipliers[severity]
        raw_delta = round(base_delta * multiplier * evidence_confidence, 3)
        triggered_by_agent_id = self._resolve_registered_agent_id(normalized_trigger)
        provenance_status = self._evaluate_provenance(
            agent_id=normalized_agent,
            event_type=event_type,
            domain=normalized_domain,
            raw_delta=raw_delta,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
        )
        global_before = _clamp_score(state.global_score)
        domain_before = _clamp_score(state.per_domain.get(normalized_domain, state.global_score))

        if provenance_status != "accepted":
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        elif state.pinned_by_human:
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        else:
            applied = True
            applied_delta = raw_delta
            global_after = _clamp_score(global_before + raw_delta)
            domain_after = _clamp_score(domain_before + raw_delta)
            state.global_score = global_after
            state.per_domain[normalized_domain] = domain_after

        event = TrustEvent(
            event_id=new_id("trust-event"),
            agent_id=agent_id,
            domain=normalized_domain,
            event_type=event_type,
            severity=severity,
            evidence_confidence=round(evidence_confidence, 3),
            raw_delta=raw_delta,
            applied_delta=applied_delta,
            applied=applied,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
            rationale=normalized_rationale,
            global_before=global_before,
            global_after=global_after,
            domain_before=domain_before,
            domain_after=domain_after,
            policy_id=self._policy.policy_id,
            provenance_status=provenance_status,
            provenance_policy_id=self._policy.provenance_policy_id,
        )
        state.history.append(event)
        return event.to_dict()

    def validate_transfer_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if receipt.get("kind") != "trust_transfer_receipt":
            errors.append("kind must equal trust_transfer_receipt")
        if receipt.get("schema_version") != TRUST_TRANSFER_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if receipt.get("transfer_policy_id") != TRUST_TRANSFER_POLICY_ID:
            errors.append("transfer_policy_id mismatch")
        if receipt.get("attestation_policy_id") != TRUST_TRANSFER_ATTESTATION_POLICY_ID:
            errors.append("attestation_policy_id mismatch")

        self._require_mapping_field(receipt.get("export_receipt"), "export_receipt", errors)
        self._require_mapping_field(
            receipt.get("federation_attestation"),
            "federation_attestation",
            errors,
        )
        self._require_mapping_field(receipt.get("import_receipt"), "import_receipt", errors)
        self._require_mapping_field(receipt.get("validation"), "validation", errors)
        self._require_non_empty_string(receipt.get("receipt_id"), "receipt_id", errors)
        self._require_non_empty_string(receipt.get("agent_id"), "agent_id", errors)
        self._require_non_empty_string(
            receipt.get("source_substrate_ref"),
            "source_substrate_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_substrate_ref"),
            "destination_substrate_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_host_ref"),
            "destination_host_ref",
            errors,
        )
        self._require_non_empty_string(receipt.get("transferred_at"), "transferred_at", errors)
        self._require_non_empty_string(
            receipt.get("source_snapshot_ref"),
            "source_snapshot_ref",
            errors,
        )
        self._require_non_empty_string(
            receipt.get("destination_snapshot_ref"),
            "destination_snapshot_ref",
            errors,
        )

        source_snapshot, source_snapshot_errors = self._snapshot_payload_errors(
            receipt.get("source_snapshot"),
            "source_snapshot",
        )
        destination_snapshot, destination_snapshot_errors = self._snapshot_payload_errors(
            receipt.get("destination_snapshot"),
            "destination_snapshot",
        )
        errors.extend(source_snapshot_errors)
        errors.extend(destination_snapshot_errors)

        summary = self._transfer_validation_summary(receipt)
        if receipt.get("validation") != summary:
            errors.append("validation must match the computed transfer validation summary")
        if receipt.get("receipt_digest") != sha256_text(canonical_json(_trust_transfer_digest_payload(receipt))):
            errors.append("receipt_digest must bind the fixed transfer digest payload")

        if isinstance(source_snapshot, Mapping) and isinstance(destination_snapshot, Mapping):
            if receipt.get("agent_id") != source_snapshot.get("agent_id"):
                errors.append("agent_id must match source_snapshot.agent_id")
            if receipt.get("agent_id") != destination_snapshot.get("agent_id"):
                errors.append("agent_id must match destination_snapshot.agent_id")
            if receipt.get("source_snapshot_digest") != sha256_text(canonical_json(source_snapshot)):
                errors.append("source_snapshot_digest must match source_snapshot")
            if receipt.get("destination_snapshot_digest") != sha256_text(
                canonical_json(destination_snapshot)
            ):
                errors.append("destination_snapshot_digest must match destination_snapshot")

        export_receipt = receipt.get("export_receipt", {})
        if isinstance(export_receipt, Mapping):
            if export_receipt.get("source_policy_id") != self._policy.policy_id:
                errors.append("export_receipt.source_policy_id mismatch")
            if export_receipt.get("provenance_policy_id") != self._policy.provenance_policy_id:
                errors.append("export_receipt.provenance_policy_id mismatch")
            self._require_non_empty_string(
                export_receipt.get("council_session_ref"),
                "export_receipt.council_session_ref",
                errors,
            )
            self._require_non_empty_string(
                export_receipt.get("rationale"),
                "export_receipt.rationale",
                errors,
            )

        import_receipt = receipt.get("import_receipt", {})
        if isinstance(import_receipt, Mapping):
            if import_receipt.get("destination_policy_id") != self._policy.policy_id:
                errors.append("import_receipt.destination_policy_id mismatch")
            if import_receipt.get("provenance_policy_id") != self._policy.provenance_policy_id:
                errors.append("import_receipt.provenance_policy_id mismatch")
            if import_receipt.get("seed_mode") != "snapshot-clone-with-history":
                errors.append("import_receipt.seed_mode mismatch")
            if import_receipt.get("destination_seeded") is not True:
                errors.append("import_receipt.destination_seeded must be true")

        federation_attestation = receipt.get("federation_attestation", {})
        if isinstance(federation_attestation, Mapping):
            required_roles = federation_attestation.get("required_roles")
            if required_roles != list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES):
                errors.append("federation_attestation.required_roles mismatch")
            attestors = federation_attestation.get("attestors", [])
            if not isinstance(attestors, list) or len(attestors) != len(
                TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES
            ):
                errors.append("federation_attestation.attestors must cover the fixed attestation roles")
            if federation_attestation.get("cross_substrate_attested") is not True:
                errors.append("federation_attestation.cross_substrate_attested must be true")
            if federation_attestation.get("route_digest") != sha256_text(
                canonical_json(_trust_transfer_route_digest_payload(receipt))
            ):
                errors.append("federation_attestation.route_digest mismatch")
            received_roles = federation_attestation.get("received_roles", [])
            if received_roles != [
                attestor.get("role")
                for attestor in attestors
                if isinstance(attestor, Mapping) and attestor.get("status") == "attested"
            ]:
                errors.append("federation_attestation.received_roles mismatch")

        ok = not errors and summary["ok"]
        return {
            **summary,
            "ok": ok,
            "errors": errors,
        }

    def _state(self, agent_id: str) -> AgentTrustState:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        if agent_key not in self._states:
            self.register_agent(agent_key)
        return self._states[agent_key]

    def _evaluate_provenance(
        self,
        *,
        agent_id: str,
        event_type: str,
        domain: str,
        raw_delta: float,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        if raw_delta <= 0:
            return self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)

        if self._same_actor(agent_id, triggered_by, triggered_by_agent_id):
            return "blocked-self-issued-positive"

        origin_status = self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)
        if origin_status != "accepted":
            return origin_status

        if triggered_by_agent_id and self._has_reciprocal_positive_history(
            agent_id=agent_id,
            evaluator_agent_id=triggered_by_agent_id,
            domain=domain,
        ):
            return "blocked-reciprocal-positive"
        return "accepted"

    def _check_event_origin(
        self,
        event_type: str,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        expected_origin = self._policy.event_origin_requirements.get(event_type, "any")
        if expected_origin == "any":
            return "accepted"
        if expected_origin == "council":
            return (
                "accepted"
                if _actor_fingerprint(triggered_by) == "council"
                else "blocked-provenance-mismatch"
            )
        if expected_origin == "guardian":
            if triggered_by_agent_id and self._is_guardian_authority(triggered_by_agent_id):
                return "accepted"
            return "blocked-provenance-mismatch"
        if expected_origin == "human":
            if _actor_fingerprint(triggered_by) == "council" or triggered_by_agent_id:
                return "blocked-provenance-mismatch"
            return "accepted"
        return "accepted"

    def _resolve_registered_agent_id(self, actor: str) -> str:
        actor_fingerprint = _actor_fingerprint(actor)
        for registered_agent_id in self._states:
            if _actor_fingerprint(registered_agent_id) == actor_fingerprint:
                return registered_agent_id
        return ""

    def _is_guardian_authority(self, agent_id: str) -> bool:
        state = self._states.get(agent_id)
        if state is None:
            return False
        return bool(state.to_dict(self._thresholds)["eligibility"]["guardian_role"])

    def _has_reciprocal_positive_history(
        self,
        *,
        agent_id: str,
        evaluator_agent_id: str,
        domain: str,
    ) -> bool:
        evaluator_state = self._states.get(evaluator_agent_id)
        if evaluator_state is None:
            return False
        for event in evaluator_state.history:
            if (
                event.domain == domain
                and event.raw_delta > 0
                and event.provenance_status == "accepted"
                and event.triggered_by_agent_id
                and self._same_actor(agent_id, event.triggered_by, event.triggered_by_agent_id)
            ):
                return True
        return False

    def _snapshot_state_from_mapping(
        self,
        snapshot: Mapping[str, Any] | Any,
    ) -> tuple[Optional[AgentTrustState], List[str]]:
        errors: List[str] = []
        if not isinstance(snapshot, Mapping):
            return None, ["snapshot must be a mapping"]

        agent_id = snapshot.get("agent_id")
        if not isinstance(agent_id, str) or not agent_id.strip():
            errors.append("snapshot.agent_id must be a non-empty string")
            normalized_agent_id = ""
        else:
            normalized_agent_id = agent_id.strip()

        try:
            global_score = _clamp_score(float(snapshot.get("global_score", 0.0)))
        except (TypeError, ValueError):
            errors.append("snapshot.global_score must be numeric")
            global_score = 0.0

        raw_per_domain = snapshot.get("per_domain")
        if not isinstance(raw_per_domain, Mapping):
            errors.append("snapshot.per_domain must be a mapping")
            per_domain: Dict[str, float] = {}
        else:
            per_domain = {}
            for domain, score in sorted(raw_per_domain.items()):
                if not isinstance(domain, str) or not domain.strip():
                    errors.append("snapshot.per_domain keys must be non-empty strings")
                    continue
                try:
                    per_domain[domain.strip()] = _clamp_score(float(score))
                except (TypeError, ValueError):
                    errors.append(
                        f"snapshot.per_domain.{domain} must be numeric within the trust range"
                    )

        raw_history = snapshot.get("history")
        if not isinstance(raw_history, list):
            errors.append("snapshot.history must be a list")
            raw_history = []
        history: List[TrustEvent] = []
        for index, event_payload in enumerate(raw_history):
            if not isinstance(event_payload, Mapping):
                errors.append(f"snapshot.history[{index}] must be a mapping")
                continue
            try:
                event = TrustEvent(**dict(event_payload))
            except TypeError as exc:
                errors.append(f"snapshot.history[{index}] is invalid: {exc}")
                continue
            if normalized_agent_id and event.agent_id != normalized_agent_id:
                errors.append(
                    f"snapshot.history[{index}].agent_id must match snapshot.agent_id"
                )
            if event.policy_id != self._policy.policy_id:
                errors.append(
                    f"snapshot.history[{index}].policy_id must equal {self._policy.policy_id}"
                )
            if event.provenance_policy_id != self._policy.provenance_policy_id:
                errors.append(
                    "snapshot.history["
                    f"{index}"
                    "].provenance_policy_id must equal "
                    f"{self._policy.provenance_policy_id}"
                )
            history.append(event)

        pinned_by_human = snapshot.get("pinned_by_human")
        if not isinstance(pinned_by_human, bool):
            errors.append("snapshot.pinned_by_human must be a boolean")
            pinned_by_human = False
        pinned_reason = snapshot.get("pinned_reason")
        if not isinstance(pinned_reason, str):
            errors.append("snapshot.pinned_reason must be a string")
            pinned_reason = ""

        state = AgentTrustState(
            agent_id=normalized_agent_id,
            global_score=global_score,
            per_domain=per_domain,
            history=history,
            pinned_by_human=pinned_by_human,
            pinned_reason=pinned_reason,
        )
        expected_snapshot = state.to_dict(self._thresholds)

        if snapshot.get("kind") != "trust_snapshot":
            errors.append("snapshot.kind must equal trust_snapshot")
        if snapshot.get("schema_version") != TRUST_SNAPSHOT_SCHEMA_VERSION:
            errors.append("snapshot.schema_version mismatch")
        if snapshot.get("thresholds") != self._thresholds.to_dict():
            errors.append("snapshot.thresholds must equal the fixed trust thresholds")
        if dict(snapshot) != expected_snapshot:
            errors.append("snapshot must match the fixed trust snapshot contract")

        return state, errors

    def _snapshot_payload_errors(
        self,
        snapshot: Mapping[str, Any] | Any,
        field_name: str,
    ) -> tuple[Optional[Mapping[str, Any]], List[str]]:
        _, errors = self._snapshot_state_from_mapping(snapshot)
        return (
            snapshot if isinstance(snapshot, Mapping) else None,
            [f"{field_name}: {error}" for error in errors],
        )

    def _transfer_validation_summary(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        source_snapshot = receipt.get("source_snapshot", {})
        destination_snapshot = receipt.get("destination_snapshot", {})
        export_receipt = receipt.get("export_receipt", {})
        import_receipt = receipt.get("import_receipt", {})
        federation_attestation = receipt.get("federation_attestation", {})

        source_snapshot_digest_bound = isinstance(source_snapshot, Mapping) and receipt.get(
            "source_snapshot_digest"
        ) == sha256_text(canonical_json(source_snapshot))
        destination_snapshot_digest_bound = isinstance(
            destination_snapshot,
            Mapping,
        ) and receipt.get("destination_snapshot_digest") == sha256_text(
            canonical_json(destination_snapshot)
        )
        history_preserved = (
            isinstance(source_snapshot, Mapping)
            and isinstance(destination_snapshot, Mapping)
            and source_snapshot.get("history") == destination_snapshot.get("history")
            and isinstance(export_receipt, Mapping)
            and isinstance(import_receipt, Mapping)
            and export_receipt.get("history_digest") == _snapshot_history_digest(source_snapshot)
            and import_receipt.get("history_digest") == _snapshot_history_digest(destination_snapshot)
            and export_receipt.get("history_digest") == import_receipt.get("history_digest")
        )
        thresholds_preserved = (
            isinstance(source_snapshot, Mapping)
            and isinstance(destination_snapshot, Mapping)
            and source_snapshot.get("thresholds") == destination_snapshot.get("thresholds")
            and isinstance(export_receipt, Mapping)
            and isinstance(import_receipt, Mapping)
            and export_receipt.get("threshold_digest") == _snapshot_threshold_digest(source_snapshot)
            and import_receipt.get("threshold_digest")
            == _snapshot_threshold_digest(destination_snapshot)
            and export_receipt.get("threshold_digest") == import_receipt.get("threshold_digest")
        )
        provenance_policy_preserved = isinstance(export_receipt, Mapping) and isinstance(
            import_receipt,
            Mapping,
        ) and (
            export_receipt.get("provenance_policy_id")
            == import_receipt.get("provenance_policy_id")
            == self._policy.provenance_policy_id
        )
        eligibility_preserved = (
            isinstance(source_snapshot, Mapping)
            and isinstance(destination_snapshot, Mapping)
            and source_snapshot.get("eligibility") == destination_snapshot.get("eligibility")
            and isinstance(export_receipt, Mapping)
            and isinstance(import_receipt, Mapping)
            and export_receipt.get("eligibility_digest")
            == _snapshot_eligibility_digest(source_snapshot)
            and import_receipt.get("eligibility_digest")
            == _snapshot_eligibility_digest(destination_snapshot)
            and export_receipt.get("eligibility_digest") == import_receipt.get("eligibility_digest")
        )
        federation_quorum_attested = False
        if isinstance(federation_attestation, Mapping):
            attestors = federation_attestation.get("attestors", [])
            received_roles = [
                attestor.get("role")
                for attestor in attestors
                if isinstance(attestor, Mapping) and attestor.get("status") == "attested"
            ]
            federation_quorum_attested = (
                federation_attestation.get("required_roles")
                == list(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("received_roles") == received_roles
                and federation_attestation.get("quorum")
                == len(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("quorum_received") == len(received_roles)
                and set(received_roles) == set(TRUST_TRANSFER_REQUIRED_ATTESTATION_ROLES)
                and federation_attestation.get("route_digest")
                == sha256_text(canonical_json(_trust_transfer_route_digest_payload(receipt)))
                and federation_attestation.get("cross_substrate_attested") is True
            )
        destination_seeded = isinstance(import_receipt, Mapping) and (
            import_receipt.get("destination_seeded") is True
            and isinstance(destination_snapshot, Mapping)
            and destination_snapshot.get("agent_id") == receipt.get("agent_id")
        )
        receipt_digest_bound = receipt.get("receipt_digest") == sha256_text(
            canonical_json(_trust_transfer_digest_payload(receipt))
        )
        summary = {
            "source_snapshot_digest_bound": source_snapshot_digest_bound,
            "destination_snapshot_digest_bound": destination_snapshot_digest_bound,
            "history_preserved": history_preserved,
            "thresholds_preserved": thresholds_preserved,
            "provenance_policy_preserved": provenance_policy_preserved,
            "eligibility_preserved": eligibility_preserved,
            "federation_quorum_attested": federation_quorum_attested,
            "destination_seeded": destination_seeded,
            "receipt_digest_bound": receipt_digest_bound,
        }
        summary["ok"] = all(summary.values())
        return summary

    @staticmethod
    def _same_actor(agent_id: str, triggered_by: str, triggered_by_agent_id: str) -> bool:
        if triggered_by_agent_id:
            return triggered_by_agent_id == agent_id
        return _actor_fingerprint(agent_id) == _actor_fingerprint(triggered_by)

    @staticmethod
    def _require_mapping_field(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, Mapping):
            errors.append(f"{field_name} must be a mapping")

    @staticmethod
    def _require_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _normalize_non_empty(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()
