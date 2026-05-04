from __future__ import annotations

from copy import deepcopy
import unittest

from omoikane.interface.biodata_transmitter import BioDataTransmitter


class BioDataTransmitterTests(unittest.TestCase):
    def test_human_biosignal_catalog_is_digest_bound(self) -> None:
        transmitter = BioDataTransmitter()

        catalog = transmitter.human_biosignal_catalog()
        validation = transmitter.validate_human_biosignal_catalog(catalog)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["catalog_digest_bound"])
        self.assertTrue(validation["family_coverage_bound"])
        self.assertTrue(validation["alias_targets_bound"])
        self.assertTrue(validation["uncatalogued_modality_policy_bound"])
        self.assertGreaterEqual(catalog["family_count"], 20)
        self.assertGreaterEqual(catalog["modality_count"], 90)
        for family in (
            "neural_electrical",
            "cardiac_electrical",
            "respiratory_gas_exchange",
            "muscle_peripheral",
            "ocular",
            "vascular_flow_perfusion",
            "pressure_fluid",
            "molecular_omics",
        ):
            self.assertIn(family, catalog["modality_families"])
        for modality in (
            "eeg",
            "ecg",
            "spo2",
            "blood_pressure",
            "intracranial_pressure",
            "urine_output",
            "dna_variant_profile",
            "metabolomics",
        ):
            self.assertIn(modality, catalog["known_modalities"])

        tampered = deepcopy(catalog)
        tampered["alias_map"]["glucose"] = "interstitial_glucose"
        self.assertFalse(transmitter.validate_human_biosignal_catalog(tampered)["ok"])

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
        self.assertTrue(validation["source_modality_projections_bound"])
        self.assertTrue(validation["human_biosignal_catalog_bound"])
        self.assertTrue(validation["target_modalities_generated"])
        self.assertFalse(validation["semantic_thought_content_generated"])
        self.assertFalse(validation["subjective_equivalence_claimed"])
        self.assertEqual(
            "internal-body-state-latent",
            validation["intermediate_representation"],
        )
        self.assertEqual(1.0, latent["interoceptive_confidence"])
        self.assertIn("ecg", latent["source_modality_projections"])
        self.assertIn("thought", bundle["signals"])
        self.assertFalse(bundle["signals"]["thought"]["semantic_content_generated"])
        self.assertEqual("not-generated://thought-content", bundle["signals"]["thought"]["content_ref"])

    def test_open_biosignal_modalities_roundtrip_through_generic_projection(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session(
            "identity-bdt-open-modalities",
            source_modalities=[
                "eeg",
                "ecg",
                "ppg",
                "eda",
                "respiration",
                "emg",
                "skin_temperature",
                "3-lead ECG",
                "SpO2",
                "fMRI BOLD",
                "pupil diameter",
                "voice acoustics",
                "blood glucose",
                "novel human biosensor",
            ],
            target_modalities=[
                "ecg",
                "eda",
                "emg",
                "skin_temperature",
                "blood_pressure",
                "3-lead ECG",
                "SpO2",
                "fMRI BOLD",
                "pupil diameter",
                "voice acoustics",
                "blood glucose",
                "novel human biosensor",
                "thought",
            ],
        )
        latent = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.4, "theta_power": 0.3, "beta_power": 0.35},
                "ecg": {"heart_rate_bpm": 74.0, "hrv_rmssd_ms": 48.0},
                "ppg": {"pulse_rate_bpm": 73.8, "pulse_amplitude": 0.7},
                "eda": {"skin_conductance_microsiemens": 4.8},
                "respiration": {"rate_bpm": 15.5, "phase": "exhale"},
                "emg": {"rms_microvolt": 21.0, "median_frequency_hz": 88.0},
                "skin_temperature": {"temperature_c": 36.3, "distal_gradient_c": 0.5},
                "3-lead ECG": {"lead_i_quality": 0.92, "lead_ii_quality": 0.89},
                "SpO2": {"oxygen_saturation_percent": 98.0, "signal_quality": 0.95},
                "fMRI BOLD": {"bold_percent_change": 0.8, "roi_count": 4.0},
                "pupil diameter": {"left_pupil_mm": 3.1, "right_pupil_mm": 3.0},
                "voice acoustics": {
                    "fundamental_frequency_hz": 146.0,
                    "jitter_percent": 0.8,
                    "speaking_state": "quiet",
                },
                "blood glucose": {"glucose_mg_dl": 94.0, "trend": "stable"},
                "novel human biosensor": {"vendor_feature_a": 0.44},
            },
            context_label="unit-test-open-biosignal-roundtrip",
        )
        bundle = transmitter.generate_biosignal_bundle(session["session_id"], latent)
        validation = transmitter.validate_transmission(session, latent, bundle)

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["source_modality_projections_bound"])
        self.assertTrue(validation["human_biosignal_catalog_bound"])
        self.assertEqual(1.0, latent["interoceptive_confidence"])
        self.assertEqual(set(session["source_modalities"]), set(latent["source_modalities"]))
        self.assertEqual(
            "human-biosignal-open-modality-catalog-v1",
            session["modality_policy_id"],
        )
        self.assertEqual(
            "cardiac_electrical",
            session["source_modality_families"]["3lead_ecg"],
        )
        self.assertEqual(
            "respiratory_gas_exchange",
            session["source_modality_families"]["spo2"],
        )
        self.assertEqual(
            "neurovascular_optical_mri",
            session["source_modality_families"]["fmri_bold"],
        )
        self.assertEqual(
            "uncatalogued_human_biosignal",
            session["source_modality_families"]["novel-human-biosensor"],
        )
        self.assertIn("emg", latent["source_modality_projections"])
        self.assertIn("skin_temperature", latent["source_modality_projections"])
        self.assertIn("3lead_ecg", latent["source_modality_projections"])
        self.assertIn("spo2", latent["source_modality_projections"])
        self.assertIn("fmri_bold", latent["source_modality_projections"])
        self.assertIn("novel-human-biosensor", latent["source_modality_projections"])
        self.assertEqual(
            "catalogued",
            latent["source_modality_projections"]["fmri_bold"]["catalog_status"],
        )
        self.assertEqual(
            "uncatalogued",
            latent["source_modality_projections"]["novel-human-biosensor"][
                "catalog_status"
            ],
        )
        self.assertIn("blood_pressure", bundle["signals"])
        self.assertEqual(
            "generic-feature-summary-to-biosignal-proxy-v1",
            bundle["signals"]["blood_pressure"]["generator_policy"],
        )
        self.assertEqual(
            "cardiac_mechanical_hemodynamic",
            bundle["signals"]["blood_pressure"]["target_modality_family"],
        )
        self.assertFalse(bundle["signals"]["blood_pressure"]["semantic_content_generated"])
        self.assertIn("emg", bundle["signals"])
        self.assertIn("skin_temperature", bundle["signals"])
        self.assertIn("spo2", bundle["signals"])
        self.assertIn("fmri_bold", bundle["signals"])
        self.assertEqual(
            "uncatalogued",
            bundle["signals"]["novel-human-biosensor"]["catalog_status"],
        )
        self.assertTrue(validation["target_modalities_generated"])

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

    def test_binds_survey_score_summary_to_eeg_feature_window(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session(
            "identity-bdt-survey-eeg",
            source_modalities=["eeg"],
            target_modalities=["eeg", "affect", "thought"],
        )
        dataset_manifest = {
            "dataset_ref": "dataset://unit/survey-eeg-window",
            "participant_ref": "participant://unit/survey-eeg-self",
            "license_ref": "license://unit/redacted-survey-eeg-summary",
            "window_ref": "window://unit/survey-eeg/day-1",
            "modality_file_refs": {
                "eeg": "dataset-file://unit/survey-eeg/eeg-window-summary",
            },
        }
        adapted = transmitter.adapt_dataset_feature_window(
            session["session_id"],
            dataset_manifest=dataset_manifest,
            window_feature_summaries={
                "eeg": {"alpha_power": 0.39, "theta_power": 0.28, "beta_power": 0.34},
            },
            context_label="survey-eeg-unit-window",
        )

        fusion = transmitter.bind_survey_eeg_window_fusion(
            session,
            adapted["adapter_receipt"],
            adapted["latent_state"],
            survey_instrument_manifest={
                "instrument_ref": "survey://unit/affect-attention-v1",
                "administration_ref": "survey-admin://unit/day-1",
                "participant_ref": "participant://unit/survey-eeg-self",
                "language": "ja-JP",
                "scale_refs": {
                    "valence": "scale://unit/valence",
                    "arousal": "scale://unit/arousal",
                    "attention": "scale://unit/attention",
                    "fatigue": "scale://unit/fatigue",
                },
            },
            survey_score_summary={
                "valence": 0.57,
                "arousal": 0.61,
                "attention": 0.66,
                "fatigue": 0.26,
            },
            alignment_evidence_refs=[
                "alignment://unit/survey-eeg/same-window",
                "consent://unit/survey-eeg/fusion",
            ],
            analysis_question="bounded survey and EEG attention-window analysis",
            operator_intent_ref="operator-intent://unit/no-ml-survey-eeg",
        )
        validation = transmitter.validate_survey_eeg_window_fusion(
            session,
            adapted["adapter_receipt"],
            adapted["latent_state"],
            fusion,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual("bound", validation["fusion_status"])
        self.assertTrue(validation["eeg_window_bound"])
        self.assertTrue(validation["survey_window_bound"])
        self.assertTrue(validation["alignment_evidence_digest_bound"])
        self.assertTrue(validation["alignment_checks_bound"])
        self.assertTrue(validation["fused_window_digest_bound"])
        self.assertTrue(validation["fusion_receipt_digest_bound"])
        self.assertTrue(validation["operator_accessibility_bound"])
        self.assertEqual(
            "survey-eeg-correlation-input-only",
            fusion["claim_ceiling"],
        )
        self.assertFalse(fusion["raw_survey_response_payload_stored"])
        self.assertFalse(fusion["raw_eeg_samples_stored"])
        self.assertFalse(fusion["diagnosis_claimed"])
        self.assertFalse(fusion["semantic_thought_content_generated"])

        tampered = deepcopy(fusion)
        tampered["survey_score_digest"] = "0" * 64
        self.assertFalse(
            transmitter.validate_survey_eeg_window_fusion(
                session,
                adapted["adapter_receipt"],
                adapted["latent_state"],
                tampered,
            )["ok"]
        )

        with self.assertRaisesRegex(ValueError, "requires at least two comparable"):
            transmitter.bind_survey_eeg_window_fusion(
                session,
                adapted["adapter_receipt"],
                adapted["latent_state"],
                survey_instrument_manifest={
                    "instrument_ref": "survey://unit/non-comparable-v1",
                    "administration_ref": "survey-admin://unit/non-comparable",
                    "participant_ref": "participant://unit/survey-eeg-self",
                    "language": "ja-JP",
                    "scale_refs": {"sleep_quality": "scale://unit/sleep"},
                },
                survey_score_summary={
                    "sleep_quality": 0.7,
                    "motivation": 0.5,
                },
                alignment_evidence_refs=[
                    "alignment://unit/non-comparable",
                    "consent://unit/non-comparable",
                ],
                analysis_question="non-comparable survey axes",
                operator_intent_ref="operator-intent://unit/non-comparable",
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

        phase_refs = [
            "circadian-phase://unit/day-1/evening",
            "circadian-phase://unit/day-2/morning",
        ]
        phase_verifier = transmitter.bind_circadian_phase_verifier(
            session,
            phase_refs,
            [
                {
                    "source_type": "external-clock",
                    "source_ref": "clock://unit/lab-clock",
                    "evidence_ref": "clock-evidence://unit/phase-digest",
                    "verifier_key_ref": "verifier-key://unit/lab-clock",
                },
                {
                    "source_type": "sleep-diary",
                    "source_ref": "sleep-diary://unit/redacted-diary",
                    "evidence_ref": "sleep-diary-evidence://unit/phase-entry",
                    "verifier_key_ref": "verifier-key://unit/sleep-diary",
                },
                {
                    "source_type": "wearable",
                    "source_ref": "wearable://unit/actigraphy",
                    "evidence_ref": "wearable-evidence://unit/phase-epoch",
                    "verifier_key_ref": "verifier-key://unit/wearable",
                },
            ],
        )
        verifier_validation = transmitter.validate_circadian_phase_verifier(
            session,
            phase_refs,
            phase_verifier,
        )
        series = transmitter.build_feature_window_series_profile(
            session,
            [day_one["adapter_receipt"], day_two["adapter_receipt"]],
            [day_one["latent_state"], day_two["latent_state"]],
            phase_refs,
            phase_verifier,
        )
        validation = transmitter.validate_feature_window_series_profile(
            session,
            [day_one["adapter_receipt"], day_two["adapter_receipt"]],
            [day_one["latent_state"], day_two["latent_state"]],
            series,
            phase_verifier,
        )

        self.assertTrue(verifier_validation["ok"])
        self.assertTrue(verifier_validation["phase_ref_digest_set_bound"])
        self.assertTrue(verifier_validation["verifier_source_digest_set_bound"])
        self.assertTrue(verifier_validation["phase_verifier_digest_bound"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["series_digest_set_bound"])
        self.assertTrue(validation["series_profile_digest_bound"])
        self.assertTrue(validation["adapter_receipt_digest_set_bound"])
        self.assertTrue(validation["latent_digest_set_bound"])
        self.assertTrue(validation["required_modalities_bound"])
        self.assertTrue(validation["circadian_profile_bound"])
        self.assertTrue(validation["circadian_phase_verifier_bound"])
        self.assertTrue(validation["circadian_phase_verifier_digest_bound"])
        self.assertTrue(validation["axis_drift_summary_bound"])
        self.assertEqual(2, series["window_count"])
        self.assertEqual(
            "decreased",
            series["axis_drift_summary"]["heart_rate_bpm"]["direction"],
        )
        self.assertFalse(phase_verifier["raw_verifier_payload_stored"])
        self.assertFalse(series["raw_series_payload_stored"])
        self.assertFalse(series["raw_phase_verifier_payload_stored"])
        self.assertFalse(series["raw_latent_payload_stored"])

        calibration = transmitter.build_calibration_profile(
            session["session_id"],
            [day_one["latent_state"], day_two["latent_state"]],
            [
                "calibration-day://unit/series-day-1",
                "calibration-day://unit/series-day-2",
            ],
        )
        threshold_authority = transmitter.bind_drift_threshold_policy_authority(
            session,
            [
                {
                    "authority_role": "clinical-reviewer",
                    "authority_ref": "clinical-reviewer://unit/threshold-review",
                    "policy_ref": "threshold-policy://unit/clinical",
                    "signer_key_ref": "signer-key://unit/clinical",
                    "signature_ref": "signature://unit/clinical-threshold",
                    "jurisdiction": "JP-13",
                },
                {
                    "authority_role": "jurisdiction-policy",
                    "authority_ref": "jurisdiction-policy://unit/jp-13",
                    "policy_ref": "threshold-policy://unit/jurisdiction",
                    "signer_key_ref": "signer-key://unit/jurisdiction",
                    "signature_ref": "signature://unit/jurisdiction-threshold",
                    "jurisdiction": "JP-13",
                },
                {
                    "authority_role": "guardian",
                    "authority_ref": "guardian://unit/integrity",
                    "policy_ref": "threshold-policy://unit/guardian",
                    "signer_key_ref": "signer-key://unit/guardian",
                    "signature_ref": "signature://unit/guardian-threshold",
                    "jurisdiction": "project-guardian",
                },
            ],
        )
        threshold_authority_validation = (
            transmitter.validate_drift_threshold_policy_authority(
                session,
                None,
                threshold_authority,
            )
        )
        drift_gate = transmitter.bind_feature_window_series_drift_gate(
            session,
            series,
            calibration,
            threshold_policy_authority_receipt=threshold_authority,
        )
        drift_validation = transmitter.validate_feature_window_series_drift_gate(
            session,
            series,
            calibration,
            drift_gate,
            threshold_authority,
        )
        refresh_receipt = transmitter.bind_calibration_refresh_receipt(
            session,
            calibration,
            drift_gate,
            [
                {
                    "source_type": "current-drift-gate",
                    "source_ref": drift_gate["drift_gate_ref"],
                    "evidence_ref": "drift-gate-evidence://unit/current-pass",
                    "verifier_key_ref": "verifier-key://unit/drift-gate",
                    "freshness_status_ref": "freshness://unit/current-drift-gate/fresh",
                },
                {
                    "source_type": "self-consent",
                    "source_ref": "self-consent://unit/calibration-refresh",
                    "evidence_ref": "consent-evidence://unit/calibration-refresh",
                    "verifier_key_ref": "verifier-key://unit/self-consent",
                    "freshness_status_ref": "freshness://unit/self-consent/fresh",
                },
                {
                    "source_type": "guardian-review",
                    "source_ref": "guardian-review://unit/calibration-refresh",
                    "evidence_ref": "guardian-evidence://unit/calibration-refresh",
                    "verifier_key_ref": "verifier-key://unit/guardian",
                    "freshness_status_ref": "freshness://unit/guardian-review/fresh",
                },
            ],
        )
        refresh_validation = transmitter.validate_calibration_refresh_receipt(
            session,
            calibration,
            drift_gate,
            refresh_receipt,
        )
        confidence_gate = transmitter.bind_calibration_confidence_gate(
            session,
            calibration,
            {
                "identity-confirmation": "identity-confirmation://unit/series",
                "sensory-loopback": "sensory-loopback://unit/series",
            },
            feature_window_series_drift_gate_receipt=drift_gate,
            calibration_refresh_receipt=refresh_receipt,
        )
        confidence_validation = transmitter.validate_calibration_confidence_gate(
            session,
            calibration,
            confidence_gate,
        )

        self.assertTrue(threshold_authority_validation["ok"])
        self.assertTrue(threshold_authority_validation["axis_threshold_digest_bound"])
        self.assertTrue(
            threshold_authority_validation["authority_source_digest_set_bound"]
        )
        self.assertTrue(
            threshold_authority_validation["required_authority_roles_bound"]
        )
        self.assertTrue(
            threshold_authority_validation["authority_receipt_digest_bound"]
        )
        self.assertTrue(drift_validation["ok"])
        self.assertEqual("pass", drift_gate["drift_gate_status"])
        self.assertTrue(drift_validation["series_profile_bound"])
        self.assertTrue(drift_validation["calibration_profile_bound"])
        self.assertTrue(drift_validation["series_calibration_latent_set_bound"])
        self.assertTrue(drift_validation["drift_threshold_digest_bound"])
        self.assertTrue(drift_validation["drift_gate_digest_bound"])
        self.assertTrue(drift_validation["threshold_policy_authority_bound"])
        self.assertTrue(drift_validation["threshold_policy_authority_digest_bound"])
        self.assertTrue(
            drift_validation["threshold_policy_source_digest_set_bound"]
        )
        self.assertTrue(refresh_validation["ok"])
        self.assertTrue(refresh_validation["calibration_profile_bound"])
        self.assertTrue(refresh_validation["feature_window_series_drift_gate_bound"])
        self.assertTrue(refresh_validation["threshold_policy_authority_digest_bound"])
        self.assertTrue(refresh_validation["refresh_window_bound"])
        self.assertTrue(refresh_validation["refresh_source_digest_set_bound"])
        self.assertTrue(refresh_validation["refresh_receipt_digest_bound"])
        self.assertFalse(refresh_receipt["raw_refresh_payload_stored"])
        self.assertFalse(drift_gate["raw_drift_payload_stored"])
        self.assertFalse(threshold_authority["raw_threshold_policy_payload_stored"])
        self.assertFalse(
            threshold_authority["raw_threshold_policy_signature_payload_stored"]
        )
        self.assertTrue(confidence_validation["ok"])
        self.assertTrue(confidence_validation["feature_window_series_drift_gate_bound"])
        self.assertTrue(
            confidence_validation[
                "feature_window_series_threshold_policy_authority_bound"
            ]
        )
        self.assertEqual(
            "pass",
            confidence_validation["feature_window_series_drift_gate_status"],
        )
        self.assertTrue(confidence_validation["calibration_refresh_bound"])
        self.assertEqual("fresh", confidence_validation["calibration_refresh_status"])
        self.assertTrue(confidence_validation["calibration_refresh_window_bound"])

        tampered = dict(series)
        tampered["series_digest_set_digest"] = "0" * 64
        self.assertFalse(
            transmitter.validate_feature_window_series_profile(
                session,
                [day_one["adapter_receipt"], day_two["adapter_receipt"]],
                [day_one["latent_state"], day_two["latent_state"]],
                tampered,
                phase_verifier,
            )["ok"]
        )
        tampered_verifier = dict(phase_verifier)
        tampered_verifier["phase_ref_digest_set"] = "0" * 64
        self.assertFalse(
            transmitter.validate_circadian_phase_verifier(
                session,
                phase_refs,
                tampered_verifier,
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
                threshold_authority,
            )["ok"]
        )
        tampered_authority = dict(threshold_authority)
        tampered_authority["authority_source_digest_set"] = "0" * 64
        self.assertFalse(
            transmitter.validate_drift_threshold_policy_authority(
                session,
                None,
                tampered_authority,
            )["ok"]
        )
        tampered_refresh = dict(refresh_receipt)
        tampered_refresh["refresh_status"] = "expired"
        self.assertFalse(
            transmitter.validate_calibration_refresh_receipt(
                session,
                calibration,
                drift_gate,
                tampered_refresh,
            )["ok"]
        )
        with self.assertRaisesRegex(ValueError, "calibration_refresh_receipt is invalid"):
            transmitter.bind_calibration_confidence_gate(
                session,
                calibration,
                {
                    "identity-confirmation": "identity-confirmation://unit/expired-refresh",
                    "sensory-loopback": "sensory-loopback://unit/expired-refresh",
                },
                feature_window_series_drift_gate_receipt=drift_gate,
                calibration_refresh_receipt=tampered_refresh,
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

    def test_binds_biodata_latent_to_mind_state_bridge_without_consciousness_claim(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-mind-state-bridge")
        latent_day_one = transmitter.encode_body_state(
            session["session_id"],
            biosignal_features={
                "eeg": {"alpha_power": 0.38, "theta_power": 0.29, "beta_power": 0.34},
                "ecg": {"heart_rate_bpm": 76.0, "hrv_rmssd_ms": 44.0},
                "ppg": {"pulse_rate_bpm": 75.6, "pulse_amplitude": 0.71},
                "eda": {"skin_conductance_microsiemens": 5.2},
                "respiration": {"rate_bpm": 16.2, "phase": "exhale"},
            },
            context_label="mind-state-bridge-day-one",
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
            context_label="mind-state-bridge-day-two",
        )
        generated_bundle = transmitter.generate_biosignal_bundle(
            session["session_id"],
            latent_day_one,
        )
        calibration = transmitter.build_calibration_profile(
            session["session_id"],
            [latent_day_one, latent_day_two],
            [
                "calibration-day://unit/bridge-day-1",
                "calibration-day://unit/bridge-day-2",
            ],
        )
        gate = transmitter.bind_calibration_confidence_gate(
            session,
            calibration,
            {
                "identity-confirmation": "identity-confirmation://unit/bridge",
                "sensory-loopback": "sensory-loopback://unit/bridge",
            },
        )

        bridge = transmitter.bind_mind_state_bridge(
            session,
            latent_day_one,
            generated_bundle,
            calibration,
            gate,
        )
        validation = transmitter.validate_mind_state_bridge(
            session,
            latent_day_one,
            generated_bundle,
            calibration,
            gate,
            bridge,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual("bound", bridge["mind_state_handoff_status"])
        self.assertEqual("body-state-surrogate-input-only", bridge["claim_ceiling"])
        self.assertTrue(validation["body_state_latent_bound"])
        self.assertTrue(validation["generated_bundle_bound"])
        self.assertTrue(validation["calibration_confidence_gate_bound"])
        self.assertTrue(validation["qualia_surrogate_bound"])
        self.assertTrue(validation["self_model_advisory_bound"])
        self.assertTrue(validation["l2_l3_handoffs_bound"])
        self.assertTrue(validation["claim_ceiling_bound"])
        self.assertTrue(validation["bridge_digest_bound"])
        self.assertEqual(4, len(bridge["qualia_surrogate_axis_refs"]))
        self.assertEqual(6, len(bridge["l2_l3_handoff_bindings"]))
        self.assertFalse(bridge["raw_biodata_payload_stored"])
        self.assertFalse(bridge["semantic_thought_content_generated"])
        self.assertFalse(bridge["subjective_equivalence_claimed"])
        self.assertFalse(bridge["consciousness_reproduction_claimed"])
        self.assertFalse(bridge["identity_replacement_claimed"])

        tampered = deepcopy(bridge)
        tampered["consciousness_reproduction_claimed"] = True
        self.assertFalse(
            transmitter.validate_mind_state_bridge(
                session,
                latent_day_one,
                generated_bundle,
                calibration,
                gate,
                tampered,
            )["ok"]
        )
        tampered_digest = deepcopy(bridge)
        tampered_digest["l2_l3_handoff_digest_set"] = "0" * 64
        self.assertFalse(
            transmitter.validate_mind_state_bridge(
                session,
                latent_day_one,
                generated_bundle,
                calibration,
                gate,
                tampered_digest,
            )["ok"]
        )

    def test_normalizes_open_modality_and_rejects_mismatched_latent(self) -> None:
        transmitter = BioDataTransmitter()
        session = transmitter.open_session("identity-bdt-2")

        custom_session = transmitter.open_session(
            "identity-bdt-3",
            source_modalities=["fMRI"],
            target_modalities=["fMRI", "blood_pressure"],
        )
        self.assertEqual(["fmri_bold"], custom_session["source_modalities"])
        self.assertEqual(
            ["fmri_bold", "blood_pressure"],
            custom_session["target_modalities"],
        )
        self.assertEqual(
            "neurovascular_optical_mri",
            custom_session["source_modality_families"]["fmri_bold"],
        )

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
