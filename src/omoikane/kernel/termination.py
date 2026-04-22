"""Immediate self-termination gate for the reference runtime."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..common import new_id, utc_now_iso
from ..substrate.adapter import ClassicalSiliconAdapter
from .continuity import ContinuityLedger
from .identity import IdentityRecord, IdentityRegistry

if TYPE_CHECKING:
    from .scheduler import AscensionScheduler

_NOTIFICATION_AUDIENCES = ("ethics", "guardians", "council")


class TerminationGate:
    """Bounded L1 reference implementation for immediate self-termination."""

    def __init__(
        self,
        identity_registry: IdentityRegistry,
        ledger: ContinuityLedger,
        substrate: ClassicalSiliconAdapter,
        scheduler: Optional["AscensionScheduler"] = None,
    ) -> None:
        self.identity_registry = identity_registry
        self.ledger = ledger
        self.substrate = substrate
        self.scheduler = scheduler
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
            "scheduler_handle_ref": scheduler_handle_ref or "",
            "active_allocation_id": active_allocation_id or "",
        }

        try:
            record = self.identity_registry.get(identity_id)
        except KeyError:
            return self._record_outcome(
                request,
                status="rejected",
                reject_reason="identity-not-found",
                substrate_lease_released=False,
                latency_ms=3.0,
                policy=self.policy_snapshot(),
                scheduler_cancellation=self._scheduler_cancellation_status(
                    scheduler_handle_ref=scheduler_handle_ref,
                    result="not-requested",
                ),
            )

        if not self._verify_self_proof(record, by_self_proof):
            return self._record_outcome(
                request,
                status="rejected",
                reject_reason="invalid-self-proof",
                substrate_lease_released=False,
                latency_ms=4.0,
                policy=self._policy_for_record(record),
                scheduler_cancellation=self._scheduler_cancellation_status(
                    scheduler_handle_ref=scheduler_handle_ref,
                    result="not-requested",
                ),
            )

        policy = self._policy_for_record(record)
        if invoke_cool_off and policy["mode"] == "cool-off-allowed":
            return self._record_outcome(
                request,
                status="cool-off-pending",
                reject_reason="",
                substrate_lease_released=False,
                latency_ms=21.0,
                policy=policy,
                scheduler_cancellation=self._scheduler_cancellation_status(
                    scheduler_handle_ref=scheduler_handle_ref,
                    result="deferred" if scheduler_handle_ref else "not-requested",
                ),
            )

        self.identity_registry.terminate(identity_id, by_self_proof)
        released = self._release_allocation(active_allocation_id)
        scheduler_cancellation = self._cancel_scheduler_handle(
            scheduler_handle_ref=scheduler_handle_ref,
            reason=reason or "termination gate completed immediate shutdown",
        )
        return self._record_outcome(
            request,
            status="completed",
            reject_reason="",
            substrate_lease_released=released,
            latency_ms=86.0,
            policy=policy,
            scheduler_cancellation=scheduler_cancellation,
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
        scheduler_cancellation = outcome.get(
            "scheduler_cancellation",
            self._scheduler_cancellation_status(),
        )
        scheduler_binding_ok = True
        if outcome["status"] == "completed" and outcome.get("scheduler_handle_ref"):
            scheduler_binding_ok = (
                scheduler_cancellation["result"] == "cancelled"
                and outcome["scheduler_handle_cancelled"]
                and scheduler_cancellation["cancel_count"] >= 1
            )
        elif outcome["status"] == "cool-off-pending":
            scheduler_binding_ok = scheduler_cancellation["result"] in {"deferred", "not-requested"}
        elif outcome["status"] == "rejected":
            scheduler_binding_ok = scheduler_cancellation["result"] == "not-requested"
        return {
            "ok": (
                (
                    outcome["status"] == "completed"
                    and outcome["latency_ms"] <= 200
                    and scheduler_binding_ok
                )
                or (
                    outcome["status"] in {"rejected", "cool-off-pending"}
                    and scheduler_binding_ok
                )
            ),
            "status": outcome["status"],
            "within_budget": outcome["latency_ms"] <= 200,
            "cool_off_pending": outcome["status"] == "cool-off-pending",
            "reject_reason": outcome["reject_reason"],
            "scheduler_binding_ok": scheduler_binding_ok,
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

    def _scheduler_cancellation_status(
        self,
        *,
        scheduler_handle_ref: Optional[str] = None,
        requested: bool = False,
        result: str = "not-requested",
        final_status: str = "",
        current_stage: str = "",
        cancel_count: int = 0,
        scenario_labels: Optional[list[str]] = None,
        history_transition: str = "",
        execution_receipt_id: str = "",
        execution_receipt_digest: str = "",
        failure_reason: str = "",
        closed_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "kind": "termination_scheduler_cancellation",
            "handle_id": scheduler_handle_ref or "",
            "requested": requested,
            "result": result,
            "final_status": final_status,
            "current_stage": current_stage,
            "cancel_count": cancel_count,
            "scenario_labels": list(scenario_labels or []),
            "history_transition": history_transition,
            "execution_receipt_id": execution_receipt_id,
            "execution_receipt_digest": execution_receipt_digest,
            "failure_reason": failure_reason,
            "closed_at": closed_at,
        }

    def _cancel_scheduler_handle(
        self,
        *,
        scheduler_handle_ref: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        if not scheduler_handle_ref:
            return self._scheduler_cancellation_status()
        if self.scheduler is None:
            return self._scheduler_cancellation_status(
                scheduler_handle_ref=scheduler_handle_ref,
                requested=True,
                result="scheduler-unavailable",
                failure_reason="termination gate has no scheduler binding",
            )

        try:
            cancelled_handle = self.scheduler.cancel(scheduler_handle_ref, reason)
            execution_receipt = self.scheduler.compile_execution_receipt(scheduler_handle_ref)
        except KeyError:
            return self._scheduler_cancellation_status(
                scheduler_handle_ref=scheduler_handle_ref,
                requested=True,
                result="handle-not-found",
                failure_reason="scheduler handle ref is unknown",
            )
        except ValueError as exc:
            return self._scheduler_cancellation_status(
                scheduler_handle_ref=scheduler_handle_ref,
                requested=True,
                result="cancel-error",
                failure_reason=str(exc),
            )

        return self._scheduler_cancellation_status(
            scheduler_handle_ref=scheduler_handle_ref,
            requested=True,
            result="cancelled" if cancelled_handle["status"] == "cancelled" else "cancel-error",
            final_status=cancelled_handle["status"],
            current_stage=cancelled_handle["current_stage"],
            cancel_count=execution_receipt["cancel_count"],
            scenario_labels=execution_receipt["scenario_labels"],
            history_transition=cancelled_handle["history"][-1]["transition"]
            if cancelled_handle["history"]
            else "",
            execution_receipt_id=execution_receipt["execution_receipt_id"],
            execution_receipt_digest=execution_receipt["receipt_digest"],
            failure_reason="",
            closed_at=cancelled_handle["closed_at"],
        )

    def _record_outcome(
        self,
        request: Dict[str, Any],
        *,
        status: str,
        reject_reason: str,
        substrate_lease_released: bool,
        latency_ms: float,
        policy: Dict[str, Any],
        scheduler_cancellation: Dict[str, Any],
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
            "scheduler_handle_ref": request["scheduler_handle_ref"],
            "ledger_event_ref": "",
            "scheduler_handle_cancelled": scheduler_cancellation["result"] == "cancelled",
            "scheduler_cancellation": deepcopy(scheduler_cancellation),
            "active_allocation_id": request["active_allocation_id"],
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
                "scheduler_handle_ref": request["scheduler_handle_ref"],
                "active_allocation_id": request["active_allocation_id"],
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
            "scheduler_handle_ref": request["scheduler_handle_ref"],
            "active_allocation_id": request["active_allocation_id"],
        }
        self._latest_by_identity[request["identity_id"]] = outcome["outcome_id"]
        return deepcopy(outcome)
