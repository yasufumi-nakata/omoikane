from __future__ import annotations

import unittest

from omoikane.interface.sensory_loopback import SensoryLoopbackService


class SensoryLoopbackServiceTests(unittest.TestCase):
    def test_coherent_bundle_preserves_immersion_and_digest_only_audit(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-1",
            body_anchor_ref="avatar://body/core",
        )

        receipt = service.deliver_bundle(
            session["session_id"],
            scene_summary="coherent avatar mirror bundle",
            artifact_refs={
                "visual": "artifact://visual/coherent",
                "auditory": "artifact://auditory/coherent",
                "haptic": "artifact://haptic/coherent",
            },
            latency_ms=48.0,
            body_coherence_score=0.09,
            attention_target="avatar://body/core",
            guardian_observed=True,
            qualia_binding_ref="qualia://tick/0",
        )
        snapshot = service.snapshot(session["session_id"])
        session_validation = service.validate_session(snapshot)
        receipt_validation = service.validate_receipt(receipt)

        self.assertEqual("delivered", receipt["delivery_status"])
        self.assertTrue(receipt["immersion_preserved"])
        self.assertFalse(receipt["safe_baseline_applied"])
        self.assertEqual("active", snapshot["status"])
        self.assertTrue(session_validation["ok"])
        self.assertTrue(session_validation["artifact_digest_only"])
        self.assertTrue(receipt_validation["ok"])

    def test_high_drift_bundle_triggers_guardian_hold_until_stabilized(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-2",
            body_anchor_ref="avatar://body/core",
        )

        held = service.deliver_bundle(
            session["session_id"],
            scene_summary="desynchronized echo destabilizes avatar ownership",
            artifact_refs={
                "visual": "artifact://visual/drifted",
                "auditory": "artifact://auditory/drifted",
                "haptic": "artifact://haptic/drifted",
            },
            latency_ms=172.0,
            body_coherence_score=0.44,
            attention_target="guardian-review",
            guardian_observed=True,
            qualia_binding_ref="qualia://tick/1",
        )
        held_snapshot = service.snapshot(session["session_id"])
        stabilized = service.stabilize(
            session["session_id"],
            reason="guardian realigned the loopback body anchor",
            restored_body_anchor_ref="avatar://body/core",
        )
        final_snapshot = service.snapshot(session["session_id"])

        self.assertEqual("guardian-hold", held["delivery_status"])
        self.assertTrue(held["requires_council_review"])
        self.assertEqual("held", held_snapshot["status"])
        self.assertEqual("stabilized", stabilized["delivery_status"])
        self.assertEqual("resume-loopback", stabilized["guardian_action"])
        self.assertEqual("active", final_snapshot["status"])
        self.assertEqual("avatar://body/core", final_snapshot["body_anchor_ref"])

    def test_degraded_bundle_requires_guardian_observation(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-3",
            body_anchor_ref="avatar://body/core",
        )

        with self.assertRaisesRegex(PermissionError, "guardian observation"):
            service.deliver_bundle(
                session["session_id"],
                scene_summary="degraded bundle without guardian",
                artifact_refs={
                    "visual": "artifact://visual/drifted",
                    "auditory": "artifact://auditory/drifted",
                },
                latency_ms=132.0,
                body_coherence_score=0.28,
                attention_target="guardian-review",
                guardian_observed=False,
            )

    def test_multi_scene_artifact_family_tracks_guardian_recovery(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-4",
            body_anchor_ref="avatar://body/core",
        )

        coherent = service.deliver_bundle(
            session["session_id"],
            scene_summary="coherent avatar mirror bundle",
            artifact_refs={
                "visual": "artifact://visual/coherent-family",
                "auditory": "artifact://auditory/coherent-family",
                "haptic": "artifact://haptic/coherent-family",
            },
            latency_ms=51.0,
            body_coherence_score=0.12,
            attention_target="avatar://body/core",
            guardian_observed=True,
            qualia_binding_ref="qualia://tick/family-0",
        )
        held = service.deliver_bundle(
            session["session_id"],
            scene_summary="loopback drift forces guardian hold",
            artifact_refs={
                "visual": "artifact://visual/drifted-family",
                "auditory": "artifact://auditory/drifted-family",
                "haptic": "artifact://haptic/drifted-family",
            },
            latency_ms=171.0,
            body_coherence_score=0.43,
            attention_target="guardian-review",
            guardian_observed=True,
            qualia_binding_ref="qualia://tick/family-1",
        )
        stabilized = service.stabilize(
            session["session_id"],
            reason="guardian realigned the body anchor",
            restored_body_anchor_ref="avatar://body/core",
        )

        artifact_family = service.capture_artifact_family(
            session["session_id"],
            family_label="atrium-realignment-family",
            receipts=[coherent, held, stabilized],
        )
        snapshot = service.snapshot(session["session_id"])
        validation = service.validate_artifact_family(artifact_family)

        self.assertTrue(validation["ok"])
        self.assertEqual(3, artifact_family["scene_count"])
        self.assertEqual(2, artifact_family["guardian_intervention_count"])
        self.assertEqual("active", artifact_family["final_session_status"])
        self.assertEqual(1, len(artifact_family["stabilization_delivery_ids"]))
        self.assertEqual(1, snapshot["artifact_family_count"])
        self.assertEqual(artifact_family["family_ref"], snapshot["last_artifact_family_ref"])


if __name__ == "__main__":
    unittest.main()
