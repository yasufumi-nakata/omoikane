from __future__ import annotations

import unittest

from omoikane.interface.biodata_transmitter import BioDataTransmitter


class BioDataTransmitterTests(unittest.TestCase):
    def test_encodes_body_state_and_generates_target_modalities(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session(
            "identity-bdt-1",
            source_modalities=["eeg", "ecg", "ppg", "eda", "respiration"],
            target_modalities=["ecg", "ppg", "respiration", "eeg", "affect", "thought"],
        )

        latent = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.4, "theta_power": 0.3, "beta_power": 0.35},
                "ecg": {"heart_rate_bpm": 74.0, "hrv_rmssd_ms": 48.0},
                "ppg": {"pulse_rate_bpm": 73.8, "pulse_amplitude": 0.7},
                "eda": {"skin_conductance_microsiemens": 4.8},
                "respiration": {"rate_bpm": 15.5, "phase": "exhale"},
            },
            context_label="unit-test-biosignal-roundtrip",
        )
        bundle = transmitter.generate_biosignal_bundle(session["session_id"], latent)
        validation = transmitter.validate_transmission(session, latent, bundle)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["literature_backed_intermediate"])
        self.assertTrue(validation["mind_upload_conflict_sink_bound"])
        self.assertTrue(validation["target_modalities_generated"])
        self.assertFalse(validation["semantic_thought_content_generated"])
        self.assertFalse(validation["subjective_equivalence_claimed"])
        self.assertEqual(
            "internal-body-state-latent",
            validation["intermediate_representation"],
        )
        self.assertEqual(1.0, latent["interoceptive_confidence"])
        self.assertIn("thought", bundle["signals"])
        self.assertFalse(bundle["signals"]["thought"]["semantic_content_generated"])
        self.assertEqual("not-generated://thought-content", bundle["signals"]["thought"]["content_ref"])

    def test_builds_multi_day_calibration_profile_without_raw_payloads(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-calibration")
        latent_day_one = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "ecg": {"heart_rate_bpm": 76.0, "hrv_rmssd_ms": 44.0},
                "eeg": {"alpha_power": 0.38, "theta_power": 0.29, "beta_power": 0.34},
                "respiration": {"rate_bpm": 16.2, "phase": "exhale"},
            },
            context_label="calibration-day-one",
        )
        latent_day_two = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "ecg": {"heart_rate_bpm": 72.0, "hrv_rmssd_ms": 49.0},
                "eeg": {"alpha_power": 0.43, "theta_power": 0.25, "beta_power": 0.32},
                "respiration": {"rate_bpm": 14.8, "phase": "inhale"},
            },
            context_label="calibration-day-two",
        )

        calibration = transmitter.build_calibration_profile(
            session["session_id"],
            [latent_day_one, latent_day_two],
            [
                "calibration-day://unit/day-1",
                "calibration-day://unit/day-2",
            ],
        )
        validation = transmitter.validate_calibration_profile(
            session,
            [latent_day_one, latent_day_two],
            calibration,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["multi_day_calibration_bound"])
        self.assertTrue(validation["source_latent_digest_set_bound"])
        self.assertTrue(validation["calibration_digest_bound"])
        self.assertTrue(validation["axis_baselines_bound"])
        self.assertEqual(2, calibration["days_covered_count"])
        self.assertEqual(2, calibration["latent_count"])
        self.assertFalse(calibration["raw_latent_payload_stored"])
        self.assertFalse(calibration["raw_calibration_payload_stored"])
        self.assertFalse(calibration["semantic_thought_content_generated"])
        with self.assertRaisesRegex(ValueError, "at least two unique days"):
            transmitter.build_calibration_profile(
                session["session_id"],
                [latent_day_one, latent_day_two],
                [
                    "calibration-day://unit/day-1",
                    "calibration-day://unit/day-1",
                ],
            )

    def test_rejects_unknown_modality_and_mismatched_latent(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-2")

        with self.assertRaisesRegex(ValueError, "unsupported modality"):
            transmitter.open_session("identity-bdt-3", source_modalities=["fMRI"])

        other_session = transmitter.open_session("identity-bdt-4")
        latent = transmitter.encode_body_state(
            other_session["session_id"],
            biosignal_features={"ecg": {"heart_rate_bpm": 70.0, "hrv_rmssd_ms": 40.0}},
            context_label="mismatch",
        )

        with self.assertRaisesRegex(ValueError, "session_id does not match"):
            transmitter.generate_biosignal_bundle(session["session_id"], latent)


if __name__ == "__main__":
    unittest.main()
