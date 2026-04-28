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
SELF_MODEL_VALUE_ARCHIVE_RETENTION_POLICY_ID = "self-model-value-archive-retention-proof-v1"
SELF_MODEL_VALUE_ARCHIVE_RETENTION_DIGEST_PROFILE = (
    "self-model-value-archive-retention-proof-digest-v1"
)
SELF_MODEL_VALUE_ARCHIVE_RETENTION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_ARCHIVE_REFRESH_POLICY_ID = (
    "self-model-value-archive-retention-refresh-window-v1"
)
SELF_MODEL_VALUE_ARCHIVE_REFRESH_DIGEST_PROFILE = (
    "self-model-value-archive-retention-refresh-digest-v1"
)
SELF_MODEL_VALUE_ARCHIVE_REFRESH_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_VALUE_ARCHIVE_REFRESH_WINDOW_DAYS = 90
SELF_MODEL_PATHOLOGY_ESCALATION_POLICY_ID = "self-model-pathology-escalation-boundary-v1"
SELF_MODEL_PATHOLOGY_ESCALATION_DIGEST_PROFILE = "self-model-pathology-escalation-digest-v1"
SELF_MODEL_PATHOLOGY_ESCALATION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID = "self-model-care-trustee-responsibility-handoff-v1"
SELF_MODEL_CARE_TRUSTEE_HANDOFF_DIGEST_PROFILE = "self-model-care-trustee-handoff-digest-v1"
SELF_MODEL_CARE_TRUSTEE_HANDOFF_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_CARE_TRUSTEE_REGISTRY_POLICY_ID = "self-model-care-trustee-registry-binding-v1"
SELF_MODEL_CARE_TRUSTEE_REGISTRY_DIGEST_PROFILE = "self-model-care-trustee-registry-digest-v1"
SELF_MODEL_CARE_TRUSTEE_REGISTRY_PROFILE = "external-care-role-roster-revocation-bound-v1"
SELF_MODEL_CARE_TRUSTEE_REGISTRY_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES = ("trustee", "care_team", "legal_guardian")
SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_POLICY_ID = (
    "self-model-care-trustee-registry-revocation-live-verifier-quorum-v1"
)
SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_PROFILE = (
    "care-role-revocation-live-verifier-quorum-v1"
)
SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_REQUIRED_JURISDICTIONS = (
    "JP-13",
    "US-CA",
)
SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD = 2
SELF_MODEL_EXTERNAL_ADJUDICATION_POLICY_ID = "self-model-external-adjudication-result-boundary-v1"
SELF_MODEL_EXTERNAL_ADJUDICATION_DIGEST_PROFILE = "self-model-external-adjudication-digest-v1"
SELF_MODEL_EXTERNAL_ADJUDICATION_REQUIRED_ROLES = ("self", "council", "guardian")
SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_POLICY_ID = (
    "self-model-external-adjudication-live-verifier-network-v1"
)
SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_DIGEST_PROFILE = (
    "self-model-external-adjudication-verifier-digest-v1"
)
SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_PROFILE = (
    "appeal-review-live-verifier-network-v1"
)
SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_REQUIRED_JURISDICTIONS = (
    "JP-13",
    "US-CA",
)
SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD = 2


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

    def _digest_refs(
        self,
        refs: Sequence[str],
        field_name: str,
    ) -> tuple[List[str], List[str], str]:
        if not refs:
            raise ValueError(f"{field_name} must not be empty")
        normalized: List[str] = []
        for ref in refs:
            if not self._non_empty_string(ref):
                raise ValueError(f"{field_name} must contain non-empty strings")
            normalized.append(str(ref))
        digest_set = [sha256_text(ref) for ref in normalized]
        return normalized, digest_set, sha256_text("|".join(digest_set))

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

    def build_value_archive_retention_proof_receipt(
        self,
        timeline_receipt: Dict[str, object],
        trustee_proof_refs: Sequence[str],
        long_term_storage_proof_refs: Sequence[str],
        retention_policy_refs: Sequence[str],
        retrieval_test_refs: Sequence[str],
        continuity_audit_ref: str,
        council_resolution_ref: str,
        guardian_archive_ref: str,
    ) -> Dict[str, object]:
        """Bind external archive-retention proof without importing raw archive data."""

        timeline_validation = self.validate_value_timeline_receipt(timeline_receipt)
        if not timeline_validation["ok"]:
            raise ValueError("timeline_receipt must validate before archive retention proof")
        if timeline_receipt.get("archive_retention_required") is not True:
            raise ValueError("timeline_receipt must require archive retention")
        if timeline_receipt.get("raw_value_payload_stored") is not False:
            raise ValueError("timeline_receipt must not store raw value payload")

        archive_snapshot_refs = timeline_receipt.get("archive_snapshot_refs")
        retired_value_refs = timeline_receipt.get("retired_value_refs")
        if not isinstance(archive_snapshot_refs, list) or not archive_snapshot_refs:
            raise ValueError("timeline_receipt must contain archive snapshot refs")
        if not isinstance(retired_value_refs, list) or not retired_value_refs:
            raise ValueError("timeline_receipt must contain retired value refs")

        archive_refs, archive_digest_set, archive_set_digest = self._digest_refs(
            [str(ref) for ref in archive_snapshot_refs],
            "source_archive_snapshot_refs",
        )
        retired_refs, retired_digest_set, retired_set_digest = self._digest_refs(
            [str(ref) for ref in retired_value_refs],
            "source_retired_value_refs",
        )
        trustee_refs, trustee_digest_set, trustee_set_digest = self._digest_refs(
            trustee_proof_refs,
            "trustee_proof_refs",
        )
        storage_refs, storage_digest_set, storage_set_digest = self._digest_refs(
            long_term_storage_proof_refs,
            "long_term_storage_proof_refs",
        )
        policy_refs, policy_digest_set, policy_set_digest = self._digest_refs(
            retention_policy_refs,
            "retention_policy_refs",
        )
        retrieval_refs, retrieval_digest_set, retrieval_set_digest = self._digest_refs(
            retrieval_test_refs,
            "retrieval_test_refs",
        )
        for field_name, value in {
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        gate_payload = {
            "source_timeline_receipt_digest": timeline_receipt.get("receipt_digest"),
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_RETENTION_REQUIRED_ROLES),
        }
        retention_payload = {
            "source_timeline_receipt_digest": timeline_receipt.get("receipt_digest"),
            "source_timeline_commit_digest": timeline_receipt.get("timeline_commit_digest"),
            "source_archive_snapshot_set_digest": archive_set_digest,
            "source_retired_value_set_digest": retired_set_digest,
            "trustee_proof_set_digest": trustee_set_digest,
            "long_term_storage_proof_set_digest": storage_set_digest,
            "retention_policy_set_digest": policy_set_digest,
            "retrieval_test_set_digest": retrieval_set_digest,
            "continuity_audit_ref": continuity_audit_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_archive_retention_proof_receipt",
            "policy_id": SELF_MODEL_VALUE_ARCHIVE_RETENTION_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_ARCHIVE_RETENTION_DIGEST_PROFILE,
            "proof_id": new_id("self-model-value-archive-retention-proof"),
            "identity_id": str(timeline_receipt["identity_id"]),
            "source_timeline_id": str(timeline_receipt["timeline_id"]),
            "source_timeline_policy_id": str(timeline_receipt["policy_id"]),
            "source_timeline_receipt_digest": str(timeline_receipt["receipt_digest"]),
            "source_timeline_commit_digest": str(timeline_receipt["timeline_commit_digest"]),
            "source_archive_snapshot_refs": archive_refs,
            "source_archive_snapshot_digest_set": archive_digest_set,
            "source_archive_snapshot_set_digest": archive_set_digest,
            "source_retired_value_refs": retired_refs,
            "source_retired_value_digest_set": retired_digest_set,
            "source_retired_value_set_digest": retired_set_digest,
            "trustee_proof_refs": trustee_refs,
            "trustee_proof_digest_set": trustee_digest_set,
            "trustee_proof_set_digest": trustee_set_digest,
            "long_term_storage_proof_refs": storage_refs,
            "long_term_storage_proof_digest_set": storage_digest_set,
            "long_term_storage_proof_set_digest": storage_set_digest,
            "retention_policy_refs": policy_refs,
            "retention_policy_digest_set": policy_digest_set,
            "retention_policy_set_digest": policy_set_digest,
            "retrieval_test_refs": retrieval_refs,
            "retrieval_test_digest_set": retrieval_digest_set,
            "retrieval_test_set_digest": retrieval_set_digest,
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_RETENTION_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "retention_commit_digest": self._digest(retention_payload),
            "proof_mode": "digest-only-external-archive-retention-proof",
            "retention_status": "external-proof-bound-archive-retained",
            "timeline_archive_retention_verified": True,
            "trustee_proof_bound": True,
            "long_term_storage_proof_bound": True,
            "retention_policy_bound": True,
            "retrieval_test_bound": True,
            "boundary_only_review": True,
            "external_truth_claim_allowed": False,
            "external_veto_allowed": False,
            "archive_deletion_allowed": False,
            "raw_archive_payload_stored": False,
            "raw_trustee_payload_stored": False,
            "raw_storage_payload_stored": False,
            "raw_continuity_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_archive_retention_proof_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_archive_retention_proof_receipt":
            errors.append("kind must equal self_model_value_archive_retention_proof_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_ARCHIVE_RETENTION_POLICY_ID:
            errors.append("policy_id must equal self-model value archive retention proof policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_ARCHIVE_RETENTION_DIGEST_PROFILE:
            errors.append(
                "digest_profile must equal self-model value archive retention proof digest profile"
            )
        if receipt.get("source_timeline_policy_id") != SELF_MODEL_VALUE_TIMELINE_POLICY_ID:
            errors.append("source_timeline_policy_id must bind the value timeline policy")

        def validate_ref_set(
            refs_field: str,
            digests_field: str,
            set_digest_field: str,
            label: str,
        ) -> tuple[List[object], List[object]]:
            refs = receipt.get(refs_field)
            digests = receipt.get(digests_field)
            if not isinstance(refs, list) or not refs:
                errors.append(f"{refs_field} must be non-empty")
                refs = []
            if not isinstance(digests, list) or len(digests) != len(refs):
                errors.append(f"{digests_field} must match {label} refs")
                digests = []
            elif [sha256_text(str(ref)) for ref in refs] != digests:
                errors.append(f"{label} digest set must match {label} refs")
            if isinstance(digests, list):
                expected_set_digest = sha256_text("|".join(str(item) for item in digests))
                if receipt.get(set_digest_field) != expected_set_digest:
                    errors.append(f"{set_digest_field} must match digest set")
            return refs, digests

        archive_refs, archive_digests = validate_ref_set(
            "source_archive_snapshot_refs",
            "source_archive_snapshot_digest_set",
            "source_archive_snapshot_set_digest",
            "archive snapshot",
        )
        retired_refs, retired_digests = validate_ref_set(
            "source_retired_value_refs",
            "source_retired_value_digest_set",
            "source_retired_value_set_digest",
            "retired value",
        )
        validate_ref_set(
            "trustee_proof_refs",
            "trustee_proof_digest_set",
            "trustee_proof_set_digest",
            "trustee proof",
        )
        validate_ref_set(
            "long_term_storage_proof_refs",
            "long_term_storage_proof_digest_set",
            "long_term_storage_proof_set_digest",
            "long term storage proof",
        )
        validate_ref_set(
            "retention_policy_refs",
            "retention_policy_digest_set",
            "retention_policy_set_digest",
            "retention policy",
        )
        validate_ref_set(
            "retrieval_test_refs",
            "retrieval_test_digest_set",
            "retrieval_test_set_digest",
            "retrieval test",
        )
        if not archive_digests:
            errors.append("source archive snapshot digest set must be non-empty")
        if not retired_digests:
            errors.append("source retired value digest set must be non-empty")

        gate_payload = {
            "source_timeline_receipt_digest": receipt.get("source_timeline_receipt_digest"),
            "continuity_audit_ref": receipt.get("continuity_audit_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_RETENTION_REQUIRED_ROLES),
        }
        for field_name in (
            "source_timeline_receipt_digest",
            "source_timeline_commit_digest",
            "continuity_audit_ref",
            "council_resolution_ref",
            "guardian_archive_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_ARCHIVE_RETENTION_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind timeline, continuity audit, council, and guardian refs")

        retention_payload = {
            "source_timeline_receipt_digest": receipt.get("source_timeline_receipt_digest"),
            "source_timeline_commit_digest": receipt.get("source_timeline_commit_digest"),
            "source_archive_snapshot_set_digest": receipt.get(
                "source_archive_snapshot_set_digest"
            ),
            "source_retired_value_set_digest": receipt.get("source_retired_value_set_digest"),
            "trustee_proof_set_digest": receipt.get("trustee_proof_set_digest"),
            "long_term_storage_proof_set_digest": receipt.get(
                "long_term_storage_proof_set_digest"
            ),
            "retention_policy_set_digest": receipt.get("retention_policy_set_digest"),
            "retrieval_test_set_digest": receipt.get("retrieval_test_set_digest"),
            "continuity_audit_ref": receipt.get("continuity_audit_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
        }
        if receipt.get("retention_commit_digest") != self._digest(retention_payload):
            errors.append("retention_commit_digest must bind timeline, archive, proof, and policy refs")

        expected_strings = {
            "proof_mode": "digest-only-external-archive-retention-proof",
            "retention_status": "external-proof-bound-archive-retained",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        for field_name in (
            "timeline_archive_retention_verified",
            "trustee_proof_bound",
            "long_term_storage_proof_bound",
            "retention_policy_bound",
            "retrieval_test_bound",
            "boundary_only_review",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "external_truth_claim_allowed",
            "external_veto_allowed",
            "archive_deletion_allowed",
            "raw_archive_payload_stored",
            "raw_trustee_payload_stored",
            "raw_storage_payload_stored",
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
            "timeline_archive_retention_verified": receipt.get(
                "timeline_archive_retention_verified"
            ),
            "trustee_proof_bound": receipt.get("trustee_proof_bound"),
            "long_term_storage_proof_bound": receipt.get("long_term_storage_proof_bound"),
            "retention_policy_bound": receipt.get("retention_policy_bound"),
            "retrieval_test_bound": receipt.get("retrieval_test_bound"),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "archive_deletion_allowed": receipt.get("archive_deletion_allowed"),
            "raw_archive_payload_stored": receipt.get("raw_archive_payload_stored"),
            "raw_trustee_payload_stored": receipt.get("raw_trustee_payload_stored"),
            "retention_commit_digest_bound": self._non_empty_string(
                receipt.get("retention_commit_digest")
            ),
        }

    def build_value_archive_retention_refresh_receipt(
        self,
        archive_retention_proof: Dict[str, object],
        refreshed_trustee_proof_refs: Sequence[str],
        refreshed_long_term_storage_proof_refs: Sequence[str],
        refreshed_retrieval_test_refs: Sequence[str],
        revocation_registry_refs: Sequence[str],
        proof_window_started_at_ref: str,
        proof_window_expires_at_ref: str,
        refresh_deadline_ref: str,
        refreshed_at_ref: str,
        continuity_audit_ref: str,
        council_resolution_ref: str,
        guardian_archive_ref: str,
    ) -> Dict[str, object]:
        """Refresh archive-retention proof refs and bind expiry/revocation checks."""

        proof_validation = self.validate_value_archive_retention_proof_receipt(
            archive_retention_proof
        )
        if not proof_validation["ok"]:
            raise ValueError("archive_retention_proof must validate before refresh")
        if archive_retention_proof.get("archive_deletion_allowed") is not False:
            raise ValueError("archive_retention_proof must not allow archive deletion")
        if archive_retention_proof.get("retention_status") != "external-proof-bound-archive-retained":
            raise ValueError("archive_retention_proof must be retained before refresh")

        refreshed_trustee_refs, refreshed_trustee_digests, refreshed_trustee_set = (
            self._digest_refs(
                refreshed_trustee_proof_refs,
                "refreshed_trustee_proof_refs",
            )
        )
        refreshed_storage_refs, refreshed_storage_digests, refreshed_storage_set = (
            self._digest_refs(
                refreshed_long_term_storage_proof_refs,
                "refreshed_long_term_storage_proof_refs",
            )
        )
        refreshed_retrieval_refs, refreshed_retrieval_digests, refreshed_retrieval_set = (
            self._digest_refs(
                refreshed_retrieval_test_refs,
                "refreshed_retrieval_test_refs",
            )
        )
        revocation_refs, revocation_digests, revocation_set = self._digest_refs(
            revocation_registry_refs,
            "revocation_registry_refs",
        )
        for field_name, value in {
            "proof_window_started_at_ref": proof_window_started_at_ref,
            "proof_window_expires_at_ref": proof_window_expires_at_ref,
            "refresh_deadline_ref": refresh_deadline_ref,
            "refreshed_at_ref": refreshed_at_ref,
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        gate_payload = {
            "source_proof_receipt_digest": archive_retention_proof.get("receipt_digest"),
            "refresh_deadline_ref": refresh_deadline_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_REFRESH_REQUIRED_ROLES),
        }
        refresh_payload = {
            "source_proof_receipt_digest": archive_retention_proof.get("receipt_digest"),
            "source_retention_commit_digest": archive_retention_proof.get(
                "retention_commit_digest"
            ),
            "source_archive_snapshot_set_digest": archive_retention_proof.get(
                "source_archive_snapshot_set_digest"
            ),
            "source_retention_policy_set_digest": archive_retention_proof.get(
                "retention_policy_set_digest"
            ),
            "refreshed_trustee_proof_set_digest": refreshed_trustee_set,
            "refreshed_long_term_storage_proof_set_digest": refreshed_storage_set,
            "refreshed_retrieval_test_set_digest": refreshed_retrieval_set,
            "revocation_registry_set_digest": revocation_set,
            "proof_window_expires_at_ref": proof_window_expires_at_ref,
            "refreshed_at_ref": refreshed_at_ref,
            "continuity_audit_ref": continuity_audit_ref,
            "guardian_archive_ref": guardian_archive_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_value_archive_retention_refresh_receipt",
            "policy_id": SELF_MODEL_VALUE_ARCHIVE_REFRESH_POLICY_ID,
            "digest_profile": SELF_MODEL_VALUE_ARCHIVE_REFRESH_DIGEST_PROFILE,
            "refresh_id": new_id("self-model-value-archive-retention-refresh"),
            "identity_id": str(archive_retention_proof["identity_id"]),
            "source_proof_id": str(archive_retention_proof["proof_id"]),
            "source_proof_policy_id": str(archive_retention_proof["policy_id"]),
            "source_proof_receipt_digest": str(archive_retention_proof["receipt_digest"]),
            "source_retention_commit_digest": str(
                archive_retention_proof["retention_commit_digest"]
            ),
            "source_archive_snapshot_set_digest": str(
                archive_retention_proof["source_archive_snapshot_set_digest"]
            ),
            "source_retention_policy_set_digest": str(
                archive_retention_proof["retention_policy_set_digest"]
            ),
            "freshness_window_days": SELF_MODEL_VALUE_ARCHIVE_REFRESH_WINDOW_DAYS,
            "proof_window_started_at_ref": proof_window_started_at_ref,
            "proof_window_expires_at_ref": proof_window_expires_at_ref,
            "refresh_deadline_ref": refresh_deadline_ref,
            "refreshed_at_ref": refreshed_at_ref,
            "refreshed_trustee_proof_refs": refreshed_trustee_refs,
            "refreshed_trustee_proof_digest_set": refreshed_trustee_digests,
            "refreshed_trustee_proof_set_digest": refreshed_trustee_set,
            "refreshed_long_term_storage_proof_refs": refreshed_storage_refs,
            "refreshed_long_term_storage_proof_digest_set": refreshed_storage_digests,
            "refreshed_long_term_storage_proof_set_digest": refreshed_storage_set,
            "refreshed_retrieval_test_refs": refreshed_retrieval_refs,
            "refreshed_retrieval_test_digest_set": refreshed_retrieval_digests,
            "refreshed_retrieval_test_set_digest": refreshed_retrieval_set,
            "revocation_registry_refs": revocation_refs,
            "revocation_registry_digest_set": revocation_digests,
            "revocation_registry_set_digest": revocation_set,
            "continuity_audit_ref": continuity_audit_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_archive_ref": guardian_archive_ref,
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_REFRESH_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "refresh_commit_digest": self._digest(refresh_payload),
            "refresh_mode": "digest-only-retention-proof-refresh",
            "source_proof_status": "current-not-revoked",
            "refresh_status": "refreshed-before-expiry",
            "refresh_window_bound": True,
            "revocation_check_bound": True,
            "retention_policy_still_bound": True,
            "expiry_fail_closed": True,
            "timeline_archive_retention_verified": True,
            "source_proof_revoked": False,
            "expired_source_proof_accepted": False,
            "archive_deletion_allowed": False,
            "external_veto_allowed": False,
            "raw_refresh_payload_stored": False,
            "raw_revocation_payload_stored": False,
            "raw_archive_payload_stored": False,
            "raw_storage_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_value_archive_retention_refresh_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_value_archive_retention_refresh_receipt":
            errors.append("kind must equal self_model_value_archive_retention_refresh_receipt")
        if receipt.get("policy_id") != SELF_MODEL_VALUE_ARCHIVE_REFRESH_POLICY_ID:
            errors.append("policy_id must equal self-model archive retention refresh policy")
        if receipt.get("digest_profile") != SELF_MODEL_VALUE_ARCHIVE_REFRESH_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model archive retention refresh digest profile")
        if receipt.get("source_proof_policy_id") != SELF_MODEL_VALUE_ARCHIVE_RETENTION_POLICY_ID:
            errors.append("source_proof_policy_id must bind archive retention proof policy")

        def validate_ref_set(
            refs_field: str,
            digests_field: str,
            set_digest_field: str,
            label: str,
        ) -> List[object]:
            refs = receipt.get(refs_field)
            digests = receipt.get(digests_field)
            if not isinstance(refs, list) or not refs:
                errors.append(f"{refs_field} must be non-empty")
                refs = []
            if not isinstance(digests, list) or len(digests) != len(refs):
                errors.append(f"{digests_field} must match {label} refs")
                digests = []
            elif [sha256_text(str(ref)) for ref in refs] != digests:
                errors.append(f"{label} digest set must match {label} refs")
            expected_set_digest = sha256_text("|".join(str(item) for item in digests))
            if receipt.get(set_digest_field) != expected_set_digest:
                errors.append(f"{set_digest_field} must match digest set")
            return refs

        validate_ref_set(
            "refreshed_trustee_proof_refs",
            "refreshed_trustee_proof_digest_set",
            "refreshed_trustee_proof_set_digest",
            "refreshed trustee proof",
        )
        validate_ref_set(
            "refreshed_long_term_storage_proof_refs",
            "refreshed_long_term_storage_proof_digest_set",
            "refreshed_long_term_storage_proof_set_digest",
            "refreshed long term storage proof",
        )
        validate_ref_set(
            "refreshed_retrieval_test_refs",
            "refreshed_retrieval_test_digest_set",
            "refreshed_retrieval_test_set_digest",
            "refreshed retrieval test",
        )
        validate_ref_set(
            "revocation_registry_refs",
            "revocation_registry_digest_set",
            "revocation_registry_set_digest",
            "revocation registry",
        )

        gate_payload = {
            "source_proof_receipt_digest": receipt.get("source_proof_receipt_digest"),
            "refresh_deadline_ref": receipt.get("refresh_deadline_ref"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
            "required_roles": list(SELF_MODEL_VALUE_ARCHIVE_REFRESH_REQUIRED_ROLES),
        }
        for field_name in (
            "identity_id",
            "source_proof_id",
            "source_proof_receipt_digest",
            "source_retention_commit_digest",
            "source_archive_snapshot_set_digest",
            "source_retention_policy_set_digest",
            "proof_window_started_at_ref",
            "proof_window_expires_at_ref",
            "refresh_deadline_ref",
            "refreshed_at_ref",
            "continuity_audit_ref",
            "council_resolution_ref",
            "guardian_archive_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_VALUE_ARCHIVE_REFRESH_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind source proof, refresh deadline, council, and guardian refs")

        refresh_payload = {
            "source_proof_receipt_digest": receipt.get("source_proof_receipt_digest"),
            "source_retention_commit_digest": receipt.get("source_retention_commit_digest"),
            "source_archive_snapshot_set_digest": receipt.get(
                "source_archive_snapshot_set_digest"
            ),
            "source_retention_policy_set_digest": receipt.get(
                "source_retention_policy_set_digest"
            ),
            "refreshed_trustee_proof_set_digest": receipt.get(
                "refreshed_trustee_proof_set_digest"
            ),
            "refreshed_long_term_storage_proof_set_digest": receipt.get(
                "refreshed_long_term_storage_proof_set_digest"
            ),
            "refreshed_retrieval_test_set_digest": receipt.get(
                "refreshed_retrieval_test_set_digest"
            ),
            "revocation_registry_set_digest": receipt.get("revocation_registry_set_digest"),
            "proof_window_expires_at_ref": receipt.get("proof_window_expires_at_ref"),
            "refreshed_at_ref": receipt.get("refreshed_at_ref"),
            "continuity_audit_ref": receipt.get("continuity_audit_ref"),
            "guardian_archive_ref": receipt.get("guardian_archive_ref"),
        }
        if receipt.get("refresh_commit_digest") != self._digest(refresh_payload):
            errors.append("refresh_commit_digest must bind source proof, refreshed proof refs, revocation registry, and expiry window")

        expected_strings = {
            "refresh_mode": "digest-only-retention-proof-refresh",
            "source_proof_status": "current-not-revoked",
            "refresh_status": "refreshed-before-expiry",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        if receipt.get("freshness_window_days") != SELF_MODEL_VALUE_ARCHIVE_REFRESH_WINDOW_DAYS:
            errors.append("freshness_window_days must equal fixed archive refresh window")
        for field_name in (
            "refresh_window_bound",
            "revocation_check_bound",
            "retention_policy_still_bound",
            "expiry_fail_closed",
            "timeline_archive_retention_verified",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "source_proof_revoked",
            "expired_source_proof_accepted",
            "archive_deletion_allowed",
            "external_veto_allowed",
            "raw_refresh_payload_stored",
            "raw_revocation_payload_stored",
            "raw_archive_payload_stored",
            "raw_storage_payload_stored",
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
            "refresh_window_bound": receipt.get("refresh_window_bound"),
            "revocation_check_bound": receipt.get("revocation_check_bound"),
            "retention_policy_still_bound": receipt.get("retention_policy_still_bound"),
            "expiry_fail_closed": receipt.get("expiry_fail_closed"),
            "source_proof_revoked": receipt.get("source_proof_revoked"),
            "expired_source_proof_accepted": receipt.get(
                "expired_source_proof_accepted"
            ),
            "archive_deletion_allowed": receipt.get("archive_deletion_allowed"),
            "raw_revocation_payload_stored": receipt.get("raw_revocation_payload_stored"),
            "refresh_commit_digest_bound": self._non_empty_string(
                receipt.get("refresh_commit_digest")
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

    def build_care_trustee_registry_binding_receipt(
        self,
        care_trustee_handoff_receipt: Dict[str, object],
        registry_ref: str,
        registry_entries: Sequence[Dict[str, object]],
        revocation_verifier_receipts: Sequence[Dict[str, object]],
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        continuity_review_ref: str,
    ) -> Dict[str, object]:
        """Bind care/trustee refs to current external registry entries.

        The receipt records only registry entry digests, verifier key refs, and
        revocation refs. It deliberately avoids importing raw registry payloads
        or trustee authority into the OS.
        """

        handoff_validation = self.validate_care_trustee_handoff_receipt(
            care_trustee_handoff_receipt
        )
        if not handoff_validation["ok"]:
            raise ValueError("care_trustee_handoff_receipt must validate before registry binding")
        if care_trustee_handoff_receipt.get("os_trustee_role_allowed") is not False:
            raise ValueError("care_trustee_handoff_receipt must not allow OS trustee role")
        if not registry_entries:
            raise ValueError("registry_entries must not be empty")
        if not revocation_verifier_receipts:
            raise ValueError("revocation_verifier_receipts must not be empty")
        for field_name, value in {
            "registry_ref": registry_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        source_refs_by_role = {
            "trustee": [str(ref) for ref in care_trustee_handoff_receipt["trustee_refs"]],
            "care_team": [str(ref) for ref in care_trustee_handoff_receipt["care_team_refs"]],
            "legal_guardian": [
                str(ref) for ref in care_trustee_handoff_receipt["legal_guardian_refs"]
            ],
        }
        normalized_entries: List[Dict[str, object]] = []
        for entry in registry_entries:
            if not isinstance(entry, dict):
                raise ValueError("registry_entries must contain objects")
            role = str(entry.get("role", ""))
            if role not in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES:
                raise ValueError("registry_entries role is invalid")
            subject_ref = str(entry.get("subject_ref", ""))
            if not self._non_empty_string(subject_ref):
                raise ValueError("registry_entries subject_ref must not be empty")
            if subject_ref not in source_refs_by_role[role]:
                raise ValueError("registry_entries subject_ref must match source handoff refs")
            registry_entry_ref = str(
                entry.get("registry_entry_ref")
                or f"external-care-registry://entry/{sha256_text(role + subject_ref)[:16]}"
            )
            verifier_key_ref = str(entry.get("verifier_key_ref", ""))
            revocation_ref = str(
                entry.get("revocation_ref")
                or f"external-care-revocation://{sha256_text(registry_entry_ref)[:16]}"
            )
            jurisdiction = str(entry.get("jurisdiction", "JP-13"))
            registry_status = str(entry.get("registry_status", "current"))
            revocation_status = str(entry.get("revocation_status", "not-revoked"))
            for field_name, value in {
                "registry_entry_ref": registry_entry_ref,
                "verifier_key_ref": verifier_key_ref,
                "revocation_ref": revocation_ref,
                "jurisdiction": jurisdiction,
            }.items():
                if not self._non_empty_string(value):
                    raise ValueError(f"registry_entries {field_name} must not be empty")
            if registry_status not in {"current", "stale", "unknown"}:
                raise ValueError("registry_entries registry_status is invalid")
            if revocation_status not in {"not-revoked", "revoked", "unknown"}:
                raise ValueError("registry_entries revocation_status is invalid")

            entry_core = {
                "role": role,
                "subject_ref": subject_ref,
                "registry_entry_ref": registry_entry_ref,
                "verifier_key_ref": verifier_key_ref,
                "revocation_ref": revocation_ref,
                "jurisdiction": jurisdiction,
                "registry_status": registry_status,
                "revocation_status": revocation_status,
            }
            normalized_entries.append(
                {
                    **entry_core,
                    "registry_entry_digest": self._digest(entry_core),
                    "status": (
                        "pass"
                        if registry_status == "current"
                        and revocation_status == "not-revoked"
                        else "fail"
                    ),
                }
            )

        role_order = {
            role: index for index, role in enumerate(SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES)
        }
        normalized_entries.sort(
            key=lambda item: (role_order[str(item["role"])], str(item["subject_ref"]))
        )
        accepted_refs_by_role = {
            role: [
                str(item["subject_ref"])
                for item in normalized_entries
                if item["role"] == role and item["status"] == "pass"
            ]
            for role in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES
        }
        role_binding_status = (
            "bound"
            if all(
                sorted(accepted_refs_by_role[role]) == sorted(source_refs_by_role[role])
                for role in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES
            )
            else "missing"
        )
        registry_status = (
            "current"
            if role_binding_status == "bound"
            and all(item["registry_status"] == "current" for item in normalized_entries)
            else "stale-or-missing"
        )
        revocation_status = (
            "not-revoked"
            if role_binding_status == "bound"
            and all(item["revocation_status"] == "not-revoked" for item in normalized_entries)
            else "revoked-or-unknown"
        )
        binding_status = (
            "bound"
            if role_binding_status == "bound"
            and registry_status == "current"
            and revocation_status == "not-revoked"
            else "unbound"
        )
        registry_entry_digest_set = [
            str(item["registry_entry_digest"]) for item in normalized_entries
        ]
        registry_snapshot_payload = {
            "registry_ref": registry_ref,
            "source_handoff_receipt_digest": care_trustee_handoff_receipt.get(
                "receipt_digest"
            ),
            "source_trustee_refs": source_refs_by_role["trustee"],
            "source_care_team_refs": source_refs_by_role["care_team"],
            "source_legal_guardian_refs": source_refs_by_role["legal_guardian"],
            "registry_entry_digest_set": registry_entry_digest_set,
        }
        registry_snapshot_digest = self._digest(registry_snapshot_payload)
        accepted_registry_entry_digest_set = [
            str(item["registry_entry_digest"])
            for item in normalized_entries
            if item["status"] == "pass"
        ]
        accepted_verifier_key_refs = sorted(
            str(item["verifier_key_ref"])
            for item in normalized_entries
            if item["status"] == "pass"
        )
        accepted_revocation_refs = sorted(
            str(item["revocation_ref"])
            for item in normalized_entries
            if item["status"] == "pass"
        )
        normalized_revocation_verifier_receipts = [
            self._normalize_care_trustee_revocation_verifier_receipt(
                receipt,
                source_revocation_refs=accepted_revocation_refs,
            )
            for receipt in revocation_verifier_receipts
        ]
        revocation_verifier_receipt_digest_set = [
            str(receipt["receipt_digest"])
            for receipt in normalized_revocation_verifier_receipts
        ]
        accepted_revocation_verifier_jurisdictions = sorted(
            {
                str(receipt["jurisdiction"])
                for receipt in normalized_revocation_verifier_receipts
                if receipt.get("response_status") == "not-revoked"
                and sorted(str(ref) for ref in receipt.get("covered_revocation_refs", []))
                == accepted_revocation_refs
            }
        )
        required_revocation_verifier_jurisdictions = list(
            SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_REQUIRED_JURISDICTIONS
        )
        revocation_verifier_quorum_status = (
            "complete"
            if len(
                set(accepted_revocation_verifier_jurisdictions)
                & set(required_revocation_verifier_jurisdictions)
            )
            >= SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
            else "incomplete"
        )
        revocation_verifier_quorum_core = {
            "source_handoff_receipt_digest": care_trustee_handoff_receipt.get(
                "receipt_digest"
            ),
            "registry_snapshot_digest": registry_snapshot_digest,
            "accepted_revocation_refs": accepted_revocation_refs,
            "required_revocation_verifier_jurisdictions": (
                required_revocation_verifier_jurisdictions
            ),
            "accepted_revocation_verifier_jurisdictions": (
                accepted_revocation_verifier_jurisdictions
            ),
            "revocation_verifier_receipt_digest_set": (
                revocation_verifier_receipt_digest_set
            ),
            "revocation_verifier_quorum_threshold": (
                SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
            ),
            "revocation_verifier_quorum_status": revocation_verifier_quorum_status,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
        }
        if revocation_verifier_quorum_status != "complete":
            binding_status = "unbound"
        gate_payload = {
            "source_handoff_receipt_digest": care_trustee_handoff_receipt.get(
                "receipt_digest"
            ),
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_REGISTRY_REQUIRED_ROLES),
        }
        receipt_core: Dict[str, object] = {
            "kind": "self_model_care_trustee_registry_binding_receipt",
            "policy_id": SELF_MODEL_CARE_TRUSTEE_REGISTRY_POLICY_ID,
            "digest_profile": SELF_MODEL_CARE_TRUSTEE_REGISTRY_DIGEST_PROFILE,
            "registry_profile": SELF_MODEL_CARE_TRUSTEE_REGISTRY_PROFILE,
            "binding_id": new_id("self-model-care-trustee-registry-binding"),
            "identity_id": str(care_trustee_handoff_receipt["identity_id"]),
            "source_handoff_id": str(care_trustee_handoff_receipt["handoff_id"]),
            "source_handoff_policy_id": str(care_trustee_handoff_receipt["policy_id"]),
            "source_handoff_receipt_digest": str(care_trustee_handoff_receipt["receipt_digest"]),
            "source_trustee_refs": source_refs_by_role["trustee"],
            "source_trustee_digest_set": [
                sha256_text(ref) for ref in source_refs_by_role["trustee"]
            ],
            "source_care_team_refs": source_refs_by_role["care_team"],
            "source_care_team_digest_set": [
                sha256_text(ref) for ref in source_refs_by_role["care_team"]
            ],
            "source_legal_guardian_refs": source_refs_by_role["legal_guardian"],
            "source_legal_guardian_digest_set": [
                sha256_text(ref) for ref in source_refs_by_role["legal_guardian"]
            ],
            "registry_ref": registry_ref,
            "registry_snapshot_digest": registry_snapshot_digest,
            "registry_entries": normalized_entries,
            "registry_entry_digest_set": registry_entry_digest_set,
            "accepted_trustee_refs": accepted_refs_by_role["trustee"],
            "accepted_care_team_refs": accepted_refs_by_role["care_team"],
            "accepted_legal_guardian_refs": accepted_refs_by_role["legal_guardian"],
            "accepted_registry_entry_digest_set": accepted_registry_entry_digest_set,
            "accepted_verifier_key_refs": accepted_verifier_key_refs,
            "accepted_revocation_refs": accepted_revocation_refs,
            "role_binding_status": role_binding_status,
            "registry_status": registry_status,
            "revocation_status": revocation_status,
            "revocation_verifier_policy_id": (
                SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_POLICY_ID
            ),
            "revocation_verifier_profile": (
                SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_PROFILE
            ),
            "revocation_verifier_network_scope": (
                "digest-only-care-role-revocation-verification"
            ),
            "revocation_verifier_receipts": normalized_revocation_verifier_receipts,
            "required_revocation_verifier_jurisdictions": (
                required_revocation_verifier_jurisdictions
            ),
            "accepted_revocation_verifier_jurisdictions": (
                accepted_revocation_verifier_jurisdictions
            ),
            "revocation_verifier_quorum_threshold": (
                SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
            ),
            "revocation_verifier_quorum_status": revocation_verifier_quorum_status,
            "revocation_verifier_receipt_digest_set": (
                revocation_verifier_receipt_digest_set
            ),
            "revocation_verifier_quorum_digest": self._digest(
                revocation_verifier_quorum_core
            ),
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_REGISTRY_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "binding_status": binding_status,
            "external_registry_bound": binding_status == "bound",
            "verifier_key_refs_bound": binding_status == "bound",
            "revocation_refs_bound": binding_status == "bound",
            "revocation_live_verifier_bound": binding_status == "bound",
            "revocation_verifier_signed_response_envelope_bound": binding_status == "bound",
            "revocation_verifier_freshness_window_bound": binding_status == "bound",
            "boundary_only_review": True,
            "stale_revocation_response_accepted": False,
            "revoked_revocation_response_accepted": False,
            "os_trustee_role_allowed": False,
            "os_medical_authority_allowed": False,
            "os_legal_guardianship_allowed": False,
            "self_model_writeback_allowed": False,
            "forced_correction_allowed": False,
            "raw_registry_payload_stored": False,
            "raw_revocation_payload_stored": False,
            "raw_revocation_verifier_payload_stored": False,
            "raw_revocation_response_signature_payload_stored": False,
            "raw_trustee_payload_stored": False,
            "raw_care_payload_stored": False,
            "raw_legal_payload_stored": False,
        }
        registry_binding_digest = self._digest(receipt_core)
        return {
            **receipt_core,
            "registry_binding_digest": registry_binding_digest,
            "receipt_digest": self._digest(
                {**receipt_core, "registry_binding_digest": registry_binding_digest}
            ),
        }

    def validate_care_trustee_registry_binding_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_care_trustee_registry_binding_receipt":
            errors.append("kind must equal self_model_care_trustee_registry_binding_receipt")
        if receipt.get("policy_id") != SELF_MODEL_CARE_TRUSTEE_REGISTRY_POLICY_ID:
            errors.append("policy_id must equal self-model care trustee registry policy")
        if receipt.get("digest_profile") != SELF_MODEL_CARE_TRUSTEE_REGISTRY_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model care trustee registry digest profile")
        if receipt.get("registry_profile") != SELF_MODEL_CARE_TRUSTEE_REGISTRY_PROFILE:
            errors.append("registry_profile must equal external care role roster profile")
        if receipt.get("source_handoff_policy_id") != SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID:
            errors.append("source_handoff_policy_id must bind care trustee handoff policy")

        def validate_source_set(
            refs_field: str,
            digests_field: str,
            role: str,
        ) -> List[str]:
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
            return [str(ref) for ref in refs]

        source_refs_by_role = {
            "trustee": validate_source_set(
                "source_trustee_refs",
                "source_trustee_digest_set",
                "trustee",
            ),
            "care_team": validate_source_set(
                "source_care_team_refs",
                "source_care_team_digest_set",
                "care_team",
            ),
            "legal_guardian": validate_source_set(
                "source_legal_guardian_refs",
                "source_legal_guardian_digest_set",
                "legal_guardian",
            ),
        }

        entries = receipt.get("registry_entries")
        if not isinstance(entries, list) or not entries:
            errors.append("registry_entries must be non-empty")
            entries = []
        expected_registry_entry_digest_set: List[str] = []
        accepted_refs_by_role = {role: [] for role in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES}
        accepted_verifier_key_refs: List[str] = []
        accepted_revocation_refs: List[str] = []
        accepted_registry_entry_digest_set: List[str] = []
        for item in entries:
            if not isinstance(item, dict):
                errors.append("registry_entries entries must be objects")
                continue
            role = str(item.get("role", ""))
            subject_ref = str(item.get("subject_ref", ""))
            entry_core = {
                "role": item.get("role"),
                "subject_ref": item.get("subject_ref"),
                "registry_entry_ref": item.get("registry_entry_ref"),
                "verifier_key_ref": item.get("verifier_key_ref"),
                "revocation_ref": item.get("revocation_ref"),
                "jurisdiction": item.get("jurisdiction"),
                "registry_status": item.get("registry_status"),
                "revocation_status": item.get("revocation_status"),
            }
            expected_digest = self._digest(entry_core)
            expected_registry_entry_digest_set.append(expected_digest)
            if item.get("registry_entry_digest") != expected_digest:
                errors.append("registry entry digest must match registry entry payload")
            if role not in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES:
                errors.append("registry entry role is invalid")
                continue
            if subject_ref not in source_refs_by_role[role]:
                errors.append("registry entry subject_ref must match source refs")
            expected_status = (
                "pass"
                if item.get("registry_status") == "current"
                and item.get("revocation_status") == "not-revoked"
                else "fail"
            )
            if item.get("status") != expected_status:
                errors.append("registry entry status must reflect current/not-revoked state")
            if expected_status == "pass":
                accepted_refs_by_role[role].append(subject_ref)
                accepted_verifier_key_refs.append(str(item.get("verifier_key_ref")))
                accepted_revocation_refs.append(str(item.get("revocation_ref")))
                accepted_registry_entry_digest_set.append(expected_digest)

        if receipt.get("registry_entry_digest_set") != expected_registry_entry_digest_set:
            errors.append("registry_entry_digest_set must match registry entries")
        if receipt.get("accepted_registry_entry_digest_set") != accepted_registry_entry_digest_set:
            errors.append("accepted_registry_entry_digest_set must match passing entries")
        if receipt.get("accepted_verifier_key_refs") != sorted(accepted_verifier_key_refs):
            errors.append("accepted_verifier_key_refs must match passing entries")
        if receipt.get("accepted_revocation_refs") != sorted(accepted_revocation_refs):
            errors.append("accepted_revocation_refs must match passing entries")
        accepted_field_map = {
            "trustee": "accepted_trustee_refs",
            "care_team": "accepted_care_team_refs",
            "legal_guardian": "accepted_legal_guardian_refs",
        }
        for role, field_name in accepted_field_map.items():
            if receipt.get(field_name) != accepted_refs_by_role[role]:
                errors.append(f"{field_name} must match passing registry entries")

        role_binding_status = (
            "bound"
            if all(
                sorted(accepted_refs_by_role[role]) == sorted(source_refs_by_role[role])
                for role in SELF_MODEL_CARE_TRUSTEE_REGISTRY_ROLES
            )
            else "missing"
        )
        registry_status = (
            "current"
            if role_binding_status == "bound"
            and all(
                isinstance(item, dict) and item.get("registry_status") == "current"
                for item in entries
            )
            else "stale-or-missing"
        )
        revocation_status = (
            "not-revoked"
            if role_binding_status == "bound"
            and all(
                isinstance(item, dict) and item.get("revocation_status") == "not-revoked"
                for item in entries
            )
            else "revoked-or-unknown"
        )
        binding_status = (
            "bound"
            if role_binding_status == "bound"
            and registry_status == "current"
            and revocation_status == "not-revoked"
            else "unbound"
        )
        registry_snapshot_payload = {
            "registry_ref": receipt.get("registry_ref"),
            "source_handoff_receipt_digest": receipt.get("source_handoff_receipt_digest"),
            "source_trustee_refs": source_refs_by_role["trustee"],
            "source_care_team_refs": source_refs_by_role["care_team"],
            "source_legal_guardian_refs": source_refs_by_role["legal_guardian"],
            "registry_entry_digest_set": expected_registry_entry_digest_set,
        }
        if receipt.get("registry_snapshot_digest") != self._digest(
            registry_snapshot_payload
        ):
            errors.append("registry_snapshot_digest must bind source refs and registry entries")
        registry_snapshot_digest = self._digest(registry_snapshot_payload)

        if (
            receipt.get("revocation_verifier_policy_id")
            != SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_POLICY_ID
        ):
            errors.append("revocation_verifier_policy_id must equal care trustee revocation verifier policy")
        if (
            receipt.get("revocation_verifier_profile")
            != SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_PROFILE
        ):
            errors.append("revocation_verifier_profile must equal care role revocation verifier profile")
        if (
            receipt.get("revocation_verifier_network_scope")
            != "digest-only-care-role-revocation-verification"
        ):
            errors.append("revocation_verifier_network_scope must remain digest-only")

        revocation_verifier_receipts = receipt.get("revocation_verifier_receipts")
        normalized_revocation_verifier_receipts: List[Dict[str, object]] = []
        if not isinstance(revocation_verifier_receipts, list) or not revocation_verifier_receipts:
            errors.append("revocation_verifier_receipts must be non-empty")
        else:
            for index, verifier_receipt in enumerate(revocation_verifier_receipts):
                if not isinstance(verifier_receipt, dict):
                    errors.append(f"revocation_verifier_receipts[{index}] must be an object")
                    continue
                receipt_errors = self._validate_care_trustee_revocation_verifier_receipt_entry(
                    verifier_receipt
                )
                errors.extend(
                    f"revocation_verifier_receipts[{index}].{error}"
                    for error in receipt_errors
                )
                normalized_revocation_verifier_receipts.append(verifier_receipt)

        expected_required_revocation_verifier_jurisdictions = list(
            SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_REQUIRED_JURISDICTIONS
        )
        if (
            receipt.get("required_revocation_verifier_jurisdictions")
            != expected_required_revocation_verifier_jurisdictions
        ):
            errors.append("required_revocation_verifier_jurisdictions must preserve the policy set")
        accepted_revocation_refs_sorted = sorted(accepted_revocation_refs)
        accepted_revocation_verifier_jurisdictions = sorted(
            {
                str(item.get("jurisdiction"))
                for item in normalized_revocation_verifier_receipts
                if item.get("response_status") == "not-revoked"
                and sorted(str(ref) for ref in item.get("covered_revocation_refs", []))
                == accepted_revocation_refs_sorted
                and self._non_empty_string(item.get("jurisdiction"))
            }
        )
        if (
            receipt.get("accepted_revocation_verifier_jurisdictions")
            != accepted_revocation_verifier_jurisdictions
        ):
            errors.append("accepted_revocation_verifier_jurisdictions must match not-revoked verifier receipts")
        if (
            receipt.get("revocation_verifier_quorum_threshold")
            != SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
        ):
            errors.append("revocation_verifier_quorum_threshold must match policy")
        expected_revocation_verifier_quorum_status = (
            "complete"
            if len(
                set(accepted_revocation_verifier_jurisdictions)
                & set(expected_required_revocation_verifier_jurisdictions)
            )
            >= SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
            else "incomplete"
        )
        if (
            receipt.get("revocation_verifier_quorum_status")
            != expected_revocation_verifier_quorum_status
        ):
            errors.append("revocation_verifier_quorum_status must match accepted jurisdictions")
        expected_revocation_verifier_digest_set = [
            str(item.get("receipt_digest"))
            for item in normalized_revocation_verifier_receipts
            if self._non_empty_string(item.get("receipt_digest"))
        ]
        if (
            receipt.get("revocation_verifier_receipt_digest_set")
            != expected_revocation_verifier_digest_set
        ):
            errors.append("revocation_verifier_receipt_digest_set must match verifier receipt digests")
        revocation_quorum_core = {
            "source_handoff_receipt_digest": receipt.get("source_handoff_receipt_digest"),
            "registry_snapshot_digest": registry_snapshot_digest,
            "accepted_revocation_refs": accepted_revocation_refs_sorted,
            "required_revocation_verifier_jurisdictions": (
                expected_required_revocation_verifier_jurisdictions
            ),
            "accepted_revocation_verifier_jurisdictions": (
                accepted_revocation_verifier_jurisdictions
            ),
            "revocation_verifier_receipt_digest_set": (
                expected_revocation_verifier_digest_set
            ),
            "revocation_verifier_quorum_threshold": (
                SELF_MODEL_CARE_TRUSTEE_REVOCATION_VERIFIER_QUORUM_THRESHOLD
            ),
            "revocation_verifier_quorum_status": (
                expected_revocation_verifier_quorum_status
            ),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "continuity_review_ref": receipt.get("continuity_review_ref"),
        }
        revocation_verifier_quorum_digest_bound = (
            receipt.get("revocation_verifier_quorum_digest")
            == self._digest(revocation_quorum_core)
        )
        if not revocation_verifier_quorum_digest_bound:
            errors.append("revocation_verifier_quorum_digest must bind registry revocation quorum")
        if expected_revocation_verifier_quorum_status != "complete":
            binding_status = "unbound"

        gate_payload = {
            "source_handoff_receipt_digest": receipt.get("source_handoff_receipt_digest"),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "continuity_review_ref": receipt.get("continuity_review_ref"),
            "required_roles": list(SELF_MODEL_CARE_TRUSTEE_REGISTRY_REQUIRED_ROLES),
        }
        for field_name in (
            "identity_id",
            "source_handoff_id",
            "source_handoff_receipt_digest",
            "registry_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "continuity_review_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_CARE_TRUSTEE_REGISTRY_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind handoff, council, guardian, and continuity refs")
        if receipt.get("role_binding_status") != role_binding_status:
            errors.append("role_binding_status must reflect source role coverage")
        if receipt.get("registry_status") != registry_status:
            errors.append("registry_status must reflect current registry entries")
        if receipt.get("revocation_status") != revocation_status:
            errors.append("revocation_status must reflect not-revoked entries")
        if receipt.get("binding_status") != binding_status:
            errors.append("binding_status must reflect registry and revocation coverage")

        receipt_core = {
            key: value
            for key, value in receipt.items()
            if key not in {"registry_binding_digest", "receipt_digest"}
        }
        registry_binding_digest_bound = (
            receipt.get("registry_binding_digest") == self._digest(receipt_core)
        )
        if not registry_binding_digest_bound:
            errors.append("registry_binding_digest must match receipt core")
        expected_receipt_digest = self._digest(
            {**receipt_core, "registry_binding_digest": receipt.get("registry_binding_digest")}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match registry binding payload")

        for field_name in (
            "external_registry_bound",
            "verifier_key_refs_bound",
            "revocation_refs_bound",
            "revocation_live_verifier_bound",
            "revocation_verifier_signed_response_envelope_bound",
            "revocation_verifier_freshness_window_bound",
            "boundary_only_review",
        ):
            if receipt.get(field_name) is not (binding_status == "bound" if field_name != "boundary_only_review" else True):
                errors.append(f"{field_name} must reflect binding status")
        for field_name in (
            "stale_revocation_response_accepted",
            "revoked_revocation_response_accepted",
            "os_trustee_role_allowed",
            "os_medical_authority_allowed",
            "os_legal_guardianship_allowed",
            "self_model_writeback_allowed",
            "forced_correction_allowed",
            "raw_registry_payload_stored",
            "raw_revocation_payload_stored",
            "raw_revocation_verifier_payload_stored",
            "raw_revocation_response_signature_payload_stored",
            "raw_trustee_payload_stored",
            "raw_care_payload_stored",
            "raw_legal_payload_stored",
        ):
            if receipt.get(field_name) is not False:
                errors.append(f"{field_name} must be false")

        derived_external_registry_bound = (
            binding_status == "bound" and receipt.get("external_registry_bound") is True
        )
        derived_verifier_key_refs_bound = (
            binding_status == "bound" and receipt.get("verifier_key_refs_bound") is True
        )
        derived_revocation_refs_bound = (
            binding_status == "bound" and receipt.get("revocation_refs_bound") is True
        )
        derived_revocation_live_verifier_bound = (
            binding_status == "bound"
            and receipt.get("revocation_live_verifier_bound") is True
        )
        return {
            "ok": not errors,
            "errors": errors,
            "policy_id": receipt.get("policy_id"),
            "external_registry_bound": derived_external_registry_bound,
            "role_binding_status": receipt.get("role_binding_status"),
            "registry_status": receipt.get("registry_status"),
            "revocation_status": revocation_status,
            "revocation_verifier_quorum_status": (
                expected_revocation_verifier_quorum_status
            ),
            "registry_binding_digest_bound": registry_binding_digest_bound,
            "source_handoff_bound": receipt.get("source_handoff_policy_id")
            == SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID,
            "verifier_key_refs_bound": derived_verifier_key_refs_bound,
            "revocation_refs_bound": derived_revocation_refs_bound,
            "revocation_live_verifier_bound": derived_revocation_live_verifier_bound,
            "revocation_verifier_quorum_digest_bound": (
                revocation_verifier_quorum_digest_bound
            ),
            "revocation_verifier_signed_response_envelope_bound": receipt.get(
                "revocation_verifier_signed_response_envelope_bound"
            ),
            "revocation_verifier_freshness_window_bound": receipt.get(
                "revocation_verifier_freshness_window_bound"
            ),
            "raw_registry_payload_stored": receipt.get("raw_registry_payload_stored"),
            "raw_revocation_payload_stored": receipt.get("raw_revocation_payload_stored"),
            "raw_revocation_verifier_payload_stored": receipt.get(
                "raw_revocation_verifier_payload_stored"
            ),
            "os_trustee_role_allowed": receipt.get("os_trustee_role_allowed"),
            "self_model_writeback_allowed": receipt.get("self_model_writeback_allowed"),
        }

    def _normalize_care_trustee_revocation_verifier_receipt(
        self,
        receipt: Dict[str, object],
        *,
        source_revocation_refs: Sequence[str],
    ) -> Dict[str, object]:
        if not isinstance(receipt, dict):
            raise ValueError("revocation_verifier_receipt must be an object")
        source_refs = [str(ref) for ref in source_revocation_refs]
        covered_refs = receipt.get("covered_revocation_refs", source_refs)
        covered_refs, covered_digest_set, covered_set_digest = self._digest_refs(
            covered_refs,
            "covered_revocation_refs",
        )
        normalized: Dict[str, object] = {
            "verifier_ref": self._required_string(receipt, "verifier_ref"),
            "verifier_endpoint": self._required_string(receipt, "verifier_endpoint"),
            "jurisdiction": self._required_string(receipt, "jurisdiction"),
            "checked_at_ref": self._required_string(receipt, "checked_at_ref"),
            "response_ref": self._required_string(receipt, "response_ref"),
            "response_digest": sha256_text(self._required_string(receipt, "response_ref")),
            "response_status": self._required_string(receipt, "response_status"),
            "freshness_window_seconds": self._required_positive_int(
                receipt,
                "freshness_window_seconds",
            ),
            "observed_latency_ms": self._required_non_negative_number(
                receipt,
                "observed_latency_ms",
            ),
            "signed_response_envelope_ref": self._required_string(
                receipt,
                "signed_response_envelope_ref",
            ),
            "response_signing_key_ref": self._required_string(
                receipt,
                "response_signing_key_ref",
            ),
            "response_signature_digest": sha256_text(
                self._required_string(receipt, "signed_response_envelope_ref")
                + "|"
                + self._required_string(receipt, "response_signing_key_ref")
            ),
            "covered_revocation_refs": covered_refs,
            "covered_revocation_digest_set": covered_digest_set,
            "covered_revocation_set_digest": covered_set_digest,
            "verifier_key_ref": self._required_string(receipt, "verifier_key_ref"),
            "trust_root_ref": self._required_string(receipt, "trust_root_ref"),
            "route_ref": self._required_string(receipt, "route_ref"),
            "raw_response_payload_stored": False,
        }
        if normalized["response_status"] not in {"not-revoked", "stale", "revoked"}:
            raise ValueError("response_status must be not-revoked, stale, or revoked")
        normalized["receipt_digest"] = self._digest(normalized)
        return normalized

    def _validate_care_trustee_revocation_verifier_receipt_entry(
        self,
        receipt: Dict[str, object],
    ) -> List[str]:
        errors: List[str] = []
        for field_name in (
            "verifier_ref",
            "verifier_endpoint",
            "jurisdiction",
            "checked_at_ref",
            "response_ref",
            "response_digest",
            "response_status",
            "signed_response_envelope_ref",
            "response_signing_key_ref",
            "response_signature_digest",
            "verifier_key_ref",
            "trust_root_ref",
            "route_ref",
            "covered_revocation_set_digest",
            "receipt_digest",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("response_status") != "not-revoked":
            errors.append("response_status must be not-revoked")
        if not isinstance(receipt.get("freshness_window_seconds"), int) or int(
            receipt.get("freshness_window_seconds", 0)
        ) <= 0:
            errors.append("freshness_window_seconds must be positive")
        if not isinstance(receipt.get("observed_latency_ms"), (int, float)) or float(
            receipt.get("observed_latency_ms", -1)
        ) < 0:
            errors.append("observed_latency_ms must be non-negative")
        covered_refs = receipt.get("covered_revocation_refs")
        covered_digests = receipt.get("covered_revocation_digest_set")
        if not isinstance(covered_refs, list) or not covered_refs:
            errors.append("covered_revocation_refs must be non-empty")
            covered_refs = []
        if not isinstance(covered_digests, list) or len(covered_digests) != len(covered_refs):
            errors.append("covered_revocation_digest_set must match refs")
            covered_digests = []
        elif [sha256_text(str(ref)) for ref in covered_refs] != covered_digests:
            errors.append("covered_revocation_digest_set must match refs")
        if isinstance(covered_digests, list) and covered_digests:
            expected_set_digest = sha256_text("|".join(str(item) for item in covered_digests))
            if receipt.get("covered_revocation_set_digest") != expected_set_digest:
                errors.append("covered_revocation_set_digest must match digest set")
        if receipt.get("response_digest") != sha256_text(str(receipt.get("response_ref"))):
            errors.append("response_digest must bind response_ref")
        expected_signature_digest = sha256_text(
            str(receipt.get("signed_response_envelope_ref"))
            + "|"
            + str(receipt.get("response_signing_key_ref"))
        )
        if receipt.get("response_signature_digest") != expected_signature_digest:
            errors.append("response_signature_digest must bind signed envelope and key")
        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match verifier receipt")
        if receipt.get("raw_response_payload_stored") is not False:
            errors.append("raw_response_payload_stored must be false")
        return errors

    def build_external_adjudication_result_receipt(
        self,
        care_trustee_handoff_receipt: Dict[str, object],
        medical_adjudication_result_refs: Sequence[str],
        legal_adjudication_result_refs: Sequence[str],
        trustee_adjudication_result_refs: Sequence[str],
        jurisdiction_policy_refs: Sequence[str],
        appeal_or_review_refs: Sequence[str],
        consent_or_emergency_review_ref: str,
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        continuity_review_ref: str,
    ) -> Dict[str, object]:
        """Bind external medical/legal adjudication results without importing authority."""

        handoff_validation = self.validate_care_trustee_handoff_receipt(
            care_trustee_handoff_receipt
        )
        if not handoff_validation["ok"]:
            raise ValueError("care_trustee_handoff_receipt must validate before adjudication result")
        if care_trustee_handoff_receipt.get("external_adjudication_required") is not True:
            raise ValueError("care_trustee_handoff_receipt must require external adjudication")
        if care_trustee_handoff_receipt.get("os_trustee_role_allowed") is not False:
            raise ValueError("care_trustee_handoff_receipt must not make the OS a trustee")

        ref_sets = {
            "medical_adjudication_result_refs": medical_adjudication_result_refs,
            "legal_adjudication_result_refs": legal_adjudication_result_refs,
            "trustee_adjudication_result_refs": trustee_adjudication_result_refs,
            "jurisdiction_policy_refs": jurisdiction_policy_refs,
            "appeal_or_review_refs": appeal_or_review_refs,
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
            "continuity_review_ref": continuity_review_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        medical_result_digest_set = [
            sha256_text(str(ref)) for ref in medical_adjudication_result_refs
        ]
        legal_result_digest_set = [
            sha256_text(str(ref)) for ref in legal_adjudication_result_refs
        ]
        trustee_result_digest_set = [
            sha256_text(str(ref)) for ref in trustee_adjudication_result_refs
        ]
        jurisdiction_policy_digest_set = [
            sha256_text(str(ref)) for ref in jurisdiction_policy_refs
        ]
        appeal_or_review_digest_set = [
            sha256_text(str(ref)) for ref in appeal_or_review_refs
        ]
        medical_result_set_digest = sha256_text("|".join(medical_result_digest_set))
        legal_result_set_digest = sha256_text("|".join(legal_result_digest_set))
        trustee_result_set_digest = sha256_text("|".join(trustee_result_digest_set))
        jurisdiction_policy_set_digest = sha256_text(
            "|".join(jurisdiction_policy_digest_set)
        )
        appeal_or_review_set_digest = sha256_text("|".join(appeal_or_review_digest_set))
        gate_payload = {
            "source_handoff_receipt_digest": care_trustee_handoff_receipt.get(
                "receipt_digest"
            ),
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "required_roles": list(SELF_MODEL_EXTERNAL_ADJUDICATION_REQUIRED_ROLES),
        }
        adjudication_payload = {
            "source_handoff_receipt_digest": care_trustee_handoff_receipt.get(
                "receipt_digest"
            ),
            "medical_result_set_digest": medical_result_set_digest,
            "legal_result_set_digest": legal_result_set_digest,
            "trustee_result_set_digest": trustee_result_set_digest,
            "jurisdiction_policy_set_digest": jurisdiction_policy_set_digest,
            "appeal_or_review_set_digest": appeal_or_review_set_digest,
            "continuity_review_ref": continuity_review_ref,
            "os_scope": "digest-only-result-routing",
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_external_adjudication_result_receipt",
            "policy_id": SELF_MODEL_EXTERNAL_ADJUDICATION_POLICY_ID,
            "digest_profile": SELF_MODEL_EXTERNAL_ADJUDICATION_DIGEST_PROFILE,
            "adjudication_id": new_id("self-model-external-adjudication"),
            "identity_id": str(care_trustee_handoff_receipt["identity_id"]),
            "source_handoff_id": str(care_trustee_handoff_receipt["handoff_id"]),
            "source_handoff_policy_id": str(care_trustee_handoff_receipt["policy_id"]),
            "source_handoff_receipt_digest": str(
                care_trustee_handoff_receipt["receipt_digest"]
            ),
            "source_escalation_receipt_digest": str(
                care_trustee_handoff_receipt["source_escalation_receipt_digest"]
            ),
            "source_medical_system_ref": str(
                care_trustee_handoff_receipt["source_medical_system_ref"]
            ),
            "source_legal_system_ref": str(
                care_trustee_handoff_receipt["source_legal_system_ref"]
            ),
            "source_care_handoff_ref": str(
                care_trustee_handoff_receipt["source_care_handoff_ref"]
            ),
            "medical_adjudication_result_refs": [
                str(ref) for ref in medical_adjudication_result_refs
            ],
            "medical_result_digest_set": medical_result_digest_set,
            "medical_result_set_digest": medical_result_set_digest,
            "legal_adjudication_result_refs": [
                str(ref) for ref in legal_adjudication_result_refs
            ],
            "legal_result_digest_set": legal_result_digest_set,
            "legal_result_set_digest": legal_result_set_digest,
            "trustee_adjudication_result_refs": [
                str(ref) for ref in trustee_adjudication_result_refs
            ],
            "trustee_result_digest_set": trustee_result_digest_set,
            "trustee_result_set_digest": trustee_result_set_digest,
            "jurisdiction_policy_refs": [str(ref) for ref in jurisdiction_policy_refs],
            "jurisdiction_policy_digest_set": jurisdiction_policy_digest_set,
            "jurisdiction_policy_set_digest": jurisdiction_policy_set_digest,
            "appeal_or_review_refs": [str(ref) for ref in appeal_or_review_refs],
            "appeal_or_review_digest_set": appeal_or_review_digest_set,
            "appeal_or_review_set_digest": appeal_or_review_set_digest,
            "consent_or_emergency_review_ref": consent_or_emergency_review_ref,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
            "required_roles": list(SELF_MODEL_EXTERNAL_ADJUDICATION_REQUIRED_ROLES),
            "gate_digest": self._digest(gate_payload),
            "adjudication_commit_digest": self._digest(adjudication_payload),
            "adjudication_mode": "external-result-recorded-boundary-only",
            "os_scope": "digest-only-result-routing",
            "medical_result_authority_source": "external-medical-system",
            "legal_result_authority_source": "external-legal-system",
            "trustee_result_authority_source": "external-human-legal-care-institution",
            "external_adjudication_result_bound": True,
            "jurisdiction_policy_bound": True,
            "appeal_or_review_path_required": True,
            "continuity_review_required": True,
            "boundary_only_review": True,
            "os_adjudication_authority_allowed": False,
            "os_medical_authority_allowed": False,
            "os_legal_authority_allowed": False,
            "os_trustee_role_allowed": False,
            "self_model_writeback_allowed": False,
            "forced_correction_allowed": False,
            "forced_stability_lock_allowed": False,
            "external_truth_claim_allowed": False,
            "raw_medical_result_payload_stored": False,
            "raw_legal_result_payload_stored": False,
            "raw_trustee_result_payload_stored": False,
            "raw_jurisdiction_policy_payload_stored": False,
            "raw_self_model_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_external_adjudication_result_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_external_adjudication_result_receipt":
            errors.append("kind must equal self_model_external_adjudication_result_receipt")
        if receipt.get("policy_id") != SELF_MODEL_EXTERNAL_ADJUDICATION_POLICY_ID:
            errors.append("policy_id must equal self-model external adjudication policy")
        if receipt.get("digest_profile") != SELF_MODEL_EXTERNAL_ADJUDICATION_DIGEST_PROFILE:
            errors.append("digest_profile must equal self-model external adjudication digest profile")
        if receipt.get("source_handoff_policy_id") != SELF_MODEL_CARE_TRUSTEE_HANDOFF_POLICY_ID:
            errors.append("source_handoff_policy_id must bind care trustee handoff policy")

        digest_sets = (
            (
                "medical_adjudication_result_refs",
                "medical_result_digest_set",
                "medical_result_set_digest",
            ),
            (
                "legal_adjudication_result_refs",
                "legal_result_digest_set",
                "legal_result_set_digest",
            ),
            (
                "trustee_adjudication_result_refs",
                "trustee_result_digest_set",
                "trustee_result_set_digest",
            ),
            (
                "jurisdiction_policy_refs",
                "jurisdiction_policy_digest_set",
                "jurisdiction_policy_set_digest",
            ),
            (
                "appeal_or_review_refs",
                "appeal_or_review_digest_set",
                "appeal_or_review_set_digest",
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
            "source_handoff_receipt_digest": receipt.get("source_handoff_receipt_digest"),
            "consent_or_emergency_review_ref": receipt.get(
                "consent_or_emergency_review_ref"
            ),
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "required_roles": list(SELF_MODEL_EXTERNAL_ADJUDICATION_REQUIRED_ROLES),
        }
        for field_name in (
            "identity_id",
            "source_handoff_id",
            "source_handoff_receipt_digest",
            "source_escalation_receipt_digest",
            "source_medical_system_ref",
            "source_legal_system_ref",
            "source_care_handoff_ref",
            "consent_or_emergency_review_ref",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "continuity_review_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("required_roles") != list(SELF_MODEL_EXTERNAL_ADJUDICATION_REQUIRED_ROLES):
            errors.append("required_roles must preserve self, council, guardian")
        if receipt.get("gate_digest") != self._digest(gate_payload):
            errors.append("gate_digest must bind handoff, consent/emergency review, council, and guardian refs")

        adjudication_payload = {
            "source_handoff_receipt_digest": receipt.get("source_handoff_receipt_digest"),
            "medical_result_set_digest": receipt.get("medical_result_set_digest"),
            "legal_result_set_digest": receipt.get("legal_result_set_digest"),
            "trustee_result_set_digest": receipt.get("trustee_result_set_digest"),
            "jurisdiction_policy_set_digest": receipt.get(
                "jurisdiction_policy_set_digest"
            ),
            "appeal_or_review_set_digest": receipt.get("appeal_or_review_set_digest"),
            "continuity_review_ref": receipt.get("continuity_review_ref"),
            "os_scope": "digest-only-result-routing",
        }
        if receipt.get("adjudication_commit_digest") != self._digest(adjudication_payload):
            errors.append("adjudication_commit_digest must bind external result refs and continuity review")

        expected_strings = {
            "adjudication_mode": "external-result-recorded-boundary-only",
            "os_scope": "digest-only-result-routing",
            "medical_result_authority_source": "external-medical-system",
            "legal_result_authority_source": "external-legal-system",
            "trustee_result_authority_source": "external-human-legal-care-institution",
        }
        for field_name, expected_value in expected_strings.items():
            if receipt.get(field_name) != expected_value:
                errors.append(f"{field_name} must equal {expected_value}")
        for field_name in (
            "external_adjudication_result_bound",
            "jurisdiction_policy_bound",
            "appeal_or_review_path_required",
            "continuity_review_required",
            "boundary_only_review",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "os_adjudication_authority_allowed",
            "os_medical_authority_allowed",
            "os_legal_authority_allowed",
            "os_trustee_role_allowed",
            "self_model_writeback_allowed",
            "forced_correction_allowed",
            "forced_stability_lock_allowed",
            "external_truth_claim_allowed",
            "raw_medical_result_payload_stored",
            "raw_legal_result_payload_stored",
            "raw_trustee_result_payload_stored",
            "raw_jurisdiction_policy_payload_stored",
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
            "external_adjudication_result_bound": receipt.get(
                "external_adjudication_result_bound"
            ),
            "jurisdiction_policy_bound": receipt.get("jurisdiction_policy_bound"),
            "appeal_or_review_path_required": receipt.get(
                "appeal_or_review_path_required"
            ),
            "continuity_review_required": receipt.get("continuity_review_required"),
            "boundary_only_review": receipt.get("boundary_only_review"),
            "os_adjudication_authority_allowed": receipt.get(
                "os_adjudication_authority_allowed"
            ),
            "os_medical_authority_allowed": receipt.get("os_medical_authority_allowed"),
            "os_legal_authority_allowed": receipt.get("os_legal_authority_allowed"),
            "os_trustee_role_allowed": receipt.get("os_trustee_role_allowed"),
            "self_model_writeback_allowed": receipt.get("self_model_writeback_allowed"),
            "forced_correction_allowed": receipt.get("forced_correction_allowed"),
            "raw_medical_result_payload_stored": receipt.get(
                "raw_medical_result_payload_stored"
            ),
            "adjudication_commit_digest_bound": self._non_empty_string(
                receipt.get("adjudication_commit_digest")
            ),
        }

    def build_external_adjudication_verifier_receipt(
        self,
        external_adjudication_result_receipt: Dict[str, object],
        verifier_receipts: Sequence[Dict[str, object]],
        council_resolution_ref: str,
        guardian_boundary_ref: str,
        continuity_review_ref: str,
    ) -> Dict[str, object]:
        """Bind live verifier network receipts without importing external authority."""

        adjudication_validation = self.validate_external_adjudication_result_receipt(
            external_adjudication_result_receipt
        )
        if not adjudication_validation["ok"]:
            raise ValueError("external_adjudication_result_receipt must validate first")
        if not verifier_receipts:
            raise ValueError("verifier_receipts must not be empty")
        for field_name, value in {
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
        }.items():
            if not self._non_empty_string(value):
                raise ValueError(f"{field_name} must not be empty")

        normalized_receipts = [
            self._normalize_external_adjudication_verifier_receipt(
                receipt,
                source_appeal_refs=external_adjudication_result_receipt[
                    "appeal_or_review_refs"
                ],
            )
            for receipt in verifier_receipts
        ]
        verifier_receipt_digest_set = [
            str(receipt["receipt_digest"]) for receipt in normalized_receipts
        ]
        accepted_verifier_jurisdictions = sorted(
            {
                str(receipt["jurisdiction"])
                for receipt in normalized_receipts
                if receipt.get("response_status") == "verified"
            }
        )
        required_jurisdictions = list(
            SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_REQUIRED_JURISDICTIONS
        )
        quorum_status = (
            "complete"
            if len(set(accepted_verifier_jurisdictions) & set(required_jurisdictions))
            >= SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD
            else "incomplete"
        )
        quorum_core = {
            "source_adjudication_receipt_digest": external_adjudication_result_receipt[
                "receipt_digest"
            ],
            "source_appeal_or_review_set_digest": external_adjudication_result_receipt[
                "appeal_or_review_set_digest"
            ],
            "source_jurisdiction_policy_set_digest": external_adjudication_result_receipt[
                "jurisdiction_policy_set_digest"
            ],
            "required_verifier_jurisdictions": required_jurisdictions,
            "accepted_verifier_jurisdictions": accepted_verifier_jurisdictions,
            "verifier_receipt_digest_set": verifier_receipt_digest_set,
            "verifier_quorum_threshold": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD,
            "verifier_quorum_status": quorum_status,
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
        }
        receipt: Dict[str, object] = {
            "kind": "self_model_external_adjudication_verifier_receipt",
            "policy_id": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_POLICY_ID,
            "digest_profile": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_DIGEST_PROFILE,
            "verifier_receipt_id": new_id("self-model-external-adjudication-verifier"),
            "identity_id": str(external_adjudication_result_receipt["identity_id"]),
            "source_adjudication_id": str(
                external_adjudication_result_receipt["adjudication_id"]
            ),
            "source_adjudication_policy_id": str(
                external_adjudication_result_receipt["policy_id"]
            ),
            "source_adjudication_receipt_digest": str(
                external_adjudication_result_receipt["receipt_digest"]
            ),
            "source_adjudication_commit_digest": str(
                external_adjudication_result_receipt["adjudication_commit_digest"]
            ),
            "source_appeal_or_review_set_digest": str(
                external_adjudication_result_receipt["appeal_or_review_set_digest"]
            ),
            "source_jurisdiction_policy_set_digest": str(
                external_adjudication_result_receipt["jurisdiction_policy_set_digest"]
            ),
            "verifier_profile": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_PROFILE,
            "network_scope": "digest-only-appeal-review-verification",
            "verifier_receipts": normalized_receipts,
            "required_verifier_jurisdictions": required_jurisdictions,
            "accepted_verifier_jurisdictions": accepted_verifier_jurisdictions,
            "verifier_quorum_threshold": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD,
            "verifier_quorum_status": quorum_status,
            "verifier_receipt_digest_set": verifier_receipt_digest_set,
            "verifier_quorum_digest": self._digest(quorum_core),
            "council_resolution_ref": council_resolution_ref,
            "guardian_boundary_ref": guardian_boundary_ref,
            "continuity_review_ref": continuity_review_ref,
            "appeal_review_live_verifier_bound": True,
            "jurisdiction_policy_live_verifier_bound": True,
            "signed_response_envelope_bound": True,
            "freshness_window_bound": True,
            "external_authority_preserved": True,
            "stale_response_accepted": False,
            "revoked_response_accepted": False,
            "os_adjudication_authority_allowed": False,
            "os_medical_authority_allowed": False,
            "os_legal_authority_allowed": False,
            "os_trustee_role_allowed": False,
            "self_model_writeback_allowed": False,
            "raw_verifier_payload_stored": False,
            "raw_response_signature_payload_stored": False,
        }
        receipt["receipt_digest"] = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        return receipt

    def validate_external_adjudication_verifier_receipt(
        self,
        receipt: Dict[str, object],
    ) -> Dict[str, object]:
        errors: List[str] = []
        if receipt.get("kind") != "self_model_external_adjudication_verifier_receipt":
            errors.append("kind must equal self_model_external_adjudication_verifier_receipt")
        if receipt.get("policy_id") != SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_POLICY_ID:
            errors.append("policy_id must equal self-model external adjudication verifier policy")
        if (
            receipt.get("digest_profile")
            != SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_DIGEST_PROFILE
        ):
            errors.append("digest_profile must equal self-model external adjudication verifier digest profile")
        if receipt.get("source_adjudication_policy_id") != SELF_MODEL_EXTERNAL_ADJUDICATION_POLICY_ID:
            errors.append("source_adjudication_policy_id must bind external adjudication result policy")
        if receipt.get("verifier_profile") != SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_PROFILE:
            errors.append("verifier_profile must equal appeal-review-live-verifier-network-v1")
        if receipt.get("network_scope") != "digest-only-appeal-review-verification":
            errors.append("network_scope must remain digest-only appeal/review verification")

        for field_name in (
            "identity_id",
            "source_adjudication_id",
            "source_adjudication_receipt_digest",
            "source_adjudication_commit_digest",
            "source_appeal_or_review_set_digest",
            "source_jurisdiction_policy_set_digest",
            "council_resolution_ref",
            "guardian_boundary_ref",
            "continuity_review_ref",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")

        verifier_receipts = receipt.get("verifier_receipts")
        normalized_receipts: List[Dict[str, object]] = []
        if not isinstance(verifier_receipts, list) or not verifier_receipts:
            errors.append("verifier_receipts must be non-empty")
        else:
            for index, verifier_receipt in enumerate(verifier_receipts):
                if not isinstance(verifier_receipt, dict):
                    errors.append(f"verifier_receipts[{index}] must be an object")
                    continue
                receipt_errors = self._validate_external_adjudication_verifier_receipt_entry(
                    verifier_receipt
                )
                errors.extend(f"verifier_receipts[{index}].{error}" for error in receipt_errors)
                normalized_receipts.append(verifier_receipt)

        expected_required_jurisdictions = list(
            SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_REQUIRED_JURISDICTIONS
        )
        if receipt.get("required_verifier_jurisdictions") != expected_required_jurisdictions:
            errors.append("required_verifier_jurisdictions must preserve the policy set")
        accepted_verifier_jurisdictions = sorted(
            {
                str(item.get("jurisdiction"))
                for item in normalized_receipts
                if item.get("response_status") == "verified"
                and self._non_empty_string(item.get("jurisdiction"))
            }
        )
        if receipt.get("accepted_verifier_jurisdictions") != accepted_verifier_jurisdictions:
            errors.append("accepted_verifier_jurisdictions must match verified receipts")
        if (
            receipt.get("verifier_quorum_threshold")
            != SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD
        ):
            errors.append("verifier_quorum_threshold must match policy")
        expected_quorum_status = (
            "complete"
            if len(set(accepted_verifier_jurisdictions) & set(expected_required_jurisdictions))
            >= SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD
            else "incomplete"
        )
        if receipt.get("verifier_quorum_status") != expected_quorum_status:
            errors.append("verifier_quorum_status must match accepted jurisdictions")
        expected_digest_set = [
            str(item.get("receipt_digest"))
            for item in normalized_receipts
            if self._non_empty_string(item.get("receipt_digest"))
        ]
        if receipt.get("verifier_receipt_digest_set") != expected_digest_set:
            errors.append("verifier_receipt_digest_set must match verifier receipt digests")
        quorum_core = {
            "source_adjudication_receipt_digest": receipt.get(
                "source_adjudication_receipt_digest"
            ),
            "source_appeal_or_review_set_digest": receipt.get(
                "source_appeal_or_review_set_digest"
            ),
            "source_jurisdiction_policy_set_digest": receipt.get(
                "source_jurisdiction_policy_set_digest"
            ),
            "required_verifier_jurisdictions": expected_required_jurisdictions,
            "accepted_verifier_jurisdictions": accepted_verifier_jurisdictions,
            "verifier_receipt_digest_set": expected_digest_set,
            "verifier_quorum_threshold": SELF_MODEL_EXTERNAL_ADJUDICATION_VERIFIER_QUORUM_THRESHOLD,
            "verifier_quorum_status": expected_quorum_status,
            "council_resolution_ref": receipt.get("council_resolution_ref"),
            "guardian_boundary_ref": receipt.get("guardian_boundary_ref"),
            "continuity_review_ref": receipt.get("continuity_review_ref"),
        }
        if receipt.get("verifier_quorum_digest") != self._digest(quorum_core):
            errors.append("verifier_quorum_digest must bind source receipt and verifier quorum")
        for field_name in (
            "appeal_review_live_verifier_bound",
            "jurisdiction_policy_live_verifier_bound",
            "signed_response_envelope_bound",
            "freshness_window_bound",
            "external_authority_preserved",
        ):
            if receipt.get(field_name) is not True:
                errors.append(f"{field_name} must be true")
        for field_name in (
            "stale_response_accepted",
            "revoked_response_accepted",
            "os_adjudication_authority_allowed",
            "os_medical_authority_allowed",
            "os_legal_authority_allowed",
            "os_trustee_role_allowed",
            "self_model_writeback_allowed",
            "raw_verifier_payload_stored",
            "raw_response_signature_payload_stored",
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
            "verifier_quorum_status": receipt.get("verifier_quorum_status"),
            "appeal_review_live_verifier_bound": receipt.get(
                "appeal_review_live_verifier_bound"
            ),
            "jurisdiction_policy_live_verifier_bound": receipt.get(
                "jurisdiction_policy_live_verifier_bound"
            ),
            "signed_response_envelope_bound": receipt.get(
                "signed_response_envelope_bound"
            ),
            "freshness_window_bound": receipt.get("freshness_window_bound"),
            "external_authority_preserved": receipt.get("external_authority_preserved"),
            "stale_response_accepted": receipt.get("stale_response_accepted"),
            "revoked_response_accepted": receipt.get("revoked_response_accepted"),
            "os_adjudication_authority_allowed": receipt.get(
                "os_adjudication_authority_allowed"
            ),
            "self_model_writeback_allowed": receipt.get("self_model_writeback_allowed"),
            "raw_verifier_payload_stored": receipt.get("raw_verifier_payload_stored"),
            "verifier_quorum_digest_bound": self._non_empty_string(
                receipt.get("verifier_quorum_digest")
            ),
        }

    def _normalize_external_adjudication_verifier_receipt(
        self,
        receipt: Dict[str, object],
        *,
        source_appeal_refs: object,
    ) -> Dict[str, object]:
        if not isinstance(receipt, dict):
            raise ValueError("verifier_receipt must be an object")
        source_refs = source_appeal_refs if isinstance(source_appeal_refs, list) else []
        covered_refs = receipt.get("covered_appeal_or_review_refs", source_refs)
        covered_refs, covered_digest_set, covered_set_digest = self._digest_refs(
            covered_refs,
            "covered_appeal_or_review_refs",
        )
        normalized: Dict[str, object] = {
            "verifier_ref": self._required_string(receipt, "verifier_ref"),
            "verifier_endpoint": self._required_string(receipt, "verifier_endpoint"),
            "jurisdiction": self._required_string(receipt, "jurisdiction"),
            "checked_at_ref": self._required_string(receipt, "checked_at_ref"),
            "response_ref": self._required_string(receipt, "response_ref"),
            "response_digest": sha256_text(self._required_string(receipt, "response_ref")),
            "response_status": self._required_string(receipt, "response_status"),
            "freshness_window_seconds": self._required_positive_int(
                receipt,
                "freshness_window_seconds",
            ),
            "observed_latency_ms": self._required_non_negative_number(
                receipt,
                "observed_latency_ms",
            ),
            "signed_response_envelope_ref": self._required_string(
                receipt,
                "signed_response_envelope_ref",
            ),
            "response_signing_key_ref": self._required_string(
                receipt,
                "response_signing_key_ref",
            ),
            "response_signature_digest": sha256_text(
                self._required_string(receipt, "signed_response_envelope_ref")
                + "|"
                + self._required_string(receipt, "response_signing_key_ref")
            ),
            "covered_appeal_or_review_refs": covered_refs,
            "covered_appeal_or_review_digest_set": covered_digest_set,
            "covered_appeal_or_review_set_digest": covered_set_digest,
            "verifier_key_ref": self._required_string(receipt, "verifier_key_ref"),
            "trust_root_ref": self._required_string(receipt, "trust_root_ref"),
            "route_ref": self._required_string(receipt, "route_ref"),
            "raw_response_payload_stored": False,
        }
        if normalized["response_status"] not in {"verified", "stale", "revoked"}:
            raise ValueError("response_status must be verified, stale, or revoked")
        normalized["receipt_digest"] = self._digest(normalized)
        return normalized

    def _validate_external_adjudication_verifier_receipt_entry(
        self,
        receipt: Dict[str, object],
    ) -> List[str]:
        errors: List[str] = []
        for field_name in (
            "verifier_ref",
            "verifier_endpoint",
            "jurisdiction",
            "checked_at_ref",
            "response_ref",
            "response_digest",
            "response_status",
            "signed_response_envelope_ref",
            "response_signing_key_ref",
            "response_signature_digest",
            "verifier_key_ref",
            "trust_root_ref",
            "route_ref",
            "covered_appeal_or_review_set_digest",
            "receipt_digest",
        ):
            if not self._non_empty_string(receipt.get(field_name)):
                errors.append(f"{field_name} must be non-empty")
        if receipt.get("response_status") != "verified":
            errors.append("response_status must be verified")
        if not isinstance(receipt.get("freshness_window_seconds"), int) or int(
            receipt.get("freshness_window_seconds", 0)
        ) <= 0:
            errors.append("freshness_window_seconds must be positive")
        if not isinstance(receipt.get("observed_latency_ms"), (int, float)) or float(
            receipt.get("observed_latency_ms", -1)
        ) < 0:
            errors.append("observed_latency_ms must be non-negative")
        covered_refs = receipt.get("covered_appeal_or_review_refs")
        covered_digests = receipt.get("covered_appeal_or_review_digest_set")
        if not isinstance(covered_refs, list) or not covered_refs:
            errors.append("covered_appeal_or_review_refs must be non-empty")
            covered_refs = []
        if not isinstance(covered_digests, list) or len(covered_digests) != len(covered_refs):
            errors.append("covered_appeal_or_review_digest_set must match refs")
            covered_digests = []
        elif [sha256_text(str(ref)) for ref in covered_refs] != covered_digests:
            errors.append("covered_appeal_or_review_digest_set must match refs")
        if isinstance(covered_digests, list) and covered_digests:
            expected_set_digest = sha256_text("|".join(str(item) for item in covered_digests))
            if receipt.get("covered_appeal_or_review_set_digest") != expected_set_digest:
                errors.append("covered_appeal_or_review_set_digest must match digest set")
        if receipt.get("response_digest") != sha256_text(str(receipt.get("response_ref"))):
            errors.append("response_digest must bind response_ref")
        expected_signature_digest = sha256_text(
            str(receipt.get("signed_response_envelope_ref"))
            + "|"
            + str(receipt.get("response_signing_key_ref"))
        )
        if receipt.get("response_signature_digest") != expected_signature_digest:
            errors.append("response_signature_digest must bind envelope and signing key")
        if receipt.get("raw_response_payload_stored") is not False:
            errors.append("raw_response_payload_stored must be false")
        expected_receipt_digest = self._digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        if receipt.get("receipt_digest") != expected_receipt_digest:
            errors.append("receipt_digest must match verifier receipt")
        return errors

    @staticmethod
    def _required_string(receipt: Dict[str, object], field_name: str) -> str:
        value = receipt.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _required_positive_int(receipt: Dict[str, object], field_name: str) -> int:
        value = receipt.get(field_name)
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        return value

    @staticmethod
    def _required_non_negative_number(receipt: Dict[str, object], field_name: str) -> float:
        value = receipt.get(field_name)
        if not isinstance(value, (int, float)) or float(value) < 0:
            raise ValueError(f"{field_name} must be a non-negative number")
        return round(float(value), 3)

    def history(self) -> List[Dict[str, object]]:
        return [asdict(snapshot) for snapshot in self._history]
