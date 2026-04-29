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
