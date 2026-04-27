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
SELF_MODEL_VALUE_ACCEPTANCE_POLICY_ID = "self-model-future-self-acceptance-writeback-v1"
SELF_MODEL_VALUE_ACCEPTANCE_DIGEST_PROFILE = "self-model-value-acceptance-digest-v1"
SELF_MODEL_VALUE_ACCEPTANCE_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_REASSESSMENT_POLICY_ID = "self-model-future-self-reevaluation-retirement-v1"
SELF_MODEL_VALUE_REASSESSMENT_DIGEST_PROFILE = "self-model-value-reassessment-digest-v1"
SELF_MODEL_VALUE_REASSESSMENT_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_TIMELINE_POLICY_ID = "self-model-value-lineage-timeline-v1"
SELF_MODEL_VALUE_TIMELINE_DIGEST_PROFILE = "self-model-value-timeline-digest-v1"
SELF_MODEL_VALUE_TIMELINE_REQUIRED_ROLES = ("self", "council", "guardian")


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

    def history(self) -> List[Dict[str, object]]:
        return [asdict(snapshot) for snapshot in self._history]
