"""Identity lifecycle management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


IDENTITY_CONFIRMATION_POLICY_ID = "multidimensional-identity-confirmation-v1"
IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID = "identity-self-report-witness-consistency-v1"
IDENTITY_CONFIRMATION_AGGREGATE_THRESHOLD = 0.85
IDENTITY_CONFIRMATION_WITNESS_QUORUM = 2
IDENTITY_CONFIRMATION_REQUIRED_WITNESS_ROLES = ("clinician", "guardian")
IDENTITY_CONFIRMATION_MAX_SELF_WITNESS_SCORE_DELTA = 0.12
IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS = {
    "episodic_recall": 0.85,
    "self_model_alignment": 0.80,
    "subjective_self_report": 0.85,
    "third_party_witness_alignment": 0.80,
}


@dataclass
class ForkApprovals:
    """Triple-signature approval set required for a fork."""

    self_signed: bool
    third_party_signed: bool
    legal_signed: bool

    def is_complete(self) -> bool:
        return self.self_signed and self.third_party_signed and self.legal_signed


@dataclass
class IdentityRecord:
    """Tracked identity in the reference runtime."""

    identity_id: str
    lineage_id: str
    consent_proof: str
    created_at: str
    status: str = "active"
    parent_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    terminated_at: Optional[str] = None
    pause_state: Optional["PauseState"] = None


@dataclass
class PauseState:
    """Most recent bounded pause/resume cycle for one identity."""

    paused_at: str
    pause_reason: str
    pause_authority: str
    council_resolution_ref: Optional[str] = None
    resumed_at: Optional[str] = None
    resume_self_proof_ref: Optional[str] = None


@dataclass(frozen=True)
class IdentityConfirmationDimension:
    """One scored dimension in the bounded identity confirmation profile."""

    dimension_id: str
    source_ref: str
    score: float
    threshold: float
    status: str
    evidence_digest: str


@dataclass(frozen=True)
class IdentityWitnessReceipt:
    """Digest-bound third-party witness observation for identity confirmation."""

    witness_id: str
    witness_role: str
    observation_ref: str
    alignment_score: float
    threshold: float
    status: str
    evidence_digest: str


class IdentityRegistry:
    """Reference implementation of the L1 IdentityRegistry."""

    def __init__(self) -> None:
        self._records: Dict[str, IdentityRecord] = {}

    def create(
        self,
        human_consent_proof: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        identity_id = new_id("id")
        record = IdentityRecord(
            identity_id=identity_id,
            lineage_id=identity_id,
            consent_proof=human_consent_proof,
            created_at=utc_now_iso(),
            metadata=metadata or {},
        )
        self._records[identity_id] = record
        return record

    def get(self, identity_id: str) -> IdentityRecord:
        try:
            return self._records[identity_id]
        except KeyError as exc:
            raise KeyError(f"unknown identity: {identity_id}") from exc

    def fork(
        self,
        identity_id: str,
        justification: str,
        approvals: ForkApprovals,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        parent = self.get(identity_id)
        if parent.status != "active":
            raise ValueError("cannot fork a non-active identity")
        if not approvals.is_complete():
            raise PermissionError("fork requires self, third-party, and legal approval")

        child_id = new_id("fork")
        record = IdentityRecord(
            identity_id=child_id,
            lineage_id=parent.lineage_id,
            consent_proof=justification,
            created_at=utc_now_iso(),
            parent_id=parent.identity_id,
            metadata=metadata or {},
        )
        self._records[child_id] = record
        return record

    def create_collective(
        self,
        member_ids: List[str],
        consent_proof: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> IdentityRecord:
        if len(member_ids) < 2:
            raise ValueError("collective identity requires at least two member identities")

        normalized_members: List[str] = []
        for member_id in member_ids:
            member = self.get(member_id)
            if member.status != "active":
                raise ValueError("cannot form a collective from a non-active identity")
            if member.identity_id not in normalized_members:
                normalized_members.append(member.identity_id)

        if len(normalized_members) < 2:
            raise ValueError("collective identity requires two unique active member identities")

        collective_id = new_id("collective")
        collective_metadata = {
            "identity_kind": "collective",
            "member_ids": ",".join(normalized_members),
            **(metadata or {}),
        }
        record = IdentityRecord(
            identity_id=collective_id,
            lineage_id=collective_id,
            consent_proof=consent_proof,
            created_at=utc_now_iso(),
            metadata=collective_metadata,
        )
        self._records[collective_id] = record
        return record

    def pause(
        self,
        identity_id: str,
        *,
        requested_by: str,
        reason: str,
        council_resolution_ref: Optional[str] = None,
    ) -> IdentityRecord:
        normalized_requester = requested_by.strip()
        if normalized_requester not in {"self", "council"}:
            raise ValueError("requested_by must be self or council")
        normalized_reason = reason.strip()
        if not normalized_reason:
            raise ValueError("reason is required for pause")
        normalized_resolution_ref = (
            council_resolution_ref.strip() if isinstance(council_resolution_ref, str) else None
        )
        if normalized_requester == "council" and not normalized_resolution_ref:
            raise PermissionError("council pause requires council_resolution_ref")
        if normalized_requester == "self" and normalized_resolution_ref:
            raise ValueError("self pause must not include council_resolution_ref")

        record = self.get(identity_id)
        if record.status != "active":
            raise ValueError("can only pause an active identity")

        record.status = "paused"
        record.pause_state = PauseState(
            paused_at=utc_now_iso(),
            pause_reason=normalized_reason,
            pause_authority=normalized_requester,
            council_resolution_ref=normalized_resolution_ref,
        )
        return record

    def resume(
        self,
        identity_id: str,
        *,
        self_proof: str,
    ) -> IdentityRecord:
        normalized_self_proof = self_proof.strip()
        if not normalized_self_proof:
            raise PermissionError("self proof is required for resume")

        record = self.get(identity_id)
        if record.status != "paused":
            raise ValueError("can only resume a paused identity")
        if record.pause_state is None:
            raise ValueError("paused identity must carry pause_state metadata")

        record.status = "active"
        record.pause_state.resumed_at = utc_now_iso()
        record.pause_state.resume_self_proof_ref = normalized_self_proof
        return record

    def confirm_identity(
        self,
        identity_id: str,
        *,
        consent_ref: str,
        scheduler_stage_ref: str,
        episodic_recall_ref: str,
        self_model_ref: str,
        self_report: Dict[str, Any],
        witness_receipts: List[Dict[str, Any]],
        episodic_recall_score: float,
        self_model_alignment_score: float,
    ) -> Dict[str, Any]:
        record = self.get(identity_id)
        normalized_consent_ref = self._non_empty_string(consent_ref, "consent_ref")
        normalized_scheduler_ref = self._non_empty_string(
            scheduler_stage_ref,
            "scheduler_stage_ref",
        )
        normalized_episodic_ref = self._non_empty_string(
            episodic_recall_ref,
            "episodic_recall_ref",
        )
        normalized_self_model_ref = self._non_empty_string(self_model_ref, "self_model_ref")
        normalized_self_report = self._normalize_self_report(self_report)
        normalized_witnesses = [
            self._normalize_witness_receipt(receipt) for receipt in witness_receipts
        ]

        accepted_witnesses = [
            receipt
            for receipt in normalized_witnesses
            if receipt.status == "pass"
        ]
        accepted_roles = sorted({receipt.witness_role for receipt in accepted_witnesses})
        witness_quorum_met = (
            len(accepted_witnesses) >= IDENTITY_CONFIRMATION_WITNESS_QUORUM
            and all(role in accepted_roles for role in IDENTITY_CONFIRMATION_REQUIRED_WITNESS_ROLES)
        )
        if accepted_witnesses:
            third_party_score = round(
                sum(receipt.alignment_score for receipt in accepted_witnesses)
                / len(accepted_witnesses),
                3,
            )
        else:
            third_party_score = 0.0

        dimensions = [
            self._build_confirmation_dimension(
                "episodic_recall",
                normalized_episodic_ref,
                episodic_recall_score,
            ),
            self._build_confirmation_dimension(
                "self_model_alignment",
                normalized_self_model_ref,
                self_model_alignment_score,
            ),
            self._build_confirmation_dimension(
                "subjective_self_report",
                normalized_self_report["report_ref"],
                normalized_self_report["continuity_score"],
                evidence_digest=normalized_self_report["evidence_digest"],
            ),
            self._build_confirmation_dimension(
                "third_party_witness_alignment",
                "witness-quorum://identity-confirmation",
                third_party_score,
            ),
        ]
        dimension_payloads = [asdict(dimension) for dimension in dimensions]
        aggregate_score = round(
            sum(dimension.score for dimension in dimensions) / len(dimensions),
            3,
        )
        all_dimensions_pass = all(dimension.status == "pass" for dimension in dimensions)
        subjective_self_report_bound = (
            normalized_self_report["status"] == "pass"
            and dimensions[2].evidence_digest == normalized_self_report["evidence_digest"]
        )
        self_report_witness_consistency = self._build_self_report_witness_consistency(
            identity_id=record.identity_id,
            lineage_id=record.lineage_id,
            consent_ref=normalized_consent_ref,
            scheduler_stage_ref=normalized_scheduler_ref,
            self_report=normalized_self_report,
            accepted_witnesses=accepted_witnesses,
            witness_quorum_met=witness_quorum_met,
            third_party_score=third_party_score,
        )
        self_report_witness_consistency_bound = (
            self_report_witness_consistency["status"] == "bound"
        )
        active_transition_allowed = (
            all_dimensions_pass
            and subjective_self_report_bound
            and witness_quorum_met
            and self_report_witness_consistency_bound
            and aggregate_score >= IDENTITY_CONFIRMATION_AGGREGATE_THRESHOLD
        )
        result = "passed" if active_transition_allowed else "failed"
        failure_reasons: List[str] = []
        if not all_dimensions_pass:
            failure_reasons.append("dimension-threshold-not-met")
        if not subjective_self_report_bound:
            failure_reasons.append("subjective-self-report-not-bound")
        if not witness_quorum_met:
            failure_reasons.append("third-party-witness-quorum-not-met")
        if not self_report_witness_consistency_bound:
            failure_reasons.append("self-report-witness-consistency-not-bound")
        if aggregate_score < IDENTITY_CONFIRMATION_AGGREGATE_THRESHOLD:
            failure_reasons.append("aggregate-threshold-not-met")

        profile_core = {
            "profile_id": IDENTITY_CONFIRMATION_POLICY_ID,
            "identity_id": record.identity_id,
            "lineage_id": record.lineage_id,
            "transition": "ascending-to-active",
            "consent_ref": normalized_consent_ref,
            "scheduler_stage_ref": normalized_scheduler_ref,
            "required_dimensions": sorted(IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS),
            "dimensions": dimension_payloads,
            "aggregate_score": aggregate_score,
            "aggregate_threshold": IDENTITY_CONFIRMATION_AGGREGATE_THRESHOLD,
            "self_report": normalized_self_report,
            "third_party_witness_receipts": [
                asdict(receipt) for receipt in normalized_witnesses
            ],
            "witness_quorum": {
                "required_count": IDENTITY_CONFIRMATION_WITNESS_QUORUM,
                "accepted_count": len(accepted_witnesses),
                "required_roles": list(IDENTITY_CONFIRMATION_REQUIRED_WITNESS_ROLES),
                "accepted_roles": accepted_roles,
                "status": "met" if witness_quorum_met else "missing",
            },
            "self_report_witness_consistency": self_report_witness_consistency,
            "result": result,
            "active_transition_allowed": active_transition_allowed,
            "failure_action": (
                "none"
                if active_transition_allowed
                else "failed-ascension-or-repeat-ascending"
            ),
            "failure_reasons": failure_reasons,
        }
        confirmation_digest = sha256_text(canonical_json(profile_core))
        return {
            "confirmation_id": new_id("identity-confirmation"),
            "confirmed_at": utc_now_iso(),
            **profile_core,
            "confirmation_digest": confirmation_digest,
        }

    def terminate(self, identity_id: str, self_proof: str) -> IdentityRecord:
        if not self_proof:
            raise PermissionError("self proof is required for termination")

        record = self.get(identity_id)
        record.status = "terminated"
        record.terminated_at = utc_now_iso()
        return record

    def active_records(self) -> List[IdentityRecord]:
        return [record for record in self._records.values() if record.status == "active"]

    def snapshot(self) -> List[Dict[str, Optional[str]]]:
        return [
            {
                "identity_id": record.identity_id,
                "lineage_id": record.lineage_id,
                "status": record.status,
                "parent_id": record.parent_id,
                "created_at": record.created_at,
                "terminated_at": record.terminated_at,
                "pause_state": asdict(record.pause_state) if record.pause_state else None,
            }
            for record in self._records.values()
        ]

    @classmethod
    def validate_identity_confirmation(cls, profile: Dict[str, Any]) -> Dict[str, Any]:
        dimensions = profile.get("dimensions", [])
        witness_quorum = profile.get("witness_quorum", {})
        self_report = profile.get("self_report", {})
        consistency = profile.get("self_report_witness_consistency", {})
        witness_receipts = profile.get("third_party_witness_receipts", [])
        dimension_map = {
            item.get("dimension_id"): item
            for item in dimensions
            if isinstance(item, dict)
        }
        required_dimensions = sorted(IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS)
        all_required_dimensions_present = sorted(dimension_map) == required_dimensions
        all_required_dimensions_pass = all(
            dimension_map.get(dimension_id, {}).get("status") == "pass"
            for dimension_id in required_dimensions
        )
        subjective_self_report_bound = (
            dimension_map.get("subjective_self_report", {}).get("evidence_digest")
            == self_report.get("evidence_digest")
            and self_report.get("status") == "pass"
        )
        third_party_witness_quorum_met = witness_quorum.get("status") == "met"
        accepted_witnesses = [
            receipt
            for receipt in witness_receipts
            if isinstance(receipt, dict) and receipt.get("status") == "pass"
        ]
        accepted_witness_digests = sorted(
            receipt.get("evidence_digest")
            for receipt in accepted_witnesses
            if isinstance(receipt.get("evidence_digest"), str)
        )
        accepted_witness_roles = sorted(
            {
                receipt.get("witness_role")
                for receipt in accepted_witnesses
                if isinstance(receipt.get("witness_role"), str)
            }
        )
        accepted_witness_scores = [
            float(receipt.get("alignment_score"))
            for receipt in accepted_witnesses
            if isinstance(receipt.get("alignment_score"), (int, float))
            and not isinstance(receipt.get("alignment_score"), bool)
        ]
        accepted_witness_mean_score = (
            round(sum(accepted_witness_scores) / len(accepted_witness_scores), 3)
            if accepted_witness_scores
            else 0.0
        )
        self_report_score = self_report.get("continuity_score")
        if not isinstance(self_report_score, (int, float)) or isinstance(self_report_score, bool):
            self_report_score = 0.0
        else:
            self_report_score = round(float(self_report_score), 3)
        observed_score_delta = round(
            abs(self_report_score - accepted_witness_mean_score),
            3,
        )
        score_consistency_status = (
            "consistent"
            if observed_score_delta <= IDENTITY_CONFIRMATION_MAX_SELF_WITNESS_SCORE_DELTA
            else "divergent"
        )
        role_binding_status = (
            "bound" if third_party_witness_quorum_met else "missing"
        )
        consistency_core = (
            {
                key: value
                for key, value in consistency.items()
                if key != "consistency_digest"
            }
            if isinstance(consistency, dict)
            else {}
        )
        consistency_digest_bound = (
            isinstance(consistency, dict)
            and consistency.get("consistency_digest")
            == sha256_text(canonical_json(consistency_core))
        )
        self_report_witness_consistency_bound = (
            isinstance(consistency, dict)
            and consistency.get("policy_id") == IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID
            and consistency.get("self_report_evidence_digest")
            == self_report.get("evidence_digest")
            and consistency.get("accepted_witness_evidence_digest_set")
            == accepted_witness_digests
            and consistency.get("accepted_witness_roles") == accepted_witness_roles
            and consistency.get("required_witness_roles")
            == list(IDENTITY_CONFIRMATION_REQUIRED_WITNESS_ROLES)
            and consistency.get("self_report_score") == self_report_score
            and consistency.get("accepted_witness_mean_score") == accepted_witness_mean_score
            and consistency.get("max_score_delta")
            == IDENTITY_CONFIRMATION_MAX_SELF_WITNESS_SCORE_DELTA
            and consistency.get("observed_score_delta") == observed_score_delta
            and consistency.get("score_consistency_status") == score_consistency_status
            and consistency.get("role_binding_status") == role_binding_status
            and consistency.get("status") == "bound"
            and consistency_digest_bound
        )
        aggregate_threshold_met = (
            profile.get("aggregate_score", 0)
            >= IDENTITY_CONFIRMATION_AGGREGATE_THRESHOLD
        )
        active_transition_allowed = (
            all_required_dimensions_present
            and all_required_dimensions_pass
            and subjective_self_report_bound
            and third_party_witness_quorum_met
            and self_report_witness_consistency_bound
            and aggregate_threshold_met
            and profile.get("result") == "passed"
            and profile.get("active_transition_allowed") is True
        )
        profile_core = {
            key: value
            for key, value in profile.items()
            if key not in {"confirmation_id", "confirmed_at", "confirmation_digest"}
        }
        confirmation_digest_bound = (
            profile.get("confirmation_digest") == sha256_text(canonical_json(profile_core))
        )
        ok = active_transition_allowed and confirmation_digest_bound
        return {
            "ok": ok,
            "policy_id": IDENTITY_CONFIRMATION_POLICY_ID,
            "all_required_dimensions_present": all_required_dimensions_present,
            "all_required_dimensions_pass": all_required_dimensions_pass,
            "subjective_self_report_bound": subjective_self_report_bound,
            "third_party_witness_quorum_met": third_party_witness_quorum_met,
            "self_report_witness_consistency_bound": self_report_witness_consistency_bound,
            "consistency_digest_bound": consistency_digest_bound,
            "aggregate_threshold_met": aggregate_threshold_met,
            "active_transition_allowed": active_transition_allowed,
            "confirmation_digest_bound": confirmation_digest_bound,
        }

    @staticmethod
    def _non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _bounded_score(value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{field_name} must be a number between 0.0 and 1.0")
        score = float(value)
        if score < 0.0 or score > 1.0:
            raise ValueError(f"{field_name} must be between 0.0 and 1.0")
        return round(score, 3)

    @classmethod
    def _normalize_self_report(cls, self_report: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(self_report, dict):
            raise ValueError("self_report must be an object")
        report_ref = cls._non_empty_string(self_report.get("report_ref"), "self_report.report_ref")
        statement = cls._non_empty_string(
            self_report.get("statement"),
            "self_report.statement",
        )
        continuity_score = cls._bounded_score(
            self_report.get("continuity_score"),
            "self_report.continuity_score",
        )
        response_digest = sha256_text(
            canonical_json(
                {
                    "report_ref": report_ref,
                    "statement": statement,
                    "continuity_score": continuity_score,
                }
            )
        )
        threshold = IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS["subjective_self_report"]
        return {
            "report_ref": report_ref,
            "statement_digest": response_digest,
            "continuity_score": continuity_score,
            "threshold": threshold,
            "status": "pass" if continuity_score >= threshold else "fail",
            "evidence_digest": response_digest,
        }

    @classmethod
    def _normalize_witness_receipt(
        cls,
        witness_receipt: Dict[str, Any],
    ) -> IdentityWitnessReceipt:
        if not isinstance(witness_receipt, dict):
            raise ValueError("witness_receipt must be an object")
        witness_id = cls._non_empty_string(
            witness_receipt.get("witness_id"),
            "witness_receipt.witness_id",
        )
        witness_role = cls._non_empty_string(
            witness_receipt.get("witness_role"),
            "witness_receipt.witness_role",
        )
        observation_ref = cls._non_empty_string(
            witness_receipt.get("observation_ref"),
            "witness_receipt.observation_ref",
        )
        alignment_score = cls._bounded_score(
            witness_receipt.get("alignment_score"),
            "witness_receipt.alignment_score",
        )
        threshold = IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS[
            "third_party_witness_alignment"
        ]
        evidence_digest = sha256_text(
            canonical_json(
                {
                    "witness_id": witness_id,
                    "witness_role": witness_role,
                    "observation_ref": observation_ref,
                    "alignment_score": alignment_score,
                }
            )
        )
        return IdentityWitnessReceipt(
            witness_id=witness_id,
            witness_role=witness_role,
            observation_ref=observation_ref,
            alignment_score=alignment_score,
            threshold=threshold,
            status="pass" if alignment_score >= threshold else "fail",
            evidence_digest=evidence_digest,
        )

    @classmethod
    def _build_self_report_witness_consistency(
        cls,
        *,
        identity_id: str,
        lineage_id: str,
        consent_ref: str,
        scheduler_stage_ref: str,
        self_report: Dict[str, Any],
        accepted_witnesses: List[IdentityWitnessReceipt],
        witness_quorum_met: bool,
        third_party_score: float,
    ) -> Dict[str, Any]:
        accepted_witness_digest_set = sorted(
            receipt.evidence_digest for receipt in accepted_witnesses
        )
        accepted_witness_roles = sorted(
            {receipt.witness_role for receipt in accepted_witnesses}
        )
        observed_score_delta = round(
            abs(self_report["continuity_score"] - third_party_score),
            3,
        )
        score_consistency_status = (
            "consistent"
            if observed_score_delta <= IDENTITY_CONFIRMATION_MAX_SELF_WITNESS_SCORE_DELTA
            else "divergent"
        )
        role_binding_status = "bound" if witness_quorum_met else "missing"
        status = (
            "bound"
            if self_report["status"] == "pass"
            and witness_quorum_met
            and score_consistency_status == "consistent"
            else "unbound"
        )
        continuity_subject_ref = f"identity://{identity_id}/ascending-to-active"
        consistency_core = {
            "policy_id": IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID,
            "consistency_profile": "score-delta-and-role-bound-v1",
            "continuity_subject_ref": continuity_subject_ref,
            "continuity_subject_digest": sha256_text(
                canonical_json(
                    {
                        "identity_id": identity_id,
                        "lineage_id": lineage_id,
                        "transition": "ascending-to-active",
                        "consent_ref": consent_ref,
                        "scheduler_stage_ref": scheduler_stage_ref,
                    }
                )
            ),
            "self_report_ref": self_report["report_ref"],
            "self_report_evidence_digest": self_report["evidence_digest"],
            "accepted_witness_evidence_digest_set": accepted_witness_digest_set,
            "accepted_witness_roles": accepted_witness_roles,
            "required_witness_roles": list(IDENTITY_CONFIRMATION_REQUIRED_WITNESS_ROLES),
            "self_report_score": self_report["continuity_score"],
            "accepted_witness_mean_score": third_party_score,
            "max_score_delta": IDENTITY_CONFIRMATION_MAX_SELF_WITNESS_SCORE_DELTA,
            "observed_score_delta": observed_score_delta,
            "score_consistency_status": score_consistency_status,
            "role_binding_status": role_binding_status,
            "status": status,
        }
        return {
            **consistency_core,
            "consistency_digest": sha256_text(canonical_json(consistency_core)),
        }

    @classmethod
    def _build_confirmation_dimension(
        cls,
        dimension_id: str,
        source_ref: str,
        score: Any,
        *,
        evidence_digest: Optional[str] = None,
    ) -> IdentityConfirmationDimension:
        normalized_source_ref = cls._non_empty_string(source_ref, f"{dimension_id}.source_ref")
        normalized_score = cls._bounded_score(score, f"{dimension_id}.score")
        threshold = IDENTITY_CONFIRMATION_DIMENSION_THRESHOLDS[dimension_id]
        normalized_evidence_digest = evidence_digest or sha256_text(
            canonical_json(
                {
                    "dimension_id": dimension_id,
                    "source_ref": normalized_source_ref,
                    "score": normalized_score,
                    "threshold": threshold,
                }
            )
        )
        return IdentityConfirmationDimension(
            dimension_id=dimension_id,
            source_ref=normalized_source_ref,
            score=normalized_score,
            threshold=threshold,
            status="pass" if normalized_score >= threshold else "fail",
            evidence_digest=normalized_evidence_digest,
        )
