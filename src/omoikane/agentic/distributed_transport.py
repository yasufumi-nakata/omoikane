"""Distributed council transport attestation reference model."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

from ..common import canonical_json, new_id, sha256_text, utc_now_iso

FEDERATION_GUARDIAN_ID = "guardian://neutral-federation"
HERITAGE_PARTICIPANTS = (
    "heritage://culture-a",
    "heritage://culture-b",
    "heritage://legal-advisor",
    "heritage://ethics-committee",
)
ROLE_TRUST_SCORES = {
    "self-liaison": 0.74,
    "guardian": 0.91,
    "cultural-representative": 0.73,
    "legal-advisor": 0.78,
    "ethics-committee": 0.88,
}


@dataclass
class DistributedParticipantAttestation:
    """One remote participant attestation bound to a transport envelope."""

    attestation_id: str
    participant_id: str
    council_tier: str
    role: str
    credential_ref: str
    proof_ref: str
    transport_key_ref: str
    trust_score: float
    issued_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_participant_attestation",
            "schema_version": "1.0.0",
            "attestation_id": self.attestation_id,
            "participant_id": self.participant_id,
            "council_tier": self.council_tier,
            "role": self.role,
            "credential_ref": self.credential_ref,
            "proof_ref": self.proof_ref,
            "transport_key_ref": self.transport_key_ref,
            "trust_score": self.trust_score,
            "issued_at": self.issued_at,
        }


@dataclass
class DistributedTransportEnvelope:
    """Bounded remote handoff bundle for a distributed council review."""

    envelope_id: str
    topology_ref: str
    proposal_ref: str
    council_tier: str
    transport_profile: str
    recipient_endpoint: str
    payload_ref: str
    payload_digest: str
    route_nonce: str
    freshness_window_s: int
    quorum: int
    required_roles: List[str]
    channel_binding_ref: str
    participant_attestations: List[DistributedParticipantAttestation]
    attestation_digest: str
    issued_at: str
    envelope_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_envelope",
            "schema_version": "1.0.0",
            "envelope_id": self.envelope_id,
            "topology_ref": self.topology_ref,
            "proposal_ref": self.proposal_ref,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "recipient_endpoint": self.recipient_endpoint,
            "payload_ref": self.payload_ref,
            "payload_digest": self.payload_digest,
            "route_nonce": self.route_nonce,
            "freshness_window_s": self.freshness_window_s,
            "quorum": self.quorum,
            "required_roles": list(self.required_roles),
            "channel_binding_ref": self.channel_binding_ref,
            "participant_attestations": [
                attestation.to_dict() for attestation in self.participant_attestations
            ],
            "attestation_digest": self.attestation_digest,
            "issued_at": self.issued_at,
            "envelope_digest": self.envelope_digest,
        }


@dataclass
class DistributedTransportReceipt:
    """Receipt recorded after one remote distributed review attempt."""

    receipt_id: str
    envelope_ref: str
    envelope_digest: str
    council_tier: str
    transport_profile: str
    result_ref: str
    result_digest: str
    route_nonce: str
    receipt_status: str
    authenticity_checks: Dict[str, Any]
    participant_bindings: List[Dict[str, Any]]
    recorded_at: str
    digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "distributed_transport_receipt",
            "schema_version": "1.0.0",
            "receipt_id": self.receipt_id,
            "envelope_ref": self.envelope_ref,
            "envelope_digest": self.envelope_digest,
            "council_tier": self.council_tier,
            "transport_profile": self.transport_profile,
            "result_ref": self.result_ref,
            "result_digest": self.result_digest,
            "route_nonce": self.route_nonce,
            "receipt_status": self.receipt_status,
            "authenticity_checks": dict(self.authenticity_checks),
            "participant_bindings": [dict(binding) for binding in self.participant_bindings],
            "recorded_at": self.recorded_at,
            "digest": self.digest,
        }


class DistributedTransportService:
    """Issue transport-attested remote handoff bundles and verify receipts."""

    def __init__(self) -> None:
        self._consumed_route_nonces: set[str] = set()

    def issue_federation_handoff(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        payload_ref: str,
        payload_digest: str,
        participant_identity_ids: List[str],
    ) -> DistributedTransportEnvelope:
        participants = sorted(set(participant_identity_ids))
        if len(participants) < 2:
            raise ValueError("federation handoff requires at least 2 identity participants")
        participants.append(FEDERATION_GUARDIAN_ID)
        return self._build_envelope(
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier="federation",
            transport_profile="federation-mtls-quorum-v1",
            recipient_endpoint="federation://shared-reality-review",
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            participant_ids=participants,
            quorum=3,
            required_roles=["self-liaison", "self-liaison", "guardian"],
            freshness_window_s=900,
        )

    def issue_heritage_handoff(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        payload_ref: str,
        payload_digest: str,
        referenced_clauses: List[str],
    ) -> DistributedTransportEnvelope:
        if not referenced_clauses:
            raise ValueError("heritage handoff requires at least 1 referenced clause")
        return self._build_envelope(
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier="heritage",
            transport_profile="heritage-attested-review-v1",
            recipient_endpoint="heritage://interpretive-review",
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            participant_ids=list(HERITAGE_PARTICIPANTS),
            quorum=4,
            required_roles=[
                "cultural-representative",
                "cultural-representative",
                "legal-advisor",
                "ethics-committee",
            ],
            freshness_window_s=1800,
        )

    def record_receipt(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        result_ref: str,
        result_digest: str,
        participant_ids: List[str],
        channel_binding_ref: str,
    ) -> DistributedTransportReceipt:
        attestation_map = {
            attestation.participant_id: attestation for attestation in envelope.participant_attestations
        }
        bindings: List[Dict[str, Any]] = []
        accepted_role_counts: Counter[str] = Counter()
        accepted_count = 0
        for participant_id in participant_ids:
            attestation = attestation_map.get(participant_id)
            accepted = attestation is not None
            binding = {
                "participant_id": participant_id,
                "role": attestation.role if attestation else "unbound",
                "attestation_ref": attestation.attestation_id if attestation else "",
                "proof_ref": attestation.proof_ref if attestation else "",
                "accepted": accepted,
            }
            bindings.append(binding)
            if accepted and attestation is not None:
                accepted_count += 1
                accepted_role_counts[attestation.role] += 1

        required_role_counts = Counter(envelope.required_roles)
        required_roles_satisfied = all(
            accepted_role_counts[role] >= count for role, count in required_role_counts.items()
        )
        quorum_attested = accepted_count >= envelope.quorum
        channel_authenticated = channel_binding_ref == envelope.channel_binding_ref
        replay_guard_status = (
            "blocked" if envelope.route_nonce in self._consumed_route_nonces else "accepted"
        )

        if replay_guard_status == "blocked":
            receipt_status = "replay-blocked"
        elif channel_authenticated and required_roles_satisfied and quorum_attested:
            receipt_status = "authenticated"
            self._consumed_route_nonces.add(envelope.route_nonce)
        else:
            receipt_status = "rejected"

        authenticity_checks = {
            "channel_authenticated": channel_authenticated,
            "required_roles_satisfied": required_roles_satisfied,
            "quorum_attested": quorum_attested,
            "replay_guard_status": replay_guard_status,
        }
        payload = {
            "authenticity_checks": authenticity_checks,
            "council_tier": envelope.council_tier,
            "envelope_digest": envelope.envelope_digest,
            "envelope_ref": envelope.envelope_id,
            "participant_bindings": bindings,
            "receipt_id": new_id("distributed-receipt"),
            "receipt_status": receipt_status,
            "recorded_at": utc_now_iso(),
            "result_digest": result_digest,
            "result_ref": result_ref,
            "route_nonce": envelope.route_nonce,
            "transport_profile": envelope.transport_profile,
        }
        digest = sha256_text(canonical_json(payload))
        return DistributedTransportReceipt(
            receipt_id=payload["receipt_id"],
            envelope_ref=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            result_ref=result_ref,
            result_digest=result_digest,
            route_nonce=envelope.route_nonce,
            receipt_status=receipt_status,
            authenticity_checks=authenticity_checks,
            participant_bindings=bindings,
            recorded_at=payload["recorded_at"],
            digest=digest,
        )

    def _build_envelope(
        self,
        *,
        topology_ref: str,
        proposal_ref: str,
        council_tier: str,
        transport_profile: str,
        recipient_endpoint: str,
        payload_ref: str,
        payload_digest: str,
        participant_ids: List[str],
        quorum: int,
        required_roles: List[str],
        freshness_window_s: int,
    ) -> DistributedTransportEnvelope:
        attestations = self._build_attestations(council_tier, participant_ids)
        route_nonce = new_id("route-nonce")
        issued_at = utc_now_iso()
        attestation_digest = sha256_text(
            canonical_json(
                {
                    "attestation_ids": [attestation.attestation_id for attestation in attestations],
                    "roles": [attestation.role for attestation in attestations],
                    "transport_profile": transport_profile,
                }
            )
        )
        envelope_payload = {
            "attestation_digest": attestation_digest,
            "channel_binding_ref": f"channel-binding://{council_tier}/{sha256_text(f'{topology_ref}:{payload_digest}:{route_nonce}')[:16]}",
            "council_tier": council_tier,
            "envelope_id": new_id("distributed-envelope"),
            "freshness_window_s": freshness_window_s,
            "issued_at": issued_at,
            "participant_attestations": [attestation.to_dict() for attestation in attestations],
            "payload_digest": payload_digest,
            "payload_ref": payload_ref,
            "proposal_ref": proposal_ref,
            "quorum": quorum,
            "recipient_endpoint": recipient_endpoint,
            "required_roles": required_roles,
            "route_nonce": route_nonce,
            "topology_ref": topology_ref,
            "transport_profile": transport_profile,
        }
        envelope_digest = sha256_text(canonical_json(envelope_payload))
        return DistributedTransportEnvelope(
            envelope_id=envelope_payload["envelope_id"],
            topology_ref=topology_ref,
            proposal_ref=proposal_ref,
            council_tier=council_tier,
            transport_profile=transport_profile,
            recipient_endpoint=recipient_endpoint,
            payload_ref=payload_ref,
            payload_digest=payload_digest,
            route_nonce=route_nonce,
            freshness_window_s=freshness_window_s,
            quorum=quorum,
            required_roles=list(required_roles),
            channel_binding_ref=envelope_payload["channel_binding_ref"],
            participant_attestations=attestations,
            attestation_digest=attestation_digest,
            issued_at=issued_at,
            envelope_digest=envelope_digest,
        )

    def _build_attestations(
        self,
        council_tier: str,
        participant_ids: List[str],
    ) -> List[DistributedParticipantAttestation]:
        attestations: List[DistributedParticipantAttestation] = []
        for participant_id in participant_ids:
            role = self._role_for_participant(council_tier, participant_id)
            digest_seed = sha256_text(f"{council_tier}:{participant_id}:{role}")
            attestations.append(
                DistributedParticipantAttestation(
                    attestation_id=new_id("distributed-attestation"),
                    participant_id=participant_id,
                    council_tier=council_tier,
                    role=role,
                    credential_ref=f"credential://{council_tier}/{digest_seed[:12]}",
                    proof_ref=f"proof://{council_tier}/{digest_seed[12:24]}",
                    transport_key_ref=f"transport-key://{council_tier}/{digest_seed[24:36]}",
                    trust_score=ROLE_TRUST_SCORES[role],
                    issued_at=utc_now_iso(),
                )
            )
        return attestations

    @staticmethod
    def _role_for_participant(council_tier: str, participant_id: str) -> str:
        if council_tier == "federation":
            if participant_id == FEDERATION_GUARDIAN_ID:
                return "guardian"
            return "self-liaison"
        if council_tier == "heritage":
            if participant_id in {"heritage://culture-a", "heritage://culture-b"}:
                return "cultural-representative"
            if participant_id == "heritage://legal-advisor":
                return "legal-advisor"
            if participant_id == "heritage://ethics-committee":
                return "ethics-committee"
        raise ValueError(f"unsupported participant for {council_tier}: {participant_id}")
