"""Council deliberation reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from ..common import new_id, utc_now_iso


@dataclass
class CouncilMember:
    """Registered council participant."""

    agent_id: str
    role: str
    trust_score: float
    is_guardian: bool = False


@dataclass
class CouncilProposal:
    """Proposal submitted to the council."""

    proposal_id: str
    title: str
    requested_action: str
    rationale: str
    risk_level: str
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CouncilVote:
    """Single member vote."""

    agent_id: str
    stance: str
    rationale: str


@dataclass
class CouncilDecision:
    """Final council outcome."""

    proposal_id: str
    outcome: str
    approve_weight: float
    reject_weight: float
    recorded_at: str
    rationales: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class Council:
    """Weighted-majority council with guardian veto."""

    def __init__(self) -> None:
        self._members: Dict[str, CouncilMember] = {}
        self._history: List[CouncilDecision] = []

    def register(self, member: CouncilMember) -> None:
        self._members[member.agent_id] = member

    def propose(
        self,
        title: str,
        requested_action: str,
        rationale: str,
        risk_level: str = "medium",
    ) -> CouncilProposal:
        return CouncilProposal(
            proposal_id=new_id("proposal"),
            title=title,
            requested_action=requested_action,
            rationale=rationale,
            risk_level=risk_level,
        )

    def deliberate(self, proposal: CouncilProposal, votes: List[CouncilVote]) -> CouncilDecision:
        approve_weight = 0.0
        reject_weight = 0.0
        rationales: List[str] = []

        for vote in votes:
            member = self._members[vote.agent_id]
            rationales.append(f"{vote.agent_id}: {vote.stance} - {vote.rationale}")
            if vote.stance == "veto" and member.is_guardian:
                decision = CouncilDecision(
                    proposal_id=proposal.proposal_id,
                    outcome="vetoed",
                    approve_weight=approve_weight,
                    reject_weight=reject_weight + member.trust_score,
                    recorded_at=utc_now_iso(),
                    rationales=rationales,
                )
                self._history.append(decision)
                return decision
            if vote.stance == "approve":
                approve_weight += member.trust_score
            elif vote.stance == "reject":
                reject_weight += member.trust_score
            elif vote.stance == "veto":
                reject_weight += member.trust_score

        if approve_weight > reject_weight:
            outcome = "approved"
        elif reject_weight > approve_weight:
            outcome = "rejected"
        else:
            outcome = "escalated"

        decision = CouncilDecision(
            proposal_id=proposal.proposal_id,
            outcome=outcome,
            approve_weight=round(approve_weight, 3),
            reject_weight=round(reject_weight, 3),
            recorded_at=utc_now_iso(),
            rationales=rationales,
        )
        self._history.append(decision)
        return decision

    def history(self) -> List[Dict[str, object]]:
        return [decision.to_dict() for decision in self._history]

