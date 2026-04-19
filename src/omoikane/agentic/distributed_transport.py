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
FEDERATION_ROOTS = (
    "root://federation/pki-a",
    "root://federation/pki-b",
)
HERITAGE_ROOTS = (
    "root://heritage/pki-a",
    "root://heritage/pki-b",
    "root://heritage/pki-c",
)


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
    trust_root_ref: str
    key_epoch: int
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
            "trust_root_ref": self.trust_root_ref,
            "key_epoch": self.key_epoch,
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
    key_epoch: int
    accepted_key_epochs: List[int]
    trust_root_refs: List[str]
    trust_root_quorum: int
    max_hops: int
    previous_envelope_ref: str | None
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
            "key_epoch": self.key_epoch,
            "accepted_key_epochs": list(self.accepted_key_epochs),
            "trust_root_refs": list(self.trust_root_refs),
            "trust_root_quorum": self.trust_root_quorum,
            "max_hops": self.max_hops,
            "previous_envelope_ref": self.previous_envelope_ref,
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
    key_epoch: int
    verified_root_refs: List[str]
    hop_nonce_chain: List[str]
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
            "key_epoch": self.key_epoch,
            "verified_root_refs": list(self.verified_root_refs),
            "hop_nonce_chain": list(self.hop_nonce_chain),
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
        self._consumed_hop_chain_digests: set[str] = set()

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
            key_epoch=1,
            accepted_key_epochs=[1],
            trust_root_refs=[FEDERATION_ROOTS[0]],
            trust_root_quorum=1,
            max_hops=2,
            previous_envelope_ref=None,
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
            key_epoch=1,
            accepted_key_epochs=[1],
            trust_root_refs=[HERITAGE_ROOTS[0], HERITAGE_ROOTS[1]],
            trust_root_quorum=2,
            max_hops=3,
            previous_envelope_ref=None,
        )

    def rotate_transport_keys(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        next_key_epoch: int,
        trust_root_refs: List[str],
        trust_root_quorum: int,
    ) -> DistributedTransportEnvelope:
        if next_key_epoch <= envelope.key_epoch:
            raise ValueError("next_key_epoch must be greater than the current key_epoch")
        normalized_roots = sorted(set(trust_root_refs))
        if not normalized_roots:
            raise ValueError("trust_root_refs must not be empty")
        if trust_root_quorum < 1 or trust_root_quorum > len(normalized_roots):
            raise ValueError("trust_root_quorum must be between 1 and the number of trust roots")

        return self._build_envelope(
            topology_ref=envelope.topology_ref,
            proposal_ref=envelope.proposal_ref,
            council_tier=envelope.council_tier,
            transport_profile=envelope.transport_profile,
            recipient_endpoint=envelope.recipient_endpoint,
            payload_ref=envelope.payload_ref,
            payload_digest=envelope.payload_digest,
            participant_ids=[attestation.participant_id for attestation in envelope.participant_attestations],
            quorum=envelope.quorum,
            required_roles=list(envelope.required_roles),
            freshness_window_s=envelope.freshness_window_s,
            key_epoch=next_key_epoch,
            accepted_key_epochs=sorted(set(envelope.accepted_key_epochs + [next_key_epoch])),
            trust_root_refs=normalized_roots,
            trust_root_quorum=trust_root_quorum,
            max_hops=envelope.max_hops,
            previous_envelope_ref=envelope.envelope_id,
        )

    def record_receipt(
        self,
        envelope: DistributedTransportEnvelope,
        *,
        result_ref: str,
        result_digest: str,
        participant_ids: List[str],
        channel_binding_ref: str,
        verified_root_refs: List[str] | None = None,
        key_epoch: int | None = None,
        hop_nonce_chain: List[str] | None = None,
    ) -> DistributedTransportReceipt:
        attestation_map = {
            attestation.participant_id: attestation for attestation in envelope.participant_attestations
        }
        if verified_root_refs is None:
            verified_root_refs = list(envelope.trust_root_refs[: envelope.trust_root_quorum])
        if key_epoch is None:
            key_epoch = envelope.key_epoch
        if hop_nonce_chain is None:
            hop_nonce_chain = [f"hop://{envelope.council_tier}/{envelope.route_nonce}"]

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
        normalized_root_refs = sorted(set(verified_root_refs))
        federated_roots_verified = sum(
            1 for root_ref in normalized_root_refs if root_ref in envelope.trust_root_refs
        ) >= envelope.trust_root_quorum
        key_epoch_accepted = key_epoch in envelope.accepted_key_epochs
        normalized_hop_nonce_chain = [hop_nonce for hop_nonce in hop_nonce_chain if hop_nonce]
        hop_chain_digest = sha256_text(canonical_json(normalized_hop_nonce_chain))
        multi_hop_replay_status = "accepted"
        if (
            not normalized_hop_nonce_chain
            or len(normalized_hop_nonce_chain) > envelope.max_hops
            or len(set(normalized_hop_nonce_chain)) != len(normalized_hop_nonce_chain)
            or hop_chain_digest in self._consumed_hop_chain_digests
        ):
            multi_hop_replay_status = "blocked"
        replay_guard_status = (
            "blocked" if envelope.route_nonce in self._consumed_route_nonces else "accepted"
        )

        if replay_guard_status == "blocked" or multi_hop_replay_status == "blocked":
            receipt_status = "replay-blocked"
        elif (
            channel_authenticated
            and required_roles_satisfied
            and quorum_attested
            and federated_roots_verified
            and key_epoch_accepted
        ):
            receipt_status = "authenticated"
            self._consumed_route_nonces.add(envelope.route_nonce)
            self._consumed_hop_chain_digests.add(hop_chain_digest)
        else:
            receipt_status = "rejected"

        authenticity_checks = {
            "channel_authenticated": channel_authenticated,
            "required_roles_satisfied": required_roles_satisfied,
            "quorum_attested": quorum_attested,
            "federated_roots_verified": federated_roots_verified,
            "key_epoch_accepted": key_epoch_accepted,
            "replay_guard_status": replay_guard_status,
            "multi_hop_replay_status": multi_hop_replay_status,
        }
        payload = {
            "authenticity_checks": authenticity_checks,
            "council_tier": envelope.council_tier,
            "envelope_digest": envelope.envelope_digest,
            "envelope_ref": envelope.envelope_id,
            "hop_nonce_chain": normalized_hop_nonce_chain,
            "key_epoch": key_epoch,
            "participant_bindings": bindings,
            "receipt_id": new_id("distributed-receipt"),
            "receipt_status": receipt_status,
            "recorded_at": utc_now_iso(),
            "result_digest": result_digest,
            "result_ref": result_ref,
            "route_nonce": envelope.route_nonce,
            "transport_profile": envelope.transport_profile,
            "verified_root_refs": normalized_root_refs,
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
            key_epoch=key_epoch,
            verified_root_refs=normalized_root_refs,
            hop_nonce_chain=normalized_hop_nonce_chain,
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
        key_epoch: int,
        accepted_key_epochs: List[int],
        trust_root_refs: List[str],
        trust_root_quorum: int,
        max_hops: int,
        previous_envelope_ref: str | None,
    ) -> DistributedTransportEnvelope:
        attestations = self._build_attestations(
            council_tier,
            participant_ids,
            key_epoch=key_epoch,
            trust_root_refs=trust_root_refs,
        )
        route_nonce = new_id("route-nonce")
        issued_at = utc_now_iso()
        attestation_digest = sha256_text(
            canonical_json(
                {
                    "attestation_ids": [attestation.attestation_id for attestation in attestations],
                    "accepted_key_epochs": accepted_key_epochs,
                    "roles": [attestation.role for attestation in attestations],
                    "trust_root_refs": trust_root_refs,
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
            "key_epoch": key_epoch,
            "accepted_key_epochs": accepted_key_epochs,
            "trust_root_refs": trust_root_refs,
            "trust_root_quorum": trust_root_quorum,
            "max_hops": max_hops,
            "previous_envelope_ref": previous_envelope_ref,
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
            key_epoch=key_epoch,
            accepted_key_epochs=list(accepted_key_epochs),
            trust_root_refs=list(trust_root_refs),
            trust_root_quorum=trust_root_quorum,
            max_hops=max_hops,
            previous_envelope_ref=previous_envelope_ref,
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
        *,
        key_epoch: int,
        trust_root_refs: List[str],
    ) -> List[DistributedParticipantAttestation]:
        attestations: List[DistributedParticipantAttestation] = []
        for index, participant_id in enumerate(participant_ids):
            role = self._role_for_participant(council_tier, participant_id)
            digest_seed = sha256_text(f"{council_tier}:{participant_id}:{role}:epoch-{key_epoch}")
            trust_root_ref = trust_root_refs[index % len(trust_root_refs)]
            attestations.append(
                DistributedParticipantAttestation(
                    attestation_id=new_id("distributed-attestation"),
                    participant_id=participant_id,
                    council_tier=council_tier,
                    role=role,
                    credential_ref=f"credential://{council_tier}/{digest_seed[:12]}",
                    proof_ref=f"proof://{council_tier}/{digest_seed[12:24]}",
                    transport_key_ref=f"transport-key://{council_tier}/epoch-{key_epoch}/{digest_seed[24:36]}",
                    trust_root_ref=trust_root_ref,
                    key_epoch=key_epoch,
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
