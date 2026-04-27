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

    def history(self) -> List[Dict[str, object]]:
        return [asdict(snapshot) for snapshot in self._history]
