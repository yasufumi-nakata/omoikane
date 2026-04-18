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
    "crystal-commit": ["self", "council"],
    "connectome-snapshot": ["self", "guardian"],
    "substrate-migrate": ["self", "council", "guardian"],
    "substrate-release": ["guardian"],
    "self-modify": ["self", "council", "guardian"],
    "fork": ["self", "council", "guardian", "third_party"],
    "terminate": ["self", "council", "guardian", "third_party"],
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
