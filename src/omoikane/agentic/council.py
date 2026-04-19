"""Council deliberation reference model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


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


@dataclass
class DistributedCouncilMember:
    """Participant in a bounded Federation or Heritage review."""

    participant_id: str
    role: str
    trust_score: float
    veto_holder: bool = False


@dataclass
class DistributedCouncilVote:
    """One distributed council vote."""

    participant_id: str
    stance: str
    rationale: str


@dataclass
class DistributedCouncilVoteSummary:
    """Aggregated distributed council vote state."""

    participant_count: int
    quorum: int
    approvals: int
    rejections: int
    abstentions: int
    approve_weight: float
    reject_weight: float
    veto_triggered: bool
    veto_holders: List[str]


@dataclass
class DistributedCouncilResolution:
    """Resolved outcome for a Federation, Heritage, or human-governance review."""

    resolution_id: str
    proposal_ref: str
    topology_ref: str
    council_tier: str
    local_outcome: str
    local_binding_status: str
    final_outcome: str
    decision_mode: str
    quorum_policy: Dict[str, Any]
    vote_summary: DistributedCouncilVoteSummary
    participant_votes: List[Dict[str, Any]]
    conflict_resolution: str
    external_resolution_refs: List[str]
    follow_up_action: str
    rationale_trace: List[str]
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_council_resolution",
            "schema_version": "1.0.0",
            "resolution_id": self.resolution_id,
            "proposal_ref": self.proposal_ref,
            "topology_ref": self.topology_ref,
            "council_tier": self.council_tier,
            "local_outcome": self.local_outcome,
            "local_binding_status": self.local_binding_status,
            "final_outcome": self.final_outcome,
            "decision_mode": self.decision_mode,
            "quorum_policy": self.quorum_policy,
            "vote_summary": asdict(self.vote_summary),
            "participant_votes": self.participant_votes,
            "conflict_resolution": self.conflict_resolution,
            "external_resolution_refs": self.external_resolution_refs,
            "follow_up_action": self.follow_up_action,
            "rationale_trace": self.rationale_trace,
            "recorded_at": self.recorded_at,
            "digest": self.digest,
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

    def resolve_federation_review(
        self,
        topology: CouncilTopology,
        *,
        local_decision: CouncilDecision,
        votes: List[DistributedCouncilVote],
    ) -> DistributedCouncilResolution:
        if topology.scope != "cross-self":
            raise ValueError("federation review requires cross-self topology")
        if topology.federation_request.status != "external-pending":
            raise ValueError("federation review requires external-pending request")

        members = self._federation_members(topology.federation_request.participants or [])
        quorum_policy = {
            "policy_id": "federation-shared-reality-v1",
            "quorum": len(topology.federation_request.participants or []) + 1,
            "veto_policy": "self-liaison-unanimous-reject",
            "required_roles": ["self-liaison", "guardian"],
        }
        summary, participant_votes, rationale_trace = self._distributed_vote_state(
            members,
            votes,
            quorum=quorum_policy["quorum"],
        )
        liaison_votes = [
            vote for vote in participant_votes if vote["role"] == "self-liaison"
        ]
        liaison_unanimous_reject = bool(liaison_votes) and all(
            vote["stance"] in {"reject", "veto"} for vote in liaison_votes
        )

        if liaison_unanimous_reject:
            final_outcome = "binding-rejected"
            decision_mode = "liaison-unanimous-reject"
            conflict_resolution = (
                "federation-overrides-local" if local_decision.outcome == "approved" else "none"
            )
            follow_up_action = "reject-cross-self-merge"
        elif summary.approve_weight > summary.reject_weight:
            final_outcome = "binding-approved"
            decision_mode = "weighted-majority"
            conflict_resolution = "none"
            follow_up_action = "execute-federated-review"
        else:
            final_outcome = "binding-rejected"
            decision_mode = "weighted-majority"
            conflict_resolution = (
                "federation-overrides-local" if local_decision.outcome == "approved" else "none"
            )
            follow_up_action = "reject-cross-self-merge"

        return self._build_distributed_resolution(
            proposal_ref=topology.proposal_ref,
            topology_ref=topology.topology_id,
            council_tier="federation",
            local_decision=local_decision,
            local_binding_status="advisory",
            final_outcome=final_outcome,
            decision_mode=decision_mode,
            quorum_policy=quorum_policy,
            vote_summary=summary,
            participant_votes=participant_votes,
            conflict_resolution=conflict_resolution,
            external_resolution_refs=[],
            follow_up_action=follow_up_action,
            rationale_trace=rationale_trace,
        )

    def resolve_heritage_review(
        self,
        topology: CouncilTopology,
        *,
        local_decision: CouncilDecision,
        votes: List[DistributedCouncilVote],
    ) -> DistributedCouncilResolution:
        if topology.scope != "interpretive":
            raise ValueError("heritage review requires interpretive topology")
        if topology.heritage_request.status != "external-pending":
            raise ValueError("heritage review requires external-pending request")

        members = self._heritage_members()
        quorum_policy = {
            "policy_id": "heritage-interpretive-review-v1",
            "quorum": 4,
            "veto_policy": "ethics-committee-single-veto",
            "required_roles": [
                "cultural-representative",
                "cultural-representative",
                "legal-advisor",
                "ethics-committee",
            ],
        }
        summary, participant_votes, rationale_trace = self._distributed_vote_state(
            members,
            votes,
            quorum=quorum_policy["quorum"],
        )
        ethics_veto = any(
            vote["role"] == "ethics-committee" and vote["stance"] == "veto"
            for vote in participant_votes
        )

        if ethics_veto:
            final_outcome = "binding-rejected"
            decision_mode = "ethics-veto"
            conflict_resolution = (
                "heritage-overrides-local" if local_decision.outcome == "approved" else "none"
            )
            follow_up_action = "block-interpretive-change"
        elif summary.approve_weight > summary.reject_weight:
            final_outcome = "binding-approved"
            decision_mode = "weighted-majority"
            conflict_resolution = "none"
            follow_up_action = "apply-heritage-ruling"
        else:
            final_outcome = "binding-rejected"
            decision_mode = "weighted-majority"
            conflict_resolution = (
                "heritage-overrides-local" if local_decision.outcome == "approved" else "none"
            )
            follow_up_action = "block-interpretive-change"

        return self._build_distributed_resolution(
            proposal_ref=topology.proposal_ref,
            topology_ref=topology.topology_id,
            council_tier="heritage",
            local_decision=local_decision,
            local_binding_status="blocked",
            final_outcome=final_outcome,
            decision_mode=decision_mode,
            quorum_policy=quorum_policy,
            vote_summary=summary,
            participant_votes=participant_votes,
            conflict_resolution=conflict_resolution,
            external_resolution_refs=[],
            follow_up_action=follow_up_action,
            rationale_trace=rationale_trace,
        )

    def reconcile_distributed_conflict(
        self,
        proposal_ref: str,
        *,
        local_decision: CouncilDecision,
        federation_resolution: DistributedCouncilResolution,
        heritage_resolution: DistributedCouncilResolution,
    ) -> DistributedCouncilResolution:
        if federation_resolution.final_outcome == heritage_resolution.final_outcome:
            raise ValueError("distributed conflict reconciliation requires divergent external outcomes")

        rationale_trace = [
            "Federation と Heritage の external result が衝突したため local binding を停止する。",
            f"federation={federation_resolution.final_outcome}",
            f"heritage={heritage_resolution.final_outcome}",
        ]
        summary = DistributedCouncilVoteSummary(
            participant_count=0,
            quorum=0,
            approvals=0,
            rejections=0,
            abstentions=0,
            approve_weight=0.0,
            reject_weight=0.0,
            veto_triggered=False,
            veto_holders=[],
        )
        return self._build_distributed_resolution(
            proposal_ref=proposal_ref,
            topology_ref="human-governance://distributed-conflict",
            council_tier="human-governance",
            local_decision=local_decision,
            local_binding_status="human-escalation",
            final_outcome="escalate-human-governance",
            decision_mode="conflict-escalation",
            quorum_policy={
                "policy_id": "distributed-council-conflict-v1",
                "quorum": 0,
                "veto_policy": "human-governance-arbitration",
                "required_roles": ["human-governance"],
            },
            vote_summary=summary,
            participant_votes=[],
            conflict_resolution="escalated-to-human-governance",
            external_resolution_refs=[
                federation_resolution.resolution_id,
                heritage_resolution.resolution_id,
            ],
            follow_up_action="request-human-governance-review",
            rationale_trace=rationale_trace,
        )

    @staticmethod
    def _federation_members(participants: List[str]) -> Dict[str, DistributedCouncilMember]:
        members: Dict[str, DistributedCouncilMember] = {}
        for index, participant in enumerate(participants):
            members[participant] = DistributedCouncilMember(
                participant_id=participant,
                role="self-liaison",
                trust_score=round(0.72 + (0.04 / max(len(participants), 1)) - (index * 0.02), 2),
                veto_holder=True,
            )
        members["guardian://neutral-federation"] = DistributedCouncilMember(
            participant_id="guardian://neutral-federation",
            role="guardian",
            trust_score=0.91,
        )
        return members

    @staticmethod
    def _heritage_members() -> Dict[str, DistributedCouncilMember]:
        return {
            "heritage://culture-a": DistributedCouncilMember(
                participant_id="heritage://culture-a",
                role="cultural-representative",
                trust_score=0.73,
            ),
            "heritage://culture-b": DistributedCouncilMember(
                participant_id="heritage://culture-b",
                role="cultural-representative",
                trust_score=0.71,
            ),
            "heritage://legal-advisor": DistributedCouncilMember(
                participant_id="heritage://legal-advisor",
                role="legal-advisor",
                trust_score=0.78,
            ),
            "heritage://ethics-committee": DistributedCouncilMember(
                participant_id="heritage://ethics-committee",
                role="ethics-committee",
                trust_score=0.88,
                veto_holder=True,
            ),
        }

    def _distributed_vote_state(
        self,
        members: Dict[str, DistributedCouncilMember],
        votes: List[DistributedCouncilVote],
        *,
        quorum: int,
    ) -> tuple[DistributedCouncilVoteSummary, List[Dict[str, Any]], List[str]]:
        if set(members) != {vote.participant_id for vote in votes}:
            raise ValueError("distributed votes must cover each required participant exactly once")

        approvals = 0
        rejections = 0
        abstentions = 0
        approve_weight = 0.0
        reject_weight = 0.0
        veto_triggered = False
        veto_holders: List[str] = []
        participant_votes: List[Dict[str, Any]] = []
        rationale_trace: List[str] = []

        for vote in votes:
            member = members[vote.participant_id]
            participant_votes.append(
                {
                    "participant_id": vote.participant_id,
                    "role": member.role,
                    "trust_score": member.trust_score,
                    "stance": vote.stance,
                    "rationale": vote.rationale,
                }
            )
            rationale_trace.append(f"{vote.participant_id}: {vote.stance} - {vote.rationale}")
            if vote.stance == "approve":
                approvals += 1
                approve_weight += member.trust_score
            elif vote.stance in {"reject", "veto"}:
                rejections += 1
                reject_weight += member.trust_score
                if vote.stance == "veto" and member.veto_holder:
                    veto_triggered = True
                    veto_holders.append(vote.participant_id)
            else:
                abstentions += 1

        if approvals + rejections + abstentions < quorum:
            raise ValueError("distributed review did not reach quorum")

        return (
            DistributedCouncilVoteSummary(
                participant_count=approvals + rejections + abstentions,
                quorum=quorum,
                approvals=approvals,
                rejections=rejections,
                abstentions=abstentions,
                approve_weight=round(approve_weight, 3),
                reject_weight=round(reject_weight, 3),
                veto_triggered=veto_triggered,
                veto_holders=veto_holders,
            ),
            participant_votes,
            rationale_trace,
        )

    def _build_distributed_resolution(
        self,
        *,
        proposal_ref: str,
        topology_ref: str,
        council_tier: str,
        local_decision: CouncilDecision,
        local_binding_status: str,
        final_outcome: str,
        decision_mode: str,
        quorum_policy: Dict[str, Any],
        vote_summary: DistributedCouncilVoteSummary,
        participant_votes: List[Dict[str, Any]],
        conflict_resolution: str,
        external_resolution_refs: List[str],
        follow_up_action: str,
        rationale_trace: List[str],
    ) -> DistributedCouncilResolution:
        recorded_at = utc_now_iso()
        digest = sha256_text(
            canonical_json(
                {
                    "proposal_ref": proposal_ref,
                    "topology_ref": topology_ref,
                    "council_tier": council_tier,
                    "local_outcome": local_decision.outcome,
                    "local_binding_status": local_binding_status,
                    "final_outcome": final_outcome,
                    "decision_mode": decision_mode,
                    "quorum_policy": quorum_policy,
                    "vote_summary": asdict(vote_summary),
                    "participant_votes": participant_votes,
                    "conflict_resolution": conflict_resolution,
                    "external_resolution_refs": external_resolution_refs,
                    "follow_up_action": follow_up_action,
                }
            )
        )
        return DistributedCouncilResolution(
            resolution_id=new_id("distributed-council"),
            proposal_ref=proposal_ref,
            topology_ref=topology_ref,
            council_tier=council_tier,
            local_outcome=local_decision.outcome,
            local_binding_status=local_binding_status,
            final_outcome=final_outcome,
            decision_mode=decision_mode,
            quorum_policy=quorum_policy,
            vote_summary=vote_summary,
            participant_votes=participant_votes,
            conflict_resolution=conflict_resolution,
            external_resolution_refs=external_resolution_refs,
            follow_up_action=follow_up_action,
            rationale_trace=rationale_trace,
            recorded_at=recorded_at,
            digest=digest,
        )
