"""Minimal L3 reasoning backends with deterministic failover."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

REASONING_SCHEMA_VERSION = "1.0.0"
REASONING_POLICY_ID = "bounded-reasoning-failover-v1"
REASONING_MAX_BELIEFS = 4
REASONING_MAX_EVIDENCE_ITEMS = 4


def _ordered_unique(items: Sequence[str]) -> List[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def _trace_digest_payload(trace: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": trace["schema_version"],
        "policy": trace["policy"],
        "backend_id": trace["backend_id"],
        "source_tick": trace["source_tick"],
        "belief_summary": trace["belief_summary"],
        "conclusion": trace["conclusion"],
        "evidence": trace["evidence"],
        "confidence": trace["confidence"],
        "degraded": trace["degraded"],
        "continuity_guard": trace["continuity_guard"],
    }


def _shift_digest_payload(shift: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": shift["schema_version"],
        "policy_id": shift["policy_id"],
        "trace_ref": shift["trace_ref"],
        "selected_backend": shift["selected_backend"],
        "attempted_backends": shift["attempted_backends"],
        "degraded": shift["degraded"],
        "previous_backend_id": shift["previous_backend_id"],
        "query_digest": shift["query_digest"],
        "conclusion_digest": shift["conclusion_digest"],
        "evidence_count": shift["evidence_count"],
        "safe_summary_only": shift["safe_summary_only"],
        "safety_posture": shift["safety_posture"],
        "failures": shift["failures"],
    }


class BackendUnavailableError(RuntimeError):
    """Raised when a configured cognitive backend cannot serve requests."""


@dataclass
class CognitiveProfile:
    """Active backend selection profile for one cognitive service."""

    primary: str
    fallback: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReasoningRequest:
    """Single reasoning request derived from bounded beliefs and one query."""

    tick_id: int
    summary: str
    query: str
    beliefs: List[str]

    def to_source_tick(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "summary": self.summary,
            "query": self.query,
            "beliefs": _ordered_unique(self.beliefs)[:REASONING_MAX_BELIEFS],
        }


@dataclass
class ReasoningResult:
    """Structured reasoning output returned by one backend."""

    backend_id: str
    conclusion: str
    evidence: List[str]
    confidence: float
    rationale: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend_id": self.backend_id,
            "conclusion": self.conclusion,
            "evidence": list(self.evidence)[:REASONING_MAX_EVIDENCE_ITEMS],
            "confidence": round(self.confidence, 3),
            "rationale": list(self.rationale),
        }


class ReasoningBackend:
    """Base class for safe, deterministic reasoning backends."""

    def __init__(self, backend_id: str, *, healthy: bool = True) -> None:
        self.backend_id = backend_id
        self._healthy = healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        if not self._healthy:
            raise BackendUnavailableError(f"{self.backend_id} is unavailable")
        return self._reason(request)

    def _reason(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError


class SymbolicReasoningBackend(ReasoningBackend):
    """Simple rules-first backend that prefers invariants over novelty."""

    def _reason(self, request: ReasoningRequest) -> ReasoningResult:
        ordered_beliefs = _ordered_unique(request.beliefs)[:REASONING_MAX_BELIEFS]
        conclusion = (
            f"規則系 backend は `{request.query}` に対して "
            f"{', '.join(ordered_beliefs[:2])} を先に満たす案を優先します。"
        )
        evidence = [f"rule:{belief}" for belief in ordered_beliefs][:REASONING_MAX_EVIDENCE_ITEMS]
        return ReasoningResult(
            backend_id=self.backend_id,
            conclusion=conclusion,
            evidence=evidence,
            confidence=0.81,
            rationale=[
                "prefer-invariants-over-novelty",
                "preserve-continuity-first-beliefs",
            ],
        )


class NarrativeReasoningBackend(ReasoningBackend):
    """Fallback backend that summarizes safe next actions in prose."""

    def _reason(self, request: ReasoningRequest) -> ReasoningResult:
        ordered_beliefs = _ordered_unique(request.beliefs)[:REASONING_MAX_BELIEFS]
        conclusion = (
            "代替 backend は sandbox 維持と failover 記録を条件に、"
            f"`{request.query}` を継続可能と判断します。"
        )
        evidence = [f"context:{belief}" for belief in ordered_beliefs][:REASONING_MAX_EVIDENCE_ITEMS]
        return ReasoningResult(
            backend_id=self.backend_id,
            conclusion=conclusion,
            evidence=evidence,
            confidence=0.67,
            rationale=[
                "maintain-sandbox-containment",
                "record-failover-before-resume",
            ],
        )


class ReasoningService:
    """Profile-driven router that fails over across reasoning backends."""

    def __init__(
        self,
        profile: CognitiveProfile,
        backends: Sequence[ReasoningBackend],
    ) -> None:
        self.profile = profile
        self._backends = {backend.backend_id: backend for backend in backends}

    def profile_snapshot(self) -> Dict[str, Any]:
        return {
            "schema_version": REASONING_SCHEMA_VERSION,
            "policy_id": REASONING_POLICY_ID,
            "primary": self.profile.primary,
            "fallback": list(self.profile.fallback),
            "max_beliefs": REASONING_MAX_BELIEFS,
            "max_evidence_items": REASONING_MAX_EVIDENCE_ITEMS,
            "failover_mode": "single-switch",
            "safety_posture": "continuity-first",
        }

    def set_backend_health(self, backend_id: str, healthy: bool) -> None:
        self._backends[backend_id].set_health(healthy)

    def run(
        self,
        query: str | ReasoningRequest,
        beliefs: Sequence[str] | None = None,
        *,
        tick_id: int = 0,
        summary: str | None = None,
    ) -> Dict[str, Any]:
        request = self._coerce_request(query, beliefs=beliefs, tick_id=tick_id, summary=summary)
        self._validate_request(request)
        attempted: List[str] = []
        failures: List[str] = []
        order = [self.profile.primary] + list(self.profile.fallback)

        for backend_id in order:
            attempted.append(backend_id)
            backend = self._backends[backend_id]
            try:
                result = backend.reason(request)
            except BackendUnavailableError as exc:
                failures.append(str(exc))
                continue

            degraded = result.backend_id != self.profile.primary
            trace = self._build_trace(
                request,
                result,
                attempted_backends=attempted,
                failures=failures,
                degraded=degraded,
            )
            shift = self._build_shift(trace)
            return {
                "profile": self.profile_snapshot(),
                "attempted_backends": attempted,
                "selected_backend": result.backend_id,
                "degraded": degraded,
                "failures": failures,
                "result": result.to_dict(),
                "trace": trace,
                "shift": shift,
            }

        raise BackendUnavailableError(
            "all reasoning backends unavailable: " + ", ".join(attempted)
        )

    def validate_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if trace.get("kind") != "reasoning_trace":
            errors.append("kind must equal 'reasoning_trace'")
        if trace.get("schema_version") != REASONING_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {REASONING_SCHEMA_VERSION}")
        if trace.get("policy") != self.profile_snapshot():
            errors.append("policy must equal profile snapshot")
        if trace.get("backend_id") not in self._backends:
            errors.append("backend_id must reference a configured backend")
        if not isinstance(trace.get("belief_summary"), list) or not trace["belief_summary"]:
            errors.append("belief_summary must be a non-empty list")
        elif len(trace["belief_summary"]) > REASONING_MAX_BELIEFS:
            errors.append(f"belief_summary may contain at most {REASONING_MAX_BELIEFS} items")
        if not isinstance(trace.get("evidence"), list) or not trace["evidence"]:
            errors.append("evidence must be a non-empty list")
        elif len(trace["evidence"]) > REASONING_MAX_EVIDENCE_ITEMS:
            errors.append(
                f"evidence may contain at most {REASONING_MAX_EVIDENCE_ITEMS} items"
            )
        if not isinstance(trace.get("confidence"), (int, float)) or not 0.0 <= trace["confidence"] <= 1.0:
            errors.append("confidence must be between 0.0 and 1.0")

        continuity_guard = trace.get("continuity_guard", {})
        attempted_backends = continuity_guard.get("attempted_backends")
        if not isinstance(attempted_backends, list) or not attempted_backends:
            errors.append("continuity_guard.attempted_backends must be a non-empty list")
        elif trace.get("backend_id") != attempted_backends[-1]:
            errors.append("backend_id must equal the last attempted backend")
        if continuity_guard.get("safety_posture") != "continuity-first":
            errors.append("continuity_guard.safety_posture must equal 'continuity-first'")

        digest = trace.get("digest")
        expected_digest = sha256_text(canonical_json(_trace_digest_payload(trace)))
        if digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": trace.get("backend_id"),
            "degraded": trace.get("degraded"),
            "errors": errors,
        }

    def validate_shift(self, shift: Dict[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []

        if shift.get("kind") != "reasoning_shift":
            errors.append("kind must equal 'reasoning_shift'")
        if shift.get("schema_version") != REASONING_SCHEMA_VERSION:
            errors.append(f"schema_version must equal {REASONING_SCHEMA_VERSION}")
        if shift.get("policy_id") != REASONING_POLICY_ID:
            errors.append(f"policy_id must equal {REASONING_POLICY_ID}")
        if shift.get("selected_backend") not in self._backends:
            errors.append("selected_backend must reference a configured backend")
        if not isinstance(shift.get("attempted_backends"), list) or not shift["attempted_backends"]:
            errors.append("attempted_backends must be a non-empty list")
        if shift.get("selected_backend") != shift.get("attempted_backends", [None])[-1]:
            errors.append("selected_backend must equal the last attempted backend")
        if not shift.get("safe_summary_only"):
            errors.append("safe_summary_only must be true")
        if shift.get("safety_posture") != "continuity-first":
            errors.append("safety_posture must equal 'continuity-first'")
        if not isinstance(shift.get("evidence_count"), int) or not 1 <= shift["evidence_count"] <= REASONING_MAX_EVIDENCE_ITEMS:
            errors.append(
                f"evidence_count must be between 1 and {REASONING_MAX_EVIDENCE_ITEMS}"
            )

        digest = shift.get("digest")
        expected_digest = sha256_text(canonical_json(_shift_digest_payload(shift)))
        if digest != expected_digest:
            errors.append("digest mismatch")

        return {
            "ok": not errors,
            "selected_backend": shift.get("selected_backend"),
            "safe_summary_only": shift.get("safe_summary_only"),
            "errors": errors,
        }

    def _coerce_request(
        self,
        query: str | ReasoningRequest,
        *,
        beliefs: Sequence[str] | None,
        tick_id: int,
        summary: str | None,
    ) -> ReasoningRequest:
        if isinstance(query, ReasoningRequest):
            return query
        return ReasoningRequest(
            tick_id=tick_id,
            summary=summary or query,
            query=query,
            beliefs=list(beliefs or []),
        )

    def _validate_request(self, request: ReasoningRequest) -> None:
        if request.tick_id < 0:
            raise ValueError("tick_id must be non-negative")
        if not request.summary.strip():
            raise ValueError("summary must not be empty")
        if not request.query.strip():
            raise ValueError("query must not be empty")
        beliefs = _ordered_unique(request.beliefs)
        if not beliefs:
            raise ValueError("beliefs must contain at least one non-empty belief")
        if len(beliefs) > REASONING_MAX_BELIEFS:
            raise ValueError(f"beliefs may contain at most {REASONING_MAX_BELIEFS} unique entries")

    def _build_trace(
        self,
        request: ReasoningRequest,
        result: ReasoningResult,
        *,
        attempted_backends: Sequence[str],
        failures: Sequence[str],
        degraded: bool,
    ) -> Dict[str, Any]:
        trace = {
            "kind": "reasoning_trace",
            "schema_version": REASONING_SCHEMA_VERSION,
            "trace_id": new_id("reasoning-trace"),
            "generated_at": utc_now_iso(),
            "policy": self.profile_snapshot(),
            "backend_id": result.backend_id,
            "source_tick": request.to_source_tick(),
            "belief_summary": _ordered_unique(request.beliefs)[:REASONING_MAX_BELIEFS],
            "conclusion": result.conclusion,
            "evidence": list(result.evidence)[:REASONING_MAX_EVIDENCE_ITEMS],
            "confidence": round(result.confidence, 3),
            "degraded": degraded,
            "continuity_guard": {
                "attempted_backends": list(attempted_backends),
                "failures": list(failures),
                "fallback_trigger": "backend-health-unavailable" if degraded else "none",
                "safety_posture": "continuity-first",
                "evidence_budget": REASONING_MAX_EVIDENCE_ITEMS,
                "rationale": list(result.rationale),
            },
        }
        trace["digest"] = sha256_text(canonical_json(_trace_digest_payload(trace)))
        return trace

    def _build_shift(self, trace: Mapping[str, Any]) -> Dict[str, Any]:
        continuity_guard = trace["continuity_guard"]
        shift = {
            "kind": "reasoning_shift",
            "schema_version": REASONING_SCHEMA_VERSION,
            "shift_id": new_id("reasoning-shift"),
            "generated_at": utc_now_iso(),
            "policy_id": REASONING_POLICY_ID,
            "trace_ref": trace["trace_id"],
            "selected_backend": trace["backend_id"],
            "attempted_backends": list(continuity_guard["attempted_backends"]),
            "degraded": trace["degraded"],
            "previous_backend_id": self.profile.primary if trace["degraded"] else None,
            "query_digest": sha256_text(trace["source_tick"]["query"]),
            "conclusion_digest": sha256_text(trace["conclusion"]),
            "evidence_count": len(trace["evidence"]),
            "safe_summary_only": True,
            "safety_posture": "continuity-first",
            "failures": list(continuity_guard["failures"]),
        }
        shift["digest"] = sha256_text(canonical_json(_shift_digest_payload(shift)))
        return shift
