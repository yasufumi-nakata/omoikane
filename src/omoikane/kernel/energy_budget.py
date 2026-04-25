"""AP-1 protected energy budget floor receipts for the L1 kernel."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional, Union

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..substrate.adapter import ClassicalSiliconAdapter, EnergyFloor


ENERGY_BUDGET_POLICY_ID = "ap1-protected-energy-budget-floor-v1"
ENERGY_BUDGET_DIGEST_PROFILE = "energy-budget-floor-digest-v1"
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
