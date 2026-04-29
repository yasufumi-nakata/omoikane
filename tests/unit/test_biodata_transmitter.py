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

    def test_adapts_dataset_feature_window_without_raw_payloads(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-dataset-adapter")
        dataset_manifest = {
            "dataset_ref": "dataset://unit/physiology-window",
            "participant_ref": "participant://unit/self",
            "license_ref": "license://unit/redacted-feature-summary",
            "window_ref": "window://unit/day-1/rest",
            "modality_file_refs": {
                "eeg": "dataset-file://unit/eeg",
                "ecg": "dataset-file://unit/ecg",
                "ppg": "dataset-file://unit/ppg",
                "eda": "dataset-file://unit/eda",
                "respiration": "dataset-file://unit/respiration",
            },
        }

        adapted = transmitter.adapt_dataset_feature_window(
            session["session_id"],
            dataset_manifest=dataset_manifest,
            window_feature_summaries={
                "eeg": {"alpha_power": 0.41, "theta_power": 0.27, "beta_power": 0.33},
                "ecg": {"heart_rate_bpm": 73.0, "hrv_rmssd_ms": 47.0},
                "ppg": {"pulse_rate_bpm": 72.7, "pulse_amplitude": 0.74},
                "eda": {"skin_conductance_microsiemens": 4.4},
                "respiration": {"rate_bpm": 15.1, "phase": "inhale"},
            },
            context_label="dataset-window-unit",
        )
        receipt = adapted["adapter_receipt"]
        latent = adapted["latent_state"]
        validation = transmitter.validate_dataset_adapter_receipt(
            session,
            dataset_manifest,
            latent,
            receipt,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["dataset_manifest_digest_bound"])
        self.assertTrue(validation["source_feature_digest_bound"])
        self.assertTrue(validation["latent_digest_bound"])
        self.assertTrue(validation["required_modalities_bound"])
        self.assertTrue(validation["adapter_receipt_digest_bound"])
        self.assertEqual(latent["latent_ref"], receipt["latent_ref"])
        self.assertFalse(receipt["raw_dataset_payload_stored"])
        self.assertFalse(receipt["raw_signal_samples_stored"])
        self.assertFalse(receipt["raw_feature_window_payload_stored"])

        tampered = dict(receipt)
        tampered["dataset_manifest_digest"] = "0" * 64
        self.assertFalse(
            transmitter.validate_dataset_adapter_receipt(
                session,
                dataset_manifest,
                latent,
                tampered,
            )["ok"]
        )
        incomplete_manifest = dict(dataset_manifest)
        incomplete_manifest["modality_file_refs"] = {
            "eeg": "dataset-file://unit/eeg",
        }
        with self.assertRaisesRegex(ValueError, "must cover observed modalities"):
            transmitter.adapt_dataset_feature_window(
                session["session_id"],
                dataset_manifest=incomplete_manifest,
                window_feature_summaries={
                    "eeg": {"alpha_power": 0.41},
                    "ecg": {"heart_rate_bpm": 73.0},
                },
                context_label="missing-manifest-ref",
            )

    def test_builds_feature_window_series_profile_from_adapter_receipts(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-feature-series")
        base_manifest = {
            "dataset_ref": "dataset://unit/physiology-window-series",
            "participant_ref": "participant://unit/self",
            "license_ref": "license://unit/redacted-feature-summary",
            "window_ref": "window://unit/day-1/evening",
            "modality_file_refs": {
                "eeg": "dataset-file://unit/day-1/eeg",
                "ecg": "dataset-file://unit/day-1/ecg",
                "ppg": "dataset-file://unit/day-1/ppg",
                "eda": "dataset-file://unit/day-1/eda",
                "respiration": "dataset-file://unit/day-1/respiration",
            },
        }
        day_one = transmitter.adapt_dataset_feature_window(
            session["session_id"],
            dataset_manifest=base_manifest,
            window_feature_summaries={
                "eeg": {"alpha_power": 0.38, "theta_power": 0.28, "beta_power": 0.35},
                "ecg": {"heart_rate_bpm": 76.0, "hrv_rmssd_ms": 44.0},
                "ppg": {"pulse_rate_bpm": 75.0, "pulse_amplitude": 0.7},
                "eda": {"skin_conductance_microsiemens": 5.1},
                "respiration": {"rate_bpm": 16.0, "phase": "exhale"},
            },
            context_label="feature-series-day-one",
        )
        day_two_manifest = dict(base_manifest)
        day_two_manifest["window_ref"] = "window://unit/day-2/morning"
        day_two_manifest["modality_file_refs"] = {
            key: value.replace("day-1", "day-2")
            for key, value in base_manifest["modality_file_refs"].items()
        }
        day_two = transmitter.adapt_dataset_feature_window(
            session["session_id"],
            dataset_manifest=day_two_manifest,
            window_feature_summaries={
                "eeg": {"alpha_power": 0.44, "theta_power": 0.24, "beta_power": 0.31},
                "ecg": {"heart_rate_bpm": 70.0, "hrv_rmssd_ms": 52.0},
                "ppg": {"pulse_rate_bpm": 70.2, "pulse_amplitude": 0.78},
                "eda": {"skin_conductance_microsiemens": 4.1},
                "respiration": {"rate_bpm": 14.0, "phase": "inhale"},
            },
            context_label="feature-series-day-two",
        )

        series = transmitter.build_feature_window_series_profile(
            session,
            [day_one["adapter_receipt"], day_two["adapter_receipt"]],
            [day_one["latent_state"], day_two["latent_state"]],
            [
                "circadian-phase://unit/day-1/evening",
                "circadian-phase://unit/day-2/morning",
            ],
        )
        validation = transmitter.validate_feature_window_series_profile(
            session,
            [day_one["adapter_receipt"], day_two["adapter_receipt"]],
            [day_one["latent_state"], day_two["latent_state"]],
            series,
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["series_digest_set_bound"])
        self.assertTrue(validation["series_profile_digest_bound"])
        self.assertTrue(validation["adapter_receipt_digest_set_bound"])
        self.assertTrue(validation["latent_digest_set_bound"])
        self.assertTrue(validation["required_modalities_bound"])
        self.assertTrue(validation["circadian_profile_bound"])
        self.assertTrue(validation["axis_drift_summary_bound"])
        self.assertEqual(2, series["window_count"])
        self.assertEqual(
            "decreased",
            series["axis_drift_summary"]["heart_rate_bpm"]["direction"],
        )
        self.assertFalse(series["raw_series_payload_stored"])
        self.assertFalse(series["raw_latent_payload_stored"])

        calibration = transmitter.build_calibration_profile(
            session["session_id"],
            [day_one["latent_state"], day_two["latent_state"]],
            [
                "calibration-day://unit/series-day-1",
                "calibration-day://unit/series-day-2",
            ],
        )
        drift_gate = transmitter.bind_feature_window_series_drift_gate(
            session,
            series,
            calibration,
        )
        drift_validation = transmitter.validate_feature_window_series_drift_gate(
            session,
            series,
            calibration,
            drift_gate,
        )
        confidence_gate = transmitter.bind_calibration_confidence_gate(
            session,
            calibration,
            {
                "identity-confirmation": "identity-confirmation://unit/series",
                "sensory-loopback": "sensory-loopback://unit/series",
            },
            feature_window_series_drift_gate_receipt=drift_gate,
        )
        confidence_validation = transmitter.validate_calibration_confidence_gate(
            session,
            calibration,
            confidence_gate,
        )

        self.assertTrue(drift_validation["ok"])
        self.assertEqual("pass", drift_gate["drift_gate_status"])
        self.assertTrue(drift_validation["series_profile_bound"])
        self.assertTrue(drift_validation["calibration_profile_bound"])
        self.assertTrue(drift_validation["series_calibration_latent_set_bound"])
        self.assertTrue(drift_validation["drift_threshold_digest_bound"])
        self.assertTrue(drift_validation["drift_gate_digest_bound"])
        self.assertFalse(drift_gate["raw_drift_payload_stored"])
        self.assertTrue(confidence_validation["ok"])
        self.assertTrue(confidence_validation["feature_window_series_drift_gate_bound"])
        self.assertEqual(
            "pass",
            confidence_validation["feature_window_series_drift_gate_status"],
        )

        tampered = dict(series)
        tampered["series_digest_set_digest"] = "0" * 64
        self.assertFalse(
            transmitter.validate_feature_window_series_profile(
                session,
                [day_one["adapter_receipt"], day_two["adapter_receipt"]],
                [day_one["latent_state"], day_two["latent_state"]],
                tampered,
            )["ok"]
        )
        with self.assertRaisesRegex(ValueError, "at least two unique phases"):
            transmitter.build_feature_window_series_profile(
                session,
                [day_one["adapter_receipt"], day_two["adapter_receipt"]],
                [day_one["latent_state"], day_two["latent_state"]],
                [
                    "circadian-phase://unit/day-1/evening",
                    "circadian-phase://unit/day-1/evening",
                ],
            )
        tampered_gate = dict(drift_gate)
        tampered_gate["drift_threshold_digest"] = "0" * 64
        self.assertFalse(
            transmitter.validate_feature_window_series_drift_gate(
                session,
                series,
                calibration,
                tampered_gate,
            )["ok"]
        )
        blocked_gate = transmitter.bind_feature_window_series_drift_gate(
            session,
            series,
            calibration,
            {"heart_rate_bpm": 1.0},
        )
        self.assertEqual("blocked", blocked_gate["drift_gate_status"])
        with self.assertRaisesRegex(ValueError, "drift_gate_receipt.drift_gate_status"):
            transmitter.bind_calibration_confidence_gate(
                session,
                calibration,
                {
                    "identity-confirmation": "identity-confirmation://unit/blocked",
                    "sensory-loopback": "sensory-loopback://unit/blocked",
                },
                feature_window_series_drift_gate_receipt=blocked_gate,
            )

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

    def test_binds_calibration_to_identity_and_loopback_confidence_gates(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-confidence-gate")
        latent_day_one = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.38, "theta_power": 0.29, "beta_power": 0.34},
                "ecg": {"heart_rate_bpm": 76.0, "hrv_rmssd_ms": 44.0},
                "ppg": {"pulse_rate_bpm": 75.6, "pulse_amplitude": 0.71},
                "eda": {"skin_conductance_microsiemens": 5.2},
                "respiration": {"rate_bpm": 16.2, "phase": "exhale"},
            },
            context_label="confidence-gate-day-one",
        )
        latent_day_two = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.43, "theta_power": 0.25, "beta_power": 0.32},
                "ecg": {"heart_rate_bpm": 72.4, "hrv_rmssd_ms": 49.0},
                "ppg": {"pulse_rate_bpm": 72.0, "pulse_amplitude": 0.76},
                "eda": {"skin_conductance_microsiemens": 4.6},
                "respiration": {"rate_bpm": 14.8, "phase": "inhale"},
            },
            context_label="confidence-gate-day-two",
        )
        calibration = transmitter.build_calibration_profile(
            session["session_id"],
            [latent_day_one, latent_day_two],
            [
                "calibration-day://unit/gate-day-1",
                "calibration-day://unit/gate-day-2",
            ],
        )

        gate = transmitter.bind_calibration_confidence_gate(
            session,
            calibration,
            {
                "identity-confirmation": "identity-confirmation://unit/ascending",
                "sensory-loopback": "sensory-loopback://unit/session",
            },
        )
        validation = transmitter.validate_calibration_confidence_gate(
            session,
            calibration,
            gate,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual("bound", gate["confidence_gate_status"])
        self.assertTrue(validation["calibration_profile_bound"])
        self.assertTrue(validation["required_modalities_bound"])
        self.assertTrue(validation["target_gate_set_digest_bound"])
        self.assertTrue(validation["gate_receipt_digest_bound"])
        self.assertTrue(validation["identity_confirmation_gate_bound"])
        self.assertTrue(validation["sensory_loopback_gate_bound"])
        self.assertFalse(gate["raw_calibration_payload_stored"])
        self.assertFalse(gate["raw_gate_payload_stored"])

        tampered = dict(gate)
        tampered["target_gate_bindings"] = [dict(item) for item in gate["target_gate_bindings"]]
        tampered["target_gate_bindings"][0]["status"] = "fail"
        tampered_validation = transmitter.validate_calibration_confidence_gate(
            session,
            calibration,
            tampered,
        )
        self.assertFalse(tampered_validation["ok"])
        self.assertFalse(tampered_validation["target_gate_set_digest_bound"])

        with self.assertRaisesRegex(ValueError, "unsupported confidence gate target"):
            transmitter.bind_calibration_confidence_gate(
                session,
                calibration,
                {"unbounded-upload": "identity-confirmation://unit/ascending"},
            )
        with self.assertRaisesRegex(ValueError, "identity-confirmation and sensory-loopback"):
            transmitter.bind_calibration_confidence_gate(
                session,
                calibration,
                {"identity-confirmation": "identity-confirmation://unit/ascending"},
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
