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
COGNITIVE_AUDIT_VERIFIER_TRANSPORT_PROFILE_ID = (
    "cognitive-audit-non-loopback-verifier-transport-v1"
)
COGNITIVE_AUDIT_VERIFIER_TRANSPORT_TRACE_PROFILE = "non-loopback-mtls-authority-route-v1"
COGNITIVE_AUDIT_VERIFIER_TRANSPORT_SOCKET_PROFILE = "mtls-socket-trace-v1"
COGNITIVE_AUDIT_VERIFIER_TRANSPORT_OS_OBSERVER_PROFILE = "os-native-tcp-observer-v1"
COGNITIVE_AUDIT_VERIFIER_TRANSPORT_ROUTE_TARGET_PROFILE = (
    "bounded-authority-route-target-discovery-v1"
)


def _verifier_transport_digest_payload(profile: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": profile["schema_version"],
        "profile_id": profile["profile_id"],
        "authority_route_trace_ref": profile["authority_route_trace_ref"],
        "authority_route_trace_digest": profile["authority_route_trace_digest"],
        "authority_plane_ref": profile["authority_plane_ref"],
        "authority_plane_digest": profile["authority_plane_digest"],
        "route_target_discovery_ref": profile["route_target_discovery_ref"],
        "route_target_discovery_digest": profile["route_target_discovery_digest"],
        "council_tier": profile["council_tier"],
        "transport_profile": profile["transport_profile"],
        "trace_profile": profile["trace_profile"],
        "socket_trace_profile": profile["socket_trace_profile"],
        "os_observer_profile": profile["os_observer_profile"],
        "route_target_discovery_profile": profile["route_target_discovery_profile"],
        "route_count": profile["route_count"],
        "distinct_remote_host_count": profile["distinct_remote_host_count"],
        "mtls_authenticated_count": profile["mtls_authenticated_count"],
        "remote_host_refs": profile["remote_host_refs"],
        "remote_host_attestation_refs": profile["remote_host_attestation_refs"],
        "remote_jurisdictions": profile["remote_jurisdictions"],
        "verifier_network_receipt_ids": profile["verifier_network_receipt_ids"],
        "reviewer_jurisdiction_count": profile["reviewer_jurisdiction_count"],
        "reviewer_binding_digest": profile["reviewer_binding_digest"],
        "route_binding_digest": profile["route_binding_digest"],
        "non_loopback_verified": profile["non_loopback_verified"],
        "cross_host_verified": profile["cross_host_verified"],
        "route_trace_authenticated": profile["route_trace_authenticated"],
        "socket_trace_complete": profile["socket_trace_complete"],
        "os_observer_complete": profile["os_observer_complete"],
        "route_target_discovery_bound": profile["route_target_discovery_bound"],
        "no_raw_socket_payload_exposed": profile["no_raw_socket_payload_exposed"],
    }


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
        "verifier_transport_profile": binding["verifier_transport_profile"],
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


def _int_at_least(value: Any, field_name: str, minimum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{field_name} must be an integer >= {minimum}")
    return value


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
            "verifier_transport_profile_id": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_PROFILE_ID,
            "required_verifier_transport_trace_status": "authenticated",
            "non_loopback_verifier_transport_required": True,
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
        verifier_transport_trace: Mapping[str, Any],
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
        normalized_transport = self._normalize_verifier_transport_trace(
            verifier_transport_trace,
            normalized_oversight,
        )
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
            "verifier_transport_profile": normalized_transport,
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
                "non_loopback_verifier_transport_bound": normalized_transport[
                    "route_trace_authenticated"
                ],
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
        verifier_transport_profile = binding.get("verifier_transport_profile", {})

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
        if (
            binding.get("policy", {}).get("verifier_transport_profile_id")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_PROFILE_ID
        ):
            errors.append("policy.verifier_transport_profile_id mismatch")
        if (
            binding.get("policy", {}).get("required_verifier_transport_trace_status")
            != "authenticated"
        ):
            errors.append("policy.required_verifier_transport_trace_status mismatch")
        if binding.get("policy", {}).get("non_loopback_verifier_transport_required") is not True:
            errors.append("policy.non_loopback_verifier_transport_required must be true")
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
        if not continuity_guard.get("non_loopback_verifier_transport_bound"):
            errors.append("continuity_guard.non_loopback_verifier_transport_bound must be true")
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
        transport_errors = self._validate_verifier_transport_profile(
            verifier_transport_profile,
            network_receipt_ids,
            jurisdiction_review_profile,
        )
        errors.extend(transport_errors)

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
            "non_loopback_verifier_transport_bound": (
                continuity_guard.get("non_loopback_verifier_transport_bound") is True
                and not transport_errors
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

    def _normalize_verifier_transport_trace(
        self,
        verifier_transport_trace: Mapping[str, Any],
        normalized_oversight: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(verifier_transport_trace, Mapping):
            raise ValueError("verifier_transport_trace must be a mapping")
        if (
            verifier_transport_trace.get("kind")
            != "distributed_transport_authority_route_trace"
        ):
            raise ValueError("verifier_transport_trace.kind must be distributed_transport_authority_route_trace")
        if verifier_transport_trace.get("trace_status") != "authenticated":
            raise ValueError("verifier transport route trace must be authenticated")
        if (
            verifier_transport_trace.get("trace_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_TRACE_PROFILE
        ):
            raise ValueError("verifier transport trace_profile mismatch")
        if (
            verifier_transport_trace.get("socket_trace_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_SOCKET_PROFILE
        ):
            raise ValueError("verifier transport socket_trace_profile mismatch")
        if (
            verifier_transport_trace.get("os_observer_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_OS_OBSERVER_PROFILE
        ):
            raise ValueError("verifier transport os_observer_profile mismatch")
        if (
            verifier_transport_trace.get("route_target_discovery_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_ROUTE_TARGET_PROFILE
        ):
            raise ValueError("verifier transport route_target_discovery_profile mismatch")

        for flag_name in (
            "non_loopback_verified",
            "authority_plane_bound",
            "response_digest_bound",
            "socket_trace_complete",
            "os_observer_complete",
            "route_target_discovery_bound",
            "cross_host_verified",
        ):
            if verifier_transport_trace.get(flag_name) is not True:
                raise ValueError(f"verifier transport {flag_name} must be true")

        route_count = _int_at_least(verifier_transport_trace.get("route_count"), "route_count", 1)
        distinct_remote_host_count = _int_at_least(
            verifier_transport_trace.get("distinct_remote_host_count"),
            "distinct_remote_host_count",
            COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM,
        )
        mtls_authenticated_count = _int_at_least(
            verifier_transport_trace.get("mtls_authenticated_count"),
            "mtls_authenticated_count",
            route_count,
        )
        if mtls_authenticated_count < route_count:
            raise ValueError("verifier transport must authenticate every traced route")

        route_bindings = verifier_transport_trace.get("route_bindings", [])
        if not isinstance(route_bindings, list) or len(route_bindings) != route_count:
            raise ValueError("verifier transport route_bindings must match route_count")

        remote_host_refs: List[str] = []
        remote_host_attestation_refs: List[str] = []
        remote_jurisdictions: List[str] = []
        route_binding_summaries: List[Dict[str, Any]] = []
        for route_binding in route_bindings:
            if not isinstance(route_binding, Mapping):
                raise ValueError("verifier transport route_bindings must contain mappings")
            remote_host_ref = _non_empty_string(
                route_binding.get("remote_host_ref"),
                "route_bindings[].remote_host_ref",
            )
            remote_host_attestation_ref = _non_empty_string(
                route_binding.get("remote_host_attestation_ref"),
                "route_bindings[].remote_host_attestation_ref",
            )
            remote_jurisdiction = _non_empty_string(
                route_binding.get("remote_jurisdiction"),
                "route_bindings[].remote_jurisdiction",
            )
            if remote_host_ref not in remote_host_refs:
                remote_host_refs.append(remote_host_ref)
            if remote_host_attestation_ref not in remote_host_attestation_refs:
                remote_host_attestation_refs.append(remote_host_attestation_ref)
            if remote_jurisdiction not in remote_jurisdictions:
                remote_jurisdictions.append(remote_jurisdiction)
            socket_trace = route_binding.get("socket_trace", {})
            os_observer_receipt = route_binding.get("os_observer_receipt", {})
            if not isinstance(socket_trace, Mapping) or not isinstance(
                os_observer_receipt,
                Mapping,
            ):
                raise ValueError("verifier transport route binding trace evidence must be mappings")
            route_binding_summaries.append(
                {
                    "route_binding_ref": _non_empty_string(
                        route_binding.get("route_binding_ref"),
                        "route_bindings[].route_binding_ref",
                    ),
                    "remote_host_ref": remote_host_ref,
                    "remote_host_attestation_ref": remote_host_attestation_ref,
                    "remote_jurisdiction": remote_jurisdiction,
                    "socket_response_digest": _non_empty_string(
                        socket_trace.get("response_digest"),
                        "route_bindings[].socket_trace.response_digest",
                    ),
                    "os_observer_host_binding_digest": _non_empty_string(
                        os_observer_receipt.get("host_binding_digest"),
                        "route_bindings[].os_observer_receipt.host_binding_digest",
                    ),
                }
            )

        jurisdiction_profile = normalized_oversight["jurisdiction_review_profile"]
        reviewer_jurisdictions = jurisdiction_profile["jurisdictions"]
        missing_jurisdictions = [
            jurisdiction
            for jurisdiction in reviewer_jurisdictions
            if jurisdiction not in remote_jurisdictions
        ]
        if missing_jurisdictions:
            raise ValueError(
                "verifier transport route trace must cover reviewer jurisdictions"
            )

        profile = {
            "kind": "cognitive_audit_verifier_transport_binding",
            "schema_version": COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION,
            "profile_id": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_PROFILE_ID,
            "authority_route_trace_ref": _non_empty_string(
                verifier_transport_trace.get("trace_ref"),
                "verifier_transport_trace.trace_ref",
            ),
            "authority_route_trace_digest": _non_empty_string(
                verifier_transport_trace.get("digest"),
                "verifier_transport_trace.digest",
            ),
            "authority_plane_ref": _non_empty_string(
                verifier_transport_trace.get("authority_plane_ref"),
                "verifier_transport_trace.authority_plane_ref",
            ),
            "authority_plane_digest": _non_empty_string(
                verifier_transport_trace.get("authority_plane_digest"),
                "verifier_transport_trace.authority_plane_digest",
            ),
            "route_target_discovery_ref": _non_empty_string(
                verifier_transport_trace.get("route_target_discovery_ref"),
                "verifier_transport_trace.route_target_discovery_ref",
            ),
            "route_target_discovery_digest": _non_empty_string(
                verifier_transport_trace.get("route_target_discovery_digest"),
                "verifier_transport_trace.route_target_discovery_digest",
            ),
            "council_tier": _non_empty_string(
                verifier_transport_trace.get("council_tier"),
                "verifier_transport_trace.council_tier",
            ),
            "transport_profile": _non_empty_string(
                verifier_transport_trace.get("transport_profile"),
                "verifier_transport_trace.transport_profile",
            ),
            "trace_profile": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_TRACE_PROFILE,
            "socket_trace_profile": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_SOCKET_PROFILE,
            "os_observer_profile": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_OS_OBSERVER_PROFILE,
            "route_target_discovery_profile": COGNITIVE_AUDIT_VERIFIER_TRANSPORT_ROUTE_TARGET_PROFILE,
            "route_count": route_count,
            "distinct_remote_host_count": distinct_remote_host_count,
            "mtls_authenticated_count": mtls_authenticated_count,
            "remote_host_refs": remote_host_refs,
            "remote_host_attestation_refs": remote_host_attestation_refs,
            "remote_jurisdictions": remote_jurisdictions,
            "verifier_network_receipt_ids": list(normalized_oversight["network_receipt_ids"]),
            "reviewer_jurisdiction_count": jurisdiction_profile["reviewer_jurisdiction_count"],
            "reviewer_binding_digest": jurisdiction_profile["reviewer_binding_digest"],
            "route_binding_digest": sha256_text(canonical_json(route_binding_summaries)),
            "non_loopback_verified": True,
            "cross_host_verified": True,
            "route_trace_authenticated": True,
            "socket_trace_complete": True,
            "os_observer_complete": True,
            "route_target_discovery_bound": True,
            "no_raw_socket_payload_exposed": True,
        }
        profile["digest"] = sha256_text(canonical_json(_verifier_transport_digest_payload(profile)))
        return profile

    def _validate_verifier_transport_profile(
        self,
        profile: Any,
        network_receipt_ids: Sequence[Any],
        jurisdiction_review_profile: Any,
    ) -> List[str]:
        errors: List[str] = []
        if not isinstance(profile, Mapping):
            return ["verifier_transport_profile must be a mapping"]
        if profile.get("kind") != "cognitive_audit_verifier_transport_binding":
            errors.append("verifier_transport_profile.kind mismatch")
        if profile.get("schema_version") != COGNITIVE_AUDIT_GOVERNANCE_SCHEMA_VERSION:
            errors.append("verifier_transport_profile.schema_version mismatch")
        if profile.get("profile_id") != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_PROFILE_ID:
            errors.append("verifier_transport_profile.profile_id mismatch")
        if profile.get("trace_profile") != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_TRACE_PROFILE:
            errors.append("verifier_transport_profile.trace_profile mismatch")
        if profile.get("socket_trace_profile") != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_SOCKET_PROFILE:
            errors.append("verifier_transport_profile.socket_trace_profile mismatch")
        if (
            profile.get("os_observer_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_OS_OBSERVER_PROFILE
        ):
            errors.append("verifier_transport_profile.os_observer_profile mismatch")
        if (
            profile.get("route_target_discovery_profile")
            != COGNITIVE_AUDIT_VERIFIER_TRANSPORT_ROUTE_TARGET_PROFILE
        ):
            errors.append("verifier_transport_profile.route_target_discovery_profile mismatch")
        if profile.get("verifier_network_receipt_ids") != list(network_receipt_ids):
            errors.append("verifier_transport_profile.verifier_network_receipt_ids mismatch")
        if isinstance(jurisdiction_review_profile, Mapping):
            if (
                profile.get("reviewer_jurisdiction_count")
                != jurisdiction_review_profile.get("reviewer_jurisdiction_count")
            ):
                errors.append("verifier_transport_profile.reviewer_jurisdiction_count mismatch")
            if (
                profile.get("reviewer_binding_digest")
                != jurisdiction_review_profile.get("reviewer_binding_digest")
            ):
                errors.append("verifier_transport_profile.reviewer_binding_digest mismatch")
            for jurisdiction in jurisdiction_review_profile.get("jurisdictions", []):
                if jurisdiction not in profile.get("remote_jurisdictions", []):
                    errors.append("verifier_transport_profile.remote_jurisdictions incomplete")
                    break
        if profile.get("route_count", 0) < COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM:
            errors.append("verifier_transport_profile.route_count below reviewer quorum")
        if profile.get("distinct_remote_host_count", 0) < COGNITIVE_AUDIT_REQUIRED_JURISDICTION_QUORUM:
            errors.append("verifier_transport_profile.distinct_remote_host_count below reviewer quorum")
        if profile.get("mtls_authenticated_count", 0) < profile.get("route_count", 0):
            errors.append("verifier_transport_profile.mtls_authenticated_count below route_count")
        for flag_name in (
            "non_loopback_verified",
            "cross_host_verified",
            "route_trace_authenticated",
            "socket_trace_complete",
            "os_observer_complete",
            "route_target_discovery_bound",
            "no_raw_socket_payload_exposed",
        ):
            if profile.get(flag_name) is not True:
                errors.append(f"verifier_transport_profile.{flag_name} must be true")
        if profile.get("digest"):
            try:
                expected_digest = sha256_text(
                    canonical_json(_verifier_transport_digest_payload(profile))
                )
            except KeyError as exc:
                errors.append(f"verifier_transport_profile missing {exc.args[0]}")
            else:
                if profile.get("digest") != expected_digest:
                    errors.append("verifier_transport_profile.digest mismatch")
        else:
            errors.append("verifier_transport_profile.digest must be present")
        return errors

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
