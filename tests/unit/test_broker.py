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

    def test_standby_probe_reports_ready_headroom(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://zeta",
            units=48,
            purpose="standby-probe-ready",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )

        probe = broker.probe_standby("identity://zeta")

        self.assertEqual("ready", probe.probe_status)
        self.assertTrue(probe.ready_for_migrate)
        self.assertGreaterEqual(probe.energy_headroom_jps, 0)
        self.assertEqual("hot-standby", probe.standby_class)

    def test_attestation_chain_requires_healthy_source_attestation(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        broker.lease(
            identity_id="identity://eta",
            units=48,
            purpose="attestation-chain-source-health",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        broker.probe_standby("identity://eta")

        with self.assertRaisesRegex(PermissionError, "healthy attestation required"):
            broker.bridge_attestation_chain(
                "identity://eta",
                state={"identity_id": "identity://eta", "checkpoint": "connectome://eta"},
            )

    def test_attestation_chain_binds_probe_and_destination(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        allocation = broker.lease(
            identity_id="identity://theta",
            units=64,
            purpose="attestation-chain-ready",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        probe = broker.probe_standby("identity://theta")
        attestation = broker.attest(
            "identity://theta",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )

        chain = broker.bridge_attestation_chain(
            "identity://theta",
            state={"identity_id": "identity://theta", "checkpoint": "connectome://theta"},
        )

        self.assertTrue(chain.handoff_ready)
        self.assertEqual("handoff-ready", chain.chain_status)
        self.assertEqual(probe.probe_id, chain.standby_probe_id)
        self.assertEqual(attestation.attestation_id, chain.source_attestation_id)
        self.assertEqual(probe.standby_substrate_id, chain.expected_destination_substrate)
        self.assertEqual(3, len(chain.observations))


if __name__ == "__main__":
    unittest.main()
