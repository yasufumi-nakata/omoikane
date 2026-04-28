"""Ascension scheduler reference model."""

from __future__ import annotations

from copy import deepcopy
import json
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence
from urllib import error, request

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
SCHEDULER_VERIFIER_ROSTER_POLICY_ID = "verifier-root-rotation-v1"
SCHEDULER_VERIFIER_ROTATION_STATES = {
    "unverified",
    "stable",
    "overlap-required",
    "rotated",
    "revoked",
}
SCHEDULER_VERIFIER_ROOT_STATUSES = {"active", "candidate", "retired"}
SCHEDULER_VERIFIER_CONNECTIVITY_TRANSPORT_PROFILE = "live-http-json-roster-v1"
SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES = {"reachable", "rejected"}
SCHEDULER_VERIFIER_MAX_TRACKED_ROOTS = 2
SCHEDULER_METHOD_B_HANDOFF_POLICY_ID = "method-b-host-bound-broker-orchestration-v1"
SCHEDULER_METHOD_B_HANDOFF_STATUSES = {"prepared", "confirmed"}
SCHEDULER_EXECUTION_PROFILE_IDS = {
    "A": "method-a-stage-execution-v1",
    "B": "method-b-protected-handoff-execution-v1",
    "C": "method-c-fail-closed-stage-execution-v1",
}
SCHEDULER_EXECUTION_SCENARIO_LABELS = (
    "timeout-recovery",
    "protected-gate-pause",
    "live-verifier-connectivity",
    "verifier-rotation-cutover",
    "signal-pause",
    "signal-rollback",
    "signal-fail-closed",
    "artifact-revoked",
    "verifier-revoked",
    "broker-handoff-prepared",
    "broker-handoff-confirmed",
    "cancelled",
    "completed",
)
SCHEDULER_METHOD_B_PREPARE_STAGE = "dual-channel-review"
SCHEDULER_METHOD_B_HANDOFF_STAGE = "authority-handoff"
SCHEDULER_METHOD_B_RETIRE_STAGE = "bio-retirement"
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
            "verifier_rotation_policy": {
                "policy_id": SCHEDULER_VERIFIER_ROSTER_POLICY_ID,
                "accepted_states_before_handoff": ["stable", "rotated"],
                "overlap_action": "pause-until-cutover",
                "revoked_action": "fail-closed",
                "max_tracked_roots": SCHEDULER_VERIFIER_MAX_TRACKED_ROOTS,
            },
            "method_b_handoff_policy": {
                "policy_id": SCHEDULER_METHOD_B_HANDOFF_POLICY_ID,
                "prepare_stage": SCHEDULER_METHOD_B_PREPARE_STAGE,
                "handoff_stage": SCHEDULER_METHOD_B_HANDOFF_STAGE,
                "retirement_stage": SCHEDULER_METHOD_B_RETIRE_STAGE,
                "required_recommended_action": "migrate-standby",
                "required_scheduler_signal_severity": "critical",
                "required_distinct_host_count": 2,
                "authority_handoff_requires": "prepared broker handoff receipt",
                "bio_retirement_requires": "confirmed broker handoff receipt",
            },
            "method_profiles": {
                "A": {
                    "stages": self._method_stages("A"),
                    "reversibility": "reversible through active-handoff rollback target",
                },
                "B": {
                    "stages": self._method_stages("B"),
                    "reversibility": "reversible until authority handoff completes",
                    "broker_handoff_required_before_stage": SCHEDULER_METHOD_B_HANDOFF_STAGE,
                    "broker_confirmation_required_before_stage": SCHEDULER_METHOD_B_RETIRE_STAGE,
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
            "verifier_roster": self._initial_verifier_roster(
                normalized_plan["governance_artifacts"]
            ),
            "broker_handoff_receipt": None,
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

    def probe_live_verifier_roster(
        self,
        handle_id: str,
        *,
        verifier_endpoint: str,
        request_timeout_ms: int = 1_000,
    ) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        normalized_endpoint = self._normalize_live_verifier_endpoint(
            verifier_endpoint,
            "verifier_endpoint",
        )
        timeout_ms = self._normalize_positive_int(request_timeout_ms, "request_timeout_ms")
        request_started = time.monotonic()
        try:
            with request.urlopen(normalized_endpoint, timeout=timeout_ms / 1000.0) as response:
                http_status = int(getattr(response, "status", 200))
                payload_text = response.read().decode("utf-8")
        except error.URLError as exc:
            raise ValueError(
                f"live verifier endpoint unreachable: {normalized_endpoint}"
            ) from exc
        observed_latency_ms = round((time.monotonic() - request_started) * 1000.0, 1)
        if http_status != 200:
            raise ValueError(
                f"live verifier endpoint returned unexpected status {http_status}"
            )
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("live verifier endpoint must return JSON") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("live verifier endpoint payload must be a mapping")

        checked_at = self._normalize_non_empty_string(
            payload.get("checked_at"),
            "verifier_roster.checked_at",
        )
        normalized_roster = self._normalize_verifier_roster_report(
            payload,
            handle["governance_artifacts"],
            checked_at=checked_at,
        )
        normalized_roster["connectivity_receipt"] = {
            "kind": "governance_verifier_connectivity_receipt",
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "receipt_id": new_id("verifier-connectivity"),
            "roster_ref": normalized_roster["roster_ref"],
            "verifier_endpoint": normalized_endpoint,
            "transport_profile": SCHEDULER_VERIFIER_CONNECTIVITY_TRANSPORT_PROFILE,
            "roster_checked_at": checked_at,
            "recorded_at": utc_now_iso(),
            "request_timeout_ms": timeout_ms,
            "observed_latency_ms": observed_latency_ms,
            "http_status": http_status,
            "response_digest": sha256_text(canonical_json(payload)),
            "receipt_status": "reachable",
            "active_root_id": normalized_roster["active_root_id"],
            "rotation_state": normalized_roster["rotation_state"],
            "accepted_root_count": len(normalized_roster["accepted_roots"]),
        }
        errors = self._check_verifier_roster(normalized_roster, handle["governance_artifacts"])
        if errors:
            raise ValueError(errors[0])
        return normalized_roster

    def advance(self, handle_id: str, stage_id: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        plan = self._require_plan(handle["plan_ref"])
        if plan["method"] not in SCHEDULER_EXECUTABLE_METHODS:
            raise ValueError(f"method {plan['method']} is not executable in this reference profile")
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
        self._ensure_method_b_handoff_for_stage(handle, plan, next_stage)
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

        checked_at = self._normalize_non_empty_string(sync_report.get("checked_at"), "checked_at")
        normalized_sync = self._normalize_artifact_sync_report(
            sync_report,
            handle["governance_artifacts"],
            checked_at=checked_at,
        )
        normalized_verifier_roster = self._normalize_verifier_roster_report(
            sync_report.get("verifier_roster"),
            handle["governance_artifacts"],
            checked_at=checked_at,
        )
        handle["artifact_sync"] = normalized_sync
        handle["verifier_roster"] = normalized_verifier_roster
        sync_ref = self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="sync",
            reason=(
                "governance artifact sync recorded with "
                f"bundle_status={normalized_sync['bundle_status']} "
                f"and verifier_rotation_state={normalized_verifier_roster['rotation_state']}"
            ),
        )

        bundle_status = normalized_sync["bundle_status"]
        rotation_state = normalized_verifier_roster["rotation_state"]
        if bundle_status == "revoked" or rotation_state == "revoked":
            handle["status"] = "failed"
            handle["closed_at"] = utc_now_iso()
            fail_reason = (
                "governance verifier root revoked; fail-closed before protected handoff"
                if rotation_state == "revoked"
                else "governance artifact revoked; fail-closed before protected handoff"
            )
            fail_ref = self._append_history(
                handle,
                stage_id=handle["current_stage"],
                transition="fail",
                reason=fail_reason,
            )
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "bundle_status": bundle_status,
                "verifier_rotation_state": rotation_state,
                "action": "fail",
                "status": handle["status"],
                "continuity_event_refs": [sync_ref, fail_ref],
                "handle": deepcopy(handle),
            }

        pause_reason = None
        if bundle_status == "refresh-required":
            pause_reason = "governance artifact refresh required before protected handoff"
        elif rotation_state == "overlap-required":
            pause_reason = "verifier root overlap must finish before protected handoff"
        if pause_reason is not None:
            continuity_event_refs = [sync_ref]
            if handle["status"] != "paused":
                handle["status"] = "paused"
                pause_ref = self._append_history(
                    handle,
                    stage_id=handle["current_stage"],
                    transition="pause",
                    reason=pause_reason,
                )
                continuity_event_refs.append(pause_ref)
            return {
                "handle_id": handle["handle_id"],
                "plan_ref": handle["plan_ref"],
                "bundle_status": bundle_status,
                "verifier_rotation_state": rotation_state,
                "action": "pause",
                "status": handle["status"],
                "continuity_event_refs": continuity_event_refs,
                "handle": deepcopy(handle),
            }

        return {
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "bundle_status": bundle_status,
            "verifier_rotation_state": rotation_state,
            "action": "accept",
            "status": handle["status"],
            "continuity_event_refs": [sync_ref],
            "handle": deepcopy(handle),
        }

    def prepare_method_b_handoff(
        self,
        handle_id: str,
        *,
        broker_signal: Mapping[str, Any],
        standby_probe: Mapping[str, Any],
        attestation_chain: Mapping[str, Any],
        dual_allocation_window: Mapping[str, Any],
        attestation_stream: Mapping[str, Any],
    ) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(
                f"cannot prepare broker handoff in status {handle['status']}"
            )
        if handle["status"] == "paused":
            raise ValueError("cannot prepare broker handoff while paused")
        plan = self._require_plan(handle["plan_ref"])
        if plan["method"] != "B":
            raise ValueError("broker handoff receipt is only supported for Method B")
        if handle["current_stage"] != SCHEDULER_METHOD_B_PREPARE_STAGE:
            raise ValueError(
                "broker handoff receipt must be prepared during dual-channel-review"
            )

        receipt = self._normalize_method_b_handoff_receipt(
            handle=handle,
            broker_signal=broker_signal,
            standby_probe=standby_probe,
            attestation_chain=attestation_chain,
            dual_allocation_window=dual_allocation_window,
            attestation_stream=attestation_stream,
        )
        handle["broker_handoff_receipt"] = receipt
        self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="sync",
            reason=(
                "Method B broker handoff prepared with cross-host standby probe, "
                "attestation chain, dual allocation window, and sealed stream"
            ),
        )
        return deepcopy(receipt)

    def confirm_method_b_handoff(
        self,
        handle_id: str,
        *,
        migration: Mapping[str, Any],
        closed_dual_allocation_window: Mapping[str, Any],
    ) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] in {"completed", "cancelled", "failed"}:
            raise ValueError(
                f"cannot confirm broker handoff in status {handle['status']}"
            )
        if handle["status"] == "paused":
            raise ValueError("cannot confirm broker handoff while paused")
        plan = self._require_plan(handle["plan_ref"])
        if plan["method"] != "B":
            raise ValueError("broker handoff receipt is only supported for Method B")
        if handle["current_stage"] != SCHEDULER_METHOD_B_HANDOFF_STAGE:
            raise ValueError(
                "broker handoff receipt must be confirmed during authority-handoff"
            )

        receipt = handle.get("broker_handoff_receipt")
        if not isinstance(receipt, Mapping):
            raise ValueError("broker handoff receipt must be prepared before confirmation")
        if receipt.get("status") == "confirmed":
            raise ValueError("broker handoff receipt is already confirmed")

        migration_snapshot, closed_window_snapshot = self._normalize_method_b_handoff_confirmation(
            receipt=receipt,
            migration=migration,
            closed_dual_allocation_window=closed_dual_allocation_window,
        )
        confirmed_receipt = dict(receipt)
        confirmed_receipt["status"] = "confirmed"
        confirmed_receipt["confirmed_at"] = migration_snapshot["transferred_at"]
        confirmed_receipt["migration_transfer_id"] = migration_snapshot["transfer_id"]
        confirmed_receipt["migration_state_digest"] = migration_snapshot["state_digest"]
        confirmed_receipt["dual_allocation_close_id"] = closed_window_snapshot["window_id"]
        confirmed_receipt["cleanup_release_status"] = closed_window_snapshot["release_status"]
        handle["broker_handoff_receipt"] = confirmed_receipt
        self._append_history(
            handle,
            stage_id=handle["current_stage"],
            transition="sync",
            reason=(
                "Method B broker handoff confirmed with hot-handoff migration "
                "and closed dual allocation cleanup"
            ),
        )
        return deepcopy(confirmed_receipt)

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

    def compile_execution_receipt(self, handle_id: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        plan = self._require_plan(handle["plan_ref"])
        history = handle["history"]
        if not isinstance(history, list) or not history:
            raise ValueError("schedule handle must contain non-empty history before compilation")

        transition_counts = {
            transition: 0 for transition in sorted(SCHEDULER_ALLOWED_TRANSITIONS)
        }
        continuity_event_refs: List[str] = []
        visited_stages: List[str] = []
        reasons: List[str] = []
        for item in history:
            if not isinstance(item, Mapping):
                raise ValueError("schedule handle history items must be mappings")
            transition = self._normalize_non_empty_string(
                item.get("transition"),
                "history.transition",
            )
            if transition not in SCHEDULER_ALLOWED_TRANSITIONS:
                raise ValueError(
                    f"history.transition must be one of {sorted(SCHEDULER_ALLOWED_TRANSITIONS)}"
                )
            transition_counts[transition] += 1
            continuity_event_ref = self._normalize_non_empty_string(
                item.get("continuity_event_ref"),
                "history.continuity_event_ref",
            )
            continuity_event_refs.append(continuity_event_ref)
            stage_id = self._normalize_non_empty_string(item.get("stage_id"), "history.stage_id")
            if stage_id not in visited_stages:
                visited_stages.append(stage_id)
            reason = item.get("reason")
            if isinstance(reason, str) and reason.strip():
                reasons.append(reason.strip())

        stage_blueprint = [stage["stage_id"] for stage in plan["stages"]]
        artifact_sync = handle["artifact_sync"]
        verifier_roster = handle["verifier_roster"]
        broker_handoff_receipt = handle.get("broker_handoff_receipt")

        artifact_bundle_status = artifact_sync["bundle_status"]
        verifier_rotation_state = verifier_roster["rotation_state"]
        connectivity_receipt = verifier_roster.get("connectivity_receipt")
        verifier_connectivity_status = None
        if isinstance(connectivity_receipt, Mapping):
            verifier_connectivity_status = connectivity_receipt.get("receipt_status")
        broker_handoff_status = None
        if isinstance(broker_handoff_receipt, Mapping):
            broker_handoff_status = broker_handoff_receipt.get("status")

        reason_blob = "\n".join(reasons)
        timeout_recovered = any(
            "timeout exceeded" in reason for reason in reasons
        ) and transition_counts["rollback"] > 0
        protected_gate_paused = any(
            marker in reason_blob
            for marker in (
                "protected handoff",
                "refresh required before protected handoff",
                "verifier root overlap must finish before protected handoff",
            )
        )
        signal_pause_observed = any(
            "substrate signal degraded" in reason or "substrate signal watch" in reason
            for reason in reasons
        ) and transition_counts["pause"] > 0
        signal_rollback_observed = any(
            "substrate signal critical" in reason for reason in reasons
        ) and transition_counts["rollback"] > 0
        signal_fail_closed_observed = any(
            "substrate signal critical" in reason for reason in reasons
        ) and transition_counts["fail"] > 0 and handle["status"] == "failed"
        live_verifier_connectivity_bound = verifier_connectivity_status == "reachable"
        verifier_rotation_cutover = (
            verifier_rotation_state == "rotated"
            and "verifier root overlap must finish before protected handoff" in reason_blob
        )
        artifact_revoked_fail_closed = (
            artifact_bundle_status == "revoked" and handle["status"] == "failed"
        )
        verifier_revoked_fail_closed = (
            verifier_rotation_state == "revoked" and handle["status"] == "failed"
        )
        method_b_broker_prepared = broker_handoff_status in {"prepared", "confirmed"}
        method_b_broker_confirmed = broker_handoff_status == "confirmed"

        scenario_labels: List[str] = []
        if timeout_recovered:
            scenario_labels.append("timeout-recovery")
        if protected_gate_paused:
            scenario_labels.append("protected-gate-pause")
        if live_verifier_connectivity_bound:
            scenario_labels.append("live-verifier-connectivity")
        if verifier_rotation_cutover:
            scenario_labels.append("verifier-rotation-cutover")
        if signal_pause_observed:
            scenario_labels.append("signal-pause")
        if signal_rollback_observed:
            scenario_labels.append("signal-rollback")
        if signal_fail_closed_observed:
            scenario_labels.append("signal-fail-closed")
        if artifact_revoked_fail_closed:
            scenario_labels.append("artifact-revoked")
        if verifier_revoked_fail_closed:
            scenario_labels.append("verifier-revoked")
        if method_b_broker_prepared:
            scenario_labels.append("broker-handoff-prepared")
        if method_b_broker_confirmed:
            scenario_labels.append("broker-handoff-confirmed")
        if handle["status"] == "cancelled":
            scenario_labels.append("cancelled")
        if handle["status"] == "completed":
            scenario_labels.append("completed")

        receipt = {
            "kind": "scheduler_execution_receipt",
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "execution_receipt_id": new_id("scheduler-exec"),
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "identity_id": handle["identity_id"],
            "method": plan["method"],
            "execution_profile_id": SCHEDULER_EXECUTION_PROFILE_IDS[plan["method"]],
            "stage_blueprint": stage_blueprint,
            "visited_stages": visited_stages,
            "current_stage": handle["current_stage"],
            "final_status": handle["status"],
            "history_length": len(history),
            "continuity_event_refs": continuity_event_refs,
            "transition_counts": transition_counts,
            "cancel_count": transition_counts["cancel"],
            "rollback_count": transition_counts["rollback"],
            "pause_count": transition_counts["pause"],
            "sync_count": transition_counts["sync"],
            "fail_count": transition_counts["fail"],
            "governance_artifact_digest": handle["governance_artifact_digest"],
            "artifact_bundle_status": artifact_bundle_status,
            "verifier_rotation_state": verifier_rotation_state,
            "verifier_connectivity_status": verifier_connectivity_status,
            "broker_handoff_status": broker_handoff_status,
            "scenario_labels": scenario_labels,
            "outcome_summary": {
                "timeout_recovered": timeout_recovered,
                "protected_gate_paused": protected_gate_paused,
                "live_verifier_connectivity_bound": live_verifier_connectivity_bound,
                "verifier_rotation_cutover": verifier_rotation_cutover,
                "signal_pause_observed": signal_pause_observed,
                "signal_rollback_observed": signal_rollback_observed,
                "signal_fail_closed_observed": signal_fail_closed_observed,
                "artifact_revoked_fail_closed": artifact_revoked_fail_closed,
                "verifier_revoked_fail_closed": verifier_revoked_fail_closed,
                "method_b_broker_prepared": method_b_broker_prepared,
                "method_b_broker_confirmed": method_b_broker_confirmed,
                "cancelled": handle["status"] == "cancelled",
                "completed": handle["status"] == "completed",
            },
            "protected_gate_summary": {
                "artifact_sync_current": artifact_bundle_status == "current",
                "verifier_rotation_ready": verifier_rotation_state in {"stable", "rotated"},
                "verifier_connectivity_bound": live_verifier_connectivity_bound,
                "broker_handoff_prepared": method_b_broker_prepared,
                "broker_handoff_confirmed": method_b_broker_confirmed,
            },
            "compiled_at": utc_now_iso(),
        }
        receipt["receipt_digest"] = sha256_text(canonical_json(receipt))
        return receipt

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
        verifier_roster = handle.get("verifier_roster")
        if not isinstance(verifier_roster, Mapping):
            errors.append("verifier_roster must be a mapping")
        else:
            errors.extend(self._check_verifier_roster(verifier_roster, governance_artifacts))
        broker_handoff_receipt = handle.get("broker_handoff_receipt")
        if broker_handoff_receipt is not None:
            if not isinstance(broker_handoff_receipt, Mapping):
                errors.append("broker_handoff_receipt must be a mapping or null")
            else:
                errors.extend(self._check_broker_handoff_receipt(broker_handoff_receipt, handle))
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

    def validate_execution_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        errors: List[str] = []
        if receipt.get("kind") != "scheduler_execution_receipt":
            errors.append("kind must be scheduler_execution_receipt")
        if receipt.get("schema_version") != SCHEDULER_SCHEMA_VERSION:
            errors.append(f"schema_version must be {SCHEDULER_SCHEMA_VERSION}")
        self._check_non_empty_string(
            receipt.get("execution_receipt_id"),
            "execution_receipt_id",
            errors,
        )
        self._check_non_empty_string(receipt.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(receipt.get("plan_ref"), "plan_ref", errors)
        self._check_non_empty_string(receipt.get("identity_id"), "identity_id", errors)

        method = receipt.get("method")
        if method not in SCHEDULER_ALLOWED_METHODS:
            errors.append(f"method must be one of {sorted(SCHEDULER_ALLOWED_METHODS)}")
        else:
            expected_profile_id = SCHEDULER_EXECUTION_PROFILE_IDS[method]
            if receipt.get("execution_profile_id") != expected_profile_id:
                errors.append(
                    f"execution_profile_id must be {expected_profile_id} for method {method}"
                )

        stage_blueprint = receipt.get("stage_blueprint")
        if not isinstance(stage_blueprint, list) or not stage_blueprint:
            errors.append("stage_blueprint must be a non-empty list")
        elif method in SCHEDULER_ALLOWED_METHODS:
            expected_stage_blueprint = [stage["stage_id"] for stage in self._method_stages(method)]
            if stage_blueprint != expected_stage_blueprint:
                errors.append("stage_blueprint must match the fixed method blueprint")

        visited_stages = receipt.get("visited_stages")
        if not isinstance(visited_stages, list) or not visited_stages:
            errors.append("visited_stages must be a non-empty list")
        elif isinstance(stage_blueprint, list):
            stage_indices: List[int] = []
            for stage_id in visited_stages:
                if not isinstance(stage_id, str) or stage_id not in stage_blueprint:
                    errors.append("visited_stages must be drawn from stage_blueprint")
                    continue
                stage_indices.append(stage_blueprint.index(stage_id))
            if stage_indices != sorted(set(stage_indices)):
                errors.append("visited_stages must preserve blueprint order without duplicates")

        current_stage = receipt.get("current_stage")
        if isinstance(stage_blueprint, list):
            if not isinstance(current_stage, str) or current_stage not in stage_blueprint:
                errors.append("current_stage must be one of stage_blueprint")

        final_status = receipt.get("final_status")
        if final_status not in SCHEDULER_ALLOWED_STATUS:
            errors.append(f"final_status must be one of {sorted(SCHEDULER_ALLOWED_STATUS)}")

        history_length = receipt.get("history_length")
        if not isinstance(history_length, int) or history_length < 1:
            errors.append("history_length must be an integer >= 1")

        continuity_event_refs = receipt.get("continuity_event_refs")
        if not isinstance(continuity_event_refs, list) or not continuity_event_refs:
            errors.append("continuity_event_refs must be a non-empty list")
        else:
            if isinstance(history_length, int) and len(continuity_event_refs) != history_length:
                errors.append("continuity_event_refs length must match history_length")
            seen_event_refs: List[str] = []
            for index, event_ref in enumerate(continuity_event_refs):
                if not isinstance(event_ref, str) or not event_ref.strip():
                    errors.append(f"continuity_event_refs[{index}] must be a non-empty string")
                    continue
                if event_ref in seen_event_refs:
                    errors.append("continuity_event_refs must not contain duplicates")
                else:
                    seen_event_refs.append(event_ref)

        transition_counts = receipt.get("transition_counts")
        if not isinstance(transition_counts, Mapping):
            errors.append("transition_counts must be a mapping")
        else:
            total_transition_count = 0
            for transition in sorted(SCHEDULER_ALLOWED_TRANSITIONS):
                value = transition_counts.get(transition)
                if not isinstance(value, int) or value < 0:
                    errors.append(f"transition_counts.{transition} must be an integer >= 0")
                else:
                    total_transition_count += value
            extra_keys = [
                key
                for key in transition_counts.keys()
                if key not in SCHEDULER_ALLOWED_TRANSITIONS
            ]
            if extra_keys:
                errors.append("transition_counts contains unsupported keys")
            if isinstance(history_length, int) and total_transition_count != history_length:
                errors.append("sum of transition_counts must match history_length")

        for field_name, transition_name in (
            ("cancel_count", "cancel"),
            ("rollback_count", "rollback"),
            ("pause_count", "pause"),
            ("sync_count", "sync"),
            ("fail_count", "fail"),
        ):
            count = receipt.get(field_name)
            if not isinstance(count, int) or count < 0:
                errors.append(f"{field_name} must be an integer >= 0")
            elif isinstance(transition_counts, Mapping) and count != transition_counts.get(
                transition_name
            ):
                errors.append(f"{field_name} must match transition_counts.{transition_name}")

        governance_artifact_digest = receipt.get("governance_artifact_digest")
        if not isinstance(governance_artifact_digest, str) or len(governance_artifact_digest) != 64:
            errors.append("governance_artifact_digest must be 64 hex chars")

        artifact_bundle_status = receipt.get("artifact_bundle_status")
        if artifact_bundle_status not in SCHEDULER_ARTIFACT_BUNDLE_STATUS:
            errors.append(
                "artifact_bundle_status must be one of "
                f"{sorted(SCHEDULER_ARTIFACT_BUNDLE_STATUS)}"
            )

        verifier_rotation_state = receipt.get("verifier_rotation_state")
        if verifier_rotation_state not in SCHEDULER_VERIFIER_ROTATION_STATES:
            errors.append(
                "verifier_rotation_state must be one of "
                f"{sorted(SCHEDULER_VERIFIER_ROTATION_STATES)}"
            )

        verifier_connectivity_status = receipt.get("verifier_connectivity_status")
        if verifier_connectivity_status is not None and verifier_connectivity_status not in (
            SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES
        ):
            errors.append(
                "verifier_connectivity_status must be null or one of "
                f"{sorted(SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES)}"
            )

        broker_handoff_status = receipt.get("broker_handoff_status")
        if broker_handoff_status is not None and broker_handoff_status not in (
            SCHEDULER_METHOD_B_HANDOFF_STATUSES
        ):
            errors.append(
                "broker_handoff_status must be null or one of "
                f"{sorted(SCHEDULER_METHOD_B_HANDOFF_STATUSES)}"
            )
        if method in SCHEDULER_ALLOWED_METHODS and method != "B" and broker_handoff_status is not None:
            errors.append("broker_handoff_status must be null outside Method B")

        scenario_labels = receipt.get("scenario_labels")
        if not isinstance(scenario_labels, list):
            errors.append("scenario_labels must be a list")
        else:
            seen_labels: List[str] = []
            for label in scenario_labels:
                if label not in SCHEDULER_EXECUTION_SCENARIO_LABELS:
                    errors.append("scenario_labels must use the fixed label vocabulary")
                    continue
                if label in seen_labels:
                    errors.append("scenario_labels must not contain duplicates")
                else:
                    seen_labels.append(label)

        outcome_summary = receipt.get("outcome_summary")
        if not isinstance(outcome_summary, Mapping):
            errors.append("outcome_summary must be a mapping")
        else:
            for key in (
                "timeout_recovered",
                "protected_gate_paused",
                "live_verifier_connectivity_bound",
                "verifier_rotation_cutover",
                "signal_pause_observed",
                "signal_rollback_observed",
                "signal_fail_closed_observed",
                "artifact_revoked_fail_closed",
                "verifier_revoked_fail_closed",
                "method_b_broker_prepared",
                "method_b_broker_confirmed",
                "cancelled",
                "completed",
            ):
                if not isinstance(outcome_summary.get(key), bool):
                    errors.append(f"outcome_summary.{key} must be a boolean")
            if isinstance(final_status, str) and isinstance(outcome_summary.get("cancelled"), bool):
                if outcome_summary["cancelled"] != (final_status == "cancelled"):
                    errors.append("outcome_summary.cancelled must match final_status")
            if isinstance(final_status, str) and isinstance(outcome_summary.get("completed"), bool):
                if outcome_summary["completed"] != (final_status == "completed"):
                    errors.append("outcome_summary.completed must match final_status")
            if isinstance(scenario_labels, list):
                for key, label in (
                    ("timeout_recovered", "timeout-recovery"),
                    ("protected_gate_paused", "protected-gate-pause"),
                    ("live_verifier_connectivity_bound", "live-verifier-connectivity"),
                    ("verifier_rotation_cutover", "verifier-rotation-cutover"),
                    ("signal_pause_observed", "signal-pause"),
                    ("signal_rollback_observed", "signal-rollback"),
                    ("signal_fail_closed_observed", "signal-fail-closed"),
                    ("artifact_revoked_fail_closed", "artifact-revoked"),
                    ("verifier_revoked_fail_closed", "verifier-revoked"),
                    ("method_b_broker_prepared", "broker-handoff-prepared"),
                    ("method_b_broker_confirmed", "broker-handoff-confirmed"),
                    ("cancelled", "cancelled"),
                    ("completed", "completed"),
                ):
                    if key in outcome_summary and isinstance(outcome_summary.get(key), bool):
                        if outcome_summary[key] != (label in scenario_labels):
                            errors.append(
                                f"outcome_summary.{key} must match scenario_labels inclusion for {label}"
                            )

        protected_gate_summary = receipt.get("protected_gate_summary")
        if not isinstance(protected_gate_summary, Mapping):
            errors.append("protected_gate_summary must be a mapping")
        else:
            for key in (
                "artifact_sync_current",
                "verifier_rotation_ready",
                "verifier_connectivity_bound",
                "broker_handoff_prepared",
                "broker_handoff_confirmed",
            ):
                if not isinstance(protected_gate_summary.get(key), bool):
                    errors.append(f"protected_gate_summary.{key} must be a boolean")
            if (
                isinstance(protected_gate_summary.get("artifact_sync_current"), bool)
                and artifact_bundle_status in SCHEDULER_ARTIFACT_BUNDLE_STATUS
                and protected_gate_summary["artifact_sync_current"]
                != (artifact_bundle_status == "current")
            ):
                errors.append(
                    "protected_gate_summary.artifact_sync_current must match artifact_bundle_status"
                )
            if (
                isinstance(protected_gate_summary.get("verifier_rotation_ready"), bool)
                and verifier_rotation_state in SCHEDULER_VERIFIER_ROTATION_STATES
                and protected_gate_summary["verifier_rotation_ready"]
                != (verifier_rotation_state in {"stable", "rotated"})
            ):
                errors.append(
                    "protected_gate_summary.verifier_rotation_ready must match verifier_rotation_state"
                )
            if (
                isinstance(protected_gate_summary.get("verifier_connectivity_bound"), bool)
                and protected_gate_summary["verifier_connectivity_bound"]
                != (verifier_connectivity_status == "reachable")
            ):
                errors.append(
                    "protected_gate_summary.verifier_connectivity_bound must match verifier_connectivity_status"
                )
            if (
                isinstance(protected_gate_summary.get("broker_handoff_prepared"), bool)
                and protected_gate_summary["broker_handoff_prepared"]
                != (broker_handoff_status in {"prepared", "confirmed"})
            ):
                errors.append(
                    "protected_gate_summary.broker_handoff_prepared must match broker_handoff_status"
                )
            if (
                isinstance(protected_gate_summary.get("broker_handoff_confirmed"), bool)
                and protected_gate_summary["broker_handoff_confirmed"]
                != (broker_handoff_status == "confirmed")
            ):
                errors.append(
                    "protected_gate_summary.broker_handoff_confirmed must match broker_handoff_status"
                )

        self._check_non_empty_string(receipt.get("compiled_at"), "compiled_at", errors)
        receipt_digest = receipt.get("receipt_digest")
        if not isinstance(receipt_digest, str) or len(receipt_digest) != 64:
            errors.append("receipt_digest must be 64 hex chars")
        else:
            digest_payload = {
                key: value for key, value in receipt.items() if key != "receipt_digest"
            }
            if receipt_digest != sha256_text(canonical_json(digest_payload)):
                errors.append("receipt_digest must match the canonical digest-less payload")

        return {
            "ok": not errors,
            "errors": errors,
            "final_status": final_status,
            "method": method,
            "history_length": history_length if isinstance(history_length, int) else 0,
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
        verifier_roster = handle.get("verifier_roster")
        if isinstance(verifier_roster, Mapping):
            payload["verifier_rotation_state"] = verifier_roster.get("rotation_state", "unverified")
            payload["verifier_root_id"] = verifier_roster.get("active_root_id")
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

    def _initial_verifier_roster(self, governance_artifacts: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "policy_id": SCHEDULER_VERIFIER_ROSTER_POLICY_ID,
            "roster_ref": self._expected_verifier_roster_ref(governance_artifacts),
            "checked_at": None,
            "active_root_id": None,
            "next_root_id": None,
            "rotation_state": "unverified",
            "accepted_roots": [],
            "proof_digest": None,
            "external_sync_ref": None,
            "dual_attestation_required": False,
            "dual_attested": False,
            "connectivity_receipt": None,
        }

    def _normalize_artifact_sync_report(
        self,
        value: Any,
        governance_artifacts: Mapping[str, Any],
        *,
        checked_at: str,
    ) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("sync_report must be a mapping")
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

    def _normalize_verifier_roster_report(
        self,
        value: Any,
        governance_artifacts: Mapping[str, Any],
        *,
        checked_at: str,
    ) -> Dict[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError("verifier_roster must be a mapping")
        raw_roots = value.get("accepted_roots")
        if not isinstance(raw_roots, Sequence) or isinstance(raw_roots, (str, bytes)):
            raise ValueError("verifier_roster.accepted_roots must be a sequence")

        normalized_roots: List[Dict[str, Any]] = []
        for index, raw_root in enumerate(raw_roots):
            if not isinstance(raw_root, Mapping):
                raise ValueError("verifier_roster.accepted_roots items must be mappings")
            root_id = self._normalize_non_empty_string(
                raw_root.get("root_id"),
                f"verifier_roster.accepted_roots[{index}].root_id",
            )
            fingerprint = self._normalize_non_empty_string(
                raw_root.get("fingerprint"),
                f"verifier_roster.accepted_roots[{index}].fingerprint",
            )
            if len(fingerprint) != 64:
                raise ValueError(
                    f"verifier_roster.accepted_roots[{index}].fingerprint must be 64 chars"
                )
            status = self._normalize_non_empty_string(
                raw_root.get("status"),
                f"verifier_roster.accepted_roots[{index}].status",
            )
            if status not in SCHEDULER_VERIFIER_ROOT_STATUSES:
                raise ValueError(
                    "verifier_roster.accepted_roots status must be one of "
                    f"{sorted(SCHEDULER_VERIFIER_ROOT_STATUSES)}"
                )
            normalized_roots.append(
                {
                    "root_id": root_id,
                    "fingerprint": fingerprint,
                    "status": status,
                }
            )

        normalized = {
            "policy_id": SCHEDULER_VERIFIER_ROSTER_POLICY_ID,
            "roster_ref": self._normalize_artifact_ref(
                value.get("roster_ref"),
                "verifier_roster.roster_ref",
                "verifier://",
            ),
            "checked_at": checked_at,
            "active_root_id": self._normalize_optional_non_empty_string(
                value.get("active_root_id"),
                "verifier_roster.active_root_id",
            ),
            "next_root_id": self._normalize_optional_non_empty_string(
                value.get("next_root_id"),
                "verifier_roster.next_root_id",
            ),
            "rotation_state": self._normalize_verifier_rotation_state(
                value.get("rotation_state")
            ),
            "accepted_roots": normalized_roots,
            "proof_digest": self._normalize_optional_digest(
                value.get("proof_digest"),
                "verifier_roster.proof_digest",
                allow_none=False,
            ),
            "external_sync_ref": self._normalize_optional_sync_ref(
                value.get("external_sync_ref"),
                allow_none=False,
            ),
            "dual_attestation_required": self._normalize_bool(
                value.get("dual_attestation_required"),
                "verifier_roster.dual_attestation_required",
            ),
            "dual_attested": self._normalize_bool(
                value.get("dual_attested"),
                "verifier_roster.dual_attested",
            ),
            "connectivity_receipt": self._normalize_optional_connectivity_receipt(
                value.get("connectivity_receipt"),
                roster_ref=self._normalize_artifact_ref(
                    value.get("roster_ref"),
                    "verifier_roster.roster_ref",
                    "verifier://",
                ),
                roster_checked_at=checked_at,
                active_root_id=self._normalize_optional_non_empty_string(
                    value.get("active_root_id"),
                    "verifier_roster.active_root_id",
                ),
                rotation_state=self._normalize_verifier_rotation_state(
                    value.get("rotation_state")
                ),
                accepted_root_count=len(normalized_roots),
            ),
        }
        errors = self._check_verifier_roster(normalized, governance_artifacts)
        if errors:
            raise ValueError(errors[0])
        return normalized

    def _normalize_optional_connectivity_receipt(
        self,
        value: Any,
        *,
        roster_ref: str,
        roster_checked_at: str,
        active_root_id: Optional[str],
        rotation_state: str,
        accepted_root_count: int,
    ) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise ValueError("verifier_roster.connectivity_receipt must be a mapping or null")
        normalized = {
            "kind": self._expect_string(
                value.get("kind"),
                "verifier_roster.connectivity_receipt.kind",
                "governance_verifier_connectivity_receipt",
            ),
            "schema_version": self._expect_schema_version(value.get("schema_version")),
            "receipt_id": self._normalize_non_empty_string(
                value.get("receipt_id"),
                "verifier_roster.connectivity_receipt.receipt_id",
            ),
            "roster_ref": self._normalize_artifact_ref(
                value.get("roster_ref"),
                "verifier_roster.connectivity_receipt.roster_ref",
                "verifier://",
            ),
            "verifier_endpoint": self._normalize_live_verifier_endpoint(
                value.get("verifier_endpoint"),
                "verifier_roster.connectivity_receipt.verifier_endpoint",
            ),
            "transport_profile": self._expect_string(
                value.get("transport_profile"),
                "verifier_roster.connectivity_receipt.transport_profile",
                SCHEDULER_VERIFIER_CONNECTIVITY_TRANSPORT_PROFILE,
            ),
            "roster_checked_at": self._normalize_non_empty_string(
                value.get("roster_checked_at"),
                "verifier_roster.connectivity_receipt.roster_checked_at",
            ),
            "recorded_at": self._normalize_non_empty_string(
                value.get("recorded_at"),
                "verifier_roster.connectivity_receipt.recorded_at",
            ),
            "request_timeout_ms": self._normalize_positive_int(
                value.get("request_timeout_ms"),
                "verifier_roster.connectivity_receipt.request_timeout_ms",
            ),
            "observed_latency_ms": self._normalize_non_negative_float(
                value.get("observed_latency_ms"),
                "verifier_roster.connectivity_receipt.observed_latency_ms",
            ),
            "http_status": self._normalize_http_status(
                value.get("http_status"),
                "verifier_roster.connectivity_receipt.http_status",
            ),
            "response_digest": self._normalize_optional_digest(
                value.get("response_digest"),
                "verifier_roster.connectivity_receipt.response_digest",
                allow_none=False,
            ),
            "receipt_status": self._normalize_connectivity_receipt_status(
                value.get("receipt_status")
            ),
            "active_root_id": self._normalize_optional_non_empty_string(
                value.get("active_root_id"),
                "verifier_roster.connectivity_receipt.active_root_id",
            ),
            "rotation_state": self._normalize_verifier_rotation_state(
                value.get("rotation_state")
            ),
            "accepted_root_count": self._normalize_non_negative_int(
                value.get("accepted_root_count"),
                "verifier_roster.connectivity_receipt.accepted_root_count",
            ),
        }
        if normalized["roster_ref"] != roster_ref:
            raise ValueError(
                "verifier_roster.connectivity_receipt.roster_ref must match verifier_roster.roster_ref"
            )
        if normalized["roster_checked_at"] != roster_checked_at:
            raise ValueError(
                "verifier_roster.connectivity_receipt.roster_checked_at must match verifier_roster.checked_at"
            )
        if normalized["active_root_id"] != active_root_id:
            raise ValueError(
                "verifier_roster.connectivity_receipt.active_root_id must match verifier_roster.active_root_id"
            )
        if normalized["rotation_state"] != rotation_state:
            raise ValueError(
                "verifier_roster.connectivity_receipt.rotation_state must match verifier_roster.rotation_state"
            )
        if normalized["accepted_root_count"] != accepted_root_count:
            raise ValueError(
                "verifier_roster.connectivity_receipt.accepted_root_count must match verifier_roster.accepted_roots"
            )
        return normalized

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

    def _check_verifier_roster(
        self,
        value: Mapping[str, Any],
        governance_artifacts: Any,
    ) -> List[str]:
        errors: List[str] = []
        if value.get("policy_id") != SCHEDULER_VERIFIER_ROSTER_POLICY_ID:
            errors.append(
                f"verifier_roster.policy_id must be {SCHEDULER_VERIFIER_ROSTER_POLICY_ID}"
            )
        expected_roster_ref = (
            self._expected_verifier_roster_ref(governance_artifacts)
            if isinstance(governance_artifacts, Mapping)
            else None
        )
        if value.get("roster_ref") != expected_roster_ref:
            errors.append("verifier_roster.roster_ref must match governance_artifacts")
        checked_at = value.get("checked_at")
        if checked_at is not None and (not isinstance(checked_at, str) or not checked_at.strip()):
            errors.append("verifier_roster.checked_at must be a string or null")
        rotation_state = value.get("rotation_state")
        if rotation_state not in SCHEDULER_VERIFIER_ROTATION_STATES:
            errors.append(
                "verifier_roster.rotation_state must be one of "
                f"{sorted(SCHEDULER_VERIFIER_ROTATION_STATES)}"
            )
        active_root_id = value.get("active_root_id")
        if active_root_id is not None and (not isinstance(active_root_id, str) or not active_root_id.strip()):
            errors.append("verifier_roster.active_root_id must be a string or null")
        next_root_id = value.get("next_root_id")
        if next_root_id is not None and (not isinstance(next_root_id, str) or not next_root_id.strip()):
            errors.append("verifier_roster.next_root_id must be a string or null")
        proof_digest = value.get("proof_digest")
        if proof_digest is not None and (
            not isinstance(proof_digest, str) or len(proof_digest) != 64
        ):
            errors.append("verifier_roster.proof_digest must be 64 hex chars or null")
        external_sync_ref = value.get("external_sync_ref")
        if external_sync_ref is not None and (
            not isinstance(external_sync_ref, str)
            or not external_sync_ref.startswith("sync://")
        ):
            errors.append("verifier_roster.external_sync_ref must start with sync:// or be null")

        dual_attestation_required = value.get("dual_attestation_required")
        if not isinstance(dual_attestation_required, bool):
            errors.append("verifier_roster.dual_attestation_required must be a boolean")
        dual_attested = value.get("dual_attested")
        if not isinstance(dual_attested, bool):
            errors.append("verifier_roster.dual_attested must be a boolean")
        connectivity_receipt = value.get("connectivity_receipt")
        if connectivity_receipt is not None and not isinstance(connectivity_receipt, Mapping):
            errors.append("verifier_roster.connectivity_receipt must be a mapping or null")

        accepted_roots = value.get("accepted_roots")
        if not isinstance(accepted_roots, list):
            errors.append("verifier_roster.accepted_roots must be a list")
            return errors
        if len(accepted_roots) > SCHEDULER_VERIFIER_MAX_TRACKED_ROOTS:
            errors.append(
                "verifier_roster.accepted_roots must not exceed "
                f"{SCHEDULER_VERIFIER_MAX_TRACKED_ROOTS} items"
            )

        seen_root_ids: List[str] = []
        status_by_root_id: Dict[str, str] = {}
        for item in accepted_roots:
            if not isinstance(item, Mapping):
                errors.append("verifier_roster.accepted_roots items must be mappings")
                continue
            root_id = item.get("root_id")
            if not isinstance(root_id, str) or not root_id.strip():
                errors.append("verifier_roster.accepted_roots.root_id must be a non-empty string")
                continue
            if root_id in seen_root_ids:
                errors.append(f"verifier_roster.accepted_roots.root_id duplicated: {root_id}")
            else:
                seen_root_ids.append(root_id)
            fingerprint = item.get("fingerprint")
            if not isinstance(fingerprint, str) or len(fingerprint) != 64:
                errors.append(
                    f"verifier_roster.accepted_roots[{root_id}].fingerprint must be 64 chars"
                )
            status = item.get("status")
            if status not in SCHEDULER_VERIFIER_ROOT_STATUSES:
                errors.append(
                    "verifier_roster.accepted_roots.status must be one of "
                    f"{sorted(SCHEDULER_VERIFIER_ROOT_STATUSES)}"
                )
                continue
            status_by_root_id[root_id] = status

        if errors:
            return errors

        active_roots = [root_id for root_id, status in status_by_root_id.items() if status == "active"]
        candidate_roots = [
            root_id for root_id, status in status_by_root_id.items() if status == "candidate"
        ]
        retired_roots = [root_id for root_id, status in status_by_root_id.items() if status == "retired"]
        if rotation_state == "unverified":
            if accepted_roots:
                errors.append("verifier_roster.accepted_roots must be empty while unverified")
            if active_root_id is not None:
                errors.append("verifier_roster.active_root_id must be null while unverified")
            if next_root_id is not None:
                errors.append("verifier_roster.next_root_id must be null while unverified")
            if proof_digest is not None:
                errors.append("verifier_roster.proof_digest must be null while unverified")
            if external_sync_ref is not None:
                errors.append("verifier_roster.external_sync_ref must be null while unverified")
            if dual_attestation_required or dual_attested:
                errors.append("verifier_roster dual attestation flags must be false while unverified")
            if isinstance(connectivity_receipt, Mapping):
                errors.extend(
                    self._check_connectivity_receipt(
                        connectivity_receipt,
                        roster_ref=value.get("roster_ref"),
                        checked_at=checked_at,
                        active_root_id=active_root_id,
                        rotation_state=rotation_state,
                        accepted_root_count=len(accepted_roots),
                    )
                )
            return errors

        if active_root_id not in status_by_root_id:
            errors.append("verifier_roster.active_root_id must reference one accepted root")
        elif status_by_root_id[active_root_id] != "active":
            errors.append("verifier_roster.active_root_id must reference an active root")
        if len(active_roots) != 1:
            errors.append("verifier_roster.accepted_roots must contain exactly one active root")
        if checked_at is None:
            errors.append("verifier_roster.checked_at must be set once verified")
        if proof_digest is None:
            errors.append("verifier_roster.proof_digest must be set once verified")
        if external_sync_ref is None:
            errors.append("verifier_roster.external_sync_ref must be set once verified")

        if rotation_state == "stable":
            if len(accepted_roots) != 1 or candidate_roots or retired_roots:
                errors.append("stable verifier roster must contain exactly one active root")
            if next_root_id is not None:
                errors.append("verifier_roster.next_root_id must be null when stable")
            if dual_attestation_required or dual_attested:
                errors.append("stable verifier roster must not require dual attestation")
        elif rotation_state == "overlap-required":
            if len(accepted_roots) != 2 or len(candidate_roots) != 1:
                errors.append(
                    "overlap-required verifier roster must contain active and candidate roots"
                )
            if next_root_id not in candidate_roots:
                errors.append(
                    "verifier_roster.next_root_id must reference the candidate root during overlap"
                )
            if dual_attestation_required is not True or dual_attested is not False:
                errors.append(
                    "overlap-required verifier roster must require but not yet satisfy dual attestation"
                )
        elif rotation_state == "rotated":
            if len(accepted_roots) != 2 or len(retired_roots) != 1:
                errors.append("rotated verifier roster must contain active and retired roots")
            if next_root_id is not None:
                errors.append("verifier_roster.next_root_id must be null after cutover")
            if dual_attestation_required or dual_attested is not True:
                errors.append(
                    "rotated verifier roster must record completed dual attestation"
                )
        elif rotation_state == "revoked":
            if next_root_id is not None:
                errors.append("verifier_roster.next_root_id must be null when revoked")
            if dual_attestation_required:
                errors.append("revoked verifier roster must not require dual attestation")
        if isinstance(connectivity_receipt, Mapping):
            errors.extend(
                self._check_connectivity_receipt(
                    connectivity_receipt,
                    roster_ref=value.get("roster_ref"),
                    checked_at=checked_at,
                    active_root_id=active_root_id,
                    rotation_state=rotation_state,
                    accepted_root_count=len(accepted_roots),
                )
            )
        return errors

    def _check_broker_handoff_receipt(
        self,
        value: Mapping[str, Any],
        handle: Mapping[str, Any],
    ) -> List[str]:
        errors: List[str] = []
        if value.get("kind") != "scheduler_method_b_handoff_receipt":
            errors.append("broker_handoff_receipt.kind must be scheduler_method_b_handoff_receipt")
        if value.get("schema_version") != SCHEDULER_SCHEMA_VERSION:
            errors.append(
                f"broker_handoff_receipt.schema_version must be {SCHEDULER_SCHEMA_VERSION}"
            )
        if value.get("handle_id") != handle.get("handle_id"):
            errors.append("broker_handoff_receipt.handle_id must match handle.handle_id")
        if value.get("plan_ref") != handle.get("plan_ref"):
            errors.append("broker_handoff_receipt.plan_ref must match handle.plan_ref")
        if value.get("identity_id") != handle.get("identity_id"):
            errors.append("broker_handoff_receipt.identity_id must match handle.identity_id")
        if value.get("method") != "B":
            errors.append("broker_handoff_receipt.method must be B")
        if value.get("policy_id") != SCHEDULER_METHOD_B_HANDOFF_POLICY_ID:
            errors.append(
                "broker_handoff_receipt.policy_id must be "
                f"{SCHEDULER_METHOD_B_HANDOFF_POLICY_ID}"
            )
        if value.get("review_stage_id") != SCHEDULER_METHOD_B_PREPARE_STAGE:
            errors.append(
                "broker_handoff_receipt.review_stage_id must be dual-channel-review"
            )
        if value.get("handoff_stage_id") != SCHEDULER_METHOD_B_HANDOFF_STAGE:
            errors.append(
                "broker_handoff_receipt.handoff_stage_id must be authority-handoff"
            )
        if value.get("retirement_stage_id") != SCHEDULER_METHOD_B_RETIRE_STAGE:
            errors.append(
                "broker_handoff_receipt.retirement_stage_id must be bio-retirement"
            )
        status = value.get("status")
        if status not in SCHEDULER_METHOD_B_HANDOFF_STATUSES:
            errors.append(
                "broker_handoff_receipt.status must be one of "
                f"{sorted(SCHEDULER_METHOD_B_HANDOFF_STATUSES)}"
            )
        for field_name in (
            "receipt_id",
            "source_substrate",
            "destination_substrate",
            "source_host_ref",
            "source_host_attestation_ref",
            "source_jurisdiction",
            "source_network_zone",
            "destination_host_ref",
            "destination_host_attestation_ref",
            "destination_jurisdiction",
            "destination_network_zone",
            "substrate_cluster_ref",
            "cross_host_binding_profile",
            "host_binding_digest",
            "broker_signal_id",
            "standby_probe_id",
            "source_attestation_id",
            "attestation_chain_id",
            "dual_allocation_window_id",
            "attestation_stream_id",
            "allocation_pair_digest",
            "handoff_state_digest",
            "prepared_at",
        ):
            self._check_non_empty_string(value.get(field_name), f"broker_handoff_receipt.{field_name}", errors)
        distinct_host_count = value.get("distinct_host_count")
        if not isinstance(distinct_host_count, int) or distinct_host_count < 2:
            errors.append("broker_handoff_receipt.distinct_host_count must be an integer >= 2")
        if value.get("broker_signal_severity") != "critical":
            errors.append("broker_handoff_receipt.broker_signal_severity must be critical")
        if value.get("recommended_action") != "migrate-standby":
            errors.append(
                "broker_handoff_receipt.recommended_action must be migrate-standby"
            )
        scheduler_signal = value.get("scheduler_signal")
        if not isinstance(scheduler_signal, Mapping):
            errors.append("broker_handoff_receipt.scheduler_signal must be a mapping")
        else:
            if scheduler_signal.get("severity") != "critical":
                errors.append("broker_handoff_receipt.scheduler_signal.severity must be critical")
            if scheduler_signal.get("source_substrate") != value.get("source_substrate"):
                errors.append(
                    "broker_handoff_receipt.scheduler_signal.source_substrate must match source_substrate"
                )
            self._check_non_empty_string(
                scheduler_signal.get("reason"),
                "broker_handoff_receipt.scheduler_signal.reason",
                errors,
            )
        confirmed_at = value.get("confirmed_at")
        if status == "prepared":
            if confirmed_at is not None:
                errors.append("broker_handoff_receipt.confirmed_at must be null while prepared")
            for field_name in (
                "migration_transfer_id",
                "migration_state_digest",
                "dual_allocation_close_id",
                "cleanup_release_status",
            ):
                if value.get(field_name) is not None:
                    errors.append(f"broker_handoff_receipt.{field_name} must be null while prepared")
        elif status == "confirmed":
            self._check_non_empty_string(
                confirmed_at,
                "broker_handoff_receipt.confirmed_at",
                errors,
            )
            self._check_non_empty_string(
                value.get("migration_transfer_id"),
                "broker_handoff_receipt.migration_transfer_id",
                errors,
            )
            self._check_non_empty_string(
                value.get("migration_state_digest"),
                "broker_handoff_receipt.migration_state_digest",
                errors,
            )
            self._check_non_empty_string(
                value.get("dual_allocation_close_id"),
                "broker_handoff_receipt.dual_allocation_close_id",
                errors,
            )
            if value.get("cleanup_release_status") != "released":
                errors.append(
                    "broker_handoff_receipt.cleanup_release_status must be released when confirmed"
                )
        return errors

    def _check_connectivity_receipt(
        self,
        value: Mapping[str, Any],
        *,
        roster_ref: Any,
        checked_at: Any,
        active_root_id: Any,
        rotation_state: Any,
        accepted_root_count: int,
    ) -> List[str]:
        errors: List[str] = []
        if value.get("kind") != "governance_verifier_connectivity_receipt":
            errors.append(
                "verifier_roster.connectivity_receipt.kind must be governance_verifier_connectivity_receipt"
            )
        if value.get("schema_version") != SCHEDULER_SCHEMA_VERSION:
            errors.append(
                f"verifier_roster.connectivity_receipt.schema_version must be {SCHEDULER_SCHEMA_VERSION}"
            )
        self._check_non_empty_string(
            value.get("receipt_id"),
            "verifier_roster.connectivity_receipt.receipt_id",
            errors,
        )
        verifier_endpoint = value.get("verifier_endpoint")
        if not isinstance(verifier_endpoint, str) or not verifier_endpoint.strip():
            errors.append(
                "verifier_roster.connectivity_receipt.verifier_endpoint must be a non-empty string"
            )
        elif not (
            verifier_endpoint.startswith("http://") or verifier_endpoint.startswith("https://")
        ):
            errors.append(
                "verifier_roster.connectivity_receipt.verifier_endpoint must start with http:// or https://"
            )
        if (
            value.get("transport_profile")
            != SCHEDULER_VERIFIER_CONNECTIVITY_TRANSPORT_PROFILE
        ):
            errors.append(
                "verifier_roster.connectivity_receipt.transport_profile must match live verifier transport profile"
            )
        self._check_non_empty_string(
            value.get("roster_checked_at"),
            "verifier_roster.connectivity_receipt.roster_checked_at",
            errors,
        )
        self._check_non_empty_string(
            value.get("recorded_at"),
            "verifier_roster.connectivity_receipt.recorded_at",
            errors,
        )
        request_timeout_ms = value.get("request_timeout_ms")
        if not isinstance(request_timeout_ms, int) or request_timeout_ms < 1:
            errors.append(
                "verifier_roster.connectivity_receipt.request_timeout_ms must be a positive integer"
            )
        observed_latency_ms = value.get("observed_latency_ms")
        if not isinstance(observed_latency_ms, (int, float)) or observed_latency_ms < 0:
            errors.append(
                "verifier_roster.connectivity_receipt.observed_latency_ms must be non-negative"
            )
        http_status = value.get("http_status")
        if not isinstance(http_status, int) or http_status < 100 or http_status > 599:
            errors.append(
                "verifier_roster.connectivity_receipt.http_status must be a valid HTTP status code"
            )
        response_digest = value.get("response_digest")
        if not isinstance(response_digest, str) or len(response_digest) != 64:
            errors.append(
                "verifier_roster.connectivity_receipt.response_digest must be 64 chars"
            )
        receipt_status = value.get("receipt_status")
        if receipt_status not in SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES:
            errors.append(
                "verifier_roster.connectivity_receipt.receipt_status must be one of "
                f"{sorted(SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES)}"
            )
        if value.get("roster_ref") != roster_ref:
            errors.append(
                "verifier_roster.connectivity_receipt.roster_ref must match verifier_roster.roster_ref"
            )
        if value.get("roster_checked_at") != checked_at:
            errors.append(
                "verifier_roster.connectivity_receipt.roster_checked_at must match verifier_roster.checked_at"
            )
        if value.get("active_root_id") != active_root_id:
            errors.append(
                "verifier_roster.connectivity_receipt.active_root_id must match verifier_roster.active_root_id"
            )
        if value.get("rotation_state") != rotation_state:
            errors.append(
                "verifier_roster.connectivity_receipt.rotation_state must match verifier_roster.rotation_state"
            )
        if value.get("accepted_root_count") != accepted_root_count:
            errors.append(
                "verifier_roster.connectivity_receipt.accepted_root_count must match verifier_roster.accepted_roots"
            )
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

    def _expected_verifier_roster_ref(self, governance_artifacts: Mapping[str, Any]) -> str:
        artifact_bundle_ref = governance_artifacts["artifact_bundle_ref"]
        return artifact_bundle_ref.replace("artifact://", "verifier://", 1).replace(
            "/bundle",
            "/root-roster",
        )

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
        verifier_roster = handle.get("verifier_roster")
        if (
            not isinstance(verifier_roster, Mapping)
            or verifier_roster.get("rotation_state") not in {"stable", "rotated"}
        ):
            raise ValueError(
                f"verifier root rotation must be stable before entering {next_stage}"
            )

    def _ensure_method_b_handoff_for_stage(
        self,
        handle: Mapping[str, Any],
        plan: Mapping[str, Any],
        next_stage: str,
    ) -> None:
        if plan["method"] != "B":
            return
        if next_stage not in {
            SCHEDULER_METHOD_B_HANDOFF_STAGE,
            SCHEDULER_METHOD_B_RETIRE_STAGE,
        }:
            return
        receipt = handle.get("broker_handoff_receipt")
        if not isinstance(receipt, Mapping):
            raise ValueError(
                f"broker handoff receipt must be prepared before entering {next_stage}"
            )
        status = receipt.get("status")
        if next_stage == SCHEDULER_METHOD_B_HANDOFF_STAGE and status not in {"prepared", "confirmed"}:
            raise ValueError(
                "broker handoff receipt must be prepared before entering authority-handoff"
            )
        if next_stage == SCHEDULER_METHOD_B_RETIRE_STAGE and status != "confirmed":
            raise ValueError(
                "broker handoff receipt must be confirmed before entering bio-retirement"
            )

    def _normalize_non_empty_string(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def _normalize_optional_non_empty_string(self, value: Any, field_name: str) -> Optional[str]:
        if value is None:
            return None
        return self._normalize_non_empty_string(value, field_name)

    def _normalize_bool(self, value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} must be a boolean")
        return value

    def _normalize_connectivity_receipt_status(self, value: Any) -> str:
        status = self._normalize_non_empty_string(
            value,
            "verifier_roster.connectivity_receipt.receipt_status",
        )
        if status not in SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES:
            raise ValueError(
                "verifier_roster.connectivity_receipt.receipt_status must be one of "
                f"{sorted(SCHEDULER_VERIFIER_CONNECTIVITY_RECEIPT_STATUSES)}"
            )
        return status

    def _normalize_http_status(self, value: Any, field_name: str) -> int:
        if not isinstance(value, int) or value < 100 or value > 599:
            raise ValueError(f"{field_name} must be a valid HTTP status code")
        return value

    def _normalize_live_verifier_endpoint(self, value: Any, field_name: str) -> str:
        normalized = self._normalize_non_empty_string(value, field_name)
        if not (normalized.startswith("http://") or normalized.startswith("https://")):
            raise ValueError(f"{field_name} must start with http:// or https://")
        return normalized

    def _normalize_non_negative_float(self, value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number")
        if value < 0:
            raise ValueError(f"{field_name} must be >= 0")
        return float(value)

    def _normalize_non_negative_int(self, value: Any, field_name: str) -> int:
        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        if value < 0:
            raise ValueError(f"{field_name} must be >= 0")
        return value

    def _normalize_method_b_handoff_receipt(
        self,
        *,
        handle: Mapping[str, Any],
        broker_signal: Mapping[str, Any],
        standby_probe: Mapping[str, Any],
        attestation_chain: Mapping[str, Any],
        dual_allocation_window: Mapping[str, Any],
        attestation_stream: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(broker_signal, Mapping):
            raise ValueError("broker_signal must be a mapping")
        if not isinstance(standby_probe, Mapping):
            raise ValueError("standby_probe must be a mapping")
        if not isinstance(attestation_chain, Mapping):
            raise ValueError("attestation_chain must be a mapping")
        if not isinstance(dual_allocation_window, Mapping):
            raise ValueError("dual_allocation_window must be a mapping")
        if not isinstance(attestation_stream, Mapping):
            raise ValueError("attestation_stream must be a mapping")

        identity_id = self._normalize_non_empty_string(handle["identity_id"], "handle.identity_id")
        signal_identity = self._normalize_non_empty_string(
            broker_signal.get("identity_id"),
            "broker_signal.identity_id",
        )
        if signal_identity != identity_id:
            raise ValueError("broker_signal.identity_id must match the schedule identity")
        signal_id = self._normalize_non_empty_string(broker_signal.get("signal_id"), "broker_signal.signal_id")
        signal_source = self._normalize_non_empty_string(
            broker_signal.get("source_substrate"),
            "broker_signal.source_substrate",
        )
        signal_destination = self._normalize_non_empty_string(
            broker_signal.get("standby_substrate"),
            "broker_signal.standby_substrate",
        )
        signal_severity = self._normalize_non_empty_string(
            broker_signal.get("severity"),
            "broker_signal.severity",
        )
        if signal_severity != "critical":
            raise ValueError("broker_signal.severity must be critical")
        recommended_action = self._normalize_non_empty_string(
            broker_signal.get("recommended_action"),
            "broker_signal.recommended_action",
        )
        if recommended_action != "migrate-standby":
            raise ValueError("broker_signal.recommended_action must be migrate-standby")
        scheduler_input = broker_signal.get("scheduler_input")
        if not isinstance(scheduler_input, Mapping):
            raise ValueError("broker_signal.scheduler_input must be a mapping")
        scheduler_severity = self._normalize_non_empty_string(
            scheduler_input.get("severity"),
            "broker_signal.scheduler_input.severity",
        )
        if scheduler_severity != "critical":
            raise ValueError("broker_signal.scheduler_input.severity must be critical")
        scheduler_source = self._normalize_non_empty_string(
            scheduler_input.get("source_substrate"),
            "broker_signal.scheduler_input.source_substrate",
        )
        if scheduler_source != signal_source:
            raise ValueError(
                "broker_signal.scheduler_input.source_substrate must match broker_signal.source_substrate"
            )
        scheduler_reason = self._normalize_non_empty_string(
            scheduler_input.get("reason"),
            "broker_signal.scheduler_input.reason",
        )

        probe_identity = self._normalize_non_empty_string(
            standby_probe.get("identity_id"),
            "standby_probe.identity_id",
        )
        if probe_identity != identity_id:
            raise ValueError("standby_probe.identity_id must match the schedule identity")
        standby_substrate_id = self._normalize_non_empty_string(
            standby_probe.get("standby_substrate_id"),
            "standby_probe.standby_substrate_id",
        )
        if standby_substrate_id != signal_destination:
            raise ValueError(
                "standby_probe.standby_substrate_id must match broker_signal.standby_substrate"
            )
        if not self._normalize_bool(
            standby_probe.get("ready_for_migrate"),
            "standby_probe.ready_for_migrate",
        ):
            raise ValueError("standby_probe.ready_for_migrate must be true")
        if self._normalize_non_empty_string(
            standby_probe.get("probe_status"),
            "standby_probe.probe_status",
        ) != "ready":
            raise ValueError("standby_probe.probe_status must be ready")
        source_substrate_id = self._normalize_non_empty_string(
            standby_probe.get("active_substrate_id"),
            "standby_probe.active_substrate_id",
        )
        if source_substrate_id != signal_source:
            raise ValueError(
                "standby_probe.active_substrate_id must match broker_signal.source_substrate"
            )
        attestation_chain_id = self._normalize_non_empty_string(
            attestation_chain.get("chain_id"),
            "attestation_chain.chain_id",
        )
        if self._normalize_non_empty_string(
            attestation_chain.get("identity_id"),
            "attestation_chain.identity_id",
        ) != identity_id:
            raise ValueError("attestation_chain.identity_id must match the schedule identity")
        if self._normalize_non_empty_string(
            attestation_chain.get("active_substrate_id"),
            "attestation_chain.active_substrate_id",
        ) != source_substrate_id:
            raise ValueError(
                "attestation_chain.active_substrate_id must match standby_probe.active_substrate_id"
            )
        if self._normalize_non_empty_string(
            attestation_chain.get("standby_substrate_id"),
            "attestation_chain.standby_substrate_id",
        ) != standby_substrate_id:
            raise ValueError(
                "attestation_chain.standby_substrate_id must match standby_probe.standby_substrate_id"
            )
        if not self._normalize_bool(
            attestation_chain.get("handoff_ready"),
            "attestation_chain.handoff_ready",
        ):
            raise ValueError("attestation_chain.handoff_ready must be true")
        if not self._normalize_bool(
            attestation_chain.get("cross_host_verified"),
            "attestation_chain.cross_host_verified",
        ):
            raise ValueError("attestation_chain.cross_host_verified must be true")
        if self._normalize_non_empty_string(
            attestation_chain.get("chain_status"),
            "attestation_chain.chain_status",
        ) != "handoff-ready":
            raise ValueError("attestation_chain.chain_status must be handoff-ready")
        source_host_ref = self._normalize_non_empty_string(
            attestation_chain.get("source_host_ref"),
            "attestation_chain.source_host_ref",
        )
        source_host_attestation_ref = self._normalize_non_empty_string(
            attestation_chain.get("source_host_attestation_ref"),
            "attestation_chain.source_host_attestation_ref",
        )
        destination_host_ref = self._normalize_non_empty_string(
            attestation_chain.get("expected_destination_host_ref"),
            "attestation_chain.expected_destination_host_ref",
        )
        destination_host_attestation_ref = self._normalize_non_empty_string(
            attestation_chain.get("standby_host_attestation_ref"),
            "attestation_chain.standby_host_attestation_ref",
        )
        substrate_cluster_ref = self._normalize_non_empty_string(
            attestation_chain.get("substrate_cluster_ref"),
            "attestation_chain.substrate_cluster_ref",
        )
        cross_host_binding_profile = self._normalize_non_empty_string(
            attestation_chain.get("cross_host_binding_profile"),
            "attestation_chain.cross_host_binding_profile",
        )
        distinct_host_count = self._normalize_non_negative_int(
            attestation_chain.get("distinct_host_count"),
            "attestation_chain.distinct_host_count",
        )
        if distinct_host_count < 2:
            raise ValueError("attestation_chain.distinct_host_count must be >= 2")
        host_binding_digest = self._normalize_non_empty_string(
            attestation_chain.get("host_binding_digest"),
            "attestation_chain.host_binding_digest",
        )
        source_attestation_id = self._normalize_non_empty_string(
            attestation_chain.get("source_attestation_id"),
            "attestation_chain.source_attestation_id",
        )

        shadow_allocation = dual_allocation_window.get("shadow_allocation")
        if not isinstance(shadow_allocation, Mapping):
            raise ValueError("dual_allocation_window.shadow_allocation must be a mapping")
        if self._normalize_non_empty_string(
            dual_allocation_window.get("method"),
            "dual_allocation_window.method",
        ) != "B":
            raise ValueError("dual_allocation_window.method must be B")
        if self._normalize_non_empty_string(
            dual_allocation_window.get("window_status"),
            "dual_allocation_window.window_status",
        ) != "shadow-active":
            raise ValueError("dual_allocation_window.window_status must be shadow-active")
        if not self._normalize_bool(
            dual_allocation_window.get("handoff_ready"),
            "dual_allocation_window.handoff_ready",
        ):
            raise ValueError("dual_allocation_window.handoff_ready must be true")
        if not self._normalize_bool(
            dual_allocation_window.get("cross_host_verified"),
            "dual_allocation_window.cross_host_verified",
        ):
            raise ValueError("dual_allocation_window.cross_host_verified must be true")
        dual_allocation_window_id = self._normalize_non_empty_string(
            dual_allocation_window.get("window_id"),
            "dual_allocation_window.window_id",
        )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("source_substrate_id"),
            "dual_allocation_window.source_substrate_id",
        ) != source_substrate_id:
            raise ValueError(
                "dual_allocation_window.source_substrate_id must match standby_probe.active_substrate_id"
            )
        if self._normalize_non_empty_string(
            shadow_allocation.get("substrate"),
            "dual_allocation_window.shadow_allocation.substrate",
        ) != standby_substrate_id:
            raise ValueError(
                "dual_allocation_window.shadow_allocation.substrate must match standby_probe.standby_substrate_id"
            )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("source_host_ref"),
            "dual_allocation_window.source_host_ref",
        ) != source_host_ref:
            raise ValueError(
                "dual_allocation_window.source_host_ref must match attestation_chain.source_host_ref"
            )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("shadow_host_ref"),
            "dual_allocation_window.shadow_host_ref",
        ) != destination_host_ref:
            raise ValueError(
                "dual_allocation_window.shadow_host_ref must match attestation_chain.expected_destination_host_ref"
            )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("substrate_cluster_ref"),
            "dual_allocation_window.substrate_cluster_ref",
        ) != substrate_cluster_ref:
            raise ValueError(
                "dual_allocation_window.substrate_cluster_ref must match attestation_chain.substrate_cluster_ref"
            )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("cross_host_binding_profile"),
            "dual_allocation_window.cross_host_binding_profile",
        ) != cross_host_binding_profile:
            raise ValueError(
                "dual_allocation_window.cross_host_binding_profile must match attestation_chain.cross_host_binding_profile"
            )
        if self._normalize_non_negative_int(
            dual_allocation_window.get("distinct_host_count"),
            "dual_allocation_window.distinct_host_count",
        ) != distinct_host_count:
            raise ValueError(
                "dual_allocation_window.distinct_host_count must match attestation_chain.distinct_host_count"
            )
        if self._normalize_non_empty_string(
            dual_allocation_window.get("host_binding_digest"),
            "dual_allocation_window.host_binding_digest",
        ) != host_binding_digest:
            raise ValueError(
                "dual_allocation_window.host_binding_digest must match attestation_chain.host_binding_digest"
            )
        allocation_pair_digest = self._normalize_non_empty_string(
            dual_allocation_window.get("allocation_pair_digest"),
            "dual_allocation_window.allocation_pair_digest",
        )
        source_jurisdiction = self._normalize_non_empty_string(
            dual_allocation_window.get("source_jurisdiction"),
            "dual_allocation_window.source_jurisdiction",
        )
        source_network_zone = self._normalize_non_empty_string(
            dual_allocation_window.get("source_network_zone"),
            "dual_allocation_window.source_network_zone",
        )
        destination_jurisdiction = self._normalize_non_empty_string(
            dual_allocation_window.get("shadow_jurisdiction"),
            "dual_allocation_window.shadow_jurisdiction",
        )
        destination_network_zone = self._normalize_non_empty_string(
            dual_allocation_window.get("shadow_network_zone"),
            "dual_allocation_window.shadow_network_zone",
        )

        if self._normalize_non_empty_string(
            attestation_stream.get("source_substrate_id"),
            "attestation_stream.source_substrate_id",
        ) != source_substrate_id:
            raise ValueError(
                "attestation_stream.source_substrate_id must match standby_probe.active_substrate_id"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("shadow_substrate_id"),
            "attestation_stream.shadow_substrate_id",
        ) != standby_substrate_id:
            raise ValueError(
                "attestation_stream.shadow_substrate_id must match standby_probe.standby_substrate_id"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("stream_status"),
            "attestation_stream.stream_status",
        ) != "sealed-handoff-ready":
            raise ValueError("attestation_stream.stream_status must be sealed-handoff-ready")
        if not self._normalize_bool(
            attestation_stream.get("handoff_ready"),
            "attestation_stream.handoff_ready",
        ):
            raise ValueError("attestation_stream.handoff_ready must be true")
        if not self._normalize_bool(
            attestation_stream.get("cross_host_verified"),
            "attestation_stream.cross_host_verified",
        ):
            raise ValueError("attestation_stream.cross_host_verified must be true")
        if self._normalize_non_empty_string(
            attestation_stream.get("expected_destination_substrate"),
            "attestation_stream.expected_destination_substrate",
        ) != standby_substrate_id:
            raise ValueError(
                "attestation_stream.expected_destination_substrate must match standby_probe.standby_substrate_id"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("expected_destination_host_ref"),
            "attestation_stream.expected_destination_host_ref",
        ) != destination_host_ref:
            raise ValueError(
                "attestation_stream.expected_destination_host_ref must match attestation_chain.expected_destination_host_ref"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("substrate_cluster_ref"),
            "attestation_stream.substrate_cluster_ref",
        ) != substrate_cluster_ref:
            raise ValueError(
                "attestation_stream.substrate_cluster_ref must match attestation_chain.substrate_cluster_ref"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("cross_host_binding_profile"),
            "attestation_stream.cross_host_binding_profile",
        ) != cross_host_binding_profile:
            raise ValueError(
                "attestation_stream.cross_host_binding_profile must match attestation_chain.cross_host_binding_profile"
            )
        if self._normalize_non_negative_int(
            attestation_stream.get("distinct_host_count"),
            "attestation_stream.distinct_host_count",
        ) != distinct_host_count:
            raise ValueError(
                "attestation_stream.distinct_host_count must match attestation_chain.distinct_host_count"
            )
        if self._normalize_non_empty_string(
            attestation_stream.get("host_binding_digest"),
            "attestation_stream.host_binding_digest",
        ) != host_binding_digest:
            raise ValueError(
                "attestation_stream.host_binding_digest must match attestation_chain.host_binding_digest"
            )
        attestation_stream_id = self._normalize_non_empty_string(
            attestation_stream.get("stream_id"),
            "attestation_stream.stream_id",
        )
        handoff_state_digest = self._normalize_non_empty_string(
            attestation_stream.get("expected_state_digest"),
            "attestation_stream.expected_state_digest",
        )

        return {
            "kind": "scheduler_method_b_handoff_receipt",
            "schema_version": SCHEDULER_SCHEMA_VERSION,
            "receipt_id": new_id("scheduler-method-b-handoff"),
            "handle_id": handle["handle_id"],
            "plan_ref": handle["plan_ref"],
            "identity_id": identity_id,
            "method": "B",
            "review_stage_id": SCHEDULER_METHOD_B_PREPARE_STAGE,
            "handoff_stage_id": SCHEDULER_METHOD_B_HANDOFF_STAGE,
            "retirement_stage_id": SCHEDULER_METHOD_B_RETIRE_STAGE,
            "policy_id": SCHEDULER_METHOD_B_HANDOFF_POLICY_ID,
            "status": "prepared",
            "source_substrate": source_substrate_id,
            "destination_substrate": standby_substrate_id,
            "source_host_ref": source_host_ref,
            "source_host_attestation_ref": source_host_attestation_ref,
            "source_jurisdiction": source_jurisdiction,
            "source_network_zone": source_network_zone,
            "destination_host_ref": destination_host_ref,
            "destination_host_attestation_ref": destination_host_attestation_ref,
            "destination_jurisdiction": destination_jurisdiction,
            "destination_network_zone": destination_network_zone,
            "substrate_cluster_ref": substrate_cluster_ref,
            "cross_host_binding_profile": cross_host_binding_profile,
            "distinct_host_count": distinct_host_count,
            "host_binding_digest": host_binding_digest,
            "broker_signal_id": signal_id,
            "broker_signal_severity": signal_severity,
            "recommended_action": recommended_action,
            "scheduler_signal": {
                "severity": scheduler_severity,
                "source_substrate": scheduler_source,
                "reason": scheduler_reason,
            },
            "standby_probe_id": self._normalize_non_empty_string(
                standby_probe.get("probe_id"),
                "standby_probe.probe_id",
            ),
            "source_attestation_id": source_attestation_id,
            "attestation_chain_id": attestation_chain_id,
            "dual_allocation_window_id": dual_allocation_window_id,
            "attestation_stream_id": attestation_stream_id,
            "allocation_pair_digest": allocation_pair_digest,
            "handoff_state_digest": handoff_state_digest,
            "prepared_at": utc_now_iso(),
            "confirmed_at": None,
            "migration_transfer_id": None,
            "migration_state_digest": None,
            "dual_allocation_close_id": None,
            "cleanup_release_status": None,
        }

    def _normalize_method_b_handoff_confirmation(
        self,
        *,
        receipt: Mapping[str, Any],
        migration: Mapping[str, Any],
        closed_dual_allocation_window: Mapping[str, Any],
    ) -> tuple[Dict[str, str], Dict[str, str]]:
        if not isinstance(migration, Mapping):
            raise ValueError("migration must be a mapping")
        if not isinstance(closed_dual_allocation_window, Mapping):
            raise ValueError("closed_dual_allocation_window must be a mapping")
        if self._normalize_non_empty_string(
            migration.get("source_substrate"),
            "migration.source_substrate",
        ) != receipt["source_substrate"]:
            raise ValueError("migration.source_substrate must match the prepared broker receipt")
        if self._normalize_non_empty_string(
            migration.get("destination_substrate"),
            "migration.destination_substrate",
        ) != receipt["destination_substrate"]:
            raise ValueError(
                "migration.destination_substrate must match the prepared broker receipt"
            )
        if self._normalize_non_empty_string(
            migration.get("source_host_ref"),
            "migration.source_host_ref",
        ) != receipt["source_host_ref"]:
            raise ValueError("migration.source_host_ref must match the prepared broker receipt")
        if self._normalize_non_empty_string(
            migration.get("destination_host_ref"),
            "migration.destination_host_ref",
        ) != receipt["destination_host_ref"]:
            raise ValueError(
                "migration.destination_host_ref must match the prepared broker receipt"
            )
        if self._normalize_non_empty_string(
            migration.get("substrate_cluster_ref"),
            "migration.substrate_cluster_ref",
        ) != receipt["substrate_cluster_ref"]:
            raise ValueError(
                "migration.substrate_cluster_ref must match the prepared broker receipt"
            )
        if self._normalize_non_empty_string(
            migration.get("cross_host_binding_profile"),
            "migration.cross_host_binding_profile",
        ) != receipt["cross_host_binding_profile"]:
            raise ValueError(
                "migration.cross_host_binding_profile must match the prepared broker receipt"
            )
        if self._normalize_non_empty_string(
            migration.get("host_binding_digest"),
            "migration.host_binding_digest",
        ) != receipt["host_binding_digest"]:
            raise ValueError(
                "migration.host_binding_digest must match the prepared broker receipt"
            )
        if not self._normalize_bool(
            migration.get("cross_host_verified"),
            "migration.cross_host_verified",
        ):
            raise ValueError("migration.cross_host_verified must be true")
        if self._normalize_non_empty_string(
            migration.get("continuity_mode"),
            "migration.continuity_mode",
        ) != "hot-handoff":
            raise ValueError("migration.continuity_mode must be hot-handoff")
        migration_transfer_id = self._normalize_non_empty_string(
            migration.get("transfer_id"),
            "migration.transfer_id",
        )
        migration_state_digest = self._normalize_non_empty_string(
            migration.get("state_digest"),
            "migration.state_digest",
        )
        if migration_state_digest != receipt["handoff_state_digest"]:
            raise ValueError(
                "migration.state_digest must match the prepared broker handoff_state_digest"
            )

        closed_window_id = self._normalize_non_empty_string(
            closed_dual_allocation_window.get("window_id"),
            "closed_dual_allocation_window.window_id",
        )
        if closed_window_id != receipt["dual_allocation_window_id"]:
            raise ValueError(
                "closed_dual_allocation_window.window_id must match the prepared broker receipt"
            )
        if self._normalize_non_empty_string(
            closed_dual_allocation_window.get("window_status"),
            "closed_dual_allocation_window.window_status",
        ) != "closed":
            raise ValueError("closed_dual_allocation_window.window_status must be closed")
        if self._normalize_non_empty_string(
            closed_dual_allocation_window.get("host_binding_digest"),
            "closed_dual_allocation_window.host_binding_digest",
        ) != receipt["host_binding_digest"]:
            raise ValueError(
                "closed_dual_allocation_window.host_binding_digest must match the prepared broker receipt"
            )
        shadow_release = closed_dual_allocation_window.get("shadow_release")
        if not isinstance(shadow_release, Mapping):
            raise ValueError("closed_dual_allocation_window.shadow_release must be a mapping")
        release_status = self._normalize_non_empty_string(
            shadow_release.get("status"),
            "closed_dual_allocation_window.shadow_release.status",
        )
        if release_status != "released":
            raise ValueError(
                "closed_dual_allocation_window.shadow_release.status must be released"
            )
        return (
            {
                "transfer_id": migration_transfer_id,
                "transferred_at": self._normalize_non_empty_string(
                    migration.get("transferred_at"),
                    "migration.transferred_at",
                ),
                "state_digest": migration_state_digest,
            },
            {
                "window_id": closed_window_id,
                "release_status": release_status,
            },
        )

    def _normalize_verifier_rotation_state(self, value: Any) -> str:
        state = self._normalize_non_empty_string(value, "verifier_roster.rotation_state")
        if state not in SCHEDULER_VERIFIER_ROTATION_STATES:
            raise ValueError(
                "verifier_roster.rotation_state must be one of "
                f"{sorted(SCHEDULER_VERIFIER_ROTATION_STATES)}"
            )
        return state

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
