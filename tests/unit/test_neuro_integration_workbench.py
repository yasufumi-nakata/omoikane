from __future__ import annotations

from copy import deepcopy
import unittest

from omoikane.interface.neuro_integration_workbench import NeuroIntegrationWorkbench


class NeuroIntegrationWorkbenchTests(unittest.TestCase):
    def _build_upstream_fusion_receipt(self, identity_id: str) -> dict:
        return {
            "profile_id": "biodata-survey-eeg-window-fusion-v1",
            "identity_id": identity_id,
            "fusion_ref": "survey-eeg-fusion://biodata/bdt-survey-eeg-fusion-111111111111",
            "fusion_receipt_digest": "a" * 64,
            "fused_window_digest": "b" * 64,
            "dataset_adapter_receipt_digest": "c" * 64,
            "latent_digest": "d" * 64,
            "source_feature_digest": "e" * 64,
            "eeg_feature_digest": "f" * 64,
            "survey_score_digest": "1" * 64,
            "fusion_axis_summary": {
                "survey_axis_count": 4,
                "eeg_cortical_load_proxy": 0.42,
                "eeg_alpha_suppression": 0.6,
                "eeg_theta_beta_ratio": 0.86,
                "survey_attention_proxy": 0.66,
                "survey_fatigue_proxy": 0.26,
                "survey_eeg_cognitive_load_proxy": 0.52,
                "fusion_confidence": 0.71,
            },
            "fusion_status": "bound",
            "operator_accessibility_bound": True,
            "claim_ceiling": "survey-eeg-correlation-input-only",
            "raw_survey_response_payload_stored": False,
            "raw_eeg_samples_stored": False,
            "raw_dataset_payload_stored": False,
            "raw_latent_payload_stored": False,
            "raw_fusion_payload_stored": False,
            "subjective_equivalence_claimed": False,
            "semantic_thought_content_generated": False,
            "diagnosis_claimed": False,
            "consciousness_reproduction_claimed": False,
            "identity_replacement_claimed": False,
        }

    def _build_demo_artifacts(self) -> dict:
        workbench = NeuroIntegrationWorkbench()
        apps = [
            workbench.register_application(
                "Measure",
                "measurement",
                ["questionnaire", "eeg", "fmri_bold", "brain_organoid"],
                ["measurement"],
            ),
            workbench.register_application(
                "Analyze",
                "analysis",
                ["questionnaire", "eeg", "fmri_bold"],
                ["analysis"],
            ),
            workbench.register_application(
                "Curate",
                "data-curation",
                ["questionnaire", "eeg", "brain_organoid"],
                ["data-curation"],
            ),
            workbench.register_application(
                "Guide",
                "operator-copilot",
                ["questionnaire", "eeg"],
                ["operator-copilot"],
            ),
            workbench.register_application(
                "Agent",
                "agent-automation",
                ["questionnaire", "eeg", "fmri_bold", "brain_organoid"],
                ["agent-automation"],
                operator_skill_floor="coding_agent",
            ),
        ]
        source_bundle = workbench.bind_source_bundle(
            "identity://neuro-unit",
            [
                {
                    "source_type": "questionnaire",
                    "source_ref": "source://unit/questionnaire",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/questionnaire",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/questionnaire",
                    "feature_summary": {
                        "stress_score": 0.6,
                        "anxiety_score": 0.5,
                        "fatigue_score": 0.4,
                        "attention_difficulty_score": 0.7,
                        "sleep_quality_score": 0.5,
                        "mood_valence_score": 0.45,
                    },
                },
                {
                    "source_type": "eeg",
                    "source_ref": "source://unit/eeg",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/eeg",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/eeg",
                    "feature_summary": {
                        "alpha_power": 0.4,
                        "theta_power": 0.3,
                        "beta_power": 0.35,
                        "artifact_rate": 0.05,
                    },
                },
                {
                    "source_type": "fmri_bold",
                    "source_ref": "source://unit/fmri",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/fmri",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/fmri",
                    "feature_summary": {
                        "bold_percent_change": 0.4,
                        "network_coupling": 0.6,
                    },
                },
                {
                    "source_type": "brain_organoid",
                    "source_ref": "source://unit/organoid",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/organoid",
                    "consent_ref": "consent://unit/organoid",
                    "license_ref": "license://unit/provenance",
                    "feature_summary_ref": "feature-summary://unit/organoid",
                    "feature_summary": {
                        "network_burst_rate": 0.45,
                        "synchrony_index": 0.5,
                        "viability_score": 0.9,
                    },
                },
            ],
            upstream_receipts=[
                self._build_upstream_fusion_receipt("identity://neuro-unit")
            ],
        )
        workspace = workbench.open_workspace(
            "identity://neuro-unit",
            apps,
            source_bundle,
            "Fuse survey and EEG, then attach fMRI and organoid context.",
            {
                "skill_level": "non_ml_operator",
                "prefers_plain_language": True,
                "llm_assistive_mode": True,
                "can_write_code": False,
            },
        )
        analysis = workbench.build_survey_eeg_fusion(workspace, source_bundle)
        guide = workbench.build_operator_guide(workspace, analysis)
        return {
            "workbench": workbench,
            "apps": apps,
            "source_bundle": source_bundle,
            "workspace": workspace,
            "analysis": analysis,
            "guide": guide,
        }

    def test_binds_survey_eeg_seed_and_expansion_modalities(self) -> None:
        artifacts = self._build_demo_artifacts()
        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["seed_survey_eeg_bound"])
        self.assertTrue(validation["expansion_modalities_bound"])
        self.assertTrue(validation["replacement_lanes_bound"])
        self.assertTrue(validation["llm_native_workflow_bound"])
        self.assertTrue(validation["beginner_operator_supported"])
        self.assertTrue(validation["coding_agent_ready"])
        self.assertTrue(validation["survey_eeg_fusion_receipt_bound"])
        self.assertTrue(validation["upstream_receipt_payload_redacted"])
        self.assertTrue(validation["claim_ceiling_bound"])
        self.assertTrue(validation["raw_payload_redacted"])
        self.assertTrue(validation["no_diagnosis_or_identity_claim"])
        self.assertEqual(
            "feature-alignment-and-analysis-plan-only",
            artifacts["analysis"]["claim_ceiling"],
        )
        self.assertIn("questionnaire", artifacts["source_bundle"]["source_types"])
        self.assertIn("eeg", artifacts["source_bundle"]["source_types"])
        self.assertIn("fmri_bold", artifacts["source_bundle"]["source_types"])
        self.assertIn("brain_organoid", artifacts["source_bundle"]["source_types"])
        self.assertEqual(1, artifacts["source_bundle"]["upstream_receipt_count"])
        self.assertTrue(artifacts["analysis"]["upstream_fusion_binding"]["bound"])
        self.assertEqual(
            "biodata-survey-eeg-fusion",
            artifacts["analysis"]["upstream_fusion_binding"]["receipt_role"],
        )
        self.assertFalse(artifacts["analysis"]["raw_questionnaire_payload_stored"])
        self.assertFalse(artifacts["analysis"]["consciousness_reproduction_claimed"])
        self.assertFalse(artifacts["analysis"]["identity_replacement_claimed"])

    def test_tampered_workspace_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_workspace = deepcopy(artifacts["workspace"])
        tampered_workspace["source_bundle_digest"] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            tampered_workspace,
            artifacts["analysis"],
            artifacts["guide"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["workspace_digest_bound"])

    def test_seed_bundle_requires_questionnaire_and_eeg(self) -> None:
        workbench = NeuroIntegrationWorkbench()

        with self.assertRaisesRegex(ValueError, "questionnaire and eeg"):
            workbench.bind_source_bundle(
                "identity://missing-eeg",
                [
                    {
                        "source_type": "questionnaire",
                        "source_ref": "source://unit/questionnaire",
                        "app_ref": "app://unit",
                        "participant_ref": "participant://unit/self",
                        "consent_ref": "consent://unit/questionnaire",
                        "license_ref": "license://unit/local",
                        "feature_summary_ref": "feature-summary://unit/questionnaire",
                        "feature_summary": {"stress_score": 0.5},
                    },
                    {
                        "source_type": "fmri_bold",
                        "source_ref": "source://unit/fmri",
                        "app_ref": "app://unit",
                        "participant_ref": "participant://unit/self",
                        "consent_ref": "consent://unit/fmri",
                        "license_ref": "license://unit/local",
                        "feature_summary_ref": "feature-summary://unit/fmri",
                        "feature_summary": {"bold_percent_change": 0.4},
                    },
                ],
            )
