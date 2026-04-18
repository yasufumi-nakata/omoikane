"""Council deliberation reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

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
    session_mode: str = "standard"
    target_identity_ids: List[str] = field(default_factory=list)
    referenced_clauses: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class CouncilVote:
    """Single member vote."""

    agent_id: str
    stance: str
    rationale: str


@dataclass
class CouncilSessionPolicy:
    """Bounded session budget and timeout policy."""

    session_mode: str
    soft_timeout_ms: int
    hard_timeout_ms: int
    max_rounds: int
    quorum: int
    soft_timeout_strategy: str
    hard_timeout_strategy: str

    @classmethod
    def for_mode(cls, session_mode: str) -> "CouncilSessionPolicy":
        if session_mode == "expedited":
            return cls(
                session_mode="expedited",
                soft_timeout_ms=250,
                hard_timeout_ms=1000,
                max_rounds=1,
                quorum=2,
                soft_timeout_strategy="fallback-weighted-majority",
                hard_timeout_strategy="defer-and-review",
            )
        if session_mode != "standard":
            raise ValueError(f"unsupported Council session mode: {session_mode}")
        return cls(
            session_mode="standard",
            soft_timeout_ms=45_000,
            hard_timeout_ms=90_000,
            max_rounds=4,
            quorum=3,
            soft_timeout_strategy="fallback-weighted-majority",
            hard_timeout_strategy="human-governance-escalation",
        )


@dataclass
class CouncilVoteSummary:
    """Aggregate vote counts and net weighted score."""

    participant_count: int
    approvals: int
    rejections: int
    abstentions: int
    weighted_score: float


@dataclass
class CouncilTimeoutStatus:
    """How the session budget affected the final verdict."""

    status: str
    elapsed_ms: int
    soft_timeout_ms: int
    hard_timeout_ms: int
    fallback_applied: str
    follow_up_action: str


@dataclass
class CouncilDecision:
    """Final council outcome."""

    proposal_id: str
    session_mode: str
    outcome: str
    decision_mode: str
    approve_weight: float
    reject_weight: float
    recorded_at: str
    rationales: List[str]
    vote_summary: CouncilVoteSummary
    timeout_status: CouncilTimeoutStatus

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CouncilExternalRequest:
    """Convening request sent to an external council tier."""

    convened: bool
    participants: Optional[List[str]] = None
    clauses: Optional[List[str]] = None
    status: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        if self.participants is not None:
            return {
                "convened": self.convened,
                "participants": self.participants,
                "status": self.status,
            }
        return {
            "convened": self.convened,
            "clauses": self.clauses or [],
            "status": self.status,
        }


@dataclass
class CouncilTopology:
    """Serialized routing state for multi-council escalation."""

    topology_id: str
    proposal_ref: str
    scope: str
    local_session_ref: str
    federation_request: CouncilExternalRequest
    heritage_request: CouncilExternalRequest
    resolved_at: str
    conflict_resolution: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "council_topology",
            "schema_version": "1.0.0",
            "topology_id": self.topology_id,
            "proposal_ref": self.proposal_ref,
            "scope": self.scope,
            "local_session_ref": self.local_session_ref,
            "federation_request": self.federation_request.to_dict(),
            "heritage_request": self.heritage_request.to_dict(),
            "resolved_at": self.resolved_at,
            "conflict_resolution": self.conflict_resolution,
        }


class Council:
    """Weighted-majority council with guardian veto."""

    INTERPRETIVE_PREFIXES = ("ethics_axiom", "identity_axiom", "governance")

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
        session_mode: str = "standard",
        *,
        target_identity_ids: Optional[List[str]] = None,
        referenced_clauses: Optional[List[str]] = None,
    ) -> CouncilProposal:
        return CouncilProposal(
            proposal_id=new_id("proposal"),
            title=title,
            requested_action=requested_action,
            rationale=rationale,
            risk_level=risk_level,
            session_mode=session_mode,
            target_identity_ids=list(target_identity_ids or []),
            referenced_clauses=list(referenced_clauses or []),
        )

    @staticmethod
    def session_policy(session_mode: str) -> CouncilSessionPolicy:
        return CouncilSessionPolicy.for_mode(session_mode)

    def deliberate(
        self,
        proposal: CouncilProposal,
        votes: List[CouncilVote],
        *,
        elapsed_ms: Optional[int] = None,
        rounds_completed: int = 1,
    ) -> CouncilDecision:
        policy = self.session_policy(proposal.session_mode)
        elapsed = max(0, elapsed_ms or 0)
        timeout_status = self._timeout_status(policy, elapsed_ms=elapsed, rounds_completed=rounds_completed)
        approve_weight = 0.0
        reject_weight = 0.0
        rationales: List[str] = []
        approvals = 0
        rejections = 0
        abstentions = 0
        guardian_veto = False

        for vote in votes:
            member = self._members[vote.agent_id]
            rationales.append(f"{vote.agent_id}: {vote.stance} - {vote.rationale}")
            if vote.stance == "approve":
                approvals += 1
                approve_weight += member.trust_score
            elif vote.stance == "reject":
                rejections += 1
                reject_weight += member.trust_score
            elif vote.stance == "veto":
                rejections += 1
                reject_weight += member.trust_score
                if member.is_guardian:
                    guardian_veto = True
                    break
            else:
                abstentions += 1

        vote_summary = CouncilVoteSummary(
            participant_count=approvals + rejections + abstentions,
            approvals=approvals,
            rejections=rejections,
            abstentions=abstentions,
            weighted_score=round(approve_weight - reject_weight, 3),
        )

        if guardian_veto:
            timeout_status = CouncilTimeoutStatus(
                status=timeout_status.status,
                elapsed_ms=timeout_status.elapsed_ms,
                soft_timeout_ms=timeout_status.soft_timeout_ms,
                hard_timeout_ms=timeout_status.hard_timeout_ms,
                fallback_applied="guardian-veto",
                follow_up_action="none",
            )
            outcome = "vetoed"
            decision_mode = "expedited" if proposal.session_mode == "expedited" else "weighted-majority"
        elif timeout_status.status == "hard-timeout":
            if proposal.session_mode == "expedited":
                outcome = "deferred"
                decision_mode = "expedited"
                timeout_status = CouncilTimeoutStatus(
                    status=timeout_status.status,
                    elapsed_ms=timeout_status.elapsed_ms,
                    soft_timeout_ms=timeout_status.soft_timeout_ms,
                    hard_timeout_ms=timeout_status.hard_timeout_ms,
                    fallback_applied="defer-and-review",
                    follow_up_action="schedule-standard-session",
                )
            else:
                outcome = "escalated"
                decision_mode = "timeout-escalation"
                timeout_status = CouncilTimeoutStatus(
                    status=timeout_status.status,
                    elapsed_ms=timeout_status.elapsed_ms,
                    soft_timeout_ms=timeout_status.soft_timeout_ms,
                    hard_timeout_ms=timeout_status.hard_timeout_ms,
                    fallback_applied="human-governance-escalation",
                    follow_up_action="escalate-to-human-governance",
                )
        elif timeout_status.status == "soft-timeout":
            if vote_summary.participant_count >= policy.quorum and approve_weight != reject_weight:
                outcome = "approved" if approve_weight > reject_weight else "rejected"
                decision_mode = "timeout-fallback"
                timeout_status = CouncilTimeoutStatus(
                    status=timeout_status.status,
                    elapsed_ms=timeout_status.elapsed_ms,
                    soft_timeout_ms=timeout_status.soft_timeout_ms,
                    hard_timeout_ms=timeout_status.hard_timeout_ms,
                    fallback_applied="weighted-majority",
                    follow_up_action="record-resolution",
                )
            elif proposal.session_mode == "expedited":
                outcome = "deferred"
                decision_mode = "expedited"
                timeout_status = CouncilTimeoutStatus(
                    status=timeout_status.status,
                    elapsed_ms=timeout_status.elapsed_ms,
                    soft_timeout_ms=timeout_status.soft_timeout_ms,
                    hard_timeout_ms=timeout_status.hard_timeout_ms,
                    fallback_applied="defer-and-review",
                    follow_up_action="schedule-standard-session",
                )
            else:
                outcome = "escalated"
                decision_mode = "timeout-escalation"
                timeout_status = CouncilTimeoutStatus(
                    status=timeout_status.status,
                    elapsed_ms=timeout_status.elapsed_ms,
                    soft_timeout_ms=timeout_status.soft_timeout_ms,
                    hard_timeout_ms=timeout_status.hard_timeout_ms,
                    fallback_applied="human-governance-escalation",
                    follow_up_action="escalate-to-human-governance",
                )
        else:
            if approve_weight > reject_weight:
                outcome = "approved"
                decision_mode = "weighted-majority"
            elif reject_weight > approve_weight:
                outcome = "rejected"
                decision_mode = "weighted-majority"
            else:
                outcome = "escalated"
                decision_mode = "consensus"
            timeout_status = CouncilTimeoutStatus(
                status=timeout_status.status,
                elapsed_ms=timeout_status.elapsed_ms,
                soft_timeout_ms=timeout_status.soft_timeout_ms,
                hard_timeout_ms=timeout_status.hard_timeout_ms,
                fallback_applied="none",
                follow_up_action="record-resolution" if outcome in {"approved", "rejected"} else "none",
            )

        decision = CouncilDecision(
            proposal_id=proposal.proposal_id,
            session_mode=proposal.session_mode,
            outcome=outcome,
            decision_mode=decision_mode,
            approve_weight=round(approve_weight, 3),
            reject_weight=round(reject_weight, 3),
            recorded_at=utc_now_iso(),
            rationales=rationales,
            vote_summary=vote_summary,
            timeout_status=timeout_status,
        )
        self._history.append(decision)
        return decision

    @staticmethod
    def _timeout_status(
        policy: CouncilSessionPolicy,
        *,
        elapsed_ms: int,
        rounds_completed: int,
    ) -> CouncilTimeoutStatus:
        if elapsed_ms >= policy.hard_timeout_ms or rounds_completed > policy.max_rounds:
            return CouncilTimeoutStatus(
                status="hard-timeout",
                elapsed_ms=elapsed_ms,
                soft_timeout_ms=policy.soft_timeout_ms,
                hard_timeout_ms=policy.hard_timeout_ms,
                fallback_applied="none",
                follow_up_action="none",
            )
        if elapsed_ms >= policy.soft_timeout_ms:
            return CouncilTimeoutStatus(
                status="soft-timeout",
                elapsed_ms=elapsed_ms,
                soft_timeout_ms=policy.soft_timeout_ms,
                hard_timeout_ms=policy.hard_timeout_ms,
                fallback_applied="none",
                follow_up_action="none",
            )
        return CouncilTimeoutStatus(
            status="within-budget",
            elapsed_ms=elapsed_ms,
            soft_timeout_ms=policy.soft_timeout_ms,
            hard_timeout_ms=policy.hard_timeout_ms,
            fallback_applied="none",
            follow_up_action="none",
        )

    def history(self) -> List[Dict[str, Any]]:
        return [decision.to_dict() for decision in self._history]

    @classmethod
    def classify_scope(cls, proposal: CouncilProposal) -> str:
        unique_targets = sorted(set(proposal.target_identity_ids))
        interpretive = any(
            clause.startswith(prefix)
            for clause in proposal.referenced_clauses
            for prefix in cls.INTERPRETIVE_PREFIXES
        )
        cross_self = len(unique_targets) >= 2
        local = len(unique_targets) == 1 and not interpretive

        if cross_self and interpretive:
            return "ambiguous"
        if cross_self:
            return "cross-self"
        if interpretive:
            return "interpretive"
        if local:
            return "local"
        return "ambiguous"

    def route_topology(self, proposal: CouncilProposal, *, local_session_ref: str) -> CouncilTopology:
        scope = self.classify_scope(proposal)
        participants = sorted(set(proposal.target_identity_ids))
        clauses = [
            clause
            for clause in proposal.referenced_clauses
            if any(clause.startswith(prefix) for prefix in self.INTERPRETIVE_PREFIXES)
        ]

        federation_request = CouncilExternalRequest(
            convened=scope == "cross-self",
            participants=participants if scope == "cross-self" else [],
            status="external-pending" if scope == "cross-self" else "none",
        )
        heritage_request = CouncilExternalRequest(
            convened=scope == "interpretive",
            clauses=clauses if scope == "interpretive" else [],
            status="external-pending" if scope == "interpretive" else "none",
        )

        return CouncilTopology(
            topology_id=new_id("topology"),
            proposal_ref=proposal.proposal_id,
            scope=scope,
            local_session_ref=local_session_ref,
            federation_request=federation_request,
            heritage_request=heritage_request,
            resolved_at=utc_now_iso(),
        )
