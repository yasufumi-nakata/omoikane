"""Inter-Mind Channel reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence, Set

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

IMC_SCHEMA_VERSION = "1.0"
IMC_ALLOWED_MODES = {
    "text",
    "voice",
    "presence",
    "affect_share",
    "memory_glimpse",
    "co_imagination",
    "merge_thought",
}
IMC_ALLOWED_STATUS = {"open", "closed"}
IMC_MODE_FIELD_CLASSES = {
    "text": ("public_fields",),
    "voice": ("public_fields",),
    "presence": ("public_fields",),
    "affect_share": ("public_fields", "intimate_fields"),
    "memory_glimpse": ("public_fields", "intimate_fields"),
    "co_imagination": ("public_fields", "intimate_fields"),
    "merge_thought": ("public_fields", "intimate_fields"),
}
IMC_MODE_OVERSIGHT = {
    "text": "none",
    "voice": "none",
    "presence": "none",
    "affect_share": "ethics-notify",
    "memory_glimpse": "council-witness",
    "co_imagination": "council-witness",
    "merge_thought": "federation-council",
}
IMC_MODE_SHARE_TOPOLOGY = {
    "text": "summary-only",
    "voice": "streamed-audio",
    "presence": "shared-presence",
    "affect_share": "bidirectional",
    "memory_glimpse": "peer-readable",
    "co_imagination": "co-authored-scene",
    "merge_thought": "bidirectional",
}
IMC_MEMORY_GLIMPSE_RECEIPT_PROFILE = "council-witnessed-memory-glimpse-receipt-v1"
IMC_MEMORY_GLIMPSE_SOURCE_PROFILE = "digest-only-memory-crystal-source-v1"
IMC_MEMORY_GLIMPSE_WITNESS_PROFILE = "council-witness-before-peer-delivery-v1"
IMC_MEMORY_GLIMPSE_REQUIRED_WITNESS_ROLES = ["CouncilWitness", "GuardianLiaison"]


def _dedupe_preserve_order(values: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _memory_glimpse_receipt_digest_payload(receipt: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


class InterMindChannel:
    """Deterministic IMC reference model for bounded disclosure-safe sessions."""

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def reference_profile(self) -> Dict[str, Any]:
        return {
            "schema_version": IMC_SCHEMA_VERSION,
            "modes": sorted(IMC_ALLOWED_MODES),
            "forward_secrecy_required": True,
            "fail_closed": True,
            "ledger_payload_policy": "summary+digest-only",
            "mode_oversight": deepcopy(IMC_MODE_OVERSIGHT),
            "mode_share_topology": deepcopy(IMC_MODE_SHARE_TOPOLOGY),
            "disclosure_floor": "narrowest-side-wins",
            "sealed_fields_policy": "always-redact",
            "emergency_disconnect": {
                "self_authorized": True,
                "close_before_notice": True,
                "key_state_after_disconnect": "revoked",
            },
        }

    def open_session(
        self,
        *,
        initiator_id: str,
        peer_id: str,
        mode: str,
        initiator_template: Mapping[str, Sequence[str]],
        peer_template: Mapping[str, Sequence[str]],
        peer_attested: bool,
        forward_secrecy: bool,
        council_witnessed: bool = False,
    ) -> Dict[str, Any]:
        initiator = self._normalize_non_empty_string(initiator_id, "initiator_id")
        peer = self._normalize_non_empty_string(peer_id, "peer_id")
        if initiator == peer:
            raise ValueError("initiator_id and peer_id must differ")

        normalized_mode = self._normalize_mode(mode)
        if not peer_attested:
            raise PermissionError("peer attestation is required before opening IMC")
        if not forward_secrecy:
            raise PermissionError("forward secrecy is required before opening IMC")

        oversight = IMC_MODE_OVERSIGHT[normalized_mode]
        requires_council = oversight in {"council-witness", "federation-council"}
        if requires_council and not council_witnessed:
            raise PermissionError(f"{normalized_mode} requires council witness before opening IMC")

        session_id = new_id("imc")
        recorded_at = utc_now_iso()
        disclosure_profile = self._derive_disclosure_profile(
            mode=normalized_mode,
            initiator_template=initiator_template,
            peer_template=peer_template,
            council_witnessed=council_witnessed,
        )
        handshake = {
            "schema_version": IMC_SCHEMA_VERSION,
            "handshake_id": new_id("imc-hs"),
            "session_id": session_id,
            "verified_peer_id": peer,
            "recorded_at": recorded_at,
            "attestation_status": "verified",
            "forward_secrecy": True,
            "route_mode": normalized_mode,
            "council_witness_required": requires_council,
            "council_witnessed": council_witnessed,
            "disclosure_profile": disclosure_profile,
            "audit_event_ref": f"ledger://imc-handshake/{session_id}",
        }
        session = {
            "schema_version": IMC_SCHEMA_VERSION,
            "session_id": session_id,
            "opened_at": recorded_at,
            "updated_at": recorded_at,
            "participants": [initiator, peer],
            "mode": normalized_mode,
            "status": "open",
            "handshake": handshake,
            "message_summaries": [],
            "disconnect_policy": {
                "emergency_self_authorized": True,
                "close_before_notice": True,
                "council_notify_async": requires_council,
            },
            "key_state": "established",
            "closed_at": None,
            "disconnect_reason": "",
            "last_disconnect": None,
        }
        self.sessions[session_id] = session
        return deepcopy(session)

    def send(
        self,
        session_id: str,
        *,
        sender_id: str,
        summary: str,
        payload: Mapping[str, Any],
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        sender = self._normalize_non_empty_string(sender_id, "sender_id")
        summary_text = self._normalize_non_empty_string(summary, "summary")
        if session["status"] != "open":
            raise ValueError("cannot send on a closed IMC session")
        if sender not in session["participants"]:
            raise PermissionError("sender must be a participant in the IMC session")
        if not isinstance(payload, Mapping) or not payload:
            raise ValueError("payload must be a non-empty mapping")

        profile = session["handshake"]["disclosure_profile"]
        allowed_fields = set(profile["mode_allowed_fields"])
        sealed_fields = set(profile["sealed_fields"])
        delivered_fields = {
            key: value for key, value in payload.items() if key in allowed_fields and key not in sealed_fields
        }
        redacted_fields = sorted(key for key in payload if key not in delivered_fields)
        payload_digest = sha256_text(canonical_json(delivered_fields))
        recorded_at = utc_now_iso()
        message = {
            "schema_version": IMC_SCHEMA_VERSION,
            "message_id": new_id("imc-msg"),
            "session_id": session_id,
            "sender_id": sender,
            "recorded_at": recorded_at,
            "mode": session["mode"],
            "summary": summary_text,
            "delivered_fields": delivered_fields,
            "redacted_fields": redacted_fields,
            "payload_digest": payload_digest,
            "delivery_status": "delivered-with-redactions" if redacted_fields else "delivered",
            "continuity_event_ref": f"ledger://imc-message/{new_id('imc-audit')}",
        }
        session["updated_at"] = recorded_at
        session["message_summaries"].append(
            {
                "message_id": message["message_id"],
                "sender_id": sender,
                "recorded_at": recorded_at,
                "summary": summary_text,
                "payload_digest": payload_digest,
                "redacted_fields": redacted_fields,
            }
        )
        return deepcopy(message)

    def seal_memory_glimpse_receipt(
        self,
        session_id: str,
        *,
        message: Mapping[str, Any],
        source_manifest: Mapping[str, Any],
        selected_segment_ids: Sequence[str],
        council_session_ref: str,
        council_resolution_ref: str,
        guardian_attestation_ref: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["mode"] != "memory_glimpse":
            raise ValueError("memory glimpse receipt requires a memory_glimpse IMC session")
        handshake = session["handshake"]
        if (
            handshake.get("council_witness_required") is not True
            or handshake.get("council_witnessed") is not True
        ):
            raise PermissionError("memory glimpse receipt requires a witnessed Council session")
        if not isinstance(message, Mapping):
            raise ValueError("message must be a mapping")
        if message.get("session_id") != session_id or message.get("mode") != "memory_glimpse":
            raise ValueError("message must belong to the memory_glimpse IMC session")
        self._check_required_message_field(message, "message_id")
        self._check_required_message_field(message, "payload_digest")

        normalized_segments = self._select_memory_segments(source_manifest, selected_segment_ids)
        segment_ids = [segment["segment_id"] for segment in normalized_segments]
        segment_digests = [segment["digest"] for segment in normalized_segments]
        source_event_ids = _dedupe_preserve_order(
            event_id
            for segment in normalized_segments
            for event_id in segment.get("source_event_ids", [])
            if isinstance(event_id, str) and event_id.strip()
        )
        source_refs = _dedupe_preserve_order(
            source_ref
            for segment in normalized_segments
            for source_ref in segment.get("source_refs", [])
            if isinstance(source_ref, str) and source_ref.strip()
        )
        source_manifest_digest = sha256_text(canonical_json(source_manifest))
        redacted_fields = self._normalize_field_list(
            message.get("redacted_fields", []),
            "message.redacted_fields",
        )
        delivered_fields = message.get("delivered_fields", {})
        if not isinstance(delivered_fields, Mapping):
            raise ValueError("message.delivered_fields must be a mapping")
        sealed_fields = self._normalize_field_list(
            handshake["disclosure_profile"].get("sealed_fields", []),
            "handshake.disclosure_profile.sealed_fields",
        )
        delivered_field_names = sorted(delivered_fields)
        if any(field in delivered_field_names for field in sealed_fields):
            raise ValueError("memory glimpse receipt cannot bind delivered sealed fields")

        council_session = self._normalize_non_empty_string(
            council_session_ref,
            "council_session_ref",
        )
        council_resolution = self._normalize_non_empty_string(
            council_resolution_ref,
            "council_resolution_ref",
        )
        guardian_attestation = self._normalize_non_empty_string(
            guardian_attestation_ref,
            "guardian_attestation_ref",
        )
        witness_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": IMC_MEMORY_GLIMPSE_WITNESS_PROFILE,
                    "session_id": session_id,
                    "message_id": message["message_id"],
                    "source_manifest_digest": source_manifest_digest,
                    "selected_segment_ids": segment_ids,
                    "council_session_ref": council_session,
                    "council_resolution_ref": council_resolution,
                    "guardian_attestation_ref": guardian_attestation,
                }
            )
        )
        recorded_at = utc_now_iso()
        receipt = {
            "schema_version": IMC_SCHEMA_VERSION,
            "receipt_id": new_id("imc-memory-glimpse"),
            "profile_id": IMC_MEMORY_GLIMPSE_RECEIPT_PROFILE,
            "session_id": session_id,
            "handshake_id": handshake["handshake_id"],
            "message_id": message["message_id"],
            "route_mode": "memory_glimpse",
            "participants": list(session["participants"]),
            "issued_at": recorded_at,
            "memory_source": {
                "source_profile": IMC_MEMORY_GLIMPSE_SOURCE_PROFILE,
                "source_manifest_ref": f"memory://manifest/{source_manifest_digest[:16]}",
                "source_manifest_digest": source_manifest_digest,
                "source_identity_id": self._normalize_non_empty_string(
                    source_manifest.get("identity_id"),
                    "source_manifest.identity_id",
                ),
                "selected_segment_ids": segment_ids,
                "selected_segment_digests": segment_digests,
                "selected_source_event_ids": source_event_ids,
                "source_ref_set_digest": sha256_text(canonical_json(source_refs)),
                "segment_digest_set_digest": sha256_text(canonical_json(segment_digests)),
                "raw_memory_payload_stored": False,
            },
            "disclosure_binding": {
                "message_payload_digest": message["payload_digest"],
                "delivered_field_names": delivered_field_names,
                "redacted_fields": redacted_fields,
                "sealed_fields": sealed_fields,
                "delivered_field_count": len(delivered_field_names),
                "redacted_field_count": len(redacted_fields),
                "raw_memory_payload_stored": False,
                "raw_message_payload_stored": False,
                "summary_only_ledger": True,
            },
            "council_witness": {
                "profile_id": IMC_MEMORY_GLIMPSE_WITNESS_PROFILE,
                "witness_status": "witnessed",
                "council_session_ref": council_session,
                "council_resolution_ref": council_resolution,
                "guardian_attestation_ref": guardian_attestation,
                "required_roles": list(IMC_MEMORY_GLIMPSE_REQUIRED_WITNESS_ROLES),
                "accepted_roles": list(IMC_MEMORY_GLIMPSE_REQUIRED_WITNESS_ROLES),
                "witness_before_peer_delivery": True,
                "witness_digest": witness_digest,
            },
            "continuity_event_ref": f"ledger://imc-memory-glimpse/{session_id}",
            "status": "sealed",
        }
        receipt["digest"] = sha256_text(
            canonical_json(_memory_glimpse_receipt_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_memory_glimpse_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        errors: List[str] = []
        if receipt.get("schema_version") != IMC_SCHEMA_VERSION:
            errors.append(f"schema_version must be {IMC_SCHEMA_VERSION}")
        if receipt.get("profile_id") != IMC_MEMORY_GLIMPSE_RECEIPT_PROFILE:
            errors.append(f"profile_id must be {IMC_MEMORY_GLIMPSE_RECEIPT_PROFILE}")
        if receipt.get("route_mode") != "memory_glimpse":
            errors.append("route_mode must be memory_glimpse")
        if receipt.get("status") != "sealed":
            errors.append("status must be sealed")

        memory_source = receipt.get("memory_source")
        source_bound = False
        raw_memory_payload_stored = True
        if not isinstance(memory_source, Mapping):
            errors.append("memory_source must be an object")
        else:
            source_bound = (
                memory_source.get("source_profile") == IMC_MEMORY_GLIMPSE_SOURCE_PROFILE
                and isinstance(memory_source.get("source_manifest_digest"), str)
                and isinstance(memory_source.get("selected_segment_ids"), list)
                and len(memory_source.get("selected_segment_ids")) >= 1
                and isinstance(memory_source.get("selected_segment_digests"), list)
                and len(memory_source.get("selected_segment_digests")) >= 1
            )
            raw_memory_payload_stored = (
                memory_source.get("raw_memory_payload_stored") is not False
            )
            if not source_bound:
                errors.append("memory_source must bind manifest and selected segment digests")
            if raw_memory_payload_stored:
                errors.append("memory_source.raw_memory_payload_stored must be false")

        disclosure = receipt.get("disclosure_binding")
        disclosure_bound = False
        raw_message_payload_stored = True
        summary_only_ledger = False
        if not isinstance(disclosure, Mapping):
            errors.append("disclosure_binding must be an object")
        else:
            redacted_fields = disclosure.get("redacted_fields")
            sealed_fields = disclosure.get("sealed_fields")
            delivered_fields = disclosure.get("delivered_field_names")
            disclosure_bound = (
                isinstance(disclosure.get("message_payload_digest"), str)
                and isinstance(redacted_fields, list)
                and isinstance(sealed_fields, list)
                and isinstance(delivered_fields, list)
                and set(sealed_fields).isdisjoint(set(delivered_fields))
                and bool(set(sealed_fields).intersection(set(redacted_fields)))
            )
            raw_message_payload_stored = (
                disclosure.get("raw_message_payload_stored") is not False
            )
            summary_only_ledger = disclosure.get("summary_only_ledger") is True
            if not disclosure_bound:
                errors.append("disclosure_binding must bind digest-only redaction evidence")
            if raw_message_payload_stored:
                errors.append("disclosure_binding.raw_message_payload_stored must be false")
            if not summary_only_ledger:
                errors.append("disclosure_binding.summary_only_ledger must be true")

        witness = receipt.get("council_witness")
        witness_bound = False
        if not isinstance(witness, Mapping):
            errors.append("council_witness must be an object")
        else:
            witness_bound = (
                witness.get("profile_id") == IMC_MEMORY_GLIMPSE_WITNESS_PROFILE
                and witness.get("witness_status") == "witnessed"
                and witness.get("witness_before_peer_delivery") is True
                and witness.get("accepted_roles") == IMC_MEMORY_GLIMPSE_REQUIRED_WITNESS_ROLES
                and isinstance(witness.get("witness_digest"), str)
            )
            if not witness_bound:
                errors.append("council_witness must bind required roles before peer delivery")

        digest_bound = False
        digest = receipt.get("digest")
        if isinstance(digest, str):
            digest_bound = digest == sha256_text(
                canonical_json(_memory_glimpse_receipt_digest_payload(dict(receipt)))
            )
        if not digest_bound:
            errors.append("receipt digest must match canonical payload")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": receipt.get("profile_id"),
            "source_bound": source_bound,
            "disclosure_bound": disclosure_bound,
            "witness_bound": witness_bound,
            "digest_bound": digest_bound,
            "raw_memory_payload_stored": raw_memory_payload_stored,
            "raw_message_payload_stored": raw_message_payload_stored,
            "summary_only_ledger": summary_only_ledger,
        }

    def emergency_disconnect(
        self,
        session_id: str,
        *,
        requested_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        reason_text = self._normalize_non_empty_string(reason, "reason")
        if requester not in session["participants"]:
            raise PermissionError("requested_by must be a participant in the IMC session")
        if session["status"] != "open":
            raise ValueError("cannot disconnect an IMC session that is already closed")

        recorded_at = utc_now_iso()
        session["status"] = "closed"
        session["updated_at"] = recorded_at
        session["closed_at"] = recorded_at
        session["disconnect_reason"] = reason_text
        session["key_state"] = "revoked"
        outcome = {
            "session_id": session_id,
            "recorded_at": recorded_at,
            "requested_by": requester,
            "reason": reason_text,
            "status": "closed",
            "key_state": "revoked",
            "close_committed_before_notice": True,
            "council_notified_async": session["disconnect_policy"]["council_notify_async"],
            "audit_event_ref": f"ledger://imc-disconnect/{new_id('imc-disconnect')}",
        }
        session["last_disconnect"] = outcome
        return deepcopy(outcome)

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        return deepcopy(self._require_session(session_id))

    def validate_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(session, Mapping):
            raise ValueError("session must be a mapping")

        self._check_non_empty_string(session.get("session_id"), "session_id", errors)
        if session.get("schema_version") != IMC_SCHEMA_VERSION:
            errors.append(f"schema_version must be {IMC_SCHEMA_VERSION}")

        status = session.get("status")
        if status not in IMC_ALLOWED_STATUS:
            errors.append(f"status must be one of {sorted(IMC_ALLOWED_STATUS)}")

        participants = session.get("participants")
        if not isinstance(participants, list) or len(participants) != 2:
            errors.append("participants must contain exactly two identities")
        else:
            normalized = [participant for participant in participants if isinstance(participant, str) and participant.strip()]
            if len(normalized) != 2 or len(set(normalized)) != 2:
                errors.append("participants must contain two distinct non-empty identity ids")

        handshake = session.get("handshake")
        council_witness_enforced = False
        sealed_fields_protected = False
        disclosure_floor_applied = False
        if not isinstance(handshake, Mapping):
            errors.append("handshake must be an object")
        else:
            self._check_non_empty_string(handshake.get("handshake_id"), "handshake.handshake_id", errors)
            if handshake.get("attestation_status") != "verified":
                errors.append("handshake.attestation_status must be verified")
            if handshake.get("forward_secrecy") is not True:
                errors.append("handshake.forward_secrecy must be true")
            route_mode = handshake.get("route_mode")
            if route_mode not in IMC_ALLOWED_MODES:
                errors.append(f"handshake.route_mode must be one of {sorted(IMC_ALLOWED_MODES)}")
            council_required = handshake.get("council_witness_required") is True
            council_witnessed = handshake.get("council_witnessed") is True
            council_witness_enforced = not council_required or council_witnessed
            if council_required and not council_witnessed:
                errors.append("handshake.council_witness_required sessions must be witnessed")
            profile = handshake.get("disclosure_profile")
            if not isinstance(profile, Mapping):
                errors.append("handshake.disclosure_profile must be an object")
            else:
                public_fields = self._normalize_field_list(profile.get("public_fields"), "public_fields")
                intimate_fields = self._normalize_field_list(profile.get("intimate_fields"), "intimate_fields")
                sealed_fields = self._normalize_field_list(profile.get("sealed_fields"), "sealed_fields")
                mode_allowed_fields = self._normalize_field_list(
                    profile.get("mode_allowed_fields"),
                    "mode_allowed_fields",
                )
                sealed_fields_protected = not any(field in set(sealed_fields) for field in mode_allowed_fields)
                disclosure_floor_applied = set(mode_allowed_fields).issubset(set(public_fields) | set(intimate_fields))
                if not sealed_fields_protected:
                    errors.append("sealed_fields must never appear in mode_allowed_fields")
                if not disclosure_floor_applied:
                    errors.append("mode_allowed_fields must remain within the disclosure floor")

        message_summaries = session.get("message_summaries")
        if not isinstance(message_summaries, list):
            errors.append("message_summaries must be a list")
        else:
            for index, item in enumerate(message_summaries):
                if not isinstance(item, Mapping):
                    errors.append(f"message_summaries[{index}] must be an object")
                    continue
                delivered_fields = item.get("delivered_fields")
                if delivered_fields is not None:
                    errors.append(f"message_summaries[{index}] must not persist delivered_fields")

        emergency_disconnect_available = False
        emergency_disconnect_finalized = False
        disconnect_policy = session.get("disconnect_policy")
        if not isinstance(disconnect_policy, Mapping):
            errors.append("disconnect_policy must be an object")
        else:
            emergency_disconnect_available = disconnect_policy.get("emergency_self_authorized") is True
            if disconnect_policy.get("close_before_notice") is not True:
                errors.append("disconnect_policy.close_before_notice must be true")
            if not emergency_disconnect_available:
                errors.append("disconnect_policy.emergency_self_authorized must be true")

        if status == "closed":
            if session.get("key_state") != "revoked":
                errors.append("closed sessions must revoke transport keys")
            if not session.get("closed_at"):
                errors.append("closed sessions must record closed_at")
            emergency_disconnect_finalized = session.get("last_disconnect") is not None

        return {
            "ok": not errors,
            "errors": errors,
            "attestation_verified": isinstance(handshake, Mapping)
            and handshake.get("attestation_status") == "verified",
            "forward_secrecy_enforced": isinstance(handshake, Mapping)
            and handshake.get("forward_secrecy") is True,
            "council_witness_enforced": council_witness_enforced,
            "sealed_fields_protected": sealed_fields_protected,
            "disclosure_floor_applied": disclosure_floor_applied,
            "emergency_disconnect_available": emergency_disconnect_available,
            "emergency_disconnect_finalized": emergency_disconnect_finalized,
            "message_summary_count": len(message_summaries) if isinstance(message_summaries, list) else 0,
        }

    def _derive_disclosure_profile(
        self,
        *,
        mode: str,
        initiator_template: Mapping[str, Sequence[str]],
        peer_template: Mapping[str, Sequence[str]],
        council_witnessed: bool,
    ) -> Dict[str, Any]:
        initiator_public = self._normalize_field_list(
            initiator_template.get("public_fields"),
            "initiator.public_fields",
        )
        peer_public = self._normalize_field_list(peer_template.get("public_fields"), "peer.public_fields")
        initiator_intimate = self._normalize_field_list(
            initiator_template.get("intimate_fields"),
            "initiator.intimate_fields",
        )
        peer_intimate = self._normalize_field_list(
            peer_template.get("intimate_fields"),
            "peer.intimate_fields",
        )
        initiator_sealed = self._normalize_field_list(
            initiator_template.get("sealed_fields"),
            "initiator.sealed_fields",
        )
        peer_sealed = self._normalize_field_list(peer_template.get("sealed_fields"), "peer.sealed_fields")

        public_fields = [field for field in initiator_public if field in set(peer_public)]
        intimate_fields = [field for field in initiator_intimate if field in set(peer_intimate)]
        sealed_fields = _dedupe_preserve_order([*initiator_sealed, *peer_sealed])

        mode_allowed_fields: List[str] = []
        for field_class in IMC_MODE_FIELD_CLASSES[mode]:
            candidates = public_fields if field_class == "public_fields" else intimate_fields
            for field in candidates:
                if field not in sealed_fields and field not in mode_allowed_fields:
                    mode_allowed_fields.append(field)

        return {
            "public_fields": public_fields,
            "intimate_fields": intimate_fields,
            "sealed_fields": sealed_fields,
            "mode_allowed_fields": mode_allowed_fields,
            "share_topology": IMC_MODE_SHARE_TOPOLOGY[mode],
            "council_witness_required": IMC_MODE_OVERSIGHT[mode] in {"council-witness", "federation-council"},
            "council_witnessed": council_witnessed,
        }

    def _require_session(self, session_id: str) -> Dict[str, Any]:
        try:
            return self.sessions[session_id]
        except KeyError as exc:
            raise ValueError(f"unknown IMC session: {session_id}") from exc

    @staticmethod
    def _normalize_mode(mode: str) -> str:
        if mode not in IMC_ALLOWED_MODES:
            raise ValueError(f"mode must be one of {sorted(IMC_ALLOWED_MODES)}")
        return mode

    @staticmethod
    def _normalize_field_list(value: Any, field_name: str) -> List[str]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise ValueError(f"{field_name} must be a sequence of non-empty strings")
        normalized: List[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{field_name} must contain non-empty strings")
            normalized.append(item.strip())
        return _dedupe_preserve_order(normalized)

    @staticmethod
    def _normalize_non_empty_string(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _check_non_empty_string(value: Any, field_name: str, errors: List[str]) -> None:
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    def _select_memory_segments(
        self,
        source_manifest: Mapping[str, Any],
        selected_segment_ids: Sequence[str],
    ) -> List[Dict[str, Any]]:
        if not isinstance(source_manifest, Mapping):
            raise ValueError("source_manifest must be a mapping")
        if not isinstance(selected_segment_ids, Sequence) or isinstance(selected_segment_ids, (str, bytes)):
            raise ValueError("selected_segment_ids must be a sequence of strings")
        normalized_ids = self._normalize_field_list(selected_segment_ids, "selected_segment_ids")
        segments = source_manifest.get("segments")
        if not isinstance(segments, Sequence) or isinstance(segments, (str, bytes)):
            raise ValueError("source_manifest.segments must be a sequence")
        by_id: Dict[str, Dict[str, Any]] = {}
        for segment in segments:
            if not isinstance(segment, Mapping):
                continue
            segment_id = segment.get("segment_id")
            if isinstance(segment_id, str) and segment_id.strip():
                by_id[segment_id] = dict(segment)
        selected: List[Dict[str, Any]] = []
        for segment_id in normalized_ids:
            try:
                segment = by_id[segment_id]
            except KeyError as exc:
                raise ValueError(f"unknown source memory segment: {segment_id}") from exc
            self._normalize_non_empty_string(segment.get("digest"), f"segment[{segment_id}].digest")
            selected.append(segment)
        return selected

    @staticmethod
    def _check_required_message_field(message: Mapping[str, Any], field_name: str) -> None:
        if not isinstance(message.get(field_name), str) or not message.get(field_name, "").strip():
            raise ValueError(f"message.{field_name} must be a non-empty string")
