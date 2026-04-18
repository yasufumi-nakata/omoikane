"""Immediate self-termination gate for the reference runtime."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from ..common import new_id, utc_now_iso
from ..substrate.adapter import ClassicalSiliconAdapter
from .continuity import ContinuityLedger
from .identity import IdentityRecord, IdentityRegistry

_NOTIFICATION_AUDIENCES = ("ethics", "guardians", "council")


class TerminationGate:
    """Bounded L1 reference implementation for immediate self-termination."""

    def __init__(
        self,
        identity_registry: IdentityRegistry,
        ledger: ContinuityLedger,
        substrate: ClassicalSiliconAdapter,
    ) -> None:
        self.identity_registry = identity_registry
        self.ledger = ledger
        self.substrate = substrate
        self._outcomes: Dict[str, Dict[str, Any]] = {}
        self._latest_by_identity: Dict[str, str] = {}

    def request(
        self,
        identity_id: str,
        by_self_proof: str,
        reason: str = "",
        *,
        invoke_cool_off: bool = False,
        scheduler_handle_ref: Optional[str] = None,
        active_allocation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_id = new_id("termination-request")
        submitted_at = utc_now_iso()
        request = {
            "kind": "termination_request",
            "schema_version": "1.0.0",
            "request_id": request_id,
            "identity_id": identity_id,
            "by_self_proof": by_self_proof,
            "reason": reason,
            "submitted_at": submitted_at,
            "invoke_cool_off": invoke_cool_off,
        }

        try:
            record = self.identity_registry.get(identity_id)
        except KeyError:
            return self._record_outcome(
                request,
                status="rejected",
                reject_reason="identity-not-found",
                scheduler_handle_cancelled=False,
                substrate_lease_released=False,
                latency_ms=3.0,
                policy=self.policy_snapshot(),
            )

        if not self._verify_self_proof(record, by_self_proof):
            return self._record_outcome(
                request,
                status="rejected",
                reject_reason="invalid-self-proof",
                scheduler_handle_cancelled=False,
                substrate_lease_released=False,
                latency_ms=4.0,
                policy=self._policy_for_record(record),
            )

        policy = self._policy_for_record(record)
        if invoke_cool_off and policy["mode"] == "cool-off-allowed":
            return self._record_outcome(
                request,
                status="cool-off-pending",
                reject_reason="",
                scheduler_handle_cancelled=False,
                substrate_lease_released=False,
                latency_ms=21.0,
                policy=policy,
                scheduler_handle_ref=scheduler_handle_ref,
            )

        self.identity_registry.terminate(identity_id, by_self_proof)
        released = self._release_allocation(active_allocation_id)
        return self._record_outcome(
            request,
            status="completed",
            reject_reason="",
            scheduler_handle_cancelled=True,
            substrate_lease_released=released,
            latency_ms=86.0,
            policy=policy,
            scheduler_handle_ref=scheduler_handle_ref,
            active_allocation_id=active_allocation_id,
        )

    def observe(self, identity_id: str) -> Dict[str, Any]:
        outcome_id = self._latest_by_identity.get(identity_id)
        if outcome_id is None:
            return {
                "kind": "no_termination",
                "identity_id": identity_id,
                "status": "none",
            }

        record = deepcopy(self._outcomes[outcome_id])
        outcome = record["outcome"]
        return {
            "kind": "termination_status",
            "identity_id": identity_id,
            "status": outcome["status"],
            "outcome_id": outcome["outcome_id"],
            "recorded_at": outcome["recorded_at"],
            "policy": record["policy"],
            "request_ref": outcome["request_ref"],
        }

    def policy_snapshot(self) -> Dict[str, Any]:
        return {
            "mode": "immediate-only",
            "latency_budget_ms": {
                "request_to_ledger_append": 10,
                "ledger_to_lease_release": 50,
                "notifications_parallelized": 100,
                "all_complete": 200,
            },
            "cool_off_override": "preconsented-only",
            "notification_audiences": list(_NOTIFICATION_AUDIENCES),
        }

    def validate_outcome(self, outcome: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": (
                (outcome["status"] == "completed" and outcome["latency_ms"] <= 200)
                or outcome["status"] in {"rejected", "cool-off-pending"}
            ),
            "status": outcome["status"],
            "within_budget": outcome["latency_ms"] <= 200,
            "cool_off_pending": outcome["status"] == "cool-off-pending",
            "reject_reason": outcome["reject_reason"],
        }

    def _release_allocation(self, active_allocation_id: Optional[str]) -> bool:
        if active_allocation_id is None:
            return True
        self.substrate.release(active_allocation_id, reason="termination-gate-immediate-release")
        return True

    def _verify_self_proof(self, record: IdentityRecord, by_self_proof: str) -> bool:
        expected = record.metadata.get("termination_self_proof")
        if expected:
            return by_self_proof == expected
        return bool(by_self_proof) and record.identity_id in by_self_proof

    def _policy_for_record(self, record: IdentityRecord) -> Dict[str, Any]:
        days_text = record.metadata.get("termination_policy_days", "0")
        try:
            cool_off_days = int(days_text)
        except ValueError:
            cool_off_days = 0
        return {
            "mode": record.metadata.get("termination_policy_mode", "immediate-only"),
            "cool_off_days": cool_off_days,
            "self_proof_ref": record.metadata.get("termination_self_proof", ""),
        }

    def _record_outcome(
        self,
        request: Dict[str, Any],
        *,
        status: str,
        reject_reason: str,
        scheduler_handle_cancelled: bool,
        substrate_lease_released: bool,
        latency_ms: float,
        policy: Dict[str, Any],
        scheduler_handle_ref: Optional[str] = None,
        active_allocation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        notifications = [
            {"audience": audience, "sent": True}
            for audience in _NOTIFICATION_AUDIENCES
        ]
        outcome = {
            "kind": "termination_outcome",
            "schema_version": "1.0.0",
            "outcome_id": new_id("termination-outcome"),
            "request_ref": request["request_id"],
            "identity_id": request["identity_id"],
            "recorded_at": utc_now_iso(),
            "status": status,
            "reject_reason": reject_reason,
            "ledger_event_ref": "",
            "scheduler_handle_cancelled": scheduler_handle_cancelled,
            "substrate_lease_released": substrate_lease_released,
            "notifications": notifications,
            "latency_ms": latency_ms,
        }

        ledger_entry = self.ledger.append(
            identity_id=request["identity_id"],
            event_type="termination.request.recorded",
            payload={
                "request": deepcopy(request),
                "outcome": dict(outcome),
                "policy": deepcopy(policy),
                "scheduler_handle_ref": scheduler_handle_ref or "",
                "active_allocation_id": active_allocation_id or "",
            },
            actor="TerminationGate",
            category="terminate",
            layer="L1",
            signature_roles=["self", "council", "guardian", "third_party"],
            substrate="classical-silicon",
        )
        outcome["ledger_event_ref"] = ledger_entry.entry_id
        self._outcomes[outcome["outcome_id"]] = {
            "outcome": deepcopy(outcome),
            "request": deepcopy(request),
            "policy": deepcopy(policy),
            "scheduler_handle_ref": scheduler_handle_ref or "",
            "active_allocation_id": active_allocation_id or "",
        }
        self._latest_by_identity[request["identity_id"]] = outcome["outcome_id"]
        return deepcopy(outcome)
