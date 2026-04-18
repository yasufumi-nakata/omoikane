"""External World Agents reference model."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional

from ..common import new_id, sha256_text, utc_now_iso
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


class ExternalWorldAgentController:
    """Deterministic L6 physical-actuation boundary with ethics-first gating."""

    def __init__(self, ethics: Optional[EthicsEnforcer] = None) -> None:
        self.ethics = ethics or EthicsEnforcer()
        self.handles: Dict[str, Dict[str, Any]] = {}

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
                ),
                reason=gate_error,
                alternative_suggestion=self._alternative_suggestion(
                    normalized_reversibility,
                    matched_tokens,
                    ambiguous=False,
                ),
            )

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
            ),
        )
        handle["actuator_state"] = "idle"
        handle["last_command_id"] = normalized_command_id
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
            ),
        )
        return {
            "schema_version": EWA_SCHEMA_VERSION,
            "handle_id": handle_id,
            "device_id": handle["device_id"],
            "observed_at": observed_at,
            "safety_status": "held",
            "actuator_state": handle["actuator_state"],
            "last_command_id": handle["last_command_id"],
            "last_command_status": handle["last_command_status"],
            "sensor_summary_ref": sensor_summary_ref,
            "audit_event_ref": audit["audit_event_ref"],
        }

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
            ),
        )
        return deepcopy(audit)

    def snapshot(self, handle_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_handle(handle_id))

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

        if not append_only_ok:
            errors.append("audit_log entry_index must remain strictly increasing")
        if not instruction_digests_ok:
            errors.append("command audit entries must store sha256 instruction digests")
        if not summary_only_audit:
            errors.append("audit log must not store raw instruction content")
        if not irreversible_requires_unanimity:
            errors.append("irreversible command execution requires unanimous council and self consent")

        return {
            "ok": not errors,
            "errors": errors,
            "audit_append_only": append_only_ok,
            "summary_only_audit": summary_only_audit,
            "instruction_digests_ok": instruction_digests_ok,
            "irreversible_requires_unanimity": irreversible_requires_unanimity,
            "released": handle.get("status") == "released",
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
    ) -> Dict[str, Any]:
        return {
            "ethics_attestation_id": ethics_attestation_id,
            "council_attestation_id": council_attestation_id,
            "council_attestation_mode": council_attestation_mode,
            "guardian_observed": guardian_observed,
            "required_self_consent": required_self_consent,
            "self_consent_granted": self_consent_granted,
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
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
