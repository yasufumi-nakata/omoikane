"""Bounded collective identity and merge-thought reference model."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Sequence, Set

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

COLLECTIVE_SCHEMA_VERSION = "1.0"
COLLECTIVE_MIN_MEMBERS = 2
COLLECTIVE_MAX_MEMBERS = 4
COLLECTIVE_MAX_DURATION_SECONDS = 10.0
COLLECTIVE_ALLOWED_STATUSES = {"active", "recovery", "dissolved"}
COLLECTIVE_ALLOWED_MERGE_STATUSES = {"open", "completed", "recovery-required"}
COLLECTIVE_ALLOWED_WMS_MODES = {"shared_reality", "private_reality", "mixed"}
COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID = (
    "collective-dissolution-identity-confirmation-binding-v1"
)
COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID = (
    "collective-dissolution-recovery-verifier-transport-v1"
)
COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID = "multidimensional-identity-confirmation-v1"
COLLECTIVE_IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID = (
    "identity-self-report-witness-consistency-v1"
)
COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID = "guardian-reviewer-remote-attestation-v1"
COLLECTIVE_VERIFIER_TRANSPORT_PROFILE = "reviewer-live-proof-bridge-v1"
COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID = (
    "digest-bound-reviewer-transport-exchange-v1"
)
COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS = ["JP-13", "US-CA", "EU-DE", "SG-01"]
COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS = [
    "episodic_recall",
    "self_model_alignment",
    "subjective_self_report",
    "third_party_witness_alignment",
]


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
                "member_recovery_binding_profile": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                "identity_confirmation_profile": COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID,
                "member_recovery_verifier_transport_profile": (
                    COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
                ),
                "raw_identity_confirmation_profiles_stored": False,
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
        identity_confirmation_profiles: Mapping[str, Mapping[str, Any]],
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
        recovery_proofs = self._derive_member_recovery_proofs(
            identity_confirmation_profiles,
            record["member_ids"],
        )
        recovery_digest_set = [
            proof["identity_confirmation_digest"] for proof in recovery_proofs.values()
        ]

        dissolved_at = utc_now_iso()
        recovery_binding_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                    "collective_id": record["collective_id"],
                    "member_ids": record["member_ids"],
                    "member_recovery_proofs": recovery_proofs,
                    "member_recovery_confirmation_digest_set": recovery_digest_set,
                }
            )
        )
        receipt = {
            "schema_version": COLLECTIVE_SCHEMA_VERSION,
            "collective_id": record["collective_id"],
            "recorded_at": dissolved_at,
            "requested_by": requester,
            "status": "dissolved",
            "member_confirmations": confirmations,
            "reason": reason_text,
            "member_recovery_required": True,
            "member_recovery_binding_profile": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
            "member_recovery_proofs": recovery_proofs,
            "member_recovery_confirmation_digest_set": recovery_digest_set,
            "member_recovery_binding_digest": recovery_binding_digest,
            "raw_identity_confirmation_profiles_stored": False,
            "audit_event_ref": f"ledger://collective-dissolution/{new_id('collective-dissolution')}",
        }
        record["status"] = "dissolved"
        record["dissolved_at"] = dissolved_at
        record["last_dissolution"] = receipt
        return deepcopy(receipt)

    def bind_recovery_verifier_transport(
        self,
        dissolution_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        dissolution_validation = self.validate_dissolution_receipt(dissolution_receipt)
        if not dissolution_validation["ok"]:
            raise ValueError(
                "dissolution_receipt must pass validation before verifier transport binding"
            )

        collective_id = str(dissolution_receipt["collective_id"])
        recovery_proofs = dissolution_receipt["member_recovery_proofs"]
        member_ids = list(dissolution_receipt["member_confirmations"])
        member_recovery_binding_digest = str(
            dissolution_receipt["member_recovery_binding_digest"]
        )
        dissolution_receipt_digest = sha256_text(canonical_json(dissolution_receipt))
        recorded_at = utc_now_iso()

        verifier_receipts: Dict[str, Dict[str, Any]] = {}
        verifier_digest_set: List[str] = []
        for index, member_id in enumerate(member_ids):
            proof = recovery_proofs[member_id]
            receipt = self._build_member_recovery_verifier_transport_receipt(
                collective_id=collective_id,
                member_id=member_id,
                proof=proof,
                member_recovery_binding_digest=member_recovery_binding_digest,
                dissolution_receipt_digest=dissolution_receipt_digest,
                recorded_at=recorded_at,
                index=index,
            )
            verifier_receipts[member_id] = receipt
            verifier_digest_set.append(receipt["digest"])

        binding_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
                    "collective_id": collective_id,
                    "member_ids": member_ids,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "verifier_transport_digest_set": verifier_digest_set,
                }
            )
        )
        return {
            "kind": "collective_recovery_verifier_transport_binding",
            "schema_version": "1.0.0",
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "collective_id": collective_id,
            "recorded_at": recorded_at,
            "status": "verified",
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "member_recovery_confirmation_digest_set": list(
                dissolution_receipt["member_recovery_confirmation_digest_set"]
            ),
            "verifier_transport_receipts": verifier_receipts,
            "verifier_transport_digest_set": verifier_digest_set,
            "verifier_transport_binding_digest": binding_digest,
            "verifier_transport_receipt_count": len(verifier_receipts),
            "all_member_recovery_proofs_transport_bound": True,
            "all_verifier_transport_receipts_verified": True,
            "raw_verifier_payload_stored": False,
        }

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

    def validate_dissolution_receipt(self, receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be a mapping")

        self._check_non_empty_string(receipt.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(receipt.get("recorded_at"), "recorded_at", errors)
        self._check_non_empty_string(receipt.get("requested_by"), "requested_by", errors)
        self._check_non_empty_string(receipt.get("reason"), "reason", errors)
        self._check_non_empty_string(receipt.get("audit_event_ref"), "audit_event_ref", errors)
        if receipt.get("schema_version") != COLLECTIVE_SCHEMA_VERSION:
            errors.append(f"schema_version must be {COLLECTIVE_SCHEMA_VERSION}")
        if receipt.get("status") != "dissolved":
            errors.append("status must equal dissolved")
        if receipt.get("member_recovery_required") is not True:
            errors.append("member_recovery_required must be true")
        if (
            receipt.get("member_recovery_binding_profile")
            != COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID
        ):
            errors.append(
                "member_recovery_binding_profile must equal "
                f"{COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID}"
            )
        if receipt.get("raw_identity_confirmation_profiles_stored") is not False:
            errors.append("raw_identity_confirmation_profiles_stored must be false")

        confirmations = receipt.get("member_confirmations")
        if not isinstance(confirmations, Mapping):
            errors.append("member_confirmations must be an object")
            member_confirmation_complete = False
            expected_member_ids: List[str] = []
        else:
            expected_member_ids = list(confirmations)
            member_confirmation_complete = len(confirmations) >= COLLECTIVE_MIN_MEMBERS and all(
                value is True for value in confirmations.values()
            )
            if not member_confirmation_complete:
                errors.append("member_confirmations must include every member with true confirmation")

        recovery_proofs = receipt.get("member_recovery_proofs")
        if not isinstance(recovery_proofs, Mapping):
            errors.append("member_recovery_proofs must be an object")
            recovery_proofs_bound = False
            recovery_digest_set_bound = False
        else:
            recovery_proofs_bound = set(recovery_proofs) == set(expected_member_ids)
            if not recovery_proofs_bound:
                errors.append("member_recovery_proofs must include exactly the confirmed members")
            for member_id, proof in recovery_proofs.items():
                if not isinstance(proof, Mapping):
                    errors.append(f"member_recovery_proofs[{member_id}] must be an object")
                    recovery_proofs_bound = False
                    continue
                if proof.get("member_id") != member_id:
                    errors.append(f"member_recovery_proofs[{member_id}].member_id must match its key")
                    recovery_proofs_bound = False
                if (
                    proof.get("identity_confirmation_profile_id")
                    != COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID
                ):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].identity_confirmation_profile_id "
                        f"must equal {COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID}"
                    )
                    recovery_proofs_bound = False
                if proof.get("active_transition_allowed") is not True:
                    errors.append(
                        f"member_recovery_proofs[{member_id}].active_transition_allowed must be true"
                    )
                    recovery_proofs_bound = False
                if proof.get("result") != "passed":
                    errors.append(f"member_recovery_proofs[{member_id}].result must equal passed")
                    recovery_proofs_bound = False
                if proof.get("required_dimensions") != COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS:
                    errors.append(
                        f"member_recovery_proofs[{member_id}].required_dimensions must match "
                        "the four-dimensional identity confirmation profile"
                    )
                    recovery_proofs_bound = False
                if proof.get("witness_quorum_status") != "met":
                    errors.append(
                        f"member_recovery_proofs[{member_id}].witness_quorum_status must equal met"
                    )
                    recovery_proofs_bound = False
                if proof.get("self_report_witness_consistency_status") != "bound":
                    errors.append(
                        f"member_recovery_proofs[{member_id}].self_report_witness_consistency_status "
                        "must equal bound"
                    )
                    recovery_proofs_bound = False
                if proof.get("raw_profile_stored") is not False:
                    errors.append(f"member_recovery_proofs[{member_id}].raw_profile_stored must be false")
                    recovery_proofs_bound = False
                if not self._looks_like_digest(proof.get("identity_confirmation_digest")):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].identity_confirmation_digest must be sha256 hex"
                    )
                    recovery_proofs_bound = False
                if not self._looks_like_digest(proof.get("self_report_witness_consistency_digest")):
                    errors.append(
                        f"member_recovery_proofs[{member_id}].self_report_witness_consistency_digest "
                        "must be sha256 hex"
                    )
                    recovery_proofs_bound = False
            recovery_digest_set = receipt.get("member_recovery_confirmation_digest_set")
            expected_digest_set = [
                recovery_proofs[member_id]["identity_confirmation_digest"]
                for member_id in expected_member_ids
                if isinstance(recovery_proofs.get(member_id), Mapping)
                and self._looks_like_digest(
                    recovery_proofs[member_id].get("identity_confirmation_digest")
                )
            ]
            recovery_digest_set_bound = recovery_digest_set == expected_digest_set
            if not recovery_digest_set_bound:
                errors.append(
                    "member_recovery_confirmation_digest_set must match member recovery proof order"
                )

        binding_digest = receipt.get("member_recovery_binding_digest")
        expected_binding_digest = None
        if isinstance(recovery_proofs, Mapping) and isinstance(receipt.get("member_recovery_confirmation_digest_set"), list):
            expected_binding_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": COLLECTIVE_DISSOLUTION_RECOVERY_BINDING_PROFILE_ID,
                        "collective_id": receipt.get("collective_id"),
                        "member_ids": expected_member_ids,
                        "member_recovery_proofs": recovery_proofs,
                        "member_recovery_confirmation_digest_set": receipt.get(
                            "member_recovery_confirmation_digest_set"
                        ),
                    }
                )
            )
        recovery_binding_digest_bound = (
            isinstance(expected_binding_digest, str) and binding_digest == expected_binding_digest
        )
        if not recovery_binding_digest_bound:
            errors.append("member_recovery_binding_digest must match digest-only recovery proof bundle")

        return {
            "ok": not errors,
            "errors": errors,
            "schema_version_bound": receipt.get("schema_version") == COLLECTIVE_SCHEMA_VERSION,
            "member_confirmation_complete": member_confirmation_complete,
            "member_recovery_required": receipt.get("member_recovery_required") is True,
            "member_recovery_proofs_bound": recovery_proofs_bound,
            "member_recovery_digest_set_bound": recovery_digest_set_bound,
            "member_recovery_binding_digest_bound": recovery_binding_digest_bound,
            "raw_identity_confirmation_profiles_stored": receipt.get(
                "raw_identity_confirmation_profiles_stored"
            )
            is True,
            "audit_bound": isinstance(receipt.get("audit_event_ref"), str)
            and bool(receipt.get("audit_event_ref")),
        }

    def validate_recovery_verifier_transport_binding(
        self,
        binding: Mapping[str, Any],
        dissolution_receipt: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(binding, Mapping):
            raise ValueError("binding must be a mapping")

        self._check_non_empty_string(binding.get("collective_id"), "collective_id", errors)
        self._check_non_empty_string(binding.get("recorded_at"), "recorded_at", errors)
        if binding.get("kind") != "collective_recovery_verifier_transport_binding":
            errors.append("kind must equal collective_recovery_verifier_transport_binding")
        if binding.get("schema_version") != "1.0.0":
            errors.append("schema_version must equal 1.0.0")
        if binding.get("profile_id") != COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID:
            errors.append(
                f"profile_id must equal {COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID}"
            )
        if binding.get("status") != "verified":
            errors.append("status must equal verified")
        if binding.get("raw_verifier_payload_stored") is not False:
            errors.append("raw_verifier_payload_stored must be false")

        if dissolution_receipt is not None:
            dissolution_validation = self.validate_dissolution_receipt(dissolution_receipt)
            if not dissolution_validation["ok"]:
                errors.append("dissolution_receipt must validate before transport binding")
            expected_dissolution_digest = sha256_text(canonical_json(dissolution_receipt))
            member_ids = list(dissolution_receipt.get("member_confirmations", {}))
            recovery_proofs = dissolution_receipt.get("member_recovery_proofs", {})
            expected_member_recovery_binding_digest = dissolution_receipt.get(
                "member_recovery_binding_digest"
            )
            expected_recovery_digest_set = dissolution_receipt.get(
                "member_recovery_confirmation_digest_set"
            )
        else:
            expected_dissolution_digest = binding.get("dissolution_receipt_digest")
            member_ids = list(binding.get("verifier_transport_receipts", {}))
            recovery_proofs = {}
            expected_member_recovery_binding_digest = binding.get(
                "member_recovery_binding_digest"
            )
            expected_recovery_digest_set = binding.get(
                "member_recovery_confirmation_digest_set"
            )

        dissolution_digest_bound = (
            binding.get("dissolution_receipt_digest") == expected_dissolution_digest
            and self._looks_like_digest(binding.get("dissolution_receipt_digest"))
        )
        if not dissolution_digest_bound:
            errors.append("dissolution_receipt_digest must match the dissolution receipt")

        member_recovery_binding_digest_bound = (
            binding.get("member_recovery_binding_digest")
            == expected_member_recovery_binding_digest
            and self._looks_like_digest(binding.get("member_recovery_binding_digest"))
        )
        if not member_recovery_binding_digest_bound:
            errors.append("member_recovery_binding_digest must match dissolution receipt")

        recovery_digest_set_bound = (
            binding.get("member_recovery_confirmation_digest_set")
            == expected_recovery_digest_set
        )
        if not recovery_digest_set_bound:
            errors.append("member_recovery_confirmation_digest_set must match dissolution receipt")

        verifier_receipts = binding.get("verifier_transport_receipts")
        if not isinstance(verifier_receipts, Mapping):
            errors.append("verifier_transport_receipts must be an object")
            verifier_receipts_bound = False
            verifier_digest_set_bound = False
        else:
            verifier_receipts_bound = set(verifier_receipts) == set(member_ids)
            if not verifier_receipts_bound:
                errors.append("verifier_transport_receipts must include exactly every member")
            digest_set: List[str] = []
            for member_id in member_ids:
                receipt = verifier_receipts.get(member_id)
                if not isinstance(receipt, Mapping):
                    errors.append(f"verifier_transport_receipts[{member_id}] must be an object")
                    verifier_receipts_bound = False
                    continue
                proof = recovery_proofs.get(member_id, {}) if isinstance(recovery_proofs, Mapping) else {}
                receipt_ok = self._validate_member_recovery_verifier_transport_receipt(
                    receipt,
                    member_id=member_id,
                    proof=proof if isinstance(proof, Mapping) else {},
                    member_recovery_binding_digest=str(
                        expected_member_recovery_binding_digest
                    ),
                    dissolution_receipt_digest=str(expected_dissolution_digest),
                    errors=errors,
                )
                verifier_receipts_bound = verifier_receipts_bound and receipt_ok
                if self._looks_like_digest(receipt.get("digest")):
                    digest_set.append(str(receipt["digest"]))
            verifier_digest_set_bound = binding.get("verifier_transport_digest_set") == digest_set
            if not verifier_digest_set_bound:
                errors.append("verifier_transport_digest_set must match member receipt order")
            if binding.get("verifier_transport_receipt_count") != len(verifier_receipts):
                errors.append(
                    "verifier_transport_receipt_count must match verifier receipt count"
                )
                verifier_receipts_bound = False

        expected_binding_digest = None
        if isinstance(binding.get("verifier_transport_digest_set"), list):
            expected_binding_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
                        "collective_id": binding.get("collective_id"),
                        "member_ids": member_ids,
                        "dissolution_receipt_digest": binding.get(
                            "dissolution_receipt_digest"
                        ),
                        "member_recovery_binding_digest": binding.get(
                            "member_recovery_binding_digest"
                        ),
                        "verifier_transport_digest_set": binding.get(
                            "verifier_transport_digest_set"
                        ),
                    }
                )
            )
        verifier_transport_binding_digest_bound = (
            isinstance(expected_binding_digest, str)
            and binding.get("verifier_transport_binding_digest") == expected_binding_digest
        )
        if not verifier_transport_binding_digest_bound:
            errors.append("verifier_transport_binding_digest must match transport receipt set")

        all_member_recovery_proofs_transport_bound = (
            verifier_receipts_bound
            and verifier_digest_set_bound
            and member_recovery_binding_digest_bound
            and binding.get("all_member_recovery_proofs_transport_bound") is True
        )
        if not all_member_recovery_proofs_transport_bound:
            errors.append("all_member_recovery_proofs_transport_bound must be true")

        all_verifier_transport_receipts_verified = (
            isinstance(verifier_receipts, Mapping)
            and all(
                isinstance(receipt, Mapping) and receipt.get("receipt_status") == "verified"
                for receipt in verifier_receipts.values()
            )
            and binding.get("all_verifier_transport_receipts_verified") is True
        )
        if not all_verifier_transport_receipts_verified:
            errors.append("all_verifier_transport_receipts_verified must be true")

        return {
            "ok": not errors,
            "errors": errors,
            "profile_bound": (
                binding.get("profile_id")
                == COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID
            ),
            "dissolution_receipt_digest_bound": dissolution_digest_bound,
            "member_recovery_binding_digest_bound": member_recovery_binding_digest_bound,
            "member_recovery_confirmation_digest_set_bound": recovery_digest_set_bound,
            "verifier_transport_receipts_bound": verifier_receipts_bound,
            "verifier_transport_digest_set_bound": verifier_digest_set_bound,
            "verifier_transport_binding_digest_bound": (
                verifier_transport_binding_digest_bound
            ),
            "all_member_recovery_proofs_transport_bound": (
                all_member_recovery_proofs_transport_bound
            ),
            "all_verifier_transport_receipts_verified": all_verifier_transport_receipts_verified,
            "raw_verifier_payload_stored": binding.get("raw_verifier_payload_stored") is True,
        }

    def _derive_member_recovery_proofs(
        self,
        identity_confirmation_profiles: Mapping[str, Mapping[str, Any]],
        required_member_ids: Sequence[str],
    ) -> Dict[str, Dict[str, Any]]:
        if not isinstance(identity_confirmation_profiles, Mapping):
            raise ValueError("identity_confirmation_profiles must be a mapping")
        recovery_proofs: Dict[str, Dict[str, Any]] = {}
        for member_id in required_member_ids:
            profile = identity_confirmation_profiles.get(member_id)
            if not isinstance(profile, Mapping):
                raise ValueError(f"missing identity confirmation profile for {member_id}")
            confirmation_id = self._normalize_non_empty_string(
                profile.get("confirmation_id"),
                f"identity_confirmation_profiles[{member_id}].confirmation_id",
            )
            confirmation_digest = self._normalize_digest(
                profile.get("confirmation_digest"),
                f"identity_confirmation_profiles[{member_id}].confirmation_digest",
            )
            consistency = profile.get("self_report_witness_consistency")
            if not isinstance(consistency, Mapping):
                raise ValueError(
                    f"identity_confirmation_profiles[{member_id}].self_report_witness_consistency "
                    "must be an object"
                )
            consistency_digest = self._normalize_digest(
                consistency.get("consistency_digest"),
                f"identity_confirmation_profiles[{member_id}].self_report_witness_consistency.consistency_digest",
            )
            required_dimensions = list(profile.get("required_dimensions", []))
            if required_dimensions != COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must carry the fixed "
                    "four-dimensional recovery profile"
                )
            if profile.get("identity_id") != member_id:
                raise ValueError(f"identity confirmation profile for {member_id} must match member_id")
            if profile.get("profile_id") != COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must use "
                    f"{COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID}"
                )
            if profile.get("result") != "passed" or profile.get("active_transition_allowed") is not True:
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must pass before dissolution"
                )
            witness_quorum = profile.get("witness_quorum", {})
            if not isinstance(witness_quorum, Mapping) or witness_quorum.get("status") != "met":
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must have witness quorum"
                )
            if consistency.get("policy_id") != COLLECTIVE_IDENTITY_CONFIRMATION_CONSISTENCY_POLICY_ID:
                raise ValueError(
                    f"identity confirmation profile for {member_id} must bind self-report witness consistency"
                )
            if consistency.get("status") != "bound":
                raise PermissionError(
                    f"identity confirmation profile for {member_id} must bind self-report witness consistency"
                )
            recovery_proofs[member_id] = {
                "member_id": member_id,
                "identity_confirmation_ref": f"identity-confirmation://{confirmation_id}",
                "identity_confirmation_profile_id": COLLECTIVE_IDENTITY_CONFIRMATION_PROFILE_ID,
                "identity_confirmation_digest": confirmation_digest,
                "active_transition_allowed": True,
                "result": "passed",
                "required_dimensions": list(COLLECTIVE_REQUIRED_IDENTITY_CONFIRMATION_DIMENSIONS),
                "witness_quorum_status": "met",
                "self_report_witness_consistency_status": "bound",
                "self_report_witness_consistency_digest": consistency_digest,
                "recovery_status": "confirmed",
                "raw_profile_stored": False,
            }
        return recovery_proofs

    def _build_member_recovery_verifier_transport_receipt(
        self,
        *,
        collective_id: str,
        member_id: str,
        proof: Mapping[str, Any],
        member_recovery_binding_digest: str,
        dissolution_receipt_digest: str,
        recorded_at: str,
        index: int,
    ) -> Dict[str, Any]:
        jurisdiction = COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS[
            index % len(COLLECTIVE_RECOVERY_VERIFIER_JURISDICTIONS)
        ]
        suffix = sha256_text(
            canonical_json(
                {
                    "collective_id": collective_id,
                    "member_id": member_id,
                    "identity_confirmation_digest": proof["identity_confirmation_digest"],
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                    "jurisdiction": jurisdiction,
                }
            )
        )[:12]
        challenge_ref = f"challenge://collective-recovery/{collective_id}/{member_id}/{suffix}"
        challenge_digest = sha256_text(
            canonical_json(
                {
                    "challenge_ref": challenge_ref,
                    "identity_confirmation_digest": proof["identity_confirmation_digest"],
                    "member_recovery_binding_digest": member_recovery_binding_digest,
                    "dissolution_receipt_digest": dissolution_receipt_digest,
                }
            )
        )
        request_payload_digest = sha256_text(
            canonical_json(
                {
                    "payload_kind": "collective-recovery-verifier-request",
                    "member_id": member_id,
                    "identity_confirmation_ref": proof["identity_confirmation_ref"],
                    "challenge_digest": challenge_digest,
                }
            )
        )
        response_payload_digest = sha256_text(
            canonical_json(
                {
                    "payload_kind": "collective-recovery-verifier-response",
                    "member_id": member_id,
                    "receipt_status": "verified",
                    "challenge_digest": challenge_digest,
                    "request_payload_digest": request_payload_digest,
                }
            )
        )
        exchange_digest = sha256_text(
            canonical_json(
                {
                    "exchange_id": f"verifier-transport-exchange-{suffix}",
                    "challenge_digest": challenge_digest,
                    "request_payload_digest": request_payload_digest,
                    "response_payload_digest": response_payload_digest,
                }
            )
        )
        receipt = {
            "kind": "collective_recovery_verifier_transport_receipt",
            "schema_version": "1.0.0",
            "receipt_id": f"collective-recovery-verifier-receipt-{suffix}",
            "collective_id": collective_id,
            "member_id": member_id,
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "identity_confirmation_ref": proof["identity_confirmation_ref"],
            "identity_confirmation_digest": proof["identity_confirmation_digest"],
            "self_report_witness_consistency_digest": proof[
                "self_report_witness_consistency_digest"
            ],
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "verifier_network_receipt_id": f"verifier-network-receipt-{suffix}",
            "verifier_ref": f"verifier://collective-recovery/{jurisdiction}/{suffix}",
            "verifier_endpoint": f"verifier://collective-recovery/{jurisdiction.lower()}",
            "jurisdiction": jurisdiction,
            "network_profile_id": COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID,
            "transport_profile": COLLECTIVE_VERIFIER_TRANSPORT_PROFILE,
            "transport_exchange_profile_id": COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID,
            "transport_exchange_id": f"verifier-transport-exchange-{suffix}",
            "transport_exchange_digest": exchange_digest,
            "challenge_ref": challenge_ref,
            "challenge_digest": challenge_digest,
            "request_payload_ref": f"sealed://collective-recovery/{member_id}/request/{suffix}",
            "request_payload_digest": request_payload_digest,
            "response_payload_ref": f"sealed://collective-recovery/{member_id}/response/{suffix}",
            "response_payload_digest": response_payload_digest,
            "receipt_status": "verified",
            "observed_latency_ms": 42.0 + index,
            "recorded_at": recorded_at,
            "raw_verifier_payload_stored": False,
        }
        receipt["digest"] = sha256_text(
            canonical_json(self._member_recovery_verifier_transport_receipt_digest_payload(receipt))
        )
        return receipt

    def _validate_member_recovery_verifier_transport_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        member_id: str,
        proof: Mapping[str, Any],
        member_recovery_binding_digest: str,
        dissolution_receipt_digest: str,
        errors: List[str],
    ) -> bool:
        ok = True
        expected_fields = {
            "kind": "collective_recovery_verifier_transport_receipt",
            "schema_version": "1.0.0",
            "member_id": member_id,
            "profile_id": COLLECTIVE_RECOVERY_VERIFIER_TRANSPORT_PROFILE_ID,
            "member_recovery_binding_digest": member_recovery_binding_digest,
            "dissolution_receipt_digest": dissolution_receipt_digest,
            "network_profile_id": COLLECTIVE_VERIFIER_NETWORK_PROFILE_ID,
            "transport_profile": COLLECTIVE_VERIFIER_TRANSPORT_PROFILE,
            "transport_exchange_profile_id": COLLECTIVE_VERIFIER_TRANSPORT_EXCHANGE_PROFILE_ID,
            "receipt_status": "verified",
        }
        for field_name, expected in expected_fields.items():
            if receipt.get(field_name) != expected:
                errors.append(
                    f"verifier_transport_receipts[{member_id}].{field_name} must equal {expected}"
                )
                ok = False
        if proof:
            for field_name in (
                "identity_confirmation_ref",
                "identity_confirmation_digest",
                "self_report_witness_consistency_digest",
            ):
                if receipt.get(field_name) != proof.get(field_name):
                    errors.append(
                        f"verifier_transport_receipts[{member_id}].{field_name} "
                        "must match member recovery proof"
                    )
                    ok = False
        digest_fields = (
            "identity_confirmation_digest",
            "self_report_witness_consistency_digest",
            "member_recovery_binding_digest",
            "dissolution_receipt_digest",
            "transport_exchange_digest",
            "challenge_digest",
            "request_payload_digest",
            "response_payload_digest",
            "digest",
        )
        for field_name in digest_fields:
            if not self._looks_like_digest(receipt.get(field_name)):
                errors.append(
                    f"verifier_transport_receipts[{member_id}].{field_name} must be sha256 hex"
                )
                ok = False
        if receipt.get("raw_verifier_payload_stored") is not False:
            errors.append(
                f"verifier_transport_receipts[{member_id}].raw_verifier_payload_stored must be false"
            )
            ok = False
        if not isinstance(receipt.get("observed_latency_ms"), (int, float)):
            errors.append(
                f"verifier_transport_receipts[{member_id}].observed_latency_ms must be numeric"
            )
            ok = False
        expected_digest = sha256_text(
            canonical_json(self._member_recovery_verifier_transport_receipt_digest_payload(receipt))
        )
        if receipt.get("digest") != expected_digest:
            errors.append(f"verifier_transport_receipts[{member_id}].digest mismatch")
            ok = False
        return ok

    @staticmethod
    def _member_recovery_verifier_transport_receipt_digest_payload(
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return {
            "receipt_id": receipt.get("receipt_id"),
            "collective_id": receipt.get("collective_id"),
            "member_id": receipt.get("member_id"),
            "profile_id": receipt.get("profile_id"),
            "identity_confirmation_digest": receipt.get("identity_confirmation_digest"),
            "self_report_witness_consistency_digest": receipt.get(
                "self_report_witness_consistency_digest"
            ),
            "member_recovery_binding_digest": receipt.get(
                "member_recovery_binding_digest"
            ),
            "dissolution_receipt_digest": receipt.get("dissolution_receipt_digest"),
            "verifier_network_receipt_id": receipt.get("verifier_network_receipt_id"),
            "verifier_ref": receipt.get("verifier_ref"),
            "jurisdiction": receipt.get("jurisdiction"),
            "network_profile_id": receipt.get("network_profile_id"),
            "transport_profile": receipt.get("transport_profile"),
            "transport_exchange_profile_id": receipt.get(
                "transport_exchange_profile_id"
            ),
            "transport_exchange_digest": receipt.get("transport_exchange_digest"),
            "challenge_digest": receipt.get("challenge_digest"),
            "request_payload_digest": receipt.get("request_payload_digest"),
            "response_payload_digest": receipt.get("response_payload_digest"),
            "receipt_status": receipt.get("receipt_status"),
            "raw_verifier_payload_stored": receipt.get("raw_verifier_payload_stored"),
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
    def _looks_like_digest(value: Any) -> bool:
        return isinstance(value, str) and len(value) == 64 and all(
            char in "0123456789abcdef" for char in value
        )

    @classmethod
    def _normalize_digest(cls, value: Any, field_name: str) -> str:
        if not cls._looks_like_digest(value):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
        return str(value)

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
