from __future__ import annotations

import unittest

from omoikane.common import canonical_json, sha256_text
from omoikane.substrate.adapter import ClassicalSiliconAdapter


class ClassicalSiliconAdapterTests(unittest.TestCase):
    def test_allocate_attest_transfer_release_flow(self) -> None:
        adapter = ClassicalSiliconAdapter()
        allocation = adapter.allocate(
            units=32,
            purpose="substrate-migration-eval",
            identity_id="identity-1",
        )
        energy_floor = adapter.energy_floor("identity-1", workload_class="migration")
        attestation = adapter.attest(
            allocation_id=allocation.allocation_id,
            integrity={"tee": "reference-attestor-v1", "status": "healthy"},
        )
        transfer = adapter.transfer(
            allocation_id=allocation.allocation_id,
            state={"identity_id": "identity-1", "checkpoint": "connectome-v1"},
            destination_substrate="classical_silicon.redundant",
        )
        release = adapter.release(allocation_id=allocation.allocation_id, reason="migration-complete")

        self.assertEqual("identity-1", allocation.identity_id)
        self.assertEqual("migration", energy_floor.workload_class)
        self.assertEqual(30, energy_floor.minimum_joules_per_second)
        self.assertEqual(allocation.allocation_id, attestation.allocation_id)
        self.assertEqual(
            sha256_text(canonical_json({"identity_id": "identity-1", "checkpoint": "connectome-v1"})),
            transfer.state_digest,
        )
        self.assertEqual("released", release["status"])
        self.assertEqual("released", adapter.snapshot()["allocations"][0]["status"])

    def test_transfer_rejects_released_allocation(self) -> None:
        adapter = ClassicalSiliconAdapter()
        allocation = adapter.allocate(units=8, purpose="cleanup", identity_id="identity-2")
        adapter.release(allocation.allocation_id, reason="cleanup")

        with self.assertRaisesRegex(ValueError, "allocation is not active"):
            adapter.transfer(
                allocation_id=allocation.allocation_id,
                state={"identity_id": "identity-2"},
                destination_substrate="classical_silicon.redundant",
            )


if __name__ == "__main__":
    unittest.main()
