from __future__ import annotations

from copy import deepcopy
import unittest

from omoikane.common import canonical_json, sha256_text
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

    def _build_second_window_source_bundle(
        self,
        workbench: NeuroIntegrationWorkbench,
        source_bundle: dict,
    ) -> dict:
        second_bundle = deepcopy(source_bundle)
        second_bundle["source_bundle_ref"] = (
            "source-bundle://neuro-integration/niw-source-bundle-222222222222"
        )
        second_bundle["created_at"] = "2026-05-06T00:00:00+00:00"
        for source in second_bundle["sources"]:
            source_type = source["source_type"]
            source["source_ref"] = f"source://unit/{source_type}/window-2"
            source["feature_summary_ref"] = (
                f"feature-summary://unit/{source_type}/window-2"
            )
            source["analysis_axes"] = {
                axis_name: round(max(0.0, min(1.0, axis_value + 0.02)), 3)
                for axis_name, axis_value in source["analysis_axes"].items()
            }
            source["construct_coverage"] = sorted(source["analysis_axes"])
            source["feature_digest"] = sha256_text(
                canonical_json(
                    {
                        "source_type": source_type,
                        "window": "unit-window-2",
                        "analysis_axes": source["analysis_axes"],
                    }
                )
            )
            source["feature_name_digest"] = sha256_text(
                canonical_json(
                    {"feature_names": sorted(source["analysis_axes"])}
                )
            )
            source["numeric_feature_count"] = max(
                source["numeric_feature_count"],
                len(source["analysis_axes"]),
            )
        second_bundle["source_digest_set"] = sha256_text(
            canonical_json(
                {
                    "profile_id": second_bundle["profile_id"],
                    "source_digests": [
                        source["feature_digest"]
                        for source in second_bundle["sources"]
                    ],
                    "source_types": second_bundle["source_types"],
                }
            )
        )
        second_bundle["source_bundle_digest"] = sha256_text(
            canonical_json(workbench._source_bundle_digest_payload(second_bundle))
        )
        return second_bundle

    def _build_demo_artifacts(self) -> dict:
        workbench = NeuroIntegrationWorkbench()
        source_types = [
            "questionnaire",
            "eeg",
            "fmri_bold",
            "brain_organoid",
            "biosensor",
            "behavioral_task",
            "omics",
            "clinical_metadata",
        ]
        apps = [
            workbench.register_application(
                "Measure",
                "measurement",
                source_types,
                ["measurement"],
            ),
            workbench.register_application(
                "Analyze",
                "analysis",
                source_types,
                ["analysis"],
            ),
            workbench.register_application(
                "Curate",
                "data-curation",
                source_types,
                ["data-curation"],
            ),
            workbench.register_application(
                "Guide",
                "operator-copilot",
                source_types,
                ["operator-copilot"],
            ),
            workbench.register_application(
                "Agent",
                "agent-automation",
                source_types,
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
                {
                    "source_type": "biosensor",
                    "source_ref": "source://unit/biosensor",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/biosensor",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/biosensor",
                    "feature_summary": {
                        "heart_rate_variability": 0.58,
                        "skin_conductance": 0.42,
                        "respiration_regular": 0.71,
                        "temperature_stability": 0.67,
                    },
                },
                {
                    "source_type": "behavioral_task",
                    "source_ref": "source://unit/behavioral-task",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/behavioral-task",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/behavioral-task",
                    "feature_summary": {
                        "reaction_time_stability": 0.62,
                        "attention_accuracy": 0.74,
                        "fatigue_error_proxy": 0.28,
                    },
                },
                {
                    "source_type": "omics",
                    "source_ref": "source://unit/omics",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/omics",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/omics",
                    "feature_summary": {
                        "inflammation_marker_proxy": 0.33,
                        "metabolic_stability_proxy": 0.68,
                        "sampling_quality_proxy": 0.86,
                    },
                },
                {
                    "source_type": "clinical_metadata",
                    "source_ref": "source://unit/clinical-metadata",
                    "app_ref": apps[0]["app_ref"],
                    "participant_ref": "participant://unit/self",
                    "consent_ref": "consent://unit/clinical-metadata",
                    "license_ref": "license://unit/local",
                    "feature_summary_ref": "feature-summary://unit/clinical-metadata",
                    "feature_summary": {
                        "medication_context_proxy": 0.2,
                        "sleep_history_proxy": 0.52,
                        "screening_completeness": 0.9,
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
            "Fuse survey and EEG, then attach fMRI, organoid, and biodata context.",
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
        collection_run = workbench.execute_collection_protocol(
            source_bundle,
            connector_bundle,
            collection_protocol,
        )
        measurement_quality_gate = workbench.bind_measurement_quality_gate(
            source_bundle,
            collection_run,
            [
                {
                    "source_type": source_type,
                    "calibration_ref": f"calibration://unit/{source_type}",
                    "artifact_qc_ref": f"artifact-qc://unit/{source_type}",
                    "consent_freshness_ref": (
                        f"consent-freshness://unit/{source_type}"
                    ),
                    "operator_review_ref": (
                        f"operator-review://unit/{source_type}/quality"
                    ),
                    "quality_authority_ref": (
                        f"quality-authority://unit/{source_type}"
                    ),
                    "calibration_score": 0.93,
                    "artifact_acceptance_score": 0.91,
                    "consent_freshness_score": 0.96,
                    "sampling_completeness_score": 0.9,
                }
                for source_type in source_bundle["source_types"]
            ],
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
        interpretation_synthesis = workbench.synthesize_operator_interpretation(
            source_bundle,
            guide,
            measurement_quality_gate,
            cross_modal_analysis_run,
        )
        second_source_bundle = self._build_second_window_source_bundle(
            workbench,
            source_bundle,
        )
        longitudinal_timeline = workbench.build_longitudinal_integration_timeline(
            "identity://neuro-unit",
            [source_bundle, second_source_bundle],
            guide,
        )
        return {
            "workbench": workbench,
            "apps": apps,
            "source_bundle": source_bundle,
            "second_source_bundle": second_source_bundle,
            "workspace": workspace,
            "analysis": analysis,
            "guide": guide,
            "replacement_plan": replacement_plan,
            "connector_bundle": connector_bundle,
            "collection_protocol": collection_protocol,
            "collection_run": collection_run,
            "measurement_quality_gate": measurement_quality_gate,
            "cross_modal_analysis_plan": cross_modal_analysis_plan,
            "cross_modal_analysis_run": cross_modal_analysis_run,
            "interpretation_synthesis": interpretation_synthesis,
            "longitudinal_timeline": longitudinal_timeline,
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
            collection_run=artifacts["collection_run"],
            measurement_quality_gate=artifacts["measurement_quality_gate"],
            interpretation_synthesis=artifacts["interpretation_synthesis"],
            longitudinal_timeline=artifacts["longitudinal_timeline"],
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
        self.assertTrue(validation["collection_semantic_thought_claim_redacted"])
        self.assertTrue(validation["collection_run_bound"])
        self.assertTrue(validation["collection_run_digest_bound"])
        self.assertTrue(validation["collection_results_bound"])
        self.assertTrue(validation["collection_result_payload_redacted"])
        self.assertTrue(
            validation["collection_result_semantic_thought_claim_redacted"]
        )
        self.assertTrue(validation["measurement_quality_gate_bound"])
        self.assertTrue(validation["measurement_quality_gate_digest_bound"])
        self.assertTrue(validation["measurement_quality_items_bound"])
        self.assertTrue(validation["measurement_quality_payload_redacted"])
        self.assertTrue(validation["cross_modal_analysis_plan_bound"])
        self.assertTrue(validation["cross_modal_analysis_plan_digest_bound"])
        self.assertTrue(validation["cross_modal_source_pair_coverage_bound"])
        self.assertTrue(validation["cross_modal_analysis_payload_redacted"])
        self.assertTrue(validation["cross_modal_analysis_run_bound"])
        self.assertTrue(validation["cross_modal_analysis_run_digest_bound"])
        self.assertTrue(validation["cross_modal_pair_results_bound"])
        self.assertTrue(validation["cross_modal_result_payload_redacted"])
        self.assertTrue(validation["interpretation_synthesis_bound"])
        self.assertTrue(validation["interpretation_synthesis_digest_bound"])
        self.assertTrue(validation["interpretation_synthesis_cards_bound"])
        self.assertTrue(validation["interpretation_operator_action_ready"])
        self.assertTrue(validation["interpretation_payload_redacted"])
        self.assertTrue(validation["longitudinal_timeline_bound"])
        self.assertTrue(validation["longitudinal_timeline_digest_bound"])
        self.assertTrue(validation["longitudinal_source_type_coverage_bound"])
        self.assertTrue(validation["longitudinal_axis_drifts_bound"])
        self.assertTrue(validation["longitudinal_payload_redacted"])
        self.assertTrue(validation["longitudinal_no_identity_or_upload_claim"])
        self.assertTrue(validation["survey_eeg_fusion_receipt_bound"])
        self.assertTrue(validation["upstream_receipt_payload_redacted"])
        self.assertTrue(validation["claim_ceiling_bound"])
        self.assertTrue(validation["raw_payload_redacted"])
        self.assertTrue(validation["no_diagnosis_or_identity_claim"])
        self.assertTrue(validation["no_semantic_thought_content_claim"])
        self.assertEqual(
            "feature-alignment-and-analysis-plan-only",
            artifacts["analysis"]["claim_ceiling"],
        )
        self.assertIn("questionnaire", artifacts["source_bundle"]["source_types"])
        self.assertIn("eeg", artifacts["source_bundle"]["source_types"])
        self.assertIn("fmri_bold", artifacts["source_bundle"]["source_types"])
        self.assertIn("brain_organoid", artifacts["source_bundle"]["source_types"])
        self.assertIn("biosensor", artifacts["source_bundle"]["source_types"])
        self.assertIn("behavioral_task", artifacts["source_bundle"]["source_types"])
        self.assertIn("omics", artifacts["source_bundle"]["source_types"])
        self.assertIn("clinical_metadata", artifacts["source_bundle"]["source_types"])
        source_axes = {
            source["source_type"]: source["analysis_axes"]
            for source in artifacts["source_bundle"]["sources"]
        }
        self.assertIn("autonomic_balance_proxy", source_axes["biosensor"])
        self.assertIn(
            "task_performance_quality_proxy",
            source_axes["behavioral_task"],
        )
        self.assertIn("molecular_burden_proxy", source_axes["omics"])
        self.assertIn(
            "clinical_context_risk_proxy",
            source_axes["clinical_metadata"],
        )
        self.assertEqual(1, artifacts["source_bundle"]["upstream_receipt_count"])
        self.assertTrue(artifacts["analysis"]["upstream_fusion_binding"]["bound"])
        self.assertTrue(artifacts["replacement_plan"]["replacement_plan_bound"])
        self.assertTrue(artifacts["connector_bundle"]["connector_bundle_bound"])
        self.assertEqual(5, artifacts["connector_bundle"]["connector_count"])
        self.assertTrue(artifacts["collection_protocol"]["collection_protocol_bound"])
        self.assertFalse(
            artifacts["collection_protocol"]["semantic_thought_content_generated"]
        )
        self.assertTrue(
            all(
                step["semantic_thought_content_generated"] is False
                for step in artifacts["collection_protocol"]["collection_steps"]
            )
        )
        self.assertEqual(8, artifacts["collection_protocol"]["collection_step_count"])
        self.assertEqual(8, validation["collection_step_count"])
        self.assertTrue(artifacts["collection_run"]["collection_run_bound"])
        self.assertFalse(artifacts["collection_run"]["semantic_thought_content_generated"])
        self.assertTrue(
            all(
                result["semantic_thought_content_generated"] is False
                for result in artifacts["collection_run"]["collection_results"]
            )
        )
        self.assertEqual(8, artifacts["collection_run"]["result_count"])
        self.assertEqual(8, validation["collection_result_count"])
        self.assertTrue(
            artifacts["measurement_quality_gate"][
                "measurement_quality_gate_bound"
            ]
        )
        self.assertEqual(
            8,
            artifacts["measurement_quality_gate"]["quality_item_count"],
        )
        self.assertEqual(8, validation["measurement_quality_item_count"])
        self.assertTrue(
            artifacts["cross_modal_analysis_plan"][
                "cross_modal_analysis_plan_bound"
            ]
        )
        self.assertEqual(
            28,
            artifacts["cross_modal_analysis_plan"]["analysis_pair_count"],
        )
        recipe_counts = {
            item["analysis_recipe_id"]: item["pair_count"]
            for item in artifacts["cross_modal_analysis_plan"]["recipe_catalog"]
        }
        self.assertEqual(1, recipe_counts["survey-eeg-feature-alignment"])
        self.assertEqual(1, recipe_counts["neural-electrical-hemodynamic-context"])
        self.assertEqual(7, recipe_counts["organoid-context-comparison"])
        self.assertEqual(3, recipe_counts["biosignal-autonomic-context-screen"])
        self.assertEqual(4, recipe_counts["behavioral-performance-context-screen"])
        self.assertEqual(5, recipe_counts["omics-physiology-context-screen"])
        self.assertEqual(1, recipe_counts["omics-clinical-context-screen"])
        self.assertEqual(5, recipe_counts["clinical-context-modulator-screen"])
        self.assertEqual(1, recipe_counts["feature-summary-cross-modal-screen"])
        self.assertTrue(
            artifacts["cross_modal_analysis_run"][
                "cross_modal_analysis_run_bound"
            ]
        )
        self.assertEqual(
            28,
            artifacts["cross_modal_analysis_run"]["result_count"],
        )
        result_statuses = {
            result["result_status"]
            for result in artifacts["cross_modal_analysis_run"]["pair_results"]
        }
        self.assertTrue(
            {
                "seed-survey-eeg-result-bound",
                "in-vitro-context-result-bound",
                "biosignal-context-result-bound",
                "behavioral-context-result-bound",
                "omics-context-result-bound",
                "clinical-context-result-bound",
                "cross-modal-context-result-bound",
            }.issubset(result_statuses)
        )
        self.assertTrue(
            artifacts["interpretation_synthesis"][
                "interpretation_synthesis_bound"
            ]
        )
        self.assertEqual(
            28,
            artifacts["interpretation_synthesis"]["synthesis_card_count"],
        )
        interpretation_statuses = {
            card["interpretation_status"]
            for card in artifacts["interpretation_synthesis"]["synthesis_cards"]
        }
        self.assertTrue(
            {
                "seed-interpretation-bound",
                "neuroimaging-context-interpretation-bound",
                "in-vitro-context-interpretation-bound",
                "biosignal-context-interpretation-bound",
                "behavioral-context-interpretation-bound",
                "omics-context-interpretation-bound",
                "clinical-context-interpretation-bound",
            }.issubset(interpretation_statuses)
        )
        self.assertEqual(28, validation["interpretation_card_count"])
        self.assertTrue(artifacts["longitudinal_timeline"]["longitudinal_timeline_bound"])
        self.assertEqual(2, artifacts["longitudinal_timeline"]["window_count"])
        self.assertEqual(2, validation["longitudinal_window_count"])
        self.assertEqual(8, validation["longitudinal_stable_source_type_count"])
        self.assertEqual(8, validation["longitudinal_axis_drift_item_count"])
        self.assertFalse(
            artifacts["longitudinal_timeline"]["upload_readiness_claimed"]
        )
        self.assertEqual(
            8,
            artifacts["replacement_plan"]["coverage_summary"]["covered_source_type_count"],
        )
        self.assertEqual(
            "biodata-survey-eeg-fusion",
            artifacts["analysis"]["upstream_fusion_binding"]["receipt_role"],
        )
        self.assertFalse(artifacts["analysis"]["raw_questionnaire_payload_stored"])
        self.assertFalse(validation["semantic_thought_content_generated"])
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
            collection_run=artifacts["collection_run"],
            measurement_quality_gate=artifacts["measurement_quality_gate"],
            interpretation_synthesis=artifacts["interpretation_synthesis"],
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

    def test_tampered_collection_result_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_run = deepcopy(artifacts["collection_run"])
        tampered_run["result_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            collection_protocol=artifacts["collection_protocol"],
            collection_run=tampered_run,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "collection_run.result_digests mismatch",
            validation["errors"],
        )

    def test_tampered_measurement_quality_item_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_gate = deepcopy(artifacts["measurement_quality_gate"])
        tampered_gate["quality_item_digests"][0] = "0" * 64

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            collection_protocol=artifacts["collection_protocol"],
            collection_run=artifacts["collection_run"],
            measurement_quality_gate=tampered_gate,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "measurement_quality_gate.quality_item_digests mismatch",
            validation["errors"],
        )

    def test_collection_run_semantic_thought_generation_claim_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_run = deepcopy(artifacts["collection_run"])
        tampered_run["semantic_thought_content_generated"] = True
        tampered_run["collection_run_digest"] = sha256_text(
            canonical_json(
                artifacts["workbench"]._collection_run_digest_payload(tampered_run)
            )
        )

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            collection_protocol=artifacts["collection_protocol"],
            collection_run=tampered_run,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "collection_run.semantic_thought_content_generated must be false",
            validation["errors"],
        )

    def test_collection_result_semantic_thought_generation_claim_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_run = deepcopy(artifacts["collection_run"])
        tampered_run["collection_results"][0]["semantic_thought_content_generated"] = True

        validation = artifacts["workbench"].validate_integration_bundle(
            artifacts["apps"],
            artifacts["source_bundle"],
            artifacts["workspace"],
            artifacts["analysis"],
            artifacts["guide"],
            artifacts["replacement_plan"],
            artifacts["connector_bundle"],
            collection_protocol=artifacts["collection_protocol"],
            collection_run=tampered_run,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "collection_result.semantic_thought_content_generated must be false",
            validation["errors"],
        )

    def test_tampered_interpretation_card_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_synthesis = deepcopy(artifacts["interpretation_synthesis"])
        tampered_synthesis["synthesis_card_digests"][0] = "0" * 64

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
            collection_run=artifacts["collection_run"],
            measurement_quality_gate=artifacts["measurement_quality_gate"],
            interpretation_synthesis=tampered_synthesis,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "interpretation_synthesis.synthesis_card_digests mismatch",
            validation["errors"],
        )

    def test_tampered_longitudinal_axis_drift_digest_fails_validation(self) -> None:
        artifacts = self._build_demo_artifacts()
        tampered_timeline = deepcopy(artifacts["longitudinal_timeline"])
        tampered_timeline["source_type_axis_drifts"][0]["axis_drift_digest"] = "0" * 64
        tampered_timeline["longitudinal_timeline_digest"] = sha256_text(
            canonical_json(
                artifacts["workbench"]._longitudinal_timeline_digest_payload(
                    tampered_timeline
                )
            )
        )

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
            collection_run=artifacts["collection_run"],
            measurement_quality_gate=artifacts["measurement_quality_gate"],
            interpretation_synthesis=artifacts["interpretation_synthesis"],
            longitudinal_timeline=tampered_timeline,
        )

        self.assertFalse(validation["ok"])
        self.assertIn(
            "axis_drift.axis_drift_digest mismatch",
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
