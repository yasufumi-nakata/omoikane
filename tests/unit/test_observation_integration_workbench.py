from __future__ import annotations

import unittest
from copy import deepcopy

from omoikane.interface.observation_integration_workbench import (
    ObservationIntegrationWorkbench,
)


class ObservationIntegrationWorkbenchTests(unittest.TestCase):
    def _source_manifest(self, source_type: str, suffix: str) -> dict:
        return {
            "source_type": source_type,
            "source_ref": f"source://unit/{suffix}",
            "measurement_ref": f"measurement://unit/{suffix}",
            "instrument_ref": f"instrument://unit/{suffix}",
            "collector_ref": f"collector://unit/{suffix}",
            "rights_ref": f"rights://unit/{suffix}",
            "consent_or_public_basis_ref": f"public-basis://unit/{suffix}",
            "license_ref": f"license://unit/{suffix}",
            "feature_summary_ref": f"feature-summary://unit/{suffix}",
            "temporal_ref": f"time://unit/{suffix}",
            "spatial_ref": f"space://unit/{suffix}",
            "unit_system_ref": f"unit://unit/{suffix}",
            "uncertainty_ref": f"uncertainty://unit/{suffix}",
            "entity_ref": f"entity://unit/{suffix}",
            "feature_summary": {
                "signal_proxy": 0.5,
                "coverage_ratio": 0.9,
                "rights_clarity": 0.95,
            },
            "uncertainty_summary": {
                "measurement_error_proxy": 0.1,
                "sampling_gap_proxy": 0.05,
            },
        }

    def _build_package(self) -> dict:
        workbench = ObservationIntegrationWorkbench()
        taxonomy = workbench.taxonomy()
        method_catalog = workbench.method_catalog()
        source_bundle = workbench.bind_source_bundle(
            "unit-observation-package",
            [
                self._source_manifest("eeg", "eeg"),
                self._source_manifest("climate_record", "climate"),
                self._source_manifest("satellite_imagery", "satellite"),
                self._source_manifest("telescope_image", "astronomy"),
            ],
        )
        graph = workbench.build_integration_graph(source_bundle)
        plan = workbench.build_analysis_plan(
            source_bundle,
            graph,
            "Align feature summaries across declared observation families.",
            method_catalog=method_catalog,
        )
        guide = workbench.build_operator_guide(source_bundle, plan)
        run = workbench.execute_analysis_plan(source_bundle, graph, plan, guide)
        return {
            "workbench": workbench,
            "taxonomy": taxonomy,
            "method_catalog": method_catalog,
            "source_bundle": source_bundle,
            "graph": graph,
            "plan": plan,
            "guide": guide,
            "run": run,
        }

    def test_binds_open_world_observation_package(self) -> None:
        package = self._build_package()
        validation = package["workbench"].validate_observation_package(
            package["taxonomy"],
            package["source_bundle"],
            package["graph"],
            package["plan"],
            package["guide"],
            method_catalog=package["method_catalog"],
            analysis_run=package["run"],
        )

        self.assertTrue(validation["ok"])
        self.assertTrue(validation["taxonomy_digest_bound"])
        self.assertTrue(validation["method_catalog_digest_bound"])
        self.assertTrue(validation["source_bundle_digest_bound"])
        self.assertTrue(validation["integration_graph_digest_bound"])
        self.assertTrue(validation["analysis_plan_digest_bound"])
        self.assertTrue(validation["operator_guide_digest_bound"])
        self.assertTrue(validation["analysis_run_digest_bound"])
        self.assertTrue(validation["observation_analysis_run_bound"])
        self.assertTrue(validation["all_lane_results_bound"])
        self.assertTrue(validation["analysis_result_payload_redacted"])
        self.assertTrue(validation["alignment_axes_bound"])
        self.assertTrue(validation["rights_and_consent_bound"])
        self.assertTrue(validation["cross_domain_graph_bound"])
        self.assertTrue(validation["all_analysis_lanes_bound"])
        self.assertTrue(validation["measurement_method_catalog_bound"])
        self.assertTrue(validation["analysis_method_catalog_bound"])
        self.assertTrue(validation["planned_methods_bound"])
        self.assertTrue(validation["operator_handoff_bound"])
        self.assertTrue(validation["raw_payload_redacted"])
        self.assertTrue(validation["no_totality_or_truth_claim"])
        self.assertTrue(validation["no_identity_or_consciousness_claim"])
        self.assertGreaterEqual(validation["family_coverage_count"], 4)
        self.assertGreaterEqual(validation["measurement_method_family_count"], 8)
        self.assertGreaterEqual(validation["analysis_method_family_count"], 10)
        self.assertEqual(6, validation["analysis_result_count"])
        self.assertTrue(package["run"]["observation_analysis_run_bound"])
        self.assertEqual(6, package["run"]["result_count"])
        self.assertEqual(
            "cross-domain-feature-integration-plan-only",
            validation["claim_ceiling"],
        )

    def test_method_catalog_is_open_world_and_digest_bound(self) -> None:
        workbench = ObservationIntegrationWorkbench()
        method_catalog = workbench.method_catalog()

        self.assertTrue(method_catalog["open_world_method_taxonomy"])
        self.assertFalse(method_catalog["raw_method_payload_stored"])
        self.assertFalse(method_catalog["raw_algorithm_payload_stored"])
        self.assertFalse(method_catalog["complete_human_method_coverage_claimed"])
        self.assertGreaterEqual(method_catalog["measurement_method_family_count"], 8)
        self.assertGreaterEqual(method_catalog["analysis_method_family_count"], 10)

        tampered = dict(method_catalog)
        tampered["analysis_method_count"] = 0

        with self.assertRaises(ValueError):
            workbench.build_analysis_plan(
                self._build_package()["source_bundle"],
                self._build_package()["graph"],
                "Tampered method catalog should be rejected.",
                method_catalog=tampered,
            )

    def test_tampered_analysis_run_result_digest_fails_validation(self) -> None:
        package = self._build_package()
        tampered_run = deepcopy(package["run"])
        tampered_run["result_digests"][0] = "0" * 64

        validation = package["workbench"].validate_observation_package(
            package["taxonomy"],
            package["source_bundle"],
            package["graph"],
            package["plan"],
            package["guide"],
            method_catalog=package["method_catalog"],
            analysis_run=tampered_run,
        )

        self.assertFalse(validation["ok"])
        self.assertIn("analysis_run.result_digests mismatch", validation["errors"])

    def test_requires_four_observation_domains(self) -> None:
        workbench = ObservationIntegrationWorkbench()

        with self.assertRaises(ValueError):
            workbench.bind_source_bundle(
                "too-small",
                [
                    self._source_manifest("eeg", "eeg"),
                    self._source_manifest("climate_record", "climate"),
                    self._source_manifest("satellite_imagery", "satellite"),
                ],
            )

    def test_rejects_missing_rights_axis(self) -> None:
        workbench = ObservationIntegrationWorkbench()
        source = self._source_manifest("eeg", "eeg")
        source["rights_ref"] = ""

        with self.assertRaises(ValueError):
            workbench.bind_source_bundle(
                "missing-rights",
                [
                    source,
                    self._source_manifest("climate_record", "climate"),
                    self._source_manifest("satellite_imagery", "satellite"),
                    self._source_manifest("telescope_image", "astronomy"),
                ],
            )
