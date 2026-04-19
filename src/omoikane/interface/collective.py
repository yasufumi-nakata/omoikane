"""Bounded collective identity and merge-thought reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence, Set

from ..common import new_id, utc_now_iso

COLLECTIVE_SCHEMA_VERSION = "1.0"
COLLECTIVE_MIN_MEMBERS = 2
COLLECTIVE_MAX_MEMBERS = 4
COLLECTIVE_MAX_DURATION_SECONDS = 10.0
COLLECTIVE_ALLOWED_STATUSES = {"active", "recovery", "dissolved"}
COLLECTIVE_ALLOWED_MERGE_STATUSES = {"open", "completed", "recovery-required"}
COLLECTIVE_ALLOWED_WMS_MODES = {"shared_reality", "private_reality", "mixed"}


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


class CollectiveIdentityService:
    """Deterministic reference model for bounded collective identity formation."""

    def __init__(self) -> None:
        self.records: Dict[str, Dict[str, Any]] = {}
        self.merge_sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "formation_mode": "bounded-collective-merge-v0",
            "member_count_bounds": {
                "min": COLLECTIVE_MIN_MEMBERS,
                "max": COLLECTIVE_MAX_MEMBERS,
            },
            "governance_mode": "meta-council",
            "merge_policy": {
                "merge_mode": "merge_thought",
                "max_duration_seconds": COLLECTIVE_MAX_DURATION_SECONDS,
                "single_active_merge_per_collective": True,
                "council_witness_required": True,
                "federation_attestation_required": True,
                "guardian_observation_required": True,
                "post_disconnect_identity_confirmation": "all-members",
                "escape_route": "private_reality",
            },
            "dissolution_policy": {
                "member_quorum": "unanimous",
                "active_merge_required": False,
                "member_recovery_required": True,
            },
        }

    def register_collective(
        self,
        *,
        collective_identity_id: str,
        member_ids: Sequence[str],
        purpose: str,
        proposed_name: str,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
    ) -> Dict[str, Any]:
        collective_id = self._normalize_non_empty_string(collective_identity_id, "collective_identity_id")
        if collective_id in self.records:
            raise ValueError(f"collective already registered: {collective_id}")

        members = self._normalize_member_ids(member_ids)
        purpose_text = self._normalize_non_empty_string(purpose, "purpose")
        proposed_name_text = self._normalize_non_empty_string(proposed_name, "proposed_name")
        self._require_oversight(
            council_witnessed=council_witnessed,
            federation_attested=federation_attested,
            guardian_observed=guardian_observed,
        )

        created_at = utc_now_iso()
        record = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "collective_id": collective_id,
            "created_at": created_at,
            "display_name": proposed_name_text,
            "status": "active",
            "member_ids": members,
            "governance_mode": "meta-council",
            "formation_mode": "bounded-collective-merge-v0",
            "purpose": purpose_text,
            "merge_policy": {
                "merge_mode": "merge_thought",
                "max_duration_seconds": COLLECTIVE_MAX_DURATION_SECONDS,
                "post_disconnect_identity_confirmation": "all-members",
                "escape_route": "private_reality",
                "single_active_merge_per_collective": True,
            },
            "oversight": {
                "council_witnessed": True,
                "federation_attested": True,
                "guardian_observed": True,
            },
            "active_merge_session_ids": [],
            "last_merge_status": "none",
            "dissolved_at": None,
            "last_dissolution": None,
        }
        self.records[collective_id] = record
        return deepcopy(record)

    def open_merge_session(
        self,
        *,
        collective_id: str,
        imc_session_id: str,
        wms_session_id: str,
        requested_duration_seconds: float,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
        shared_world_mode: str,
    ) -> Dict[str, Any]:
        record = self._require_record(collective_id)
        if record["status"] != "active":
            raise ValueError("collective must be active before opening a merge session")
        if record["active_merge_session_ids"]:
            raise ValueError("collective already has an active merge session")

        self._require_oversight(
            council_witnessed=council_witnessed,
            federation_attested=federation_attested,
            guardian_observed=guardian_observed,
        )
        imc_ref = self._normalize_non_empty_string(imc_session_id, "imc_session_id")
        wms_ref = self._normalize_non_empty_string(wms_session_id, "wms_session_id")
        requested = self._normalize_duration(requested_duration_seconds, "requested_duration_seconds")
        granted = min(requested, COLLECTIVE_MAX_DURATION_SECONDS)
        mode = self._normalize_wms_mode(shared_world_mode, "shared_world_mode")
        merge_session_id = new_id("collective-merge")
        opened_at = utc_now_iso()
        session = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "merge_session_id": merge_session_id,
            "collective_id": record["collective_id"],
            "opened_at": opened_at,
            "closed_at": None,
            "status": "open",
            "merge_mode": "merge_thought",
            "imc_session_id": imc_ref,
            "wms_session_id": wms_ref,
            "requested_duration_seconds": requested,
            "granted_duration_seconds": granted,
            "duration_capped": requested > COLLECTIVE_MAX_DURATION_SECONDS,
            "shared_world_mode": mode,
            "oversight": {
                "council_witnessed": True,
                "federation_attested": True,
                "guardian_observed": True,
            },
            "identity_confirmation_required": list(record["member_ids"]),
            "disconnect_reason": "",
            "identity_confirmations": {},
            "time_in_merge_seconds": None,
            "within_budget": None,
            "resulting_wms_mode": None,
            "private_escape_honored": False,
            "audit_event_ref": "",
        }
        self.merge_sessions[merge_session_id] = session
        record["active_merge_session_ids"].append(merge_session_id)
        record["last_merge_status"] = "open"
        return deepcopy(session)

    def close_merge_session(
        self,
        merge_session_id: str,
        *,
        disconnect_reason: str,
        time_in_merge_seconds: float,
        resulting_wms_mode: str,
        identity_confirmations: Mapping[str, bool],
    ) -> Dict[str, Any]:
        session = self._require_merge_session(merge_session_id)
        if session["status"] != "open":
            raise ValueError("merge session must be open before it can be closed")

        reason_text = self._normalize_non_empty_string(disconnect_reason, "disconnect_reason")
        elapsed = self._normalize_duration(time_in_merge_seconds, "time_in_merge_seconds")
        resulting_mode = self._normalize_wms_mode(resulting_wms_mode, "resulting_wms_mode")
        confirmations = self._normalize_confirmations(
            identity_confirmations,
            session["identity_confirmation_required"],
        )
        within_budget = elapsed <= session["granted_duration_seconds"]
        all_confirmed = all(confirmations.values())
        status = "completed" if within_budget and all_confirmed else "recovery-required"
        closed_at = utc_now_iso()

        session["closed_at"] = closed_at
        session["status"] = status
        session["disconnect_reason"] = reason_text
        session["identity_confirmations"] = confirmations
        session["time_in_merge_seconds"] = elapsed
        session["within_budget"] = within_budget
        session["resulting_wms_mode"] = resulting_mode
        session["private_escape_honored"] = resulting_mode == "private_reality"
        session["audit_event_ref"] = f"ledger://collective-merge/{new_id('collective-audit')}"

        record = self._require_record(session["collective_id"])
        record["active_merge_session_ids"] = [
            merge_id for merge_id in record["active_merge_session_ids"] if merge_id != merge_session_id
        ]
        record["last_merge_status"] = status
        if status == "recovery-required":
            record["status"] = "recovery"

        return deepcopy(session)

    def dissolve_collective(
        self,
        collective_id: str,
        *,
        requested_by: str,
        member_confirmations: Mapping[str, bool],
        reason: str,
    ) -> Dict[str, Any]:
        record = self._require_record(collective_id)
        if record["active_merge_session_ids"]:
            raise ValueError("cannot dissolve a collective while a merge session is active")

        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")
        confirmations = self._normalize_confirmations(member_confirmations, record["member_ids"])
        if not all(confirmations.values()):
            raise PermissionError("dissolution requires unanimous member confirmation")

        dissolved_at = utc_now_iso()
        receipt = {
            "collective_id": record["collective_id"],
            "recorded_at": dissolved_at,
            "requested_by": requester,
            "status": "dissolved",
            "member_confirmations": confirmations,
            "reason": reason_text,
            "member_recovery_required": True,
            "audit_event_ref": f"ledger://collective-dissolution/{new_id('collective-dissolution')}",
        }
        record["status"] = "dissolved"
        record["dissolved_at"] = dissolved_at
        record["last_dissolution"] = receipt
        return deepcopy(receipt)

    def snapshot(self, collective_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_record(collective_id))

    def merge_snapshot(self, merge_session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_merge_session(merge_session_id))

    def validate_record(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(record, Mapping):
            raise ValueError("record must be a mapping")

        self._check_non_empty_string(record.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(record.get("display_name"), "display_name", errors)
        self._check_non_empty_string(record.get("created_at"), "created_at", errors)
        if record.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if record.get("status") not in COLLECTIVE_ALLOWED_STATUSES:
            errors.append(f"status must be one of {sorted(COLLECTIVE_ALLOWED_STATUSES)}")

        member_ids = record.get("member_ids")
        if not isinstance(member_ids, list):
            errors.append("member_ids must be a list")
            member_count = 0
        else:
            member_count = len(member_ids)
            if member_count < COLLECTIVE_MIN_MEMBERS or member_count > COLLECTIVE_MAX_MEMBERS:
                errors.append(
                    f"member_ids must contain between {COLLECTIVE_MIN_MEMBERS} and {COLLECTIVE_MAX_MEMBERS} entries"
                )
            if len(set(member_ids)) != len(member_ids):
                errors.append("member_ids must be unique")

        merge_policy = record.get("merge_policy")
        if not isinstance(merge_policy, Mapping):
            errors.append("merge_policy must be an object")
            merge_window_bounded = False
        else:
            merge_window_bounded = merge_policy.get("max_duration_seconds") == COLLECTIVE_MAX_DURATION_SECONDS
            if merge_policy.get("merge_mode") != "merge_thought":
                errors.append("merge_policy.merge_mode must equal merge_thought")
            if not merge_window_bounded:
                errors.append(
                    f"merge_policy.max_duration_seconds must equal {COLLECTIVE_MAX_DURATION_SECONDS}"
                )
            if merge_policy.get("post_disconnect_identity_confirmation") != "all-members":
                errors.append("merge_policy.post_disconnect_identity_confirmation must equal all-members")
            if merge_policy.get("escape_route") != "private_reality":
                errors.append("merge_policy.escape_route must equal private_reality")

        oversight = record.get("oversight")
        oversight_bound = self._oversight_bound(oversight)
        if not oversight_bound:
            errors.append("oversight must record council witness, federation attestation, and guardian observation")

        active_merge_session_ids = record.get("active_merge_session_ids")
        if not isinstance(active_merge_session_ids, list):
            errors.append("active_merge_session_ids must be a list")
            active_merge_bound = False
        else:
            active_merge_bound = len(active_merge_session_ids) <= 1
            if not active_merge_bound:
                errors.append("active_merge_session_ids must contain at most one session")

        return {
            "ok": not errors,
            "errors": errors,
            "member_count": member_count,
            "merge_window_bounded": merge_window_bounded,
            "oversight_bound": oversight_bound,
            "active_merge_bound": active_merge_bound,
        }

    def validate_merge_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(session, Mapping):
            raise ValueError("session must be a mapping")

        self._check_non_empty_string(session.get("merge_session_id"), "merge_session_id", errors)
        self._check_non_empty_string(session.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(session.get("opened_at"), "opened_at", errors)
        if session.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if session.get("status") not in COLLECTIVE_ALLOWED_MERGE_STATUSES:
            errors.append(f"status must be one of {sorted(COLLECTIVE_ALLOWED_MERGE_STATUSES)}")
        if session.get("merge_mode") != "merge_thought":
            errors.append("merge_mode must equal merge_thought")

        granted = session.get("granted_duration_seconds")
        merge_window_bounded = isinstance(granted, (int, float)) and granted <= COLLECTIVE_MAX_DURATION_SECONDS
        if not merge_window_bounded:
            errors.append(f"granted_duration_seconds must be <= {COLLECTIVE_MAX_DURATION_SECONDS}")

        oversight_bound = self._oversight_bound(session.get("oversight"))
        if not oversight_bound:
            errors.append("oversight must record council witness, federation attestation, and guardian observation")

        required_confirmations = session.get("identity_confirmation_required")
        if not isinstance(required_confirmations, list) or not required_confirmations:
            errors.append("identity_confirmation_required must be a non-empty list")

        resulting_mode = session.get("resulting_wms_mode")
        if resulting_mode is not None and resulting_mode not in COLLECTIVE_ALLOWED_WMS_MODES:
            errors.append(f"resulting_wms_mode must be one of {sorted(COLLECTIVE_ALLOWED_WMS_MODES)}")

        return {
            "ok": not errors,
            "errors": errors,
            "merge_window_bounded": merge_window_bounded,
            "oversight_bound": oversight_bound,
            "identity_confirmation_complete": bool(session.get("identity_confirmations"))
            and all(bool(value) for value in session.get("identity_confirmations", {}).values()),
            "private_escape_honored": session.get("private_escape_honored") is True,
        }

    def _require_record(self, collective_id: str) -> Dict[str, Any]:
        collective = self._normalize_non_empty_string(collective_id, "collective_id")
        try:
            return self.records[collective]
        except KeyError as exc:
            raise KeyError(f"unknown collective: {collective}") from exc

    def _require_merge_session(self, merge_session_id: str) -> Dict[str, Any]:
        merge_id = self._normalize_non_empty_string(merge_session_id, "merge_session_id")
        try:
            return self.merge_sessions[merge_id]
        except KeyError as exc:
            raise KeyError(f"unknown merge session: {merge_id}") from exc

    def _normalize_member_ids(self, member_ids: Sequence[str]) -> List[str]:
        if not isinstance(member_ids, Sequence) or isinstance(member_ids, (str, bytes)):
            raise ValueError("member_ids must be a sequence of identity ids")
        normalized = [
            self._normalize_non_empty_string(member_id, f"member_ids[{index}]")
            for index, member_id in enumerate(member_ids)
        ]
        deduped = _dedupe_preserve_order(normalized)
        if len(deduped) < COLLECTIVE_MIN_MEMBERS or len(deduped) > COLLECTIVE_MAX_MEMBERS:
            raise ValueError(
                f"collective must contain between {COLLECTIVE_MIN_MEMBERS} and {COLLECTIVE_MAX_MEMBERS} unique members"
            )
        return deduped

    @staticmethod
    def _normalize_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _normalize_duration(value: Any, field_name: str) -> float:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{field_name} must be a positive number")
        normalized = float(value)
        if normalized <= 0:
            raise ValueError(f"{field_name} must be > 0")
        return normalized

    @staticmethod
    def _normalize_wms_mode(value: Any, field_name: str) -> str:
        if value not in COLLECTIVE_ALLOWED_WMS_MODES:
            raise ValueError(f"{field_name} must be one of {sorted(COLLECTIVE_ALLOWED_WMS_MODES)}")
        return str(value)

    def _normalize_confirmations(
        self,
        confirmations: Mapping[str, bool],
        required_member_ids: Sequence[str],
    ) -> Dict[str, bool]:
        if not isinstance(confirmations, Mapping):
            raise ValueError("identity confirmations must be a mapping")
        normalized: Dict[str, bool] = {}
        for member_id in required_member_ids:
            if member_id not in confirmations:
                raise ValueError(f"missing identity confirmation for {member_id}")
            normalized[member_id] = bool(confirmations[member_id])
        return normalized

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    @staticmethod
    def _oversight_bound(oversight: Any) -> bool:
        return isinstance(oversight, Mapping) and all(
            oversight.get(field) is True
            for field in ("council_witnessed", "federation_attested", "guardian_observed")
        )

    def _require_oversight(
        self,
        *,
        council_witnessed: bool,
        federation_attested: bool,
        guardian_observed: bool,
    ) -> None:
        if not council_witnessed:
            raise PermissionError("collective operations require council witness")
        if not federation_attested:
            raise PermissionError("collective operations require federation attestation")
        if not guardian_observed:
            raise PermissionError("collective operations require guardian observation")
