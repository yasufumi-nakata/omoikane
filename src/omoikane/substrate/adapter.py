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

    def __init__(self) -> None:
        self.substrate_id = "classical_silicon"
        self.allocations: Dict[str, SubstrateAllocation] = {}
        self.transfers: List[SubstrateTransferRecord] = []
        self.releases: List[Dict[str, Any]] = []
        self.energy_floors: Dict[str, EnergyFloor] = {}

    def allocate(self, units: int, purpose: str, identity_id: str = "system") -> SubstrateAllocation:
        if units < 1:
            raise ValueError("units must be positive")
        allocation = SubstrateAllocation(
            allocation_id=new_id("alloc"),
            identity_id=identity_id,
            substrate=self.substrate_id,
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
    ) -> SubstrateTransferRecord:
        allocation = self._require_active_allocation(allocation_id)
        record = SubstrateTransferRecord(
            transfer_id=new_id("xfer"),
            allocation_id=allocation.allocation_id,
            source_substrate=allocation.substrate,
            destination_substrate=destination_substrate,
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
        floor_table = {
            "baseline": 12,
            "sandbox": 18,
            "council": 24,
            "migration": 30,
        }
        minimum = floor_table.get(workload_class, floor_table["baseline"])
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
