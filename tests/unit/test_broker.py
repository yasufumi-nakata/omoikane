from __future__ import annotations

import unittest

from omoikane.kernel.broker import BrokerRegistryEntry, SubstrateBrokerService
from omoikane.substrate.adapter import ClassicalSiliconAdapter


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
        self.assertEqual(
            broker.observe("identity://theta")["selection"]["standby_substrate"]["host_ref"],
            chain.expected_destination_host_ref,
        )
        self.assertTrue(chain.cross_host_verified)
        self.assertEqual(2, chain.distinct_host_count)
        self.assertEqual(3, len(chain.observations))

    def test_dual_allocation_window_requires_method_b(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        allocation = broker.lease(
            identity_id="identity://iota",
            units=64,
            purpose="dual-allocation-method-gate",
            method="A",
            required_capability=0.92,
            workload_class="migration",
        )
        broker.probe_standby("identity://iota")
        broker.attest(
            "identity://iota",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )
        broker.bridge_attestation_chain(
            "identity://iota",
            state={"identity_id": "identity://iota", "checkpoint": "connectome://iota"},
        )

        with self.assertRaisesRegex(PermissionError, "Method B"):
            broker.open_dual_allocation_window(
                "identity://iota",
                state={"identity_id": "identity://iota", "checkpoint": "connectome://iota"},
            )

    def test_dual_allocation_window_materializes_and_closes_shadow_allocation(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        allocation = broker.lease(
            identity_id="identity://kappa",
            units=64,
            purpose="dual-allocation-shadow-sync",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        probe = broker.probe_standby("identity://kappa")
        attestation = broker.attest(
            "identity://kappa",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )
        chain = broker.bridge_attestation_chain(
            "identity://kappa",
            state={"identity_id": "identity://kappa", "checkpoint": "connectome://kappa"},
        )

        window = broker.open_dual_allocation_window(
            "identity://kappa",
            state={
                "identity_id": "identity://kappa",
                "checkpoint": "connectome://kappa",
                "stage": "shadow-sync",
            },
        )

        self.assertEqual("B", window.method)
        self.assertEqual("shadow-active", window.window_status)
        self.assertEqual("allocated", window.shadow_allocation.status)
        self.assertTrue(window.cross_host_verified)
        self.assertEqual(2, window.distinct_host_count)
        self.assertNotEqual(window.source_host_ref, window.shadow_host_ref)
        self.assertEqual(probe.probe_id, window.standby_probe_id)
        self.assertEqual(attestation.attestation_id, window.source_attestation_id)
        self.assertEqual(chain.chain_id, window.attestation_chain_id)
        self.assertEqual(3, len(window.sync_observations))

        closed = broker.close_dual_allocation_window(
            "identity://kappa",
            reason="authority-handoff-complete-demo-cleanup",
        )

        self.assertEqual("closed", closed.window_status)
        self.assertFalse(closed.dual_active)
        self.assertEqual("released", closed.shadow_allocation.status)
        self.assertEqual("released", closed.shadow_release["status"])

    def test_hot_handoff_migrate_requires_sealed_attestation_stream(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        allocation = broker.lease(
            identity_id="identity://lambda",
            units=64,
            purpose="attestation-stream-migrate-gate",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        broker.probe_standby("identity://lambda")
        broker.attest(
            "identity://lambda",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )
        broker.bridge_attestation_chain(
            "identity://lambda",
            state={"identity_id": "identity://lambda", "checkpoint": "connectome://lambda"},
        )
        broker.open_dual_allocation_window(
            "identity://lambda",
            state={
                "identity_id": "identity://lambda",
                "checkpoint": "connectome://lambda",
                "stage": "shadow-sync",
            },
        )

        with self.assertRaisesRegex(PermissionError, "sealed attestation stream"):
            broker.migrate(
                "identity://lambda",
                state={
                    "identity_id": "identity://lambda",
                    "checkpoint": "connectome://lambda",
                    "stage": "authority-handoff",
                },
                continuity_mode="hot-handoff",
            )

    def test_attestation_stream_binds_dual_window_and_handoff_digest(self) -> None:
        broker = SubstrateBrokerService.reference_service()
        allocation = broker.lease(
            identity_id="identity://mu",
            units=64,
            purpose="attestation-stream-seal",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        probe = broker.probe_standby("identity://mu")
        attestation = broker.attest(
            "identity://mu",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )
        chain = broker.bridge_attestation_chain(
            "identity://mu",
            state={"identity_id": "identity://mu", "checkpoint": "connectome://mu"},
        )
        window = broker.open_dual_allocation_window(
            "identity://mu",
            state={
                "identity_id": "identity://mu",
                "checkpoint": "connectome://mu",
                "stage": "shadow-sync",
            },
        )
        handoff_state = {
            "identity_id": "identity://mu",
            "checkpoint": "connectome://mu",
            "stage": "authority-handoff",
        }

        stream = broker.seal_attestation_stream("identity://mu", state=handoff_state)
        transfer = broker.migrate(
            "identity://mu",
            state=handoff_state,
            continuity_mode="hot-handoff",
        )

        self.assertEqual(probe.standby_substrate_id, stream.expected_destination_substrate)
        self.assertEqual(attestation.attestation_id, stream.source_attestation_id)
        self.assertEqual(chain.chain_id, stream.attestation_chain_id)
        self.assertEqual(window.window_id, stream.dual_allocation_window_id)
        self.assertEqual("sealed-handoff-ready", stream.stream_status)
        self.assertTrue(stream.handoff_ready)
        self.assertTrue(stream.cross_host_verified)
        self.assertEqual(2, stream.distinct_host_count)
        self.assertEqual(window.shadow_host_ref, stream.expected_destination_host_ref)
        self.assertEqual(5, len(stream.observations))
        self.assertEqual(5, stream.minimum_healthy_beats)
        self.assertEqual(window.shadow_allocation.substrate, transfer.destination_substrate)
        self.assertEqual(window.shadow_host_ref, transfer.destination_host_ref)
        self.assertTrue(transfer.cross_host_verified)

    def test_attestation_chain_flags_same_host_pair_as_blocked(self) -> None:
        active = ClassicalSiliconAdapter(
            "classical_silicon",
            host_ref="host://substrate/shared-edge-a",
            host_attestation_ref="host-attestation://substrate/shared-edge-a/reference-v1",
            network_zone="tokyo-a",
            substrate_cluster_ref="substrate-cluster://shared-edge",
        )
        standby = ClassicalSiliconAdapter(
            "neuromorphic_mesh.alpha",
            host_ref="host://substrate/shared-edge-a",
            host_attestation_ref="host-attestation://substrate/shared-edge-a/reference-v1",
            network_zone="tokyo-a",
            substrate_cluster_ref="substrate-cluster://shared-edge",
        )
        broker = SubstrateBrokerService(
            adapters={
                active.substrate_id: active,
                standby.substrate_id: standby,
            },
            registry=[
                BrokerRegistryEntry(
                    substrate_id=active.substrate_id,
                    substrate_kind="classical-silicon",
                    capability_score=0.96,
                    health_score=0.94,
                    attestation_valid=True,
                    energy_capacity_jps=64,
                    method_priorities={"A": 0.96, "B": 0.91, "C": 0.72},
                    standby_class="hot-standby",
                    host_ref=active.host_ref,
                    host_attestation_ref=active.host_attestation_ref,
                    jurisdiction=active.jurisdiction,
                    network_zone=active.network_zone,
                    substrate_cluster_ref=active.substrate_cluster_ref,
                ),
                BrokerRegistryEntry(
                    substrate_id=standby.substrate_id,
                    substrate_kind="neuromorphic",
                    capability_score=0.96,
                    health_score=0.94,
                    attestation_valid=True,
                    energy_capacity_jps=64,
                    method_priorities={"A": 0.96, "B": 0.91, "C": 0.72},
                    standby_class="hot-standby",
                    host_ref=standby.host_ref,
                    host_attestation_ref=standby.host_attestation_ref,
                    jurisdiction=standby.jurisdiction,
                    network_zone=standby.network_zone,
                    substrate_cluster_ref=standby.substrate_cluster_ref,
                ),
            ],
        )
        allocation = broker.lease(
            identity_id="identity://same-host",
            units=64,
            purpose="same-host-cross-host-gate",
            method="B",
            required_capability=0.92,
            workload_class="migration",
        )
        broker.probe_standby("identity://same-host")
        broker.attest(
            "identity://same-host",
            {
                "allocation_id": allocation.allocation_id,
                "tee": "reference-broker-attestor-v1",
                "status": "healthy",
            },
        )

        chain = broker.bridge_attestation_chain(
            "identity://same-host",
            state={"identity_id": "identity://same-host", "checkpoint": "connectome://same-host"},
        )

        self.assertFalse(chain.cross_host_verified)
        self.assertFalse(chain.handoff_ready)
        self.assertIn(
            "cross-host handoff requires distinct source and standby hosts",
            chain.blocking_reasons,
        )


if __name__ == "__main__":
    unittest.main()
