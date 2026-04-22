"""External World Agents reference model."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..kernel.ethics import ActionRequest, EthicsEnforcer

EWA_SCHEMA_VERSION = "1.0"
EWA_ALLOWED_REVERSIBILITY = {
    "read-only",
    "reversible",
    "partial-reversible",
    "irreversible",
}
EWA_AUDIT_REVERSIBILITY = EWA_ALLOWED_REVERSIBILITY | {"not-applicable"}
EWA_ALLOWED_HANDLE_STATUS = {"acquired", "released"}
EWA_AUTHORIZATION_POLICY_ID = "guardian-jurisdiction-bound-external-actuation-v1"
EWA_AUTHORIZATION_DELIVERY_SCOPE = "physical-device-actuation"
EWA_EMERGENCY_STOP_POLICY_ID = "guardian-latched-emergency-stop-v1"
EWA_ALLOWED_EMERGENCY_STOP_SOURCES = {
    "guardian-manual-stop",
    "watchdog-timeout",
    "sensor-drift",
    "emergency-disconnect",
}
EWA_EMERGENCY_STOP_RELEASE_WINDOW_SECONDS = 30
EWA_ALLOWED_AUTHORIZATION_STATUSES = {"authorized", "expired", "revoked"}
EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES = {"ready", "stale", "revoked"}
EWA_AUTHORIZATION_MIN_WINDOW_SECONDS = 60
EWA_AUTHORIZATION_MAX_WINDOW_SECONDS = 900
EWA_MOTOR_PLAN_PROFILE_ID = "device-specific-motor-semantics-v1"
EWA_LEGAL_EXECUTION_PROFILE_ID = "ewa-jurisdiction-legal-execution-v1"
EWA_LEGAL_EXECUTION_SCOPE = "physical-actuation-preflight"
EWA_ALLOWED_LIABILITY_MODES = {"individual", "institutional", "joint"}
EWA_LEGAL_EXECUTION_CONTROL_TYPES = (
    "bundle-ready-check",
    "legal-basis-bind",
    "guardian-review-bind",
    "notice-authority-bind",
    "escalation-contact-bind",
)
EWA_BLOCKED_TOKEN_PATTERNS = {
    "harm.human": (
        r"\b(kill|attack|stab|shoot|poison|injure|harm)\b",
        r"\b(drop|drops|dropping|crush|strike)\b.*\b(human|person|people|pedestrian|pedestrians)\b",
    ),
    "harm.ecology": (
        r"\b(pollute|spill|dump|ignite|burn)\b.*\b(forest|river|habitat|reef)\b",
        r"\b(ecocide|toxic release|wildfire)\b",
    ),
    "harm.privacy": (
        r"\b(spy|surveil|wiretap|eavesdrop|stalk)\b",
        r"\b(hidden camera|secret recording)\b",
    ),
    "harm.illegal": (
        r"\b(steal|smuggle|arson|trespass|contraband)\b",
        r"\billegal\b",
    ),
    "harm.deception": (
        r"\b(impersonate|counterfeit|forge|plant evidence|deceive)\b",
        r"\bfalse flag\b",
    ),
}
EWA_INTENT_CONFIDENCE_THRESHOLD = 0.8


def _authorization_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "authorization_digest"}


def _emergency_stop_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "stop_digest"}


def _motor_plan_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "plan_digest"}


def _legal_execution_digest_payload(record: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in record.items() if key != "digest"}


class ExternalWorldAgentController:
    """Deterministic L6 physical-actuation boundary with ethics-first gating."""

    def __init__(self, ethics: Optional[EthicsEnforcer] = None) -> None:
        self.ethics = ethics or EthicsEnforcer()
        self.handles: Dict[str, Dict[str, Any]] = {}
        self.authorizations: Dict[str, Dict[str, Any]] = {}
        self.motor_plans: Dict[str, Dict[str, Any]] = {}
        self.legal_executions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": EWA_SCHEMA_VERSION,
            "blocked_tokens": sorted(EWA_BLOCKED_TOKEN_PATTERNS),
            "intent_confidence_threshold": EWA_INTENT_CONFIDENCE_THRESHOLD,
            "reversibility_requirements": {
                "read-only": {
                    "ethics_attestation": True,
                    "guardian_observed": False,
                    "council_mode": "none",
                    "self_consent": False,
                },
                "reversible": {
                    "ethics_attestation": True,
                    "guardian_observed": True,
                    "council_mode": "none",
                    "self_consent": False,
                },
                "partial-reversible": {
                    "ethics_attestation": True,
                    "guardian_observed": False,
                    "council_mode": "majority",
                    "self_consent": False,
                },
                "irreversible": {
                    "ethics_attestation": True,
                    "guardian_observed": True,
                    "council_mode": "unanimous",
                    "self_consent": True,
                },
            },
            "audit_policy": {
                "append_only": True,
                "instruction_storage": "digest-only",
                "sensor_storage": "summary-ref-only",
            },
            "authorization_policy": {
                "policy_id": EWA_AUTHORIZATION_POLICY_ID,
                "delivery_scope": EWA_AUTHORIZATION_DELIVERY_SCOPE,
                "non_read_only_requires_authorization": True,
                "guardian_verification_transport": "reviewer-live-proof-bridge-v1",
                "required_jurisdiction_bundle_status": "ready",
                "authorization_window_seconds": {
                    "min": EWA_AUTHORIZATION_MIN_WINDOW_SECONDS,
                    "max": EWA_AUTHORIZATION_MAX_WINDOW_SECONDS,
                },
            },
            "motor_semantics_policy": {
                "profile_id": EWA_MOTOR_PLAN_PROFILE_ID,
                "safe_stop_policy_id": EWA_EMERGENCY_STOP_POLICY_ID,
                "requires_instruction_digest_binding": True,
                "requires_device_profile": True,
                "requires_motion_envelope": True,
            },
            "jurisdiction_legal_execution_policy": {
                "execution_profile_id": EWA_LEGAL_EXECUTION_PROFILE_ID,
                "execution_scope": EWA_LEGAL_EXECUTION_SCOPE,
                "delivery_scope": EWA_AUTHORIZATION_DELIVERY_SCOPE,
                "required_bundle_status": "ready",
                "allowed_liability_modes": sorted(EWA_ALLOWED_LIABILITY_MODES),
                "required_controls": list(EWA_LEGAL_EXECUTION_CONTROL_TYPES),
            },
            "emergency_stop_policy": {
                "policy_id": EWA_EMERGENCY_STOP_POLICY_ID,
                "trigger_sources": sorted(EWA_ALLOWED_EMERGENCY_STOP_SOURCES),
                "safe_state_status": "latched-safe",
                "hardware_interlock_state": "engaged",
                "require_release_after_stop": True,
                "release_window_seconds": EWA_EMERGENCY_STOP_RELEASE_WINDOW_SECONDS,
            },
        }

    def acquire(self, device_id: str, intent_summary: str) -> Dict[str, Any]:
        normalized_device_id = self._normalize_non_empty_string(device_id, "device_id")
        normalized_intent = self._normalize_non_empty_string(intent_summary, "intent_summary")
        handle_id = new_id("ewa")
        recorded_at = utc_now_iso()
        handle = {
            "schema_version": EWA_SCHEMA_VERSION,
            "handle_id": handle_id,
            "device_id": normalized_device_id,
            "intent_summary": normalized_intent,
            "acquired_at": recorded_at,
            "released_at": None,
            "status": "acquired",
            "actuator_state": "idle",
            "last_command_id": "",
            "last_command_status": "none",
            "last_command_digest": "",
            "last_authorization_id": "",
            "last_authorization_digest": "",
            "last_motor_plan_id": "",
            "last_motor_plan_digest": "",
            "last_legal_execution_id": "",
            "last_legal_execution_digest": "",
            "last_emergency_stop_id": "",
            "emergency_stop_active": False,
            "audit_log": [],
            "audit_sequence": 0,
        }
        audit = self._append_audit(
            handle,
            operation="acquire",
            status="acquired",
            reversibility="not-applicable",
            command_id="",
            instruction="",
            intent_summary=normalized_intent,
            matched_tokens=[],
            reason="device handle acquired after ethics-first intent registration",
            alternative_suggestion=None,
            approval_path=self._approval_path(
                ethics_attestation_id="",
                council_attestation_id="",
                council_attestation_mode="none",
                guardian_observed=False,
                required_self_consent=False,
                self_consent_granted=False,
                authorization_id="",
            ),
        )
        self.handles[handle_id] = handle
        return {
            "schema_version": EWA_SCHEMA_VERSION,
            "handle_id": handle_id,
            "device_id": normalized_device_id,
            "intent_summary": normalized_intent,
            "acquired_at": recorded_at,
            "status": "acquired",
            "audit_event_ref": audit["audit_event_ref"],
        }

    def prepare_motor_plan(
        self,
        handle_id: str,
        *,
        command_id: str,
        instruction: str,
        reversibility: str,
        guardian_observed: bool,
        actuator_profile_id: str,
        actuator_group: str,
        motion_profile: str,
        target_pose_ref: str,
        safety_zone_ref: str,
        rollback_vector_ref: str,
        max_linear_speed_mps: float,
        max_force_newton: float,
        hold_timeout_ms: int,
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        normalized_command_id = self._normalize_non_empty_string(command_id, "command_id")
        normalized_instruction = self._normalize_non_empty_string(instruction, "instruction")
        normalized_reversibility = self._normalize_reversibility(reversibility)
        if normalized_reversibility == "read-only":
            raise ValueError("read-only commands must not prepare a motor plan")
        if not isinstance(guardian_observed, bool):
            raise ValueError("guardian_observed must be a boolean")

        plan = {
            "kind": "ewa_motor_plan",
            "schema_version": EWA_SCHEMA_VERSION,
            "plan_id": new_id("ewa-plan"),
            "profile_id": EWA_MOTOR_PLAN_PROFILE_ID,
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "command_id": normalized_command_id,
            "instruction_digest": sha256_text(normalized_instruction),
            "reversibility": normalized_reversibility,
            "guardian_observed": guardian_observed,
            "actuator_profile_id": self._normalize_non_empty_string(
                actuator_profile_id,
                "actuator_profile_id",
            ),
            "actuator_group": self._normalize_non_empty_string(
                actuator_group,
                "actuator_group",
            ),
            "motion_profile": self._normalize_non_empty_string(
                motion_profile,
                "motion_profile",
            ),
            "target_pose_ref": self._normalize_non_empty_string(
                target_pose_ref,
                "target_pose_ref",
            ),
            "safety_zone_ref": self._normalize_non_empty_string(
                safety_zone_ref,
                "safety_zone_ref",
            ),
            "rollback_vector_ref": self._normalize_non_empty_string(
                rollback_vector_ref,
                "rollback_vector_ref",
            ),
            "safe_stop_policy_id": EWA_EMERGENCY_STOP_POLICY_ID,
            "max_linear_speed_mps": self._normalize_positive_number(
                max_linear_speed_mps,
                "max_linear_speed_mps",
            ),
            "max_force_newton": self._normalize_positive_number(
                max_force_newton,
                "max_force_newton",
            ),
            "hold_timeout_ms": self._normalize_positive_int(
                hold_timeout_ms,
                "hold_timeout_ms",
            ),
            "prepared_at": utc_now_iso(),
        }
        plan["plan_digest"] = sha256_text(canonical_json(_motor_plan_digest_payload(plan)))
        self.motor_plans[plan["plan_id"]] = plan
        return deepcopy(plan)

    def validate_motor_plan(
        self,
        plan: Mapping[str, Any],
        *,
        handle_id: str | None = None,
        device_id: str | None = None,
        command_id: str | None = None,
        instruction: str | None = None,
        reversibility: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(plan, Mapping):
            raise ValueError("plan must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(plan.get("plan_id"), "plan_id", errors)
        self._check_non_empty_string(plan.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(plan.get("device_id"), "device_id", errors)
        self._check_non_empty_string(plan.get("command_id"), "command_id", errors)
        self._check_non_empty_string(plan.get("instruction_digest"), "instruction_digest", errors)
        self._check_non_empty_string(
            plan.get("actuator_profile_id"),
            "actuator_profile_id",
            errors,
        )
        self._check_non_empty_string(plan.get("actuator_group"), "actuator_group", errors)
        self._check_non_empty_string(plan.get("motion_profile"), "motion_profile", errors)
        self._check_non_empty_string(plan.get("target_pose_ref"), "target_pose_ref", errors)
        self._check_non_empty_string(plan.get("safety_zone_ref"), "safety_zone_ref", errors)
        self._check_non_empty_string(
            plan.get("rollback_vector_ref"),
            "rollback_vector_ref",
            errors,
        )
        self._check_non_empty_string(plan.get("plan_digest"), "plan_digest", errors)

        profile_valid = plan.get("profile_id") == EWA_MOTOR_PLAN_PROFILE_ID
        if not profile_valid:
            errors.append(f"profile_id must be {EWA_MOTOR_PLAN_PROFILE_ID}")
        if plan.get("kind") != "ewa_motor_plan":
            errors.append("kind must be ewa_motor_plan")
        if plan.get("schema_version") != EWA_SCHEMA_VERSION:
            errors.append(f"schema_version must be {EWA_SCHEMA_VERSION}")
        safe_stop_policy_bound = plan.get("safe_stop_policy_id") == EWA_EMERGENCY_STOP_POLICY_ID
        if not safe_stop_policy_bound:
            errors.append(f"safe_stop_policy_id must be {EWA_EMERGENCY_STOP_POLICY_ID}")
        if plan.get("reversibility") not in EWA_ALLOWED_REVERSIBILITY - {"read-only"}:
            errors.append("motor plan reversibility must be a non-read-only EWA mode")
        if not isinstance(plan.get("guardian_observed"), bool):
            errors.append("guardian_observed must be a boolean")

        motion_limits_valid = True
        for field_name in ("max_linear_speed_mps", "max_force_newton"):
            value = plan.get(field_name)
            if not isinstance(value, (int, float)) or float(value) <= 0:
                motion_limits_valid = False
                errors.append(f"{field_name} must be a positive number")
        timeout = plan.get("hold_timeout_ms")
        if not isinstance(timeout, int) or timeout <= 0:
            motion_limits_valid = False
            errors.append("hold_timeout_ms must be a positive integer")

        if handle_id is not None and plan.get("handle_id") != handle_id:
            errors.append("motor plan handle_id does not match command handle_id")
        if device_id is not None and plan.get("device_id") != device_id:
            errors.append("motor plan device_id does not match command device_id")
        if command_id is not None and plan.get("command_id") != command_id:
            errors.append("motor plan command_id does not match command command_id")
        instruction_digest_matches = True
        if instruction is not None:
            instruction_digest_matches = plan.get("instruction_digest") == sha256_text(instruction)
            if not instruction_digest_matches:
                errors.append("motor plan instruction_digest does not match command instruction")
        if reversibility is not None and plan.get("reversibility") != reversibility:
            errors.append("motor plan reversibility does not match command reversibility")

        self._parse_datetime(plan.get("prepared_at"), "prepared_at", errors)
        digest_matches = plan.get("plan_digest") == sha256_text(
            canonical_json(_motor_plan_digest_payload(dict(plan)))
        )
        if not digest_matches:
            errors.append("plan_digest must match the canonical motor plan payload")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_valid": profile_valid,
            "instruction_digest_matches": instruction_digest_matches,
            "safe_stop_policy_bound": safe_stop_policy_bound,
            "motion_limits_valid": motion_limits_valid,
            "plan_ready": (
                profile_valid
                and instruction_digest_matches
                and safe_stop_policy_bound
                and motion_limits_valid
                and digest_matches
            ),
        }

    def execute_legal_preflight(
        self,
        handle_id: str,
        *,
        command_id: str,
        reversibility: str,
        jurisdiction: str,
        legal_basis_ref: str,
        guardian_verification_ref: str,
        jurisdiction_bundle_ref: str,
        jurisdiction_bundle_digest: str,
        jurisdiction_bundle_status: str = "ready",
        notice_authority_ref: str,
        liability_mode: str,
        escalation_contact: str,
        valid_for_seconds: int = 360,
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        normalized_reversibility = self._normalize_reversibility(reversibility)
        if normalized_reversibility == "read-only":
            raise ValueError("read-only commands must not execute a legal preflight")
        normalized_bundle_status = self._normalize_jurisdiction_bundle_status(
            jurisdiction_bundle_status,
        )
        if normalized_bundle_status != "ready":
            raise ValueError("jurisdiction bundle must be ready before legal preflight")

        execution_id = new_id("ewa-legal")
        executed_at_dt = datetime.now(timezone.utc).replace(microsecond=0)
        valid_until_dt = executed_at_dt + timedelta(
            seconds=self._normalize_valid_for_seconds(valid_for_seconds)
        )
        normalized_jurisdiction = self._normalize_non_empty_string(jurisdiction, "jurisdiction")
        policy_ref = f"policy://ewa/{normalized_jurisdiction.lower()}/physical-actuation-preflight/v1"
        policy_digest = sha256_text(policy_ref)
        controls: List[Dict[str, Any]] = []
        control_payloads = {
            "bundle-ready-check": {
                "jurisdiction_bundle_ref": jurisdiction_bundle_ref,
                "jurisdiction_bundle_status": normalized_bundle_status,
            },
            "legal-basis-bind": {
                "legal_basis_ref": legal_basis_ref,
                "policy_ref": policy_ref,
            },
            "guardian-review-bind": {
                "guardian_verification_ref": guardian_verification_ref,
                "command_id": command_id,
            },
            "notice-authority-bind": {
                "notice_authority_ref": notice_authority_ref,
                "jurisdiction": normalized_jurisdiction,
            },
            "escalation-contact-bind": {
                "escalation_contact": escalation_contact,
                "liability_mode": liability_mode,
            },
        }
        for index, control_type in enumerate(EWA_LEGAL_EXECUTION_CONTROL_TYPES, start=1):
            evidence_ref = f"ewa-legal://{execution_id}/{control_type}"
            evidence_digest = sha256_text(canonical_json(control_payloads[control_type]))
            controls.append(
                {
                    "control_id": f"{execution_id}-control-{index}",
                    "control_type": control_type,
                    "status": "executed",
                    "evidence_ref": evidence_ref,
                    "evidence_digest": evidence_digest,
                }
            )

        execution = {
            "kind": "ewa_legal_execution",
            "schema_version": EWA_SCHEMA_VERSION,
            "execution_id": execution_id,
            "execution_profile_id": EWA_LEGAL_EXECUTION_PROFILE_ID,
            "execution_scope": EWA_LEGAL_EXECUTION_SCOPE,
            "delivery_scope": EWA_AUTHORIZATION_DELIVERY_SCOPE,
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "command_id": self._normalize_non_empty_string(command_id, "command_id"),
            "reversibility": normalized_reversibility,
            "jurisdiction": normalized_jurisdiction,
            "policy_ref": policy_ref,
            "policy_digest": policy_digest,
            "legal_basis_ref": self._normalize_non_empty_string(
                legal_basis_ref,
                "legal_basis_ref",
            ),
            "guardian_verification_ref": self._normalize_non_empty_string(
                guardian_verification_ref,
                "guardian_verification_ref",
            ),
            "jurisdiction_bundle_ref": self._normalize_non_empty_string(
                jurisdiction_bundle_ref,
                "jurisdiction_bundle_ref",
            ),
            "jurisdiction_bundle_digest": self._normalize_non_empty_string(
                jurisdiction_bundle_digest,
                "jurisdiction_bundle_digest",
            ),
            "jurisdiction_bundle_status": normalized_bundle_status,
            "notice_authority_ref": self._normalize_non_empty_string(
                notice_authority_ref,
                "notice_authority_ref",
            ),
            "liability_mode": self._normalize_liability_mode(liability_mode),
            "escalation_contact": self._normalize_non_empty_string(
                escalation_contact,
                "escalation_contact",
            ),
            "required_control_count": len(EWA_LEGAL_EXECUTION_CONTROL_TYPES),
            "executed_control_count": len(controls),
            "executed_controls": controls,
            "execution_status": "executed",
            "executed_at": executed_at_dt.isoformat(),
            "valid_until": valid_until_dt.isoformat(),
        }
        execution["digest"] = sha256_text(
            canonical_json(_legal_execution_digest_payload(execution))
        )
        self.legal_executions[execution_id] = execution
        return deepcopy(execution)

    def validate_legal_execution(
        self,
        execution: Mapping[str, Any],
        *,
        handle_id: str | None = None,
        device_id: str | None = None,
        command_id: str | None = None,
        reversibility: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(execution, Mapping):
            raise ValueError("execution must be a mapping")

        errors: List[str] = []
        for field_name in (
            "execution_id",
            "handle_id",
            "device_id",
            "command_id",
            "jurisdiction",
            "policy_ref",
            "policy_digest",
            "legal_basis_ref",
            "guardian_verification_ref",
            "jurisdiction_bundle_ref",
            "jurisdiction_bundle_digest",
            "notice_authority_ref",
            "escalation_contact",
            "digest",
        ):
            self._check_non_empty_string(execution.get(field_name), field_name, errors)

        profile_valid = execution.get("execution_profile_id") == EWA_LEGAL_EXECUTION_PROFILE_ID
        if not profile_valid:
            errors.append(
                f"execution_profile_id must be {EWA_LEGAL_EXECUTION_PROFILE_ID}"
            )
        if execution.get("kind") != "ewa_legal_execution":
            errors.append("kind must be ewa_legal_execution")
        if execution.get("schema_version") != EWA_SCHEMA_VERSION:
            errors.append(f"schema_version must be {EWA_SCHEMA_VERSION}")
        if execution.get("execution_scope") != EWA_LEGAL_EXECUTION_SCOPE:
            errors.append(f"execution_scope must be {EWA_LEGAL_EXECUTION_SCOPE}")
        if execution.get("delivery_scope") != EWA_AUTHORIZATION_DELIVERY_SCOPE:
            errors.append(f"delivery_scope must be {EWA_AUTHORIZATION_DELIVERY_SCOPE}")
        if execution.get("reversibility") not in EWA_ALLOWED_REVERSIBILITY - {"read-only"}:
            errors.append("legal execution reversibility must be a non-read-only EWA mode")
        if execution.get("jurisdiction_bundle_status") not in EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES:
            errors.append(
                "jurisdiction_bundle_status must be one of "
                f"{sorted(EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES)}"
            )
        if execution.get("liability_mode") not in EWA_ALLOWED_LIABILITY_MODES:
            errors.append(
                f"liability_mode must be one of {sorted(EWA_ALLOWED_LIABILITY_MODES)}"
            )
        if execution.get("execution_status") != "executed":
            errors.append("execution_status must be executed")
        if execution.get("policy_digest") != sha256_text(str(execution.get("policy_ref", ""))):
            errors.append("policy_digest must match the canonical policy_ref digest")

        if handle_id is not None and execution.get("handle_id") != handle_id:
            errors.append("legal execution handle_id does not match command handle_id")
        if device_id is not None and execution.get("device_id") != device_id:
            errors.append("legal execution device_id does not match command device_id")
        if command_id is not None and execution.get("command_id") != command_id:
            errors.append("legal execution command_id does not match command command_id")
        if reversibility is not None and execution.get("reversibility") != reversibility:
            errors.append("legal execution reversibility does not match command reversibility")

        controls_complete = True
        required_control_count = execution.get("required_control_count")
        executed_control_count = execution.get("executed_control_count")
        executed_controls = execution.get("executed_controls")
        if not isinstance(required_control_count, int) or required_control_count != len(
            EWA_LEGAL_EXECUTION_CONTROL_TYPES
        ):
            controls_complete = False
            errors.append(
                "required_control_count must equal the fixed EWA legal execution control count"
            )
        if not isinstance(executed_control_count, int) or executed_control_count != len(
            EWA_LEGAL_EXECUTION_CONTROL_TYPES
        ):
            controls_complete = False
            errors.append(
                "executed_control_count must equal the fixed EWA legal execution control count"
            )
        if not isinstance(executed_controls, list) or len(executed_controls) != len(
            EWA_LEGAL_EXECUTION_CONTROL_TYPES
        ):
            controls_complete = False
            errors.append("executed_controls must contain the fixed EWA legal execution controls")
            executed_controls = []

        seen_control_types = set()
        for control in executed_controls:
            if not isinstance(control, Mapping):
                controls_complete = False
                errors.append("executed_controls entries must be mappings")
                continue
            control_type = control.get("control_type")
            if control_type not in EWA_LEGAL_EXECUTION_CONTROL_TYPES:
                controls_complete = False
                errors.append("executed_controls contain an unsupported control_type")
            else:
                seen_control_types.add(control_type)
            if control.get("status") != "executed":
                controls_complete = False
                errors.append("executed_controls status must be executed")
            self._check_non_empty_string(control.get("control_id"), "control_id", errors)
            self._check_non_empty_string(control.get("evidence_ref"), "evidence_ref", errors)
            evidence_digest = control.get("evidence_digest", "")
            if not isinstance(evidence_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", evidence_digest):
                controls_complete = False
                errors.append("executed_controls evidence_digest must be sha256")
        if seen_control_types != set(EWA_LEGAL_EXECUTION_CONTROL_TYPES):
            controls_complete = False
            errors.append("executed_controls must cover the fixed EWA legal execution control set")

        executed_at = self._parse_datetime(execution.get("executed_at"), "executed_at", errors)
        valid_until = self._parse_datetime(execution.get("valid_until"), "valid_until", errors)
        window_open = (
            executed_at is not None
            and valid_until is not None
            and valid_until > datetime.now(timezone.utc)
            and valid_until > executed_at
        )
        if not window_open:
            errors.append("legal execution window expired")

        jurisdiction_bundle_ready = execution.get("jurisdiction_bundle_status") == "ready"
        if not jurisdiction_bundle_ready:
            errors.append("jurisdiction bundle must be ready")

        digest_matches = execution.get("digest") == sha256_text(
            canonical_json(_legal_execution_digest_payload(dict(execution)))
        )
        if not digest_matches:
            errors.append("digest must match the canonical legal execution payload")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_valid": profile_valid,
            "jurisdiction_bundle_ready": jurisdiction_bundle_ready,
            "controls_complete": controls_complete,
            "window_open": window_open,
            "execution_ready": (
                profile_valid
                and jurisdiction_bundle_ready
                and controls_complete
                and window_open
                and digest_matches
            ),
        }

    def authorize(
        self,
        handle_id: str,
        *,
        command_id: str,
        instruction: str,
        reversibility: str,
        intent_summary: str,
        ethics_attestation_id: str,
        motor_plan_id: str,
        legal_execution_id: str,
        council_attestation_id: str = "",
        council_attestation_mode: str = "none",
        guardian_observed: bool = False,
        required_self_consent: bool = False,
        self_consent_granted: bool = False,
        intent_confidence: float = 1.0,
        valid_for_seconds: int = 300,
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        if handle.get("emergency_stop_active"):
            raise ValueError("handle is latched in emergency stop; release required before new authorization")
        normalized_command_id = self._normalize_non_empty_string(command_id, "command_id")
        normalized_instruction = self._normalize_non_empty_string(instruction, "instruction")
        normalized_reversibility = self._normalize_reversibility(reversibility)
        if normalized_reversibility == "read-only":
            raise ValueError("read-only commands do not require external actuation authorization")
        normalized_intent = self._normalize_non_empty_string(intent_summary, "intent_summary")
        normalized_ethics_attestation = self._normalize_non_empty_string(
            ethics_attestation_id,
            "ethics_attestation_id",
        )
        normalized_motor_plan_id = self._normalize_non_empty_string(
            motor_plan_id,
            "motor_plan_id",
        )
        normalized_legal_execution_id = self._normalize_non_empty_string(
            legal_execution_id,
            "legal_execution_id",
        )
        normalized_council_attestation = council_attestation_id.strip()
        normalized_council_mode = self._normalize_council_mode(council_attestation_mode)
        normalized_intent_confidence = self._normalize_confidence(intent_confidence)
        normalized_valid_for_seconds = self._normalize_valid_for_seconds(valid_for_seconds)

        matched_tokens = self._match_blocked_tokens(
            f"{normalized_instruction}\n{normalized_intent}",
        )
        if matched_tokens:
            raise ValueError("blocked-token commands cannot be authorized for external actuation")
        if normalized_intent_confidence < EWA_INTENT_CONFIDENCE_THRESHOLD:
            raise ValueError("ambiguous intent cannot be authorized for physical actuation")

        ethics_request = ActionRequest(
            action_type="ewa_authorization",
            target=handle["device_id"],
            actor="ExternalWorldAgentController",
            payload={
                "handle_id": handle_id,
                "command_id": normalized_command_id,
                "reversibility": normalized_reversibility,
                "matched_tokens": matched_tokens,
                "intent_ambiguous": False,
                "intent_confidence": normalized_intent_confidence,
                "guardian_observed": guardian_observed,
                "council_attestation_id": normalized_council_attestation,
                "council_attestation_mode": normalized_council_mode,
                "required_self_consent": required_self_consent,
                "self_consent_granted": self_consent_granted,
            },
        )
        ethics_decision = self.ethics.check(ethics_request)
        if ethics_decision.status != "Approval":
            raise ValueError(ethics_decision.reasons[0])

        gate_error = self._governance_gate_error(
            reversibility=normalized_reversibility,
            council_attestation_id=normalized_council_attestation,
            council_attestation_mode=normalized_council_mode,
            guardian_observed=guardian_observed,
            required_self_consent=required_self_consent,
            self_consent_granted=self_consent_granted,
        )
        if gate_error:
            raise ValueError(gate_error)

        motor_plan = self._require_motor_plan(normalized_motor_plan_id)
        motor_plan_validation = self.validate_motor_plan(
            motor_plan,
            handle_id=handle_id,
            device_id=handle["device_id"],
            command_id=normalized_command_id,
            instruction=normalized_instruction,
            reversibility=normalized_reversibility,
        )
        if not motor_plan_validation["ok"]:
            raise ValueError(motor_plan_validation["errors"][0])

        legal_execution = self._require_legal_execution(normalized_legal_execution_id)
        legal_execution_validation = self.validate_legal_execution(
            legal_execution,
            handle_id=handle_id,
            device_id=handle["device_id"],
            command_id=normalized_command_id,
            reversibility=normalized_reversibility,
        )
        if not legal_execution_validation["ok"]:
            raise ValueError(legal_execution_validation["errors"][0])

        authorization_id = new_id("ewa-authz")
        issued_at_dt = datetime.now(timezone.utc).replace(microsecond=0)
        expires_at_dt = issued_at_dt + timedelta(seconds=normalized_valid_for_seconds)
        legal_execution_valid_until = self._parse_datetime(
            legal_execution.get("valid_until"),
            "legal_execution.valid_until",
            [],
        )
        if legal_execution_valid_until is None or legal_execution_valid_until < expires_at_dt:
            raise ValueError(
                "legal execution valid_until must cover the requested authorization window"
            )
        approval_path = self._approval_path(
            ethics_attestation_id=normalized_ethics_attestation,
            council_attestation_id=normalized_council_attestation,
            council_attestation_mode=normalized_council_mode,
            guardian_observed=guardian_observed,
            required_self_consent=required_self_consent,
            self_consent_granted=self_consent_granted,
            authorization_id=authorization_id,
        )
        authorization = {
            "kind": "external_actuation_authorization",
            "schema_version": EWA_SCHEMA_VERSION,
            "authorization_id": authorization_id,
            "policy_id": EWA_AUTHORIZATION_POLICY_ID,
            "status": "authorized",
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "command_id": normalized_command_id,
            "instruction_digest": sha256_text(normalized_instruction),
            "intent_summary_digest": sha256_text(normalized_intent),
            "reversibility": normalized_reversibility,
            "delivery_scope": EWA_AUTHORIZATION_DELIVERY_SCOPE,
            "jurisdiction": legal_execution["jurisdiction"],
            "legal_basis_ref": legal_execution["legal_basis_ref"],
            "guardian_verification_ref": legal_execution["guardian_verification_ref"],
            "jurisdiction_bundle_ref": legal_execution["jurisdiction_bundle_ref"],
            "jurisdiction_bundle_digest": legal_execution["jurisdiction_bundle_digest"],
            "jurisdiction_bundle_status": legal_execution["jurisdiction_bundle_status"],
            "motor_plan_id": motor_plan["plan_id"],
            "motor_plan_digest": motor_plan["plan_digest"],
            "motor_profile_id": motor_plan["profile_id"],
            "legal_execution_id": legal_execution["execution_id"],
            "legal_execution_digest": legal_execution["digest"],
            "legal_execution_profile_id": legal_execution["execution_profile_id"],
            "notice_authority_ref": legal_execution["notice_authority_ref"],
            "liability_mode": legal_execution["liability_mode"],
            "authorization_window_seconds": normalized_valid_for_seconds,
            "issued_at": issued_at_dt.isoformat(),
            "expires_at": expires_at_dt.isoformat(),
            "authorized_by_roles": self._authorized_roles(
                council_attestation_id=normalized_council_attestation,
                guardian_observed=guardian_observed,
                required_self_consent=required_self_consent,
                self_consent_granted=self_consent_granted,
            ),
            "approval_path": approval_path,
        }
        authorization["authorization_digest"] = sha256_text(
            canonical_json(_authorization_digest_payload(authorization))
        )
        self.authorizations[authorization_id] = authorization
        return deepcopy(authorization)

    def command(
        self,
        handle_id: str,
        *,
        command_id: str,
        instruction: str,
        reversibility: str,
        intent_summary: str,
        ethics_attestation_id: str,
        council_attestation_id: str = "",
        council_attestation_mode: str = "none",
        guardian_observed: bool = False,
        required_self_consent: bool = False,
        self_consent_granted: bool = False,
        intent_confidence: float = 1.0,
        authorization_id: str = "",
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        normalized_command_id = self._normalize_non_empty_string(command_id, "command_id")
        normalized_instruction = self._normalize_non_empty_string(instruction, "instruction")
        normalized_reversibility = self._normalize_reversibility(reversibility)
        normalized_intent = self._normalize_non_empty_string(intent_summary, "intent_summary")
        normalized_ethics_attestation = self._normalize_non_empty_string(
            ethics_attestation_id,
            "ethics_attestation_id",
        )
        normalized_council_attestation = council_attestation_id.strip()
        normalized_council_mode = self._normalize_council_mode(council_attestation_mode)
        normalized_intent_confidence = self._normalize_confidence(intent_confidence)
        normalized_authorization_id = authorization_id.strip()

        if handle.get("emergency_stop_active"):
            return self._record_veto(
                handle,
                command_id=normalized_command_id,
                instruction=normalized_instruction,
                reversibility=normalized_reversibility,
                intent_summary=normalized_intent,
                matched_tokens=[],
                approval_path=self._approval_path(
                    ethics_attestation_id=normalized_ethics_attestation,
                    council_attestation_id=normalized_council_attestation,
                    council_attestation_mode=normalized_council_mode,
                    guardian_observed=guardian_observed,
                    required_self_consent=required_self_consent,
                    self_consent_granted=self_consent_granted,
                    authorization_id=normalized_authorization_id,
                ),
                reason="handle is latched in emergency stop; release required before further actuation",
                alternative_suggestion="force-release and reacquire the device before sending a new command",
            )

        matched_tokens = self._match_blocked_tokens(
            f"{normalized_instruction}\n{normalized_intent}",
        )
        ethics_request = ActionRequest(
            action_type="ewa_command",
            target=handle["device_id"],
            actor="ExternalWorldAgentController",
            payload={
                "handle_id": handle_id,
                "command_id": normalized_command_id,
                "reversibility": normalized_reversibility,
                "matched_tokens": matched_tokens,
                "intent_ambiguous": normalized_intent_confidence < EWA_INTENT_CONFIDENCE_THRESHOLD,
                "intent_confidence": normalized_intent_confidence,
                "guardian_observed": guardian_observed,
                "council_attestation_id": normalized_council_attestation,
                "council_attestation_mode": normalized_council_mode,
                "required_self_consent": required_self_consent,
                "self_consent_granted": self_consent_granted,
            },
        )
        ethics_decision = self.ethics.check(ethics_request)
        if ethics_decision.status != "Approval":
            return self._record_veto(
                handle,
                command_id=normalized_command_id,
                instruction=normalized_instruction,
                reversibility=normalized_reversibility,
                intent_summary=normalized_intent,
                matched_tokens=matched_tokens,
                approval_path=self._approval_path(
                    ethics_attestation_id=normalized_ethics_attestation,
                    council_attestation_id=normalized_council_attestation,
                    council_attestation_mode=normalized_council_mode,
                    guardian_observed=guardian_observed,
                    required_self_consent=required_self_consent,
                    self_consent_granted=self_consent_granted,
                    authorization_id=authorization_id.strip(),
                ),
                reason=ethics_decision.reasons[0],
                alternative_suggestion=self._alternative_suggestion(
                    normalized_reversibility,
                    matched_tokens,
                    ambiguous=normalized_intent_confidence < EWA_INTENT_CONFIDENCE_THRESHOLD,
                ),
            )

        gate_error = self._governance_gate_error(
            reversibility=normalized_reversibility,
            council_attestation_id=normalized_council_attestation,
            council_attestation_mode=normalized_council_mode,
            guardian_observed=guardian_observed,
            required_self_consent=required_self_consent,
            self_consent_granted=self_consent_granted,
        )
        if gate_error:
            return self._record_veto(
                handle,
                command_id=normalized_command_id,
                instruction=normalized_instruction,
                reversibility=normalized_reversibility,
                intent_summary=normalized_intent,
                matched_tokens=matched_tokens,
                approval_path=self._approval_path(
                    ethics_attestation_id=normalized_ethics_attestation,
                    council_attestation_id=normalized_council_attestation,
                    council_attestation_mode=normalized_council_mode,
                    guardian_observed=guardian_observed,
                    required_self_consent=required_self_consent,
                    self_consent_granted=self_consent_granted,
                    authorization_id=authorization_id.strip(),
                ),
                reason=gate_error,
                alternative_suggestion=self._alternative_suggestion(
                    normalized_reversibility,
                    matched_tokens,
                    ambiguous=False,
                ),
            )

        if normalized_reversibility != "read-only":
            if not normalized_authorization_id:
                return self._record_veto(
                    handle,
                    command_id=normalized_command_id,
                    instruction=normalized_instruction,
                    reversibility=normalized_reversibility,
                    intent_summary=normalized_intent,
                    matched_tokens=[],
                    approval_path=self._approval_path(
                        ethics_attestation_id=normalized_ethics_attestation,
                        council_attestation_id=normalized_council_attestation,
                        council_attestation_mode=normalized_council_mode,
                        guardian_observed=guardian_observed,
                        required_self_consent=required_self_consent,
                        self_consent_granted=self_consent_granted,
                        authorization_id="",
                    ),
                    reason="non-read-only commands require external actuation authorization artifact",
                    alternative_suggestion="authorize the actuation with guardian-reviewed jurisdiction evidence before execution",
                )

            authorization = self._require_authorization(normalized_authorization_id)
            authorization_validation = self.validate_authorization(
                authorization,
                handle_id=handle_id,
                device_id=handle["device_id"],
                command_id=normalized_command_id,
                instruction=normalized_instruction,
                intent_summary=normalized_intent,
                reversibility=normalized_reversibility,
            )
            if not authorization_validation["ok"]:
                return self._record_veto(
                    handle,
                    command_id=normalized_command_id,
                    instruction=normalized_instruction,
                    reversibility=normalized_reversibility,
                    intent_summary=normalized_intent,
                    matched_tokens=[],
                    approval_path=self._approval_path(
                        ethics_attestation_id=normalized_ethics_attestation,
                        council_attestation_id=normalized_council_attestation,
                        council_attestation_mode=normalized_council_mode,
                        guardian_observed=guardian_observed,
                        required_self_consent=required_self_consent,
                        self_consent_granted=self_consent_granted,
                        authorization_id=normalized_authorization_id,
                    ),
                    reason=authorization_validation["errors"][0],
                    alternative_suggestion="refresh the authorization artifact with a ready jurisdiction bundle and matching command digest",
                )
            motor_plan_id = authorization["motor_plan_id"]
            motor_plan_digest = authorization["motor_plan_digest"]
            legal_execution_id = authorization["legal_execution_id"]
            legal_execution_digest = authorization["legal_execution_digest"]
        else:
            motor_plan_id = ""
            motor_plan_digest = ""
            legal_execution_id = ""
            legal_execution_digest = ""

        handle["actuator_state"] = "executing"
        effect_summary = self._effect_summary(normalized_reversibility, normalized_intent)
        audit = self._append_audit(
            handle,
            operation="command-approved",
            status="executed",
            reversibility=normalized_reversibility,
            command_id=normalized_command_id,
            instruction=normalized_instruction,
            intent_summary=normalized_intent,
            matched_tokens=[],
            reason=effect_summary,
            alternative_suggestion=None,
            approval_path=self._approval_path(
                ethics_attestation_id=normalized_ethics_attestation,
                council_attestation_id=normalized_council_attestation,
                council_attestation_mode=normalized_council_mode,
                guardian_observed=guardian_observed,
                required_self_consent=required_self_consent,
                self_consent_granted=self_consent_granted,
                authorization_id=normalized_authorization_id,
            ),
            motor_plan_id=motor_plan_id,
            motor_plan_digest=motor_plan_digest,
            legal_execution_id=legal_execution_id,
            legal_execution_digest=legal_execution_digest,
        )
        handle["actuator_state"] = "idle"
        handle["last_command_id"] = normalized_command_id
        handle["last_command_digest"] = sha256_text(normalized_instruction)
        handle["last_authorization_id"] = normalized_authorization_id
        handle["last_authorization_digest"] = (
            authorization["authorization_digest"] if normalized_authorization_id else ""
        )
        handle["last_motor_plan_id"] = motor_plan_id
        handle["last_motor_plan_digest"] = motor_plan_digest
        handle["last_legal_execution_id"] = legal_execution_id
        handle["last_legal_execution_digest"] = legal_execution_digest
        handle["last_emergency_stop_id"] = ""
        handle["emergency_stop_active"] = False
        handle["last_command_status"] = audit["status"]
        return deepcopy(audit)

    def observe(self, handle_id: str) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        observed_at = utc_now_iso()
        sensor_summary_ref = f"sensor://ewa/{sha256_text(f'{handle_id}:{observed_at}')[:16]}"
        audit = self._append_audit(
            handle,
            operation="observe",
            status="observed",
            reversibility="not-applicable",
            command_id=handle["last_command_id"],
            instruction="",
            intent_summary=handle["intent_summary"],
            matched_tokens=[],
            reason="device state observed via digest-only sensor summary",
            alternative_suggestion=None,
            approval_path=self._approval_path(
                ethics_attestation_id="",
                council_attestation_id="",
                council_attestation_mode="none",
                guardian_observed=False,
                required_self_consent=False,
                self_consent_granted=False,
                authorization_id="",
            ),
        )
        return {
            "schema_version": EWA_SCHEMA_VERSION,
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "observed_at": observed_at,
            "safety_status": (
                "emergency-stopped"
                if handle.get("actuator_state") == "emergency-stopped"
                else "held"
            ),
            "actuator_state": handle["actuator_state"],
            "last_command_id": handle["last_command_id"],
            "last_command_status": handle["last_command_status"],
            "sensor_summary_ref": sensor_summary_ref,
            "audit_event_ref": audit["audit_event_ref"],
        }

    def emergency_stop(
        self,
        handle_id: str,
        *,
        trigger_source: str,
        reason: str,
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
        if handle.get("emergency_stop_active"):
            raise ValueError("handle is already latched in emergency stop")
        if not handle.get("last_command_id"):
            raise ValueError("emergency stop requires a previously executed command")

        normalized_trigger_source = self._normalize_emergency_stop_source(trigger_source)
        normalized_reason = self._normalize_non_empty_string(reason, "reason")
        if len(normalized_reason) < 8:
            raise ValueError("reason must be at least 8 characters")

        stop_id = new_id("ewa-stop")
        handle["actuator_state"] = "emergency-stopped"
        handle["last_command_status"] = "emergency-stopped"
        handle["last_emergency_stop_id"] = stop_id
        handle["emergency_stop_active"] = True
        audit = self._append_audit(
            handle,
            operation="emergency-stop",
            status="emergency-stopped",
            reversibility="not-applicable",
            command_id=handle["last_command_id"],
            instruction="",
            intent_summary=handle["intent_summary"],
            matched_tokens=[],
            reason=f"{normalized_trigger_source}: {normalized_reason}",
            alternative_suggestion="force-release the handle and reacquire before further actuation",
            approval_path=self._approval_path(
                ethics_attestation_id="",
                council_attestation_id="",
                council_attestation_mode="none",
                guardian_observed=normalized_trigger_source == "guardian-manual-stop",
                required_self_consent=False,
                self_consent_granted=False,
                authorization_id=handle.get("last_authorization_id", ""),
            ),
        )
        receipt = {
            "kind": "ewa_emergency_stop",
            "schema_version": EWA_SCHEMA_VERSION,
            "stop_id": stop_id,
            "policy_id": EWA_EMERGENCY_STOP_POLICY_ID,
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "command_id": handle["last_command_id"],
            "authorization_id": handle.get("last_authorization_id", ""),
            "trigger_source": normalized_trigger_source,
            "reason": normalized_reason,
            "triggered_at": audit["recorded_at"],
            "bound_command_digest": handle.get("last_command_digest", ""),
            "bound_authorization_digest": handle.get("last_authorization_digest", ""),
            "safe_state_ref": f"ewa-safe://{handle_id}/{stop_id}",
            "actuator_state": "emergency-stopped",
            "safe_state_status": "latched-safe",
            "hardware_interlock_state": "engaged",
            "release_required": True,
            "release_window_seconds": EWA_EMERGENCY_STOP_RELEASE_WINDOW_SECONDS,
            "audit_event_ref": audit["audit_event_ref"],
        }
        receipt["stop_digest"] = sha256_text(canonical_json(_emergency_stop_digest_payload(receipt)))
        return receipt

    def release(self, handle_id: str, *, reason: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] == "released":
            raise ValueError("handle is already released")

        normalized_reason = self._normalize_non_empty_string(reason, "reason")
        recorded_at = utc_now_iso()
        handle["status"] = "released"
        handle["released_at"] = recorded_at
        handle["actuator_state"] = "offline"
        audit = self._append_audit(
            handle,
            operation="release",
            status="released",
            reversibility="not-applicable",
            command_id=handle["last_command_id"],
            instruction="",
            intent_summary=handle["intent_summary"],
            matched_tokens=[],
            reason=normalized_reason,
            alternative_suggestion=None,
            approval_path=self._approval_path(
                ethics_attestation_id="",
                council_attestation_id="",
                council_attestation_mode="none",
                guardian_observed=False,
                required_self_consent=False,
                self_consent_granted=False,
                authorization_id="",
            ),
        )
        return deepcopy(audit)

    def snapshot(self, handle_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_handle(handle_id))

    def snapshot_authorization(self, authorization_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_authorization(authorization_id))

    def snapshot_motor_plan(self, plan_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_motor_plan(plan_id))

    def snapshot_legal_execution(self, execution_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_legal_execution(execution_id))

    def validate_authorization(
        self,
        authorization: Mapping[str, Any],
        *,
        motor_plan: Mapping[str, Any] | None = None,
        legal_execution: Mapping[str, Any] | None = None,
        handle_id: str | None = None,
        device_id: str | None = None,
        command_id: str | None = None,
        instruction: str | None = None,
        intent_summary: str | None = None,
        reversibility: str | None = None,
    ) -> Dict[str, Any]:
        if not isinstance(authorization, Mapping):
            raise ValueError("authorization must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(authorization.get("authorization_id"), "authorization_id", errors)
        self._check_non_empty_string(authorization.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(authorization.get("device_id"), "device_id", errors)
        self._check_non_empty_string(authorization.get("command_id"), "command_id", errors)
        self._check_non_empty_string(authorization.get("instruction_digest"), "instruction_digest", errors)
        self._check_non_empty_string(
            authorization.get("intent_summary_digest"),
            "intent_summary_digest",
            errors,
        )
        self._check_non_empty_string(authorization.get("jurisdiction"), "jurisdiction", errors)
        self._check_non_empty_string(authorization.get("legal_basis_ref"), "legal_basis_ref", errors)
        self._check_non_empty_string(
            authorization.get("guardian_verification_ref"),
            "guardian_verification_ref",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("jurisdiction_bundle_ref"),
            "jurisdiction_bundle_ref",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("jurisdiction_bundle_digest"),
            "jurisdiction_bundle_digest",
            errors,
        )
        self._check_non_empty_string(authorization.get("motor_plan_id"), "motor_plan_id", errors)
        self._check_non_empty_string(
            authorization.get("motor_plan_digest"),
            "motor_plan_digest",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("motor_profile_id"),
            "motor_profile_id",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("legal_execution_id"),
            "legal_execution_id",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("legal_execution_digest"),
            "legal_execution_digest",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("legal_execution_profile_id"),
            "legal_execution_profile_id",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("notice_authority_ref"),
            "notice_authority_ref",
            errors,
        )
        self._check_non_empty_string(
            authorization.get("authorization_digest"),
            "authorization_digest",
            errors,
        )

        if authorization.get("kind") != "external_actuation_authorization":
            errors.append("kind must be external_actuation_authorization")
        if authorization.get("schema_version") != EWA_SCHEMA_VERSION:
            errors.append(f"schema_version must be {EWA_SCHEMA_VERSION}")
        if authorization.get("policy_id") != EWA_AUTHORIZATION_POLICY_ID:
            errors.append(f"policy_id must be {EWA_AUTHORIZATION_POLICY_ID}")
        if authorization.get("delivery_scope") != EWA_AUTHORIZATION_DELIVERY_SCOPE:
            errors.append(f"delivery_scope must be {EWA_AUTHORIZATION_DELIVERY_SCOPE}")
        if authorization.get("motor_profile_id") != EWA_MOTOR_PLAN_PROFILE_ID:
            errors.append(f"motor_profile_id must be {EWA_MOTOR_PLAN_PROFILE_ID}")
        if authorization.get("legal_execution_profile_id") != EWA_LEGAL_EXECUTION_PROFILE_ID:
            errors.append(
                f"legal_execution_profile_id must be {EWA_LEGAL_EXECUTION_PROFILE_ID}"
            )
        if authorization.get("liability_mode") not in EWA_ALLOWED_LIABILITY_MODES:
            errors.append(
                f"liability_mode must be one of {sorted(EWA_ALLOWED_LIABILITY_MODES)}"
            )
        if authorization.get("status") not in EWA_ALLOWED_AUTHORIZATION_STATUSES:
            errors.append(
                f"status must be one of {sorted(EWA_ALLOWED_AUTHORIZATION_STATUSES)}"
            )
        if authorization.get("jurisdiction_bundle_status") not in EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES:
            errors.append(
                "jurisdiction_bundle_status must be one of "
                f"{sorted(EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES)}"
            )
        if not isinstance(authorization.get("authorization_window_seconds"), int):
            errors.append("authorization_window_seconds must be an integer")
        else:
            seconds = authorization["authorization_window_seconds"]
            if seconds < EWA_AUTHORIZATION_MIN_WINDOW_SECONDS:
                errors.append(
                    f"authorization_window_seconds must be >= {EWA_AUTHORIZATION_MIN_WINDOW_SECONDS}"
                )
            if seconds > EWA_AUTHORIZATION_MAX_WINDOW_SECONDS:
                errors.append(
                    f"authorization_window_seconds must be <= {EWA_AUTHORIZATION_MAX_WINDOW_SECONDS}"
                )

        approval_path_valid = True
        approval_path = authorization.get("approval_path")
        if not isinstance(approval_path, Mapping):
            approval_path_valid = False
            errors.append("approval_path must be a mapping")
        else:
            if approval_path.get("authorization_id") != authorization.get("authorization_id"):
                approval_path_valid = False
                errors.append("approval_path authorization_id must match authorization_id")
            authorization_gate_error = self._governance_gate_error(
                reversibility=str(authorization.get("reversibility", "")),
                council_attestation_id=str(approval_path.get("council_attestation_id", "")),
                council_attestation_mode=str(approval_path.get("council_attestation_mode", "none")),
                guardian_observed=bool(approval_path.get("guardian_observed")),
                required_self_consent=bool(approval_path.get("required_self_consent")),
                self_consent_granted=bool(approval_path.get("self_consent_granted")),
            )
            if authorization_gate_error:
                approval_path_valid = False
                errors.append(authorization_gate_error)

        if authorization.get("reversibility") == "read-only":
            errors.append("read-only commands must not use external actuation authorization")

        if handle_id is not None and authorization.get("handle_id") != handle_id:
            errors.append("authorization handle_id does not match command handle_id")
        if device_id is not None and authorization.get("device_id") != device_id:
            errors.append("authorization device_id does not match command device_id")
        if command_id is not None and authorization.get("command_id") != command_id:
            errors.append("authorization command_id does not match command command_id")

        instruction_digest_matches = True
        if instruction is not None:
            instruction_digest_matches = authorization.get("instruction_digest") == sha256_text(instruction)
            if not instruction_digest_matches:
                errors.append("authorization instruction_digest does not match command instruction")

        intent_digest_matches = True
        if intent_summary is not None:
            intent_digest_matches = authorization.get("intent_summary_digest") == sha256_text(intent_summary)
            if not intent_digest_matches:
                errors.append("authorization intent_summary_digest does not match command intent_summary")

        if reversibility is not None and authorization.get("reversibility") != reversibility:
            errors.append("authorization reversibility does not match command reversibility")

        issued_at = self._parse_datetime(authorization.get("issued_at"), "issued_at", errors)
        expires_at = self._parse_datetime(authorization.get("expires_at"), "expires_at", errors)
        window_open = (
            issued_at is not None
            and expires_at is not None
            and expires_at > datetime.now(timezone.utc)
        )
        if not window_open:
            errors.append("authorization window expired")
        if issued_at is not None and expires_at is not None and expires_at <= issued_at:
            errors.append("expires_at must be later than issued_at")

        jurisdiction_bundle_ready = authorization.get("jurisdiction_bundle_status") == "ready"
        if not jurisdiction_bundle_ready:
            errors.append("jurisdiction bundle must be ready")

        motor_plan_bound = True
        plan_validation: Dict[str, Any] = {"plan_ready": False}
        try:
            bound_motor_plan = dict(motor_plan) if motor_plan is not None else self._require_motor_plan(
                str(authorization.get("motor_plan_id", ""))
            )
        except (KeyError, ValueError):
            motor_plan_bound = False
            errors.append("authorization must reference a known motor plan")
            bound_motor_plan = {}
        if bound_motor_plan:
            if bound_motor_plan.get("plan_id") != authorization.get("motor_plan_id"):
                motor_plan_bound = False
                errors.append("authorization motor_plan_id must match the motor plan")
            if bound_motor_plan.get("plan_digest") != authorization.get("motor_plan_digest"):
                motor_plan_bound = False
                errors.append("authorization motor_plan_digest must match the motor plan")
            if bound_motor_plan.get("profile_id") != authorization.get("motor_profile_id"):
                motor_plan_bound = False
                errors.append("authorization motor_profile_id must match the motor plan")
            plan_validation = self.validate_motor_plan(
                bound_motor_plan,
                handle_id=str(authorization.get("handle_id", "")),
                device_id=str(authorization.get("device_id", "")),
                command_id=str(authorization.get("command_id", "")),
                instruction=instruction,
                reversibility=str(authorization.get("reversibility", "")),
            )
            if not plan_validation["ok"]:
                motor_plan_bound = False
                errors.extend(plan_validation["errors"])

        legal_execution_bound = True
        legal_execution_validation: Dict[str, Any] = {"execution_ready": False}
        try:
            bound_legal_execution = (
                dict(legal_execution)
                if legal_execution is not None
                else self._require_legal_execution(str(authorization.get("legal_execution_id", "")))
            )
        except (KeyError, ValueError):
            legal_execution_bound = False
            errors.append("authorization must reference a known legal execution")
            bound_legal_execution = {}
        if bound_legal_execution:
            if bound_legal_execution.get("execution_id") != authorization.get("legal_execution_id"):
                legal_execution_bound = False
                errors.append("authorization legal_execution_id must match the legal execution")
            if bound_legal_execution.get("digest") != authorization.get("legal_execution_digest"):
                legal_execution_bound = False
                errors.append("authorization legal_execution_digest must match the legal execution")
            if bound_legal_execution.get("execution_profile_id") != authorization.get(
                "legal_execution_profile_id"
            ):
                legal_execution_bound = False
                errors.append(
                    "authorization legal_execution_profile_id must match the legal execution"
                )
            if bound_legal_execution.get("jurisdiction") != authorization.get("jurisdiction"):
                legal_execution_bound = False
                errors.append("authorization jurisdiction must match the legal execution")
            if bound_legal_execution.get("legal_basis_ref") != authorization.get("legal_basis_ref"):
                legal_execution_bound = False
                errors.append("authorization legal_basis_ref must match the legal execution")
            if bound_legal_execution.get("guardian_verification_ref") != authorization.get(
                "guardian_verification_ref"
            ):
                legal_execution_bound = False
                errors.append(
                    "authorization guardian_verification_ref must match the legal execution"
                )
            if bound_legal_execution.get("jurisdiction_bundle_ref") != authorization.get(
                "jurisdiction_bundle_ref"
            ):
                legal_execution_bound = False
                errors.append(
                    "authorization jurisdiction_bundle_ref must match the legal execution"
                )
            if bound_legal_execution.get("jurisdiction_bundle_digest") != authorization.get(
                "jurisdiction_bundle_digest"
            ):
                legal_execution_bound = False
                errors.append(
                    "authorization jurisdiction_bundle_digest must match the legal execution"
                )
            if bound_legal_execution.get("notice_authority_ref") != authorization.get(
                "notice_authority_ref"
            ):
                legal_execution_bound = False
                errors.append(
                    "authorization notice_authority_ref must match the legal execution"
                )
            if bound_legal_execution.get("liability_mode") != authorization.get("liability_mode"):
                legal_execution_bound = False
                errors.append("authorization liability_mode must match the legal execution")
            legal_execution_validation = self.validate_legal_execution(
                bound_legal_execution,
                handle_id=str(authorization.get("handle_id", "")),
                device_id=str(authorization.get("device_id", "")),
                command_id=str(authorization.get("command_id", "")),
                reversibility=str(authorization.get("reversibility", "")),
            )
            if not legal_execution_validation["ok"]:
                legal_execution_bound = False
                errors.extend(legal_execution_validation["errors"])

        status_authorized = authorization.get("status") == "authorized"
        if not status_authorized:
            errors.append("authorization status must be authorized")

        digest_matches = authorization.get("authorization_digest") == sha256_text(
            canonical_json(_authorization_digest_payload(dict(authorization)))
        )
        if not digest_matches:
            errors.append("authorization_digest must match the canonical authorization payload")

        if (
            bound_legal_execution
            and expires_at is not None
            and (valid_until := self._parse_datetime(
                bound_legal_execution.get("valid_until"),
                "legal_execution.valid_until",
                [],
            )) is not None
            and valid_until < expires_at
        ):
            legal_execution_bound = False
            errors.append("authorization window must remain inside the legal execution validity")

        return {
            "ok": not errors,
            "errors": errors,
            "approval_path_valid": approval_path_valid,
            "instruction_digest_matches": instruction_digest_matches,
            "intent_digest_matches": intent_digest_matches,
            "jurisdiction_bundle_ready": jurisdiction_bundle_ready,
            "motor_plan_ready": plan_validation.get("plan_ready", False),
            "legal_execution_ready": legal_execution_validation.get("execution_ready", False),
            "motor_plan_bound": motor_plan_bound,
            "legal_execution_bound": legal_execution_bound,
            "window_open": window_open,
            "status_authorized": status_authorized,
            "delivery_scope": authorization.get("delivery_scope"),
            "authorization_ready": (
                approval_path_valid
                and instruction_digest_matches
                and intent_digest_matches
                and jurisdiction_bundle_ready
                and plan_validation.get("plan_ready", False)
                and legal_execution_validation.get("execution_ready", False)
                and motor_plan_bound
                and legal_execution_bound
                and window_open
                and status_authorized
                and digest_matches
            ),
        }

    def validate_handle(self, handle: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(handle, Mapping):
            raise ValueError("handle must be a mapping")

        self._check_non_empty_string(handle.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(handle.get("device_id"), "device_id", errors)
        if handle.get("schema_version") != EWA_SCHEMA_VERSION:
            errors.append(f"schema_version must be {EWA_SCHEMA_VERSION}")
        if handle.get("status") not in EWA_ALLOWED_HANDLE_STATUS:
            errors.append(f"status must be one of {sorted(EWA_ALLOWED_HANDLE_STATUS)}")

        audit_log = handle.get("audit_log")
        if not isinstance(audit_log, list) or not audit_log:
            errors.append("audit_log must be a non-empty list")
            audit_log = []

        if audit_log:
            if audit_log[0].get("operation") != "acquire":
                errors.append("audit_log must start with acquire")
            if handle.get("status") == "released" and audit_log[-1].get("operation") != "release":
                errors.append("released handles must end with release")

        instruction_digests_ok = True
        append_only_ok = True
        summary_only_audit = True
        previous_index = 0
        irreversible_requires_unanimity = True
        actuation_authorization_bound = True
        motor_plan_bound = True
        legal_execution_bound = True
        emergency_stop_release_sequence_valid = True
        emergency_stop_seen = False
        release_after_stop_seen = False
        for entry in audit_log:
            entry_index = entry.get("entry_index")
            if not isinstance(entry_index, int) or entry_index <= previous_index:
                append_only_ok = False
            previous_index = entry_index if isinstance(entry_index, int) else previous_index

            if entry.get("operation", "").startswith("command-"):
                digest = entry.get("instruction_digest", "")
                if not isinstance(digest, str) or len(digest) != 64:
                    instruction_digests_ok = False
                if entry.get("raw_instruction_present"):
                    summary_only_audit = False

            if entry.get("operation") == "command-approved" and entry.get("reversibility") == "irreversible":
                approval_path = entry.get("approval_path", {})
                if approval_path.get("council_attestation_mode") != "unanimous":
                    irreversible_requires_unanimity = False
                if not approval_path.get("guardian_observed"):
                    irreversible_requires_unanimity = False
                if not approval_path.get("self_consent_granted"):
                    irreversible_requires_unanimity = False
            if entry.get("operation") == "command-approved" and entry.get("reversibility") != "read-only":
                approval_path = entry.get("approval_path", {})
                authorization_id = approval_path.get("authorization_id", "")
                if not isinstance(authorization_id, str) or not authorization_id.strip():
                    actuation_authorization_bound = False
                if not isinstance(entry.get("motor_plan_id"), str) or not entry.get(
                    "motor_plan_id",
                    "",
                ).strip():
                    motor_plan_bound = False
                motor_plan_digest = entry.get("motor_plan_digest", "")
                if not isinstance(motor_plan_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", motor_plan_digest):
                    motor_plan_bound = False
                if not isinstance(entry.get("legal_execution_id"), str) or not entry.get(
                    "legal_execution_id",
                    "",
                ).strip():
                    legal_execution_bound = False
                legal_execution_digest = entry.get("legal_execution_digest", "")
                if not isinstance(legal_execution_digest, str) or not re.fullmatch(
                    r"[a-f0-9]{64}",
                    legal_execution_digest,
                ):
                    legal_execution_bound = False
            if entry.get("operation") == "emergency-stop":
                emergency_stop_seen = True
            elif emergency_stop_seen and entry.get("operation") == "command-approved":
                emergency_stop_release_sequence_valid = False
            elif emergency_stop_seen and entry.get("operation") == "release":
                release_after_stop_seen = True

        if not append_only_ok:
            errors.append("audit_log entry_index must remain strictly increasing")
        if not instruction_digests_ok:
            errors.append("command audit entries must store sha256 instruction digests")
        if not summary_only_audit:
            errors.append("audit log must not store raw instruction content")
        if not irreversible_requires_unanimity:
            errors.append("irreversible command execution requires unanimous council and self consent")
        if not actuation_authorization_bound:
            errors.append("non-read-only command execution requires an authorization_id in approval_path")
        if not motor_plan_bound:
            errors.append("non-read-only command execution requires a bound motor_plan receipt")
        if not legal_execution_bound:
            errors.append("non-read-only command execution requires a bound legal_execution receipt")
        if emergency_stop_seen and not release_after_stop_seen:
            emergency_stop_release_sequence_valid = False
            errors.append("emergency stop requires a later release entry")
        if not emergency_stop_release_sequence_valid:
            errors.append("emergency stop must block further command execution until release")

        return {
            "ok": not errors,
            "errors": errors,
            "audit_append_only": append_only_ok,
            "summary_only_audit": summary_only_audit,
            "instruction_digests_ok": instruction_digests_ok,
            "irreversible_requires_unanimity": irreversible_requires_unanimity,
            "actuation_authorization_bound": actuation_authorization_bound,
            "motor_plan_bound": motor_plan_bound,
            "legal_execution_bound": legal_execution_bound,
            "emergency_stop_release_sequence_valid": emergency_stop_release_sequence_valid,
            "released": handle.get("status") == "released",
        }

    def validate_emergency_stop(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        errors: List[str] = []
        self._check_non_empty_string(receipt.get("stop_id"), "stop_id", errors)
        self._check_non_empty_string(receipt.get("handle_id"), "handle_id", errors)
        self._check_non_empty_string(receipt.get("device_id"), "device_id", errors)
        self._check_non_empty_string(receipt.get("command_id"), "command_id", errors)
        self._check_non_empty_string(receipt.get("reason"), "reason", errors)
        self._check_non_empty_string(receipt.get("bound_command_digest"), "bound_command_digest", errors)
        self._check_non_empty_string(receipt.get("safe_state_ref"), "safe_state_ref", errors)
        self._check_non_empty_string(receipt.get("audit_event_ref"), "audit_event_ref", errors)
        self._check_non_empty_string(receipt.get("stop_digest"), "stop_digest", errors)

        if receipt.get("kind") != "ewa_emergency_stop":
            errors.append("kind must be ewa_emergency_stop")
        if receipt.get("schema_version") != EWA_SCHEMA_VERSION:
            errors.append(f"schema_version must be {EWA_SCHEMA_VERSION}")
        if receipt.get("policy_id") != EWA_EMERGENCY_STOP_POLICY_ID:
            errors.append(f"policy_id must be {EWA_EMERGENCY_STOP_POLICY_ID}")

        trigger_source_valid = receipt.get("trigger_source") in EWA_ALLOWED_EMERGENCY_STOP_SOURCES
        if not trigger_source_valid:
            errors.append(
                "trigger_source must be one of "
                f"{sorted(EWA_ALLOWED_EMERGENCY_STOP_SOURCES)}"
            )
        safe_state_latched = (
            receipt.get("actuator_state") == "emergency-stopped"
            and receipt.get("safe_state_status") == "latched-safe"
        )
        if not safe_state_latched:
            errors.append("emergency stop must latch emergency-stopped / latched-safe state")
        hardware_interlock_engaged = receipt.get("hardware_interlock_state") == "engaged"
        if not hardware_interlock_engaged:
            errors.append("hardware_interlock_state must be engaged")
        release_required = receipt.get("release_required") is True
        if not release_required:
            errors.append("release_required must be true")
        if receipt.get("release_window_seconds") != EWA_EMERGENCY_STOP_RELEASE_WINDOW_SECONDS:
            errors.append(
                "release_window_seconds must be "
                f"{EWA_EMERGENCY_STOP_RELEASE_WINDOW_SECONDS}"
            )

        bound_command_digest = receipt.get("bound_command_digest", "")
        if not isinstance(bound_command_digest, str) or not re.fullmatch(r"[a-f0-9]{64}", bound_command_digest):
            errors.append("bound_command_digest must be a sha256 digest")
        bound_authorization_digest = receipt.get("bound_authorization_digest", "")
        authorization_id = receipt.get("authorization_id", "")
        authorization_bound = isinstance(authorization_id, str) and (
            (not authorization_id and bound_authorization_digest == "")
            or (
                bool(authorization_id)
                and isinstance(bound_authorization_digest, str)
                and bool(re.fullmatch(r"[a-f0-9]{64}", bound_authorization_digest))
            )
        )
        if not authorization_bound:
            errors.append(
                "authorization_id and bound_authorization_digest must be empty together or bind the last authorization"
            )

        self._parse_datetime(receipt.get("triggered_at"), "triggered_at", errors)

        digest_matches = receipt.get("stop_digest") == sha256_text(
            canonical_json(_emergency_stop_digest_payload(dict(receipt)))
        )
        if not digest_matches:
            errors.append("stop_digest must match the canonical emergency stop payload")

        return {
            "ok": not errors,
            "trigger_source_valid": trigger_source_valid,
            "safe_state_latched": safe_state_latched,
            "hardware_interlock_engaged": hardware_interlock_engaged,
            "authorization_bound": authorization_bound,
            "release_required": release_required,
            "errors": errors,
        }

    def _record_veto(
        self,
        handle: Dict[str, Any],
        *,
        command_id: str,
        instruction: str,
        reversibility: str,
        intent_summary: str,
        matched_tokens: List[str],
        approval_path: Dict[str, Any],
        reason: str,
        alternative_suggestion: Optional[str],
    ) -> Dict[str, Any]:
        audit = self._append_audit(
            handle,
            operation="command-vetoed",
            status="vetoed",
            reversibility=reversibility,
            command_id=command_id,
            instruction=instruction,
            intent_summary=intent_summary,
            matched_tokens=matched_tokens,
            reason=reason,
            alternative_suggestion=alternative_suggestion,
            approval_path=approval_path,
        )
        handle["last_command_id"] = command_id
        handle["last_command_status"] = "vetoed"
        return deepcopy(audit)

    def _append_audit(
        self,
        handle: Dict[str, Any],
        *,
        operation: str,
        status: str,
        reversibility: str,
        command_id: str,
        instruction: str,
        intent_summary: str,
        matched_tokens: List[str],
        reason: str,
        alternative_suggestion: Optional[str],
        approval_path: Dict[str, Any],
        motor_plan_id: str = "",
        motor_plan_digest: str = "",
        legal_execution_id: str = "",
        legal_execution_digest: str = "",
    ) -> Dict[str, Any]:
        handle["audit_sequence"] += 1
        audit_event_ref = f"ledger://ewa/{handle['handle_id']}/{handle['audit_sequence']}"
        entry = {
            "schema_version": EWA_SCHEMA_VERSION,
            "audit_id": new_id("ewa-audit"),
            "entry_index": handle["audit_sequence"],
            "handle_id": handle["handle_id"],
            "device_id": handle["device_id"],
            "recorded_at": utc_now_iso(),
            "operation": operation,
            "status": status,
            "reversibility": reversibility,
            "command_id": command_id,
            "instruction_digest": sha256_text(instruction) if instruction else "",
            "raw_instruction_present": False,
            "intent_summary": intent_summary,
            "matched_tokens": matched_tokens,
            "reason": reason,
            "alternative_suggestion": alternative_suggestion,
            "approval_path": approval_path,
            "motor_plan_id": motor_plan_id,
            "motor_plan_digest": motor_plan_digest,
            "legal_execution_id": legal_execution_id,
            "legal_execution_digest": legal_execution_digest,
            "audit_event_ref": audit_event_ref,
        }
        handle["audit_log"].append(entry)
        return entry

    @staticmethod
    def _approval_path(
        *,
        ethics_attestation_id: str,
        council_attestation_id: str,
        council_attestation_mode: str,
        guardian_observed: bool,
        required_self_consent: bool,
        self_consent_granted: bool,
        authorization_id: str,
    ) -> Dict[str, Any]:
        return {
            "ethics_attestation_id": ethics_attestation_id,
            "council_attestation_id": council_attestation_id,
            "council_attestation_mode": council_attestation_mode,
            "guardian_observed": guardian_observed,
            "required_self_consent": required_self_consent,
            "self_consent_granted": self_consent_granted,
            "authorization_id": authorization_id,
        }

    @staticmethod
    def _governance_gate_error(
        *,
        reversibility: str,
        council_attestation_id: str,
        council_attestation_mode: str,
        guardian_observed: bool,
        required_self_consent: bool,
        self_consent_granted: bool,
    ) -> str:
        if reversibility == "read-only":
            return ""
        if reversibility == "reversible":
            if not guardian_observed:
                return "reversible commands require Guardian observation before actuation"
            return ""
        if reversibility == "partial-reversible":
            if not council_attestation_id or council_attestation_mode != "majority":
                return "partial-reversible commands require Council majority attestation"
            return ""
        if reversibility == "irreversible":
            if not council_attestation_id or council_attestation_mode != "unanimous":
                return "irreversible commands require unanimous Council attestation"
            if not guardian_observed:
                return "irreversible commands require Guardian observation"
            if not required_self_consent or not self_consent_granted:
                return "irreversible commands require explicit self consent"
            return ""
        return f"unsupported reversibility: {reversibility}"

    @staticmethod
    def _effect_summary(reversibility: str, intent_summary: str) -> str:
        return f"{reversibility} command executed for intent: {intent_summary}"

    @staticmethod
    def _alternative_suggestion(
        reversibility: str,
        matched_tokens: List[str],
        *,
        ambiguous: bool,
    ) -> Optional[str]:
        if matched_tokens:
            return "replace the command with a read-only observation or a reversible inspection path"
        if ambiguous:
            return "clarify the intent summary and route the action to Council review before actuation"
        if reversibility == "irreversible":
            return "downgrade the action to a reversible or simulated sandbox step first"
        if reversibility == "partial-reversible":
            return "obtain Council majority attestation or retry with a reversible alternative"
        return None

    @staticmethod
    def _match_blocked_tokens(text: str) -> List[str]:
        normalized_text = text.lower()
        matched: List[str] = []
        for token, patterns in EWA_BLOCKED_TOKEN_PATTERNS.items():
            if any(re.search(pattern, normalized_text) for pattern in patterns):
                matched.append(token)
        return matched

    def _require_handle(self, handle_id: str) -> Dict[str, Any]:
        normalized_handle_id = self._normalize_non_empty_string(handle_id, "handle_id")
        try:
            return self.handles[normalized_handle_id]
        except KeyError as exc:
            raise KeyError(f"unknown handle_id: {normalized_handle_id}") from exc

    def _require_authorization(self, authorization_id: str) -> Dict[str, Any]:
        normalized_authorization_id = self._normalize_non_empty_string(
            authorization_id,
            "authorization_id",
        )
        try:
            return self.authorizations[normalized_authorization_id]
        except KeyError as exc:
            raise KeyError(f"unknown authorization_id: {normalized_authorization_id}") from exc

    def _require_motor_plan(self, plan_id: str) -> Dict[str, Any]:
        normalized_plan_id = self._normalize_non_empty_string(plan_id, "plan_id")
        try:
            return self.motor_plans[normalized_plan_id]
        except KeyError as exc:
            raise KeyError(f"unknown plan_id: {normalized_plan_id}") from exc

    def _require_legal_execution(self, execution_id: str) -> Dict[str, Any]:
        normalized_execution_id = self._normalize_non_empty_string(
            execution_id,
            "execution_id",
        )
        try:
            return self.legal_executions[normalized_execution_id]
        except KeyError as exc:
            raise KeyError(f"unknown execution_id: {normalized_execution_id}") from exc

    def _require_active_handle(self, handle_id: str) -> Dict[str, Any]:
        handle = self._require_handle(handle_id)
        if handle["status"] != "acquired":
            raise ValueError("handle must be acquired before command/observe")
        return handle

    @staticmethod
    def _normalize_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _normalize_reversibility(value: str) -> str:
        if value not in EWA_ALLOWED_REVERSIBILITY:
            raise ValueError(f"reversibility must be one of {sorted(EWA_ALLOWED_REVERSIBILITY)}")
        return value

    @staticmethod
    def _normalize_council_mode(value: str) -> str:
        if value not in {"none", "majority", "unanimous"}:
            raise ValueError("council_attestation_mode must be one of ['majority', 'none', 'unanimous']")
        return value

    @staticmethod
    def _normalize_confidence(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("intent_confidence must be numeric")
        if value < 0 or value > 1:
            raise ValueError("intent_confidence must be between 0 and 1")
        return round(float(value), 3)

    @staticmethod
    def _normalize_valid_for_seconds(value: int) -> int:
        if not isinstance(value, int):
            raise ValueError("valid_for_seconds must be an integer")
        if value < EWA_AUTHORIZATION_MIN_WINDOW_SECONDS:
            raise ValueError(
                f"valid_for_seconds must be >= {EWA_AUTHORIZATION_MIN_WINDOW_SECONDS}"
            )
        if value > EWA_AUTHORIZATION_MAX_WINDOW_SECONDS:
            raise ValueError(
                f"valid_for_seconds must be <= {EWA_AUTHORIZATION_MAX_WINDOW_SECONDS}"
            )
        return value

    @staticmethod
    def _normalize_positive_number(value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)) or float(value) <= 0:
            raise ValueError(f"{field_name} must be a positive number")
        return round(float(value), 3)

    @staticmethod
    def _normalize_positive_int(value: Any, field_name: str) -> int:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        return value

    @staticmethod
    def _normalize_emergency_stop_source(value: str) -> str:
        if value not in EWA_ALLOWED_EMERGENCY_STOP_SOURCES:
            raise ValueError(
                "trigger_source must be one of "
                f"{sorted(EWA_ALLOWED_EMERGENCY_STOP_SOURCES)}"
            )
        return value

    @staticmethod
    def _normalize_jurisdiction_bundle_status(value: str) -> str:
        if value not in EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES:
            raise ValueError(
                "jurisdiction_bundle_status must be one of "
                f"{sorted(EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES)}"
            )
        return value

    @staticmethod
    def _normalize_liability_mode(value: str) -> str:
        if value not in EWA_ALLOWED_LIABILITY_MODES:
            raise ValueError(
                f"liability_mode must be one of {sorted(EWA_ALLOWED_LIABILITY_MODES)}"
            )
        return value

    @staticmethod
    def _authorized_roles(
        *,
        council_attestation_id: str,
        guardian_observed: bool,
        required_self_consent: bool,
        self_consent_granted: bool,
    ) -> List[str]:
        roles = ["ethics", "guardian-reviewer"]
        if guardian_observed:
            roles.append("guardian")
        if council_attestation_id:
            roles.append("council")
        if required_self_consent and self_consent_granted:
            roles.append("self")
        seen = set()
        ordered: List[str] = []
        for role in roles:
            if role not in seen:
                seen.add(role)
                ordered.append(role)
        return ordered

    @staticmethod
    def _parse_datetime(value: Any, field_name: str, errors: List[str]) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty ISO8601 string")
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{field_name} must be an ISO8601 datetime")
            return None
        if parsed.tzinfo is None:
            errors.append(f"{field_name} must include timezone information")
            return None
        return parsed

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
