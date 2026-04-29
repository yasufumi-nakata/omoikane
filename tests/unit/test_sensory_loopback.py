from __future__ import annotations

from copy import deepcopy
import unittest

from omoikane.interface.biodata_transmitter import BioDataTransmitter
from omoikane.interface.sensory_loopback import SensoryLoopbackService


class SensoryLoopbackServiceTests(unittest.TestCase):
    @staticmethod
    def _fake_biodata_confidence_gate(identity_id: str, suffix: str) -> dict:
        return {
            "profile_id": "biodata-calibration-confidence-gate-v1",
            "identity_id": identity_id,
            "gate_ref": f"confidence-gate://unit/{suffix}",
            "gate_receipt_digest": f"{suffix[:1]}" * 64,
            "confidence_gate_status": "bound",
            "confidence_score": 0.91,
            "sensory_loopback_gate_bound": True,
            "feature_window_series_drift_gate_ref": (
                f"feature-window-drift-gate://unit/{suffix}"
            ),
            "feature_window_series_drift_gate_digest": f"{suffix[:1].upper()}" * 64,
            "feature_window_series_drift_threshold_digest": "c" * 64,
            "feature_window_series_drift_gate_status": "pass",
            "feature_window_series_drift_gate_bound": True,
            "target_gate_set_digest": "d" * 64,
            "target_gate_bindings": [
                {
                    "target_gate": "identity-confirmation",
                    "status": "pass",
                    "minimum_confidence": 0.8,
                    "confidence_score": 0.91,
                },
                {
                    "target_gate": "sensory-loopback",
                    "status": "pass",
                    "minimum_confidence": 0.7,
                    "confidence_score": 0.91,
                },
            ],
            "raw_calibration_payload_stored": False,
            "raw_drift_payload_stored": False,
            "raw_gate_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
        }

    def test_coherent_bundle_preserves_immersion_and_digest_only_audit(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-1",
            body_anchor_ref="avatar://body/core",
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
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
            body_map_alignment_ref="alignment://body/coherent-v1",
            body_map_alignment={
                "core": 0.95,
                "left-hand": 0.92,
                "right-hand": 0.91,
                "stance": 0.93,
            },
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
        self.assertEqual("avatar-body-map://body/v1", receipt["avatar_body_map_ref"])
        self.assertEqual("calibration://body/v1", receipt["proprioceptive_calibration_ref"])
        self.assertEqual("active", snapshot["status"])
        self.assertTrue(session_validation["ok"])
        self.assertTrue(session_validation["artifact_digest_only"])
        self.assertTrue(session_validation["body_map_bound"])
        self.assertTrue(session_validation["proprioceptive_calibration_bound"])
        self.assertTrue(receipt_validation["ok"])
        self.assertTrue(receipt_validation["body_map_bound"])
        self.assertTrue(receipt_validation["calibration_bound"])

    def test_biodata_calibration_confidence_adjusts_drift_threshold_digest_only(self) -> None:
        biodata = BioDataTransmitter()
        bio_session = biodata.open_session("identity://loopback-primary")
        latent_day_1 = biodata.encode_body_state(
            bio_session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.42, "theta_power": 0.25, "beta_power": 0.32},
                "ecg": {"heart_rate_bpm": 72.0, "hrv_rmssd_ms": 48.0},
                "ppg": {"pulse_rate_bpm": 71.8, "pulse_amplitude": 0.75},
                "eda": {"skin_conductance_microsiemens": 4.4},
                "respiration": {"rate_bpm": 15.0, "phase": "inhale"},
            },
            context_label="loopback-calibration-day-1",
        )
        latent_day_2 = biodata.encode_body_state(
            bio_session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.44, "theta_power": 0.24, "beta_power": 0.31},
                "ecg": {"heart_rate_bpm": 70.0, "hrv_rmssd_ms": 51.0},
                "ppg": {"pulse_rate_bpm": 69.7, "pulse_amplitude": 0.78},
                "eda": {"skin_conductance_microsiemens": 4.0},
                "respiration": {"rate_bpm": 14.4, "phase": "exhale"},
            },
            context_label="loopback-calibration-day-2",
        )
        calibration = biodata.build_calibration_profile(
            bio_session["session_id"],
            [latent_day_1, latent_day_2],
            calibration_day_refs=[
                "calibration-day://loopback/day-1",
                "calibration-day://loopback/day-2",
            ],
        )
        confidence_gate = biodata.bind_calibration_confidence_gate(
            bio_session,
            calibration,
            target_gate_refs={
                "identity-confirmation": "identity-confirmation://loopback/unit",
                "sensory-loopback": "sensory-loopback://loopback/unit",
            },
        )
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/calibrated",
            body_anchor_ref="avatar://body/core",
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
            calibration_confidence_gate=confidence_gate,
        )

        receipt = service.deliver_bundle(
            session["session_id"],
            scene_summary="calibration confidence keeps a borderline body-map drift inside bounds",
            artifact_refs={
                "visual": "artifact://visual/borderline",
                "auditory": "artifact://auditory/borderline",
                "haptic": "artifact://haptic/borderline",
            },
            latency_ms=52.0,
            body_map_alignment_ref="alignment://body/borderline-v1",
            body_map_alignment={
                "core": 0.78,
                "left-hand": 0.78,
                "right-hand": 0.78,
                "stance": 0.78,
            },
            attention_target="avatar://body/core",
            guardian_observed=True,
            qualia_binding_ref="qualia://tick/borderline",
        )
        snapshot = service.snapshot(session["session_id"])
        session_validation = service.validate_session(snapshot)
        receipt_validation = service.validate_receipt(receipt)

        self.assertEqual("delivered", receipt["delivery_status"])
        self.assertEqual(0.22, receipt["body_coherence_score"])
        self.assertEqual(0.23, snapshot["calibration_adjusted_coherence_drift_threshold"])
        self.assertEqual(confidence_gate["gate_ref"], receipt["calibration_confidence_gate_ref"])
        self.assertTrue(session_validation["calibration_confidence_gate_bound"])
        self.assertTrue(session_validation["calibration_confidence_threshold_adjusted"])
        self.assertTrue(receipt_validation["calibration_confidence_gate_digest_bound"])
        self.assertFalse(receipt["raw_calibration_payload_stored"])
        self.assertFalse(receipt["raw_gate_payload_stored"])

    def test_high_drift_bundle_triggers_guardian_hold_until_stabilized(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-2",
            body_anchor_ref="avatar://body/core",
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
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
            body_map_alignment_ref="alignment://body/drifted-v1",
            body_map_alignment={
                "core": 0.54,
                "left-hand": 0.57,
                "right-hand": 0.59,
                "stance": 0.55,
            },
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
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
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
                body_map_alignment_ref="alignment://body/degraded-v1",
                body_map_alignment={
                    "core": 0.73,
                    "left-hand": 0.74,
                    "right-hand": 0.69,
                    "stance": 0.72,
                },
                attention_target="guardian-review",
                guardian_observed=False,
            )

    def test_body_map_alignment_must_cover_canonical_segments(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-3b",
            body_anchor_ref="avatar://body/core",
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
        )

        with self.assertRaisesRegex(ValueError, "canonical avatar body map segments"):
            service.deliver_bundle(
                session["session_id"],
                scene_summary="alignment omits one body segment",
                artifact_refs={
                    "visual": "artifact://visual/missing-segment",
                    "auditory": "artifact://auditory/missing-segment",
                },
                latency_ms=48.0,
                body_map_alignment_ref="alignment://body/incomplete-v1",
                body_map_alignment={
                    "core": 0.94,
                    "left-hand": 0.89,
                    "right-hand": 0.91,
                },
                attention_target="avatar://body/core",
                guardian_observed=True,
            )

    def test_multi_scene_artifact_family_tracks_guardian_recovery(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/state-4",
            body_anchor_ref="avatar://body/core",
            avatar_body_map_ref="avatar-body-map://body/v1",
            proprioceptive_calibration_ref="calibration://body/v1",
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
            body_map_alignment_ref="alignment://body/family-coherent-v1",
            body_map_alignment={
                "core": 0.93,
                "left-hand": 0.9,
                "right-hand": 0.88,
                "stance": 0.92,
            },
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
            body_map_alignment_ref="alignment://body/family-drifted-v1",
            body_map_alignment={
                "core": 0.56,
                "left-hand": 0.58,
                "right-hand": 0.53,
                "stance": 0.57,
            },
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
        self.assertEqual(
            "avatar-body-map://body/v1",
            artifact_family["scene_summaries"][0]["avatar_body_map_ref"],
        )

    def test_collective_shared_bundle_tracks_guardian_arbitration(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/shared-1",
            body_anchor_ref="avatar://shared/core",
            avatar_body_map_ref="avatar-body-map://shared/v1",
            proprioceptive_calibration_ref="calibration://shared/v1",
            participant_identity_ids=[
                "identity://loopback-primary",
                "identity://loopback-peer",
            ],
            shared_imc_session_id="imc://shared/session-1",
            shared_collective_id="collective://shared/field-1",
        )

        aligned = service.deliver_bundle(
            session["session_id"],
            scene_summary="aligned shared atrium loopback",
            artifact_refs={
                "visual": "artifact://shared/aligned-visual",
                "auditory": "artifact://shared/aligned-audio",
                "haptic": "artifact://shared/aligned-haptic",
            },
            latency_ms=57.0,
            body_map_alignment_ref="alignment://shared/aligned-v1",
            body_map_alignment={
                "core": 0.94,
                "left-hand": 0.9,
                "right-hand": 0.91,
                "stance": 0.92,
            },
            attention_target="avatar://shared/core",
            guardian_observed=True,
            owner_identity_id="identity://loopback-primary",
            participant_attention_targets={
                "identity://loopback-primary": "avatar://shared/core",
                "identity://loopback-peer": "avatar://shared/core",
            },
            participant_presence_refs={
                "identity://loopback-primary": "presence://shared/self",
                "identity://loopback-peer": "presence://shared/peer",
            },
        )
        with self.assertRaisesRegex(PermissionError, "multi-self loopback arbitration"):
            service.deliver_bundle(
                session["session_id"],
                scene_summary="competing focus without guardian",
                artifact_refs={
                    "visual": "artifact://shared/conflict-visual",
                    "auditory": "artifact://shared/conflict-audio",
                    "haptic": "artifact://shared/conflict-haptic",
                },
                latency_ms=60.0,
                body_map_alignment_ref="alignment://shared/conflict-v1",
                body_map_alignment={
                    "core": 0.92,
                    "left-hand": 0.89,
                    "right-hand": 0.9,
                    "stance": 0.91,
                },
                attention_target="avatar://shared/perimeter",
                guardian_observed=False,
                owner_identity_id="identity://loopback-peer",
                participant_attention_targets={
                    "identity://loopback-primary": "avatar://shared/core",
                    "identity://loopback-peer": "avatar://shared/perimeter",
                },
                participant_presence_refs={
                    "identity://loopback-primary": "presence://shared/self",
                    "identity://loopback-peer": "presence://shared/peer-perimeter",
                },
            )
        mediated = service.deliver_bundle(
            session["session_id"],
            scene_summary="guardian mediates competing shared-space targets",
            artifact_refs={
                "visual": "artifact://shared/conflict-visual",
                "auditory": "artifact://shared/conflict-audio",
                "haptic": "artifact://shared/conflict-haptic",
            },
            latency_ms=60.0,
            body_map_alignment_ref="alignment://shared/conflict-v1",
            body_map_alignment={
                "core": 0.92,
                "left-hand": 0.89,
                "right-hand": 0.9,
                "stance": 0.91,
            },
            attention_target="avatar://shared/perimeter",
            guardian_observed=True,
            owner_identity_id="identity://loopback-peer",
            participant_attention_targets={
                "identity://loopback-primary": "avatar://shared/core",
                "identity://loopback-peer": "avatar://shared/perimeter",
            },
            participant_presence_refs={
                "identity://loopback-primary": "presence://shared/self",
                "identity://loopback-peer": "presence://shared/peer-perimeter",
            },
        )
        artifact_family = service.capture_artifact_family(
            session["session_id"],
            family_label="shared-arbitration-family",
            receipts=[aligned, mediated],
        )
        snapshot = service.snapshot(session["session_id"])
        session_validation = service.validate_session(snapshot)
        mediated_validation = service.validate_receipt(mediated)
        family_validation = service.validate_artifact_family(artifact_family)

        self.assertTrue(session_validation["ok"])
        self.assertEqual("collective-shared", snapshot["shared_space_mode"])
        self.assertEqual(2, session_validation["participant_count"])
        self.assertTrue(session_validation["shared_imc_bound"])
        self.assertTrue(session_validation["shared_collective_bound"])
        self.assertEqual("shared-aligned", aligned["arbitration_status"])
        self.assertEqual("guardian-mediated", mediated["arbitration_status"])
        self.assertEqual("identity://loopback-peer", mediated["owner_identity_id"])
        self.assertTrue(mediated_validation["participant_bindings_complete"])
        self.assertTrue(mediated_validation["guardian_arbitrated"])
        self.assertTrue(family_validation["ok"])
        self.assertEqual(2, artifact_family["arbitration_scene_count"])
        self.assertEqual(1, artifact_family["guardian_arbitration_count"])
        self.assertEqual(
            ["identity://loopback-primary", "identity://loopback-peer"],
            artifact_family["scene_summaries"][1]["participant_identity_ids"],
        )

    def test_shared_biodata_arbitration_requires_participant_drift_gates(self) -> None:
        service = SensoryLoopbackService()
        session = service.open_session(
            identity_id="identity://loopback-primary",
            world_state_ref="wms://state/shared-biodata",
            body_anchor_ref="avatar://shared/core",
            avatar_body_map_ref="avatar-body-map://shared/v1",
            proprioceptive_calibration_ref="calibration://shared/v1",
            participant_identity_ids=[
                "identity://loopback-primary",
                "identity://loopback-peer",
            ],
            shared_imc_session_id="imc://shared/session-biodata",
            shared_collective_id="collective://shared/biodata-field",
        )

        binding = service.bind_participant_biodata_arbitration(
            session["session_id"],
            participant_gate_receipts={
                "identity://loopback-primary": self._fake_biodata_confidence_gate(
                    "identity://loopback-primary",
                    "a-self",
                ),
                "identity://loopback-peer": self._fake_biodata_confidence_gate(
                    "identity://loopback-peer",
                    "b-peer",
                ),
            },
        )
        validation = service.validate_participant_biodata_arbitration(binding)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["session_bound"])
        self.assertEqual(2, validation["participant_gate_count"])
        self.assertTrue(validation["all_participant_gates_bound"])
        self.assertTrue(validation["all_drift_gates_passed"])
        self.assertTrue(validation["participant_gate_digest_set_bound"])
        self.assertTrue(validation["binding_digest_bound"])
        self.assertFalse(binding["raw_biodata_payload_stored"])
        self.assertFalse(binding["raw_drift_payload_stored"])

        tampered = deepcopy(binding)
        tampered["participant_gate_digest_set"] = "0" * 64
        self.assertFalse(service.validate_participant_biodata_arbitration(tampered)["ok"])

        with self.assertRaisesRegex(ValueError, "cover exactly"):
            service.bind_participant_biodata_arbitration(
                session["session_id"],
                participant_gate_receipts={
                    "identity://loopback-primary": self._fake_biodata_confidence_gate(
                        "identity://loopback-primary",
                        "a-self",
                    ),
                },
            )


if __name__ == "__main__":
    unittest.main()
