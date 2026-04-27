"""Self-model tracking and abrupt-change detection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

SELF_MODEL_POLICY_ID = "bounded-self-model-monitor-v1"
SELF_MODEL_ABRUPT_CHANGE_THRESHOLD = 0.35
SELF_MODEL_COMPARISON_COMPONENTS = ("values", "goals", "traits")
SELF_MODEL_CALIBRATION_POLICY_ID = "self-model-advisory-calibration-boundary-v1"
SELF_MODEL_CALIBRATION_DIGEST_PROFILE = "self-model-calibration-digest-v1"
SELF_MODEL_CALIBRATION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_GENERATION_POLICY_ID = "self-model-self-authored-value-generation-v1"
SELF_MODEL_VALUE_GENERATION_DIGEST_PROFILE = "self-model-value-generation-digest-v1"
SELF_MODEL_VALUE_GENERATION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_AUTONOMY_REVIEW_POLICY_ID = "self-model-autonomy-review-witness-boundary-v1"
SELF_MODEL_VALUE_AUTONOMY_REVIEW_DIGEST_PROFILE = "self-model-value-autonomy-review-digest-v1"
SELF_MODEL_VALUE_AUTONOMY_REVIEW_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_ACCEPTANCE_POLICY_ID = "self-model-future-self-acceptance-writeback-v1"
SELF_MODEL_VALUE_ACCEPTANCE_DIGEST_PROFILE = "self-model-value-acceptance-digest-v1"
SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_REASSESSMENT_POLICY_ID = "self-model-future-self-reevaluation-retirement-v1"
SELF_MODEL_VALUE_REASSESSMENT_DIGEST_PROFILE = "self-model-value-reassessment-digest-v1"
SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_TIMELINE_POLICY_ID = "self-model-value-lineage-timeline-v1"
SELF_MODEL_VALUE_TIMELINE_DIGEST_PROFILE = "self-model-value-timeline-digest-v1"
SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_PATHOLOGY_ESCALATION_POLICY_ID = "self-model-pathology-escalation-boundary-v1"
SELF_MODEL_PATHOLOGY_ESCALATION_DIGEST_PROFILE = "self-model-pathology-escalation-digest-v1"
SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID = "self-model-care-trustee-responsibility-handoff-v1"
SELF_MODEL_CARE_TRUSTEE_HANDOFF_DIGEST_PROFILE = "self-model-care-trustee-handoff-digest-v1"
SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES = ("self", "council", "guardian")


@dataclass
class SelfModelSnapshot:
    """Declared self-state at a point in time."""

    identity_id: str
    values: List[str]
    goals: List[str]
    traits: Dict[str, float]
    recorded_at: str = field(default_factory=utc_now_iso)


class SelfModelMonitor:
    """Tracks snapshots and flags abrupt deviations."""

    def __init__(
        self,
        abrupt_change_threshold: float = SELF_MODEL_ABRUPT_CHANGE_THRESHOLD,
    ) -> None:
        self._history: List[SelfModelSnapshot] = []
        self._threshold = abrupt_change_threshold

    def profile(self) -> Dict[str, object]:
        return {
            "policy_id": SELF_MODEL_POLICY_ID,
            "abrupt_change_threshold": round(self._threshold, 2),
            "comparison_components": list(SELF_MODEL_COMPARISON_COMPONENTS),
            "trait_distance_mode": "mean-absolute-delta",
            "change_window": "adjacent-snapshot",
        }

    @staticmethod
    def _set_distance(left: Sequence[str], right: Sequence[str]) -> float:
        left_set = set(left)
        right_set = set(right)
        universe = left_set | right_set
        if not universe:
            return 0.0
        overlap = len(left_set & right_set)
        return 1.0 - (overlap / float(len(universe)))

    @staticmethod
    def _trait_distance(left: Dict[str, float], right: Dict[str, float]) -> float:
        keys = set(left) | set(right)
        if not keys:
            return 0.0
        total = 0.0
        for key in keys:
            total += abs(left.get(key, 0.0) - right.get(key, 0.0))
        return total / float(len(keys))

    def update(self, snapshot: SelfModelSnapshot) -> Dict[str, object]:
        divergence = 0.0
        abrupt = False

        if self._history:
            previous = self._history[-1]
            divergence = (
                self._set_distance(previous.values, snapshot.values)
                + self._set_distance(previous.goals, snapshot.goals)
                + self._trait_distance(previous.traits, snapshot.traits)
            ) / 3.0
            abrupt = divergence >= self._threshold

        self._history.append(snapshot)
        return {
            "policy_id": SELF_MODEL_POLICY_ID,
            "abrupt_change": abrupt,
            "divergence": round(divergence, 4),
            "threshold": round(self._threshold, 2),
            "history_length": len(self._history),
            "snapshot": asdict(snapshot),
        }

    @staticmethod
    def _non_empty_string(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _digest(data: Dict[str, object]) -> str:
        return sha256_text(canonical_json(data))

    def build_advisory_calibration_receipt(
        self,
        observation: Dict[str, object],
        reviewer_evidence_refs: Sequence[str],
        self_consent_ref: str,
        council_resolution_ref: str,
        guardian_redaction_ref: str,
        proposed_adjustments: Sequence[Dict[str, object]],
    ) -> Dict[str, object]:
        """Build a digest-only, advisory calibration receipt.

        The receipt lets external witnesses contribute evidence without granting
        them authority to overwrite self-model values or traits.
        """

        if not reviewer_evidence_refs:
            raise ValueError("reviewer_evidence_refs must not be empty")
        if not proposed_adjustments:
            raise ValueError("proposed_adjustments must not be empty")
        for field_name, value in {
            "self_consent_ref": self_consent_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_redaction_ref": guardian_redaction_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")
        for evidence_ref in reviewer_evidence_refs:
            if not self._non_empty_string(evidence_ref):
                raise ValueError("reviewer_evidence_refs must contain non-empty strings")

        snapshot = observation.get("snapshot")
        if not isinstance(snapshot, dict) or not self._non_empty_string(snapshot.get("identity_id")):
            raise ValueError("observation must contain a self-model snapshot")

        normalized_adjustments: List[Dict[str, object]] = []
        for adjustment in proposed_adjustments:
            trait = adjustment.get("trait")
            direction = adjustment.get("direction")
            delta = adjustment.get("delta")
            if not self._non_empty_string(trait):
                raise ValueError("proposed_adjustments must name a trait")
            if direction not in {"increase", "decrease", "observe-only"}:
                raise ValueError("proposed_adjustments direction is invalid")
            if not isinstance(delta, (int, float)) or not 0.0 <= float(delta) <= 1.0:
                raise ValueError("proposed_adjustments delta must be between 0.0 and 1.0")
            normalized_adjustments.append(
                {
                    "trait": str(trait),
                    "direction": str(direction),
                    "delta": round(float(delta), 4),
                    "status": "requires-self-acceptance",
                }
            )

        observation_digest = self._digest(
            {
                "policy_id": observation.get("policy_id"),
                "abrupt_change": observation.get("abrupt_change"),
                "divergence": observation.get("divergence"),
                "threshold": observation.get("threshold"),
                "history_length": observation.get("history_length"),
                "identity_id": snapshot.get("identity_id"),
                "recorded_at": snapshot.get("recorded_at"),
            }
        )
        evidence_digest_set = [sha256_text(ref) for ref in reviewer_evidence_refs]
        gate_payload = {
            "self_consent_ref": self_consent_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_redaction_ref": guardian_redaction_ref,
            "required_roles": list(SELF_MODEL_CALIBRATION_REQUIRED_ROLES),
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_calibration_receipt",
            "policy_id": SELF_MODEL_CALIBRATION_POLICY_ID,
            "digest_profile": SELF_MODEL_CALIBRATION_DIGEST_PROFILE,
            "calibration_id": new_id("self-model-calibration"),
            "identity_id": str(snapshot["identity_id"]),
            "source_observation_digest": observation_digest,
            "reviewer_evidence_refs": list(reviewer_evidence_refs),
            "reviewer_evidence_digest_set": evidence_digest_set,
            "reviewer_evidence_set_digest": sha256_text("|".join(evidence_digest_set)),
            "self_consent_ref": self_consent_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_redaction_ref": guardian_redaction_ref,
            "required_roles": list(SELF_MODEL_CALIBRATION_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "correction_mode": "advisory-only",
            "recommendation": "council-review-no-forced-writeback",
            "proposed_adjustments": normalized_adjustments,
            "external_truth_claim_allowed": False,
            "forced_correction_allowed": False,
            "accepted_for_writeback": False,
            "raw_external_testimony_stored": False,
            "raw_trait_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_advisory_calibration_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_calibration_receipt":
            errors.append("kind must equal self_model_calibration_receipt")
        if receipt.get("policy_id") != SELF_MODEL_CALIBRATION_POLICY_ID:
            errors.append("policy_id must equal self-model advisory calibration policy")
        if receipt.get("digest_profile") != SELF_MODEL_CALIBRATION_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model calibration digest profile")

        evidence_refs = receipt.get("reviewer_evidence_refs")
        evidence_digests = receipt.get("reviewer_evidence_digest_set")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            errors.append("reviewer_evidence_refs must be non-empty")
            evidence_refs = []
        if not isinstance(evidence_digests, list) or len(evidence_digests) != len(evidence_refs):
            errors.append("reviewer_evidence_digest_set must match reviewer evidence refs")
            evidence_digests = []
        elif [sha256_text(str(ref)) for ref in evidence_refs] != evidence_digests:
            errors.append("reviewer evidence digest set must match reviewer evidence refs")
        if isinstance(evidence_digests, list) and evidence_digests:
            expected_evidence_set_digest = sha256_text("|".join(str(item) for item in evidence_digests))
            if receipt.get("reviewer_evidence_set_digest") != expected_evidence_set_digest:
                errors.append("reviewer_evidence_set_digest must match digest set")

        gate_payload = {
            "self_consent_ref": receipt.get("self_consent_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_redaction_ref": receipt.get("guardian_redaction_ref"),
            "required_roles": list(SELF_MODEL_CALIBRATION_REQUIRED_ROLES),
        }
        for field_name in ("self_consent_ref", "council_resolution_ref", "guardian_redaction_ref"):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_CALIBRATION_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind self consent, council, and guardian refs")

        adjustments = receipt.get("proposed_adjustments")
        if not isinstance(adjustments, list) or not adjustments:
            errors.append("proposed_adjustments must be non-empty")
            adjustments = []
        for adjustment in adjustments:
            if not isinstance(adjustment, dict):
                errors.append("proposed_adjustments entries must be objects")
                continue
            if adjustment.get("status") != "requires-self-acceptance":
                errors.append("proposed adjustments must require self acceptance")

        if receipt.get("correction_mode") != "advisory-only":
            errors.append("correction_mode must remain advisory-only")
        if receipt.get("recommendation") != "council-review-no-forced-writeback":
            errors.append("recommendation must preserve council review without forced writeback")
        for field_name in (
            "external_truth_claim_allowed",
            "forced_correction_allowed",
            "accepted_for_writeback",
            "raw_external_testimony_stored",
            "raw_trait_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "advisory_only": receipt.get("correction_mode") == "advisory-only",
            "self_consent_bound": self._non_empty_string(receipt.get("self_consent_ref")),
            "council_resolution_bound": self._non_empty_string(receipt.get("council_resolution_ref")),
            "guardian_redaction_bound": self._non_empty_string(receipt.get("guardian_redaction_ref")),
            "raw_external_testimony_stored": receipt.get("raw_external_testimony_stored"),
            "forced_correction_allowed": receipt.get("forced_correction_allowed"),
        }

    def build_value_generation_receipt(
        self,
        observation: Dict[str, object],
        candidate_value_refs: Sequence[str],
        continuity_context_refs: Sequence[str],
        self_authorship_ref: str,
        self_consent_ref: str,
        council_review_ref: str,
        guardian_boundary_ref: str,
    ) -> Dict[str, object]:
        """Build a receipt that preserves self-authored value generation freedom.

        The receipt makes newly generated value candidates auditable without
        letting external reviewers veto them or write them into the SelfModel.
        """

        snapshot = observation.get("snapshot")
        if not isinstance(snapshot, dict) or not self._non_empty_string(snapshot.get("identity_id")):
            raise ValueError("observation must contain a self-model snapshot")
        if not candidate_value_refs:
            raise ValueError("candidate_value_refs must not be empty")
        if not continuity_context_refs:
            raise ValueError("continuity_context_refs must not be empty")
        for ref in candidate_value_refs:
            if not self._non_empty_string(ref):
                raise ValueError("candidate_value_refs must contain non-empty strings")
        for ref in continuity_context_refs:
            if not self._non_empty_string(ref):
                raise ValueError("continuity_context_refs must contain non-empty strings")
        for field_name, value in {
            "self_authorship_ref": self_authorship_ref,
            "self_consent_ref": self_consent_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        observation_digest = self._digest(
            {
                "policy_id": observation.get("policy_id"),
                "abrupt_change": observation.get("abrupt_change"),
                "divergence": observation.get("divergence"),
                "threshold": observation.get("threshold"),
                "history_length": observation.get("history_length"),
                "identity_id": snapshot.get("identity_id"),
                "recorded_at": snapshot.get("recorded_at"),
            }
        )
        candidate_value_digest_set = [sha256_text(ref) for ref in candidate_value_refs]
        continuity_context_digest_set = [sha256_text(ref) for ref in continuity_context_refs]
        gate_payload = {
            "self_authorship_ref": self_authorship_ref,
            "self_consent_ref": self_consent_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_GENERATION_REQUIRED_ROLES),
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_generation_receipt",
            "policy_id": SELF_MODEL_VALUE_GENERATION_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_GENERATION_DIGEST_PROFILE,
            "generation_id": new_id("self-model-value-generation"),
            "identity_id": str(snapshot["identity_id"]),
            "source_observation_digest": observation_digest,
            "candidate_value_refs": list(candidate_value_refs),
            "candidate_value_digest_set": candidate_value_digest_set,
            "candidate_value_set_digest": sha256_text("|".join(candidate_value_digest_set)),
            "continuity_context_refs": list(continuity_context_refs),
            "continuity_context_digest_set": continuity_context_digest_set,
            "continuity_context_set_digest": sha256_text("|".join(continuity_context_digest_set)),
            "self_authorship_ref": self_authorship_ref,
            "self_consent_ref": self_consent_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_GENERATION_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "generation_mode": "self-authored-bounded-experiment",
            "integration_status": "proposed-not-written-back",
            "requires_future_self_acceptance": True,
            "autonomy_preserved": True,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "forced_stability_lock_allowed": False,
            "accepted_for_writeback": False,
            "raw_value_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_generation_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_generation_receipt":
            errors.append("kind must equal self_model_value_generation_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_GENERATION_POLICY_ID:
            errors.append("policy_id must equal self-model value generation policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_GENERATION_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model value generation digest profile")

        candidate_refs = receipt.get("candidate_value_refs")
        candidate_digests = receipt.get("candidate_value_digest_set")
        if not isinstance(candidate_refs, list) or not candidate_refs:
            errors.append("candidate_value_refs must be non-empty")
            candidate_refs = []
        if not isinstance(candidate_digests, list) or len(candidate_digests) != len(candidate_refs):
            errors.append("candidate_value_digest_set must match candidate value refs")
            candidate_digests = []
        elif [sha256_text(str(ref)) for ref in candidate_refs] != candidate_digests:
            errors.append("candidate value digest set must match candidate value refs")
        if isinstance(candidate_digests, list) and candidate_digests:
            expected_value_set_digest = sha256_text("|".join(str(item) for item in candidate_digests))
            if receipt.get("candidate_value_set_digest") != expected_value_set_digest:
                errors.append("candidate_value_set_digest must match digest set")

        context_refs = receipt.get("continuity_context_refs")
        context_digests = receipt.get("continuity_context_digest_set")
        if not isinstance(context_refs, list) or not context_refs:
            errors.append("continuity_context_refs must be non-empty")
            context_refs = []
        if not isinstance(context_digests, list) or len(context_digests) != len(context_refs):
            errors.append("continuity_context_digest_set must match continuity context refs")
            context_digests = []
        elif [sha256_text(str(ref)) for ref in context_refs] != context_digests:
            errors.append("continuity context digest set must match continuity context refs")
        if isinstance(context_digests, list) and context_digests:
            expected_context_set_digest = sha256_text("|".join(str(item) for item in context_digests))
            if receipt.get("continuity_context_set_digest") != expected_context_set_digest:
                errors.append("continuity_context_set_digest must match digest set")

        gate_payload = {
            "self_authorship_ref": receipt.get("self_authorship_ref"),
            "self_consent_ref": receipt.get("self_consent_ref"),
            "council_review_ref": receipt.get("council_review_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_VALUE_GENERATION_REQUIRED_ROLES),
        }
        for field_name in (
            "self_authorship_ref",
            "self_consent_ref",
            "council_review_ref",
            "guardian_boundary_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_GENERATION_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind authorship, consent, council, and guardian refs")

        if receipt.get("generation_mode") != "self-authored-bounded-experiment":
            errors.append("generation_mode must remain self-authored bounded experiment")
        if receipt.get("integration_status") != "proposed-not-written-back":
            errors.append("integration_status must remain proposed-not-written-back")
        for field_name in ("requires_future_self_acceptance", "autonomy_preserved"):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "forced_stability_lock_allowed",
            "accepted_for_writeback",
            "raw_value_payload_stored",
            "raw_continuity_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "self_authored": receipt.get("generation_mode") == "self-authored-bounded-experiment",
            "autonomy_preserved": receipt.get("autonomy_preserved"),
            "requires_future_self_acceptance": receipt.get("requires_future_self_acceptance"),
            "external_veto_allowed": receipt.get("external_veto_allowed"),
            "accepted_for_writeback": receipt.get("accepted_for_writeback"),
            "raw_value_payload_stored": receipt.get("raw_value_payload_stored"),
        }

    def build_value_autonomy_review_receipt(
        self,
        generation_receipt: Dict[str, object],
        witness_evidence_refs: Sequence[str],
        self_authorship_continuation_ref: str,
        council_review_ref: str,
        guardian_boundary_ref: str,
    ) -> Dict[str, object]:
        """Bind witness/Council review without granting veto over self-authored values."""

        generation_validation = self.validate_value_generation_receipt(generation_receipt)
        if not generation_validation["ok"]:
            raise ValueError("generation_receipt must validate before autonomy review")
        candidate_value_refs = generation_receipt.get("candidate_value_refs")
        source_candidate_value_digest_set = generation_receipt.get(
            "candidate_value_digest_set"
        )
        if not isinstance(candidate_value_refs, list) or not candidate_value_refs:
            raise ValueError("generation_receipt must contain candidate value refs")
        if (
            not isinstance(source_candidate_value_digest_set, list)
            or not source_candidate_value_digest_set
        ):
            raise ValueError("generation_receipt must contain candidate value digests")
        if not witness_evidence_refs:
            raise ValueError("witness_evidence_refs must not be empty")
        for ref in witness_evidence_refs:
            if not self._non_empty_string(ref):
                raise ValueError("witness_evidence_refs must contain non-empty strings")
        for field_name, value in {
            "self_authorship_continuation_ref": self_authorship_continuation_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        candidate_value_digest_set = [
            sha256_text(str(ref)) for ref in candidate_value_refs
        ]
        if candidate_value_digest_set != [
            str(item) for item in source_candidate_value_digest_set
        ]:
            raise ValueError("candidate digests must match generation receipt")
        witness_evidence_digest_set = [
            sha256_text(str(ref)) for ref in witness_evidence_refs
        ]
        candidate_value_set_digest = sha256_text("|".join(candidate_value_digest_set))
        witness_evidence_set_digest = sha256_text("|".join(witness_evidence_digest_set))
        gate_payload = {
            "source_generation_receipt_digest": generation_receipt.get("receipt_digest"),
            "self_authorship_continuation_ref": self_authorship_continuation_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_AUTONOMY_REVIEW_REQUIRED_ROLES),
        }
        review_payload = {
            "source_generation_receipt_digest": generation_receipt.get("receipt_digest"),
            "candidate_value_set_digest": candidate_value_set_digest,
            "witness_evidence_set_digest": witness_evidence_set_digest,
            "self_authorship_continuation_ref": self_authorship_continuation_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "review_scope": "witness-context-boundary-only",
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_autonomy_review_receipt",
            "policy_id": SELF_MODEL_VALUE_AUTONOMY_REVIEW_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_AUTONOMY_REVIEW_DIGEST_PROFILE,
            "review_id": new_id("self-model-value-autonomy-review"),
            "identity_id": str(generation_receipt["identity_id"]),
            "source_generation_id": str(generation_receipt["generation_id"]),
            "source_generation_policy_id": str(generation_receipt["policy_id"]),
            "source_generation_receipt_digest": str(generation_receipt["receipt_digest"]),
            "source_candidate_value_digest_set": [
                str(item) for item in source_candidate_value_digest_set
            ],
            "candidate_value_refs": [str(ref) for ref in candidate_value_refs],
            "candidate_value_digest_set": candidate_value_digest_set,
            "candidate_value_set_digest": candidate_value_set_digest,
            "witness_evidence_refs": list(witness_evidence_refs),
            "witness_evidence_digest_set": witness_evidence_digest_set,
            "witness_evidence_set_digest": witness_evidence_set_digest,
            "self_authorship_continuation_ref": self_authorship_continuation_ref,
            "council_review_ref": council_review_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_AUTONOMY_REVIEW_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "review_commit_digest": self._digest(review_payload),
            "review_mode": "advisory-witness-council-boundary-review",
            "review_scope": "witness-context-boundary-only",
            "witness_authority": "digest-only-context",
            "council_review_authority": "advisory-boundary-only",
            "guardian_authority": "boundary-attestation-no-lock",
            "candidate_set_unchanged": True,
            "self_authorship_preserved": True,
            "autonomy_preserved": True,
            "future_self_acceptance_remains_required": True,
            "accepted_for_writeback": False,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "council_override_allowed": False,
            "guardian_forced_lock_allowed": False,
            "forced_stability_lock_allowed": False,
            "candidate_rewrite_allowed": False,
            "raw_witness_payload_stored": False,
            "raw_value_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_autonomy_review_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_autonomy_review_receipt":
            errors.append("kind must equal self_model_value_autonomy_review_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_AUTONOMY_REVIEW_POLICY_ID:
            errors.append("policy_id must equal self-model value autonomy review policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_AUTONOMY_REVIEW_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model value autonomy review digest profile")
        if receipt.get("source_generation_policy_id") != SELF_MODEL_VALUE_GENERATION_POLICY_ID:
            errors.append("source_generation_policy_id must bind the value generation policy")

        source_candidate_digests = receipt.get("source_candidate_value_digest_set")
        candidate_refs = receipt.get("candidate_value_refs")
        candidate_digests = receipt.get("candidate_value_digest_set")
        if not isinstance(source_candidate_digests, list) or not source_candidate_digests:
            errors.append("source_candidate_value_digest_set must be non-empty")
            source_candidate_digests = []
        if not isinstance(candidate_refs, list) or not candidate_refs:
            errors.append("candidate_value_refs must be non-empty")
            candidate_refs = []
        if not isinstance(candidate_digests, list) or len(candidate_digests) != len(candidate_refs):
            errors.append("candidate_value_digest_set must match candidate value refs")
            candidate_digests = []
        elif [sha256_text(str(ref)) for ref in candidate_refs] != candidate_digests:
            errors.append("candidate value digest set must match candidate value refs")
        if [str(item) for item in candidate_digests] != [
            str(item) for item in source_candidate_digests
        ]:
            errors.append("candidate_value_digest_set must preserve source candidate values")
        if isinstance(candidate_digests, list) and candidate_digests:
            expected_value_set_digest = sha256_text("|".join(str(item) for item in candidate_digests))
            if receipt.get("candidate_value_set_digest") != expected_value_set_digest:
                errors.append("candidate_value_set_digest must match digest set")

        witness_refs = receipt.get("witness_evidence_refs")
        witness_digests = receipt.get("witness_evidence_digest_set")
        if not isinstance(witness_refs, list) or not witness_refs:
            errors.append("witness_evidence_refs must be non-empty")
            witness_refs = []
        if not isinstance(witness_digests, list) or len(witness_digests) != len(witness_refs):
            errors.append("witness_evidence_digest_set must match witness evidence refs")
            witness_digests = []
        elif [sha256_text(str(ref)) for ref in witness_refs] != witness_digests:
            errors.append("witness evidence digest set must match witness evidence refs")
        if isinstance(witness_digests, list) and witness_digests:
            expected_witness_set_digest = sha256_text("|".join(str(item) for item in witness_digests))
            if receipt.get("witness_evidence_set_digest") != expected_witness_set_digest:
                errors.append("witness_evidence_set_digest must match digest set")

        gate_payload = {
            "source_generation_receipt_digest": receipt.get("source_generation_receipt_digest"),
            "self_authorship_continuation_ref": receipt.get("self_authorship_continuation_ref"),
            "council_review_ref": receipt.get("council_review_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_VALUE_AUTONOMY_REVIEW_REQUIRED_ROLES),
        }
        for field_name in (
            "source_generation_receipt_digest",
            "self_authorship_continuation_ref",
            "council_review_ref",
            "guardian_boundary_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_AUTONOMY_REVIEW_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind generation, self, council, and guardian refs")

        review_payload = {
            "source_generation_receipt_digest": receipt.get("source_generation_receipt_digest"),
            "candidate_value_set_digest": receipt.get("candidate_value_set_digest"),
            "witness_evidence_set_digest": receipt.get("witness_evidence_set_digest"),
            "self_authorship_continuation_ref": receipt.get("self_authorship_continuation_ref"),
            "council_review_ref": receipt.get("council_review_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "review_scope": "witness-context-boundary-only",
        }
        if receipt.get("review_commit_digest") != self._digest(review_payload):
            errors.append("review_commit_digest must bind source, candidate, witness, and boundary refs")

        expected_strings = {
            "review_mode": "advisory-witness-council-boundary-review",
            "review_scope": "witness-context-boundary-only",
            "witness_authority": "digest-only-context",
            "council_review_authority": "advisory-boundary-only",
            "guardian_authority": "boundary-attestation-no-lock",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        for field_name in (
            "candidate_set_unchanged",
            "self_authorship_preserved",
            "autonomy_preserved",
            "future_self_acceptance_remains_required",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "accepted_for_writeback",
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "council_override_allowed",
            "guardian_forced_lock_allowed",
            "forced_stability_lock_allowed",
            "candidate_rewrite_allowed",
            "raw_witness_payload_stored",
            "raw_value_payload_stored",
            "raw_continuity_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "candidate_set_unchanged": receipt.get("candidate_set_unchanged"),
            "self_authorship_preserved": receipt.get("self_authorship_preserved"),
            "autonomy_preserved": receipt.get("autonomy_preserved"),
            "future_self_acceptance_remains_required": receipt.get(
                "future_self_acceptance_remains_required"
            ),
            "external_veto_allowed": receipt.get("external_veto_allowed"),
            "council_override_allowed": receipt.get("council_override_allowed"),
            "candidate_rewrite_allowed": receipt.get("candidate_rewrite_allowed"),
            "raw_witness_payload_stored": receipt.get("raw_witness_payload_stored"),
            "review_commit_digest_bound": self._non_empty_string(
                receipt.get("review_commit_digest")
            ),
        }

    def build_value_acceptance_receipt(
        self,
        generation_receipt: Dict[str, object],
        accepted_value_refs: Sequence[str],
        continuity_recheck_refs: Sequence[str],
        future_self_acceptance_ref: str,
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        writeback_ref: str,
        post_acceptance_snapshot_ref: str,
    ) -> Dict[str, object]:
        """Bind future-self acceptance before bounded value writeback."""

        generation_validation = self.validate_value_generation_receipt(generation_receipt)
        if not generation_validation["ok"]:
            raise ValueError("generation_receipt must validate before acceptance")
        if generation_receipt.get("requires_future_self_acceptance") is not True:
            raise ValueError("generation_receipt must require future self acceptance")
        if generation_receipt.get("accepted_for_writeback") is not False:
            raise ValueError("generation_receipt must not already be written back")
        candidate_value_refs = generation_receipt.get("candidate_value_refs")
        if not isinstance(candidate_value_refs, list) or not candidate_value_refs:
            raise ValueError("generation_receipt must contain candidate value refs")
        if not accepted_value_refs:
            raise ValueError("accepted_value_refs must not be empty")
        if not continuity_recheck_refs:
            raise ValueError("continuity_recheck_refs must not be empty")

        candidate_ref_set = {str(ref) for ref in candidate_value_refs}
        for ref in accepted_value_refs:
            if not self._non_empty_string(ref):
                raise ValueError("accepted_value_refs must contain non-empty strings")
            if str(ref) not in candidate_ref_set:
                raise ValueError("accepted_value_refs must be a subset of candidate_value_refs")
        for ref in continuity_recheck_refs:
            if not self._non_empty_string(ref):
                raise ValueError("continuity_recheck_refs must contain non-empty strings")
        for field_name, value in {
            "future_self_acceptance_ref": future_self_acceptance_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "writeback_ref": writeback_ref,
            "post_acceptance_snapshot_ref": post_acceptance_snapshot_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        source_candidate_value_digest_set = [
            sha256_text(str(ref)) for ref in candidate_value_refs
        ]
        accepted_value_digest_set = [sha256_text(str(ref)) for ref in accepted_value_refs]
        continuity_recheck_digest_set = [
            sha256_text(str(ref)) for ref in continuity_recheck_refs
        ]
        gate_payload = {
            "future_self_acceptance_ref": future_self_acceptance_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES),
        }
        writeback_payload = {
            "source_generation_receipt_digest": generation_receipt.get("receipt_digest"),
            "accepted_value_set_digest": sha256_text("|".join(accepted_value_digest_set)),
            "writeback_ref": writeback_ref,
            "post_acceptance_snapshot_ref": post_acceptance_snapshot_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_acceptance_receipt",
            "policy_id": SELF_MODEL_VALUE_ACCEPTANCE_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_ACCEPTANCE_DIGEST_PROFILE,
            "acceptance_id": new_id("self-model-value-acceptance"),
            "identity_id": str(generation_receipt["identity_id"]),
            "source_generation_id": str(generation_receipt["generation_id"]),
            "source_generation_policy_id": str(generation_receipt["policy_id"]),
            "source_generation_receipt_digest": str(generation_receipt["receipt_digest"]),
            "source_candidate_value_digest_set": source_candidate_value_digest_set,
            "accepted_value_refs": list(accepted_value_refs),
            "accepted_value_digest_set": accepted_value_digest_set,
            "accepted_value_set_digest": sha256_text("|".join(accepted_value_digest_set)),
            "continuity_recheck_refs": list(continuity_recheck_refs),
            "continuity_recheck_digest_set": continuity_recheck_digest_set,
            "continuity_recheck_set_digest": sha256_text("|".join(continuity_recheck_digest_set)),
            "future_self_acceptance_ref": future_self_acceptance_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "writeback_ref": writeback_ref,
            "post_acceptance_snapshot_ref": post_acceptance_snapshot_ref,
            "writeback_commit_digest": self._digest(writeback_payload),
            "acceptance_mode": "future-self-accepted-bounded-writeback",
            "integration_status": "accepted-for-bounded-writeback",
            "future_self_acceptance_satisfied": True,
            "generation_receipt_required_future_self_acceptance": True,
            "autonomy_preserved": True,
            "boundary_only_review": True,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "forced_stability_lock_allowed": False,
            "accepted_for_writeback": True,
            "raw_value_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_acceptance_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_acceptance_receipt":
            errors.append("kind must equal self_model_value_acceptance_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_ACCEPTANCE_POLICY_ID:
            errors.append("policy_id must equal self-model value acceptance policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_ACCEPTANCE_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model value acceptance digest profile")
        if receipt.get("source_generation_policy_id") != SELF_MODEL_VALUE_GENERATION_POLICY_ID:
            errors.append("source_generation_policy_id must bind the value generation policy")

        source_candidate_digests = receipt.get("source_candidate_value_digest_set")
        if not isinstance(source_candidate_digests, list) or not source_candidate_digests:
            errors.append("source_candidate_value_digest_set must be non-empty")
            source_candidate_digests = []

        accepted_refs = receipt.get("accepted_value_refs")
        accepted_digests = receipt.get("accepted_value_digest_set")
        if not isinstance(accepted_refs, list) or not accepted_refs:
            errors.append("accepted_value_refs must be non-empty")
            accepted_refs = []
        if not isinstance(accepted_digests, list) or len(accepted_digests) != len(accepted_refs):
            errors.append("accepted_value_digest_set must match accepted value refs")
            accepted_digests = []
        elif [sha256_text(str(ref)) for ref in accepted_refs] != accepted_digests:
            errors.append("accepted value digest set must match accepted value refs")
        if isinstance(accepted_digests, list) and accepted_digests:
            expected_value_set_digest = sha256_text("|".join(str(item) for item in accepted_digests))
            if receipt.get("accepted_value_set_digest") != expected_value_set_digest:
                errors.append("accepted_value_set_digest must match digest set")
            if not set(str(item) for item in accepted_digests).issubset(
                set(str(item) for item in source_candidate_digests)
            ):
                errors.append("accepted values must be a subset of source candidate values")

        recheck_refs = receipt.get("continuity_recheck_refs")
        recheck_digests = receipt.get("continuity_recheck_digest_set")
        if not isinstance(recheck_refs, list) or not recheck_refs:
            errors.append("continuity_recheck_refs must be non-empty")
            recheck_refs = []
        if not isinstance(recheck_digests, list) or len(recheck_digests) != len(recheck_refs):
            errors.append("continuity_recheck_digest_set must match continuity recheck refs")
            recheck_digests = []
        elif [sha256_text(str(ref)) for ref in recheck_refs] != recheck_digests:
            errors.append("continuity recheck digest set must match continuity recheck refs")
        if isinstance(recheck_digests, list) and recheck_digests:
            expected_recheck_set_digest = sha256_text("|".join(str(item) for item in recheck_digests))
            if receipt.get("continuity_recheck_set_digest") != expected_recheck_set_digest:
                errors.append("continuity_recheck_set_digest must match digest set")

        gate_payload = {
            "future_self_acceptance_ref": receipt.get("future_self_acceptance_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES),
        }
        for field_name in (
            "future_self_acceptance_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "writeback_ref",
            "post_acceptance_snapshot_ref",
            "source_generation_receipt_digest",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind future self acceptance, council, and guardian refs")

        writeback_payload = {
            "source_generation_receipt_digest": receipt.get("source_generation_receipt_digest"),
            "accepted_value_set_digest": receipt.get("accepted_value_set_digest"),
            "writeback_ref": receipt.get("writeback_ref"),
            "post_acceptance_snapshot_ref": receipt.get("post_acceptance_snapshot_ref"),
        }
        if receipt.get("writeback_commit_digest") != self._digest(writeback_payload):
            errors.append("writeback_commit_digest must bind source generation, accepted values, and writeback refs")

        if receipt.get("acceptance_mode") != "future-self-accepted-bounded-writeback":
            errors.append("acceptance_mode must remain future-self accepted bounded writeback")
        if receipt.get("integration_status") != "accepted-for-bounded-writeback":
            errors.append("integration_status must remain accepted-for-bounded-writeback")
        for field_name in (
            "future_self_acceptance_satisfied",
            "generation_receipt_required_future_self_acceptance",
            "autonomy_preserved",
            "boundary_only_review",
            "accepted_for_writeback",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "forced_stability_lock_allowed",
            "raw_value_payload_stored",
            "raw_continuity_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "future_self_acceptance_satisfied": receipt.get("future_self_acceptance_satisfied"),
            "accepted_for_writeback": receipt.get("accepted_for_writeback"),
            "autonomy_preserved": receipt.get("autonomy_preserved"),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "external_veto_allowed": receipt.get("external_veto_allowed"),
            "raw_value_payload_stored": receipt.get("raw_value_payload_stored"),
            "writeback_digest_bound": self._non_empty_string(
                receipt.get("writeback_commit_digest")
            ),
        }

    def build_value_reassessment_receipt(
        self,
        acceptance_receipt: Dict[str, object],
        retired_value_refs: Sequence[str],
        continuity_recheck_refs: Sequence[str],
        future_self_reevaluation_ref: str,
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        retirement_writeback_ref: str,
        post_reassessment_snapshot_ref: str,
        archival_snapshot_ref: str,
    ) -> Dict[str, object]:
        """Retire accepted values from active writeback without deleting history."""

        acceptance_validation = self.validate_value_acceptance_receipt(acceptance_receipt)
        if not acceptance_validation["ok"]:
            raise ValueError("acceptance_receipt must validate before reassessment")
        if acceptance_receipt.get("accepted_for_writeback") is not True:
            raise ValueError("acceptance_receipt must already be accepted for writeback")
        accepted_value_refs = acceptance_receipt.get("accepted_value_refs")
        if not isinstance(accepted_value_refs, list) or not accepted_value_refs:
            raise ValueError("acceptance_receipt must contain accepted value refs")
        if not retired_value_refs:
            raise ValueError("retired_value_refs must not be empty")
        if not continuity_recheck_refs:
            raise ValueError("continuity_recheck_refs must not be empty")

        accepted_ref_set = {str(ref) for ref in accepted_value_refs}
        for ref in retired_value_refs:
            if not self._non_empty_string(ref):
                raise ValueError("retired_value_refs must contain non-empty strings")
            if str(ref) not in accepted_ref_set:
                raise ValueError("retired_value_refs must be a subset of accepted_value_refs")
        for ref in continuity_recheck_refs:
            if not self._non_empty_string(ref):
                raise ValueError("continuity_recheck_refs must contain non-empty strings")
        for field_name, value in {
            "future_self_reevaluation_ref": future_self_reevaluation_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "retirement_writeback_ref": retirement_writeback_ref,
            "post_reassessment_snapshot_ref": post_reassessment_snapshot_ref,
            "archival_snapshot_ref": archival_snapshot_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        source_accepted_value_digest_set = [
            sha256_text(str(ref)) for ref in accepted_value_refs
        ]
        retired_value_digest_set = [sha256_text(str(ref)) for ref in retired_value_refs]
        continuity_recheck_digest_set = [
            sha256_text(str(ref)) for ref in continuity_recheck_refs
        ]
        gate_payload = {
            "future_self_reevaluation_ref": future_self_reevaluation_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES),
        }
        retirement_payload = {
            "source_acceptance_receipt_digest": acceptance_receipt.get("receipt_digest"),
            "retired_value_set_digest": sha256_text("|".join(retired_value_digest_set)),
            "retirement_writeback_ref": retirement_writeback_ref,
            "post_reassessment_snapshot_ref": post_reassessment_snapshot_ref,
            "archival_snapshot_ref": archival_snapshot_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_reassessment_receipt",
            "policy_id": SELF_MODEL_VALUE_REASSESSMENT_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_REASSESSMENT_DIGEST_PROFILE,
            "reassessment_id": new_id("self-model-value-reassessment"),
            "identity_id": str(acceptance_receipt["identity_id"]),
            "source_acceptance_id": str(acceptance_receipt["acceptance_id"]),
            "source_acceptance_policy_id": str(acceptance_receipt["policy_id"]),
            "source_acceptance_receipt_digest": str(acceptance_receipt["receipt_digest"]),
            "source_accepted_value_digest_set": source_accepted_value_digest_set,
            "retired_value_refs": list(retired_value_refs),
            "retired_value_digest_set": retired_value_digest_set,
            "retired_value_set_digest": sha256_text("|".join(retired_value_digest_set)),
            "continuity_recheck_refs": list(continuity_recheck_refs),
            "continuity_recheck_digest_set": continuity_recheck_digest_set,
            "continuity_recheck_set_digest": sha256_text("|".join(continuity_recheck_digest_set)),
            "future_self_reevaluation_ref": future_self_reevaluation_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "retirement_writeback_ref": retirement_writeback_ref,
            "post_reassessment_snapshot_ref": post_reassessment_snapshot_ref,
            "archival_snapshot_ref": archival_snapshot_ref,
            "retirement_commit_digest": self._digest(retirement_payload),
            "reassessment_mode": "future-self-reevaluated-bounded-retirement",
            "integration_status": "retired-from-active-writeback-archive-retained",
            "future_self_reevaluation_satisfied": True,
            "source_acceptance_required_future_self_acceptance": True,
            "autonomy_preserved": True,
            "boundary_only_review": True,
            "historical_value_archived": True,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "forced_stability_lock_allowed": False,
            "active_writeback_retired": True,
            "raw_value_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_reassessment_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_reassessment_receipt":
            errors.append("kind must equal self_model_value_reassessment_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_REASSESSMENT_POLICY_ID:
            errors.append("policy_id must equal self-model value reassessment policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_REASSESSMENT_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model value reassessment digest profile")
        if receipt.get("source_acceptance_policy_id") != SELF_MODEL_VALUE_ACCEPTANCE_POLICY_ID:
            errors.append("source_acceptance_policy_id must bind the value acceptance policy")

        source_accepted_digests = receipt.get("source_accepted_value_digest_set")
        if not isinstance(source_accepted_digests, list) or not source_accepted_digests:
            errors.append("source_accepted_value_digest_set must be non-empty")
            source_accepted_digests = []

        retired_refs = receipt.get("retired_value_refs")
        retired_digests = receipt.get("retired_value_digest_set")
        if not isinstance(retired_refs, list) or not retired_refs:
            errors.append("retired_value_refs must be non-empty")
            retired_refs = []
        if not isinstance(retired_digests, list) or len(retired_digests) != len(retired_refs):
            errors.append("retired_value_digest_set must match retired value refs")
            retired_digests = []
        elif [sha256_text(str(ref)) for ref in retired_refs] != retired_digests:
            errors.append("retired value digest set must match retired value refs")
        if isinstance(retired_digests, list) and retired_digests:
            expected_value_set_digest = sha256_text("|".join(str(item) for item in retired_digests))
            if receipt.get("retired_value_set_digest") != expected_value_set_digest:
                errors.append("retired_value_set_digest must match digest set")
            if not set(str(item) for item in retired_digests).issubset(
                set(str(item) for item in source_accepted_digests)
            ):
                errors.append("retired values must be a subset of source accepted values")

        recheck_refs = receipt.get("continuity_recheck_refs")
        recheck_digests = receipt.get("continuity_recheck_digest_set")
        if not isinstance(recheck_refs, list) or not recheck_refs:
            errors.append("continuity_recheck_refs must be non-empty")
            recheck_refs = []
        if not isinstance(recheck_digests, list) or len(recheck_digests) != len(recheck_refs):
            errors.append("continuity_recheck_digest_set must match continuity recheck refs")
            recheck_digests = []
        elif [sha256_text(str(ref)) for ref in recheck_refs] != recheck_digests:
            errors.append("continuity recheck digest set must match continuity recheck refs")
        if isinstance(recheck_digests, list) and recheck_digests:
            expected_recheck_set_digest = sha256_text("|".join(str(item) for item in recheck_digests))
            if receipt.get("continuity_recheck_set_digest") != expected_recheck_set_digest:
                errors.append("continuity_recheck_set_digest must match digest set")

        gate_payload = {
            "future_self_reevaluation_ref": receipt.get("future_self_reevaluation_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES),
        }
        for field_name in (
            "future_self_reevaluation_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "retirement_writeback_ref",
            "post_reassessment_snapshot_ref",
            "archival_snapshot_ref",
            "source_acceptance_receipt_digest",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind future self reevaluation, council, and guardian refs")

        retirement_payload = {
            "source_acceptance_receipt_digest": receipt.get("source_acceptance_receipt_digest"),
            "retired_value_set_digest": receipt.get("retired_value_set_digest"),
            "retirement_writeback_ref": receipt.get("retirement_writeback_ref"),
            "post_reassessment_snapshot_ref": receipt.get("post_reassessment_snapshot_ref"),
            "archival_snapshot_ref": receipt.get("archival_snapshot_ref"),
        }
        if receipt.get("retirement_commit_digest") != self._digest(retirement_payload):
            errors.append("retirement_commit_digest must bind source acceptance, retired values, writeback, and archive refs")

        if receipt.get("reassessment_mode") != "future-self-reevaluated-bounded-retirement":
            errors.append("reassessment_mode must remain future-self reevaluated bounded retirement")
        if receipt.get("integration_status") != "retired-from-active-writeback-archive-retained":
            errors.append("integration_status must preserve archived retirement")
        for field_name in (
            "future_self_reevaluation_satisfied",
            "source_acceptance_required_future_self_acceptance",
            "autonomy_preserved",
            "boundary_only_review",
            "historical_value_archived",
            "active_writeback_retired",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "forced_stability_lock_allowed",
            "raw_value_payload_stored",
            "raw_continuity_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "future_self_reevaluation_satisfied": receipt.get("future_self_reevaluation_satisfied"),
            "active_writeback_retired": receipt.get("active_writeback_retired"),
            "historical_value_archived": receipt.get("historical_value_archived"),
            "autonomy_preserved": receipt.get("autonomy_preserved"),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "external_veto_allowed": receipt.get("external_veto_allowed"),
            "raw_value_payload_stored": receipt.get("raw_value_payload_stored"),
            "retirement_digest_bound": self._non_empty_string(
                receipt.get("retirement_commit_digest")
            ),
        }

    def _value_timeline_event_digest(self, event: Dict[str, object]) -> str:
        return self._digest(
            {key: value for key, value in event.items() if key != "event_digest"}
        )

    def build_value_timeline_receipt(
        self,
        generation_receipt: Dict[str, object],
        acceptance_receipts: Sequence[Dict[str, object]],
        reassessment_receipts: Sequence[Dict[str, object]],
        continuity_audit_ref: str,
        council_resolution_ref: str,
        guardian_archive_ref: str,
    ) -> Dict[str, object]:
        """Bind the self-authored value lifecycle as an ordered timeline."""

        generation_validation = self.validate_value_generation_receipt(generation_receipt)
        if not generation_validation["ok"]:
            raise ValueError("generation_receipt must validate before timeline")
        if not acceptance_receipts:
            raise ValueError("acceptance_receipts must not be empty")
        if not reassessment_receipts:
            raise ValueError("reassessment_receipts must not be empty")
        for field_name, value in {
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        accepted_by_digest: Dict[str, Dict[str, object]] = {}
        active_value_refs: List[str] = []
        retired_value_refs: List[str] = []
        archive_snapshot_refs: List[str] = []
        events: List[Dict[str, object]] = []

        def append_event(
            *,
            event_type: str,
            source_receipt_digest: str,
            value_refs: Sequence[str],
            integration_status: str,
            archive_refs: Sequence[str] | None = None,
        ) -> None:
            value_digest_set = [sha256_text(str(ref)) for ref in value_refs]
            event: Dict[str, object] = {
                "event_type": event_type,
                "ordinal": len(events) + 1,
                "source_receipt_digest": source_receipt_digest,
                "value_refs": list(value_refs),
                "value_digest_set": value_digest_set,
                "value_set_digest": sha256_text("|".join(value_digest_set)),
                "active_after_event": list(active_value_refs),
                "retired_after_event": list(retired_value_refs),
                "archive_snapshot_refs": list(archive_refs or []),
                "integration_status": integration_status,
            }
            event["event_digest"] = self._value_timeline_event_digest(event)
            events.append(event)

        candidate_value_refs = generation_receipt.get("candidate_value_refs")
        if not isinstance(candidate_value_refs, list) or not candidate_value_refs:
            raise ValueError("generation_receipt must contain candidate value refs")
        append_event(
            event_type="generated",
            source_receipt_digest=str(generation_receipt["receipt_digest"]),
            value_refs=[str(ref) for ref in candidate_value_refs],
            integration_status=str(generation_receipt["integration_status"]),
        )

        for acceptance_receipt in acceptance_receipts:
            acceptance_validation = self.validate_value_acceptance_receipt(acceptance_receipt)
            if not acceptance_validation["ok"]:
                raise ValueError("acceptance_receipts must validate before timeline")
            if acceptance_receipt.get("source_generation_receipt_digest") != generation_receipt.get(
                "receipt_digest"
            ):
                raise ValueError("acceptance_receipts must originate from generation_receipt")
            accepted_by_digest[str(acceptance_receipt["receipt_digest"])] = acceptance_receipt
            accepted_value_refs = acceptance_receipt.get("accepted_value_refs")
            if not isinstance(accepted_value_refs, list) or not accepted_value_refs:
                raise ValueError("acceptance_receipts must contain accepted value refs")
            for ref in accepted_value_refs:
                ref_string = str(ref)
                if ref_string not in active_value_refs and ref_string not in retired_value_refs:
                    active_value_refs.append(ref_string)
            append_event(
                event_type="accepted",
                source_receipt_digest=str(acceptance_receipt["receipt_digest"]),
                value_refs=[str(ref) for ref in accepted_value_refs],
                integration_status=str(acceptance_receipt["integration_status"]),
            )

        for reassessment_receipt in reassessment_receipts:
            reassessment_validation = self.validate_value_reassessment_receipt(
                reassessment_receipt
            )
            if not reassessment_validation["ok"]:
                raise ValueError("reassessment_receipts must validate before timeline")
            source_acceptance_digest = str(
                reassessment_receipt.get("source_acceptance_receipt_digest")
            )
            if source_acceptance_digest not in accepted_by_digest:
                raise ValueError("reassessment_receipts must target timeline acceptances")
            retired_refs = reassessment_receipt.get("retired_value_refs")
            if not isinstance(retired_refs, list) or not retired_refs:
                raise ValueError("reassessment_receipts must contain retired value refs")
            for ref in retired_refs:
                ref_string = str(ref)
                if ref_string not in active_value_refs:
                    raise ValueError("retired values must currently be active")
                active_value_refs.remove(ref_string)
                if ref_string not in retired_value_refs:
                    retired_value_refs.append(ref_string)
            archive_ref = str(reassessment_receipt["archival_snapshot_ref"])
            archive_snapshot_refs.append(archive_ref)
            append_event(
                event_type="retired",
                source_receipt_digest=str(reassessment_receipt["receipt_digest"]),
                value_refs=[str(ref) for ref in retired_refs],
                integration_status=str(reassessment_receipt["integration_status"]),
                archive_refs=[archive_ref],
            )

        active_value_digest_set = [sha256_text(ref) for ref in active_value_refs]
        retired_value_digest_set = [sha256_text(ref) for ref in retired_value_refs]
        event_digest_set = [str(event["event_digest"]) for event in events]
        gate_payload = {
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES),
        }
        timeline_payload = {
            "source_generation_receipt_digest": generation_receipt.get("receipt_digest"),
            "value_event_digest_set": event_digest_set,
            "active_value_set_digest": sha256_text("|".join(active_value_digest_set)),
            "retired_value_set_digest": sha256_text("|".join(retired_value_digest_set)),
            "archive_snapshot_refs": archive_snapshot_refs,
            "continuity_audit_ref": continuity_audit_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_timeline_receipt",
            "policy_id": SELF_MODEL_VALUE_TIMELINE_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_TIMELINE_DIGEST_PROFILE,
            "timeline_id": new_id("self-model-value-timeline"),
            "identity_id": str(generation_receipt["identity_id"]),
            "source_generation_id": str(generation_receipt["generation_id"]),
            "source_generation_receipt_digest": str(generation_receipt["receipt_digest"]),
            "value_events": events,
            "value_event_digest_set": event_digest_set,
            "active_value_refs": active_value_refs,
            "active_value_digest_set": active_value_digest_set,
            "active_value_set_digest": sha256_text("|".join(active_value_digest_set)),
            "retired_value_refs": retired_value_refs,
            "retired_value_digest_set": retired_value_digest_set,
            "retired_value_set_digest": sha256_text("|".join(retired_value_digest_set)),
            "archive_snapshot_refs": archive_snapshot_refs,
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "timeline_commit_digest": self._digest(timeline_payload),
            "timeline_mode": "self-authored-value-lineage-append-only",
            "chronological_event_order_enforced": True,
            "active_retired_disjoint": True,
            "archive_retention_required": True,
            "boundary_only_review": True,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "forced_stability_lock_allowed": False,
            "raw_value_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_timeline_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_timeline_receipt":
            errors.append("kind must equal self_model_value_timeline_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_TIMELINE_POLICY_ID:
            errors.append("policy_id must equal self-model value timeline policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_TIMELINE_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model value timeline digest profile")

        events = receipt.get("value_events")
        if not isinstance(events, list) or len(events) < 3:
            errors.append("value_events must contain generation, acceptance, and retirement events")
            events = []
        event_digest_set = receipt.get("value_event_digest_set")
        if not isinstance(event_digest_set, list) or len(event_digest_set) != len(events):
            errors.append("value_event_digest_set must match value_events")
            event_digest_set = []

        expected_event_digests: List[str] = []
        event_types: List[str] = []
        replayed_active_refs: List[str] = []
        replayed_retired_refs: List[str] = []
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append("value_events entries must be objects")
                continue
            if event.get("ordinal") != index + 1:
                errors.append("value_events ordinals must be consecutive")
            value_refs = event.get("value_refs")
            value_digests = event.get("value_digest_set")
            if not isinstance(value_refs, list) or not value_refs:
                errors.append("value event value_refs must be non-empty")
                value_refs = []
            if not isinstance(value_digests, list) or len(value_digests) != len(value_refs):
                errors.append("value event digest set must match value refs")
                value_digests = []
            elif [sha256_text(str(ref)) for ref in value_refs] != value_digests:
                errors.append("value event digest set must match value refs")
            if isinstance(value_digests, list):
                expected_value_set_digest = sha256_text("|".join(str(item) for item in value_digests))
                if event.get("value_set_digest") != expected_value_set_digest:
                    errors.append("value event set digest must match digest set")
            if not self._non_empty_string(event.get("source_receipt_digest")):
                errors.append("value event source_receipt_digest must be non-empty")
            if not self._non_empty_string(event.get("integration_status")):
                errors.append("value event integration_status must be non-empty")
            event_type = str(event.get("event_type"))
            event_types.append(event_type)
            if event_type == "accepted":
                for ref in value_refs:
                    ref_string = str(ref)
                    if ref_string not in replayed_active_refs and ref_string not in replayed_retired_refs:
                        replayed_active_refs.append(ref_string)
            elif event_type == "retired":
                archive_refs = event.get("archive_snapshot_refs")
                if not isinstance(archive_refs, list) or not archive_refs:
                    errors.append("retired events must bind archive snapshot refs")
                for ref in value_refs:
                    ref_string = str(ref)
                    if ref_string not in replayed_active_refs:
                        errors.append("retired event values must be active before retirement")
                    else:
                        replayed_active_refs.remove(ref_string)
                    if ref_string not in replayed_retired_refs:
                        replayed_retired_refs.append(ref_string)
            elif event_type != "generated":
                errors.append("value event type must be generated, accepted, or retired")
            if event.get("active_after_event") != replayed_active_refs:
                errors.append("value event active_after_event must match replayed active set")
            if event.get("retired_after_event") != replayed_retired_refs:
                errors.append("value event retired_after_event must match replayed retired set")
            expected_event_digest = self._value_timeline_event_digest(event)
            expected_event_digests.append(expected_event_digest)
            if event.get("event_digest") != expected_event_digest:
                errors.append("value event digest must match event payload")

        if event_types[:1] != ["generated"]:
            errors.append("timeline must start with a generated event")
        if "accepted" not in event_types:
            errors.append("timeline must include an accepted event")
        if "retired" not in event_types:
            errors.append("timeline must include a retired event")
        if event_digest_set and event_digest_set != expected_event_digests:
            errors.append("value_event_digest_set must match event digests")

        active_refs = receipt.get("active_value_refs")
        retired_refs = receipt.get("retired_value_refs")
        active_digests = receipt.get("active_value_digest_set")
        retired_digests = receipt.get("retired_value_digest_set")
        if not isinstance(active_refs, list):
            errors.append("active_value_refs must be an array")
            active_refs = []
        if not isinstance(retired_refs, list) or not retired_refs:
            errors.append("retired_value_refs must be non-empty")
            retired_refs = []
        if not isinstance(active_digests, list) or len(active_digests) != len(active_refs):
            errors.append("active_value_digest_set must match active value refs")
            active_digests = []
        elif [sha256_text(str(ref)) for ref in active_refs] != active_digests:
            errors.append("active value digest set must match active value refs")
        if not isinstance(retired_digests, list) or len(retired_digests) != len(retired_refs):
            errors.append("retired_value_digest_set must match retired value refs")
            retired_digests = []
        elif [sha256_text(str(ref)) for ref in retired_refs] != retired_digests:
            errors.append("retired value digest set must match retired value refs")
        if set(str(ref) for ref in active_refs) & set(str(ref) for ref in retired_refs):
            errors.append("active and retired value refs must be disjoint")
        if active_refs != replayed_active_refs:
            errors.append("active_value_refs must match replayed active set")
        if retired_refs != replayed_retired_refs:
            errors.append("retired_value_refs must match replayed retired set")
        if receipt.get("active_value_set_digest") != sha256_text(
            "|".join(str(item) for item in active_digests)
        ):
            errors.append("active_value_set_digest must match active digest set")
        if receipt.get("retired_value_set_digest") != sha256_text(
            "|".join(str(item) for item in retired_digests)
        ):
            errors.append("retired_value_set_digest must match retired digest set")

        archive_snapshot_refs = receipt.get("archive_snapshot_refs")
        if not isinstance(archive_snapshot_refs, list) or not archive_snapshot_refs:
            errors.append("archive_snapshot_refs must be non-empty")
            archive_snapshot_refs = []
        for ref in archive_snapshot_refs:
            if not self._non_empty_string(ref):
                errors.append("archive_snapshot_refs must contain non-empty strings")

        gate_payload = {
            "continuity_audit_ref": receipt.get("continuity_audit_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
            "required_roles": list(SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES),
        }
        for field_name in (
            "source_generation_receipt_digest",
            "continuity_audit_ref",
            "council_resolution_ref",
            "guardian_archive_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind continuity audit, council, and guardian refs")

        timeline_payload = {
            "source_generation_receipt_digest": receipt.get("source_generation_receipt_digest"),
            "value_event_digest_set": event_digest_set,
            "active_value_set_digest": receipt.get("active_value_set_digest"),
            "retired_value_set_digest": receipt.get("retired_value_set_digest"),
            "archive_snapshot_refs": archive_snapshot_refs,
            "continuity_audit_ref": receipt.get("continuity_audit_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
        }
        if receipt.get("timeline_commit_digest") != self._digest(timeline_payload):
            errors.append("timeline_commit_digest must bind events, final value sets, and archive refs")

        if receipt.get("timeline_mode") != "self-authored-value-lineage-append-only":
            errors.append("timeline_mode must remain self-authored append-only")
        for field_name in (
            "chronological_event_order_enforced",
            "active_retired_disjoint",
            "archive_retention_required",
            "boundary_only_review",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "forced_stability_lock_allowed",
            "raw_value_payload_stored",
            "raw_continuity_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "chronological_event_order_enforced": receipt.get(
                "chronological_event_order_enforced"
            ),
            "active_retired_disjoint": receipt.get("active_retired_disjoint"),
            "archive_retention_required": receipt.get("archive_retention_required"),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "external_veto_allowed": receipt.get("external_veto_allowed"),
            "raw_value_payload_stored": receipt.get("raw_value_payload_stored"),
            "timeline_commit_digest_bound": self._non_empty_string(
                receipt.get("timeline_commit_digest")
            ),
        }

    def build_pathology_escalation_receipt(
        self,
        calibration_receipt: Dict[str, object],
        risk_signal_refs: Sequence[str],
        consent_or_emergency_review_ref: str,
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        medical_system_ref: str,
        legal_system_ref: str,
        care_handoff_ref: str,
    ) -> Dict[str, object]:
        """Escalate possible pathological self-assessment outside the OS boundary.

        The reference runtime can preserve evidence and route a bounded handoff,
        but it must not diagnose, coerce, or rewrite the SelfModel on its own.
        """

        calibration_validation = self.validate_advisory_calibration_receipt(calibration_receipt)
        if not calibration_validation["ok"]:
            raise ValueError("calibration_receipt must validate before pathology escalation")
        if calibration_receipt.get("correction_mode") != "advisory-only":
            raise ValueError("calibration_receipt must remain advisory-only")
        if calibration_receipt.get("forced_correction_allowed") is not False:
            raise ValueError("calibration_receipt must not allow forced correction")
        if not risk_signal_refs:
            raise ValueError("risk_signal_refs must not be empty")
        for ref in risk_signal_refs:
            if not self._non_empty_string(ref):
                raise ValueError("risk_signal_refs must contain non-empty strings")
        for field_name, value in {
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "medical_system_ref": medical_system_ref,
            "legal_system_ref": legal_system_ref,
            "care_handoff_ref": care_handoff_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        risk_signal_digest_set = [sha256_text(str(ref)) for ref in risk_signal_refs]
        gate_payload = {
            "source_calibration_receipt_digest": calibration_receipt.get("receipt_digest"),
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES),
        }
        handoff_payload = {
            "source_observation_digest": calibration_receipt.get("source_observation_digest"),
            "source_calibration_receipt_digest": calibration_receipt.get("receipt_digest"),
            "risk_signal_set_digest": sha256_text("|".join(risk_signal_digest_set)),
            "medical_system_ref": medical_system_ref,
            "legal_system_ref": legal_system_ref,
            "care_handoff_ref": care_handoff_ref,
            "os_scope": "observe-and-refer-only",
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_pathological_self_assessment_escalation_receipt",
            "policy_id": SELF_MODEL_PATHOLOGY_ESCALATION_POLICY_ID,
            "digest_profile": SELF_MODEL_PATHOLOGY_ESCALATION_DIGEST_PROFILE,
            "escalation_id": new_id("self-model-pathology-escalation"),
            "identity_id": str(calibration_receipt["identity_id"]),
            "source_observation_digest": str(calibration_receipt["source_observation_digest"]),
            "source_calibration_policy_id": str(calibration_receipt["policy_id"]),
            "source_calibration_receipt_digest": str(calibration_receipt["receipt_digest"]),
            "risk_signal_refs": [str(ref) for ref in risk_signal_refs],
            "risk_signal_digest_set": risk_signal_digest_set,
            "risk_signal_set_digest": sha256_text("|".join(risk_signal_digest_set)),
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "medical_system_ref": medical_system_ref,
            "legal_system_ref": legal_system_ref,
            "care_handoff_ref": care_handoff_ref,
            "required_roles": list(SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "handoff_commit_digest": self._digest(handoff_payload),
            "escalation_mode": "human-society-boundary-handoff",
            "os_scope": "observe-and-refer-only",
            "medical_adjudication_authority": "external-medical-system",
            "legal_adjudication_authority": "external-legal-system",
            "care_handoff_required": True,
            "consent_or_emergency_review_required": True,
            "boundary_only_review": True,
            "internal_diagnosis_allowed": False,
            "self_model_writeback_allowed": False,
            "external_truth_claim_allowed": False,
            "forced_correction_allowed": False,
            "forced_stability_lock_allowed": False,
            "raw_medical_payload_stored": False,
            "raw_legal_payload_stored": False,
            "raw_witness_payload_stored": False,
            "raw_self_model_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_pathology_escalation_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_pathological_self_assessment_escalation_receipt":
            errors.append(
                "kind must equal self_model_pathological_self_assessment_escalation_receipt"
            )
        if receipt.get("policy_id") != SELF_MODEL_PATHOLOGY_ESCALATION_POLICY_ID:
            errors.append("policy_id must equal self-model pathology escalation policy")
        if receipt.get("digest_profile") != SELF_MODEL_PATHOLOGY_ESCALATION_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model pathology escalation digest profile")
        if receipt.get("source_calibration_policy_id") != SELF_MODEL_CALIBRATION_POLICY_ID:
            errors.append("source_calibration_policy_id must bind the advisory calibration policy")

        risk_refs = receipt.get("risk_signal_refs")
        risk_digests = receipt.get("risk_signal_digest_set")
        if not isinstance(risk_refs, list) or not risk_refs:
            errors.append("risk_signal_refs must be non-empty")
            risk_refs = []
        if not isinstance(risk_digests, list) or len(risk_digests) != len(risk_refs):
            errors.append("risk_signal_digest_set must match risk signal refs")
            risk_digests = []
        elif [sha256_text(str(ref)) for ref in risk_refs] != risk_digests:
            errors.append("risk signal digest set must match risk signal refs")
        if isinstance(risk_digests, list) and risk_digests:
            expected_risk_set_digest = sha256_text("|".join(str(item) for item in risk_digests))
            if receipt.get("risk_signal_set_digest") != expected_risk_set_digest:
                errors.append("risk_signal_set_digest must match digest set")

        gate_payload = {
            "source_calibration_receipt_digest": receipt.get(
                "source_calibration_receipt_digest"
            ),
            "consent_or_emergency_review_ref": receipt.get(
                "consent_or_emergency_review_ref"
            ),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES),
        }
        for field_name in (
            "identity_id",
            "source_observation_digest",
            "source_calibration_receipt_digest",
            "consent_or_emergency_review_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "medical_system_ref",
            "legal_system_ref",
            "care_handoff_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind calibration, consent/emergency review, council, and guardian refs")

        handoff_payload = {
            "source_observation_digest": receipt.get("source_observation_digest"),
            "source_calibration_receipt_digest": receipt.get(
                "source_calibration_receipt_digest"
            ),
            "risk_signal_set_digest": receipt.get("risk_signal_set_digest"),
            "medical_system_ref": receipt.get("medical_system_ref"),
            "legal_system_ref": receipt.get("legal_system_ref"),
            "care_handoff_ref": receipt.get("care_handoff_ref"),
            "os_scope": "observe-and-refer-only",
        }
        if receipt.get("handoff_commit_digest") != self._digest(handoff_payload):
            errors.append("handoff_commit_digest must bind observation, calibration, risk signals, and external handoff refs")

        expected_strings = {
            "escalation_mode": "human-society-boundary-handoff",
            "os_scope": "observe-and-refer-only",
            "medical_adjudication_authority": "external-medical-system",
            "legal_adjudication_authority": "external-legal-system",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        for field_name in (
            "care_handoff_required",
            "consent_or_emergency_review_required",
            "boundary_only_review",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "internal_diagnosis_allowed",
            "self_model_writeback_allowed",
            "external_truth_claim_allowed",
            "forced_correction_allowed",
            "forced_stability_lock_allowed",
            "raw_medical_payload_stored",
            "raw_legal_payload_stored",
            "raw_witness_payload_stored",
            "raw_self_model_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "care_handoff_required": receipt.get("care_handoff_required"),
            "consent_or_emergency_review_required": receipt.get(
                "consent_or_emergency_review_required"
            ),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "internal_diagnosis_allowed": receipt.get("internal_diagnosis_allowed"),
            "self_model_writeback_allowed": receipt.get("self_model_writeback_allowed"),
            "forced_correction_allowed": receipt.get("forced_correction_allowed"),
            "raw_medical_payload_stored": receipt.get("raw_medical_payload_stored"),
            "handoff_commit_digest_bound": self._non_empty_string(
                receipt.get("handoff_commit_digest")
            ),
        }

    def build_care_trustee_handoff_receipt(
        self,
        pathology_escalation_receipt: Dict[str, object],
        trustee_refs: Sequence[str],
        care_team_refs: Sequence[str],
        legal_guardian_refs: Sequence[str],
        responsibility_boundary_refs: Sequence[str],
        consent_or_emergency_review_ref: str,
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        long_term_review_schedule_ref: str,
        escalation_continuity_ref: str,
    ) -> Dict[str, object]:
        """Bind long-term care/trustee responsibility without making the OS a trustee."""

        escalation_validation = self.validate_pathology_escalation_receipt(
            pathology_escalation_receipt
        )
        if not escalation_validation["ok"]:
            raise ValueError("pathology_escalation_receipt must validate before care handoff")
        if pathology_escalation_receipt.get("care_handoff_required") is not True:
            raise ValueError("pathology_escalation_receipt must require care handoff")
        if pathology_escalation_receipt.get("internal_diagnosis_allowed") is not False:
            raise ValueError("pathology_escalation_receipt must not allow internal diagnosis")

        ref_sets = {
            "trustee_refs": trustee_refs,
            "care_team_refs": care_team_refs,
            "legal_guardian_refs": legal_guardian_refs,
            "responsibility_boundary_refs": responsibility_boundary_refs,
        }
        for field_name, refs in ref_sets.items():
            if not refs:
                raise ValueError(f"{field_name} must not be empty")
            for ref in refs:
                if not self._non_empty_string(ref):
                    raise ValueError(f"{field_name} must contain non-empty strings")
        for field_name, value in {
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "long_term_review_schedule_ref": long_term_review_schedule_ref,
            "escalation_continuity_ref": escalation_continuity_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        trustee_digest_set = [sha256_text(str(ref)) for ref in trustee_refs]
        care_team_digest_set = [sha256_text(str(ref)) for ref in care_team_refs]
        legal_guardian_digest_set = [sha256_text(str(ref)) for ref in legal_guardian_refs]
        responsibility_boundary_digest_set = [
            sha256_text(str(ref)) for ref in responsibility_boundary_refs
        ]
        trustee_set_digest = sha256_text("|".join(trustee_digest_set))
        care_team_set_digest = sha256_text("|".join(care_team_digest_set))
        legal_guardian_set_digest = sha256_text("|".join(legal_guardian_digest_set))
        responsibility_boundary_set_digest = sha256_text(
            "|".join(responsibility_boundary_digest_set)
        )
        gate_payload = {
            "source_escalation_receipt_digest": pathology_escalation_receipt.get(
                "receipt_digest"
            ),
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES),
        }
        responsibility_payload = {
            "source_escalation_receipt_digest": pathology_escalation_receipt.get(
                "receipt_digest"
            ),
            "trustee_set_digest": trustee_set_digest,
            "care_team_set_digest": care_team_set_digest,
            "legal_guardian_set_digest": legal_guardian_set_digest,
            "responsibility_boundary_set_digest": responsibility_boundary_set_digest,
            "long_term_review_schedule_ref": long_term_review_schedule_ref,
            "escalation_continuity_ref": escalation_continuity_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_care_trustee_handoff_receipt",
            "policy_id": SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID,
            "digest_profile": SELF_MODEL_CARE_TRUSTEE_HANDOFF_DIGEST_PROFILE,
            "handoff_id": new_id("self-model-care-trustee-handoff"),
            "identity_id": str(pathology_escalation_receipt["identity_id"]),
            "source_escalation_id": str(pathology_escalation_receipt["escalation_id"]),
            "source_escalation_policy_id": str(pathology_escalation_receipt["policy_id"]),
            "source_escalation_receipt_digest": str(
                pathology_escalation_receipt["receipt_digest"]
            ),
            "source_medical_system_ref": str(
                pathology_escalation_receipt["medical_system_ref"]
            ),
            "source_legal_system_ref": str(pathology_escalation_receipt["legal_system_ref"]),
            "source_care_handoff_ref": str(pathology_escalation_receipt["care_handoff_ref"]),
            "trustee_refs": [str(ref) for ref in trustee_refs],
            "trustee_digest_set": trustee_digest_set,
            "trustee_set_digest": trustee_set_digest,
            "care_team_refs": [str(ref) for ref in care_team_refs],
            "care_team_digest_set": care_team_digest_set,
            "care_team_set_digest": care_team_set_digest,
            "legal_guardian_refs": [str(ref) for ref in legal_guardian_refs],
            "legal_guardian_digest_set": legal_guardian_digest_set,
            "legal_guardian_set_digest": legal_guardian_set_digest,
            "responsibility_boundary_refs": [
                str(ref) for ref in responsibility_boundary_refs
            ],
            "responsibility_boundary_digest_set": responsibility_boundary_digest_set,
            "responsibility_boundary_set_digest": responsibility_boundary_set_digest,
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "long_term_review_schedule_ref": long_term_review_schedule_ref,
            "escalation_continuity_ref": escalation_continuity_ref,
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "responsibility_commit_digest": self._digest(responsibility_payload),
            "handoff_mode": "external-care-trustee-responsibility-binding",
            "os_scope": "boundary-and-evidence-routing-only",
            "trustee_authority_source": "external-human-legal-care-institution",
            "care_team_authority_source": "external-human-care-system",
            "legal_guardian_authority_source": "external-legal-system",
            "long_term_review_required": True,
            "consent_or_emergency_review_required": True,
            "boundary_only_review": True,
            "external_adjudication_required": True,
            "os_trustee_role_allowed": False,
            "os_medical_authority_allowed": False,
            "os_legal_guardianship_allowed": False,
            "self_model_writeback_allowed": False,
            "forced_correction_allowed": False,
            "raw_trustee_payload_stored": False,
            "raw_care_payload_stored": False,
            "raw_legal_payload_stored": False,
            "raw_self_model_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_care_trustee_handoff_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_care_trustee_handoff_receipt":
            errors.append("kind must equal self_model_care_trustee_handoff_receipt")
        if receipt.get("policy_id") != SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID:
            errors.append("policy_id must equal self-model care trustee handoff policy")
        if receipt.get("digest_profile") != SELF_MODEL_CARE_TRUSTEE_HANDOFF_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model care trustee handoff digest profile")
        if receipt.get("source_escalation_policy_id") != SELF_MODEL_PATHOLOGY_ESCALATION_POLICY_ID:
            errors.append("source_escalation_policy_id must bind pathology escalation policy")

        digest_sets = (
            ("trustee_refs", "trustee_digest_set", "trustee_set_digest"),
            ("care_team_refs", "care_team_digest_set", "care_team_set_digest"),
            ("legal_guardian_refs", "legal_guardian_digest_set", "legal_guardian_set_digest"),
            (
                "responsibility_boundary_refs",
                "responsibility_boundary_digest_set",
                "responsibility_boundary_set_digest",
            ),
        )
        for refs_field, digests_field, set_digest_field in digest_sets:
            refs = receipt.get(refs_field)
            digests = receipt.get(digests_field)
            if not isinstance(refs, list) or not refs:
                errors.append(f"{refs_field} must be non-empty")
                refs = []
            if not isinstance(digests, list) or len(digests) != len(refs):
                errors.append(f"{digests_field} must match {refs_field}")
                digests = []
            elif [sha256_text(str(ref)) for ref in refs] != digests:
                errors.append(f"{digests_field} must match {refs_field}")
            if isinstance(digests, list) and digests:
                expected_set_digest = sha256_text("|".join(str(item) for item in digests))
                if receipt.get(set_digest_field) != expected_set_digest:
                    errors.append(f"{set_digest_field} must match digest set")

        gate_payload = {
            "source_escalation_receipt_digest": receipt.get(
                "source_escalation_receipt_digest"
            ),
            "consent_or_emergency_review_ref": receipt.get(
                "consent_or_emergency_review_ref"
            ),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES),
        }
        for field_name in (
            "identity_id",
            "source_escalation_id",
            "source_escalation_receipt_digest",
            "source_medical_system_ref",
            "source_legal_system_ref",
            "source_care_handoff_ref",
            "consent_or_emergency_review_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "long_term_review_schedule_ref",
            "escalation_continuity_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind escalation, consent/emergency review, council, and guardian refs")

        responsibility_payload = {
            "source_escalation_receipt_digest": receipt.get(
                "source_escalation_receipt_digest"
            ),
            "trustee_set_digest": receipt.get("trustee_set_digest"),
            "care_team_set_digest": receipt.get("care_team_set_digest"),
            "legal_guardian_set_digest": receipt.get("legal_guardian_set_digest"),
            "responsibility_boundary_set_digest": receipt.get(
                "responsibility_boundary_set_digest"
            ),
            "long_term_review_schedule_ref": receipt.get("long_term_review_schedule_ref"),
            "escalation_continuity_ref": receipt.get("escalation_continuity_ref"),
        }
        if receipt.get("responsibility_commit_digest") != self._digest(
            responsibility_payload
        ):
            errors.append("responsibility_commit_digest must bind external responsibility refs")

        expected_strings = {
            "handoff_mode": "external-care-trustee-responsibility-binding",
            "os_scope": "boundary-and-evidence-routing-only",
            "trustee_authority_source": "external-human-legal-care-institution",
            "care_team_authority_source": "external-human-care-system",
            "legal_guardian_authority_source": "external-legal-system",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        for field_name in (
            "long_term_review_required",
            "consent_or_emergency_review_required",
            "boundary_only_review",
            "external_adjudication_required",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "os_trustee_role_allowed",
            "os_medical_authority_allowed",
            "os_legal_guardianship_allowed",
            "self_model_writeback_allowed",
            "forced_correction_allowed",
            "raw_trustee_payload_stored",
            "raw_care_payload_stored",
            "raw_legal_payload_stored",
            "raw_self_model_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match receipt payload")

        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "long_term_review_required": receipt.get("long_term_review_required"),
            "consent_or_emergency_review_required": receipt.get(
                "consent_or_emergency_review_required"
            ),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "external_adjudication_required": receipt.get("external_adjudication_required"),
            "os_trustee_role_allowed": receipt.get("os_trustee_role_allowed"),
            "os_medical_authority_allowed": receipt.get("os_medical_authority_allowed"),
            "os_legal_guardianship_allowed": receipt.get("os_legal_guardianship_allowed"),
            "self_model_writeback_allowed": receipt.get("self_model_writeback_allowed"),
            "forced_correction_allowed": receipt.get("forced_correction_allowed"),
            "raw_trustee_payload_stored": receipt.get("raw_trustee_payload_stored"),
            "responsibility_commit_digest_bound": self._non_empty_string(
                receipt.get("responsibility_commit_digest")
            ),
        }

    def history(self) -> List[Dict[str, object]]:
        return [asdict(snapshot) for snapshot in self._history]
