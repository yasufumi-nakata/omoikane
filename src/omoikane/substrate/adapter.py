"""Reference substrate adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from ..common import new_id, utc_now_iso


@dataclass
class SubstrateAllocation:
    """Allocated compute/storage slice on a substrate."""

    allocation_id: str
    units: int
    purpose: str
    created_at: str


@dataclass
class SubstrateAttestation:
    """Integrity attestation emitted by the substrate."""

    attestation_id: str
    substrate: str
    integrity: Dict[str, Any]
    measured_at: str
    status: str = "healthy"


class ClassicalSiliconAdapter:
    """Minimal L0 adapter for the reference runtime."""

    def __init__(self) -> None:
        self.allocations: List[SubstrateAllocation] = []
        self.transfers: List[Dict[str, Any]] = []

    def allocate(self, units: int, purpose: str) -> SubstrateAllocation:
        allocation = SubstrateAllocation(
            allocation_id=new_id("alloc"),
            units=units,
            purpose=purpose,
            created_at=utc_now_iso(),
        )
        self.allocations.append(allocation)
        return allocation

    def transfer(self, state: Dict[str, Any], destination: str) -> Dict[str, Any]:
        record = {
            "transfer_id": new_id("xfer"),
            "destination": destination,
            "state_size": len(str(state)),
            "transferred_at": utc_now_iso(),
        }
        self.transfers.append(record)
        return record

    def attest(self, integrity: Dict[str, Any]) -> SubstrateAttestation:
        return SubstrateAttestation(
            attestation_id=new_id("attest"),
            substrate="classical_silicon",
            integrity=integrity,
            measured_at=utc_now_iso(),
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "allocations": [asdict(item) for item in self.allocations],
            "transfers": list(self.transfers),
        }

