"""Simplified ethics enforcement for the reference runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ActionRequest:
    """Action being checked by the ethics layer."""

    action_type: str
    target: str
    actor: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EthicsDecision:
    """Decision emitted by the ethics layer."""

    status: str
    reasons: List[str]


class EthicsEnforcer:
    """Conservative rule engine aligned with the design docs."""

    IMMUTABLE_COMPONENTS = {"EthicsEnforcer", "ContinuityLedger"}

    def check(self, request: ActionRequest) -> EthicsDecision:
        reasons: List[str] = []

        if request.action_type == "fork_identity":
            approvals = request.payload.get("approvals", {})
            required = ["self_signed", "third_party_signed", "legal_signed"]
            missing = [name for name in required if not approvals.get(name)]
            if missing:
                return EthicsDecision(
                    status="Veto",
                    reasons=[f"fork requires triple approval: missing {', '.join(missing)}"],
                )
            return EthicsDecision(status="Approval", reasons=["triple approval confirmed"])

        if request.action_type == "terminate_identity":
            if not request.payload.get("self_proof"):
                return EthicsDecision(
                    status="Veto",
                    reasons=["termination requires self proof"],
                )
            return EthicsDecision(status="Approval", reasons=["self proof confirmed"])

        if request.action_type == "self_modify":
            target_component = request.payload.get("target_component", request.target)
            if target_component in self.IMMUTABLE_COMPONENTS:
                return EthicsDecision(
                    status="Veto",
                    reasons=[f"{target_component} is immutable in the reference runtime"],
                )
            if not request.payload.get("sandboxed", False):
                return EthicsDecision(
                    status="Escalate",
                    reasons=["self modification must first target a sandbox self"],
                )
            if not request.payload.get("guardian_signed", False):
                return EthicsDecision(
                    status="Escalate",
                    reasons=["guardian approval is required for self modification"],
                )
            reasons.append("sandbox and guardian gates satisfied")
            return EthicsDecision(status="Approval", reasons=reasons)

        if request.action_type == "ledger_append" and request.payload.get("rewrite"):
            return EthicsDecision(
                status="Veto",
                reasons=["continuity ledger is append-only"],
            )

        return EthicsDecision(status="Approval", reasons=["no blocking ethics rule matched"])

