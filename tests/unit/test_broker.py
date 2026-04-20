from __future__ import annotations

import unittest

from omoikane.kernel.broker import SubstrateBrokerService


class SubstrateBrokerServiceTests(unittest.TestCase):
    def test_rotation_tie_breaker_promotes_another_substrate_kind(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://alpha",
            units=48,
            purpose="rotation-probe-primary",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )

        rotation_probe = broker.select(
            identity_id="identity://beta",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )

        self.assertTrue(rotation_probe["neutrality_rotation_applied"])
        self.assertEqual("neuromorphic", rotation_probe["active_substrate"]["substrate_kind"])

    def test_same_identity_cannot_hold_two_active_leases(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://gamma",
            units=32,
            purpose="single-active-lease",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )

        with self.assertRaisesRegex(PermissionError, "active leases"):
            broker.lease(
                identity_id="identity://gamma",
                units=16,
                purpose="duplicate-active-lease",
                method="A",
                required_capability=0.92,
                workload_class="migration",
            )

    def test_unhealthy_attestation_blocks_migration(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://delta",
            units=64,
            purpose="attestation-fail-closed",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        broker.attest(
            "identity://delta",
            {
                "allocation_id": "alloc-test",
                "tee": "reference-broker-attestor-v1",
                "status": "compromised",
            },
        )

        with self.assertRaisesRegex(PermissionError, "healthy attestation required"):
            broker.migrate(
                "identity://delta",
                state={"identity_id": "identity://delta", "checkpoint": "connectome://failed"},
            )

    def test_energy_floor_signal_routes_to_standby(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://epsilon",
            units=64,
            purpose="energy-floor-signal",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        observed = broker.observe("identity://epsilon")

        signal = broker.handle_energy_floor_signal(
            "identity://epsilon",
            current_joules_per_second=observed["energy_floor"]["minimum_joules_per_second"] - 1,
        )

        self.assertEqual("critical", signal["severity"])
        self.assertEqual("migrate-standby", signal["recommended_action"])
        self.assertEqual(
            observed["selection"]["standby_substrate"]["substrate_id"],
            signal["standby_substrate"],
        )


if __name__ == "__main__":
    unittest.main()
