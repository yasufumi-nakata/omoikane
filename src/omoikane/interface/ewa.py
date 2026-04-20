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
EWA_ALLOWED_AUTHORIZATION_STATUSES = {"authorized", "expired", "revoked"}
EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES = {"ready", "stale", "revoked"}
EWA_AUTHORIZATION_MIN_WINDOW_SECONDS = 60
EWA_AUTHORIZATION_MAX_WINDOW_SECONDS = 900
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


class ExternalWorldAgentController:
    """Deterministic L6 physical-actuation boundary with ethics-first gating."""

    def __init__(self, ethics: Optional[EthicsEnforcer] = None) -> None:
        self.ethics = ethics or EthicsEnforcer()
        self.handles: Dict[str, Dict[str, Any]] = {}
        self.authorizations: Dict[str, Dict[str, Any]] = {}

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

    def authorize(
        self,
        handle_id: str,
        *,
        command_id: str,
        instruction: str,
        reversibility: str,
        intent_summary: str,
        ethics_attestation_id: str,
        jurisdiction: str,
        legal_basis_ref: str,
        guardian_verification_ref: str,
        jurisdiction_bundle_ref: str,
        jurisdiction_bundle_digest: str,
        jurisdiction_bundle_status: str = "ready",
        council_attestation_id: str = "",
        council_attestation_mode: str = "none",
        guardian_observed: bool = False,
        required_self_consent: bool = False,
        self_consent_granted: bool = False,
        intent_confidence: float = 1.0,
        valid_for_seconds: int = 300,
    ) -> Dict[str, Any]:
        handle = self._require_active_handle(handle_id)
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
        normalized_jurisdiction = self._normalize_non_empty_string(jurisdiction, "jurisdiction")
        normalized_legal_basis_ref = self._normalize_non_empty_string(
            legal_basis_ref,
            "legal_basis_ref",
        )
        normalized_guardian_verification_ref = self._normalize_non_empty_string(
            guardian_verification_ref,
            "guardian_verification_ref",
        )
        normalized_bundle_ref = self._normalize_non_empty_string(
            jurisdiction_bundle_ref,
            "jurisdiction_bundle_ref",
        )
        normalized_bundle_digest = self._normalize_non_empty_string(
            jurisdiction_bundle_digest,
            "jurisdiction_bundle_digest",
        )
        normalized_bundle_status = self._normalize_jurisdiction_bundle_status(
            jurisdiction_bundle_status,
        )
        normalized_council_attestation = council_attestation_id.strip()
        normalized_council_mode = self._normalize_council_mode(council_attestation_mode)
        normalized_intent_confidence = self._normalize_confidence(intent_confidence)
        normalized_valid_for_seconds = self._normalize_valid_for_seconds(valid_for_seconds)

        if normalized_bundle_status != "ready":
            raise ValueError("jurisdiction bundle must be ready before actuation authorization")

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

        authorization_id = new_id("ewa-authz")
        issued_at_dt = datetime.now(timezone.utc).replace(microsecond=0)
        expires_at_dt = issued_at_dt + timedelta(seconds=normalized_valid_for_seconds)
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
            "jurisdiction": normalized_jurisdiction,
            "legal_basis_ref": normalized_legal_basis_ref,
            "guardian_verification_ref": normalized_guardian_verification_ref,
            "jurisdiction_bundle_ref": normalized_bundle_ref,
            "jurisdiction_bundle_digest": normalized_bundle_digest,
            "jurisdiction_bundle_status": normalized_bundle_status,
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

        normalized_authorization_id = authorization_id.strip()
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
                authorization_id="",
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
                authorization_id="",
            ),
        )
        return deepcopy(audit)

    def snapshot(self, handle_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_handle(handle_id))

    def snapshot_authorization(self, authorization_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_authorization(authorization_id))

    def validate_authorization(
        self,
        authorization: Mapping[str, Any],
        *,
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

        status_authorized = authorization.get("status") == "authorized"
        if not status_authorized:
            errors.append("authorization status must be authorized")

        digest_matches = authorization.get("authorization_digest") == sha256_text(
            canonical_json(_authorization_digest_payload(dict(authorization)))
        )
        if not digest_matches:
            errors.append("authorization_digest must match the canonical authorization payload")

        return {
            "ok": not errors,
            "errors": errors,
            "approval_path_valid": approval_path_valid,
            "instruction_digest_matches": instruction_digest_matches,
            "intent_digest_matches": intent_digest_matches,
            "jurisdiction_bundle_ready": jurisdiction_bundle_ready,
            "window_open": window_open,
            "status_authorized": status_authorized,
            "delivery_scope": authorization.get("delivery_scope"),
            "authorization_ready": (
                approval_path_valid
                and instruction_digest_matches
                and intent_digest_matches
                and jurisdiction_bundle_ready
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

        return {
            "ok": not errors,
            "errors": errors,
            "audit_append_only": append_only_ok,
            "summary_only_audit": summary_only_audit,
            "instruction_digests_ok": instruction_digests_ok,
            "irreversible_requires_unanimity": irreversible_requires_unanimity,
            "actuation_authorization_bound": actuation_authorization_bound,
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
    def _normalize_jurisdiction_bundle_status(value: str) -> str:
        if value not in EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES:
            raise ValueError(
                "jurisdiction_bundle_status must be one of "
                f"{sorted(EWA_ALLOWED_JURISDICTION_BUNDLE_STATUSES)}"
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
