"""AP-1 protected energy budget floor receipts for the L1 kernel."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional, Sequence, Union

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..substrate.adapter import ClassicalSiliconAdapter, EnergyFloor


ENERGY_BUDGET_POLICY_ID = "ap1-protected-energy-budget-floor-v1"
ENERGY_BUDGET_DIGEST_PROFILE = "energy-budget-floor-digest-v1"
ENERGY_BUDGET_POOL_POLICY_ID = "ap1-protected-energy-budget-pool-floor-v1"
ENERGY_BUDGET_POOL_DIGEST_PROFILE = "energy-budget-pool-floor-digest-v1"
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


def _receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _pool_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}
