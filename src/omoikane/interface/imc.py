"""Inter-Mind Channel reference model."""

from __future__ import annotations

from copy import deepcopy
import json
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set
from urllib import error as urlerror
from urllib import request

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
IMC_MEMORY_GLIMPSE_RECONSENT_PROFILE = (
    "timeboxed-memory-glimpse-reconsent-receipt-v1"
)
IMC_MEMORY_GLIMPSE_RECONSENT_WINDOW_PROFILE = (
    "bounded-memory-glimpse-consent-window-v1"
)
IMC_MEMORY_GLIMPSE_RECONSENT_DIGEST_PROFILE = (
    "memory-glimpse-reconsent-digest-v1"
)
IMC_MEMORY_GLIMPSE_REVOCATION_PROFILE = (
    "participant-withdrawal-memory-glimpse-revocation-v1"
)
IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS = 86_400
IMC_MERGE_THOUGHT_ETHICS_RECEIPT_PROFILE = (
    "federation-council-merge-thought-ethics-gate-v1"
)
IMC_MERGE_THOUGHT_RISK_PROFILE = "identity-confusion-bounded-merge-thought-v1"
IMC_MERGE_THOUGHT_GATE_PROFILE = "federation-council-guardian-ethics-gate-v1"
IMC_MERGE_THOUGHT_COLLECTIVE_BINDING_PROFILE = (
    "distinct-collective-merge-thought-binding-v1"
)
IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS = 10
IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE = "merge-thought-window-policy-authority-v1"
IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF = (
    "policy-registry://imc/merge-thought-window/v1"
)
IMC_MERGE_THOUGHT_WINDOW_SIGNER_ROSTER_REF = (
    "signer-roster://imc/merge-thought-window/v1"
)
IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS = [
    "signer-key://imc-window-policy/jp-13-primary",
    "signer-key://imc-window-policy/us-ca-witness",
]
IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS = [
    "verifier://imc-window-policy/jp-13-live",
    "verifier://imc-window-policy/us-ca-live",
]
IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE = (
    "merge-thought-window-live-verifier-receipt-v1"
)
IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_DIGEST_PROFILE = (
    "merge-thought-window-live-verifier-digest-v1"
)
IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE = (
    "live-http-json-merge-thought-window-policy-v1"
)
IMC_MERGE_THOUGHT_WINDOW_LIVE_RESPONSE_SIGNATURE_PROFILE = (
    "digest-only-merge-thought-window-policy-response-signature-v1"
)
IMC_MERGE_THOUGHT_WINDOW_LIVE_LATENCY_BUDGET_MS = 250.0
IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES = [
    "FederationCouncil",
    "EthicsCommittee",
    "GuardianLiaison",
]


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


def _memory_glimpse_reconsent_receipt_digest_payload(
    receipt: Dict[str, Any],
) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _merge_thought_ethics_receipt_digest_payload(
    receipt: Dict[str, Any],
) -> Dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "digest"}


def _is_live_http_endpoint(endpoint_ref: str) -> bool:
    return endpoint_ref.startswith("http://") or endpoint_ref.startswith("https://")


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
            "memory_glimpse_reconsent": {
                "profile_id": IMC_MEMORY_GLIMPSE_RECONSENT_PROFILE,
                "max_window_seconds": IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS,
                "revocation_profile": IMC_MEMORY_GLIMPSE_REVOCATION_PROFILE,
                "raw_payload_policy": "digest-only",
            },
            "merge_thought_ethics_gate": {
                "profile_id": IMC_MERGE_THOUGHT_ETHICS_RECEIPT_PROFILE,
                "risk_profile": IMC_MERGE_THOUGHT_RISK_PROFILE,
                "gate_profile": IMC_MERGE_THOUGHT_GATE_PROFILE,
                "max_merge_window_seconds": IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
                "window_policy_profile": IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE,
                "window_policy_registry_ref": (
                    IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF
                ),
                "live_verifier_profile": (
                    IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE
                ),
                "live_verifier_transport_profile": (
                    IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE
                ),
                "required_roles": list(IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES),
                "raw_payload_policy": "digest-only",
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

    def seal_memory_glimpse_reconsent_receipt(
        self,
        session_id: str,
        *,
        memory_glimpse_receipt: Mapping[str, Any],
        requested_by: str,
        expires_after_seconds: int,
        revoke_after_event_ref: str,
        council_reconsent_ref: str,
        guardian_attestation_ref: str,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        requester = self._normalize_non_empty_string(requested_by, "requested_by")
        if requester not in session["participants"]:
            raise PermissionError("requested_by must be a participant in the IMC session")
        if not isinstance(memory_glimpse_receipt, Mapping):
            raise ValueError("memory_glimpse_receipt must be a mapping")
        if memory_glimpse_receipt.get("session_id") != session_id:
            raise ValueError("memory_glimpse_receipt must belong to the IMC session")
        if memory_glimpse_receipt.get("profile_id") != IMC_MEMORY_GLIMPSE_RECEIPT_PROFILE:
            raise ValueError("memory_glimpse_receipt must use the memory glimpse profile")
        if memory_glimpse_receipt.get("status") != "sealed":
            raise ValueError("memory_glimpse_receipt must be sealed before re-consent")
        source = memory_glimpse_receipt.get("memory_source")
        disclosure = memory_glimpse_receipt.get("disclosure_binding")
        witness = memory_glimpse_receipt.get("council_witness")
        if not isinstance(source, Mapping):
            raise ValueError("memory_glimpse_receipt.memory_source must be a mapping")
        if not isinstance(disclosure, Mapping):
            raise ValueError("memory_glimpse_receipt.disclosure_binding must be a mapping")
        if not isinstance(witness, Mapping):
            raise ValueError("memory_glimpse_receipt.council_witness must be a mapping")

        receipt_digest = self._normalize_non_empty_string(
            memory_glimpse_receipt.get("digest"),
            "memory_glimpse_receipt.digest",
        )
        receipt_id = self._normalize_non_empty_string(
            memory_glimpse_receipt.get("receipt_id"),
            "memory_glimpse_receipt.receipt_id",
        )
        selected_segment_ids = self._normalize_field_list(
            source.get("selected_segment_ids"),
            "memory_glimpse_receipt.memory_source.selected_segment_ids",
        )
        selected_segment_digests = self._normalize_field_list(
            source.get("selected_segment_digests"),
            "memory_glimpse_receipt.memory_source.selected_segment_digests",
        )
        selected_source_event_ids = self._normalize_field_list(
            source.get("selected_source_event_ids"),
            "memory_glimpse_receipt.memory_source.selected_source_event_ids",
        )
        window_seconds = self._normalize_reconsent_window(expires_after_seconds)
        revoke_event = self._normalize_non_empty_string(
            revoke_after_event_ref,
            "revoke_after_event_ref",
        )
        council_reconsent = self._normalize_non_empty_string(
            council_reconsent_ref,
            "council_reconsent_ref",
        )
        guardian_attestation = self._normalize_non_empty_string(
            guardian_attestation_ref,
            "guardian_attestation_ref",
        )
        recorded_at = utc_now_iso()
        reconsent_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": IMC_MEMORY_GLIMPSE_RECONSENT_DIGEST_PROFILE,
                    "session_id": session_id,
                    "memory_glimpse_receipt_digest": receipt_digest,
                    "source_manifest_digest": source.get("source_manifest_digest"),
                    "selected_segment_digests": selected_segment_digests,
                    "message_payload_digest": disclosure.get("message_payload_digest"),
                    "witness_digest": witness.get("witness_digest"),
                    "requested_by": requester,
                    "expires_after_seconds": window_seconds,
                    "revoke_after_event_ref": revoke_event,
                    "council_reconsent_ref": council_reconsent,
                    "guardian_attestation_ref": guardian_attestation,
                }
            )
        )
        receipt = {
            "schema_version": IMC_SCHEMA_VERSION,
            "receipt_id": new_id("imc-memory-glimpse-reconsent"),
            "profile_id": IMC_MEMORY_GLIMPSE_RECONSENT_PROFILE,
            "session_id": session_id,
            "memory_glimpse_receipt_id": receipt_id,
            "memory_glimpse_receipt_digest": receipt_digest,
            "message_id": memory_glimpse_receipt.get("message_id"),
            "participants": list(session["participants"]),
            "requested_by": requester,
            "issued_at": recorded_at,
            "session_status_at_issue": session["status"],
            "key_state_at_issue": session["key_state"],
            "consent_window": {
                "window_profile": IMC_MEMORY_GLIMPSE_RECONSENT_WINDOW_PROFILE,
                "issued_at": recorded_at,
                "expires_after_seconds": window_seconds,
                "expires_at_ref": f"issued_at+PT{window_seconds}S",
                "reconsent_required_before_redisclosure": True,
                "max_window_seconds": IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS,
            },
            "revocation_binding": {
                "revocation_profile": IMC_MEMORY_GLIMPSE_REVOCATION_PROFILE,
                "revoke_after_event_ref": revoke_event,
                "requester_is_participant": True,
                "emergency_disconnect_compatible": True,
                "key_revocation_required": True,
                "reconsent_required_after_revocation": True,
            },
            "reconsent_binding": {
                "digest_profile": IMC_MEMORY_GLIMPSE_RECONSENT_DIGEST_PROFILE,
                "council_reconsent_ref": council_reconsent,
                "guardian_attestation_ref": guardian_attestation,
                "source_manifest_digest": source.get("source_manifest_digest"),
                "selected_segment_ids": selected_segment_ids,
                "selected_segment_digests": selected_segment_digests,
                "selected_source_event_ids": selected_source_event_ids,
                "message_payload_digest": disclosure.get("message_payload_digest"),
                "witness_digest": witness.get("witness_digest"),
                "reconsent_digest": reconsent_digest,
            },
            "payload_policy": {
                "raw_memory_payload_stored": False,
                "raw_message_payload_stored": False,
                "raw_reconsent_payload_stored": False,
                "summary_only_ledger": True,
            },
            "continuity_event_ref": f"ledger://imc-memory-glimpse-reconsent/{session_id}",
            "status": (
                "revoked-pending-reconsent"
                if session["status"] == "closed"
                else "active-until-expiry"
            ),
        }
        receipt["digest"] = sha256_text(
            canonical_json(_memory_glimpse_reconsent_receipt_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_memory_glimpse_reconsent_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        errors: List[str] = []
        if receipt.get("schema_version") != IMC_SCHEMA_VERSION:
            errors.append(f"schema_version must be {IMC_SCHEMA_VERSION}")
        if receipt.get("profile_id") != IMC_MEMORY_GLIMPSE_RECONSENT_PROFILE:
            errors.append(f"profile_id must be {IMC_MEMORY_GLIMPSE_RECONSENT_PROFILE}")
        if receipt.get("status") not in {"active-until-expiry", "revoked-pending-reconsent"}:
            errors.append("status must be active-until-expiry or revoked-pending-reconsent")

        consent_window = receipt.get("consent_window")
        consent_window_bound = False
        if not isinstance(consent_window, Mapping):
            errors.append("consent_window must be an object")
        else:
            expires_after = consent_window.get("expires_after_seconds")
            consent_window_bound = (
                consent_window.get("window_profile")
                == IMC_MEMORY_GLIMPSE_RECONSENT_WINDOW_PROFILE
                and isinstance(expires_after, int)
                and 0 < expires_after <= IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS
                and consent_window.get("reconsent_required_before_redisclosure") is True
                and consent_window.get("max_window_seconds")
                == IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS
            )
            if not consent_window_bound:
                errors.append("consent_window must bind bounded timeboxed re-consent")

        revocation = receipt.get("revocation_binding")
        revocation_bound = False
        if not isinstance(revocation, Mapping):
            errors.append("revocation_binding must be an object")
        else:
            revocation_bound = (
                revocation.get("revocation_profile") == IMC_MEMORY_GLIMPSE_REVOCATION_PROFILE
                and isinstance(revocation.get("revoke_after_event_ref"), str)
                and revocation.get("requester_is_participant") is True
                and revocation.get("emergency_disconnect_compatible") is True
                and revocation.get("key_revocation_required") is True
                and revocation.get("reconsent_required_after_revocation") is True
            )
            if not revocation_bound:
                errors.append("revocation_binding must require participant withdrawal and re-consent")

        reconsent = receipt.get("reconsent_binding")
        reconsent_bound = False
        if not isinstance(reconsent, Mapping):
            errors.append("reconsent_binding must be an object")
        else:
            reconsent_bound = (
                reconsent.get("digest_profile") == IMC_MEMORY_GLIMPSE_RECONSENT_DIGEST_PROFILE
                and isinstance(reconsent.get("council_reconsent_ref"), str)
                and isinstance(reconsent.get("guardian_attestation_ref"), str)
                and isinstance(reconsent.get("source_manifest_digest"), str)
                and isinstance(reconsent.get("selected_segment_ids"), list)
                and len(reconsent.get("selected_segment_ids")) >= 1
                and isinstance(reconsent.get("selected_segment_digests"), list)
                and len(reconsent.get("selected_segment_digests")) >= 1
                and isinstance(reconsent.get("message_payload_digest"), str)
                and isinstance(reconsent.get("witness_digest"), str)
                and isinstance(reconsent.get("reconsent_digest"), str)
            )
            if not reconsent_bound:
                errors.append("reconsent_binding must bind Council, Guardian, source, and message digests")

        source_receipt_bound = (
            isinstance(receipt.get("memory_glimpse_receipt_id"), str)
            and isinstance(receipt.get("memory_glimpse_receipt_digest"), str)
            and isinstance(receipt.get("message_id"), str)
        )
        if not source_receipt_bound:
            errors.append("receipt must bind the source memory_glimpse receipt")

        payload_policy = receipt.get("payload_policy")
        raw_memory_payload_stored = True
        raw_message_payload_stored = True
        raw_reconsent_payload_stored = True
        summary_only_ledger = False
        if not isinstance(payload_policy, Mapping):
            errors.append("payload_policy must be an object")
        else:
            raw_memory_payload_stored = payload_policy.get("raw_memory_payload_stored") is not False
            raw_message_payload_stored = payload_policy.get("raw_message_payload_stored") is not False
            raw_reconsent_payload_stored = payload_policy.get("raw_reconsent_payload_stored") is not False
            summary_only_ledger = payload_policy.get("summary_only_ledger") is True
            if raw_memory_payload_stored:
                errors.append("payload_policy.raw_memory_payload_stored must be false")
            if raw_message_payload_stored:
                errors.append("payload_policy.raw_message_payload_stored must be false")
            if raw_reconsent_payload_stored:
                errors.append("payload_policy.raw_reconsent_payload_stored must be false")
            if not summary_only_ledger:
                errors.append("payload_policy.summary_only_ledger must be true")

        digest_bound = False
        digest = receipt.get("digest")
        if isinstance(digest, str):
            digest_bound = digest == sha256_text(
                canonical_json(
                    _memory_glimpse_reconsent_receipt_digest_payload(dict(receipt))
                )
            )
        if not digest_bound:
            errors.append("receipt digest must match canonical payload")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": receipt.get("profile_id"),
            "source_receipt_bound": source_receipt_bound,
            "consent_window_bound": consent_window_bound,
            "revocation_bound": revocation_bound,
            "reconsent_bound": reconsent_bound,
            "digest_bound": digest_bound,
            "raw_memory_payload_stored": raw_memory_payload_stored,
            "raw_message_payload_stored": raw_message_payload_stored,
            "raw_reconsent_payload_stored": raw_reconsent_payload_stored,
            "summary_only_ledger": summary_only_ledger,
        }

    def seal_merge_thought_ethics_receipt(
        self,
        session_id: str,
        *,
        message: Mapping[str, Any],
        collective_ref: str,
        council_session_ref: str,
        federation_council_ref: str,
        ethics_decision_ref: str,
        guardian_attestation_ref: str,
        requested_merge_window_seconds: int = IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
        window_policy_verifier_receipts: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        session = self._require_session(session_id)
        if session["mode"] != "merge_thought":
            raise ValueError("merge_thought ethics receipt requires a merge_thought IMC session")
        handshake = session["handshake"]
        if (
            handshake.get("council_witness_required") is not True
            or handshake.get("council_witnessed") is not True
        ):
            raise PermissionError("merge_thought ethics receipt requires witnessed Council session")
        if not isinstance(message, Mapping):
            raise ValueError("message must be a mapping")
        if message.get("session_id") != session_id or message.get("mode") != "merge_thought":
            raise ValueError("message must belong to the merge_thought IMC session")
        self._check_required_message_field(message, "message_id")
        self._check_required_message_field(message, "payload_digest")
        merge_window = self._normalize_merge_window(requested_merge_window_seconds)
        collective = self._normalize_non_empty_string(collective_ref, "collective_ref")
        council_session = self._normalize_non_empty_string(
            council_session_ref,
            "council_session_ref",
        )
        federation_council = self._normalize_non_empty_string(
            federation_council_ref,
            "federation_council_ref",
        )
        ethics_decision = self._normalize_non_empty_string(
            ethics_decision_ref,
            "ethics_decision_ref",
        )
        guardian_attestation = self._normalize_non_empty_string(
            guardian_attestation_ref,
            "guardian_attestation_ref",
        )
        delivered_fields = message.get("delivered_fields", {})
        if not isinstance(delivered_fields, Mapping):
            raise ValueError("message.delivered_fields must be a mapping")
        delivered_field_names = sorted(delivered_fields)
        redacted_fields = self._normalize_field_list(
            message.get("redacted_fields", []),
            "message.redacted_fields",
        )
        sealed_fields = self._normalize_field_list(
            handshake["disclosure_profile"].get("sealed_fields", []),
            "handshake.disclosure_profile.sealed_fields",
        )
        if any(field in delivered_field_names for field in sealed_fields):
            raise ValueError("merge_thought ethics receipt cannot bind delivered sealed fields")
        collective_binding_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": IMC_MERGE_THOUGHT_COLLECTIVE_BINDING_PROFILE,
                    "session_id": session_id,
                    "collective_ref": collective,
                    "participants": list(session["participants"]),
                    "merge_mode": "merge_thought",
                    "distinct_collective_required": True,
                }
            )
        )
        window_policy_authority = self._build_merge_thought_window_policy_authority(
            session_id=session_id,
            requested_merge_window_seconds=merge_window,
            live_verifier_receipts=window_policy_verifier_receipts,
        )
        gate_digest = sha256_text(
            canonical_json(
                {
                    "gate_profile": IMC_MERGE_THOUGHT_GATE_PROFILE,
                    "session_id": session_id,
                    "message_id": message["message_id"],
                    "collective_ref": collective,
                    "council_session_ref": council_session,
                    "federation_council_ref": federation_council,
                    "ethics_decision_ref": ethics_decision,
                    "guardian_attestation_ref": guardian_attestation,
                    "requested_merge_window_seconds": merge_window,
                    "window_policy_authority_digest": window_policy_authority[
                        "policy_authority_digest"
                    ],
                    "message_payload_digest": message["payload_digest"],
                    "collective_binding_digest": collective_binding_digest,
                }
            )
        )
        recorded_at = utc_now_iso()
        receipt = {
            "schema_version": IMC_SCHEMA_VERSION,
            "receipt_id": new_id("imc-merge-ethics"),
            "profile_id": IMC_MERGE_THOUGHT_ETHICS_RECEIPT_PROFILE,
            "session_id": session_id,
            "handshake_id": handshake["handshake_id"],
            "message_id": message["message_id"],
            "route_mode": "merge_thought",
            "participants": list(session["participants"]),
            "issued_at": recorded_at,
            "risk_boundary": {
                "risk_profile": IMC_MERGE_THOUGHT_RISK_PROFILE,
                "identity_confusion_risk": "high",
                "max_merge_window_seconds": IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
                "requested_merge_window_seconds": merge_window,
                "merge_window_policy_authority": window_policy_authority,
                "post_disconnect_identity_confirmation_required": True,
                "emergency_disconnect_required": True,
                "private_recovery_mode_required": True,
            },
            "collective_binding": {
                "binding_profile": IMC_MERGE_THOUGHT_COLLECTIVE_BINDING_PROFILE,
                "collective_ref": collective,
                "merge_mode": "merge_thought",
                "distinct_collective_required": True,
                "participants": list(session["participants"]),
                "collective_binding_digest": collective_binding_digest,
            },
            "disclosure_binding": {
                "message_payload_digest": message["payload_digest"],
                "delivered_field_names": delivered_field_names,
                "redacted_fields": redacted_fields,
                "sealed_fields": sealed_fields,
                "summary_only_ledger": True,
                "raw_thought_payload_stored": False,
                "raw_message_payload_stored": False,
            },
            "council_guardian_gate": {
                "gate_profile": IMC_MERGE_THOUGHT_GATE_PROFILE,
                "gate_status": "approved",
                "council_session_ref": council_session,
                "federation_council_ref": federation_council,
                "ethics_decision_ref": ethics_decision,
                "guardian_attestation_ref": guardian_attestation,
                "required_roles": list(IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES),
                "accepted_roles": list(IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES),
                "gate_before_collective_merge": True,
                "gate_digest": gate_digest,
            },
            "continuity_event_ref": f"ledger://imc-merge-thought-ethics/{session_id}",
            "status": "approved",
        }
        receipt["digest"] = sha256_text(
            canonical_json(_merge_thought_ethics_receipt_digest_payload(receipt))
        )
        return deepcopy(receipt)

    def validate_merge_thought_ethics_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")
        errors: List[str] = []
        if receipt.get("schema_version") != IMC_SCHEMA_VERSION:
            errors.append(f"schema_version must be {IMC_SCHEMA_VERSION}")
        if receipt.get("profile_id") != IMC_MERGE_THOUGHT_ETHICS_RECEIPT_PROFILE:
            errors.append(f"profile_id must be {IMC_MERGE_THOUGHT_ETHICS_RECEIPT_PROFILE}")
        if receipt.get("route_mode") != "merge_thought":
            errors.append("route_mode must be merge_thought")
        if receipt.get("status") != "approved":
            errors.append("status must be approved")

        risk = receipt.get("risk_boundary")
        risk_bound = False
        window_policy_authority_bound = False
        window_policy_live_verifier_bound = False
        raw_window_policy_payload_stored = True
        raw_window_policy_verifier_payload_stored = True
        raw_window_policy_response_signature_payload_stored = True
        if not isinstance(risk, Mapping):
            errors.append("risk_boundary must be an object")
        else:
            policy_authority = risk.get("merge_window_policy_authority")
            if not isinstance(policy_authority, Mapping):
                errors.append("risk_boundary.merge_window_policy_authority must be an object")
            elif isinstance(risk.get("requested_merge_window_seconds"), int):
                try:
                    expected_policy_authority = (
                        self._build_merge_thought_window_policy_authority(
                            session_id=str(receipt.get("session_id")),
                            requested_merge_window_seconds=risk[
                                "requested_merge_window_seconds"
                            ],
                            live_verifier_receipts=policy_authority.get(
                                "live_verifier_receipts",
                                [],
                            ),
                        )
                    )
                    window_policy_live_verifier_bound = bool(
                        expected_policy_authority.get("live_verifier_quorum_bound")
                    )
                    raw_window_policy_payload_stored = (
                        expected_policy_authority.get("raw_policy_payload_stored")
                        is not False
                    )
                    raw_window_policy_verifier_payload_stored = (
                        expected_policy_authority.get("raw_verifier_payload_stored")
                        is not False
                    )
                    raw_window_policy_response_signature_payload_stored = (
                        expected_policy_authority.get(
                            "raw_response_signature_payload_stored"
                        )
                        is not False
                    )
                    window_policy_authority_bound = (
                        dict(policy_authority) == expected_policy_authority
                        and policy_authority.get("max_merge_window_seconds")
                        == risk.get("max_merge_window_seconds")
                        and policy_authority.get("requested_merge_window_seconds")
                        == risk.get("requested_merge_window_seconds")
                        and policy_authority.get("policy_authority_status")
                        == "verified"
                        and policy_authority.get("raw_policy_payload_stored") is False
                        and policy_authority.get("raw_verifier_payload_stored") is False
                        and policy_authority.get(
                            "raw_response_signature_payload_stored"
                        )
                        is False
                        and window_policy_live_verifier_bound
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                if not window_policy_authority_bound:
                    errors.append(
                        "risk_boundary.merge_window_policy_authority must bind signed policy authority"
                    )
            risk_bound = (
                risk.get("risk_profile") == IMC_MERGE_THOUGHT_RISK_PROFILE
                and risk.get("identity_confusion_risk") == "high"
                and risk.get("max_merge_window_seconds")
                == IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS
                and isinstance(risk.get("requested_merge_window_seconds"), int)
                and 0
                < risk.get("requested_merge_window_seconds")
                <= IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS
                and window_policy_authority_bound
                and window_policy_live_verifier_bound
                and risk.get("post_disconnect_identity_confirmation_required") is True
                and risk.get("emergency_disconnect_required") is True
                and risk.get("private_recovery_mode_required") is True
            )
            if not risk_bound:
                errors.append("risk_boundary must bind bounded merge-thought recovery policy")

        collective = receipt.get("collective_binding")
        collective_bound = False
        if not isinstance(collective, Mapping):
            errors.append("collective_binding must be an object")
        else:
            collective_core = {
                "profile_id": IMC_MERGE_THOUGHT_COLLECTIVE_BINDING_PROFILE,
                "session_id": receipt.get("session_id"),
                "collective_ref": collective.get("collective_ref"),
                "participants": collective.get("participants"),
                "merge_mode": "merge_thought",
                "distinct_collective_required": True,
            }
            collective_bound = (
                collective.get("binding_profile")
                == IMC_MERGE_THOUGHT_COLLECTIVE_BINDING_PROFILE
                and collective.get("merge_mode") == "merge_thought"
                and collective.get("distinct_collective_required") is True
                and collective.get("participants") == receipt.get("participants")
                and isinstance(collective.get("collective_ref"), str)
                and collective.get("collective_binding_digest")
                == sha256_text(canonical_json(collective_core))
            )
            if not collective_bound:
                errors.append("collective_binding must bind a distinct collective merge target")

        disclosure = receipt.get("disclosure_binding")
        disclosure_bound = False
        raw_thought_payload_stored = True
        raw_message_payload_stored = True
        if not isinstance(disclosure, Mapping):
            errors.append("disclosure_binding must be an object")
        else:
            delivered_fields = disclosure.get("delivered_field_names")
            redacted_fields = disclosure.get("redacted_fields")
            sealed_fields = disclosure.get("sealed_fields")
            disclosure_bound = (
                isinstance(disclosure.get("message_payload_digest"), str)
                and isinstance(delivered_fields, list)
                and isinstance(redacted_fields, list)
                and isinstance(sealed_fields, list)
                and set(sealed_fields).isdisjoint(set(delivered_fields))
                and bool(set(sealed_fields).intersection(set(redacted_fields)))
                and disclosure.get("summary_only_ledger") is True
            )
            raw_thought_payload_stored = (
                disclosure.get("raw_thought_payload_stored") is not False
            )
            raw_message_payload_stored = (
                disclosure.get("raw_message_payload_stored") is not False
            )
            if not disclosure_bound:
                errors.append("disclosure_binding must bind digest-only redaction evidence")
            if raw_thought_payload_stored:
                errors.append("disclosure_binding.raw_thought_payload_stored must be false")
            if raw_message_payload_stored:
                errors.append("disclosure_binding.raw_message_payload_stored must be false")

        gate = receipt.get("council_guardian_gate")
        gate_bound = False
        if not isinstance(gate, Mapping):
            errors.append("council_guardian_gate must be an object")
        else:
            gate_core = {
                "gate_profile": IMC_MERGE_THOUGHT_GATE_PROFILE,
                "session_id": receipt.get("session_id"),
                "message_id": receipt.get("message_id"),
                "collective_ref": (
                    collective.get("collective_ref")
                    if isinstance(collective, Mapping)
                    else None
                ),
                "council_session_ref": gate.get("council_session_ref"),
                "federation_council_ref": gate.get("federation_council_ref"),
                "ethics_decision_ref": gate.get("ethics_decision_ref"),
                "guardian_attestation_ref": gate.get("guardian_attestation_ref"),
                "requested_merge_window_seconds": (
                    risk.get("requested_merge_window_seconds")
                    if isinstance(risk, Mapping)
                    else None
                ),
                "window_policy_authority_digest": (
                    risk.get("merge_window_policy_authority", {}).get(
                        "policy_authority_digest"
                    )
                    if isinstance(risk, Mapping)
                    and isinstance(risk.get("merge_window_policy_authority"), Mapping)
                    else None
                ),
                "message_payload_digest": (
                    disclosure.get("message_payload_digest")
                    if isinstance(disclosure, Mapping)
                    else None
                ),
                "collective_binding_digest": (
                    collective.get("collective_binding_digest")
                    if isinstance(collective, Mapping)
                    else None
                ),
            }
            gate_bound = (
                gate.get("gate_profile") == IMC_MERGE_THOUGHT_GATE_PROFILE
                and gate.get("gate_status") == "approved"
                and gate.get("accepted_roles") == IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES
                and gate.get("required_roles") == IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES
                and gate.get("gate_before_collective_merge") is True
                and gate.get("gate_digest") == sha256_text(canonical_json(gate_core))
            )
            if not gate_bound:
                errors.append("council_guardian_gate must bind Federation Council, Ethics, and Guardian approval")

        digest_bound = False
        digest = receipt.get("digest")
        if isinstance(digest, str):
            digest_bound = digest == sha256_text(
                canonical_json(_merge_thought_ethics_receipt_digest_payload(dict(receipt)))
            )
        if not digest_bound:
            errors.append("receipt digest must match canonical payload")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_id": receipt.get("profile_id"),
            "risk_bound": risk_bound,
            "window_policy_authority_bound": window_policy_authority_bound,
            "window_policy_live_verifier_bound": window_policy_live_verifier_bound,
            "collective_bound": collective_bound,
            "disclosure_bound": disclosure_bound,
            "gate_bound": gate_bound,
            "digest_bound": digest_bound,
            "raw_window_policy_payload_stored": raw_window_policy_payload_stored,
            "raw_window_policy_verifier_payload_stored": (
                raw_window_policy_verifier_payload_stored
            ),
            "raw_window_policy_response_signature_payload_stored": (
                raw_window_policy_response_signature_payload_stored
            ),
            "raw_thought_payload_stored": raw_thought_payload_stored,
            "raw_message_payload_stored": raw_message_payload_stored,
        }

    def build_merge_thought_window_policy_verifier_payload(
        self,
        *,
        verifier_ref: str,
        verifier_authority_ref: str,
        jurisdiction: str,
    ) -> Dict[str, Any]:
        normalized_verifier_ref = self._normalize_non_empty_string(
            verifier_ref,
            "verifier_ref",
        )
        normalized_authority_ref = self._normalize_non_empty_string(
            verifier_authority_ref,
            "verifier_authority_ref",
        )
        normalized_jurisdiction = self._normalize_non_empty_string(
            jurisdiction,
            "jurisdiction",
        )
        policy_material = self._merge_thought_window_policy_material()
        response_signature_digest = (
            self._merge_thought_window_live_response_signature_digest(
                verifier_ref=normalized_verifier_ref,
                verifier_authority_ref=normalized_authority_ref,
                jurisdiction=normalized_jurisdiction,
                policy_registry_digest=policy_material["policy_registry_digest"],
                policy_body_digest=policy_material["policy_body_digest"],
                policy_signature_digest=policy_material["policy_signature_digest"],
                signer_roster_digest=policy_material["signer_roster_digest"],
                max_merge_window_seconds=IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            )
        )
        return {
            "policy_profile": IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE,
            "policy_registry_ref": IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF,
            "policy_registry_digest": policy_material["policy_registry_digest"],
            "policy_body_digest": policy_material["policy_body_digest"],
            "policy_signature_digest": policy_material["policy_signature_digest"],
            "signer_roster_ref": IMC_MERGE_THOUGHT_WINDOW_SIGNER_ROSTER_REF,
            "signer_roster_digest": policy_material["signer_roster_digest"],
            "signer_key_refs": list(IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS),
            "max_merge_window_seconds": IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            "verifier_ref": normalized_verifier_ref,
            "verifier_authority_ref": normalized_authority_ref,
            "jurisdiction": normalized_jurisdiction,
            "response_status": "verified",
            "response_signature_profile": (
                IMC_MERGE_THOUGHT_WINDOW_LIVE_RESPONSE_SIGNATURE_PROFILE
            ),
            "response_signature_digest": response_signature_digest,
            "raw_policy_payload_stored": False,
            "raw_verifier_payload_stored": False,
            "raw_response_signature_payload_stored": False,
        }

    def probe_merge_thought_window_policy_verifier_endpoint(
        self,
        *,
        verifier_endpoint: str,
        verifier_ref: str,
        verifier_authority_ref: str,
        jurisdiction: str,
        timeout_ms: int = 1000,
    ) -> Dict[str, Any]:
        normalized_endpoint = self._normalize_non_empty_string(
            verifier_endpoint,
            "verifier_endpoint",
        )
        if not _is_live_http_endpoint(normalized_endpoint):
            raise ValueError("verifier_endpoint must be http:// or https://")
        if timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")

        request_started = time.monotonic()
        try:
            with request.urlopen(  # noqa: S310 - bounded reference verifier probe
                normalized_endpoint,
                timeout=timeout_ms / 1000.0,
            ) as response:
                http_status = int(getattr(response, "status", response.getcode()))
                raw_body = response.read()
        except (OSError, urlerror.URLError) as exc:
            raise ValueError(
                f"merge_thought window policy verifier endpoint unreachable: {normalized_endpoint}"
            ) from exc
        observed_latency_ms = round((time.monotonic() - request_started) * 1000.0, 3)
        if http_status != 200:
            raise ValueError(
                "merge_thought window policy verifier endpoint returned "
                f"unexpected status {http_status}"
            )
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                "merge_thought window policy verifier endpoint must return JSON"
            ) from exc
        if not isinstance(payload, Mapping):
            raise ValueError(
                "merge_thought window policy verifier endpoint payload must be an object"
            )

        expected_payload = self.build_merge_thought_window_policy_verifier_payload(
            verifier_ref=verifier_ref,
            verifier_authority_ref=verifier_authority_ref,
            jurisdiction=jurisdiction,
        )
        for field_name, expected_value in expected_payload.items():
            if payload.get(field_name) != expected_value:
                raise ValueError(
                    "merge_thought window policy verifier endpoint field mismatch: "
                    f"{field_name}"
                )

        network_response_digest = sha256_text(canonical_json(dict(payload)))
        response_digest = self._merge_thought_window_live_response_digest(
            verifier_ref=expected_payload["verifier_ref"],
            verifier_endpoint_ref=normalized_endpoint,
            verifier_authority_ref=expected_payload["verifier_authority_ref"],
            jurisdiction=expected_payload["jurisdiction"],
            policy_registry_digest=expected_payload["policy_registry_digest"],
            policy_body_digest=expected_payload["policy_body_digest"],
            policy_signature_digest=expected_payload["policy_signature_digest"],
            signer_roster_digest=expected_payload["signer_roster_digest"],
            max_merge_window_seconds=expected_payload["max_merge_window_seconds"],
            network_response_digest=network_response_digest,
            response_signature_digest=expected_payload["response_signature_digest"],
        )
        receipt = {
            "schema_version": IMC_SCHEMA_VERSION,
            "receipt_id": new_id("imc-window-verifier"),
            "profile_id": IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE,
            "digest_profile": IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_DIGEST_PROFILE,
            "transport_profile": IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE,
            "verifier_ref": expected_payload["verifier_ref"],
            "verifier_endpoint_ref": normalized_endpoint,
            "verifier_authority_ref": expected_payload["verifier_authority_ref"],
            "jurisdiction": expected_payload["jurisdiction"],
            "policy_profile": expected_payload["policy_profile"],
            "policy_registry_ref": expected_payload["policy_registry_ref"],
            "policy_registry_digest": expected_payload["policy_registry_digest"],
            "policy_body_digest": expected_payload["policy_body_digest"],
            "policy_signature_digest": expected_payload["policy_signature_digest"],
            "signer_roster_ref": expected_payload["signer_roster_ref"],
            "signer_roster_digest": expected_payload["signer_roster_digest"],
            "signer_key_refs": list(expected_payload["signer_key_refs"]),
            "max_merge_window_seconds": expected_payload["max_merge_window_seconds"],
            "http_status": http_status,
            "request_timeout_ms": timeout_ms,
            "observed_latency_ms": observed_latency_ms,
            "latency_budget_ms": IMC_MERGE_THOUGHT_WINDOW_LIVE_LATENCY_BUDGET_MS,
            "network_response_digest": network_response_digest,
            "network_probe_status": "verified",
            "network_probe_bound": True,
            "response_status": expected_payload["response_status"],
            "response_signature_profile": expected_payload[
                "response_signature_profile"
            ],
            "response_signature_digest": expected_payload[
                "response_signature_digest"
            ],
            "response_digest": response_digest,
            "policy_payload_bound": True,
            "signed_response_bound": True,
            "raw_policy_payload_stored": False,
            "raw_verifier_payload_stored": False,
            "raw_response_signature_payload_stored": False,
        }
        receipt["digest"] = sha256_text(canonical_json(receipt))
        return receipt

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

    @staticmethod
    def _normalize_reconsent_window(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("expires_after_seconds must be an integer")
        if value <= 0 or value > IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS:
            raise ValueError(
                "expires_after_seconds must be between 1 and "
                f"{IMC_MEMORY_GLIMPSE_MAX_RECONSENT_WINDOW_SECONDS}"
            )
        return value

    @staticmethod
    def _normalize_merge_window(value: Any) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("requested_merge_window_seconds must be an integer")
        if value <= 0 or value > IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS:
            raise ValueError(
                "requested_merge_window_seconds must be between 1 and "
                f"{IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS}"
            )
        return value

    def _build_merge_thought_window_policy_authority(
        self,
        *,
        session_id: str,
        requested_merge_window_seconds: int,
        live_verifier_receipts: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> Dict[str, Any]:
        normalized_receipts = (
            self._normalize_merge_thought_window_policy_live_verifier_receipts(
                live_verifier_receipts or []
            )
        )
        policy_material = self._merge_thought_window_policy_material()
        verifier_response_digests = [
            str(receipt["response_digest"]) for receipt in normalized_receipts
        ]
        live_verifier_receipt_digests = [
            str(receipt["digest"]) for receipt in normalized_receipts
        ]
        live_verifier_network_response_digests = [
            str(receipt["network_response_digest"]) for receipt in normalized_receipts
        ]
        live_verifier_response_signature_digests = [
            str(receipt["response_signature_digest"]) for receipt in normalized_receipts
        ]
        live_verifier_jurisdictions = [
            str(receipt["jurisdiction"]) for receipt in normalized_receipts
        ]
        live_verifier_authority_refs = [
            str(receipt["verifier_authority_ref"]) for receipt in normalized_receipts
        ]
        live_verifier_quorum_bound = bool(
            len(normalized_receipts) >= 2
            and len(set(receipt["verifier_ref"] for receipt in normalized_receipts))
            == len(normalized_receipts)
            and set(receipt["verifier_ref"] for receipt in normalized_receipts)
            == set(IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS)
            and len(set(live_verifier_jurisdictions)) == len(normalized_receipts)
        )
        live_verifier_quorum_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE,
                    "verifier_refs": [
                        str(receipt["verifier_ref"]) for receipt in normalized_receipts
                    ],
                    "verifier_authority_refs": live_verifier_authority_refs,
                    "jurisdictions": live_verifier_jurisdictions,
                    "receipt_digests": live_verifier_receipt_digests,
                    "network_response_digests": live_verifier_network_response_digests,
                    "response_signature_digests": (
                        live_verifier_response_signature_digests
                    ),
                    "required_verifier_count": len(
                        IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS
                    ),
                    "max_merge_window_seconds": (
                        IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS
                    ),
                }
            )
        )
        verifier_quorum_digest = sha256_text(
            canonical_json(
                {
                    "verifier_refs": [
                        str(receipt["verifier_ref"]) for receipt in normalized_receipts
                    ],
                    "verifier_response_digests": verifier_response_digests,
                    "live_verifier_receipt_digests": live_verifier_receipt_digests,
                    "live_verifier_quorum_digest": live_verifier_quorum_digest,
                    "required_verifier_count": len(
                        IMC_MERGE_THOUGHT_WINDOW_POLICY_VERIFIER_REFS
                    ),
                }
            )
        )
        authority_core = {
            "policy_profile": IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE,
            "session_id": session_id,
            "policy_registry_ref": IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF,
            "policy_registry_digest": policy_material["policy_registry_digest"],
            "policy_body_digest": policy_material["policy_body_digest"],
            "policy_signature_digest": policy_material["policy_signature_digest"],
            "signer_roster_ref": IMC_MERGE_THOUGHT_WINDOW_SIGNER_ROSTER_REF,
            "signer_roster_digest": policy_material["signer_roster_digest"],
            "signer_key_refs": list(IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS),
            "verifier_refs": [
                str(receipt["verifier_ref"]) for receipt in normalized_receipts
            ],
            "verifier_response_digests": verifier_response_digests,
            "verifier_quorum_digest": verifier_quorum_digest,
            "live_verifier_profile": IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE,
            "live_verifier_transport_profile": (
                IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE
            ),
            "live_verifier_receipts": normalized_receipts,
            "live_verifier_receipt_digests": live_verifier_receipt_digests,
            "live_verifier_network_response_digests": (
                live_verifier_network_response_digests
            ),
            "live_verifier_response_signature_digests": (
                live_verifier_response_signature_digests
            ),
            "live_verifier_authority_refs": live_verifier_authority_refs,
            "live_verifier_jurisdictions": live_verifier_jurisdictions,
            "live_verifier_quorum_digest": live_verifier_quorum_digest,
            "live_verifier_quorum_bound": live_verifier_quorum_bound,
            "max_merge_window_seconds": IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            "requested_merge_window_seconds": requested_merge_window_seconds,
            "policy_authority_status": "verified",
            "raw_policy_payload_stored": False,
            "raw_verifier_payload_stored": False,
            "raw_response_signature_payload_stored": False,
        }
        return {
            **authority_core,
            "policy_authority_digest": sha256_text(canonical_json(authority_core)),
        }

    @staticmethod
    def _merge_thought_window_policy_material() -> Dict[str, Any]:
        policy_body = {
            "policy_profile": IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE,
            "policy_registry_ref": IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF,
            "risk_profile": IMC_MERGE_THOUGHT_RISK_PROFILE,
            "max_merge_window_seconds": IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            "required_gate_roles": list(IMC_MERGE_THOUGHT_REQUIRED_GATE_ROLES),
        }
        policy_registry_digest = sha256_text(canonical_json(policy_body))
        policy_body_digest = sha256_text(canonical_json(policy_body))
        signer_roster = {
            "signer_roster_ref": IMC_MERGE_THOUGHT_WINDOW_SIGNER_ROSTER_REF,
            "signer_key_refs": list(IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS),
            "policy_registry_digest": policy_registry_digest,
        }
        signer_roster_digest = sha256_text(canonical_json(signer_roster))
        policy_signature_digest = sha256_text(
            canonical_json(
                {
                    "policy_body_digest": policy_body_digest,
                    "signer_roster_digest": signer_roster_digest,
                    "signer_key_refs": list(IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS),
                }
            )
        )
        return {
            "policy_body": policy_body,
            "policy_registry_digest": policy_registry_digest,
            "policy_body_digest": policy_body_digest,
            "signer_roster_digest": signer_roster_digest,
            "policy_signature_digest": policy_signature_digest,
        }

    def _normalize_merge_thought_window_policy_live_verifier_receipts(
        self,
        receipts: Sequence[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes)):
            raise ValueError("live_verifier_receipts must be a sequence")
        if len(receipts) < 2:
            raise ValueError("live_verifier_receipts must include at least two receipts")
        normalized: List[Dict[str, Any]] = []
        for index, receipt in enumerate(receipts):
            if not isinstance(receipt, Mapping):
                raise ValueError(f"live_verifier_receipts[{index}] must be an object")
            normalized_receipt = dict(receipt)
            self._validate_merge_thought_window_policy_live_verifier_receipt(
                normalized_receipt,
                field_name=f"live_verifier_receipts[{index}]",
            )
            normalized.append(normalized_receipt)
        return normalized

    def _validate_merge_thought_window_policy_live_verifier_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        field_name: str,
    ) -> None:
        policy_material = self._merge_thought_window_policy_material()
        required_fields = [
            "schema_version",
            "receipt_id",
            "profile_id",
            "digest_profile",
            "transport_profile",
            "verifier_ref",
            "verifier_endpoint_ref",
            "verifier_authority_ref",
            "jurisdiction",
            "policy_profile",
            "policy_registry_ref",
            "policy_registry_digest",
            "policy_body_digest",
            "policy_signature_digest",
            "signer_roster_ref",
            "signer_roster_digest",
            "signer_key_refs",
            "max_merge_window_seconds",
            "http_status",
            "observed_latency_ms",
            "latency_budget_ms",
            "network_response_digest",
            "network_probe_status",
            "network_probe_bound",
            "response_status",
            "response_signature_profile",
            "response_signature_digest",
            "response_digest",
            "policy_payload_bound",
            "signed_response_bound",
            "raw_policy_payload_stored",
            "raw_verifier_payload_stored",
            "raw_response_signature_payload_stored",
            "digest",
        ]
        missing = [key for key in required_fields if key not in receipt]
        if missing:
            raise ValueError(f"{field_name} missing fields: {missing}")
        if receipt.get("schema_version") != IMC_SCHEMA_VERSION:
            raise ValueError(f"{field_name}.schema_version mismatch")
        if receipt.get("profile_id") != IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE:
            raise ValueError(f"{field_name}.profile_id mismatch")
        if (
            receipt.get("digest_profile")
            != IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_DIGEST_PROFILE
        ):
            raise ValueError(f"{field_name}.digest_profile mismatch")
        if (
            receipt.get("transport_profile")
            != IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE
        ):
            raise ValueError(f"{field_name}.transport_profile mismatch")
        endpoint_ref = self._normalize_non_empty_string(
            receipt.get("verifier_endpoint_ref"),
            f"{field_name}.verifier_endpoint_ref",
        )
        if not _is_live_http_endpoint(endpoint_ref):
            raise ValueError(f"{field_name}.verifier_endpoint_ref must be http(s)")
        if receipt.get("policy_profile") != IMC_MERGE_THOUGHT_WINDOW_POLICY_PROFILE:
            raise ValueError(f"{field_name}.policy_profile mismatch")
        if (
            receipt.get("policy_registry_ref")
            != IMC_MERGE_THOUGHT_WINDOW_POLICY_REGISTRY_REF
        ):
            raise ValueError(f"{field_name}.policy_registry_ref mismatch")
        for digest_field in (
            "policy_registry_digest",
            "policy_body_digest",
            "policy_signature_digest",
            "signer_roster_digest",
        ):
            if receipt.get(digest_field) != policy_material[digest_field]:
                raise ValueError(f"{field_name}.{digest_field} mismatch")
        if receipt.get("signer_roster_ref") != IMC_MERGE_THOUGHT_WINDOW_SIGNER_ROSTER_REF:
            raise ValueError(f"{field_name}.signer_roster_ref mismatch")
        if receipt.get("signer_key_refs") != IMC_MERGE_THOUGHT_WINDOW_SIGNER_KEY_REFS:
            raise ValueError(f"{field_name}.signer_key_refs mismatch")
        if receipt.get("max_merge_window_seconds") != IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS:
            raise ValueError(f"{field_name}.max_merge_window_seconds mismatch")
        if receipt.get("http_status") != 200:
            raise ValueError(f"{field_name}.http_status must be 200")
        try:
            observed_latency_ms = float(receipt.get("observed_latency_ms"))
            latency_budget_ms = float(receipt.get("latency_budget_ms"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name}.latency fields must be numeric") from exc
        if latency_budget_ms != IMC_MERGE_THOUGHT_WINDOW_LIVE_LATENCY_BUDGET_MS:
            raise ValueError(f"{field_name}.latency_budget_ms mismatch")
        if observed_latency_ms < 0 or observed_latency_ms > latency_budget_ms:
            raise ValueError(f"{field_name}.observed_latency_ms exceeds budget")
        if not isinstance(receipt.get("network_response_digest"), str) or len(
            str(receipt.get("network_response_digest"))
        ) != 64:
            raise ValueError(f"{field_name}.network_response_digest must be sha256")
        if receipt.get("network_probe_status") != "verified":
            raise ValueError(f"{field_name}.network_probe_status mismatch")
        if receipt.get("network_probe_bound") is not True:
            raise ValueError(f"{field_name}.network_probe_bound must be true")
        if receipt.get("response_status") != "verified":
            raise ValueError(f"{field_name}.response_status mismatch")
        if (
            receipt.get("response_signature_profile")
            != IMC_MERGE_THOUGHT_WINDOW_LIVE_RESPONSE_SIGNATURE_PROFILE
        ):
            raise ValueError(f"{field_name}.response_signature_profile mismatch")
        expected_response_signature_digest = (
            self._merge_thought_window_live_response_signature_digest(
                verifier_ref=str(receipt.get("verifier_ref")),
                verifier_authority_ref=str(receipt.get("verifier_authority_ref")),
                jurisdiction=str(receipt.get("jurisdiction")),
                policy_registry_digest=policy_material["policy_registry_digest"],
                policy_body_digest=policy_material["policy_body_digest"],
                policy_signature_digest=policy_material["policy_signature_digest"],
                signer_roster_digest=policy_material["signer_roster_digest"],
                max_merge_window_seconds=IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            )
        )
        if receipt.get("response_signature_digest") != expected_response_signature_digest:
            raise ValueError(f"{field_name}.response_signature_digest mismatch")
        expected_response_digest = self._merge_thought_window_live_response_digest(
            verifier_ref=str(receipt.get("verifier_ref")),
            verifier_endpoint_ref=endpoint_ref,
            verifier_authority_ref=str(receipt.get("verifier_authority_ref")),
            jurisdiction=str(receipt.get("jurisdiction")),
            policy_registry_digest=policy_material["policy_registry_digest"],
            policy_body_digest=policy_material["policy_body_digest"],
            policy_signature_digest=policy_material["policy_signature_digest"],
            signer_roster_digest=policy_material["signer_roster_digest"],
            max_merge_window_seconds=IMC_MERGE_THOUGHT_MAX_WINDOW_SECONDS,
            network_response_digest=str(receipt.get("network_response_digest")),
            response_signature_digest=expected_response_signature_digest,
        )
        if receipt.get("response_digest") != expected_response_digest:
            raise ValueError(f"{field_name}.response_digest mismatch")
        if receipt.get("policy_payload_bound") is not True:
            raise ValueError(f"{field_name}.policy_payload_bound must be true")
        if receipt.get("signed_response_bound") is not True:
            raise ValueError(f"{field_name}.signed_response_bound must be true")
        if receipt.get("raw_policy_payload_stored") is not False:
            raise ValueError(f"{field_name}.raw_policy_payload_stored must be false")
        if receipt.get("raw_verifier_payload_stored") is not False:
            raise ValueError(f"{field_name}.raw_verifier_payload_stored must be false")
        if receipt.get("raw_response_signature_payload_stored") is not False:
            raise ValueError(
                f"{field_name}.raw_response_signature_payload_stored must be false"
            )
        receipt_without_digest = {
            key: value for key, value in dict(receipt).items() if key != "digest"
        }
        if receipt.get("digest") != sha256_text(canonical_json(receipt_without_digest)):
            raise ValueError(f"{field_name}.digest mismatch")

    @staticmethod
    def _merge_thought_window_live_response_signature_digest(
        *,
        verifier_ref: str,
        verifier_authority_ref: str,
        jurisdiction: str,
        policy_registry_digest: str,
        policy_body_digest: str,
        policy_signature_digest: str,
        signer_roster_digest: str,
        max_merge_window_seconds: int,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "response_signature_profile": (
                        IMC_MERGE_THOUGHT_WINDOW_LIVE_RESPONSE_SIGNATURE_PROFILE
                    ),
                    "verifier_ref": verifier_ref,
                    "verifier_authority_ref": verifier_authority_ref,
                    "jurisdiction": jurisdiction,
                    "policy_registry_digest": policy_registry_digest,
                    "policy_body_digest": policy_body_digest,
                    "policy_signature_digest": policy_signature_digest,
                    "signer_roster_digest": signer_roster_digest,
                    "max_merge_window_seconds": max_merge_window_seconds,
                }
            )
        )

    @staticmethod
    def _merge_thought_window_live_response_digest(
        *,
        verifier_ref: str,
        verifier_endpoint_ref: str,
        verifier_authority_ref: str,
        jurisdiction: str,
        policy_registry_digest: str,
        policy_body_digest: str,
        policy_signature_digest: str,
        signer_roster_digest: str,
        max_merge_window_seconds: int,
        network_response_digest: str,
        response_signature_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": IMC_MERGE_THOUGHT_WINDOW_LIVE_VERIFIER_PROFILE,
                    "transport_profile": (
                        IMC_MERGE_THOUGHT_WINDOW_LIVE_TRANSPORT_PROFILE
                    ),
                    "verifier_ref": verifier_ref,
                    "verifier_endpoint_ref": verifier_endpoint_ref,
                    "verifier_authority_ref": verifier_authority_ref,
                    "jurisdiction": jurisdiction,
                    "policy_registry_digest": policy_registry_digest,
                    "policy_body_digest": policy_body_digest,
                    "policy_signature_digest": policy_signature_digest,
                    "signer_roster_digest": signer_roster_digest,
                    "max_merge_window_seconds": max_merge_window_seconds,
                    "network_response_digest": network_response_digest,
                    "response_signature_digest": response_signature_digest,
                }
            )
        )

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
