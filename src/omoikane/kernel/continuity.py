"""Append-only continuity ledger."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..common import canonical_json, hmac_sha256_text, sha256_text, utc_now_iso

GENESIS_HASH = "GENESIS:sha256"
DEFAULT_CHAIN_ALGORITHM = "sha256"
DEFAULT_SIGNATURE_ALGORITHM = "hmac-sha256"
DEFAULT_SUBSTRATE = "reference-runtime"
PUBLIC_VERIFICATION_PROFILE_ID = "continuity-public-verification-key-management-v1"
PUBLIC_VERIFICATION_SCHEMA_VERSION = "1.0.0"
PUBLIC_VERIFICATION_ROSTER_REF = "verifier://continuity-ledger/public-roster/reference-v1"
PUBLIC_VERIFICATION_ROOT_REF = "verifier://continuity-ledger/root/reference-v1"
PUBLIC_VERIFICATION_KEY_ALGORITHM = "hmac-sha256-reference-key-digest-v1"

ROLE_SECRET_KEYS = {
    "self": "omoikane-reference-self",
    "council": "omoikane-reference-council",
    "guardian": "omoikane-reference-guardian",
    "third_party": "omoikane-reference-third-party",
}

REQUIRED_SIGNATURE_ROLES = {
    "ascension": ["self"],
    "attestation": ["guardian"],
    "qualia-checkpoint": ["self"],
    "cognitive-audit": ["self", "council", "guardian"],
    "episodic-window": ["self"],
    "crystal-commit": ["self", "council"],
    "semantic-projection": ["self", "council"],
    "memory-edit": ["self", "guardian"],
    "energy-budget": ["self", "guardian"],
    "procedural-preview": ["self", "council"],
    "connectome-snapshot": ["self", "guardian"],
    "substrate-migrate": ["self", "council", "guardian"],
    "substrate-release": ["guardian"],
    "self-modify": ["self", "council", "guardian"],
    "fork": ["self", "council", "guardian", "third_party"],
    "terminate": ["self", "council", "guardian", "third_party"],
    "selfctor-gap-report-scan": ["self", "guardian"],
    "ethics-veto": ["guardian"],
    "ethics-escalate": ["guardian"],
    "cognitive-failover": ["guardian"],
    "sandbox-monitor": ["guardian"],
    "sandbox-freeze": ["guardian"],
    "guardian-oversight": ["third_party"],
}


def _canonical_payload_ref(payload: Dict[str, Any]) -> str:
    return f"cas://sha256/{sha256_text(canonical_json(payload))}"


def _signature_value(role: str, entry_hash: str) -> str:
    return f"{DEFAULT_SIGNATURE_ALGORITHM}:{hmac_sha256_text(ROLE_SECRET_KEYS[role], entry_hash)}"


def _role_verification_scope(role: str) -> List[str]:
    return sorted(
        category
        for category, roles in REQUIRED_SIGNATURE_ROLES.items()
        if role in roles
    )


def _public_verifier_key_ref(role: str) -> str:
    return f"key://continuity-ledger/{role}/reference-verifier/v1"


@dataclass
class ContinuityLedgerEntry:
    """Single append-only ledger event."""

    cursor: int
    entry_id: str
    prev_hash: str
    identity_id: str
    logical_time: int
    wall_time: str
    substrate: str
    layer: str
    category: str
    event_type: str
    payload_ref: str
    payload: Dict[str, Any]
    actor: str
    chain_algorithm: str = DEFAULT_CHAIN_ALGORITHM
    signature_algorithm: str = DEFAULT_SIGNATURE_ALGORITHM
    signatures: Dict[str, str] = field(default_factory=dict)
    entry_hash: str = ""

    def signable_payload(self) -> Dict[str, Any]:
        return {
            "actor": self.actor,
            "category": self.category,
            "chain_algorithm": self.chain_algorithm,
            "cursor": self.cursor,
            "event_type": self.event_type,
            "identity_id": self.identity_id,
            "layer": self.layer,
            "logical_time": self.logical_time,
            "payload_ref": self.payload_ref,
            "prev_hash": self.prev_hash,
            "signature_algorithm": self.signature_algorithm,
            "substrate": self.substrate,
            "wall_time": self.wall_time,
        }

    def to_schema_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "entry_hash": self.entry_hash,
            "prev_hash": self.prev_hash,
            "identity_id": self.identity_id,
            "logical_time": self.logical_time,
            "wall_time": self.wall_time,
            "substrate": self.substrate,
            "layer": self.layer,
            "category": self.category,
            "event_type": self.event_type,
            "payload_ref": self.payload_ref,
            "payload_inline": deepcopy(self.payload),
            "chain_algorithm": self.chain_algorithm,
            "signature_algorithm": self.signature_algorithm,
            "signatures": dict(self.signatures),
        }


class ContinuityLedger:
    """Reference append-only continuity ledger."""

    def __init__(self) -> None:
        self._entries: List[ContinuityLedgerEntry] = []

    def append(
        self,
        identity_id: str,
        event_type: str,
        payload: Dict[str, Any],
        actor: str,
        category: str,
        layer: str,
        signature_roles: Optional[List[str]] = None,
        substrate: str = DEFAULT_SUBSTRATE,
        wall_time: Optional[str] = None,
    ) -> ContinuityLedgerEntry:
        required_roles = REQUIRED_SIGNATURE_ROLES.get(category, [])
        requested_roles = list(signature_roles or [])
        missing = [role for role in required_roles if role not in requested_roles]
        if missing:
            raise ValueError(
                f"category '{category}' requires signatures from: {', '.join(missing)}"
            )

        payload_copy = deepcopy(payload)
        payload_ref = _canonical_payload_ref(payload_copy)
        entry = ContinuityLedgerEntry(
            cursor=len(self._entries),
            entry_id="",
            prev_hash=self._entries[-1].entry_hash if self._entries else GENESIS_HASH,
            identity_id=identity_id,
            logical_time=len(self._entries),
            wall_time=wall_time or utc_now_iso(),
            substrate=substrate,
            layer=layer,
            category=category,
            event_type=event_type,
            payload_ref=payload_ref,
            payload=payload_copy,
            actor=actor,
        )
        entry.entry_hash = sha256_text(canonical_json(entry.signable_payload()))
        entry.entry_id = entry.entry_hash
        entry.signatures = {
            role: _signature_value(role, entry.entry_hash)
            for role in requested_roles
        }
        self._entries.append(entry)
        return entry

    def entries(self) -> List[ContinuityLedgerEntry]:
        return list(self._entries)

    def profile(self) -> Dict[str, Any]:
        return {
            "genesis_hash": GENESIS_HASH,
            "chain_algorithm": DEFAULT_CHAIN_ALGORITHM,
            "signature_algorithm": DEFAULT_SIGNATURE_ALGORITHM,
            "required_signature_roles": deepcopy(REQUIRED_SIGNATURE_ROLES),
            "public_verification_profile": {
                "profile_id": PUBLIC_VERIFICATION_PROFILE_ID,
                "key_roster_ref": PUBLIC_VERIFICATION_ROSTER_REF,
                "root_ref": PUBLIC_VERIFICATION_ROOT_REF,
                "rotation_state": "stable",
                "raw_key_material_exposed": False,
                "raw_signature_payload_exposed": False,
            },
        }

    def public_verification_key_roster(self) -> Dict[str, Any]:
        key_records: List[Dict[str, Any]] = []
        for role in sorted(ROLE_SECRET_KEYS):
            record_core = {
                "role": role,
                "key_epoch": 1,
                "verifier_key_ref": _public_verifier_key_ref(role),
                "key_algorithm": PUBLIC_VERIFICATION_KEY_ALGORITHM,
                "signature_algorithm": DEFAULT_SIGNATURE_ALGORITHM,
                "status": "active",
                "verification_scope": _role_verification_scope(role),
                "raw_key_material_exposed": False,
            }
            key_records.append(
                {
                    **record_core,
                    "key_digest": sha256_text(canonical_json(record_core)),
                }
            )

        roster_core = {
            "profile_id": PUBLIC_VERIFICATION_PROFILE_ID,
            "roster_ref": PUBLIC_VERIFICATION_ROSTER_REF,
            "root_ref": PUBLIC_VERIFICATION_ROOT_REF,
            "rotation_state": "stable",
            "active_epoch": 1,
            "signature_algorithm": DEFAULT_SIGNATURE_ALGORITHM,
            "key_algorithm": PUBLIC_VERIFICATION_KEY_ALGORITHM,
            "key_records": key_records,
            "raw_key_material_exposed": False,
        }
        return {
            **roster_core,
            "roster_digest": sha256_text(canonical_json(roster_core)),
        }

    def compile_public_verification_bundle(self) -> Dict[str, Any]:
        key_roster = self.public_verification_key_roster()
        records_by_role = {
            record["role"]: record
            for record in key_roster["key_records"]
        }
        verification_entries: List[Dict[str, Any]] = []

        for entry in self._entries:
            required_roles = REQUIRED_SIGNATURE_ROLES.get(entry.category, [])
            present_roles = sorted(entry.signatures)
            failure_reasons: List[str] = []
            missing_roles = [role for role in required_roles if role not in entry.signatures]
            if missing_roles:
                failure_reasons.append(
                    f"missing required signatures: {','.join(missing_roles)}"
                )

            signature_digests: Dict[str, str] = {}
            verifier_key_refs: Dict[str, str] = {}
            for role in present_roles:
                if role not in records_by_role:
                    failure_reasons.append(f"unknown signature role: {role}")
                    continue
                signature_digests[role] = sha256_text(entry.signatures[role])
                verifier_key_refs[role] = records_by_role[role]["verifier_key_ref"]
                expected_signature = _signature_value(role, entry.entry_hash)
                if entry.signatures[role] != expected_signature:
                    failure_reasons.append(f"signature mismatch: {role}")

            expected_hash = sha256_text(canonical_json(entry.signable_payload()))
            if entry.entry_hash != expected_hash:
                failure_reasons.append("entry_hash mismatch")
            if entry.payload_ref != _canonical_payload_ref(entry.payload):
                failure_reasons.append("payload_ref mismatch")

            entry_core = {
                "entry_id": entry.entry_id,
                "entry_hash": entry.entry_hash,
                "payload_ref": entry.payload_ref,
                "category": entry.category,
                "event_type": entry.event_type,
                "required_signature_roles": list(required_roles),
                "present_signature_roles": present_roles,
                "signature_digests": signature_digests,
                "verifier_key_refs": verifier_key_refs,
                "verification_status": "verified" if not failure_reasons else "failed",
                "failure_reasons": failure_reasons,
            }
            verification_entries.append(
                {
                    **entry_core,
                    "verification_digest": sha256_text(canonical_json(entry_core)),
                }
            )

        ledger_verification = self.verify()
        ledger_head = self._entries[-1].entry_hash if self._entries else GENESIS_HASH
        bundle_id_seed = {
            "entry_count": len(self._entries),
            "ledger_head": ledger_head,
            "roster_digest": key_roster["roster_digest"],
        }
        bundle_core = {
            "kind": "continuity_public_verification_bundle",
            "schema_version": PUBLIC_VERIFICATION_SCHEMA_VERSION,
            "profile_id": PUBLIC_VERIFICATION_PROFILE_ID,
            "bundle_id": f"continuity-public-verification-{sha256_text(canonical_json(bundle_id_seed))[:12]}",
            "identity_ids": sorted({entry.identity_id for entry in self._entries}),
            "ledger_head": ledger_head,
            "entry_count": len(self._entries),
            "verified_entry_count": sum(
                1
                for item in verification_entries
                if item["verification_status"] == "verified"
            ),
            "chain_algorithm": DEFAULT_CHAIN_ALGORITHM,
            "signature_algorithm": DEFAULT_SIGNATURE_ALGORITHM,
            "key_roster": key_roster,
            "ledger_verification_digest": sha256_text(canonical_json(ledger_verification)),
            "verification_entries": verification_entries,
            "public_verification_ready": (
                ledger_verification["ok"]
                and len(verification_entries) == len(self._entries)
                and all(
                    item["verification_status"] == "verified"
                    for item in verification_entries
                )
            ),
            "raw_key_material_exposed": False,
            "raw_signature_payload_exposed": False,
        }
        return {
            **bundle_core,
            "bundle_digest": sha256_text(canonical_json(bundle_core)),
        }

    def validate_public_verification_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        expected = self.compile_public_verification_bundle()
        errors: List[str] = []
        bundle_core = {
            key: deepcopy(value)
            for key, value in bundle.items()
            if key != "bundle_digest"
        }
        actual_bundle_digest = sha256_text(canonical_json(bundle_core))

        if bundle.get("kind") != "continuity_public_verification_bundle":
            errors.append("kind mismatch")
        if bundle.get("schema_version") != PUBLIC_VERIFICATION_SCHEMA_VERSION:
            errors.append("schema_version mismatch")
        if bundle.get("profile_id") != PUBLIC_VERIFICATION_PROFILE_ID:
            errors.append("profile_id mismatch")
        if bundle.get("bundle_digest") != actual_bundle_digest:
            errors.append("bundle_digest mismatch")
        if bundle.get("bundle_digest") != expected["bundle_digest"]:
            errors.append("bundle_digest does not match current ledger")
        if bundle.get("ledger_head") != expected["ledger_head"]:
            errors.append("ledger_head mismatch")
        if bundle.get("verification_entries") != expected["verification_entries"]:
            errors.append("verification_entries mismatch")

        key_roster = bundle.get("key_roster")
        expected_roster = expected["key_roster"]
        key_roster_bound = key_roster == expected_roster
        if not key_roster_bound:
            errors.append("key_roster mismatch")

        raw_key_material_excluded = (
            bundle.get("raw_key_material_exposed") is False
            and isinstance(key_roster, dict)
            and key_roster.get("raw_key_material_exposed") is False
            and all(
                isinstance(record, dict)
                and record.get("raw_key_material_exposed") is False
                and "secret" not in record
                for record in key_roster.get("key_records", [])
            )
        )
        if not raw_key_material_excluded:
            errors.append("raw key material must not be exposed")

        raw_signature_material_excluded = (
            bundle.get("raw_signature_payload_exposed") is False
            and all(
                "signatures" not in item
                for item in bundle.get("verification_entries", [])
                if isinstance(item, dict)
            )
        )
        if not raw_signature_material_excluded:
            errors.append("raw signature payload must not be exposed")

        public_verification_ready = (
            bundle.get("public_verification_ready") is True
            and bundle.get("verified_entry_count") == bundle.get("entry_count")
            and not errors
        )

        return {
            "ok": not errors,
            "profile_id": PUBLIC_VERIFICATION_PROFILE_ID,
            "public_verification_ready": public_verification_ready,
            "key_roster_bound": key_roster_bound,
            "ledger_head_bound": bundle.get("ledger_head") == expected["ledger_head"],
            "entry_verification_bound": bundle.get("verification_entries") == expected["verification_entries"],
            "raw_key_material_excluded": raw_key_material_excluded,
            "raw_signature_material_excluded": raw_signature_material_excluded,
            "verified_entry_count": bundle.get("verified_entry_count"),
            "errors": errors,
        }

    def verify(self) -> Dict[str, Any]:
        errors: List[str] = []
        previous_hash = GENESIS_HASH
        category_counts: Dict[str, int] = {}

        for index, entry in enumerate(self._entries):
            category_counts[entry.category] = category_counts.get(entry.category, 0) + 1
            if entry.cursor != index:
                errors.append(f"cursor mismatch at {index}")
            if entry.logical_time != index:
                errors.append(f"logical_time mismatch at {index}")
            if entry.prev_hash != previous_hash:
                errors.append(f"prev_hash mismatch at {index}")
            if entry.chain_algorithm != DEFAULT_CHAIN_ALGORITHM:
                errors.append(f"unsupported chain_algorithm at {index}")
            if entry.signature_algorithm != DEFAULT_SIGNATURE_ALGORITHM:
                errors.append(f"unsupported signature_algorithm at {index}")

            expected_payload_ref = _canonical_payload_ref(entry.payload)
            if entry.payload_ref != expected_payload_ref:
                errors.append(f"payload_ref mismatch at {index}")

            expected_hash = sha256_text(canonical_json(entry.signable_payload()))
            if entry.entry_hash != expected_hash:
                errors.append(f"entry_hash mismatch at {index}")
            if entry.entry_id != entry.entry_hash:
                errors.append(f"entry_id mismatch at {index}")

            required_roles = REQUIRED_SIGNATURE_ROLES.get(entry.category, [])
            missing_roles = [role for role in required_roles if role not in entry.signatures]
            if missing_roles:
                errors.append(
                    f"missing required signatures at {index}: {', '.join(missing_roles)}"
                )

            for role, signature in entry.signatures.items():
                if role not in ROLE_SECRET_KEYS:
                    errors.append(f"unknown signature role at {index}: {role}")
                    continue
                expected_signature = _signature_value(role, entry.entry_hash)
                if signature != expected_signature:
                    errors.append(f"signature mismatch at {index}: {role}")

            previous_hash = entry.entry_hash

        return {
            "ok": not errors,
            "entry_count": len(self._entries),
            "category_counts": category_counts,
            "profile": self.profile(),
            "errors": errors,
        }

    def snapshot(self) -> List[Dict[str, Any]]:
        return [entry.to_schema_dict() for entry in self._entries]

    def raw_entries(self) -> List[Dict[str, Any]]:
        return [asdict(entry) for entry in self._entries]
