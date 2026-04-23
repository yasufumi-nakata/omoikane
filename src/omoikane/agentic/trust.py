"""Deterministic trust scoring for the reference agent roster."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any, Dict, List, Optional

from ..common import new_id, utc_now_iso


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)


def _actor_fingerprint(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


@dataclass(frozen=True)
class TrustThresholds:
    """Operational trust floors used by the reference runtime."""

    council_invite_floor: float = 0.5
    weighted_vote_floor: float = 0.6
    apply_floor: float = 0.8
    self_modify_floor: float = 0.95
    guardian_floor: float = 0.99
    guardian_requires_human_pin: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrustUpdatePolicy:
    """Fixed trust update policy for the reference runtime."""

    policy_id: str = "reference-v0"
    provenance_policy_id: str = "reference-trust-provenance-v1"
    initial_score: float = 0.3
    base_deltas: Dict[str, float] = field(
        default_factory=lambda: {
            "council_quality_positive": 0.04,
            "guardian_audit_pass": 0.06,
            "human_feedback_good": 0.05,
            "guardian_veto": -0.12,
            "regression_detected": -0.08,
            "human_feedback_bad": -0.10,
            "ethics_violation": -0.25,
        }
    )
    severity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
    )
    event_origin_requirements: Dict[str, str] = field(
        default_factory=lambda: {
            "council_quality_positive": "council",
            "guardian_audit_pass": "guardian",
            "human_feedback_good": "human",
            "guardian_veto": "guardian",
            "regression_detected": "any",
            "human_feedback_bad": "human",
            "ethics_violation": "any",
        }
    )
    blocked_positive_reciprocity_scope: str = "registered-agent-domain-history"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustEvent:
    """One audited trust update attempt."""

    event_id: str
    agent_id: str
    domain: str
    event_type: str
    severity: str
    evidence_confidence: float
    raw_delta: float
    applied_delta: float
    applied: bool
    triggered_by: str
    triggered_by_agent_id: str
    rationale: str
    global_before: float
    global_after: float
    domain_before: float
    domain_after: float
    policy_id: str
    provenance_status: str
    provenance_policy_id: str
    recorded_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTrustState:
    """Serializable trust state for one agent."""

    agent_id: str
    global_score: float
    per_domain: Dict[str, float] = field(default_factory=dict)
    history: List[TrustEvent] = field(default_factory=list)
    pinned_by_human: bool = False
    pinned_reason: str = ""

    def to_dict(self, thresholds: TrustThresholds) -> Dict[str, Any]:
        per_domain = {key: _clamp_score(value) for key, value in sorted(self.per_domain.items())}
        self_modify_score = per_domain.get("self_modify", _clamp_score(self.global_score))
        return {
            "kind": "trust_snapshot",
            "schema_version": "1.0.0",
            "agent_id": self.agent_id,
            "global_score": _clamp_score(self.global_score),
            "per_domain": per_domain,
            "history": [event.to_dict() for event in self.history],
            "pinned_by_human": self.pinned_by_human,
            "pinned_reason": self.pinned_reason,
            "thresholds": thresholds.to_dict(),
            "eligibility": {
                "invite_to_council": self.global_score >= thresholds.council_invite_floor,
                "count_for_weighted_vote": self.global_score >= thresholds.weighted_vote_floor,
                "apply_to_runtime": self.global_score >= thresholds.apply_floor,
                "self_modify_role": (
                    self.global_score >= thresholds.self_modify_floor
                    and self_modify_score >= thresholds.self_modify_floor
                ),
                "guardian_role": (
                    self.global_score >= thresholds.guardian_floor
                    and (not thresholds.guardian_requires_human_pin or self.pinned_by_human)
                ),
            },
        }


class TrustService:
    """Reference trust registry with deterministic scoring and human pinning."""

    def __init__(
        self,
        *,
        policy: Optional[TrustUpdatePolicy] = None,
        thresholds: Optional[TrustThresholds] = None,
    ) -> None:
        self._policy = policy or TrustUpdatePolicy()
        self._thresholds = thresholds or TrustThresholds()
        self._states: Dict[str, AgentTrustState] = {}

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "policy": self._policy.to_dict(),
            "thresholds": self._thresholds.to_dict(),
        }

    def register_agent(
        self,
        agent_id: str,
        *,
        initial_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        pinned_by_human: bool = False,
        pinned_reason: str = "",
    ) -> Dict[str, Any]:
        score = _clamp_score(
            self._policy.initial_score if initial_score is None else float(initial_score)
        )
        domain_scores = {
            name: _clamp_score(value)
            for name, value in sorted((per_domain or {}).items())
            if name.strip()
        }
        state = AgentTrustState(
            agent_id=agent_id,
            global_score=score,
            per_domain=domain_scores,
            pinned_by_human=pinned_by_human,
            pinned_reason=pinned_reason,
        )
        self._states[agent_id] = state
        return state.to_dict(self._thresholds)

    def snapshot(self, agent_id: str) -> Dict[str, Any]:
        return self._state(agent_id).to_dict(self._thresholds)

    def has_agent(self, agent_id: str) -> bool:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        return agent_key in self._states

    def all_snapshots(self) -> List[Dict[str, Any]]:
        return [self._states[agent_id].to_dict(self._thresholds) for agent_id in sorted(self._states)]

    def pin_agent(
        self,
        agent_id: str,
        *,
        global_score: Optional[float] = None,
        per_domain: Optional[Dict[str, float]] = None,
        reason: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = True
        state.pinned_reason = reason
        if global_score is not None:
            state.global_score = _clamp_score(float(global_score))
        if per_domain:
            for domain, score in per_domain.items():
                if domain.strip():
                    state.per_domain[domain] = _clamp_score(float(score))
        return state.to_dict(self._thresholds)

    def unpin_agent(self, agent_id: str) -> Dict[str, Any]:
        state = self._state(agent_id)
        state.pinned_by_human = False
        state.pinned_reason = ""
        return state.to_dict(self._thresholds)

    def record_event(
        self,
        agent_id: str,
        *,
        event_type: str,
        domain: str,
        severity: str = "medium",
        evidence_confidence: float = 1.0,
        triggered_by: str,
        rationale: str,
    ) -> Dict[str, Any]:
        state = self._state(agent_id)
        normalized_agent = self._normalize_non_empty(agent_id, "agent_id")
        normalized_domain = self._normalize_non_empty(domain, "domain")
        normalized_trigger = self._normalize_non_empty(triggered_by, "triggered_by")
        normalized_rationale = self._normalize_non_empty(rationale, "rationale")

        if event_type not in self._policy.base_deltas:
            raise ValueError(f"unsupported trust event_type: {event_type}")
        if severity not in self._policy.severity_multipliers:
            raise ValueError(f"unsupported trust severity: {severity}")
        if not 0.0 <= evidence_confidence <= 1.0:
            raise ValueError("evidence_confidence must be between 0.0 and 1.0")

        base_delta = self._policy.base_deltas[event_type]
        multiplier = self._policy.severity_multipliers[severity]
        raw_delta = round(base_delta * multiplier * evidence_confidence, 3)
        triggered_by_agent_id = self._resolve_registered_agent_id(normalized_trigger)
        provenance_status = self._evaluate_provenance(
            agent_id=normalized_agent,
            event_type=event_type,
            domain=normalized_domain,
            raw_delta=raw_delta,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
        )
        global_before = _clamp_score(state.global_score)
        domain_before = _clamp_score(state.per_domain.get(normalized_domain, state.global_score))

        if provenance_status != "accepted":
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        elif state.pinned_by_human:
            applied = False
            applied_delta = 0.0
            global_after = global_before
            domain_after = domain_before
        else:
            applied = True
            applied_delta = raw_delta
            global_after = _clamp_score(global_before + raw_delta)
            domain_after = _clamp_score(domain_before + raw_delta)
            state.global_score = global_after
            state.per_domain[normalized_domain] = domain_after

        event = TrustEvent(
            event_id=new_id("trust-event"),
            agent_id=agent_id,
            domain=normalized_domain,
            event_type=event_type,
            severity=severity,
            evidence_confidence=round(evidence_confidence, 3),
            raw_delta=raw_delta,
            applied_delta=applied_delta,
            applied=applied,
            triggered_by=normalized_trigger,
            triggered_by_agent_id=triggered_by_agent_id,
            rationale=normalized_rationale,
            global_before=global_before,
            global_after=global_after,
            domain_before=domain_before,
            domain_after=domain_after,
            policy_id=self._policy.policy_id,
            provenance_status=provenance_status,
            provenance_policy_id=self._policy.provenance_policy_id,
        )
        state.history.append(event)
        return event.to_dict()

    def _state(self, agent_id: str) -> AgentTrustState:
        agent_key = self._normalize_non_empty(agent_id, "agent_id")
        if agent_key not in self._states:
            self.register_agent(agent_key)
        return self._states[agent_key]

    def _evaluate_provenance(
        self,
        *,
        agent_id: str,
        event_type: str,
        domain: str,
        raw_delta: float,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        if raw_delta <= 0:
            return self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)

        if self._same_actor(agent_id, triggered_by, triggered_by_agent_id):
            return "blocked-self-issued-positive"

        origin_status = self._check_event_origin(event_type, triggered_by, triggered_by_agent_id)
        if origin_status != "accepted":
            return origin_status

        if triggered_by_agent_id and self._has_reciprocal_positive_history(
            agent_id=agent_id,
            evaluator_agent_id=triggered_by_agent_id,
            domain=domain,
        ):
            return "blocked-reciprocal-positive"
        return "accepted"

    def _check_event_origin(
        self,
        event_type: str,
        triggered_by: str,
        triggered_by_agent_id: str,
    ) -> str:
        expected_origin = self._policy.event_origin_requirements.get(event_type, "any")
        if expected_origin == "any":
            return "accepted"
        if expected_origin == "council":
            return "accepted" if _actor_fingerprint(triggered_by) == "council" else "blocked-provenance-mismatch"
        if expected_origin == "guardian":
            if triggered_by_agent_id and self._is_guardian_authority(triggered_by_agent_id):
                return "accepted"
            return "blocked-provenance-mismatch"
        if expected_origin == "human":
            if _actor_fingerprint(triggered_by) == "council" or triggered_by_agent_id:
                return "blocked-provenance-mismatch"
            return "accepted"
        return "accepted"

    def _resolve_registered_agent_id(self, actor: str) -> str:
        actor_fingerprint = _actor_fingerprint(actor)
        for registered_agent_id in self._states:
            if _actor_fingerprint(registered_agent_id) == actor_fingerprint:
                return registered_agent_id
        return ""

    def _is_guardian_authority(self, agent_id: str) -> bool:
        state = self._states.get(agent_id)
        if state is None:
            return False
        return bool(state.to_dict(self._thresholds)["eligibility"]["guardian_role"])

    def _has_reciprocal_positive_history(
        self,
        *,
        agent_id: str,
        evaluator_agent_id: str,
        domain: str,
    ) -> bool:
        evaluator_state = self._states.get(evaluator_agent_id)
        if evaluator_state is None:
            return False
        for event in evaluator_state.history:
            if (
                event.domain == domain
                and event.raw_delta > 0
                and event.provenance_status == "accepted"
                and event.triggered_by_agent_id
                and self._same_actor(agent_id, event.triggered_by, event.triggered_by_agent_id)
            ):
                return True
        return False

    @staticmethod
    def _same_actor(agent_id: str, triggered_by: str, triggered_by_agent_id: str) -> bool:
        if triggered_by_agent_id:
            return triggered_by_agent_id == agent_id
        return _actor_fingerprint(agent_id) == _actor_fingerprint(triggered_by)

    @staticmethod
    def _normalize_non_empty(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()
