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
    "cancel",
    "fail",
}
SCHEDULER_SIGNAL_SEVERITIES = {"watch", "degraded", "critical"}
SCHEDULER_WITNESS_QUORUM = 2
GOVERNANCE_ARTIFACT_PREFIXES = {
    "self_consent_ref": "consent://",
    "ethics_attestation_ref": "ethics://",
    "council_attestation_ref": "council://",
    "legal_attestation_ref": "legal://",
    "artifact_bundle_ref": "artifact://",
}
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

    def _normalize_artifact_ref(self, value: Any, field_name: str, prefix: str) -> str:
        normalized = self._normalize_non_empty_string(value, field_name)
        if not normalized.startswith(prefix):
            raise ValueError(f"{field_name} must start with {prefix}")
        return normalized

    def _governance_artifact_digest(self, governance_artifacts: Mapping[str, Any]) -> str:
        return sha256_text(canonical_json(dict(governance_artifacts)))

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
