"""Deterministic amendment flow for governance-layer changes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, List, Tuple

from ..common import new_id, utc_now_iso

KERNEL_HUMAN_REVIEW_QUORUM = 2
SCHEMA_VERSION = "1.0.0"
TIERS = ("T-Core", "T-Kernel", "T-Operational", "T-Cosmetic")


@dataclass(frozen=True)
class AmendmentSignatures:
    """Approval signals that determine whether one amendment can apply."""

    council: str = "none"
    self_consent: bool = False
    guardian_attested: bool = False
    human_reviewers: int = 0
    design_architect_attested: bool = False


@dataclass(frozen=True)
class AmendmentProposal:
    """Serializable amendment proposal."""

    tier: str
    target_clauses: List[str]
    draft_text_ref: str
    rationale: str
    drafted_by: str
    signatures: AmendmentSignatures
    status: str = "drafted"
    proposal_id: str = ""
    drafted_at: str = ""
    kind: str = "amendment_proposal"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"unsupported amendment tier: {self.tier}")
        if self.signatures.council not in {"none", "majority", "unanimous"}:
            raise ValueError(f"unsupported council signature state: {self.signatures.council}")
        if not self.target_clauses:
            raise ValueError("target_clauses must not be empty")
        if not self.proposal_id:
            object.__setattr__(self, "proposal_id", new_id("amendment"))
        if not self.drafted_at:
            object.__setattr__(self, "drafted_at", utc_now_iso())

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["signatures"] = asdict(self.signatures)
        return payload


class AmendmentService:
    """Reference governance amendment policy."""

    def policy(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "kernel_human_review_quorum": KERNEL_HUMAN_REVIEW_QUORUM,
            "allow_apply_rules": {
                "T-Core": "always-freeze",
                "T-Kernel": "unanimous-council + self-consent + guardian-attested + human-reviewers>=2",
                "T-Operational": "majority-or-better + guardian-attested",
                "T-Cosmetic": "design-architect-attested",
            },
            "initial_apply_stage": {
                "T-Kernel": "dark-launch",
                "T-Operational": "5pct",
                "T-Cosmetic": "100pct",
            },
        }

    def propose(
        self,
        *,
        tier: str,
        target_clauses: List[str],
        draft_text_ref: str,
        rationale: str,
        drafted_by: str,
        signatures: AmendmentSignatures,
    ) -> AmendmentProposal:
        proposal = AmendmentProposal(
            tier=tier,
            target_clauses=target_clauses,
            draft_text_ref=draft_text_ref,
            rationale=rationale,
            drafted_by=drafted_by,
            signatures=signatures,
        )
        return self.attest(proposal, signatures)

    def attest(
        self,
        proposal: AmendmentProposal,
        signatures: AmendmentSignatures,
    ) -> AmendmentProposal:
        status = "drafted"
        if proposal.tier == "T-Core":
            if signatures.council != "none" or signatures.guardian_attested:
                status = "pending-human-review"
        elif proposal.tier == "T-Kernel":
            if signatures.council == "unanimous":
                status = "council-attested"
            if signatures.guardian_attested:
                status = "guardian-attested"
            if signatures.human_reviewers > 0:
                status = "pending-human-review"
        elif proposal.tier == "T-Operational":
            if signatures.council in {"majority", "unanimous"}:
                status = "council-attested"
            if signatures.guardian_attested:
                status = "sandbox-attested"
        elif proposal.tier == "T-Cosmetic" and signatures.design_architect_attested:
            status = "council-attested"

        return replace(proposal, signatures=signatures, status=status)

    def decide(
        self,
        proposal: AmendmentProposal,
        *,
        continuity_event_ref: str,
    ) -> Tuple[AmendmentProposal, Dict[str, Any]]:
        allow_apply, reasons = self._allow_apply(proposal)
        applied_stage = self._applied_stage(proposal.tier, allow_apply)
        status = self._proposal_status(proposal, allow_apply)
        updated = replace(proposal, status=status)
        decision = {
            "kind": "amendment_decision",
            "schema_version": SCHEMA_VERSION,
            "decision_id": new_id("amendment-decision"),
            "proposal_ref": proposal.proposal_id,
            "decided_at": utc_now_iso(),
            "tier": proposal.tier,
            "allow_apply": allow_apply,
            "reasons": reasons,
            "continuity_event_ref": continuity_event_ref,
            "applied_stage": applied_stage,
        }
        return updated, decision

    def _allow_apply(self, proposal: AmendmentProposal) -> Tuple[bool, List[str]]:
        signatures = proposal.signatures
        reasons: List[str] = []

        if proposal.tier == "T-Core":
            reasons.extend(
                [
                    "tier T-Core は reference runtime からは適用できません",
                    "外部の human governance 承認が入るまで freeze します",
                ]
            )
            return False, reasons

        if proposal.tier == "T-Kernel":
            if signatures.council != "unanimous":
                reasons.append("T-Kernel には Council 全会一致が必要です")
            if not signatures.self_consent:
                reasons.append("T-Kernel には本人同意が必要です")
            if not signatures.guardian_attested:
                reasons.append("T-Kernel には Guardian attest が必要です")
            if signatures.human_reviewers < KERNEL_HUMAN_REVIEW_QUORUM:
                reasons.append(
                    f"T-Kernel には human reviewer {KERNEL_HUMAN_REVIEW_QUORUM} 名以上が必要です"
                )
            return not reasons, reasons or ["kernel amendment may progress to guarded rollout"]

        if proposal.tier == "T-Operational":
            if signatures.council not in {"majority", "unanimous"}:
                reasons.append("T-Operational には Council 過半が必要です")
            if not signatures.guardian_attested:
                reasons.append("T-Operational には Guardian attest が必要です")
            return not reasons, reasons or ["operational amendment may progress under guarded rollout"]

        if proposal.tier == "T-Cosmetic":
            if not signatures.design_architect_attested:
                reasons.append("T-Cosmetic には DesignArchitect attest が必要です")
            return not reasons, reasons or ["cosmetic amendment may apply immediately"]

        raise ValueError(f"unsupported amendment tier: {proposal.tier}")

    @staticmethod
    def _applied_stage(tier: str, allow_apply: bool) -> str:
        if not allow_apply:
            return "none"
        if tier == "T-Kernel":
            return "dark-launch"
        if tier == "T-Operational":
            return "5pct"
        return "100pct"

    @staticmethod
    def _proposal_status(proposal: AmendmentProposal, allow_apply: bool) -> str:
        if allow_apply:
            return "applied"
        if proposal.tier == "T-Core":
            return "frozen"
        if proposal.tier == "T-Kernel" and proposal.signatures.human_reviewers < KERNEL_HUMAN_REVIEW_QUORUM:
            return "pending-human-review"
        return "rejected"
