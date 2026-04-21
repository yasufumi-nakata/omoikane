"""Reference substrate adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


@dataclass
class SubstrateAllocation:
    """Allocated compute/storage slice on a substrate."""

    allocation_id: str
    identity_id: str
    substrate: str
    host_ref: str
    host_attestation_ref: str
    jurisdiction: str
    network_zone: str
    substrate_cluster_ref: str
    units: int
    purpose: str
    created_at: str
    status: str = "allocated"
    released_at: Optional[str] = None


@dataclass
class SubstrateAttestation:
    """Integrity attestation emitted by the substrate."""

    attestation_id: str
    allocation_id: str
    substrate: str
    integrity: Dict[str, Any]
    measured_at: str
    status: str = "healthy"


@dataclass
class SubstrateTransferRecord:
    """Recorded migration of one allocation across substrates."""

    transfer_id: str
    allocation_id: str
    source_substrate: str
    destination_substrate: str
    source_host_ref: str
    source_host_attestation_ref: str
    source_jurisdiction: str
    source_network_zone: str
    destination_host_ref: str
    destination_host_attestation_ref: str
    destination_jurisdiction: str
    destination_network_zone: str
    substrate_cluster_ref: str
    cross_host_binding_profile: str
    host_binding_digest: str
    cross_host_verified: bool
    state_digest: str
    continuity_mode: str
    transferred_at: str


@dataclass
class EnergyFloor:
    """Ethics-coupled minimum energy budget for one identity."""

    identity_id: str
    minimum_joules_per_second: int
    workload_class: str
    evaluated_at: str


class ClassicalSiliconAdapter:
    """Minimal L0 adapter for the reference runtime."""

    ENERGY_FLOOR_TABLE = {
        "baseline": 12,
        "sandbox": 18,
        "council": 24,
        "migration": 30,
    }

    def __init__(
        self,
        substrate_id: str = "classical_silicon",
        *,
        host_ref: Optional[str] = None,
        host_attestation_ref: Optional[str] = None,
        jurisdiction: str = "JP-13",
        network_zone: Optional[str] = None,
        substrate_cluster_ref: str = "substrate-cluster://reference-broker-fabric",
    ) -> None:
        self.substrate_id = substrate_id
        self.host_ref = host_ref or _default_host_ref(substrate_id)
        self.host_attestation_ref = host_attestation_ref or _default_host_attestation_ref(
            substrate_id
        )
        self.jurisdiction = jurisdiction
        self.network_zone = network_zone or _default_network_zone(substrate_id)
        self.substrate_cluster_ref = substrate_cluster_ref
        self.allocations: Dict[str, SubstrateAllocation] = {}
        self.transfers: List[SubstrateTransferRecord] = []
        self.releases: List[Dict[str, Any]] = []
        self.energy_floors: Dict[str, EnergyFloor] = {}

    @classmethod
    def minimum_energy_floor_for(cls, workload_class: str = "baseline") -> int:
        return int(cls.ENERGY_FLOOR_TABLE.get(workload_class, cls.ENERGY_FLOOR_TABLE["baseline"]))

    def allocate(self, units: int, purpose: str, identity_id: str = "system") -> SubstrateAllocation:
        if units < 1:
            raise ValueError("units must be positive")
        allocation = SubstrateAllocation(
            allocation_id=new_id("alloc"),
            identity_id=identity_id,
            substrate=self.substrate_id,
            host_ref=self.host_ref,
            host_attestation_ref=self.host_attestation_ref,
            jurisdiction=self.jurisdiction,
            network_zone=self.network_zone,
            substrate_cluster_ref=self.substrate_cluster_ref,
            units=units,
            purpose=purpose,
            created_at=utc_now_iso(),
        )
        self.allocations[allocation.allocation_id] = allocation
        return allocation

    def transfer(
        self,
        allocation_id: str,
        state: Dict[str, Any],
        destination_substrate: str,
        continuity_mode: str = "warm-standby",
        *,
        destination_host_ref: Optional[str] = None,
        destination_host_attestation_ref: Optional[str] = None,
        destination_jurisdiction: Optional[str] = None,
        destination_network_zone: Optional[str] = None,
        substrate_cluster_ref: Optional[str] = None,
        cross_host_binding_profile: str = "attested-cross-host-substrate-handoff-v1",
        host_binding_digest: Optional[str] = None,
    ) -> SubstrateTransferRecord:
        allocation = self._require_active_allocation(allocation_id)
        resolved_destination_host_ref = destination_host_ref or _default_host_ref(destination_substrate)
        resolved_destination_host_attestation_ref = (
            destination_host_attestation_ref
            or _default_host_attestation_ref(destination_substrate)
        )
        resolved_destination_jurisdiction = destination_jurisdiction or self.jurisdiction
        resolved_destination_network_zone = destination_network_zone or _default_network_zone(
            destination_substrate
        )
        resolved_cluster_ref = substrate_cluster_ref or allocation.substrate_cluster_ref
        cross_host_verified = allocation.host_ref != resolved_destination_host_ref
        resolved_host_binding_digest = host_binding_digest or sha256_text(
            canonical_json(
                {
                    "source_substrate_id": allocation.substrate,
                    "source_host_ref": allocation.host_ref,
                    "destination_substrate_id": destination_substrate,
                    "destination_host_ref": resolved_destination_host_ref,
                    "substrate_cluster_ref": resolved_cluster_ref,
                }
            )
        )
        record = SubstrateTransferRecord(
            transfer_id=new_id("xfer"),
            allocation_id=allocation.allocation_id,
            source_substrate=allocation.substrate,
            destination_substrate=destination_substrate,
            source_host_ref=allocation.host_ref,
            source_host_attestation_ref=allocation.host_attestation_ref,
            source_jurisdiction=allocation.jurisdiction,
            source_network_zone=allocation.network_zone,
            destination_host_ref=resolved_destination_host_ref,
            destination_host_attestation_ref=resolved_destination_host_attestation_ref,
            destination_jurisdiction=resolved_destination_jurisdiction,
            destination_network_zone=resolved_destination_network_zone,
            substrate_cluster_ref=resolved_cluster_ref,
            cross_host_binding_profile=cross_host_binding_profile,
            host_binding_digest=resolved_host_binding_digest,
            cross_host_verified=cross_host_verified,
            state_digest=sha256_text(canonical_json(state)),
            continuity_mode=continuity_mode,
            transferred_at=utc_now_iso(),
        )
        self.transfers.append(record)
        return record

    def attest(self, allocation_id: str, integrity: Dict[str, Any]) -> SubstrateAttestation:
        allocation = self._require_active_allocation(allocation_id)
        return SubstrateAttestation(
            attestation_id=new_id("attest"),
            allocation_id=allocation.allocation_id,
            substrate=allocation.substrate,
            integrity=integrity,
            measured_at=utc_now_iso(),
            status=str(integrity.get("status", "healthy")),
        )

    def release(self, allocation_id: str, reason: str = "completed") -> Dict[str, Any]:
        allocation = self._require_active_allocation(allocation_id)
        allocation.status = "released"
        allocation.released_at = utc_now_iso()
        record = {
            "release_id": new_id("release"),
            "allocation_id": allocation.allocation_id,
            "reason": reason,
            "released_at": allocation.released_at,
            "status": allocation.status,
        }
        self.releases.append(record)
        return record

    def energy_floor(self, identity_id: str, workload_class: str = "baseline") -> EnergyFloor:
        minimum = self.minimum_energy_floor_for(workload_class)
        floor = EnergyFloor(
            identity_id=identity_id,
            minimum_joules_per_second=minimum,
            workload_class=workload_class,
            evaluated_at=utc_now_iso(),
        )
        self.energy_floors[identity_id] = floor
        return floor

    def snapshot(self) -> Dict[str, Any]:
        return {
            "substrate": self.substrate_id,
            "allocations": [asdict(item) for item in self.allocations.values()],
            "transfers": [asdict(item) for item in self.transfers],
            "releases": list(self.releases),
            "energy_floors": [asdict(item) for item in self.energy_floors.values()],
        }

    def _require_active_allocation(self, allocation_id: str) -> SubstrateAllocation:
        allocation = self.allocations.get(allocation_id)
        if allocation is None:
            raise ValueError(f"unknown allocation: {allocation_id}")
        if allocation.status != "allocated":
            raise ValueError(f"allocation is not active: {allocation_id}")
        return allocation


def _default_host_ref(substrate_id: str) -> str:
    return f"host://substrate/{_substrate_slug(substrate_id)}"


def _default_host_attestation_ref(substrate_id: str) -> str:
    return f"host-attestation://substrate/{_substrate_slug(substrate_id)}/reference-v1"


def _default_network_zone(substrate_id: str) -> str:
    lowered = substrate_id.lower()
    if "neuromorphic" in lowered:
        return "tokyo-b"
    if "photonic" in lowered:
        return "osaka-a"
    if "redundant" in lowered:
        return "tokyo-c"
    return "tokyo-a"


def _substrate_slug(substrate_id: str) -> str:
    slug = "".join(character if character.isalnum() else "-" for character in substrate_id.lower())
    return slug.strip("-") or "substrate"
