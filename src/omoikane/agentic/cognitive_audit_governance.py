"""Governance binding for cognitive audit follow-up."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION = "1.0.0"
COGNITIVE_AUDIT_GOVERNANCE_POLICY_ID = "cognitive-audit-governance-binding-v1"
COGNITIVE_AUDIT_ALLOWED_FOLLOW_UP_ACTIONS = {
    "continue-monitoring",
    "open-guardian-review",
    "activate-containment",
    "preserve-boundary",
    "schedule-standard-session",
    "escalate-to-human-governance",
}
COGNITIVE_AUDIT_ALLOWED_EXECUTION_GATES = {
    "oversight-attested-local",
    "federation-attested-review",
    "heritage-veto-boundary",
    "distributed-conflict-human-escalation",
}
COGNITIVE_AUDIT_ALLOWED_COUNCIL_TIERS = {"federation", "heritage"}
COGNITIVE_AUDIT_MAX_DISTRIBUTED_VERDICTS = 2


def _binding_digest_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": binding["schema_version"],
        "policy": binding["policy"],
        "audit_ref": binding["audit_ref"],
        "local_resolution_ref": binding["local_resolution_ref"],
        "local_follow_up_action": binding["local_follow_up_action"],
        "final_follow_up_action": binding["final_follow_up_action"],
        "execution_gate": binding["execution_gate"],
        "distributed_verdicts": binding["distributed_verdicts"],
        "external_resolution_refs": binding["external_resolution_refs"],
        "oversight_event_ref": binding["oversight_event_ref"],
        "reviewer_binding_count": binding["reviewer_binding_count"],
        "network_receipt_ids": binding["network_receipt_ids"],
        "continuity_guard": binding["continuity_guard"],
    }


def _non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _unique_strings(values: Sequence[Any], field_name: str) -> List[str]:
    unique: List[str] = []
    for value in values:
        normalized = _non_empty_string(value, field_name)
        if normalized not in unique:
            unique.append(normalized)
    return unique


class CognitiveAuditGovernanceService:
    """Bind local cognitive-audit outcomes to distributed council and oversight evidence."""

    @staticmethod
    def reference_policy() -> Dict[str, Any]:
        return {
            "schema_version": COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION,
            "policy_id": COGNITIVE_AUDIT_GOVERNANCE_POLICY_ID,
            "accepted_council_tiers": sorted(COGNITIVE_AUDIT_ALLOWED_COUNCIL_TIERS),
            "max_distributed_verdicts": COGNITIVE_AUDIT_MAX_DISTRIBUTED_VERDICTS,
            "required_oversight_status": "satisfied",
            "required_network_receipt_for_review": True,
            "conflict_action": "escalate-to-human-governance",
            "heritage_veto_action": "preserve-boundary",
            "raw_payload_policy": "digest-and-ref-only",
        }

    def bind_governance(
        self,
        record: Mapping[str, Any],
        local_resolution: Mapping[str, Any],
        *,
        distributed_resolutions: Sequence[Mapping[str, Any]] = (),
        oversight_event: Mapping[str, Any],
    ) -> Dict[str, Any]:
        audit_ref = _non_empty_string(record.get("audit_id"), "record.audit_id")
        if local_resolution.get("audit_ref") != audit_ref:
            raise ValueError("local_resolution.audit_ref must match record.audit_id")

        local_follow_up_action = _non_empty_string(
            local_resolution.get("follow_up_action"),
            "local_resolution.follow_up_action",
        )
        if local_follow_up_action not in COGNITIVE_AUDIT_ALLOWED_FOLLOW_UP_ACTIONS:
            raise ValueError("local_resolution.follow_up_action is invalid")

        normalized_oversight = self._normalize_oversight_event(oversight_event)
        distributed_verdicts = self._normalize_distributed_resolutions(distributed_resolutions)

        federation_approved = any(
            verdict["council_tier"] == "federation"
            and verdict["final_outcome"] == "binding-approved"
            for verdict in distributed_verdicts
        )
        heritage_rejected = any(
            verdict["council_tier"] == "heritage"
            and verdict["final_outcome"] == "binding-rejected"
            for verdict in distributed_verdicts
        )
        external_escalation = any(
            verdict["final_outcome"] == "escalate-human-governance"
            for verdict in distributed_verdicts
        )
        conflict_detected = external_escalation or (federation_approved and heritage_rejected)

        if conflict_detected:
            final_follow_up_action = "escalate-to-human-governance"
            execution_gate = "distributed-conflict-human-escalation"
        elif heritage_rejected:
            final_follow_up_action = "preserve-boundary"
            execution_gate = "heritage-veto-boundary"
        elif federation_approved:
            final_follow_up_action = local_follow_up_action
            execution_gate = "federation-attested-review"
        else:
            final_follow_up_action = local_follow_up_action
            execution_gate = "oversight-attested-local"

        if (
            final_follow_up_action in {"open-guardian-review", "activate-containment"}
            and not normalized_oversight["network_receipt_ids"]
        ):
            raise ValueError("network-bound oversight evidence is required for review follow-up")

        binding = {
            "kind": "cognitive_audit_governance_binding",
            "schema_version": COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION,
            "binding_id": new_id("cognitive-audit-governance"),
            "recorded_at": utc_now_iso(),
            "policy": self.reference_policy(),
            "audit_ref": audit_ref,
            "local_resolution_ref": _non_empty_string(
                local_resolution.get("resolution_id"),
                "local_resolution.resolution_id",
            ),
            "local_follow_up_action": local_follow_up_action,
            "final_follow_up_action": final_follow_up_action,
            "execution_gate": execution_gate,
            "distributed_verdicts": distributed_verdicts,
            "external_resolution_refs": _unique_strings(
                [
                    external_ref
                    for verdict in distributed_verdicts
                    for external_ref in verdict["external_resolution_refs"]
                ],
                "external_resolution_refs",
            ),
            "oversight_event_ref": normalized_oversight["event_id"],
            "reviewer_binding_count": normalized_oversight["reviewer_binding_count"],
            "network_receipt_ids": normalized_oversight["network_receipt_ids"],
            "continuity_guard": {
                "local_resolution_preserved": True,
                "distributed_refs_present": bool(distributed_verdicts),
                "oversight_quorum_satisfied": True,
                "network_receipts_bound": normalized_oversight["network_bound"],
                "no_raw_payload_exposed": True,
                "conflict_detected": conflict_detected,
            },
        }
        binding["digest"] = sha256_text(canonical_json(_binding_digest_payload(binding)))
        return binding

    def validate_binding(self, binding: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        execution_gate = binding.get("execution_gate")
        final_follow_up_action = binding.get("final_follow_up_action")
        distributed_verdicts = binding.get("distributed_verdicts", [])
        continuity_guard = binding.get("continuity_guard", {})
        network_receipt_ids = binding.get("network_receipt_ids", [])

        if binding.get("kind") != "cognitive_audit_governance_binding":
            errors.append("kind must equal cognitive_audit_governance_binding")
        if binding.get("schema_version") != COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if binding.get("policy", {}).get("policy_id") != COGNITIVE_AUDIT_GOVERNANCE_POLICY_ID:
            errors.append("policy.policy_id mismatch")
        if execution_gate not in COGNITIVE_AUDIT_ALLOWED_EXECUTION_GATES:
            errors.append("execution_gate invalid")
        if final_follow_up_action not in COGNITIVE_AUDIT_ALLOWED_FOLLOW_UP_ACTIONS:
            errors.append("final_follow_up_action invalid")
        if not isinstance(distributed_verdicts, list) or (
            len(distributed_verdicts) > COGNITIVE_AUDIT_MAX_DISTRIBUTED_VERDICTS
        ):
            errors.append("distributed_verdicts exceeds max_distributed_verdicts")
        if not isinstance(network_receipt_ids, list) or not all(
            isinstance(receipt_id, str) and receipt_id
            for receipt_id in network_receipt_ids
        ):
            errors.append("network_receipt_ids must contain non-empty strings")
        if not continuity_guard.get("local_resolution_preserved"):
            errors.append("continuity_guard.local_resolution_preserved must be true")
        if not continuity_guard.get("oversight_quorum_satisfied"):
            errors.append("continuity_guard.oversight_quorum_satisfied must be true")
        if not continuity_guard.get("network_receipts_bound"):
            errors.append("continuity_guard.network_receipts_bound must be true")
        if continuity_guard.get("no_raw_payload_exposed") is not True:
            errors.append("continuity_guard.no_raw_payload_exposed must be true")

        tiers = [verdict.get("council_tier") for verdict in distributed_verdicts]
        if len(tiers) != len(set(tiers)):
            errors.append("distributed_verdicts council_tier values must be unique")

        federation_approved = any(
            verdict.get("council_tier") == "federation"
            and verdict.get("final_outcome") == "binding-approved"
            for verdict in distributed_verdicts
        )
        heritage_rejected = any(
            verdict.get("council_tier") == "heritage"
            and verdict.get("final_outcome") == "binding-rejected"
            for verdict in distributed_verdicts
        )
        conflict_detected = bool(continuity_guard.get("conflict_detected"))

        if execution_gate == "federation-attested-review":
            if not federation_approved:
                errors.append("federation-attested-review requires a binding-approved federation verdict")
            if final_follow_up_action not in {"open-guardian-review", "activate-containment"}:
                errors.append("federation-attested-review must preserve a review-oriented follow-up action")
        elif execution_gate == "heritage-veto-boundary":
            if not heritage_rejected:
                errors.append("heritage-veto-boundary requires a binding-rejected heritage verdict")
            if final_follow_up_action != "preserve-boundary":
                errors.append("heritage-veto-boundary must preserve-boundary")
        elif execution_gate == "distributed-conflict-human-escalation":
            if not conflict_detected:
                errors.append("distributed-conflict-human-escalation requires continuity_guard.conflict_detected")
            if final_follow_up_action != "escalate-to-human-governance":
                errors.append("distributed-conflict-human-escalation must escalate to human governance")
        elif execution_gate == "oversight-attested-local":
            if distributed_verdicts and not (federation_approved or heritage_rejected):
                errors.append("oversight-attested-local cannot carry unresolved distributed verdicts")

        return {
            "ok": not errors,
            "execution_gate": execution_gate,
            "final_follow_up_action": final_follow_up_action,
            "distributed_verdict_count": len(distributed_verdicts),
            "oversight_network_bound": bool(network_receipt_ids)
            and continuity_guard.get("network_receipts_bound") is True,
            "errors": errors,
        }

    def _normalize_oversight_event(self, oversight_event: Mapping[str, Any]) -> Dict[str, Any]:
        event_id = _non_empty_string(oversight_event.get("event_id"), "oversight_event.event_id")
        human_attestation = oversight_event.get("human_attestation", {})
        if human_attestation.get("status") != "satisfied":
            raise ValueError("oversight_event.human_attestation.status must be satisfied")
        reviewer_bindings = oversight_event.get("reviewer_bindings", [])
        if not isinstance(reviewer_bindings, list) or not reviewer_bindings:
            raise ValueError("oversight_event.reviewer_bindings must contain at least one binding")
        network_receipt_ids = _unique_strings(
            [
                binding.get("network_receipt_id")
                for binding in reviewer_bindings
                if binding.get("network_receipt_id")
            ],
            "oversight_event.reviewer_bindings[].network_receipt_id",
        )
        if len(network_receipt_ids) != len(reviewer_bindings):
            raise ValueError("each reviewer binding must carry one network_receipt_id")
        return {
            "event_id": event_id,
            "reviewer_binding_count": len(reviewer_bindings),
            "network_receipt_ids": network_receipt_ids,
            "network_bound": len(network_receipt_ids) == len(reviewer_bindings),
        }

    def _normalize_distributed_resolutions(
        self,
        distributed_resolutions: Sequence[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        if len(distributed_resolutions) > COGNITIVE_AUDIT_MAX_DISTRIBUTED_VERDICTS:
            raise ValueError("distributed_resolutions exceeds max_distributed_verdicts")

        verdicts: List[Dict[str, Any]] = []
        seen_tiers = set()
        for resolution in distributed_resolutions:
            council_tier = _non_empty_string(
                resolution.get("council_tier"),
                "distributed_resolution.council_tier",
            )
            if council_tier not in COGNITIVE_AUDIT_ALLOWED_COUNCIL_TIERS:
                raise ValueError("distributed_resolution.council_tier must be federation or heritage")
            if council_tier in seen_tiers:
                raise ValueError("distributed_resolution.council_tier values must be unique")
            seen_tiers.add(council_tier)
            verdicts.append(
                {
                    "council_tier": council_tier,
                    "resolution_ref": _non_empty_string(
                        resolution.get("resolution_id"),
                        "distributed_resolution.resolution_id",
                    ),
                    "topology_ref": _non_empty_string(
                        resolution.get("topology_ref"),
                        "distributed_resolution.topology_ref",
                    ),
                    "final_outcome": _non_empty_string(
                        resolution.get("final_outcome"),
                        "distributed_resolution.final_outcome",
                    ),
                    "decision_mode": _non_empty_string(
                        resolution.get("decision_mode"),
                        "distributed_resolution.decision_mode",
                    ),
                    "conflict_resolution": _non_empty_string(
                        resolution.get("conflict_resolution"),
                        "distributed_resolution.conflict_resolution",
                    ),
                    "follow_up_action": _non_empty_string(
                        resolution.get("follow_up_action"),
                        "distributed_resolution.follow_up_action",
                    ),
                    "external_resolution_refs": _unique_strings(
                        resolution.get("external_resolution_refs", []),
                        "distributed_resolution.external_resolution_refs",
                    ),
                }
            )
        return verdicts
