"""World Model Sync reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence

from ..common import new_id, utc_now_iso

WMS_SCHEMA_VERSION = "1.0"
WMS_MINOR_DIFF_THRESHOLD = 0.05
WMS_DEFAULT_TIME_RATE = 1.0
WMS_DEFAULT_PHYSICS_RULES_REF = "baseline-physical-consensus-v1"
WMS_ALLOWED_MODES = {"shared_reality", "private_reality", "mixed"}
WMS_ALLOWED_AUTHORITIES = {"consensus", "local", "broker"}


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


class WorldModelSync:
    """Deterministic L6 world-state reconciliation and escape model."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": WMS_SCHEMA_VERSION,
            "modes": ["shared_reality", "private_reality", "mixed"],
            "minor_diff_threshold": WMS_MINOR_DIFF_THRESHOLD,
            "default_time_rate": WMS_DEFAULT_TIME_RATE,
            "private_escape_free": True,
            "malicious_inject_action": "guardian-veto",
            "consensus_policy": {
                "minor_diff": "consensus_round",
                "major_diff": "offer-private-reality",
                "malicious_inject": "guardian-veto",
            },
        }

    def create_session(
        self,
        participants: Sequence[str],
        *,
        mode: str = "shared_reality",
        objects: Sequence[str],
        authority: str = "consensus",
        physics_rules_ref: str = WMS_DEFAULT_PHYSICS_RULES_REF,
        time_rate: float = WMS_DEFAULT_TIME_RATE,
    ) -> Dict[str, Any]:
        normalized_participants = self._normalize_string_list(participants, "participants")
        normalized_objects = self._normalize_string_list(objects, "objects")
        normalized_mode = self._normalize_mode(mode)
        normalized_authority = self._normalize_authority(authority)
        normalized_physics_rules = self._normalize_non_empty_string(
            physics_rules_ref,
            "physics_rules_ref",
        )
        normalized_time_rate = self._normalize_time_rate(time_rate)

        session_id = new_id("wms")
        recorded_at = utc_now_iso()
        state = {
            "schema_version": WMS_SCHEMA_VERSION,
            "state_id": new_id("world-state"),
            "participants": normalized_participants,
            "spatial_layout": self._layout_ref(normalized_mode, normalized_objects),
            "objects": normalized_objects,
            "physics_rules_ref": normalized_physics_rules,
            "time_rate": normalized_time_rate,
            "authority": normalized_authority,
            "recorded_at": recorded_at,
        }
        session = {
            "schema_version": WMS_SCHEMA_VERSION,
            "session_id": session_id,
            "mode": normalized_mode,
            "authority": normalized_authority,
            "baseline_state": deepcopy(state),
            "current_state": deepcopy(state),
            "consensus_rounds": 0,
            "last_reconcile": None,
            "last_violation": None,
        }
        self.sessions[session_id] = session
        return deepcopy(session)

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        return deepcopy(session["current_state"])

    def propose_diff(
        self,
        session_id: str,
        *,
        proposer_id: str,
        candidate_objects: Sequence[str],
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float = WMS_DEFAULT_TIME_RATE,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        proposer = self._normalize_non_empty_string(proposer_id, "proposer_id")
        objects = self._normalize_string_list(candidate_objects, "candidate_objects")
        ratio = self._normalize_ratio(affected_object_ratio, "affected_object_ratio")
        time_rate = self._normalize_time_rate(requested_time_rate)

        classification = self._classify_diff(
            session,
            proposer_id=proposer,
            affected_object_ratio=ratio,
            attested=attested,
            requested_time_rate=time_rate,
        )
        reconcile_id = new_id("wms-reconcile")
        recorded_at = utc_now_iso()
        audit_event_ref = f"ledger://wms-reconcile/{reconcile_id}"

        if classification == "malicious_inject":
            violation = self._build_violation(
                session,
                classification=classification,
                proposer_id=proposer,
                affected_object_ratio=ratio,
                attested=attested,
                requested_time_rate=time_rate,
                audit_event_ref=audit_event_ref,
            )
            session["last_violation"] = violation
            result = {
                "schema_version": WMS_SCHEMA_VERSION,
                "reconcile_id": reconcile_id,
                "session_id": session_id,
                "recorded_at": recorded_at,
                "classification": classification,
                "decision": "guardian-veto",
                "consensus_required": False,
                "guardian_action": "isolate-session",
                "council_notification": "async-audit-only",
                "escape_offered": True,
                "resulting_mode": session["mode"],
                "resulting_state_id": session["current_state"]["state_id"],
                "affected_object_ratio": ratio,
                "requested_time_rate": time_rate,
                "audit_event_ref": audit_event_ref,
            }
            session["last_reconcile"] = result
            return deepcopy(result)

        candidate_state = {
            "schema_version": WMS_SCHEMA_VERSION,
            "state_id": new_id("world-state"),
            "participants": list(session["current_state"]["participants"]),
            "spatial_layout": self._layout_ref(session["mode"], objects),
            "objects": objects,
            "physics_rules_ref": session["current_state"]["physics_rules_ref"],
            "time_rate": session["current_state"]["time_rate"],
            "authority": session["current_state"]["authority"],
            "recorded_at": recorded_at,
        }

        if classification == "minor_diff":
            session["consensus_rounds"] += 1
            session["current_state"] = candidate_state
            decision = "consensus-round"
            guardian_action = "continue-shared-sync"
            council_notification = "not-required"
            escape_offered = False
        else:
            decision = "offer-private-reality"
            guardian_action = "await-human-choice"
            council_notification = "required"
            escape_offered = True

        result = {
            "schema_version": WMS_SCHEMA_VERSION,
            "reconcile_id": reconcile_id,
            "session_id": session_id,
            "recorded_at": recorded_at,
            "classification": classification,
            "decision": decision,
            "consensus_required": classification == "minor_diff",
            "guardian_action": guardian_action,
            "council_notification": council_notification,
            "escape_offered": escape_offered,
            "resulting_mode": session["mode"],
            "resulting_state_id": (
                candidate_state["state_id"]
                if classification == "minor_diff"
                else session["current_state"]["state_id"]
            ),
            "affected_object_ratio": ratio,
            "requested_time_rate": time_rate,
            "audit_event_ref": audit_event_ref,
        }
        session["last_reconcile"] = result
        return deepcopy(result)

    def switch_mode(
        self,
        session_id: str,
        *,
        mode: str,
        requested_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        target_mode = self._normalize_mode(mode)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")

        previous_mode = session["mode"]
        session["mode"] = target_mode
        session["current_state"]["authority"] = "local" if target_mode == "private_reality" else "consensus"
        session["current_state"]["spatial_layout"] = self._layout_ref(
            target_mode,
            session["current_state"]["objects"],
        )
        session["current_state"]["recorded_at"] = utc_now_iso()

        return {
            "session_id": session_id,
            "recorded_at": session["current_state"]["recorded_at"],
            "old_mode": previous_mode,
            "new_mode": target_mode,
            "requested_by": requester,
            "reason": reason_text,
            "authority": session["current_state"]["authority"],
            "private_escape_honored": previous_mode == "shared_reality"
            and target_mode == "private_reality",
            "resulting_state_id": session["current_state"]["state_id"],
            "audit_event_ref": f"ledger://wms-mode/{new_id('wms-mode')}",
        }

    def observe_violation(self, session_id: str) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["last_violation"] is None:
            return {
                "session_id": session_id,
                "observed_at": utc_now_iso(),
                "violation_detected": False,
                "classification": "none",
                "guardian_action": "continue-shared-sync",
                "requires_council_review": False,
                "audit_event_ref": "",
            }
        return deepcopy(session["last_violation"])

    def validate_state(self, state: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        self._check_non_empty_string(state.get("state_id"), "state_id", errors)
        participants = state.get("participants")
        if not isinstance(participants, list) or not participants:
            errors.append("participants must be a non-empty list")
        else:
            for participant in participants:
                if not isinstance(participant, str) or not participant.strip():
                    errors.append("participants must contain non-empty strings")
                    break

        objects = state.get("objects")
        if not isinstance(objects, list) or not objects:
            errors.append("objects must be a non-empty list")
        else:
            for obj in objects:
                if not isinstance(obj, str) or not obj.strip():
                    errors.append("objects must contain non-empty strings")
                    break

        if state.get("schema_version") != WMS_SCHEMA_VERSION:
            errors.append(f"schema_version must be {WMS_SCHEMA_VERSION}")

        authority = state.get("authority")
        if authority not in WMS_ALLOWED_AUTHORITIES:
            errors.append(f"authority must be one of {sorted(WMS_ALLOWED_AUTHORITIES)}")

        time_rate = state.get("time_rate")
        if not isinstance(time_rate, (int, float)) or float(time_rate) <= 0:
            errors.append("time_rate must be > 0")

        return {
            "ok": not errors,
            "errors": errors,
            "time_rate_locked": float(time_rate or 0) == WMS_DEFAULT_TIME_RATE,
            "authority_valid": authority in WMS_ALLOWED_AUTHORITIES,
            "participants_count": len(participants) if isinstance(participants, list) else 0,
        }

    def _classify_diff(
        self,
        session: Mapping[str, Any],
        *,
        proposer_id: str,
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float,
    ) -> str:
        participants = set(session["current_state"]["participants"])
        if not attested or proposer_id not in participants:
            return "malicious_inject"
        if requested_time_rate != session["current_state"]["time_rate"]:
            return "major_diff"
        if affected_object_ratio < WMS_MINOR_DIFF_THRESHOLD:
            return "minor_diff"
        return "major_diff"

    def _build_violation(
        self,
        session: Mapping[str, Any],
        *,
        classification: str,
        proposer_id: str,
        affected_object_ratio: float,
        attested: bool,
        requested_time_rate: float,
        audit_event_ref: str,
    ) -> Dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "observed_at": utc_now_iso(),
            "violation_detected": True,
            "classification": classification,
            "proposer_id": proposer_id,
            "attested": attested,
            "affected_object_ratio": affected_object_ratio,
            "requested_time_rate": requested_time_rate,
            "guardian_action": "isolate-session",
            "requires_council_review": False,
            "audit_event_ref": audit_event_ref,
        }

    @staticmethod
    def _normalize_non_empty_string(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def _normalize_string_list(self, values: Sequence[str], field_name: str) -> List[str]:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise ValueError(f"{field_name} must be a sequence of strings")
        normalized = [
            self._normalize_non_empty_string(value, field_name)
            for value in values
        ]
        deduped = _dedupe_preserve_order(normalized)
        if not deduped:
            raise ValueError(f"{field_name} must contain at least one value")
        return deduped

    @staticmethod
    def _normalize_ratio(value: float, field_name: str) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be numeric")
        normalized = round(float(value), 3)
        if normalized < 0 or normalized > 1:
            raise ValueError(f"{field_name} must be between 0 and 1")
        return normalized

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        if mode not in WMS_ALLOWED_MODES:
            raise ValueError(f"mode must be one of {sorted(WMS_ALLOWED_MODES)}")
        return mode

    @staticmethod
    def _normalize_authority(authority: str) -> str:
        if authority not in WMS_ALLOWED_AUTHORITIES:
            raise ValueError(f"authority must be one of {sorted(WMS_ALLOWED_AUTHORITIES)}")
        return authority

    @staticmethod
    def _normalize_time_rate(value: float) -> float:
        if not isinstance(value, (int, float)):
            raise ValueError("time_rate must be numeric")
        normalized = round(float(value), 3)
        if normalized <= 0:
            raise ValueError("time_rate must be > 0")
        return normalized

    @staticmethod
    def _layout_ref(mode: str, objects: Sequence[str]) -> str:
        return f"scene://{mode}/{len(objects)}-objects"

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError(f"unknown session_id: {session_id}")
        return self.sessions[session_id]

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")
