"""Ascension scheduler reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .continuity import ContinuityLedger

SCHEDULER_SCHEMA_VERSION = "1.0.0"
SCHEDULER_ALLOWED_METHODS = {"A", "B", "C"}
SCHEDULER_EXECUTABLE_METHODS = {"A", "B", "C"}
SCHEDULER_ALLOWED_STATUS = {
    "scheduled",
    "advancing",
    "paused",
    "rolled-back",
    "completed",
    "cancelled",
    "failed",
}
SCHEDULER_ALLOWED_TRANSITIONS = {
    "enter",
    "complete",
    "rollback",
    "pause",
    "resume",
    "sync",
    "cancel",
    "fail",
}
SCHEDULER_SIGNAL_SEVERITIES = {"watch", "degraded", "critical"}
SCHEDULER_WITNESS_QUORUM = 2
SCHEDULER_ARTIFACT_SYNC_POLICY_ID = "attestation-freshness-v1"
SCHEDULER_ARTIFACT_REFRESH_WINDOW_HOURS = 24
SCHEDULER_ARTIFACT_BUNDLE_STATUS = {"unsynced", "current", "refresh-required", "revoked"}
SCHEDULER_ARTIFACT_STATUS = {"unsynced", "current", "stale", "revoked"}
SCHEDULER_SYNC_REQUIRED_STAGE_BY_METHOD = {
    "A": "active-handoff",
    "B": "authority-handoff",
    "C": "scan-commit",
}
GOVERNANCE_ARTIFACT_PREFIXES = {
    "self_consent_ref": "consent://",
    "ethics_attestation_ref": "ethics://",
    "council_attestation_ref": "council://",
    "legal_attestation_ref": "legal://",
    "artifact_bundle_ref": "artifact://",
}
SYNCED_GOVERNANCE_ARTIFACT_KEYS = (
    "self_consent_ref",
    "ethics_attestation_ref",
    "council_attestation_ref",
    "legal_attestation_ref",
    "artifact_bundle_ref",
)
METHOD_A_STAGE_BLUEPRINT = (
    {
        "stage_id": "scan-baseline",
        "precondition": "pre-upload-consent",
        "timeout_ms": 7_776_000_000,
        "rollback_to": None,
    },
    {
        "stage_id": "bdb-bridge",
        "precondition": "scan-baseline:done",
        "timeout_ms": 600_000,
        "rollback_to": "scan-baseline",
    },
    {
        "stage_id": "identity-confirmation",
        "precondition": "bdb-bridge:done",
        "timeout_ms": 1_800_000,
        "rollback_to": "bdb-bridge",
    },
    {
        "stage_id": "active-handoff",
        "precondition": "identity-confirmation:passed",
        "timeout_ms": 300_000,
        "rollback_to": "bdb-bridge",
    },
)
METHOD_B_STAGE_BLUEPRINT = (
    {
        "stage_id": "shadow-sync",
        "precondition": "pre-upload-consent",
        "timeout_ms": 2_592_000_000,
        "rollback_to": None,
    },
    {
        "stage_id": "dual-channel-review",
        "precondition": "shadow-sync:stable",
        "timeout_ms": 86_400_000,
        "rollback_to": "shadow-sync",
    },
    {
        "stage_id": "authority-handoff",
        "precondition": "dual-channel-review:attested",
        "timeout_ms": 600_000,
        "rollback_to": "dual-channel-review",
    },
    {
        "stage_id": "bio-retirement",
        "precondition": "authority-handoff:confirmed",
        "timeout_ms": 604_800_000,
        "rollback_to": None,
    },
)
METHOD_C_STAGE_BLUEPRINT = (
    {
        "stage_id": "consent-lock",
        "precondition": "pre-upload-consent+human-review",
        "timeout_ms": 604_800_000,
        "rollback_to": None,
    },
    {
        "stage_id": "scan-commit",
        "precondition": "consent-lock:confirmed",
        "timeout_ms": 300_000,
        "rollback_to": None,
    },
    {
        "stage_id": "activation-review",
        "precondition": "scan-commit:completed",
        "timeout_ms": 1_800_000,
        "rollback_to": None,
    },
)
METHOD_STAGE_BLUEPRINTS = {
    "A": METHOD_A_STAGE_BLUEPRINT,
    "B": METHOD_B_STAGE_BLUEPRINT,
    "C": METHOD_C_STAGE_BLUEPRINT,
}


class AscensionScheduler:
    """Deterministic Method A/B/C scheduler and substrate failover engine."""

    def __init__(self, ledger: ContinuityLedger) -> None:
        self.ledger = ledger
        self._plans: Dict[str, Dict[str, Any]] = {}
        self._handles: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "accepted_plan_methods": sorted(SCHEDULER_ALLOWED_METHODS),
            "executable_methods": sorted(SCHEDULER_EXECUTABLE_METHODS),
            "artifact_policy": {
                "self_consent_required": True,
                "ethics_attestation_required": True,
                "council_attestation_required": True,
                "legal_attestation_required": True,
                "minimum_witness_quorum": SCHEDULER_WITNESS_QUORUM,
                "digest_algorithm": "sha256",
                "sync_policy_id": SCHEDULER_ARTIFACT_SYNC_POLICY_ID,
                "refresh_window_hours": SCHEDULER_ARTIFACT_REFRESH_WINDOW_HOURS,
                "stale_action": "pause-and-refresh",
                "revoked_action": "fail-closed",
                "sync_required_before_stage": dict(SCHEDULER_SYNC_REQUIRED_STAGE_BY_METHOD),
            },
            "method_profiles": {
                "A": {
                    "stages": self._method_stages("A"),
                    "reversibility": "reversible through active-handoff rollback target",
                },
                "B": {
                    "stages": self._method_stages("B"),
                    "reversibility": "reversible until authority handoff completes",
                },
                "C": {
                    "stages": self._method_stages("C"),
                    "reversibility": "fail-closed once destructive scan begins",
                },
            },
            "status_values": sorted(SCHEDULER_ALLOWED_STATUS),
            "history_transitions": sorted(SCHEDULER_ALLOWED_TRANSITIONS),
            "timeout_policy": {
                "auto_rollback": True,
                "fail_when_no_rollback_target": True,
                "continuity_append_required_before_commit": True,
            },
            "substrate_signal_policy": {
                "watch": "pause",
                "degraded": "pause",
                "critical_with_rollback_target": "rollback",
                "critical_without_rollback_target": "fail-closed",
            },
        }

    def build_method_a_plan(
        self,
        identity_id: str,
        *,
        plan_id: Optional[str] = None,
        ethics_attestation_required: bool = True,
        council_attestation_required: bool = True,
    ) -> Dict[str, Any]:
        return self._build_plan(
            identity_id,
            method="A",
            plan_id=plan_id,
            ethics_attestation_required=ethics_attestation_required,
            council_attestation_required=council_attestation_required,
        )

    def build_method_b_plan(
        self,
        identity_id: str,
        *,
        plan_id: Optional[str] = None,
        ethics_attestation_required: bool = True,
        council_attestation_required: bool = True,
    ) -> Dict[str, Any]:
        return self._build_plan(
            identity_id,
            method="B",
            plan_id=plan_id,
            ethics_attestation_required=ethics_attestation_required,
            council_attestation_required=council_attestation_required,
        )

    def build_method_c_plan(
        self,
        identity_id: str,
        *,
        plan_id: Optional[str] = None,
        ethics_attestation_required: bool = True,
        council_attestation_required: bool = True,
    ) -> Dict[str, Any]:
        return self._build_plan(
            identity_id,
            method="C",
            plan_id=plan_id,
            ethics_attestation_required=ethics_attestation_required,
            council_attestation_required=council_attestation_required,
        )

    def schedule(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        normalized_plan = self.validate_plan(plan)
        handle_id = new_id("schedule")
        opened_at = utc_now_iso()
        first_stage = normalized_plan["stages"][0]["stage_id"]
        handle = {
            "kind": "schedule_handle",
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "handle_id": handle_id,
            "plan_ref": normalized_plan["plan_id"],
            "identity_id": normalized_plan["identity_id"],
            "governance_artifacts": deepcopy(normalized_plan["governance_artifacts"]),
            "governance_artifact_digest": normalized_plan["governance_artifact_digest"],
            "artifact_sync": self._initial_artifact_sync(normalized_plan["governance_artifacts"]),
            "current_stage": first_stage,
            "status": "scheduled",
            "history": [],
            "opened_at": opened_at,
            "closed_at": None,
        }
        self._plans[normalized_plan["plan_id"]] = normalized_plan
        self._handles[handle_id] = handle
        self._append_history(
            handle,
            stage_id=first_stage,
            transition="enter",
            reason="schedule accepted and first stage opened",
        )
        return deepcopy(handle)

    def observe(self, handle_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_handle(handle_id))

    def advance(self, handle_id: str, stage_id: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        plan = self._require_plan(handle["plan_ref"])
        if plan["method"] not in SCHEDULER_EXECUTABLE_METHODS:
            raise NotImplementedError(f"execution for method {plan['method']} is not implemented")
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot advance schedule in status {handle['status']}")
        if handle["status"] == "paused":
            raise ValueError("cannot advance while paused")

        expected_stage = handle["current_stage"]
        requested_stage = self._normalize_non_empty_string(stage_id, "stage_id")
        if requested_stage != expected_stage:
            raise ValueError(
                f"stage order violation: current stage is {expected_stage}, requested {requested_stage}"
            )

        completed_ref = self._append_history(
            handle,
            stage_id=requested_stage,
            transition="complete",
            reason="stage completed without timeout violation",
        )
        stage_index = self._stage_index(plan, requested_stage)
        if stage_index == len(plan["stages"]) - 1:
            handle["status"] = "completed"
            handle["closed_at"] = utc_now_iso()
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "completed_stage": requested_stage,
                "next_stage": None,
                "status": handle["status"],
                "continuity_event_refs": [completed_ref],
                "triggered_rollback": False,
            }

        next_stage = plan["stages"][stage_index + 1]["stage_id"]
        self._ensure_artifact_sync_for_stage(handle, plan, next_stage)
        handle["current_stage"] = next_stage
        handle["status"] = "advancing"
        entered_ref = self._append_history(
            handle,
            stage_id=next_stage,
            transition="enter",
            reason=f"{requested_stage} completed; next stage opened",
        )
        return {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "completed_stage": requested_stage,
            "next_stage": next_stage,
            "status": handle["status"],
            "continuity_event_refs": [completed_ref, entered_ref],
            "triggered_rollback": False,
        }

    def pause(self, handle_id: str, reason: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot pause schedule in status {handle['status']}")
        if handle["status"] == "paused":
            raise ValueError("schedule is already paused")
        handle["status"] = "paused"
        self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="pause",
            reason=self._normalize_non_empty_string(reason, "reason"),
        )
        return deepcopy(handle)

    def resume(self, handle_id: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] != "paused":
            raise ValueError("schedule must be paused before resume")
        handle["status"] = "advancing"
        self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="resume",
            reason="stage resumed after bounded pause",
        )
        return deepcopy(handle)

    def rollback(self, handle_id: str, to_stage_id: str, *, reason: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        plan = self._require_plan(handle["plan_ref"])
        target_stage = self._normalize_non_empty_string(to_stage_id, "to_stage_id")
        current_stage = self._stage_definition(plan, handle["current_stage"])
        rollback_target = current_stage["rollback_to"]
        if rollback_target is None:
            raise ValueError(f"stage {current_stage['stage_id']} does not allow rollback")
        if target_stage != rollback_target:
            raise ValueError(
                f"rollback target for {current_stage['stage_id']} must be {rollback_target}"
            )
        handle["current_stage"] = target_stage
        handle["status"] = "rolled-back"
        self._append_history(
            handle,
            stage_id=target_stage,
            transition="rollback",
            reason=self._normalize_non_empty_string(reason, "reason"),
        )
        return deepcopy(handle)

    def enforce_timeout(self, handle_id: str, *, elapsed_ms: int) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot enforce timeout in status {handle['status']}")
        if handle["status"] == "paused":
            raise ValueError("cannot enforce timeout while schedule is paused")

        plan = self._require_plan(handle["plan_ref"])
        stage = self._stage_definition(plan, handle["current_stage"])
        normalized_elapsed = self._normalize_positive_int(elapsed_ms, "elapsed_ms")
        if normalized_elapsed <= stage["timeout_ms"]:
            raise ValueError("elapsed_ms does not exceed the active stage timeout")

        fail_ref = self._append_history(
            handle,
            stage_id=stage["stage_id"],
            transition="fail",
            reason=(
                f"timeout exceeded for {stage['stage_id']}: "
                f"{normalized_elapsed}ms > {stage['timeout_ms']}ms"
            ),
        )
        rollback_target = stage["rollback_to"]
        if rollback_target is None:
            handle["status"] = "failed"
            handle["closed_at"] = utc_now_iso()
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "timed_out_stage": stage["stage_id"],
                "elapsed_ms": normalized_elapsed,
                "timeout_ms": stage["timeout_ms"],
                "action": "fail",
                "rollback_target": None,
                "status": handle["status"],
                "continuity_event_refs": [fail_ref],
            }

        rolled_back = self.rollback(
            handle_id,
            rollback_target,
            reason=(
                f"automatic rollback after timeout on {stage['stage_id']} "
                f"({normalized_elapsed}ms > {stage['timeout_ms']}ms)"
            ),
        )
        rollback_ref = rolled_back["history"][-1]["continuity_event_ref"]
        return {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "timed_out_stage": stage["stage_id"],
            "elapsed_ms": normalized_elapsed,
            "timeout_ms": stage["timeout_ms"],
            "action": "rollback",
            "rollback_target": rollback_target,
            "status": rolled_back["status"],
            "continuity_event_refs": [fail_ref, rollback_ref],
            "handle": rolled_back,
        }

    def handle_substrate_signal(
        self,
        handle_id: str,
        *,
        severity: str,
        source_substrate: str,
        reason: str,
    ) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot process substrate signal in status {handle['status']}")

        plan = self._require_plan(handle["plan_ref"])
        stage = self._stage_definition(plan, handle["current_stage"])
        normalized_severity = self._normalize_signal_severity(severity)
        normalized_source = self._normalize_non_empty_string(
            source_substrate,
            "source_substrate",
        )
        normalized_reason = self._normalize_non_empty_string(reason, "reason")
        signal_reason = (
            f"substrate signal {normalized_severity} from {normalized_source}: {normalized_reason}"
        )

        if normalized_severity in {"watch", "degraded"}:
            paused = self.pause(handle_id, signal_reason)
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "stage_id": stage["stage_id"],
                "severity": normalized_severity,
                "source_substrate": normalized_source,
                "action": "pause",
                "rollback_target": None,
                "status": paused["status"],
                "continuity_event_refs": [paused["history"][-1]["continuity_event_ref"]],
                "handle": paused,
            }

        fail_ref = self._append_history(
            handle,
            stage_id=stage["stage_id"],
            transition="fail",
            reason=signal_reason,
        )
        rollback_target = stage["rollback_to"]
        if rollback_target is None:
            handle["status"] = "failed"
            handle["closed_at"] = utc_now_iso()
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "stage_id": stage["stage_id"],
                "severity": normalized_severity,
                "source_substrate": normalized_source,
                "action": "fail",
                "rollback_target": None,
                "status": handle["status"],
                "continuity_event_refs": [fail_ref],
                "handle": deepcopy(handle),
            }

        rolled_back = self.rollback(handle_id, rollback_target, reason=signal_reason)
        return {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "stage_id": stage["stage_id"],
            "severity": normalized_severity,
            "source_substrate": normalized_source,
            "action": "rollback",
            "rollback_target": rollback_target,
            "status": rolled_back["status"],
            "continuity_event_refs": [fail_ref, rolled_back["history"][-1]["continuity_event_ref"]],
            "handle": rolled_back,
        }

    def sync_governance_artifacts(
        self,
        handle_id: str,
        sync_report: Mapping[str, Any],
    ) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot sync governance artifacts in status {handle['status']}")

        normalized_sync = self._normalize_artifact_sync_report(
            sync_report,
            handle["governance_artifacts"],
        )
        handle["artifact_sync"] = normalized_sync
        sync_ref = self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="sync",
            reason=(
                "governance artifact sync recorded with "
                f"bundle_status={normalized_sync['bundle_status']}"
            ),
        )

        bundle_status = normalized_sync["bundle_status"]
        if bundle_status == "revoked":
            handle["status"] = "failed"
            handle["closed_at"] = utc_now_iso()
            fail_ref = self._append_history(
                handle,
                stage_id=handle["current_stage"],
                transition="fail",
                reason="governance artifact revoked; fail-closed before protected handoff",
            )
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "bundle_status": bundle_status,
                "action": "fail",
                "status": handle["status"],
                "continuity_event_refs": [sync_ref, fail_ref],
                "handle": deepcopy(handle),
            }

        if bundle_status == "refresh-required":
            continuity_event_refs = [sync_ref]
            if handle["status"] != "paused":
                handle["status"] = "paused"
                pause_ref = self._append_history(
                    handle,
                    stage_id=handle["current_stage"],
                    transition="pause",
                    reason="governance artifact refresh required before protected handoff",
                )
                continuity_event_refs.append(pause_ref)
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "bundle_status": bundle_status,
                "action": "pause",
                "status": handle["status"],
                "continuity_event_refs": continuity_event_refs,
                "handle": deepcopy(handle),
            }

        return {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "bundle_status": bundle_status,
            "action": "accept",
            "status": handle["status"],
            "continuity_event_refs": [sync_ref],
            "handle": deepcopy(handle),
        }

    def cancel(self, handle_id: str, reason: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(f"cannot cancel schedule in status {handle['status']}")
        handle["status"] = "cancelled"
        handle["closed_at"] = utc_now_iso()
        self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="cancel",
            reason=self._normalize_non_empty_string(reason, "reason"),
        )
        return deepcopy(handle)

    def validate_plan(self, plan: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(plan, Mapping):
            raise ValueError("plan must be a mapping")

        normalized = {
            "kind": self._expect_string(plan.get("kind"), "kind", "ascension_plan"),
            "schema_version": self._expect_schema_version(plan.get("schema_version")),
            "plan_id": self._normalize_non_empty_string(plan.get("plan_id"), "plan_id"),
            "identity_id": self._normalize_non_empty_string(plan.get("identity_id"), "identity_id"),
            "method": self._normalize_method(plan.get("method")),
            "stages": self._normalize_stages(plan.get("stages")),
            "ethics_attestation_required": self._normalize_bool(
                plan.get("ethics_attestation_required"),
                "ethics_attestation_required",
            ),
            "council_attestation_required": self._normalize_bool(
                plan.get("council_attestation_required"),
                "council_attestation_required",
            ),
            "governance_artifacts": self._normalize_governance_artifacts(
                plan.get("governance_artifacts")
            ),
            "governance_artifact_digest": self._normalize_non_empty_string(
                plan.get("governance_artifact_digest"),
                "governance_artifact_digest",
            ),
        }
        expected = self._method_stages(normalized["method"])
        if normalized["stages"] != expected:
            raise ValueError(
                f"method {normalized['method']} must use the fixed reference blueprint"
            )
        expected_digest = self._governance_artifact_digest(normalized["governance_artifacts"])
        if normalized["governance_artifact_digest"] != expected_digest:
            raise ValueError("governance_artifact_digest must match governance_artifacts")
        return normalized

    def validate_handle(self, handle: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(handle, Mapping):
            raise ValueError("handle must be a mapping")

        errors: List[str] = []
        if handle.get("kind") != "schedule_handle":
            errors.append("kind must be schedule_handle")
        if handle.get("schema_version") != SCHEDULER_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SCHEDULER_SCHEMA_VERSION}")
        self._check_non_empty_string(handle.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(handle.get("plan_ref"), "plan_ref", errors)
        self._check_non_empty_string(handle.get("identity_id"), "identity_id", errors)
        governance_artifacts = handle.get("governance_artifacts")
        if not isinstance(governance_artifacts, Mapping):
            errors.append("governance_artifacts must be a mapping")
        else:
            errors.extend(self._check_governance_artifacts(governance_artifacts))
        governance_digest = handle.get("governance_artifact_digest")
        self._check_non_empty_string(
            governance_digest,
            "governance_artifact_digest",
            errors,
        )
        if isinstance(governance_artifacts, Mapping) and isinstance(governance_digest, str):
            expected_digest = self._governance_artifact_digest(governance_artifacts)
            if governance_digest != expected_digest:
                errors.append(
                    "governance_artifact_digest must match governance_artifacts"
                )
        artifact_sync = handle.get("artifact_sync")
        if not isinstance(artifact_sync, Mapping):
            errors.append("artifact_sync must be a mapping")
        else:
            errors.extend(self._check_artifact_sync(artifact_sync, governance_artifacts))
        self._check_non_empty_string(handle.get("current_stage"), "current_stage", errors)

        status = handle.get("status")
        if status not in SCHEDULER_ALLOWED_STATUS:
            errors.append(f"status must be one of {sorted(SCHEDULER_ALLOWED_STATUS)}")

        history = handle.get("history")
        if not isinstance(history, list) or not history:
            errors.append("history must be a non-empty list")
        else:
            last_sequence = -1
            transitions = 0
            for item in history:
                if not isinstance(item, Mapping):
                    errors.append("history items must be mappings")
                    continue
                sequence = item.get("sequence")
                if not isinstance(sequence, int):
                    errors.append("history.sequence must be an integer")
                elif sequence != last_sequence + 1:
                    errors.append("history.sequence must be contiguous")
                    last_sequence = sequence
                else:
                    last_sequence = sequence
                transition = item.get("transition")
                if transition not in SCHEDULER_ALLOWED_TRANSITIONS:
                    errors.append(
                        f"history.transition must be one of {sorted(SCHEDULER_ALLOWED_TRANSITIONS)}"
                    )
                if transition == "rollback":
                    transitions += 1
                self._check_non_empty_string(
                    item.get("continuity_event_ref"),
                    "history.continuity_event_ref",
                    errors,
                )
                self._check_non_empty_string(item.get("stage_id"), "history.stage_id", errors)
                self._check_non_empty_string(item.get("recorded_at"), "history.recorded_at", errors)
            rollback_count = transitions
        return {
            "ok": not errors,
            "errors": errors,
            "history_length": len(history) if isinstance(history, list) else 0,
            "rollback_count": rollback_count if "rollback_count" in locals() else 0,
            "status": status,
        }

    def _append_history(
        self,
        handle: Dict[str, Any],
        *,
        stage_id: str,
        transition: str,
        reason: str,
    ) -> str:
        payload = {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "stage_id": stage_id,
            "transition": transition,
            "status": handle["status"],
            "reason": reason,
            "history_length": len(handle["history"]),
            "governance_artifact_digest": handle["governance_artifact_digest"],
            "artifact_bundle_ref": handle["governance_artifacts"]["artifact_bundle_ref"],
        }
        artifact_sync = handle.get("artifact_sync")
        if isinstance(artifact_sync, Mapping):
            payload["artifact_bundle_status"] = artifact_sync.get("bundle_status", "unsynced")
            payload["artifact_sync_checked_at"] = artifact_sync.get("last_checked_at")
        entry = self.ledger.append(
            identity_id=handle["identity_id"],
            event_type=f"ascension.scheduler.{transition}",
            payload=payload,
            actor="AscensionScheduler",
            category="ascension",
            layer="L1",
            signature_roles=["self"],
            substrate="classical-silicon",
        )
        history_item = {
            "sequence": len(handle["history"]),
            "stage_id": stage_id,
            "transition": transition,
            "recorded_at": entry.wall_time,
            "continuity_event_ref": entry.entry_id,
            "reason": reason,
        }
        handle["history"].append(history_item)
        return entry.entry_id

    def _require_handle(self, handle_id: str) -> Dict[str, Any]:
        handle = self._handles.get(handle_id)
        if handle is None:
            raise ValueError(f"unknown schedule handle: {handle_id}")
        return handle

    def _require_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            return self._plans[plan_id]
        except KeyError as exc:
            raise ValueError(f"unknown ascension plan: {plan_id}") from exc

    def _stage_definition(self, plan: Mapping[str, Any], stage_id: str) -> Dict[str, Any]:
        for stage in plan["stages"]:
            if stage["stage_id"] == stage_id:
                return stage
        raise ValueError(f"unknown stage_id: {stage_id}")

    def _stage_index(self, plan: Mapping[str, Any], stage_id: str) -> int:
        for index, stage in enumerate(plan["stages"]):
            if stage["stage_id"] == stage_id:
                return index
        raise ValueError(f"unknown stage_id: {stage_id}")

    def _normalize_stages(self, stages: Any) -> List[Dict[str, Any]]:
        if not isinstance(stages, Sequence) or isinstance(stages, (str, bytes)):
            raise ValueError("stages must be a non-empty sequence")
        normalized: List[Dict[str, Any]] = []
        for raw_stage in stages:
            if not isinstance(raw_stage, Mapping):
                raise ValueError("each stage must be a mapping")
            normalized.append(
                {
                    "stage_id": self._normalize_non_empty_string(raw_stage.get("stage_id"), "stage_id"),
                    "precondition": self._normalize_non_empty_string(
                        raw_stage.get("precondition"),
                        "precondition",
                    ),
                    "timeout_ms": self._normalize_positive_int(
                        raw_stage.get("timeout_ms"),
                        "timeout_ms",
                    ),
                    "rollback_to": self._normalize_optional_stage(raw_stage.get("rollback_to")),
                }
            )
        return normalized

    def _normalize_optional_stage(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        return self._normalize_non_empty_string(value, "rollback_to")

    def _normalize_governance_artifacts(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("governance_artifacts must be a mapping")
        normalized = {
            field_name: self._normalize_artifact_ref(
                value.get(field_name),
                field_name,
                prefix,
            )
            for field_name, prefix in GOVERNANCE_ARTIFACT_PREFIXES.items()
        }
        witness_refs = value.get("witness_refs")
        if not isinstance(witness_refs, Sequence) or isinstance(witness_refs, (str, bytes)):
            raise ValueError("witness_refs must be a sequence")
        normalized_witness_refs: List[str] = []
        for index, witness_ref in enumerate(witness_refs):
            normalized_witness_ref = self._normalize_artifact_ref(
                witness_ref,
                f"witness_refs[{index}]",
                "witness://",
            )
            if normalized_witness_ref not in normalized_witness_refs:
                normalized_witness_refs.append(normalized_witness_ref)
        if len(normalized_witness_refs) < SCHEDULER_WITNESS_QUORUM:
            raise ValueError(
                f"witness_refs must contain at least {SCHEDULER_WITNESS_QUORUM} entries"
            )
        normalized["witness_refs"] = normalized_witness_refs
        return normalized

    def _initial_artifact_sync(self, governance_artifacts: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "policy_id": SCHEDULER_ARTIFACT_SYNC_POLICY_ID,
            "bundle_status": "unsynced",
            "last_checked_at": None,
            "artifacts": [
                {
                    "artifact_key": artifact_key,
                    "artifact_ref": governance_artifacts[artifact_key],
                    "status": "unsynced",
                    "checked_at": None,
                    "proof_digest": None,
                    "external_sync_ref": None,
                    "refresh_required": False,
                }
                for artifact_key in SYNCED_GOVERNANCE_ARTIFACT_KEYS
            ],
        }

    def _normalize_artifact_sync_report(
        self,
        value: Any,
        governance_artifacts: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("sync_report must be a mapping")
        checked_at = self._normalize_non_empty_string(value.get("checked_at"), "checked_at")
        raw_artifacts = value.get("artifacts")
        if not isinstance(raw_artifacts, Sequence) or isinstance(raw_artifacts, (str, bytes)):
            raise ValueError("artifacts must be a sequence")

        expected_keys = list(SYNCED_GOVERNANCE_ARTIFACT_KEYS)
        seen_keys: List[str] = []
        normalized_artifacts: List[Dict[str, Any]] = []
        for raw_artifact in raw_artifacts:
            if not isinstance(raw_artifact, Mapping):
                raise ValueError("artifacts entries must be mappings")
            artifact_key = self._normalize_non_empty_string(
                raw_artifact.get("artifact_key"),
                "artifact_key",
            )
            if artifact_key not in expected_keys:
                raise ValueError(
                    f"artifact_key must be one of {sorted(SYNCED_GOVERNANCE_ARTIFACT_KEYS)}"
                )
            if artifact_key in seen_keys:
                raise ValueError(f"artifact_key duplicated in sync_report: {artifact_key}")
            seen_keys.append(artifact_key)
            status = self._normalize_artifact_status(raw_artifact.get("status"))
            normalized_artifacts.append(
                {
                    "artifact_key": artifact_key,
                    "artifact_ref": governance_artifacts[artifact_key],
                    "status": status,
                    "checked_at": checked_at,
                    "proof_digest": self._normalize_optional_digest(
                        raw_artifact.get("proof_digest"),
                        "proof_digest",
                        allow_none=status == "unsynced",
                    ),
                    "external_sync_ref": self._normalize_optional_sync_ref(
                        raw_artifact.get("external_sync_ref"),
                        allow_none=status == "unsynced",
                    ),
                    "refresh_required": status == "stale",
                }
            )

        missing_keys = [artifact_key for artifact_key in expected_keys if artifact_key not in seen_keys]
        if missing_keys:
            raise ValueError(f"sync_report is missing artifact keys: {', '.join(missing_keys)}")

        bundle_status = self._bundle_status_from_artifacts(normalized_artifacts)
        return {
            "policy_id": SCHEDULER_ARTIFACT_SYNC_POLICY_ID,
            "bundle_status": bundle_status,
            "last_checked_at": checked_at,
            "artifacts": normalized_artifacts,
        }

    def _check_governance_artifacts(self, value: Mapping[str, Any]) -> List[str]:
        errors: List[str] = []
        for field_name, prefix in GOVERNANCE_ARTIFACT_PREFIXES.items():
            field_value = value.get(field_name)
            if not isinstance(field_value, str) or not field_value.strip():
                errors.append(f"governance_artifacts.{field_name} must be a non-empty string")
            elif not field_value.startswith(prefix):
                errors.append(
                    f"governance_artifacts.{field_name} must start with {prefix}"
                )
        witness_refs = value.get("witness_refs")
        if not isinstance(witness_refs, Sequence) or isinstance(witness_refs, (str, bytes)):
            errors.append("governance_artifacts.witness_refs must be a sequence")
        else:
            normalized_witness_refs: List[str] = []
            for index, witness_ref in enumerate(witness_refs):
                if not isinstance(witness_ref, str) or not witness_ref.strip():
                    errors.append(
                        f"governance_artifacts.witness_refs[{index}] must be a non-empty string"
                    )
                    continue
                if not witness_ref.startswith("witness://"):
                    errors.append(
                        f"governance_artifacts.witness_refs[{index}] must start with witness://"
                    )
                    continue
                if witness_ref not in normalized_witness_refs:
                    normalized_witness_refs.append(witness_ref)
            if len(normalized_witness_refs) < SCHEDULER_WITNESS_QUORUM:
                errors.append(
                    f"governance_artifacts.witness_refs must contain at least {SCHEDULER_WITNESS_QUORUM} entries"
                )
        return errors

    def _check_artifact_sync(
        self,
        value: Mapping[str, Any],
        governance_artifacts: Any,
    ) -> List[str]:
        errors: List[str] = []
        policy_id = value.get("policy_id")
        if policy_id != SCHEDULER_ARTIFACT_SYNC_POLICY_ID:
            errors.append(f"artifact_sync.policy_id must be {SCHEDULER_ARTIFACT_SYNC_POLICY_ID}")
        bundle_status = value.get("bundle_status")
        if bundle_status not in SCHEDULER_ARTIFACT_BUNDLE_STATUS:
            errors.append(
                f"artifact_sync.bundle_status must be one of {sorted(SCHEDULER_ARTIFACT_BUNDLE_STATUS)}"
            )
        last_checked_at = value.get("last_checked_at")
        if last_checked_at is not None and (not isinstance(last_checked_at, str) or not last_checked_at.strip()):
            errors.append("artifact_sync.last_checked_at must be a string or null")

        artifacts = value.get("artifacts")
        if not isinstance(artifacts, list) or len(artifacts) != len(SYNCED_GOVERNANCE_ARTIFACT_KEYS):
            errors.append(
                f"artifact_sync.artifacts must contain {len(SYNCED_GOVERNANCE_ARTIFACT_KEYS)} entries"
            )
            return errors

        expected_refs = {
            artifact_key: governance_artifacts.get(artifact_key)
            for artifact_key in SYNCED_GOVERNANCE_ARTIFACT_KEYS
            if isinstance(governance_artifacts, Mapping)
        }
        seen_keys: List[str] = []
        for item in artifacts:
            if not isinstance(item, Mapping):
                errors.append("artifact_sync.artifacts items must be mappings")
                continue
            artifact_key = item.get("artifact_key")
            if artifact_key not in SYNCED_GOVERNANCE_ARTIFACT_KEYS:
                errors.append(
                    f"artifact_sync.artifact_key must be one of {sorted(SYNCED_GOVERNANCE_ARTIFACT_KEYS)}"
                )
                continue
            if artifact_key in seen_keys:
                errors.append(f"artifact_sync.artifact_key duplicated: {artifact_key}")
            else:
                seen_keys.append(artifact_key)
            artifact_ref = item.get("artifact_ref")
            if artifact_ref != expected_refs.get(artifact_key):
                errors.append(f"artifact_sync.artifact_ref mismatch for {artifact_key}")
            status = item.get("status")
            if status not in SCHEDULER_ARTIFACT_STATUS:
                errors.append(
                    f"artifact_sync.status must be one of {sorted(SCHEDULER_ARTIFACT_STATUS)}"
                )
            checked_at = item.get("checked_at")
            if checked_at is not None and (not isinstance(checked_at, str) or not checked_at.strip()):
                errors.append(f"artifact_sync.checked_at must be a string or null for {artifact_key}")
            proof_digest = item.get("proof_digest")
            if proof_digest is not None and (
                not isinstance(proof_digest, str) or len(proof_digest) != 64
            ):
                errors.append(f"artifact_sync.proof_digest must be 64 hex chars for {artifact_key}")
            external_sync_ref = item.get("external_sync_ref")
            if external_sync_ref is not None and (
                not isinstance(external_sync_ref, str)
                or not external_sync_ref.startswith("sync://")
            ):
                errors.append(
                    f"artifact_sync.external_sync_ref must start with sync:// for {artifact_key}"
                )
            refresh_required = item.get("refresh_required")
            if not isinstance(refresh_required, bool):
                errors.append(f"artifact_sync.refresh_required must be a boolean for {artifact_key}")
            elif refresh_required != (status == "stale"):
                errors.append(
                    f"artifact_sync.refresh_required mismatch for {artifact_key}"
                )

        if seen_keys != list(SYNCED_GOVERNANCE_ARTIFACT_KEYS):
            expected_key_set = list(SYNCED_GOVERNANCE_ARTIFACT_KEYS)
            missing = [artifact_key for artifact_key in expected_key_set if artifact_key not in seen_keys]
            if missing:
                errors.append(
                    f"artifact_sync.artifacts missing keys: {', '.join(missing)}"
                )
        if not errors and self._bundle_status_from_artifacts(artifacts) != bundle_status:
            errors.append("artifact_sync.bundle_status does not match artifact statuses")
        return errors

    def _normalize_artifact_ref(self, value: Any, field_name: str, prefix: str) -> str:
        normalized = self._normalize_non_empty_string(value, field_name)
        if not normalized.startswith(prefix):
            raise ValueError(f"{field_name} must start with {prefix}")
        return normalized

    def _normalize_artifact_status(self, value: Any) -> str:
        status = self._normalize_non_empty_string(value, "status")
        if status not in SCHEDULER_ARTIFACT_STATUS:
            raise ValueError(f"status must be one of {sorted(SCHEDULER_ARTIFACT_STATUS)}")
        return status

    def _normalize_optional_digest(
        self,
        value: Any,
        field_name: str,
        *,
        allow_none: bool,
    ) -> Optional[str]:
        if value is None:
            if allow_none:
                return None
            raise ValueError(f"{field_name} must be a 64 character digest")
        normalized = self._normalize_non_empty_string(value, field_name)
        if len(normalized) != 64:
            raise ValueError(f"{field_name} must be a 64 character digest")
        return normalized

    def _normalize_optional_sync_ref(self, value: Any, *, allow_none: bool) -> Optional[str]:
        if value is None:
            if allow_none:
                return None
            raise ValueError("external_sync_ref must start with sync://")
        normalized = self._normalize_non_empty_string(value, "external_sync_ref")
        if not normalized.startswith("sync://"):
            raise ValueError("external_sync_ref must start with sync://")
        return normalized

    def _bundle_status_from_artifacts(self, artifacts: Sequence[Mapping[str, Any]]) -> str:
        statuses = [artifact["status"] for artifact in artifacts]
        if statuses and all(status == "unsynced" for status in statuses):
            return "unsynced"
        if "revoked" in statuses:
            return "revoked"
        if "stale" in statuses or "unsynced" in statuses:
            return "refresh-required"
        return "current"

    def _governance_artifact_digest(self, governance_artifacts: Mapping[str, Any]) -> str:
        return sha256_text(canonical_json(dict(governance_artifacts)))

    def _ensure_artifact_sync_for_stage(
        self,
        handle: Mapping[str, Any],
        plan: Mapping[str, Any],
        next_stage: str,
    ) -> None:
        if SCHEDULER_SYNC_REQUIRED_STAGE_BY_METHOD.get(plan["method"]) != next_stage:
            return
        artifact_sync = handle.get("artifact_sync")
        if not isinstance(artifact_sync, Mapping) or artifact_sync.get("bundle_status") != "current":
            raise ValueError(
                f"governance artifacts must be synced as current before entering {next_stage}"
            )

    def _normalize_non_empty_string(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def _normalize_bool(self, value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} must be a boolean")
        return value

    def _normalize_method(self, value: Any) -> str:
        method = self._normalize_non_empty_string(value, "method")
        if method not in SCHEDULER_ALLOWED_METHODS:
            raise ValueError(f"method must be one of {sorted(SCHEDULER_ALLOWED_METHODS)}")
        return method

    def _normalize_signal_severity(self, value: Any) -> str:
        severity = self._normalize_non_empty_string(value, "severity")
        if severity not in SCHEDULER_SIGNAL_SEVERITIES:
            raise ValueError(
                f"severity must be one of {sorted(SCHEDULER_SIGNAL_SEVERITIES)}"
            )
        return severity

    def _normalize_positive_int(self, value: Any, field_name: str) -> int:
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"{field_name} must be a positive integer")
        return value

    def _expect_string(self, value: Any, field_name: str, expected: str) -> str:
        normalized = self._normalize_non_empty_string(value, field_name)
        if normalized != expected:
            raise ValueError(f"{field_name} must be {expected}")
        return normalized

    def _expect_schema_version(self, value: Any) -> str:
        normalized = self._normalize_non_empty_string(value, "schema_version")
        if normalized != SCHEDULER_SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEDULER_SCHEMA_VERSION}")
        return normalized

    def _check_non_empty_string(self, value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    def _method_a_stages(self) -> List[Dict[str, Any]]:
        return self._method_stages("A")

    def _method_stages(self, method: str) -> List[Dict[str, Any]]:
        return [deepcopy(stage) for stage in METHOD_STAGE_BLUEPRINTS[method]]

    def _build_plan(
        self,
        identity_id: str,
        *,
        method: str,
        plan_id: Optional[str],
        ethics_attestation_required: bool,
        council_attestation_required: bool,
    ) -> Dict[str, Any]:
        normalized_identity_id = self._normalize_non_empty_string(identity_id, "identity_id")
        normalized_method = self._normalize_method(method)
        governance_artifacts = self._reference_governance_artifacts(
            normalized_identity_id,
            normalized_method,
        )
        return {
            "kind": "ascension_plan",
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "plan_id": plan_id or new_id("ascension-plan"),
            "identity_id": normalized_identity_id,
            "method": normalized_method,
            "stages": self._method_stages(normalized_method),
            "ethics_attestation_required": ethics_attestation_required,
            "council_attestation_required": council_attestation_required,
            "governance_artifacts": governance_artifacts,
            "governance_artifact_digest": self._governance_artifact_digest(governance_artifacts),
        }

    def _reference_governance_artifacts(self, identity_id: str, method: str) -> Dict[str, Any]:
        token = sha256_text(f"{identity_id}:{method}")[:12]
        method_token = method.lower()
        return {
            "self_consent_ref": f"consent://ascension/{method_token}/{token}/self-consent",
            "ethics_attestation_ref": (
                f"ethics://ascension/{method_token}/{token}/guardian-approval"
            ),
            "council_attestation_ref": (
                f"council://ascension/{method_token}/{token}/reference-resolution"
            ),
            "legal_attestation_ref": (
                f"legal://ascension/{method_token}/{token}/clinical-readiness"
            ),
            "witness_refs": [
                f"witness://ascension/{method_token}/{token}/clinician-primary",
                f"witness://ascension/{method_token}/{token}/guardian-observer",
            ],
            "artifact_bundle_ref": f"artifact://ascension/{method_token}/{token}/bundle",
        }
