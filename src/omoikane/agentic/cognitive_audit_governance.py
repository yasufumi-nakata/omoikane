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
COGNITIVE_AUDIT_JURISDICTION_REVIEW_PROFILE_ID = (
    "cognitive-audit-multi-jurisdiction-review-v1"
)
COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM = 2
COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_PROFILE_ID = (
    "distributed-council-verdict-signature-binding-v1"
)
COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_ALGORITHM = "sha256-reference-signature-v1"


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
        "jurisdiction_review_profile": binding["jurisdiction_review_profile"],
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
            "jurisdiction_review_profile_id": COGNITIVE_AUDIT_JURISDICTION_REVIEW_PROFILE_ID,
            "required_jurisdiction_quorum": COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM,
            "distributed_verdict_signature_profile_id": (
                COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_PROFILE_ID
            ),
            "distributed_verdict_signature_algorithm": (
                COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_ALGORITHM
            ),
            "distributed_verdict_signatures_required": True,
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
            "jurisdiction_review_profile": normalized_oversight["jurisdiction_review_profile"],
            "continuity_guard": {
                "local_resolution_preserved": True,
                "distributed_refs_present": bool(distributed_verdicts),
                "oversight_quorum_satisfied": True,
                "network_receipts_bound": normalized_oversight["network_bound"],
                "multi_jurisdiction_review_bound": normalized_oversight[
                    "jurisdiction_review_profile"
                ]["multi_jurisdiction_quorum_met"],
                "distributed_verdict_signatures_bound": self._distributed_verdict_signatures_bound(
                    distributed_verdicts
                ),
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
        jurisdiction_review_profile = binding.get("jurisdiction_review_profile", {})

        if binding.get("kind") != "cognitive_audit_governance_binding":
            errors.append("kind must equal cognitive_audit_governance_binding")
        if binding.get("schema_version") != COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if binding.get("policy", {}).get("policy_id") != COGNITIVE_AUDIT_GOVERNANCE_POLICY_ID:
            errors.append("policy.policy_id mismatch")
        if (
            binding.get("policy", {}).get("jurisdiction_review_profile_id")
            != COGNITIVE_AUDIT_JURISDICTION_REVIEW_PROFILE_ID
        ):
            errors.append("policy.jurisdiction_review_profile_id mismatch")
        if (
            binding.get("policy", {}).get("required_jurisdiction_quorum")
            != COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM
        ):
            errors.append("policy.required_jurisdiction_quorum mismatch")
        if (
            binding.get("policy", {}).get("distributed_verdict_signature_profile_id")
            != COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_PROFILE_ID
        ):
            errors.append("policy.distributed_verdict_signature_profile_id mismatch")
        if (
            binding.get("policy", {}).get("distributed_verdict_signature_algorithm")
            != COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_ALGORITHM
        ):
            errors.append("policy.distributed_verdict_signature_algorithm mismatch")
        if binding.get("policy", {}).get("distributed_verdict_signatures_required") is not True:
            errors.append("policy.distributed_verdict_signatures_required must be true")
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
        if not continuity_guard.get("multi_jurisdiction_review_bound"):
            errors.append("continuity_guard.multi_jurisdiction_review_bound must be true")
        if not continuity_guard.get("distributed_verdict_signatures_bound"):
            errors.append("continuity_guard.distributed_verdict_signatures_bound must be true")
        if continuity_guard.get("no_raw_payload_exposed") is not True:
            errors.append("continuity_guard.no_raw_payload_exposed must be true")
        if not isinstance(jurisdiction_review_profile, Mapping):
            errors.append("jurisdiction_review_profile must be a mapping")
        else:
            if (
                jurisdiction_review_profile.get("profile_id")
                != COGNITIVE_AUDIT_JURISDICTION_REVIEW_PROFILE_ID
            ):
                errors.append("jurisdiction_review_profile.profile_id mismatch")
            if (
                jurisdiction_review_profile.get("required_jurisdiction_quorum")
                != COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM
            ):
                errors.append("jurisdiction_review_profile.required_jurisdiction_quorum mismatch")
            if jurisdiction_review_profile.get("reviewer_jurisdiction_count", 0) < (
                COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM
            ):
                errors.append("jurisdiction_review_profile reviewer jurisdiction quorum not met")
            if jurisdiction_review_profile.get("multi_jurisdiction_quorum_met") is not True:
                errors.append("jurisdiction_review_profile.multi_jurisdiction_quorum_met must be true")
            if jurisdiction_review_profile.get("network_receipt_count") != len(network_receipt_ids):
                errors.append("jurisdiction_review_profile.network_receipt_count mismatch")

        tiers = [verdict.get("council_tier") for verdict in distributed_verdicts]
        if len(tiers) != len(set(tiers)):
            errors.append("distributed_verdicts council_tier values must be unique")
        signature_errors = self._validate_distributed_verdict_signatures(distributed_verdicts)
        errors.extend(signature_errors)

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
            "multi_jurisdiction_review_bound": continuity_guard.get(
                "multi_jurisdiction_review_bound"
            )
            is True
            and isinstance(jurisdiction_review_profile, Mapping)
            and jurisdiction_review_profile.get("multi_jurisdiction_quorum_met") is True,
            "distributed_signature_bound": (
                continuity_guard.get("distributed_verdict_signatures_bound") is True
                and not signature_errors
            ),
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
        jurisdiction_review_profile = self._build_jurisdiction_review_profile(reviewer_bindings)
        return {
            "event_id": event_id,
            "reviewer_binding_count": len(reviewer_bindings),
            "network_receipt_ids": network_receipt_ids,
            "network_bound": len(network_receipt_ids) == len(reviewer_bindings),
            "jurisdiction_review_profile": jurisdiction_review_profile,
        }

    def _build_jurisdiction_review_profile(
        self,
        reviewer_bindings: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        normalized_bindings: List[Dict[str, Any]] = []
        jurisdictions: List[str] = []
        legal_policy_refs: List[str] = []
        jurisdiction_bundle_refs: List[str] = []
        legal_execution_ids: List[str] = []
        network_receipt_ids: List[str] = []
        for binding in reviewer_bindings:
            reviewer_id = _non_empty_string(
                binding.get("reviewer_id"),
                "oversight_event.reviewer_bindings[].reviewer_id",
            )
            jurisdiction = _non_empty_string(
                binding.get("jurisdiction"),
                "oversight_event.reviewer_bindings[].jurisdiction",
            )
            legal_policy_ref = _non_empty_string(
                binding.get("legal_policy_ref"),
                "oversight_event.reviewer_bindings[].legal_policy_ref",
            )
            jurisdiction_bundle_ref = _non_empty_string(
                binding.get("jurisdiction_bundle_ref"),
                "oversight_event.reviewer_bindings[].jurisdiction_bundle_ref",
            )
            jurisdiction_bundle_digest = _non_empty_string(
                binding.get("jurisdiction_bundle_digest"),
                "oversight_event.reviewer_bindings[].jurisdiction_bundle_digest",
            )
            legal_execution_id = _non_empty_string(
                binding.get("legal_execution_id"),
                "oversight_event.reviewer_bindings[].legal_execution_id",
            )
            legal_execution_digest = _non_empty_string(
                binding.get("legal_execution_digest"),
                "oversight_event.reviewer_bindings[].legal_execution_digest",
            )
            network_receipt_id = _non_empty_string(
                binding.get("network_receipt_id"),
                "oversight_event.reviewer_bindings[].network_receipt_id",
            )
            if jurisdiction not in jurisdictions:
                jurisdictions.append(jurisdiction)
            if legal_policy_ref not in legal_policy_refs:
                legal_policy_refs.append(legal_policy_ref)
            if jurisdiction_bundle_ref not in jurisdiction_bundle_refs:
                jurisdiction_bundle_refs.append(jurisdiction_bundle_ref)
            if legal_execution_id not in legal_execution_ids:
                legal_execution_ids.append(legal_execution_id)
            if network_receipt_id not in network_receipt_ids:
                network_receipt_ids.append(network_receipt_id)
            normalized_bindings.append(
                {
                    "reviewer_id": reviewer_id,
                    "jurisdiction": jurisdiction,
                    "legal_policy_ref": legal_policy_ref,
                    "jurisdiction_bundle_ref": jurisdiction_bundle_ref,
                    "jurisdiction_bundle_digest": jurisdiction_bundle_digest,
                    "legal_execution_id": legal_execution_id,
                    "legal_execution_digest": legal_execution_digest,
                    "network_receipt_id": network_receipt_id,
                }
            )
        multi_jurisdiction_quorum_met = (
            len(jurisdictions) >= COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM
        )
        if not multi_jurisdiction_quorum_met:
            raise ValueError("cognitive audit governance requires multi-jurisdiction reviewer quorum")
        return {
            "profile_id": COGNITIVE_AUDIT_JURISDICTION_REVIEW_PROFILE_ID,
            "required_jurisdiction_quorum": COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM,
            "reviewer_jurisdiction_count": len(jurisdictions),
            "jurisdictions": jurisdictions,
            "legal_policy_refs": legal_policy_refs,
            "jurisdiction_bundle_refs": jurisdiction_bundle_refs,
            "legal_execution_ids": legal_execution_ids,
            "network_receipt_count": len(network_receipt_ids),
            "reviewer_binding_digest": sha256_text(canonical_json(normalized_bindings)),
            "multi_jurisdiction_quorum_met": multi_jurisdiction_quorum_met,
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
            verdict = {
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
            verdict["signature_binding"] = self._build_distributed_verdict_signature(verdict)
            verdicts.append(verdict)
        return verdicts

    def _build_distributed_verdict_signature(
        self,
        verdict_without_signature: Mapping[str, Any],
    ) -> Dict[str, Any]:
        council_tier = _non_empty_string(
            verdict_without_signature.get("council_tier"),
            "distributed_verdict.council_tier",
        )
        resolution_ref = _non_empty_string(
            verdict_without_signature.get("resolution_ref"),
            "distributed_verdict.resolution_ref",
        )
        signer_ref = f"council://{council_tier}/returned-result-signer/v1"
        public_key_ref = f"key://{council_tier}/returned-result/reference-v1"
        signed_payload_digest = sha256_text(canonical_json(verdict_without_signature))
        signature_payload = {
            "profile_id": COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_PROFILE_ID,
            "signature_algorithm": COGNITIVE_AUDIT_DISTRIBUTED_VERDICT_SIGNATURE_ALGORITHM,
            "signer_ref": signer_ref,
            "public_key_ref": public_key_ref,
            "signed_resolution_ref": resolution_ref,
            "signed_payload_digest": signed_payload_digest,
        }
        return {
            **signature_payload,
            "signature_digest": sha256_text(canonical_json(signature_payload)),
            "raw_signature_payload_exposed": False,
        }

    def _distributed_verdict_signatures_bound(
        self,
        verdicts: Sequence[Mapping[str, Any]],
    ) -> bool:
        return not self._validate_distributed_verdict_signatures(verdicts)

    def _validate_distributed_verdict_signatures(
        self,
        verdicts: Sequence[Any],
    ) -> List[str]:
        errors: List[str] = []
        for index, verdict in enumerate(verdicts):
            if not isinstance(verdict, Mapping):
                errors.append(f"distributed_verdicts[{index}] must be a mapping")
                continue
            signature_binding = verdict.get("signature_binding")
            if not isinstance(signature_binding, Mapping):
                errors.append(f"distributed_verdicts[{index}].signature_binding must be present")
                continue
            unsigned_verdict = dict(verdict)
            unsigned_verdict.pop("signature_binding", None)
            expected_signature = self._build_distributed_verdict_signature(unsigned_verdict)
            for field_name, expected_value in expected_signature.items():
                if signature_binding.get(field_name) != expected_value:
                    errors.append(
                        f"distributed_verdicts[{index}].signature_binding.{field_name} mismatch"
                    )
        return errors
