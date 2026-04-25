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
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_POLICY_ID = (
    "consent-bound-energy-budget-voluntary-subsidy-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_DIGEST_PROFILE = (
    "energy-budget-voluntary-subsidy-digest-v1"
)
ENERGY_BUDGET_VOLUNTARY_SUBSIDY_CONSENT_DIGEST_PROFILE = (
    "participant-consent-bound-subsidy-digest-v1"
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
        )

        rejection_reasons = sorted(
            {
                reason
                for offer in offers
                for reason in offer["rejection_reasons"]
            }
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
            "raw_payload_redacted": receipt.get("raw_funding_payload_stored") is False,
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
