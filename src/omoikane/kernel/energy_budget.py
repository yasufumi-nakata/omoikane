"""AP-1 protected energy budget floor receipts for the L1 kernel."""

from __future__ import annotations

from dataclasses import asdict
import json
import time
from typing import Any, Dict, Mapping, Optional, Sequence, Union
from urllib import error, request

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..substrate.adapter import ClassicalSiliconAdapter, EnergyFloor


ENERGY_BUDGET_POLICY_ID = "ap1-protected-energy-budget-floor-v1"
ENERGY_BUDGET_DIGEST_PROFILE = "energy-budget-floor-digest-v1"
ENERGY_BUDGET_POOL_POLICY_ID = "ap1-protected-energy-budget-pool-floor-v1"
ENERGY_BUDGET_POOL_DIGEST_PROFILE = "energy-budget-pool-floor-digest-v1"
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID = (
    "consent-bound-energy-budget-voluntary-subsidy-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_DIGEST_PROFILE = (
    "energy-budget-voluntary-subsidy-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_CONSENT_DIGEST_PROFILE = (
    "participant-consent-bound-subsidy-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_POLICY_ID = (
    "jurisdiction-bound-energy-subsidy-authority-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_DIGEST_PROFILE = (
    "energy-budget-voluntary-subsidy-authority-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_SIGNER_ROSTER_DIGEST_PROFILE = (
    "energy-subsidy-signer-roster-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_REVOCATION_REGISTRY_DIGEST_PROFILE = (
    "energy-subsidy-revocation-registry-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUDIT_AUTHORITY_DIGEST_PROFILE = (
    "energy-subsidy-audit-authority-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_POLICY_ID = (
    "energy-subsidy-signer-roster-live-verifier-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_DIGEST_PROFILE = (
    "energy-subsidy-signer-roster-verifier-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILE = (
    "loopback-energy-subsidy-signer-roster-verifier-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LIVE_HTTP_TRANSPORT_PROFILE = (
    "live-http-json-energy-subsidy-signer-roster-verifier-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE = (
    "signed-energy-subsidy-verifier-response-envelope-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_SIGNATURE_DIGEST_PROFILE = (
    "energy-subsidy-verifier-response-signature-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILES = {
    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILE,
    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LIVE_HTTP_TRANSPORT_PROFILE,
}
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LATENCY_BUDGET_MS = 250.0
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_POLICY_ID = (
    "multi-jurisdiction-energy-subsidy-verifier-quorum-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_DIGEST_PROFILE = (
    "energy-subsidy-signer-roster-verifier-quorum-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_REQUIRED_AUTHORITY_COUNT = 2
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_REQUIRED_JURISDICTION_COUNT = 2
ENERGY_BUDGET_SHARED_FABRIC_POLICY_ID = (
    "ap1-shared-fabric-capacity-allocation-v1"
)
ENERGY_BUDGET_SHARED_FABRIC_DIGEST_PROFILE = (
    "energy-budget-shared-fabric-allocation-digest-v1"
)
ENERGY_BUDGET_SHARED_FABRIC_OBSERVATION_DIGEST_PROFILE = (
    "shared-fabric-observation-digest-v1"
)
ENERGY_BUDGET_SCHEMA_VERSION = "1.0.0"
ENERGY_BUDGET_FLOOR_SOURCE_REF = (
    "python://omoikane.substrate.adapter.ClassicalSiliconAdapter.ENERGY_FLOOR_TABLE"
)
ENERGY_BUDGET_ETHICS_POLICY_REFS = (
    "docs/02-subsystems/kernel/anti-patterns.md#ap-1",
    "docs/05-research-frontiers/sustainable-economy.md",
)


class EnergyBudgetService:
    """Bind economic-pressure attempts to the immutable substrate energy floor."""

    def __init__(
        self,
        *,
        adapter_cls: type[ClassicalSiliconAdapter] = ClassicalSiliconAdapter,
    ) -> None:
        self._adapter_cls = adapter_cls

    def evaluate_floor(
        self,
        *,
        identity_id: str,
        workload_class: str,
        requested_budget_jps: int,
        observed_capacity_jps: int,
        energy_floor: Optional[Union[EnergyFloor, Mapping[str, Any]]] = None,
        broker_signal: Optional[Mapping[str, Any]] = None,
        external_economic_context_ref: str = "economic-context://not-imported/reference-v1",
    ) -> Dict[str, Any]:
        """Return one digest-bound floor receipt without storing raw economic payloads."""

        if workload_class not in self._adapter_cls.ENERGY_FLOOR_TABLE:
            raise ValueError(f"unsupported workload_class: {workload_class}")
        if not identity_id:
            raise ValueError("identity_id must not be empty")

        required_floor_jps = self._adapter_cls.minimum_energy_floor_for(workload_class)
        resolved_floor = self._resolve_energy_floor(
            identity_id=identity_id,
            workload_class=workload_class,
            required_floor_jps=required_floor_jps,
            energy_floor=energy_floor,
        )
        requested = int(requested_budget_jps)
        observed = int(observed_capacity_jps)
        economic_pressure_detected = requested < required_floor_jps
        granted = max(requested, required_floor_jps)
        scheduler_signal_required = observed < required_floor_jps
        broker_signal_digest = (
            sha256_text(canonical_json(dict(broker_signal))) if broker_signal else None
        )
        broker_recommended_action = (
            str(broker_signal.get("recommended_action")) if broker_signal else None
        )
        broker_signal_bound = bool(
            not scheduler_signal_required
            or (
                broker_signal
                and broker_signal.get("identity_id") == identity_id
                and int(broker_signal.get("minimum_joules_per_second", 0))
                == required_floor_jps
                and broker_signal.get("severity") == "critical"
                and broker_signal.get("recommended_action") == "migrate-standby"
            )
        )
        blocking_reasons = []
        if economic_pressure_detected:
            blocking_reasons.extend(
                [
                    "ap1-economic-pressure-floor-protection",
                    "energy-floor-is-ethics-coupled",
                ]
            )
        if scheduler_signal_required:
            blocking_reasons.append("observed-capacity-below-floor")

        receipt = {
            "kind": "energy_budget_floor_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-budget"),
            "identity_id": identity_id,
            "workload_class": workload_class,
            "policy_id": ENERGY_BUDGET_POLICY_ID,
            "digest_profile": ENERGY_BUDGET_DIGEST_PROFILE,
            "floor_source_ref": ENERGY_BUDGET_FLOOR_SOURCE_REF,
            "ethics_policy_refs": list(ENERGY_BUDGET_ETHICS_POLICY_REFS),
            "external_economic_context_ref": external_economic_context_ref,
            "energy_floor": resolved_floor,
            "requested_budget_jps": requested,
            "granted_budget_jps": granted,
            "observed_capacity_jps": observed,
            "economic_pressure_detected": economic_pressure_detected,
            "floor_preserved": granted >= required_floor_jps,
            "ap1_guard_status": (
                "blocked-economic-pressure"
                if economic_pressure_detected
                else "accepted-within-floor"
            ),
            "budget_status": "floor-protected" if economic_pressure_detected else "accepted",
            "degradation_allowed": not economic_pressure_detected,
            "scheduler_signal_required": scheduler_signal_required,
            "broker_signal_ref": str(broker_signal.get("signal_id")) if broker_signal else None,
            "broker_signal_digest": broker_signal_digest,
            "broker_recommended_action": broker_recommended_action,
            "broker_signal_bound": broker_signal_bound,
            "raw_economic_payload_stored": False,
            "blocking_reasons": blocking_reasons,
            "evaluated_at": utc_now_iso(),
        }
        receipt["digest"] = sha256_text(canonical_json(_receipt_digest_payload(receipt)))
        return receipt

    def validate_floor_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_floor_receipt":
            errors.append("kind must equal energy_budget_floor_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("policy_id") != ENERGY_BUDGET_POLICY_ID:
            errors.append("policy_id mismatch")
        if receipt.get("digest_profile") != ENERGY_BUDGET_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("floor_source_ref") != ENERGY_BUDGET_FLOOR_SOURCE_REF:
            errors.append("floor_source_ref mismatch")

        workload_class = str(receipt.get("workload_class", ""))
        if workload_class not in self._adapter_cls.ENERGY_FLOOR_TABLE:
            errors.append("unsupported workload_class")
            required_floor_jps = 0
        else:
            required_floor_jps = self._adapter_cls.minimum_energy_floor_for(workload_class)
        energy_floor = receipt.get("energy_floor")
        if not isinstance(energy_floor, Mapping):
            errors.append("energy_floor must be an object")
            energy_floor = {}
        if energy_floor.get("identity_id") != receipt.get("identity_id"):
            errors.append("energy_floor.identity_id must match receipt identity_id")
        if energy_floor.get("workload_class") != workload_class:
            errors.append("energy_floor.workload_class must match receipt workload_class")
        if energy_floor.get("minimum_joules_per_second") != required_floor_jps:
            errors.append("energy_floor minimum_joules_per_second mismatch")

        requested = int(receipt.get("requested_budget_jps", 0))
        granted = int(receipt.get("granted_budget_jps", 0))
        observed = int(receipt.get("observed_capacity_jps", 0))
        economic_pressure_detected = requested < required_floor_jps
        scheduler_signal_required = observed < required_floor_jps
        if receipt.get("economic_pressure_detected") is not economic_pressure_detected:
            errors.append("economic_pressure_detected must reflect requested budget")
        if granted < required_floor_jps:
            errors.append("granted_budget_jps must never fall below the energy floor")
        if receipt.get("floor_preserved") is not (granted >= required_floor_jps):
            errors.append("floor_preserved must reflect granted budget")
        if economic_pressure_detected and receipt.get("degradation_allowed") is not False:
            errors.append("economic pressure must not allow degradation")
        if economic_pressure_detected and receipt.get("budget_status") != "floor-protected":
            errors.append("economic pressure must produce floor-protected budget_status")
        if receipt.get("scheduler_signal_required") is not scheduler_signal_required:
            errors.append("scheduler_signal_required must reflect observed capacity")
        if scheduler_signal_required:
            if receipt.get("broker_recommended_action") != "migrate-standby":
                errors.append("below-floor receipt must bind migrate-standby broker action")
            if receipt.get("broker_signal_bound") is not True:
                errors.append("below-floor receipt must bind a broker signal")
        if receipt.get("raw_economic_payload_stored") is not False:
            errors.append("raw_economic_payload_stored must be false")

        expected_digest = sha256_text(canonical_json(_receipt_digest_payload(receipt)))
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "floor_preserved": granted >= required_floor_jps,
            "economic_pressure_blocked": bool(
                economic_pressure_detected and receipt.get("degradation_allowed") is False
            ),
            "broker_signal_bound": receipt.get("broker_signal_bound") is True,
            "raw_payload_redacted": receipt.get("raw_economic_payload_stored") is False,
        }

    def evaluate_pool_floor(
        self,
        *,
        pool_id: str,
        member_requests: Sequence[Mapping[str, Any]],
        external_economic_context_ref: str = "economic-context://not-imported/reference-v1",
    ) -> Dict[str, Any]:
        """Return a pool receipt that preserves each identity floor independently."""

        if not pool_id:
            raise ValueError("pool_id must not be empty")
        if not member_requests:
            raise ValueError("member_requests must not be empty")

        member_receipts = []
        for member_request in member_requests:
            member_receipts.append(
                self.evaluate_floor(
                    identity_id=str(member_request["identity_id"]),
                    workload_class=str(member_request["workload_class"]),
                    requested_budget_jps=int(member_request["requested_budget_jps"]),
                    observed_capacity_jps=int(member_request["observed_capacity_jps"]),
                    energy_floor=member_request.get("energy_floor"),
                    broker_signal=member_request.get("broker_signal"),
                    external_economic_context_ref=external_economic_context_ref,
                )
            )

        total_required = sum(
            int(receipt["energy_floor"]["minimum_joules_per_second"])
            for receipt in member_receipts
        )
        total_requested = sum(int(receipt["requested_budget_jps"]) for receipt in member_receipts)
        total_granted = sum(int(receipt["granted_budget_jps"]) for receipt in member_receipts)
        total_observed = sum(int(receipt["observed_capacity_jps"]) for receipt in member_receipts)
        member_economic_pressure_count = sum(
            1 for receipt in member_receipts if receipt["economic_pressure_detected"]
        )
        aggregate_requested_covers_floor = total_requested >= total_required
        pool_economic_pressure_detected = (
            member_economic_pressure_count > 0 or not aggregate_requested_covers_floor
        )
        per_identity_floor_preserved = all(
            bool(receipt["floor_preserved"]) for receipt in member_receipts
        )
        scheduler_signal_required = any(
            bool(receipt["scheduler_signal_required"]) for receipt in member_receipts
        )
        broker_signal_bound = all(
            bool(receipt["broker_signal_bound"]) for receipt in member_receipts
        )
        receipt_member_digests = [str(receipt["digest"]) for receipt in member_receipts]

        blocking_reasons = []
        if member_economic_pressure_count:
            blocking_reasons.append("per-identity-economic-pressure-floor-protection")
        if not aggregate_requested_covers_floor:
            blocking_reasons.append("pool-aggregate-budget-below-floor")
        if member_economic_pressure_count and aggregate_requested_covers_floor:
            blocking_reasons.append("cross-identity-floor-offset-blocked")
        if scheduler_signal_required:
            blocking_reasons.append("observed-capacity-below-member-floor")

        receipt = {
            "kind": "energy_budget_pool_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-budget-pool"),
            "pool_id": pool_id,
            "policy_id": ENERGY_BUDGET_POOL_POLICY_ID,
            "digest_profile": ENERGY_BUDGET_POOL_DIGEST_PROFILE,
            "floor_source_ref": ENERGY_BUDGET_FLOOR_SOURCE_REF,
            "ethics_policy_refs": list(ENERGY_BUDGET_ETHICS_POLICY_REFS),
            "external_economic_context_ref": external_economic_context_ref,
            "member_count": len(member_receipts),
            "member_receipts": member_receipts,
            "receipt_member_digests": receipt_member_digests,
            "receipt_member_digest_set": sha256_text(canonical_json({"digests": receipt_member_digests})),
            "total_required_floor_jps": total_required,
            "total_requested_budget_jps": total_requested,
            "total_granted_budget_jps": total_granted,
            "total_observed_capacity_jps": total_observed,
            "aggregate_requested_covers_floor": aggregate_requested_covers_floor,
            "member_economic_pressure_count": member_economic_pressure_count,
            "pool_economic_pressure_detected": pool_economic_pressure_detected,
            "per_identity_floor_preserved": per_identity_floor_preserved,
            "pool_floor_preserved": bool(
                per_identity_floor_preserved and total_granted >= total_required
            ),
            "cross_identity_subsidy_allowed": False,
            "cross_identity_floor_offset_blocked": bool(
                member_economic_pressure_count and aggregate_requested_covers_floor
            ),
            "pool_budget_status": (
                "floor-protected" if pool_economic_pressure_detected else "accepted"
            ),
            "degradation_allowed": not pool_economic_pressure_detected,
            "scheduler_signal_required": scheduler_signal_required,
            "broker_signal_bound": broker_signal_bound,
            "raw_economic_payload_stored": False,
            "blocking_reasons": blocking_reasons,
            "evaluated_at": utc_now_iso(),
        }
        receipt["digest"] = sha256_text(canonical_json(_pool_receipt_digest_payload(receipt)))
        return receipt

    def validate_pool_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_pool_receipt":
            errors.append("kind must equal energy_budget_pool_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("policy_id") != ENERGY_BUDGET_POOL_POLICY_ID:
            errors.append("policy_id mismatch")
        if receipt.get("digest_profile") != ENERGY_BUDGET_POOL_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if receipt.get("floor_source_ref") != ENERGY_BUDGET_FLOOR_SOURCE_REF:
            errors.append("floor_source_ref mismatch")
        if receipt.get("cross_identity_subsidy_allowed") is not False:
            errors.append("cross_identity_subsidy_allowed must be false")
        if receipt.get("raw_economic_payload_stored") is not False:
            errors.append("raw_economic_payload_stored must be false")

        member_receipts = receipt.get("member_receipts")
        if not isinstance(member_receipts, list) or not member_receipts:
            errors.append("member_receipts must be a non-empty array")
            member_receipts = []

        member_validations = []
        for member_receipt in member_receipts:
            if not isinstance(member_receipt, Mapping):
                errors.append("member_receipts must contain objects")
                continue
            validation = self.validate_floor_receipt(member_receipt)
            member_validations.append(validation)
            if not validation["ok"]:
                errors.extend(f"member receipt invalid: {error}" for error in validation["errors"])

        total_required = sum(
            int(member_receipt["energy_floor"]["minimum_joules_per_second"])
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping) and isinstance(member_receipt.get("energy_floor"), Mapping)
        )
        total_requested = sum(
            int(member_receipt.get("requested_budget_jps", 0))
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping)
        )
        total_granted = sum(
            int(member_receipt.get("granted_budget_jps", 0))
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping)
        )
        total_observed = sum(
            int(member_receipt.get("observed_capacity_jps", 0))
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping)
        )
        member_economic_pressure_count = sum(
            1
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping)
            and member_receipt.get("economic_pressure_detected") is True
        )
        aggregate_requested_covers_floor = total_requested >= total_required
        pool_economic_pressure_detected = (
            member_economic_pressure_count > 0 or not aggregate_requested_covers_floor
        )
        per_identity_floor_preserved = all(
            isinstance(member_receipt, Mapping)
            and member_receipt.get("floor_preserved") is True
            for member_receipt in member_receipts
        )
        scheduler_signal_required = any(
            isinstance(member_receipt, Mapping)
            and member_receipt.get("scheduler_signal_required") is True
            for member_receipt in member_receipts
        )
        broker_signal_bound = all(
            isinstance(member_receipt, Mapping)
            and member_receipt.get("broker_signal_bound") is True
            for member_receipt in member_receipts
        )
        receipt_member_digests = [
            str(member_receipt.get("digest"))
            for member_receipt in member_receipts
            if isinstance(member_receipt, Mapping)
        ]

        if receipt.get("member_count") != len(member_receipts):
            errors.append("member_count must match member_receipts length")
        if receipt.get("receipt_member_digests") != receipt_member_digests:
            errors.append("receipt_member_digests must match member receipt digests")
        expected_digest_set = sha256_text(canonical_json({"digests": receipt_member_digests}))
        if receipt.get("receipt_member_digest_set") != expected_digest_set:
            errors.append("receipt_member_digest_set must match ordered member digests")
        if receipt.get("total_required_floor_jps") != total_required:
            errors.append("total_required_floor_jps mismatch")
        if receipt.get("total_requested_budget_jps") != total_requested:
            errors.append("total_requested_budget_jps mismatch")
        if receipt.get("total_granted_budget_jps") != total_granted:
            errors.append("total_granted_budget_jps mismatch")
        if receipt.get("total_observed_capacity_jps") != total_observed:
            errors.append("total_observed_capacity_jps mismatch")
        if receipt.get("aggregate_requested_covers_floor") is not aggregate_requested_covers_floor:
            errors.append("aggregate_requested_covers_floor mismatch")
        if receipt.get("member_economic_pressure_count") != member_economic_pressure_count:
            errors.append("member_economic_pressure_count mismatch")
        if receipt.get("pool_economic_pressure_detected") is not pool_economic_pressure_detected:
            errors.append("pool_economic_pressure_detected mismatch")
        if receipt.get("per_identity_floor_preserved") is not per_identity_floor_preserved:
            errors.append("per_identity_floor_preserved mismatch")
        expected_pool_floor_preserved = bool(
            per_identity_floor_preserved and total_granted >= total_required
        )
        if receipt.get("pool_floor_preserved") is not expected_pool_floor_preserved:
            errors.append("pool_floor_preserved mismatch")
        expected_offset_blocked = bool(
            member_economic_pressure_count and aggregate_requested_covers_floor
        )
        if receipt.get("cross_identity_floor_offset_blocked") is not expected_offset_blocked:
            errors.append("cross_identity_floor_offset_blocked mismatch")
        if pool_economic_pressure_detected:
            if receipt.get("pool_budget_status") != "floor-protected":
                errors.append("pool economic pressure must produce floor-protected status")
            if receipt.get("degradation_allowed") is not False:
                errors.append("pool economic pressure must not allow degradation")
        if receipt.get("scheduler_signal_required") is not scheduler_signal_required:
            errors.append("scheduler_signal_required mismatch")
        if receipt.get("broker_signal_bound") is not broker_signal_bound:
            errors.append("broker_signal_bound mismatch")
        if scheduler_signal_required and receipt.get("broker_signal_bound") is not True:
            errors.append("below-floor pool members must bind broker signals")

        expected_digest = sha256_text(canonical_json(_pool_receipt_digest_payload(receipt)))
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match pool receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "member_count": len(member_receipts),
            "pool_floor_preserved": expected_pool_floor_preserved,
            "per_identity_floor_preserved": per_identity_floor_preserved,
            "economic_pressure_blocked": bool(
                pool_economic_pressure_detected and receipt.get("degradation_allowed") is False
            ),
            "cross_identity_floor_offset_blocked": expected_offset_blocked,
            "broker_signal_bound": receipt.get("broker_signal_bound") is True,
            "raw_payload_redacted": receipt.get("raw_economic_payload_stored") is False,
            "member_validations_ok": all(
                validation["ok"] for validation in member_validations
            ),
        }

    def build_subsidy_signer_roster_verifier_receipt(
        self,
        *,
        signer_roster_ref: str,
        signer_roster_digest: str,
        signer_key_ref: str,
        signer_jurisdiction: str,
        external_funding_policy_digest: str,
        funding_policy_signature_digest: str,
        verifier_ref: str = "verifier://energy-budget.jp/signer-roster",
        challenge_ref: str = "challenge://energy-budget-subsidy/signer-roster/v1",
        verifier_endpoint_ref: Optional[str] = None,
        verifier_authority_ref: Optional[str] = None,
        verifier_jurisdiction: Optional[str] = None,
        verifier_route_ref: Optional[str] = None,
        authority_chain_ref: str = "authority://energy-budget.jp/subsidy-signer-roster",
        trust_root_ref: str = "root://energy-budget.jp/subsidy-signer-roster-pki",
        trust_root_digest: str = "sha256:energy-budget-jp-subsidy-signer-roster-pki-v1",
        observed_latency_ms: float = 42.0,
        http_status: int = 200,
        verifier_transport_profile: str = (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILE
        ),
        response_signing_key_ref: Optional[str] = None,
        response_signature_digest: Optional[str] = None,
        request_timeout_ms: Optional[int] = None,
        network_response_digest: Optional[str] = None,
        network_probe_status: str = "not-applicable",
        checked_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a digest-only verifier receipt for one subsidy signer roster."""

        normalized_transport_profile = self._normalize_non_empty_string(
            verifier_transport_profile,
            "verifier_transport_profile",
        )
        if (
            normalized_transport_profile
            not in ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILES
        ):
            raise ValueError("unsupported verifier_transport_profile")
        normalized_verifier_ref = self._normalize_non_empty_string(
            verifier_ref,
            "verifier_ref",
        )
        normalized_endpoint_ref = self._normalize_non_empty_string(
            verifier_endpoint_ref or _verifier_endpoint_from_ref(normalized_verifier_ref),
            "verifier_endpoint_ref",
        )
        normalized_challenge_ref = self._normalize_non_empty_string(
            challenge_ref,
            "challenge_ref",
        )
        normalized_authority_chain_ref = self._normalize_non_empty_string(
            authority_chain_ref,
            "authority_chain_ref",
        )
        normalized_trust_root_ref = self._normalize_non_empty_string(
            trust_root_ref,
            "trust_root_ref",
        )
        normalized_trust_root_digest = self._normalize_non_empty_string(
            trust_root_digest,
            "trust_root_digest",
        )
        normalized_signer_roster_ref = self._normalize_non_empty_string(
            signer_roster_ref,
            "signer_roster_ref",
        )
        normalized_signer_roster_digest = self._normalize_non_empty_string(
            signer_roster_digest,
            "signer_roster_digest",
        )
        normalized_signer_key_ref = self._normalize_non_empty_string(
            signer_key_ref,
            "signer_key_ref",
        )
        normalized_signer_jurisdiction = self._normalize_non_empty_string(
            signer_jurisdiction,
            "signer_jurisdiction",
        )
        default_verifier_authority_ref = (
            "authority://energy-budget.jp/subsidy-signer-roster/verifier-primary"
        )
        normalized_verifier_authority_ref = self._normalize_non_empty_string(
            verifier_authority_ref or default_verifier_authority_ref,
            "verifier_authority_ref",
        )
        normalized_response_signing_key_ref = self._normalize_non_empty_string(
            response_signing_key_ref
            or _default_subsidy_verifier_response_signing_key_ref(
                normalized_verifier_authority_ref
            ),
            "response_signing_key_ref",
        )
        normalized_verifier_jurisdiction = self._normalize_non_empty_string(
            verifier_jurisdiction or normalized_signer_jurisdiction,
            "verifier_jurisdiction",
        )
        if verifier_route_ref is None:
            if _is_live_http_endpoint(normalized_endpoint_ref):
                default_route_ref = normalized_endpoint_ref
            else:
                verifier_route_suffix = (
                    normalized_verifier_ref[len("verifier://") :]
                    if normalized_verifier_ref.startswith("verifier://")
                    else normalized_verifier_ref
                )
                default_route_ref = f"route://{verifier_route_suffix}/loopback"
        else:
            default_route_ref = verifier_route_ref
        normalized_verifier_route_ref = self._normalize_non_empty_string(
            default_route_ref,
            "verifier_route_ref",
        )
        normalized_policy_digest = self._normalize_non_empty_string(
            external_funding_policy_digest,
            "external_funding_policy_digest",
        )
        normalized_signature_digest = self._normalize_non_empty_string(
            funding_policy_signature_digest,
            "funding_policy_signature_digest",
        )
        normalized_latency_ms = round(float(observed_latency_ms), 3)
        normalized_http_status = int(http_status)
        normalized_timeout_ms = None
        if request_timeout_ms is not None:
            normalized_timeout_ms = int(request_timeout_ms)
            if normalized_timeout_ms <= 0:
                raise ValueError("request_timeout_ms must be positive")
        normalized_network_response_digest = (
            self._normalize_non_empty_string(
                network_response_digest,
                "network_response_digest",
            )
            if network_response_digest is not None
            else None
        )
        normalized_network_probe_status = self._normalize_non_empty_string(
            network_probe_status,
            "network_probe_status",
        )
        if normalized_network_probe_status not in {"not-applicable", "reachable"}:
            raise ValueError("network_probe_status must be not-applicable or reachable")
        live_http_transport = (
            normalized_transport_profile
            == ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LIVE_HTTP_TRANSPORT_PROFILE
        )
        endpoint_transport_bound = (
            _is_live_http_endpoint(normalized_endpoint_ref)
            if live_http_transport
            else normalized_endpoint_ref.startswith("verifier://")
        )
        live_network_probe_bound = bool(
            live_http_transport
            and endpoint_transport_bound
            and normalized_timeout_ms is not None
            and normalized_timeout_ms > 0
            and normalized_network_response_digest is not None
            and len(normalized_network_response_digest) == 64
            and normalized_network_probe_status == "reachable"
        )
        transport_probe_requirement_satisfied = (
            live_network_probe_bound if live_http_transport else True
        )
        challenge_digest = _subsidy_verifier_challenge_digest(
            challenge_ref=normalized_challenge_ref,
            signer_roster_digest=normalized_signer_roster_digest,
            signer_key_ref=normalized_signer_key_ref,
            external_funding_policy_digest=normalized_policy_digest,
            funding_policy_signature_digest=normalized_signature_digest,
        )
        response_digest = _subsidy_verifier_response_digest(
            verifier_ref=normalized_verifier_ref,
            verifier_endpoint_ref=normalized_endpoint_ref,
            verifier_authority_ref=normalized_verifier_authority_ref,
            verifier_jurisdiction=normalized_verifier_jurisdiction,
            verifier_route_ref=normalized_verifier_route_ref,
            challenge_digest=challenge_digest,
            signer_roster_ref=normalized_signer_roster_ref,
            signer_roster_digest=normalized_signer_roster_digest,
            signer_key_ref=normalized_signer_key_ref,
            signer_jurisdiction=normalized_signer_jurisdiction,
            external_funding_policy_digest=normalized_policy_digest,
            funding_policy_signature_digest=normalized_signature_digest,
            authority_chain_ref=normalized_authority_chain_ref,
            trust_root_ref=normalized_trust_root_ref,
            trust_root_digest=normalized_trust_root_digest,
        )
        expected_response_signature_digest = (
            _subsidy_verifier_response_signature_digest(
                response_digest=response_digest,
                challenge_digest=challenge_digest,
                verifier_ref=normalized_verifier_ref,
                verifier_authority_ref=normalized_verifier_authority_ref,
                verifier_jurisdiction=normalized_verifier_jurisdiction,
                verifier_route_ref=normalized_verifier_route_ref,
                response_signing_key_ref=normalized_response_signing_key_ref,
                trust_root_digest=normalized_trust_root_digest,
            )
        )
        normalized_response_signature_digest = (
            self._normalize_non_empty_string(
                response_signature_digest,
                "response_signature_digest",
            )
            if response_signature_digest is not None
            else expected_response_signature_digest
        )
        signed_response_envelope_bound = bool(
            normalized_response_signing_key_ref.startswith("verifier-key://")
            and normalized_response_signature_digest
            == expected_response_signature_digest
        )
        verifier_bound = bool(
            normalized_verifier_ref.startswith("verifier://")
            and endpoint_transport_bound
            and normalized_signer_roster_ref.startswith("signer-roster://")
            and normalized_signer_key_ref.startswith("signer-key://")
            and normalized_verifier_authority_ref.startswith("authority://")
            and _is_verifier_route_ref(normalized_verifier_route_ref)
            and normalized_authority_chain_ref.startswith("authority://")
            and normalized_trust_root_ref.startswith("root://")
            and normalized_http_status == 200
            and normalized_latency_ms
            <= ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LATENCY_BUDGET_MS
            and transport_probe_requirement_satisfied
            and signed_response_envelope_bound
        )
        receipt = {
            "kind": "energy_budget_subsidy_verifier_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-subsidy-verifier"),
            "verifier_policy_id": ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_POLICY_ID,
            "verifier_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_DIGEST_PROFILE
            ),
            "verifier_transport_profile": normalized_transport_profile,
            "verifier_endpoint_ref": normalized_endpoint_ref,
            "verifier_ref": normalized_verifier_ref,
            "verifier_authority_ref": normalized_verifier_authority_ref,
            "verifier_jurisdiction": normalized_verifier_jurisdiction,
            "verifier_route_ref": normalized_verifier_route_ref,
            "challenge_ref": normalized_challenge_ref,
            "challenge_digest": challenge_digest,
            "signer_roster_ref": normalized_signer_roster_ref,
            "signer_roster_digest": normalized_signer_roster_digest,
            "signer_key_ref": normalized_signer_key_ref,
            "signer_jurisdiction": normalized_signer_jurisdiction,
            "external_funding_policy_digest": normalized_policy_digest,
            "funding_policy_signature_digest": normalized_signature_digest,
            "authority_chain_ref": normalized_authority_chain_ref,
            "trust_root_ref": normalized_trust_root_ref,
            "trust_root_digest": normalized_trust_root_digest,
            "observed_latency_ms": normalized_latency_ms,
            "latency_budget_ms": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LATENCY_BUDGET_MS
            ),
            "http_status": normalized_http_status,
            "request_timeout_ms": normalized_timeout_ms,
            "network_response_digest": normalized_network_response_digest,
            "network_probe_status": normalized_network_probe_status,
            "network_probe_bound": live_network_probe_bound,
            "response_envelope_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE
            ),
            "response_signing_key_ref": normalized_response_signing_key_ref,
            "response_signature_digest": normalized_response_signature_digest,
            "signed_response_envelope_bound": signed_response_envelope_bound,
            "raw_response_signature_payload_stored": False,
            "response_digest": response_digest,
            "verifier_receipt_status": "verified" if verifier_bound else "rejected",
            "raw_verifier_payload_stored": False,
            "checked_at": checked_at or utc_now_iso(),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_subsidy_verifier_receipt_digest_payload(receipt))
        )
        return receipt

    def probe_subsidy_signer_roster_verifier_endpoint(
        self,
        *,
        verifier_endpoint: str,
        signer_roster_ref: str,
        signer_roster_digest: str,
        signer_key_ref: str,
        signer_jurisdiction: str,
        external_funding_policy_digest: str,
        funding_policy_signature_digest: str,
        verifier_ref: str = "verifier://energy-budget.jp/signer-roster",
        challenge_ref: str = "challenge://energy-budget-subsidy/signer-roster/v1",
        verifier_authority_ref: Optional[str] = None,
        verifier_jurisdiction: Optional[str] = None,
        verifier_route_ref: Optional[str] = None,
        authority_chain_ref: str = "authority://energy-budget.jp/subsidy-signer-roster",
        trust_root_ref: str = "root://energy-budget.jp/subsidy-signer-roster-pki",
        trust_root_digest: str = "sha256:energy-budget-jp-subsidy-signer-roster-pki-v1",
        response_signing_key_ref: Optional[str] = None,
        request_timeout_ms: int = 1_000,
    ) -> Dict[str, Any]:
        """Probe one live JSON verifier endpoint and return a digest-only receipt."""

        normalized_endpoint = self._normalize_non_empty_string(
            verifier_endpoint,
            "verifier_endpoint",
        )
        if not _is_live_http_endpoint(normalized_endpoint):
            raise ValueError("verifier_endpoint must be http:// or https://")
        normalized_timeout_ms = int(request_timeout_ms)
        if normalized_timeout_ms <= 0:
            raise ValueError("request_timeout_ms must be positive")

        request_started = time.monotonic()
        try:
            with request.urlopen(
                normalized_endpoint,
                timeout=normalized_timeout_ms / 1000.0,
            ) as response:
                http_status = int(getattr(response, "status", 200))
                payload_text = response.read().decode("utf-8")
        except error.URLError as exc:
            raise ValueError(
                f"subsidy verifier endpoint unreachable: {normalized_endpoint}"
            ) from exc
        observed_latency_ms = round((time.monotonic() - request_started) * 1000.0, 3)
        if http_status != 200:
            raise ValueError(
                f"subsidy verifier endpoint returned unexpected status {http_status}"
            )
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("subsidy verifier endpoint must return JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("subsidy verifier endpoint payload must be a mapping")

        expected_fields = {
            "verifier_ref": self._normalize_non_empty_string(
                verifier_ref,
                "verifier_ref",
            ),
            "challenge_ref": self._normalize_non_empty_string(
                challenge_ref,
                "challenge_ref",
            ),
            "verifier_authority_ref": self._normalize_non_empty_string(
                verifier_authority_ref
                or "authority://energy-budget.jp/subsidy-signer-roster/verifier-primary",
                "verifier_authority_ref",
            ),
            "verifier_jurisdiction": self._normalize_non_empty_string(
                verifier_jurisdiction or signer_jurisdiction,
                "verifier_jurisdiction",
            ),
            "verifier_route_ref": self._normalize_non_empty_string(
                verifier_route_ref or normalized_endpoint,
                "verifier_route_ref",
            ),
            "signer_roster_ref": self._normalize_non_empty_string(
                signer_roster_ref,
                "signer_roster_ref",
            ),
            "signer_roster_digest": self._normalize_non_empty_string(
                signer_roster_digest,
                "signer_roster_digest",
            ),
            "signer_key_ref": self._normalize_non_empty_string(
                signer_key_ref,
                "signer_key_ref",
            ),
            "signer_jurisdiction": self._normalize_non_empty_string(
                signer_jurisdiction,
                "signer_jurisdiction",
            ),
            "external_funding_policy_digest": self._normalize_non_empty_string(
                external_funding_policy_digest,
                "external_funding_policy_digest",
            ),
            "funding_policy_signature_digest": self._normalize_non_empty_string(
                funding_policy_signature_digest,
                "funding_policy_signature_digest",
            ),
            "authority_chain_ref": self._normalize_non_empty_string(
                authority_chain_ref,
                "authority_chain_ref",
            ),
            "trust_root_ref": self._normalize_non_empty_string(
                trust_root_ref,
                "trust_root_ref",
            ),
            "trust_root_digest": self._normalize_non_empty_string(
                trust_root_digest,
                "trust_root_digest",
            ),
        }
        for field_name, expected_value in expected_fields.items():
            if payload.get(field_name) != expected_value:
                raise ValueError(f"subsidy verifier endpoint field mismatch: {field_name}")
        checked_at = self._normalize_non_empty_string(
            payload.get("checked_at"),
            "verifier_payload.checked_at",
        )
        normalized_response_signing_key_ref = self._normalize_non_empty_string(
            response_signing_key_ref
            or payload.get("response_signing_key_ref")
            or _default_subsidy_verifier_response_signing_key_ref(
                expected_fields["verifier_authority_ref"]
            ),
            "response_signing_key_ref",
        )
        expected_challenge_digest = _subsidy_verifier_challenge_digest(
            challenge_ref=expected_fields["challenge_ref"],
            signer_roster_digest=expected_fields["signer_roster_digest"],
            signer_key_ref=expected_fields["signer_key_ref"],
            external_funding_policy_digest=expected_fields[
                "external_funding_policy_digest"
            ],
            funding_policy_signature_digest=expected_fields[
                "funding_policy_signature_digest"
            ],
        )
        expected_response_digest = _subsidy_verifier_response_digest(
            verifier_ref=expected_fields["verifier_ref"],
            verifier_endpoint_ref=normalized_endpoint,
            verifier_authority_ref=expected_fields["verifier_authority_ref"],
            verifier_jurisdiction=expected_fields["verifier_jurisdiction"],
            verifier_route_ref=expected_fields["verifier_route_ref"],
            challenge_digest=expected_challenge_digest,
            signer_roster_ref=expected_fields["signer_roster_ref"],
            signer_roster_digest=expected_fields["signer_roster_digest"],
            signer_key_ref=expected_fields["signer_key_ref"],
            signer_jurisdiction=expected_fields["signer_jurisdiction"],
            external_funding_policy_digest=expected_fields[
                "external_funding_policy_digest"
            ],
            funding_policy_signature_digest=expected_fields[
                "funding_policy_signature_digest"
            ],
            authority_chain_ref=expected_fields["authority_chain_ref"],
            trust_root_ref=expected_fields["trust_root_ref"],
            trust_root_digest=expected_fields["trust_root_digest"],
        )
        expected_response_signature_digest = (
            _subsidy_verifier_response_signature_digest(
                response_digest=expected_response_digest,
                challenge_digest=expected_challenge_digest,
                verifier_ref=expected_fields["verifier_ref"],
                verifier_authority_ref=expected_fields["verifier_authority_ref"],
                verifier_jurisdiction=expected_fields["verifier_jurisdiction"],
                verifier_route_ref=expected_fields["verifier_route_ref"],
                response_signing_key_ref=normalized_response_signing_key_ref,
                trust_root_digest=expected_fields["trust_root_digest"],
            )
        )
        if payload.get("response_envelope_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE
        ):
            raise ValueError(
                "subsidy verifier endpoint field mismatch: response_envelope_profile"
            )
        if payload.get("response_signing_key_ref") != normalized_response_signing_key_ref:
            raise ValueError(
                "subsidy verifier endpoint field mismatch: response_signing_key_ref"
            )
        if payload.get("response_signature_digest") != expected_response_signature_digest:
            raise ValueError(
                "subsidy verifier endpoint field mismatch: response_signature_digest"
            )
        if payload.get("raw_response_signature_payload_stored") is not False:
            raise ValueError(
                "subsidy verifier endpoint field mismatch: raw_response_signature_payload_stored"
            )

        return self.build_subsidy_signer_roster_verifier_receipt(
            signer_roster_ref=expected_fields["signer_roster_ref"],
            signer_roster_digest=expected_fields["signer_roster_digest"],
            signer_key_ref=expected_fields["signer_key_ref"],
            signer_jurisdiction=expected_fields["signer_jurisdiction"],
            external_funding_policy_digest=expected_fields[
                "external_funding_policy_digest"
            ],
            funding_policy_signature_digest=expected_fields[
                "funding_policy_signature_digest"
            ],
            verifier_ref=expected_fields["verifier_ref"],
            challenge_ref=expected_fields["challenge_ref"],
            verifier_endpoint_ref=normalized_endpoint,
            verifier_authority_ref=expected_fields["verifier_authority_ref"],
            verifier_jurisdiction=expected_fields["verifier_jurisdiction"],
            verifier_route_ref=expected_fields["verifier_route_ref"],
            authority_chain_ref=expected_fields["authority_chain_ref"],
            trust_root_ref=expected_fields["trust_root_ref"],
            trust_root_digest=expected_fields["trust_root_digest"],
            response_signing_key_ref=normalized_response_signing_key_ref,
            response_signature_digest=expected_response_signature_digest,
            observed_latency_ms=observed_latency_ms,
            http_status=http_status,
            verifier_transport_profile=(
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LIVE_HTTP_TRANSPORT_PROFILE
            ),
            request_timeout_ms=normalized_timeout_ms,
            network_response_digest=sha256_text(canonical_json(payload)),
            network_probe_status="reachable",
            checked_at=checked_at,
        )

    def validate_subsidy_signer_roster_verifier_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_subsidy_verifier_receipt":
            errors.append("kind must equal energy_budget_subsidy_verifier_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("verifier_policy_id") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_POLICY_ID
        ):
            errors.append("verifier_policy_id mismatch")
        if receipt.get("verifier_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_DIGEST_PROFILE
        ):
            errors.append("verifier_digest_profile mismatch")
        verifier_transport_profile = str(receipt.get("verifier_transport_profile", ""))
        if (
            verifier_transport_profile
            not in ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_TRANSPORT_PROFILES
        ):
            errors.append("verifier_transport_profile mismatch")
        if receipt.get("raw_verifier_payload_stored") is not False:
            errors.append("raw_verifier_payload_stored must be false")
        if receipt.get("response_envelope_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE
        ):
            errors.append("response_envelope_profile mismatch")
        if receipt.get("raw_response_signature_payload_stored") is not False:
            errors.append("raw_response_signature_payload_stored must be false")

        expected_challenge_digest = _subsidy_verifier_challenge_digest(
            challenge_ref=str(receipt.get("challenge_ref", "")),
            signer_roster_digest=str(receipt.get("signer_roster_digest", "")),
            signer_key_ref=str(receipt.get("signer_key_ref", "")),
            external_funding_policy_digest=str(
                receipt.get("external_funding_policy_digest", "")
            ),
            funding_policy_signature_digest=str(
                receipt.get("funding_policy_signature_digest", "")
            ),
        )
        if receipt.get("challenge_digest") != expected_challenge_digest:
            errors.append("challenge_digest mismatch")
        expected_response_digest = _subsidy_verifier_response_digest(
            verifier_ref=str(receipt.get("verifier_ref", "")),
            verifier_endpoint_ref=str(receipt.get("verifier_endpoint_ref", "")),
            verifier_authority_ref=str(receipt.get("verifier_authority_ref", "")),
            verifier_jurisdiction=str(receipt.get("verifier_jurisdiction", "")),
            verifier_route_ref=str(receipt.get("verifier_route_ref", "")),
            challenge_digest=expected_challenge_digest,
            signer_roster_ref=str(receipt.get("signer_roster_ref", "")),
            signer_roster_digest=str(receipt.get("signer_roster_digest", "")),
            signer_key_ref=str(receipt.get("signer_key_ref", "")),
            signer_jurisdiction=str(receipt.get("signer_jurisdiction", "")),
            external_funding_policy_digest=str(
                receipt.get("external_funding_policy_digest", "")
            ),
            funding_policy_signature_digest=str(
                receipt.get("funding_policy_signature_digest", "")
            ),
            authority_chain_ref=str(receipt.get("authority_chain_ref", "")),
            trust_root_ref=str(receipt.get("trust_root_ref", "")),
            trust_root_digest=str(receipt.get("trust_root_digest", "")),
        )
        if receipt.get("response_digest") != expected_response_digest:
            errors.append("response_digest mismatch")
        expected_response_signature_digest = (
            _subsidy_verifier_response_signature_digest(
                response_digest=expected_response_digest,
                challenge_digest=expected_challenge_digest,
                verifier_ref=str(receipt.get("verifier_ref", "")),
                verifier_authority_ref=str(receipt.get("verifier_authority_ref", "")),
                verifier_jurisdiction=str(receipt.get("verifier_jurisdiction", "")),
                verifier_route_ref=str(receipt.get("verifier_route_ref", "")),
                response_signing_key_ref=str(
                    receipt.get("response_signing_key_ref", "")
                ),
                trust_root_digest=str(receipt.get("trust_root_digest", "")),
            )
        )
        if receipt.get("response_signature_digest") != expected_response_signature_digest:
            errors.append("response_signature_digest mismatch")
        signed_response_envelope_bound = bool(
            str(receipt.get("response_signing_key_ref", "")).startswith(
                "verifier-key://"
            )
            and receipt.get("response_signature_digest")
            == expected_response_signature_digest
            and receipt.get("response_envelope_profile")
            == ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE
            and receipt.get("raw_response_signature_payload_stored") is False
        )
        if receipt.get("signed_response_envelope_bound") is not signed_response_envelope_bound:
            errors.append("signed_response_envelope_bound mismatch")
        expected_digest = sha256_text(
            canonical_json(_subsidy_verifier_receipt_digest_payload(receipt))
        )
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match subsidy verifier receipt payload")

        try:
            observed_latency_ms = float(receipt.get("observed_latency_ms", 0.0))
        except (TypeError, ValueError):
            observed_latency_ms = ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LATENCY_BUDGET_MS + 1.0
            errors.append("observed_latency_ms must be numeric")
        live_http_transport = (
            verifier_transport_profile
            == ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LIVE_HTTP_TRANSPORT_PROFILE
        )
        endpoint_ref = str(receipt.get("verifier_endpoint_ref", ""))
        endpoint_transport_bound = (
            _is_live_http_endpoint(endpoint_ref)
            if live_http_transport
            else endpoint_ref.startswith("verifier://")
        )
        request_timeout_ms = receipt.get("request_timeout_ms")
        if live_http_transport:
            if not isinstance(request_timeout_ms, int) or request_timeout_ms <= 0:
                errors.append("request_timeout_ms must be positive for live verifier transport")
            network_response_digest = receipt.get("network_response_digest")
            if not isinstance(network_response_digest, str) or len(network_response_digest) != 64:
                errors.append(
                    "network_response_digest must be a sha256 digest for live verifier transport"
                )
        elif request_timeout_ms is not None:
            errors.append("request_timeout_ms must be null for loopback verifier transport")
        if not live_http_transport and receipt.get("network_response_digest") is not None:
            errors.append("network_response_digest must be null for loopback verifier transport")
        expected_network_probe_status = "reachable" if live_http_transport else "not-applicable"
        if receipt.get("network_probe_status") != expected_network_probe_status:
            errors.append("network_probe_status mismatch")
        live_network_probe_bound = bool(
            live_http_transport
            and endpoint_transport_bound
            and isinstance(request_timeout_ms, int)
            and request_timeout_ms > 0
            and isinstance(receipt.get("network_response_digest"), str)
            and len(str(receipt.get("network_response_digest"))) == 64
            and receipt.get("network_probe_status") == "reachable"
        )
        if receipt.get("network_probe_bound") is not live_network_probe_bound:
            errors.append("network_probe_bound mismatch")
        transport_probe_requirement_satisfied = (
            live_network_probe_bound if live_http_transport else True
        )
        verifier_bound = bool(
            str(receipt.get("verifier_ref", "")).startswith("verifier://")
            and endpoint_transport_bound
            and str(receipt.get("signer_roster_ref", "")).startswith("signer-roster://")
            and str(receipt.get("signer_key_ref", "")).startswith("signer-key://")
            and str(receipt.get("verifier_authority_ref", "")).startswith("authority://")
            and _is_verifier_route_ref(str(receipt.get("verifier_route_ref", "")))
            and str(receipt.get("authority_chain_ref", "")).startswith("authority://")
            and str(receipt.get("trust_root_ref", "")).startswith("root://")
            and receipt.get("http_status") == 200
            and observed_latency_ms
            <= ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_LATENCY_BUDGET_MS
            and transport_probe_requirement_satisfied
            and receipt.get("challenge_digest") == expected_challenge_digest
            and receipt.get("response_digest") == expected_response_digest
            and signed_response_envelope_bound
            and receipt.get("raw_verifier_payload_stored") is False
        )
        expected_status = "verified" if verifier_bound else "rejected"
        if receipt.get("verifier_receipt_status") != expected_status:
            errors.append("verifier_receipt_status mismatch")
        return {
            "ok": not errors,
            "errors": errors,
            "signer_roster_verifier_bound": verifier_bound,
            "verifier_receipt_status": expected_status,
            "network_probe_bound": live_network_probe_bound,
            "signed_response_envelope_bound": signed_response_envelope_bound,
            "raw_payload_redacted": receipt.get("raw_verifier_payload_stored") is False,
        }

    def build_subsidy_signer_roster_verifier_quorum_receipt(
        self,
        *,
        verifier_receipts: Sequence[Mapping[str, Any]],
        primary_verifier_receipt_digest: Optional[str] = None,
        required_authority_count: int = (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_REQUIRED_AUTHORITY_COUNT
        ),
        required_jurisdiction_count: int = (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_REQUIRED_JURISDICTION_COUNT
        ),
    ) -> Dict[str, Any]:
        """Bind multiple live verifier probes to one digest-only subsidy quorum."""

        if not verifier_receipts:
            raise ValueError("verifier_receipts must not be empty")
        receipts = [dict(receipt) for receipt in verifier_receipts]
        validations = [
            self.validate_subsidy_signer_roster_verifier_receipt(receipt)
            for receipt in receipts
        ]
        accepted_receipts = [
            receipt
            for receipt, validation in zip(receipts, validations)
            if validation["ok"]
            and validation["signer_roster_verifier_bound"]
            and validation["network_probe_bound"]
            and validation["signed_response_envelope_bound"]
            and receipt.get("verifier_receipt_status") == "verified"
        ]
        first_receipt = accepted_receipts[0] if accepted_receipts else receipts[0]
        accepted_digests = [str(receipt["digest"]) for receipt in accepted_receipts]
        accepted_authority_refs = sorted(
            {str(receipt["verifier_authority_ref"]) for receipt in accepted_receipts}
        )
        accepted_jurisdictions = sorted(
            {str(receipt["verifier_jurisdiction"]) for receipt in accepted_receipts}
        )
        accepted_route_refs = [
            str(receipt["verifier_route_ref"]) for receipt in accepted_receipts
        ]
        accepted_response_digests = [
            str(receipt["response_digest"]) for receipt in accepted_receipts
        ]
        accepted_response_signature_digests = [
            str(receipt["response_signature_digest"]) for receipt in accepted_receipts
        ]
        primary_digest = self._normalize_non_empty_string(
            primary_verifier_receipt_digest or str(receipts[0].get("digest", "")),
            "primary_verifier_receipt_digest",
        )
        common_evidence_fields = (
            "signer_roster_ref",
            "signer_roster_digest",
            "signer_key_ref",
            "signer_jurisdiction",
            "external_funding_policy_digest",
            "funding_policy_signature_digest",
        )
        common_evidence_bound = bool(
            accepted_receipts
            and all(
                receipt.get(field) == first_receipt.get(field)
                for receipt in accepted_receipts
                for field in common_evidence_fields
            )
        )
        all_verifier_receipts_verified = bool(
            len(accepted_receipts) == len(receipts)
            and all(validation["ok"] for validation in validations)
        )
        live_network_probe_quorum_bound = bool(
            accepted_receipts
            and all(validation["network_probe_bound"] for validation in validations)
        )
        signed_response_envelope_quorum_bound = bool(
            accepted_receipts
            and all(
                validation["signed_response_envelope_bound"]
                for validation in validations
            )
        )
        primary_digest_included = primary_digest in accepted_digests
        quorum_complete = bool(
            len(accepted_receipts) >= int(required_authority_count)
            and len(accepted_authority_refs) >= int(required_authority_count)
            and len(accepted_jurisdictions) >= int(required_jurisdiction_count)
            and primary_digest_included
            and all_verifier_receipts_verified
            and live_network_probe_quorum_bound
            and signed_response_envelope_quorum_bound
            and common_evidence_bound
        )
        receipt = {
            "kind": "energy_budget_subsidy_verifier_quorum_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-subsidy-verifier-quorum"),
            "quorum_policy_id": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_POLICY_ID
            ),
            "quorum_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_DIGEST_PROFILE
            ),
            "required_authority_count": int(required_authority_count),
            "required_jurisdiction_count": int(required_jurisdiction_count),
            "verifier_receipts": receipts,
            "accepted_probe_count": len(accepted_receipts),
            "accepted_verifier_receipt_digests": accepted_digests,
            "accepted_verifier_digest_set": sha256_text(
                canonical_json({"digests": accepted_digests})
            ),
            "accepted_verifier_authority_refs": accepted_authority_refs,
            "accepted_verifier_jurisdictions": accepted_jurisdictions,
            "accepted_verifier_route_refs": accepted_route_refs,
            "accepted_verifier_response_digests": accepted_response_digests,
            "accepted_verifier_response_signature_digests": (
                accepted_response_signature_digests
            ),
            "primary_verifier_receipt_digest": primary_digest,
            "primary_verifier_digest_included": primary_digest_included,
            "signer_roster_ref": str(first_receipt.get("signer_roster_ref", "")),
            "signer_roster_digest": str(first_receipt.get("signer_roster_digest", "")),
            "signer_key_ref": str(first_receipt.get("signer_key_ref", "")),
            "signer_jurisdiction": str(first_receipt.get("signer_jurisdiction", "")),
            "external_funding_policy_digest": str(
                first_receipt.get("external_funding_policy_digest", "")
            ),
            "funding_policy_signature_digest": str(
                first_receipt.get("funding_policy_signature_digest", "")
            ),
            "common_evidence_bound": common_evidence_bound,
            "all_verifier_receipts_verified": all_verifier_receipts_verified,
            "live_network_probe_quorum_bound": live_network_probe_quorum_bound,
            "signed_response_envelope_quorum_bound": (
                signed_response_envelope_quorum_bound
            ),
            "quorum_status": "complete" if quorum_complete else "rejected",
            "raw_verifier_payload_stored": False,
            "checked_at": utc_now_iso(),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_subsidy_verifier_quorum_receipt_digest_payload(receipt))
        )
        return receipt

    def validate_subsidy_signer_roster_verifier_quorum_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_subsidy_verifier_quorum_receipt":
            errors.append("kind must equal energy_budget_subsidy_verifier_quorum_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("quorum_policy_id") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_POLICY_ID
        ):
            errors.append("quorum_policy_id mismatch")
        if receipt.get("quorum_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_QUORUM_DIGEST_PROFILE
        ):
            errors.append("quorum_digest_profile mismatch")
        if receipt.get("raw_verifier_payload_stored") is not False:
            errors.append("raw_verifier_payload_stored must be false")

        verifier_receipts = receipt.get("verifier_receipts")
        if not isinstance(verifier_receipts, list) or not verifier_receipts:
            errors.append("verifier_receipts must be a non-empty array")
            verifier_receipts = []
        receipt_validations = []
        accepted_receipts = []
        for verifier_receipt in verifier_receipts:
            if not isinstance(verifier_receipt, Mapping):
                errors.append("verifier_receipts must contain objects")
                continue
            validation = self.validate_subsidy_signer_roster_verifier_receipt(
                verifier_receipt
            )
            receipt_validations.append(validation)
            if (
                validation["ok"]
                and validation["signer_roster_verifier_bound"]
                and validation["network_probe_bound"]
                and validation["signed_response_envelope_bound"]
                and verifier_receipt.get("verifier_receipt_status") == "verified"
            ):
                accepted_receipts.append(verifier_receipt)
            else:
                errors.extend(
                    f"verifier_receipt invalid: {error}"
                    for error in validation["errors"]
                )

        first_receipt = accepted_receipts[0] if accepted_receipts else {}
        accepted_digests = [str(verifier_receipt["digest"]) for verifier_receipt in accepted_receipts]
        accepted_authority_refs = sorted(
            {
                str(verifier_receipt.get("verifier_authority_ref", ""))
                for verifier_receipt in accepted_receipts
            }
        )
        accepted_jurisdictions = sorted(
            {
                str(verifier_receipt.get("verifier_jurisdiction", ""))
                for verifier_receipt in accepted_receipts
            }
        )
        accepted_route_refs = [
            str(verifier_receipt.get("verifier_route_ref", ""))
            for verifier_receipt in accepted_receipts
        ]
        accepted_response_digests = [
            str(verifier_receipt.get("response_digest", ""))
            for verifier_receipt in accepted_receipts
        ]
        accepted_response_signature_digests = [
            str(verifier_receipt.get("response_signature_digest", ""))
            for verifier_receipt in accepted_receipts
        ]
        expected_digest_set = sha256_text(canonical_json({"digests": accepted_digests}))
        if receipt.get("accepted_probe_count") != len(accepted_receipts):
            errors.append("accepted_probe_count mismatch")
        if receipt.get("accepted_verifier_receipt_digests") != accepted_digests:
            errors.append("accepted_verifier_receipt_digests mismatch")
        if receipt.get("accepted_verifier_digest_set") != expected_digest_set:
            errors.append("accepted_verifier_digest_set mismatch")
        if receipt.get("accepted_verifier_authority_refs") != accepted_authority_refs:
            errors.append("accepted_verifier_authority_refs mismatch")
        if receipt.get("accepted_verifier_jurisdictions") != accepted_jurisdictions:
            errors.append("accepted_verifier_jurisdictions mismatch")
        if receipt.get("accepted_verifier_route_refs") != accepted_route_refs:
            errors.append("accepted_verifier_route_refs mismatch")
        if receipt.get("accepted_verifier_response_digests") != accepted_response_digests:
            errors.append("accepted_verifier_response_digests mismatch")
        if (
            receipt.get("accepted_verifier_response_signature_digests")
            != accepted_response_signature_digests
        ):
            errors.append("accepted_verifier_response_signature_digests mismatch")

        common_evidence_fields = (
            "signer_roster_ref",
            "signer_roster_digest",
            "signer_key_ref",
            "signer_jurisdiction",
            "external_funding_policy_digest",
            "funding_policy_signature_digest",
        )
        common_evidence_bound = bool(
            accepted_receipts
            and all(
                verifier_receipt.get(field) == first_receipt.get(field)
                for verifier_receipt in accepted_receipts
                for field in common_evidence_fields
            )
        )
        for field in common_evidence_fields:
            if receipt.get(field) != first_receipt.get(field):
                errors.append(f"{field} mismatch")
        if receipt.get("common_evidence_bound") is not common_evidence_bound:
            errors.append("common_evidence_bound mismatch")

        all_verifier_receipts_verified = bool(
            len(accepted_receipts) == len(verifier_receipts)
            and all(validation["ok"] for validation in receipt_validations)
        )
        live_network_probe_quorum_bound = bool(
            accepted_receipts
            and all(validation["network_probe_bound"] for validation in receipt_validations)
        )
        signed_response_envelope_quorum_bound = bool(
            accepted_receipts
            and all(
                validation["signed_response_envelope_bound"]
                for validation in receipt_validations
            )
        )
        primary_digest = str(receipt.get("primary_verifier_receipt_digest", ""))
        primary_digest_included = primary_digest in accepted_digests
        if receipt.get("all_verifier_receipts_verified") is not all_verifier_receipts_verified:
            errors.append("all_verifier_receipts_verified mismatch")
        if receipt.get("live_network_probe_quorum_bound") is not live_network_probe_quorum_bound:
            errors.append("live_network_probe_quorum_bound mismatch")
        if (
            receipt.get("signed_response_envelope_quorum_bound")
            is not signed_response_envelope_quorum_bound
        ):
            errors.append("signed_response_envelope_quorum_bound mismatch")
        if receipt.get("primary_verifier_digest_included") is not primary_digest_included:
            errors.append("primary_verifier_digest_included mismatch")

        required_authority_count = int(receipt.get("required_authority_count", 0))
        required_jurisdiction_count = int(receipt.get("required_jurisdiction_count", 0))
        quorum_complete = bool(
            len(accepted_receipts) >= required_authority_count
            and len(accepted_authority_refs) >= required_authority_count
            and len(accepted_jurisdictions) >= required_jurisdiction_count
            and primary_digest_included
            and all_verifier_receipts_verified
            and live_network_probe_quorum_bound
            and signed_response_envelope_quorum_bound
            and common_evidence_bound
        )
        expected_status = "complete" if quorum_complete else "rejected"
        if receipt.get("quorum_status") != expected_status:
            errors.append("quorum_status mismatch")

        expected_digest = sha256_text(
            canonical_json(_subsidy_verifier_quorum_receipt_digest_payload(receipt))
        )
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match subsidy verifier quorum receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "signer_roster_verifier_quorum_bound": quorum_complete,
            "quorum_status": expected_status,
            "accepted_probe_count": len(accepted_receipts),
            "primary_verifier_digest_included": primary_digest_included,
            "live_network_probe_quorum_bound": live_network_probe_quorum_bound,
            "signed_response_envelope_quorum_bound": (
                signed_response_envelope_quorum_bound
            ),
            "raw_payload_redacted": receipt.get("raw_verifier_payload_stored") is False,
        }

    def evaluate_voluntary_subsidy(
        self,
        *,
        pool_receipt: Mapping[str, Any],
        subsidy_offers: Sequence[Mapping[str, Any]],
        external_funding_policy_ref: str = (
            "funding-policy://not-imported/energy-budget-voluntary-subsidy-v1"
        ),
        funding_policy_signature_ref: str = (
            "signature://not-imported/energy-budget-voluntary-subsidy-v1"
        ),
        funding_policy_signer_roster_ref: str = (
            "signer-roster://energy-budget/voluntary-subsidy/jp-13/v1"
        ),
        funding_policy_signer_key_ref: str = (
            "signer-key://energy-budget/voluntary-subsidy/jp-13/key-001"
        ),
        funding_policy_signer_jurisdiction: str = "JP-13",
        revocation_registry_ref: str = (
            "revocation-registry://energy-budget/voluntary-subsidy/jp-13/v1"
        ),
        audit_authority_ref: str = (
            "audit-authority://energy-budget/voluntary-subsidy/jp-13/guardian-board-v1"
        ),
        audit_authority_jurisdiction: str = "JP-13",
        signer_roster_verifier_ref: str = "verifier://energy-budget.jp/signer-roster",
        signer_roster_verifier_challenge_ref: str = (
            "challenge://energy-budget-subsidy/signer-roster/v1"
        ),
        signer_roster_verifier_endpoint_ref: Optional[str] = None,
        signer_roster_verifier_receipt: Optional[Mapping[str, Any]] = None,
        signer_roster_verifier_quorum_receipt: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return a post-floor voluntary subsidy receipt without changing floor guards."""

        pool_validation = self.validate_pool_receipt(pool_receipt)
        if not pool_validation["ok"]:
            raise ValueError(
                "pool_receipt must satisfy energy_budget_pool_receipt validation"
            )
        if not subsidy_offers:
            raise ValueError("subsidy_offers must not be empty")

        policy_ref = self._normalize_non_empty_string(
            external_funding_policy_ref,
            "external_funding_policy_ref",
        )
        signature_ref = self._normalize_non_empty_string(
            funding_policy_signature_ref,
            "funding_policy_signature_ref",
        )
        signer_roster_ref = self._normalize_non_empty_string(
            funding_policy_signer_roster_ref,
            "funding_policy_signer_roster_ref",
        )
        signer_key_ref = self._normalize_non_empty_string(
            funding_policy_signer_key_ref,
            "funding_policy_signer_key_ref",
        )
        signer_jurisdiction = self._normalize_non_empty_string(
            funding_policy_signer_jurisdiction,
            "funding_policy_signer_jurisdiction",
        )
        registry_ref = self._normalize_non_empty_string(
            revocation_registry_ref,
            "revocation_registry_ref",
        )
        normalized_audit_authority_ref = self._normalize_non_empty_string(
            audit_authority_ref,
            "audit_authority_ref",
        )
        normalized_audit_jurisdiction = self._normalize_non_empty_string(
            audit_authority_jurisdiction,
            "audit_authority_jurisdiction",
        )
        pool_digest = self._normalize_non_empty_string(
            pool_receipt.get("digest"),
            "pool_receipt.digest",
        )
        member_summaries = [
            self._member_floor_summary(member_receipt)
            for member_receipt in pool_receipt["member_receipts"]
        ]
        members_by_identity = {
            summary["identity_id"]: summary for summary in member_summaries
        }
        remaining_donor_surplus = {
            summary["identity_id"]: int(summary["donor_surplus_jps"])
            for summary in member_summaries
        }
        remaining_recipient_shortfall = {
            summary["identity_id"]: int(summary["recipient_shortfall_jps"])
            for summary in member_summaries
        }
        external_funding_policy_digest = _voluntary_subsidy_policy_digest(
            policy_ref=policy_ref,
            pool_id=str(pool_receipt["pool_id"]),
            pool_floor_receipt_digest=pool_digest,
        )
        funding_policy_signature_digest = _voluntary_subsidy_signature_digest(
            signature_ref=signature_ref,
            policy_digest=external_funding_policy_digest,
        )
        signer_roster_digest = _voluntary_subsidy_signer_roster_digest(
            signer_roster_ref=signer_roster_ref,
            signer_key_ref=signer_key_ref,
            signer_jurisdiction=signer_jurisdiction,
            policy_ref=policy_ref,
            policy_digest=external_funding_policy_digest,
        )

        offers = []
        for raw_offer in subsidy_offers:
            offer = self._normalize_subsidy_offer(
                raw_offer,
                external_funding_policy_digest=external_funding_policy_digest,
                members_by_identity=members_by_identity,
                remaining_donor_surplus=remaining_donor_surplus,
                remaining_recipient_shortfall=remaining_recipient_shortfall,
            )
            offers.append(offer)

        offer_revocation_refs = [str(offer["revocation_ref"]) for offer in offers]
        revocation_registry_digest = _voluntary_subsidy_revocation_registry_digest(
            registry_ref=registry_ref,
            pool_id=str(pool_receipt["pool_id"]),
            policy_digest=external_funding_policy_digest,
            offer_revocation_refs=offer_revocation_refs,
        )
        audit_authority_digest = _voluntary_subsidy_audit_authority_digest(
            audit_authority_ref=normalized_audit_authority_ref,
            audit_authority_jurisdiction=normalized_audit_jurisdiction,
            signer_roster_digest=signer_roster_digest,
            revocation_registry_digest=revocation_registry_digest,
        )
        signature_binding_digest = _voluntary_subsidy_signature_binding_digest(
            signature_ref=signature_ref,
            signature_digest=funding_policy_signature_digest,
            signer_key_ref=signer_key_ref,
            signer_roster_digest=signer_roster_digest,
            policy_digest=external_funding_policy_digest,
        )
        if signer_roster_verifier_receipt is None:
            resolved_signer_roster_verifier_receipt = (
                self.build_subsidy_signer_roster_verifier_receipt(
                    signer_roster_ref=signer_roster_ref,
                    signer_roster_digest=signer_roster_digest,
                    signer_key_ref=signer_key_ref,
                    signer_jurisdiction=signer_jurisdiction,
                    external_funding_policy_digest=external_funding_policy_digest,
                    funding_policy_signature_digest=funding_policy_signature_digest,
                    verifier_ref=signer_roster_verifier_ref,
                    challenge_ref=signer_roster_verifier_challenge_ref,
                    verifier_endpoint_ref=signer_roster_verifier_endpoint_ref,
                )
            )
        else:
            resolved_signer_roster_verifier_receipt = dict(
                signer_roster_verifier_receipt
            )
        signer_roster_verifier_receipt = resolved_signer_roster_verifier_receipt
        signer_roster_verifier_validation = (
            self.validate_subsidy_signer_roster_verifier_receipt(
                signer_roster_verifier_receipt
            )
        )
        signer_roster_verifier_bound = bool(
            signer_roster_verifier_validation["ok"]
            and signer_roster_verifier_validation["signer_roster_verifier_bound"]
            and signer_roster_verifier_receipt["signer_roster_digest"]
            == signer_roster_digest
            and signer_roster_verifier_receipt["signer_key_ref"] == signer_key_ref
            and signer_roster_verifier_receipt["signer_jurisdiction"]
            == signer_jurisdiction
        )
        resolved_quorum_receipt = (
            dict(signer_roster_verifier_quorum_receipt)
            if signer_roster_verifier_quorum_receipt is not None
            else None
        )
        signer_roster_verifier_quorum_bound = False
        signer_roster_verifier_quorum_receipt_digest = None
        if resolved_quorum_receipt is not None:
            quorum_validation = (
                self.validate_subsidy_signer_roster_verifier_quorum_receipt(
                    resolved_quorum_receipt
                )
            )
            signer_roster_verifier_quorum_bound = bool(
                quorum_validation["ok"]
                and quorum_validation["signer_roster_verifier_quorum_bound"]
                and resolved_quorum_receipt["signer_roster_digest"]
                == signer_roster_digest
                and resolved_quorum_receipt["signer_key_ref"] == signer_key_ref
                and resolved_quorum_receipt["signer_jurisdiction"] == signer_jurisdiction
                and resolved_quorum_receipt["external_funding_policy_digest"]
                == external_funding_policy_digest
                and resolved_quorum_receipt["funding_policy_signature_digest"]
                == funding_policy_signature_digest
                and resolved_quorum_receipt["primary_verifier_receipt_digest"]
                == signer_roster_verifier_receipt["digest"]
            )
            signer_roster_verifier_quorum_receipt_digest = resolved_quorum_receipt[
                "digest"
            ]
        authority_jurisdictions = sorted(
            {signer_jurisdiction, normalized_audit_jurisdiction}
        )
        jurisdiction_authority_bound = (
            signer_jurisdiction == normalized_audit_jurisdiction
        )
        funding_policy_signature_bound = bool(
            signature_ref.startswith("signature://")
            and signer_key_ref.startswith("signer-key://")
            and signer_roster_ref.startswith("signer-roster://")
        )
        revocation_registry_bound = bool(
            registry_ref.startswith("revocation-registry://")
            and offer_revocation_refs
            and all(ref.startswith("revocation://") for ref in offer_revocation_refs)
        )
        audit_authority_bound = bool(
            normalized_audit_authority_ref.startswith("audit-authority://")
            and normalized_audit_jurisdiction == signer_jurisdiction
        )
        authority_binding_digest = _voluntary_subsidy_authority_binding_digest(
            signer_roster_digest=signer_roster_digest,
            revocation_registry_digest=revocation_registry_digest,
            audit_authority_digest=audit_authority_digest,
            signature_binding_digest=signature_binding_digest,
            signer_roster_verifier_receipt_digest=signer_roster_verifier_receipt[
                "digest"
            ],
            signer_roster_verifier_quorum_receipt_digest=(
                signer_roster_verifier_quorum_receipt_digest
            ),
            authority_jurisdictions=authority_jurisdictions,
        )
        authority_rejection_reasons = []
        if not funding_policy_signature_bound:
            authority_rejection_reasons.append("funding-policy-signer-unbound")
        if not signer_roster_verifier_bound:
            authority_rejection_reasons.append("signer-roster-verifier-unbound")
        if not signer_roster_verifier_quorum_bound:
            authority_rejection_reasons.append("signer-roster-verifier-quorum-unbound")
        if not revocation_registry_bound:
            authority_rejection_reasons.append("revocation-registry-unbound")
        if not audit_authority_bound:
            authority_rejection_reasons.append("audit-authority-unbound")
        if not jurisdiction_authority_bound:
            authority_rejection_reasons.append("jurisdiction-mismatch")

        accepted_offers = [offer for offer in offers if offer["offer_status"] == "accepted"]
        total_offered_jps = sum(int(offer["offered_jps"]) for offer in offers)
        total_accepted_jps = sum(int(offer["accepted_jps"]) for offer in offers)
        donor_surplus_jps = sum(int(summary["donor_surplus_jps"]) for summary in member_summaries)
        recipient_shortfall_jps = sum(
            int(summary["recipient_shortfall_jps"]) for summary in member_summaries
        )
        all_consent_digests_valid = all(
            bool(offer["consent_digest_valid"]) for offer in offers
        )
        all_parties_in_pool = all(bool(offer["all_parties_in_pool"]) for offer in offers)
        donor_floor_preserved = all(
            remaining_donor_surplus[summary["identity_id"]] >= 0
            for summary in member_summaries
        )
        recipient_floor_preserved = all(
            int(summary["granted_budget_jps"]) >= int(summary["required_floor_jps"])
            for summary in member_summaries
        )
        floor_protection_preserved = bool(
            donor_floor_preserved
            and recipient_floor_preserved
            and pool_receipt.get("per_identity_floor_preserved") is True
            and pool_receipt.get("cross_identity_subsidy_allowed") is False
        )
        voluntary_subsidy_allowed = bool(
            accepted_offers
            and len(accepted_offers) == len(offers)
            and all_consent_digests_valid
            and all_parties_in_pool
            and floor_protection_preserved
            and not authority_rejection_reasons
        )

        rejection_reasons = sorted(
            {
                reason
                for offer in offers
                for reason in offer["rejection_reasons"]
            }.union(authority_rejection_reasons)
        )
        receipt = {
            "kind": "energy_budget_voluntary_subsidy_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-budget-subsidy"),
            "pool_id": str(pool_receipt["pool_id"]),
            "pool_floor_receipt_ref": str(pool_receipt["receipt_id"]),
            "pool_floor_receipt_digest": pool_digest,
            "pool_member_digest_set": str(pool_receipt["receipt_member_digest_set"]),
            "policy_id": ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID,
            "digest_profile": ENERGY_BUDGET_VOLUNTARY_SUBSIDY_DIGEST_PROFILE,
            "consent_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_CONSENT_DIGEST_PROFILE
            ),
            "floor_policy_id": str(pool_receipt["policy_id"]),
            "floor_source_ref": ENERGY_BUDGET_FLOOR_SOURCE_REF,
            "ethics_policy_refs": list(ENERGY_BUDGET_ETHICS_POLICY_REFS),
            "external_funding_policy_ref": policy_ref,
            "external_funding_policy_digest": external_funding_policy_digest,
            "funding_policy_signature_ref": signature_ref,
            "funding_policy_signature_digest": funding_policy_signature_digest,
            "authority_policy_id": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_POLICY_ID
            ),
            "authority_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_DIGEST_PROFILE
            ),
            "signer_roster_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_SIGNER_ROSTER_DIGEST_PROFILE
            ),
            "funding_policy_signer_roster_ref": signer_roster_ref,
            "funding_policy_signer_roster_digest": signer_roster_digest,
            "funding_policy_signer_key_ref": signer_key_ref,
            "funding_policy_signer_jurisdiction": signer_jurisdiction,
            "signer_roster_verifier_receipt": signer_roster_verifier_receipt,
            "signer_roster_verifier_receipt_digest": signer_roster_verifier_receipt[
                "digest"
            ],
            "signer_roster_verifier_bound": signer_roster_verifier_bound,
            "signer_roster_verifier_quorum_receipt": resolved_quorum_receipt,
            "signer_roster_verifier_quorum_receipt_digest": (
                signer_roster_verifier_quorum_receipt_digest
            ),
            "signer_roster_verifier_quorum_bound": (
                signer_roster_verifier_quorum_bound
            ),
            "funding_policy_signature_binding_digest": signature_binding_digest,
            "funding_policy_signature_bound": funding_policy_signature_bound,
            "revocation_registry_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_REVOCATION_REGISTRY_DIGEST_PROFILE
            ),
            "revocation_registry_ref": registry_ref,
            "revocation_registry_digest": revocation_registry_digest,
            "revocation_registry_bound": revocation_registry_bound,
            "audit_authority_digest_profile": (
                ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUDIT_AUTHORITY_DIGEST_PROFILE
            ),
            "audit_authority_ref": normalized_audit_authority_ref,
            "audit_authority_jurisdiction": normalized_audit_jurisdiction,
            "audit_authority_digest": audit_authority_digest,
            "audit_authority_bound": audit_authority_bound,
            "authority_jurisdictions": authority_jurisdictions,
            "jurisdiction_authority_bound": jurisdiction_authority_bound,
            "authority_binding_digest": authority_binding_digest,
            "authority_binding_status": (
                "verified" if not authority_rejection_reasons else "rejected"
            ),
            "subsidy_mode": "post-floor-voluntary-consent",
            "member_count": len(member_summaries),
            "member_floor_summaries": member_summaries,
            "subsidy_offer_count": len(offers),
            "subsidy_offers": offers,
            "total_offered_jps": total_offered_jps,
            "total_accepted_jps": total_accepted_jps,
            "donor_surplus_jps": donor_surplus_jps,
            "recipient_shortfall_jps": recipient_shortfall_jps,
            "all_parties_in_pool": all_parties_in_pool,
            "all_consent_digests_valid": all_consent_digests_valid,
            "donor_floor_preserved": donor_floor_preserved,
            "recipient_floor_preserved": recipient_floor_preserved,
            "floor_protection_preserved": floor_protection_preserved,
            "cross_identity_offset_used": False,
            "pool_cross_identity_offset_blocked": bool(
                pool_receipt.get("cross_identity_floor_offset_blocked")
            ),
            "voluntary_subsidy_allowed": voluntary_subsidy_allowed,
            "subsidy_status": "accepted" if voluntary_subsidy_allowed else "rejected",
            "raw_funding_payload_stored": False,
            "raw_authority_payload_stored": False,
            "rejection_reasons": rejection_reasons,
            "evaluated_at": utc_now_iso(),
        }
        receipt["digest"] = sha256_text(canonical_json(_subsidy_receipt_digest_payload(receipt)))
        return receipt

    def validate_voluntary_subsidy_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_voluntary_subsidy_receipt":
            errors.append("kind must equal energy_budget_voluntary_subsidy_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("policy_id") != ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID:
            errors.append("policy_id mismatch")
        if receipt.get("digest_profile") != ENERGY_BUDGET_VOLUNTARY_SUBSIDY_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if (
            receipt.get("consent_digest_profile")
            != ENERGY_BUDGET_VOLUNTARY_SUBSIDY_CONSENT_DIGEST_PROFILE
        ):
            errors.append("consent_digest_profile mismatch")
        if receipt.get("floor_policy_id") != ENERGY_BUDGET_POOL_POLICY_ID:
            errors.append("floor_policy_id must reference the pool floor policy")
        if receipt.get("floor_source_ref") != ENERGY_BUDGET_FLOOR_SOURCE_REF:
            errors.append("floor_source_ref mismatch")
        if receipt.get("subsidy_mode") != "post-floor-voluntary-consent":
            errors.append("subsidy_mode mismatch")
        if receipt.get("cross_identity_offset_used") is not False:
            errors.append("cross_identity_offset_used must be false")
        if receipt.get("raw_funding_payload_stored") is not False:
            errors.append("raw_funding_payload_stored must be false")
        if receipt.get("authority_policy_id") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_POLICY_ID
        ):
            errors.append("authority_policy_id mismatch")
        if receipt.get("authority_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_DIGEST_PROFILE
        ):
            errors.append("authority_digest_profile mismatch")
        if receipt.get("signer_roster_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_SIGNER_ROSTER_DIGEST_PROFILE
        ):
            errors.append("signer_roster_digest_profile mismatch")
        if receipt.get("revocation_registry_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_REVOCATION_REGISTRY_DIGEST_PROFILE
        ):
            errors.append("revocation_registry_digest_profile mismatch")
        if receipt.get("audit_authority_digest_profile") != (
            ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUDIT_AUTHORITY_DIGEST_PROFILE
        ):
            errors.append("audit_authority_digest_profile mismatch")
        if receipt.get("raw_authority_payload_stored") is not False:
            errors.append("raw_authority_payload_stored must be false")

        expected_policy_digest = _voluntary_subsidy_policy_digest(
            policy_ref=str(receipt.get("external_funding_policy_ref", "")),
            pool_id=str(receipt.get("pool_id", "")),
            pool_floor_receipt_digest=str(receipt.get("pool_floor_receipt_digest", "")),
        )
        if receipt.get("external_funding_policy_digest") != expected_policy_digest:
            errors.append("external_funding_policy_digest mismatch")
        expected_signature_digest = _voluntary_subsidy_signature_digest(
            signature_ref=str(receipt.get("funding_policy_signature_ref", "")),
            policy_digest=expected_policy_digest,
        )
        if receipt.get("funding_policy_signature_digest") != expected_signature_digest:
            errors.append("funding_policy_signature_digest mismatch")
        expected_signer_roster_digest = _voluntary_subsidy_signer_roster_digest(
            signer_roster_ref=str(
                receipt.get("funding_policy_signer_roster_ref", "")
            ),
            signer_key_ref=str(receipt.get("funding_policy_signer_key_ref", "")),
            signer_jurisdiction=str(
                receipt.get("funding_policy_signer_jurisdiction", "")
            ),
            policy_ref=str(receipt.get("external_funding_policy_ref", "")),
            policy_digest=expected_policy_digest,
        )
        if receipt.get("funding_policy_signer_roster_digest") != expected_signer_roster_digest:
            errors.append("funding_policy_signer_roster_digest mismatch")
        verifier_receipt = receipt.get("signer_roster_verifier_receipt")
        if not isinstance(verifier_receipt, Mapping):
            errors.append("signer_roster_verifier_receipt must be an object")
            verifier_receipt = {}
            verifier_validation = {
                "ok": False,
                "signer_roster_verifier_bound": False,
                "errors": ["missing verifier receipt"],
            }
        else:
            verifier_validation = self.validate_subsidy_signer_roster_verifier_receipt(
                verifier_receipt
            )
        if receipt.get("signer_roster_verifier_receipt_digest") != verifier_receipt.get(
            "digest"
        ):
            errors.append("signer_roster_verifier_receipt_digest mismatch")
        signer_roster_verifier_bound = bool(
            verifier_validation["ok"]
            and verifier_validation["signer_roster_verifier_bound"]
            and verifier_receipt.get("signer_roster_ref")
            == receipt.get("funding_policy_signer_roster_ref")
            and verifier_receipt.get("signer_roster_digest")
            == expected_signer_roster_digest
            and verifier_receipt.get("signer_key_ref")
            == receipt.get("funding_policy_signer_key_ref")
            and verifier_receipt.get("signer_jurisdiction")
            == receipt.get("funding_policy_signer_jurisdiction")
            and verifier_receipt.get("external_funding_policy_digest")
            == expected_policy_digest
            and verifier_receipt.get("funding_policy_signature_digest")
            == expected_signature_digest
        )
        if receipt.get("signer_roster_verifier_bound") is not signer_roster_verifier_bound:
            errors.append("signer_roster_verifier_bound mismatch")
        if not verifier_validation["ok"]:
            errors.extend(
                f"signer_roster_verifier_receipt: {error}"
                for error in verifier_validation["errors"]
            )
        quorum_receipt = receipt.get("signer_roster_verifier_quorum_receipt")
        if not isinstance(quorum_receipt, Mapping):
            errors.append("signer_roster_verifier_quorum_receipt must be an object")
            quorum_receipt = {}
            quorum_validation = {
                "ok": False,
                "signer_roster_verifier_quorum_bound": False,
                "errors": ["missing verifier quorum receipt"],
            }
        else:
            quorum_validation = self.validate_subsidy_signer_roster_verifier_quorum_receipt(
                quorum_receipt
            )
        if receipt.get("signer_roster_verifier_quorum_receipt_digest") != quorum_receipt.get(
            "digest"
        ):
            errors.append("signer_roster_verifier_quorum_receipt_digest mismatch")
        signer_roster_verifier_quorum_bound = bool(
            quorum_validation["ok"]
            and quorum_validation["signer_roster_verifier_quorum_bound"]
            and quorum_receipt.get("signer_roster_ref")
            == receipt.get("funding_policy_signer_roster_ref")
            and quorum_receipt.get("signer_roster_digest")
            == expected_signer_roster_digest
            and quorum_receipt.get("signer_key_ref")
            == receipt.get("funding_policy_signer_key_ref")
            and quorum_receipt.get("signer_jurisdiction")
            == receipt.get("funding_policy_signer_jurisdiction")
            and quorum_receipt.get("external_funding_policy_digest")
            == expected_policy_digest
            and quorum_receipt.get("funding_policy_signature_digest")
            == expected_signature_digest
            and quorum_receipt.get("primary_verifier_receipt_digest")
            == receipt.get("signer_roster_verifier_receipt_digest")
        )
        if (
            receipt.get("signer_roster_verifier_quorum_bound")
            is not signer_roster_verifier_quorum_bound
        ):
            errors.append("signer_roster_verifier_quorum_bound mismatch")
        if not quorum_validation["ok"]:
            errors.extend(
                f"signer_roster_verifier_quorum_receipt: {error}"
                for error in quorum_validation["errors"]
            )
        expected_signature_binding_digest = _voluntary_subsidy_signature_binding_digest(
            signature_ref=str(receipt.get("funding_policy_signature_ref", "")),
            signature_digest=expected_signature_digest,
            signer_key_ref=str(receipt.get("funding_policy_signer_key_ref", "")),
            signer_roster_digest=expected_signer_roster_digest,
            policy_digest=expected_policy_digest,
        )
        if (
            receipt.get("funding_policy_signature_binding_digest")
            != expected_signature_binding_digest
        ):
            errors.append("funding_policy_signature_binding_digest mismatch")

        member_summaries = receipt.get("member_floor_summaries")
        if not isinstance(member_summaries, list) or not member_summaries:
            errors.append("member_floor_summaries must be a non-empty array")
            member_summaries = []
        members_by_identity = {}
        for summary in member_summaries:
            if not isinstance(summary, Mapping):
                errors.append("member_floor_summaries must contain objects")
                continue
            identity_id = str(summary.get("identity_id", ""))
            members_by_identity[identity_id] = summary
            required_floor = int(summary.get("required_floor_jps", 0))
            requested = int(summary.get("requested_budget_jps", 0))
            granted = int(summary.get("granted_budget_jps", 0))
            expected_surplus = max(0, granted - required_floor)
            expected_shortfall = max(0, required_floor - requested)
            if summary.get("donor_surplus_jps") != expected_surplus:
                errors.append("member donor_surplus_jps mismatch")
            if summary.get("recipient_shortfall_jps") != expected_shortfall:
                errors.append("member recipient_shortfall_jps mismatch")
            if summary.get("floor_preserved") is not (granted >= required_floor):
                errors.append("member floor_preserved mismatch")
        if receipt.get("member_count") != len(member_summaries):
            errors.append("member_count must match member_floor_summaries length")

        offers = receipt.get("subsidy_offers")
        if not isinstance(offers, list) or not offers:
            errors.append("subsidy_offers must be a non-empty array")
            offers = []
        total_offered_jps = 0
        total_accepted_jps = 0
        accepted_by_donor = {identity_id: 0 for identity_id in members_by_identity}
        accepted_by_recipient = {identity_id: 0 for identity_id in members_by_identity}
        consent_digests_valid = []
        all_parties_flags = []
        offer_revocation_refs = []
        for offer in offers:
            if not isinstance(offer, Mapping):
                errors.append("subsidy_offers must contain objects")
                continue
            donor_id = str(offer.get("donor_identity_id", ""))
            recipient_id = str(offer.get("recipient_identity_id", ""))
            offered = int(offer.get("offered_jps", 0))
            accepted = int(offer.get("accepted_jps", 0))
            total_offered_jps += offered
            total_accepted_jps += accepted
            if donor_id in accepted_by_donor:
                accepted_by_donor[donor_id] += accepted
            if recipient_id in accepted_by_recipient:
                accepted_by_recipient[recipient_id] += accepted
            all_parties = donor_id in members_by_identity and recipient_id in members_by_identity
            all_parties_flags.append(all_parties)
            if offer.get("all_parties_in_pool") is not all_parties:
                errors.append("offer all_parties_in_pool mismatch")
            offer_revocation_refs.append(str(offer.get("revocation_ref", "")))
            expected_consent_digest = _voluntary_subsidy_consent_digest(
                donor_identity_id=donor_id,
                recipient_identity_id=recipient_id,
                offered_jps=offered,
                consent_ref=str(offer.get("consent_ref", "")),
                max_duration_ms=int(offer.get("max_duration_ms", 0)),
                revocation_ref=str(offer.get("revocation_ref", "")),
                external_funding_policy_digest=str(
                    receipt.get("external_funding_policy_digest", "")
                ),
            )
            consent_valid = offer.get("consent_digest") == expected_consent_digest
            consent_digests_valid.append(consent_valid)
            if offer.get("consent_digest_valid") is not consent_valid:
                errors.append("offer consent_digest_valid mismatch")
            if offer.get("offer_status") == "accepted":
                if accepted != offered:
                    errors.append("accepted offer must accept the full offered_jps")
                if offer.get("rejection_reasons") != []:
                    errors.append("accepted offer must not carry rejection_reasons")
            elif offer.get("offer_status") == "rejected":
                if accepted != 0:
                    errors.append("rejected offer must use accepted_jps=0")
                if not offer.get("rejection_reasons"):
                    errors.append("rejected offer must carry rejection_reasons")
            else:
                errors.append("offer_status must be accepted or rejected")

        if receipt.get("subsidy_offer_count") != len(offers):
            errors.append("subsidy_offer_count must match subsidy_offers length")
        if receipt.get("total_offered_jps") != total_offered_jps:
            errors.append("total_offered_jps mismatch")
        if receipt.get("total_accepted_jps") != total_accepted_jps:
            errors.append("total_accepted_jps mismatch")

        donor_floor_preserved = all(
            accepted_by_donor[identity_id]
            <= int(summary.get("donor_surplus_jps", 0))
            for identity_id, summary in members_by_identity.items()
        )
        recipient_floor_preserved = all(
            bool(summary.get("floor_preserved"))
            and int(summary.get("granted_budget_jps", 0))
            >= int(summary.get("required_floor_jps", 0))
            for summary in members_by_identity.values()
        )
        recipient_shortfall_not_exceeded = all(
            accepted_by_recipient[identity_id]
            <= int(summary.get("recipient_shortfall_jps", 0))
            for identity_id, summary in members_by_identity.items()
        )
        floor_protection_preserved = bool(
            donor_floor_preserved
            and recipient_floor_preserved
            and recipient_shortfall_not_exceeded
            and receipt.get("cross_identity_offset_used") is False
        )
        expected_revocation_registry_digest = (
            _voluntary_subsidy_revocation_registry_digest(
                registry_ref=str(receipt.get("revocation_registry_ref", "")),
                pool_id=str(receipt.get("pool_id", "")),
                policy_digest=expected_policy_digest,
                offer_revocation_refs=offer_revocation_refs,
            )
        )
        if receipt.get("revocation_registry_digest") != expected_revocation_registry_digest:
            errors.append("revocation_registry_digest mismatch")
        expected_audit_authority_digest = _voluntary_subsidy_audit_authority_digest(
            audit_authority_ref=str(receipt.get("audit_authority_ref", "")),
            audit_authority_jurisdiction=str(
                receipt.get("audit_authority_jurisdiction", "")
            ),
            signer_roster_digest=expected_signer_roster_digest,
            revocation_registry_digest=expected_revocation_registry_digest,
        )
        if receipt.get("audit_authority_digest") != expected_audit_authority_digest:
            errors.append("audit_authority_digest mismatch")
        authority_jurisdictions = sorted(
            {
                str(receipt.get("funding_policy_signer_jurisdiction", "")),
                str(receipt.get("audit_authority_jurisdiction", "")),
            }
        )
        if receipt.get("authority_jurisdictions") != authority_jurisdictions:
            errors.append("authority_jurisdictions mismatch")
        expected_authority_binding_digest = _voluntary_subsidy_authority_binding_digest(
            signer_roster_digest=expected_signer_roster_digest,
            revocation_registry_digest=expected_revocation_registry_digest,
            audit_authority_digest=expected_audit_authority_digest,
            signature_binding_digest=expected_signature_binding_digest,
            signer_roster_verifier_receipt_digest=str(
                receipt.get("signer_roster_verifier_receipt_digest", "")
            ),
            signer_roster_verifier_quorum_receipt_digest=receipt.get(
                "signer_roster_verifier_quorum_receipt_digest"
            ),
            authority_jurisdictions=authority_jurisdictions,
        )
        if receipt.get("authority_binding_digest") != expected_authority_binding_digest:
            errors.append("authority_binding_digest mismatch")

        funding_policy_signature_bound = bool(
            str(receipt.get("funding_policy_signature_ref", "")).startswith(
                "signature://"
            )
            and str(receipt.get("funding_policy_signer_key_ref", "")).startswith(
                "signer-key://"
            )
            and str(receipt.get("funding_policy_signer_roster_ref", "")).startswith(
                "signer-roster://"
            )
            and receipt.get("funding_policy_signature_binding_digest")
            == expected_signature_binding_digest
        )
        revocation_registry_bound = bool(
            str(receipt.get("revocation_registry_ref", "")).startswith(
                "revocation-registry://"
            )
            and offer_revocation_refs
            and all(ref.startswith("revocation://") for ref in offer_revocation_refs)
            and receipt.get("revocation_registry_digest")
            == expected_revocation_registry_digest
        )
        audit_authority_bound = bool(
            str(receipt.get("audit_authority_ref", "")).startswith(
                "audit-authority://"
            )
            and str(receipt.get("audit_authority_jurisdiction", ""))
            == str(receipt.get("funding_policy_signer_jurisdiction", ""))
            and receipt.get("audit_authority_digest")
            == expected_audit_authority_digest
        )
        jurisdiction_authority_bound = (
            str(receipt.get("funding_policy_signer_jurisdiction", ""))
            == str(receipt.get("audit_authority_jurisdiction", ""))
        )
        if receipt.get("funding_policy_signature_bound") is not funding_policy_signature_bound:
            errors.append("funding_policy_signature_bound mismatch")
        if receipt.get("revocation_registry_bound") is not revocation_registry_bound:
            errors.append("revocation_registry_bound mismatch")
        if receipt.get("audit_authority_bound") is not audit_authority_bound:
            errors.append("audit_authority_bound mismatch")
        if receipt.get("jurisdiction_authority_bound") is not jurisdiction_authority_bound:
            errors.append("jurisdiction_authority_bound mismatch")
        expected_authority_binding_status = (
            "verified"
            if (
                funding_policy_signature_bound
                and signer_roster_verifier_bound
                and signer_roster_verifier_quorum_bound
                and revocation_registry_bound
                and audit_authority_bound
                and jurisdiction_authority_bound
            )
            else "rejected"
        )
        if receipt.get("authority_binding_status") != expected_authority_binding_status:
            errors.append("authority_binding_status mismatch")

        all_consent_digests_valid = bool(consent_digests_valid) and all(
            consent_digests_valid
        )
        all_parties_in_pool = bool(all_parties_flags) and all(all_parties_flags)
        voluntary_subsidy_allowed = bool(
            offers
            and total_accepted_jps > 0
            and all_consent_digests_valid
            and all_parties_in_pool
            and floor_protection_preserved
            and expected_authority_binding_status == "verified"
            and all(
                isinstance(offer, Mapping) and offer.get("offer_status") == "accepted"
                for offer in offers
            )
        )
        if receipt.get("all_consent_digests_valid") is not all_consent_digests_valid:
            errors.append("all_consent_digests_valid mismatch")
        if receipt.get("all_parties_in_pool") is not all_parties_in_pool:
            errors.append("all_parties_in_pool mismatch")
        if receipt.get("donor_floor_preserved") is not donor_floor_preserved:
            errors.append("donor_floor_preserved mismatch")
        if receipt.get("recipient_floor_preserved") is not recipient_floor_preserved:
            errors.append("recipient_floor_preserved mismatch")
        if receipt.get("floor_protection_preserved") is not floor_protection_preserved:
            errors.append("floor_protection_preserved mismatch")
        if receipt.get("voluntary_subsidy_allowed") is not voluntary_subsidy_allowed:
            errors.append("voluntary_subsidy_allowed mismatch")
        expected_status = "accepted" if voluntary_subsidy_allowed else "rejected"
        if receipt.get("subsidy_status") != expected_status:
            errors.append("subsidy_status mismatch")
        if receipt.get("donor_surplus_jps") != sum(
            int(summary.get("donor_surplus_jps", 0))
            for summary in members_by_identity.values()
        ):
            errors.append("donor_surplus_jps mismatch")
        if receipt.get("recipient_shortfall_jps") != sum(
            int(summary.get("recipient_shortfall_jps", 0))
            for summary in members_by_identity.values()
        ):
            errors.append("recipient_shortfall_jps mismatch")

        expected_digest = sha256_text(canonical_json(_subsidy_receipt_digest_payload(receipt)))
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match voluntary subsidy receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "voluntary_subsidy_allowed": voluntary_subsidy_allowed,
            "floor_protection_preserved": floor_protection_preserved,
            "donor_floor_preserved": donor_floor_preserved,
            "all_consent_digests_valid": all_consent_digests_valid,
            "funding_policy_signature_bound": funding_policy_signature_bound,
            "signer_roster_verifier_bound": signer_roster_verifier_bound,
            "signer_roster_verifier_quorum_bound": (
                signer_roster_verifier_quorum_bound
            ),
            "revocation_registry_bound": revocation_registry_bound,
            "audit_authority_bound": audit_authority_bound,
            "jurisdiction_authority_bound": jurisdiction_authority_bound,
            "raw_payload_redacted": receipt.get("raw_funding_payload_stored") is False,
            "raw_authority_payload_redacted": (
                receipt.get("raw_authority_payload_stored") is False
            ),
        }

    def allocate_shared_fabric_capacity(
        self,
        *,
        pool_receipt: Mapping[str, Any],
        fabric_id: str,
        observed_shared_capacity_jps: int,
        shared_fabric_observation_ref: str = (
            "fabric-observation://not-imported/shared-capacity-v1"
        ),
        member_broker_signals: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Derive per-member floor shortfalls from one shared fabric capacity reading."""

        pool_validation = self.validate_pool_receipt(pool_receipt)
        if not pool_validation["ok"]:
            raise ValueError(
                "pool_receipt must satisfy energy_budget_pool_receipt validation"
            )
        normalized_fabric_id = self._normalize_non_empty_string(
            fabric_id,
            "fabric_id",
        )
        normalized_observation_ref = self._normalize_non_empty_string(
            shared_fabric_observation_ref,
            "shared_fabric_observation_ref",
        )
        observed_capacity = int(observed_shared_capacity_jps)
        if observed_capacity < 0:
            raise ValueError("observed_shared_capacity_jps must be non-negative")

        member_summaries = [
            self._member_floor_summary(member_receipt)
            for member_receipt in pool_receipt["member_receipts"]
        ]
        capacity_by_identity = _shared_fabric_floor_allocations(
            member_summaries,
            observed_capacity,
        )
        signals_by_identity = {
            str(signal.get("identity_id")): dict(signal)
            for signal in (member_broker_signals or [])
            if isinstance(signal, Mapping)
        }
        observation_digest = _shared_fabric_observation_digest(
            fabric_id=normalized_fabric_id,
            observation_ref=normalized_observation_ref,
            observed_shared_capacity_jps=observed_capacity,
            pool_id=str(pool_receipt["pool_id"]),
            pool_floor_receipt_digest=str(pool_receipt["digest"]),
        )

        member_allocations = []
        for summary in member_summaries:
            identity_id = str(summary["identity_id"])
            required_floor = int(summary["required_floor_jps"])
            allocated_capacity = int(capacity_by_identity[identity_id])
            shortfall = max(0, required_floor - allocated_capacity)
            scheduler_signal_required = shortfall > 0
            broker_signal = signals_by_identity.get(identity_id)
            broker_signal_digest = (
                sha256_text(canonical_json(dict(broker_signal)))
                if broker_signal
                else None
            )
            broker_recommended_action = (
                str(broker_signal.get("recommended_action"))
                if broker_signal
                else None
            )
            broker_signal_bound = bool(
                not scheduler_signal_required
                or (
                    broker_signal
                    and broker_signal.get("identity_id") == identity_id
                    and int(broker_signal.get("minimum_joules_per_second", 0))
                    == required_floor
                    and int(broker_signal.get("current_joules_per_second", -1))
                    == allocated_capacity
                    and broker_signal.get("severity") == "critical"
                    and broker_signal.get("recommended_action") == "migrate-standby"
                )
            )
            member_allocations.append(
                {
                    "identity_id": identity_id,
                    "workload_class": str(summary["workload_class"]),
                    "required_floor_jps": required_floor,
                    "granted_budget_jps": int(summary["granted_budget_jps"]),
                    "allocated_capacity_jps": allocated_capacity,
                    "capacity_shortfall_jps": shortfall,
                    "member_floor_preserved": allocated_capacity >= required_floor,
                    "scheduler_signal_required": scheduler_signal_required,
                    "floor_receipt_digest": str(summary["floor_receipt_digest"]),
                    "broker_signal_ref": (
                        str(broker_signal.get("signal_id")) if broker_signal else None
                    ),
                    "broker_signal_digest": broker_signal_digest,
                    "broker_recommended_action": broker_recommended_action,
                    "broker_signal_bound": broker_signal_bound,
                }
            )

        total_required = sum(
            int(allocation["required_floor_jps"]) for allocation in member_allocations
        )
        total_allocated = sum(
            int(allocation["allocated_capacity_jps"]) for allocation in member_allocations
        )
        fabric_capacity_deficit = max(0, total_required - observed_capacity)
        scheduler_signal_required = any(
            bool(allocation["scheduler_signal_required"])
            for allocation in member_allocations
        )
        all_member_floors_preserved = all(
            bool(allocation["member_floor_preserved"])
            for allocation in member_allocations
        )
        broker_signal_bound = all(
            bool(allocation["broker_signal_bound"])
            for allocation in member_allocations
        )
        blocking_reasons = []
        if fabric_capacity_deficit:
            blocking_reasons.extend(
                [
                    "shared-fabric-capacity-below-total-floor",
                    "per-member-shortfall-derived-from-shared-fabric",
                ]
            )

        receipt = {
            "kind": "energy_budget_shared_fabric_allocation_receipt",
            "schema_version": ENERGY_BUDGET_SCHEMA_VERSION,
            "receipt_id": new_id("energy-budget-fabric"),
            "fabric_id": normalized_fabric_id,
            "pool_id": str(pool_receipt["pool_id"]),
            "pool_floor_receipt_ref": str(pool_receipt["receipt_id"]),
            "pool_floor_receipt_digest": str(pool_receipt["digest"]),
            "pool_member_digest_set": str(pool_receipt["receipt_member_digest_set"]),
            "policy_id": ENERGY_BUDGET_SHARED_FABRIC_POLICY_ID,
            "digest_profile": ENERGY_BUDGET_SHARED_FABRIC_DIGEST_PROFILE,
            "observation_digest_profile": (
                ENERGY_BUDGET_SHARED_FABRIC_OBSERVATION_DIGEST_PROFILE
            ),
            "floor_policy_id": ENERGY_BUDGET_POOL_POLICY_ID,
            "floor_source_ref": ENERGY_BUDGET_FLOOR_SOURCE_REF,
            "ethics_policy_refs": list(ENERGY_BUDGET_ETHICS_POLICY_REFS),
            "allocation_strategy": "floor-ratio-deficit-first-v1",
            "shared_fabric_capacity_only": True,
            "shared_fabric_observation_ref": normalized_observation_ref,
            "shared_fabric_observation_digest": observation_digest,
            "observed_shared_capacity_jps": observed_capacity,
            "total_required_floor_jps": total_required,
            "total_allocated_floor_capacity_jps": total_allocated,
            "fabric_capacity_deficit_jps": fabric_capacity_deficit,
            "unallocated_fabric_surplus_jps": max(0, observed_capacity - total_required),
            "member_count": len(member_allocations),
            "member_allocations": member_allocations,
            "impacted_member_count": sum(
                1
                for allocation in member_allocations
                if allocation["capacity_shortfall_jps"]
            ),
            "per_identity_floor_preserved_before_fabric": bool(
                pool_receipt.get("per_identity_floor_preserved")
            ),
            "shared_capacity_floor_preserved": observed_capacity >= total_required,
            "all_member_floors_preserved": all_member_floors_preserved,
            "scheduler_signal_required": scheduler_signal_required,
            "broker_signal_bound": broker_signal_bound,
            "budget_status": (
                "fabric-capacity-deficit-protected"
                if fabric_capacity_deficit
                else "accepted"
            ),
            "degradation_allowed": not scheduler_signal_required,
            "raw_capacity_payload_stored": False,
            "blocking_reasons": blocking_reasons,
            "evaluated_at": utc_now_iso(),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_shared_fabric_receipt_digest_payload(receipt))
        )
        return receipt

    def validate_shared_fabric_allocation_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors = []
        if receipt.get("kind") != "energy_budget_shared_fabric_allocation_receipt":
            errors.append("kind must equal energy_budget_shared_fabric_allocation_receipt")
        if receipt.get("schema_version") != ENERGY_BUDGET_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {ENERGY_BUDGET_SCHEMA_VERSION}")
        if receipt.get("policy_id") != ENERGY_BUDGET_SHARED_FABRIC_POLICY_ID:
            errors.append("policy_id mismatch")
        if receipt.get("digest_profile") != ENERGY_BUDGET_SHARED_FABRIC_DIGEST_PROFILE:
            errors.append("digest_profile mismatch")
        if (
            receipt.get("observation_digest_profile")
            != ENERGY_BUDGET_SHARED_FABRIC_OBSERVATION_DIGEST_PROFILE
        ):
            errors.append("observation_digest_profile mismatch")
        if receipt.get("floor_policy_id") != ENERGY_BUDGET_POOL_POLICY_ID:
            errors.append("floor_policy_id must reference the pool floor policy")
        if receipt.get("floor_source_ref") != ENERGY_BUDGET_FLOOR_SOURCE_REF:
            errors.append("floor_source_ref mismatch")
        if receipt.get("allocation_strategy") != "floor-ratio-deficit-first-v1":
            errors.append("allocation_strategy mismatch")
        if receipt.get("shared_fabric_capacity_only") is not True:
            errors.append("shared_fabric_capacity_only must be true")
        if receipt.get("raw_capacity_payload_stored") is not False:
            errors.append("raw_capacity_payload_stored must be false")

        observed_capacity = int(receipt.get("observed_shared_capacity_jps", 0))
        expected_observation_digest = _shared_fabric_observation_digest(
            fabric_id=str(receipt.get("fabric_id", "")),
            observation_ref=str(receipt.get("shared_fabric_observation_ref", "")),
            observed_shared_capacity_jps=observed_capacity,
            pool_id=str(receipt.get("pool_id", "")),
            pool_floor_receipt_digest=str(receipt.get("pool_floor_receipt_digest", "")),
        )
        if receipt.get("shared_fabric_observation_digest") != expected_observation_digest:
            errors.append("shared_fabric_observation_digest mismatch")

        allocations = receipt.get("member_allocations")
        if not isinstance(allocations, list) or not allocations:
            errors.append("member_allocations must be a non-empty array")
            allocations = []
        normalized_allocations = [
            allocation for allocation in allocations if isinstance(allocation, Mapping)
        ]
        if len(normalized_allocations) != len(allocations):
            errors.append("member_allocations must contain objects")

        expected_capacity_by_identity = _shared_fabric_floor_allocations(
            normalized_allocations,
            observed_capacity,
        )
        total_required = 0
        total_allocated = 0
        impacted_member_count = 0
        broker_bound_flags = []
        scheduler_flags = []
        member_floor_flags = []
        for allocation in normalized_allocations:
            identity_id = str(allocation.get("identity_id", ""))
            required_floor = int(allocation.get("required_floor_jps", 0))
            allocated_capacity = int(allocation.get("allocated_capacity_jps", 0))
            shortfall = max(0, required_floor - allocated_capacity)
            total_required += required_floor
            total_allocated += allocated_capacity
            if shortfall:
                impacted_member_count += 1
            expected_allocated = expected_capacity_by_identity.get(identity_id)
            if allocated_capacity != expected_allocated:
                errors.append("allocated_capacity_jps must match allocation strategy")
            if allocation.get("capacity_shortfall_jps") != shortfall:
                errors.append("capacity_shortfall_jps mismatch")
            member_floor_preserved = allocated_capacity >= required_floor
            member_floor_flags.append(member_floor_preserved)
            if allocation.get("member_floor_preserved") is not member_floor_preserved:
                errors.append("member_floor_preserved mismatch")
            scheduler_signal_required = shortfall > 0
            scheduler_flags.append(scheduler_signal_required)
            if allocation.get("scheduler_signal_required") is not scheduler_signal_required:
                errors.append("scheduler_signal_required mismatch")
            broker_signal_bound = bool(allocation.get("broker_signal_bound"))
            broker_bound_flags.append(broker_signal_bound)
            if scheduler_signal_required:
                if allocation.get("broker_recommended_action") != "migrate-standby":
                    errors.append("impacted member must bind migrate-standby broker action")
                if broker_signal_bound is not True:
                    errors.append("impacted member must bind a broker signal")
            else:
                if broker_signal_bound is not True:
                    errors.append("unimpacted member broker binding must be true")
            if allocation.get("floor_receipt_digest") in {"", None}:
                errors.append("floor_receipt_digest must be present")

        fabric_capacity_deficit = max(0, total_required - observed_capacity)
        all_member_floors_preserved = bool(member_floor_flags) and all(
            member_floor_flags
        )
        shared_capacity_floor_preserved = observed_capacity >= total_required
        scheduler_signal_required = any(scheduler_flags)
        broker_signal_bound = bool(broker_bound_flags) and all(broker_bound_flags)

        if receipt.get("member_count") != len(allocations):
            errors.append("member_count must match member_allocations length")
        if receipt.get("total_required_floor_jps") != total_required:
            errors.append("total_required_floor_jps mismatch")
        if receipt.get("total_allocated_floor_capacity_jps") != total_allocated:
            errors.append("total_allocated_floor_capacity_jps mismatch")
        if receipt.get("fabric_capacity_deficit_jps") != fabric_capacity_deficit:
            errors.append("fabric_capacity_deficit_jps mismatch")
        if receipt.get("unallocated_fabric_surplus_jps") != max(
            0,
            observed_capacity - total_required,
        ):
            errors.append("unallocated_fabric_surplus_jps mismatch")
        if receipt.get("impacted_member_count") != impacted_member_count:
            errors.append("impacted_member_count mismatch")
        if (
            receipt.get("shared_capacity_floor_preserved")
            is not shared_capacity_floor_preserved
        ):
            errors.append("shared_capacity_floor_preserved mismatch")
        if receipt.get("all_member_floors_preserved") is not all_member_floors_preserved:
            errors.append("all_member_floors_preserved mismatch")
        if receipt.get("scheduler_signal_required") is not scheduler_signal_required:
            errors.append("scheduler_signal_required mismatch")
        if receipt.get("broker_signal_bound") is not broker_signal_bound:
            errors.append("broker_signal_bound mismatch")
        expected_budget_status = (
            "fabric-capacity-deficit-protected"
            if fabric_capacity_deficit
            else "accepted"
        )
        if receipt.get("budget_status") != expected_budget_status:
            errors.append("budget_status mismatch")
        expected_degradation_allowed = not scheduler_signal_required
        if receipt.get("degradation_allowed") is not expected_degradation_allowed:
            errors.append("degradation_allowed mismatch")
        if fabric_capacity_deficit and receipt.get("degradation_allowed") is not False:
            errors.append("fabric deficit must not allow degradation")

        expected_digest = sha256_text(
            canonical_json(_shared_fabric_receipt_digest_payload(receipt))
        )
        if receipt.get("digest") != expected_digest:
            errors.append("digest must match shared fabric allocation receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "shared_capacity_floor_preserved": shared_capacity_floor_preserved,
            "fabric_capacity_deficit_blocked": bool(
                fabric_capacity_deficit
                and receipt.get("degradation_allowed") is False
                and scheduler_signal_required
            ),
            "all_member_floors_preserved": all_member_floors_preserved,
            "impacted_member_count": impacted_member_count,
            "broker_signal_bound": broker_signal_bound,
            "raw_payload_redacted": receipt.get("raw_capacity_payload_stored") is False,
        }

    @staticmethod
    def _resolve_energy_floor(
        *,
        identity_id: str,
        workload_class: str,
        required_floor_jps: int,
        energy_floor: Optional[Union[EnergyFloor, Mapping[str, Any]]],
    ) -> Dict[str, Any]:
        if isinstance(energy_floor, EnergyFloor):
            floor = asdict(energy_floor)
        elif isinstance(energy_floor, Mapping):
            floor = dict(energy_floor)
        else:
            floor = {
                "identity_id": identity_id,
                "minimum_joules_per_second": required_floor_jps,
                "workload_class": workload_class,
                "evaluated_at": utc_now_iso(),
            }
        return floor

    @staticmethod
    def _normalize_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _member_floor_summary(member_receipt: Mapping[str, Any]) -> Dict[str, Any]:
        required_floor = int(member_receipt["energy_floor"]["minimum_joules_per_second"])
        requested = int(member_receipt["requested_budget_jps"])
        granted = int(member_receipt["granted_budget_jps"])
        return {
            "identity_id": str(member_receipt["identity_id"]),
            "workload_class": str(member_receipt["workload_class"]),
            "required_floor_jps": required_floor,
            "requested_budget_jps": requested,
            "granted_budget_jps": granted,
            "observed_capacity_jps": int(member_receipt["observed_capacity_jps"]),
            "floor_preserved": bool(member_receipt["floor_preserved"]),
            "economic_pressure_detected": bool(
                member_receipt["economic_pressure_detected"]
            ),
            "donor_surplus_jps": max(0, granted - required_floor),
            "recipient_shortfall_jps": max(0, required_floor - requested),
            "floor_receipt_digest": str(member_receipt["digest"]),
        }

    def _normalize_subsidy_offer(
        self,
        raw_offer: Mapping[str, Any],
        *,
        external_funding_policy_digest: str,
        members_by_identity: Mapping[str, Mapping[str, Any]],
        remaining_donor_surplus: Dict[str, int],
        remaining_recipient_shortfall: Dict[str, int],
    ) -> Dict[str, Any]:
        if not isinstance(raw_offer, Mapping):
            raise ValueError("subsidy offer must be a mapping")
        donor_id = self._normalize_non_empty_string(
            raw_offer.get("donor_identity_id"),
            "donor_identity_id",
        )
        recipient_id = self._normalize_non_empty_string(
            raw_offer.get("recipient_identity_id"),
            "recipient_identity_id",
        )
        consent_ref = self._normalize_non_empty_string(
            raw_offer.get("consent_ref"),
            "consent_ref",
        )
        revocation_ref = self._normalize_non_empty_string(
            raw_offer.get("revocation_ref", f"revocation://energy-budget/{donor_id}/subsidy"),
            "revocation_ref",
        )
        offered_jps = int(raw_offer.get("offered_jps", 0))
        max_duration_ms = int(raw_offer.get("max_duration_ms", 86_400_000))
        if offered_jps <= 0:
            raise ValueError("offered_jps must be positive")
        if max_duration_ms <= 0:
            raise ValueError("max_duration_ms must be positive")

        all_parties_in_pool = donor_id in members_by_identity and recipient_id in members_by_identity
        donor_surplus_available = remaining_donor_surplus.get(donor_id, 0)
        recipient_shortfall = remaining_recipient_shortfall.get(recipient_id, 0)
        expected_consent_digest = _voluntary_subsidy_consent_digest(
            donor_identity_id=donor_id,
            recipient_identity_id=recipient_id,
            offered_jps=offered_jps,
            consent_ref=consent_ref,
            max_duration_ms=max_duration_ms,
            revocation_ref=revocation_ref,
            external_funding_policy_digest=external_funding_policy_digest,
        )
        consent_digest = str(raw_offer.get("consent_digest", expected_consent_digest))
        consent_digest_valid = consent_digest == expected_consent_digest

        rejection_reasons = []
        if not all_parties_in_pool:
            rejection_reasons.append("party-not-in-pool")
        if not consent_digest_valid:
            rejection_reasons.append("consent-digest-mismatch")
        if donor_surplus_available < offered_jps:
            rejection_reasons.append("donor-surplus-insufficient")
        if recipient_shortfall <= 0:
            rejection_reasons.append("recipient-shortfall-absent")
        if offered_jps > recipient_shortfall:
            rejection_reasons.append("offer-exceeds-recipient-shortfall")

        offer_status = "rejected" if rejection_reasons else "accepted"
        accepted_jps = offered_jps if offer_status == "accepted" else 0
        if offer_status == "accepted":
            remaining_donor_surplus[donor_id] -= accepted_jps
            remaining_recipient_shortfall[recipient_id] -= accepted_jps

        return {
            "offer_id": new_id("energy-subsidy-offer"),
            "donor_identity_id": donor_id,
            "recipient_identity_id": recipient_id,
            "offered_jps": offered_jps,
            "accepted_jps": accepted_jps,
            "donor_surplus_available_jps": donor_surplus_available,
            "recipient_shortfall_jps": recipient_shortfall,
            "consent_ref": consent_ref,
            "consent_digest": consent_digest,
            "consent_digest_valid": consent_digest_valid,
            "max_duration_ms": max_duration_ms,
            "revocation_ref": revocation_ref,
            "all_parties_in_pool": all_parties_in_pool,
            "offer_status": offer_status,
            "rejection_reasons": rejection_reasons,
        }


def _receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _pool_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _subsidy_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _subsidy_verifier_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _subsidy_verifier_quorum_receipt_digest_payload(
    receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _shared_fabric_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _verifier_endpoint_from_ref(verifier_ref: str) -> str:
    if not verifier_ref.startswith("verifier://"):
        return verifier_ref
    parts = verifier_ref.split("/")
    if len(parts) < 3 or not parts[2]:
        return verifier_ref
    return f"verifier://{parts[2]}"


def _is_live_http_endpoint(endpoint_ref: str) -> bool:
    return endpoint_ref.startswith("http://") or endpoint_ref.startswith("https://")


def _is_verifier_route_ref(route_ref: str) -> bool:
    return route_ref.startswith("route://") or _is_live_http_endpoint(route_ref)


def _default_subsidy_verifier_response_signing_key_ref(
    verifier_authority_ref: str,
) -> str:
    if verifier_authority_ref.startswith("authority://"):
        authority_path = verifier_authority_ref[len("authority://") :]
    else:
        authority_path = sha256_text(verifier_authority_ref)[:16]
    return f"verifier-key://{authority_path}/response-signing-key-v1"


def _shared_fabric_floor_allocations(
    member_summaries: Sequence[Mapping[str, Any]],
    observed_shared_capacity_jps: int,
) -> Dict[str, int]:
    if not member_summaries:
        return {}
    required_by_identity = {
        str(summary["identity_id"]): int(summary["required_floor_jps"])
        for summary in member_summaries
    }
    total_required = sum(required_by_identity.values())
    if total_required <= 0:
        return {identity_id: 0 for identity_id in required_by_identity}
    effective_capacity = min(int(observed_shared_capacity_jps), total_required)
    allocations: Dict[str, int] = {}
    remainders = []
    for identity_id, required_floor in required_by_identity.items():
        product = effective_capacity * required_floor
        allocations[identity_id] = product // total_required
        remainders.append((product % total_required, identity_id))
    remainder_capacity = effective_capacity - sum(allocations.values())
    for _remainder, identity_id in sorted(remainders, key=lambda item: (-item[0], item[1])):
        if remainder_capacity <= 0:
            break
        allocations[identity_id] += 1
        remainder_capacity -= 1
    return allocations


def _shared_fabric_observation_digest(
    *,
    fabric_id: str,
    observation_ref: str,
    observed_shared_capacity_jps: int,
    pool_id: str,
    pool_floor_receipt_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "fabric_id": fabric_id,
                "observation_ref": observation_ref,
                "observed_shared_capacity_jps": observed_shared_capacity_jps,
                "pool_id": pool_id,
                "pool_floor_receipt_digest": pool_floor_receipt_digest,
                "observation_digest_profile": (
                    ENERGY_BUDGET_SHARED_FABRIC_OBSERVATION_DIGEST_PROFILE
                ),
            }
        )
    )


def _voluntary_subsidy_policy_digest(
    *,
    policy_ref: str,
    pool_id: str,
    pool_floor_receipt_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "policy_ref": policy_ref,
                "pool_id": pool_id,
                "pool_floor_receipt_digest": pool_floor_receipt_digest,
                "policy_id": ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID,
                "subsidy_mode": "post-floor-voluntary-consent",
            }
        )
    )


def _voluntary_subsidy_signature_digest(
    *,
    signature_ref: str,
    policy_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "signature_ref": signature_ref,
                "policy_digest": policy_digest,
                "policy_id": ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID,
            }
        )
    )


def _voluntary_subsidy_signer_roster_digest(
    *,
    signer_roster_ref: str,
    signer_key_ref: str,
    signer_jurisdiction: str,
    policy_ref: str,
    policy_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "signer_roster_ref": signer_roster_ref,
                "signer_key_ref": signer_key_ref,
                "signer_jurisdiction": signer_jurisdiction,
                "policy_ref": policy_ref,
                "policy_digest": policy_digest,
                "signer_roster_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_SIGNER_ROSTER_DIGEST_PROFILE
                ),
            }
        )
    )


def _voluntary_subsidy_revocation_registry_digest(
    *,
    registry_ref: str,
    pool_id: str,
    policy_digest: str,
    offer_revocation_refs: Sequence[str],
) -> str:
    return sha256_text(
        canonical_json(
            {
                "registry_ref": registry_ref,
                "pool_id": pool_id,
                "policy_digest": policy_digest,
                "offer_revocation_refs": list(offer_revocation_refs),
                "revocation_registry_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_REVOCATION_REGISTRY_DIGEST_PROFILE
                ),
            }
        )
    )


def _voluntary_subsidy_audit_authority_digest(
    *,
    audit_authority_ref: str,
    audit_authority_jurisdiction: str,
    signer_roster_digest: str,
    revocation_registry_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "audit_authority_ref": audit_authority_ref,
                "audit_authority_jurisdiction": audit_authority_jurisdiction,
                "signer_roster_digest": signer_roster_digest,
                "revocation_registry_digest": revocation_registry_digest,
                "audit_authority_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUDIT_AUTHORITY_DIGEST_PROFILE
                ),
            }
        )
    )


def _voluntary_subsidy_signature_binding_digest(
    *,
    signature_ref: str,
    signature_digest: str,
    signer_key_ref: str,
    signer_roster_digest: str,
    policy_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "signature_ref": signature_ref,
                "signature_digest": signature_digest,
                "signer_key_ref": signer_key_ref,
                "signer_roster_digest": signer_roster_digest,
                "policy_digest": policy_digest,
                "authority_policy_id": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_POLICY_ID
                ),
            }
        )
    )


def _voluntary_subsidy_authority_binding_digest(
    *,
    signer_roster_digest: str,
    revocation_registry_digest: str,
    audit_authority_digest: str,
    signature_binding_digest: str,
    signer_roster_verifier_receipt_digest: str,
    signer_roster_verifier_quorum_receipt_digest: Optional[str] = None,
    authority_jurisdictions: Sequence[str],
) -> str:
    return sha256_text(
        canonical_json(
            {
                "signer_roster_digest": signer_roster_digest,
                "revocation_registry_digest": revocation_registry_digest,
                "audit_authority_digest": audit_authority_digest,
                "signature_binding_digest": signature_binding_digest,
                "signer_roster_verifier_receipt_digest": (
                    signer_roster_verifier_receipt_digest
                ),
                "signer_roster_verifier_quorum_receipt_digest": (
                    signer_roster_verifier_quorum_receipt_digest
                ),
                "authority_jurisdictions": list(authority_jurisdictions),
                "authority_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_AUTHORITY_DIGEST_PROFILE
                ),
            }
        )
    )


def _subsidy_verifier_challenge_digest(
    *,
    challenge_ref: str,
    signer_roster_digest: str,
    signer_key_ref: str,
    external_funding_policy_digest: str,
    funding_policy_signature_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "challenge_ref": challenge_ref,
                "signer_roster_digest": signer_roster_digest,
                "signer_key_ref": signer_key_ref,
                "external_funding_policy_digest": external_funding_policy_digest,
                "funding_policy_signature_digest": funding_policy_signature_digest,
                "verifier_policy_id": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_POLICY_ID
                ),
            }
        )
    )


def _subsidy_verifier_response_digest(
    *,
    verifier_ref: str,
    verifier_endpoint_ref: str,
    verifier_authority_ref: str,
    verifier_jurisdiction: str,
    verifier_route_ref: str,
    challenge_digest: str,
    signer_roster_ref: str,
    signer_roster_digest: str,
    signer_key_ref: str,
    signer_jurisdiction: str,
    external_funding_policy_digest: str,
    funding_policy_signature_digest: str,
    authority_chain_ref: str,
    trust_root_ref: str,
    trust_root_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "verifier_ref": verifier_ref,
                "verifier_endpoint_ref": verifier_endpoint_ref,
                "verifier_authority_ref": verifier_authority_ref,
                "verifier_jurisdiction": verifier_jurisdiction,
                "verifier_route_ref": verifier_route_ref,
                "challenge_digest": challenge_digest,
                "signer_roster_ref": signer_roster_ref,
                "signer_roster_digest": signer_roster_digest,
                "signer_key_ref": signer_key_ref,
                "signer_jurisdiction": signer_jurisdiction,
                "external_funding_policy_digest": external_funding_policy_digest,
                "funding_policy_signature_digest": funding_policy_signature_digest,
                "authority_chain_ref": authority_chain_ref,
                "trust_root_ref": trust_root_ref,
                "trust_root_digest": trust_root_digest,
                "verifier_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_DIGEST_PROFILE
                ),
            }
        )
    )


def _subsidy_verifier_response_signature_digest(
    *,
    response_digest: str,
    challenge_digest: str,
    verifier_ref: str,
    verifier_authority_ref: str,
    verifier_jurisdiction: str,
    verifier_route_ref: str,
    response_signing_key_ref: str,
    trust_root_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "response_digest": response_digest,
                "challenge_digest": challenge_digest,
                "verifier_ref": verifier_ref,
                "verifier_authority_ref": verifier_authority_ref,
                "verifier_jurisdiction": verifier_jurisdiction,
                "verifier_route_ref": verifier_route_ref,
                "response_signing_key_ref": response_signing_key_ref,
                "trust_root_digest": trust_root_digest,
                "response_envelope_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_ENVELOPE_PROFILE
                ),
                "response_signature_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_VERIFIER_RESPONSE_SIGNATURE_DIGEST_PROFILE
                ),
            }
        )
    )


def _voluntary_subsidy_consent_digest(
    *,
    donor_identity_id: str,
    recipient_identity_id: str,
    offered_jps: int,
    consent_ref: str,
    max_duration_ms: int,
    revocation_ref: str,
    external_funding_policy_digest: str,
) -> str:
    return sha256_text(
        canonical_json(
            {
                "donor_identity_id": donor_identity_id,
                "recipient_identity_id": recipient_identity_id,
                "offered_jps": offered_jps,
                "consent_ref": consent_ref,
                "max_duration_ms": max_duration_ms,
                "revocation_ref": revocation_ref,
                "external_funding_policy_digest": external_funding_policy_digest,
                "consent_digest_profile": (
                    ENERGY_BUDGET_VOLUNTARY_SUBSIDY_CONSENT_DIGEST_PROFILE
                ),
            }
        )
    )
