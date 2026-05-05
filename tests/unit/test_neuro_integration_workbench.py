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
                ["questionnaire", "eeg", "fmri_bold", "brain_organoid"],
                ["analysis"],
            ),
            workbench.register_application(
                "Curate",
                "data-curation",
                ["questionnaire", "eeg", "fmri_bold", "brain_organoid"],
                ["data-curation"],
            ),
            workbench.register_application(
                "Guide",
                "operator-copilot",
                ["questionnaire", "eeg", "fmri_bold", "brain_organoid"],
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
        replacement_plan = workbench.build_application_replacement_plan(
            apps,
            source_bundle,
            workspace,
            guide,
        )
        connector_source_types = source_bundle["source_types"]
        connector_bundle = workbench.bind_application_connector_bundle(
            apps,
            replacement_plan,
            [
                {
                    "app_ref": apps[0]["app_ref"],
                    "connector_kind": "measurement-ingest",
                    "protocol": "local-file",
                    "endpoint_ref": "connector-endpoint://unit/measure/import",
                    "credential_ref": "credential://unit/measure/redacted",
                    "permission_ref": "permission://unit/measure/feature-summary-only",
                    "data_contract_ref": "data-contract://unit/measure/source-summary-v1",
                    "llm_tool_ref": "llm-tool://unit/measure/import-source-summary",
                    "operator_label": "Import source feature summaries",
                    "supported_source_types": connector_source_types,
                    "dry_run_supported": True,
                },
                {
                    "app_ref": apps[1]["app_ref"],
                    "connector_kind": "analysis-runner",
                    "protocol": "notebook-runner",
                    "endpoint_ref": "connector-endpoint://unit/analysis/run",
                    "credential_ref": "credential://unit/analysis/redacted",
                    "permission_ref": "permission://unit/analysis/digest-only",
                    "data_contract_ref": "data-contract://unit/analysis/receipt-v1",
                    "llm_tool_ref": "llm-tool://unit/analysis/run-bounded-plan",
                    "operator_label": "Run bounded analysis plan",
                    "supported_source_types": connector_source_types,
                    "dry_run_supported": True,
                },
                {
                    "app_ref": apps[2]["app_ref"],
                    "connector_kind": "curation-ledger",
                    "protocol": "database-view",
                    "endpoint_ref": "connector-endpoint://unit/curation/ledger",
                    "credential_ref": "credential://unit/curation/redacted",
                    "permission_ref": "permission://unit/curation/append-only-digest",
                    "data_contract_ref": "data-contract://unit/curation/provenance-v1",
                    "llm_tool_ref": "llm-tool://unit/curation/check-provenance",
                    "operator_label": "Check provenance digests",
                    "supported_source_types": connector_source_types,
                    "dry_run_supported": True,
                },
                {
                    "app_ref": apps[3]["app_ref"],
                    "connector_kind": "operator-console",
                    "protocol": "llm-tool",
                    "endpoint_ref": "connector-endpoint://unit/copilot/plain-status",
                    "credential_ref": "credential://unit/copilot/redacted",
                    "permission_ref": "permission://unit/copilot/plain-language-only",
                    "data_contract_ref": "data-contract://unit/copilot/operator-guide-v1",
                    "llm_tool_ref": "llm-tool://unit/copilot/explain-next-action",
                    "operator_label": "Explain safe next action",
                    "supported_source_types": connector_source_types,
                    "dry_run_supported": True,
                },
                {
                    "app_ref": apps[4]["app_ref"],
                    "connector_kind": "agent-runner",
                    "protocol": "message-queue",
                    "endpoint_ref": "connector-endpoint://unit/agent/task-runner",
                    "credential_ref": "credential://unit/agent/redacted",
                    "permission_ref": "permission://unit/agent/schema-bound-only",
                    "data_contract_ref": "data-contract://unit/agent/task-template-v1",
                    "llm_tool_ref": "llm-tool://unit/agent/execute-schema-task",
                    "operator_label": "Run coding-agent schema task",
                    "supported_source_types": connector_source_types,
                    "dry_run_supported": True,
                },
            ],
        )
        collection_protocol = workbench.build_collection_protocol(
            source_bundle,
            replacement_plan,
            connector_bundle,
        )
        cross_modal_analysis_plan = workbench.build_cross_modal_analysis_plan(
            source_bundle,
            analysis,
            guide,
            replacement_plan,
            connector_bundle,
        )
        cross_modal_analysis_run = workbench.execute_cross_modal_analysis_plan(
            source_bundle,
            connector_bundle,
            cross_modal_analysis_plan,
        )
        return {
            "workbench": workbench,
            "apps": apps,
            "source_bundle": source_bundle,
            "workspace": workspace,
            "analysis": analysis,
            "guide": guide,
            "replacement_plan": replacement_plan,
            "connector_bundle": connector_bundle,
            "collection_protocol": collection_protocol,
            "cross_modal_analysis_plan": cross_modal_analysis_plan,
            "cross_modal_analysis_run": cross_modal_analysis_run,
        }

    def test_binds_survey_eeg_seed_and_expansion_modalities(self) -> None:
        artifacts = self._build_demo_artifacts()
        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            artifacts["cross_modal_analysis_plan"],
            artifacts["cross_modal_analysis_run"],
            collection_protocol=artifacts["collection_protocol"],
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["seed_survey_eeg_bound"])
        self.assertTrue(validation["expansion_modalities_bound"])
        self.assertTrue(validation["replacement_lanes_bound"])
        self.assertTrue(validation["llm_native_workflow_bound"])
        self.assertTrue(validation["beginner_operator_supported"])
        self.assertTrue(validation["coding_agent_ready"])
        self.assertTrue(validation["application_replacement_plan_bound"])
        self.assertTrue(validation["source_type_lane_coverage_bound"])
        self.assertTrue(validation["replacement_plan_payload_redacted"])
        self.assertTrue(validation["application_connector_bundle_bound"])
        self.assertTrue(validation["connector_bundle_digest_bound"])
        self.assertTrue(validation["connector_source_type_coverage_bound"])
        self.assertTrue(validation["connector_payload_redacted"])
        self.assertTrue(validation["collection_protocol_bound"])
        self.assertTrue(validation["collection_protocol_digest_bound"])
        self.assertTrue(validation["source_collection_coverage_bound"])
        self.assertTrue(validation["seed_collection_bound"])
        self.assertTrue(validation["collection_payload_redacted"])
        self.assertTrue(validation["cross_modal_analysis_plan_bound"])
        self.assertTrue(validation["cross_modal_analysis_plan_digest_bound"])
        self.assertTrue(validation["cross_modal_source_pair_coverage_bound"])
        self.assertTrue(validation["cross_modal_analysis_payload_redacted"])
        self.assertTrue(validation["cross_modal_analysis_run_bound"])
        self.assertTrue(validation["cross_modal_analysis_run_digest_bound"])
        self.assertTrue(validation["cross_modal_pair_results_bound"])
        self.assertTrue(validation["cross_modal_result_payload_redacted"])
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
        self.assertTrue(artifacts["replacement_plan"]["replacement_plan_bound"])
        self.assertTrue(artifacts["connector_bundle"]["connector_bundle_bound"])
        self.assertEqual(5, artifacts["connector_bundle"]["connector_count"])
        self.assertTrue(artifacts["collection_protocol"]["collection_protocol_bound"])
        self.assertEqual(4, artifacts["collection_protocol"]["collection_step_count"])
        self.assertEqual(4, validation["collection_step_count"])
        self.assertTrue(
            artifacts["cross_modal_analysis_plan"][
                "cross_modal_analysis_plan_bound"
            ]
        )
        self.assertEqual(
            6,
            artifacts["cross_modal_analysis_plan"]["analysis_pair_count"],
        )
        self.assertTrue(
            artifacts["cross_modal_analysis_run"][
                "cross_modal_analysis_run_bound"
            ]
        )
        self.assertEqual(
            6,
            artifacts["cross_modal_analysis_run"]["result_count"],
        )
        self.assertEqual(
            4,
            artifacts["replacement_plan"]["coverage_summary"]["covered_source_type_count"],
        )
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
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            artifacts["cross_modal_analysis_plan"],
            artifacts["cross_modal_analysis_run"],
            collection_protocol=artifacts["collection_protocol"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["workspace_digest_bound"])

    def test_tampered_connector_digest_set_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_connector_bundle = deepcopy(artifacts["connector_bundle"])
        tampered_connector_bundle["connector_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            tampered_connector_bundle,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "connector_bundle.connector_digests mismatch",
            validation["errors"],
        )

    def test_tampered_cross_modal_pair_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_plan = deepcopy(artifacts["cross_modal_analysis_plan"])
        tampered_plan["pair_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            tampered_plan,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "cross_modal_analysis_plan.pair_digests mismatch",
            validation["errors"],
        )

    def test_tampered_cross_modal_result_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_run = deepcopy(artifacts["cross_modal_analysis_run"])
        tampered_run["result_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            artifacts["cross_modal_analysis_plan"],
            tampered_run,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "cross_modal_analysis_run.result_digests mismatch",
            validation["errors"],
        )

    def test_tampered_collection_step_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_protocol = deepcopy(artifacts["collection_protocol"])
        tampered_protocol["collection_step_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            collection_protocol=tampered_protocol,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "collection_protocol.collection_step_digests mismatch",
            validation["errors"],
        )

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
