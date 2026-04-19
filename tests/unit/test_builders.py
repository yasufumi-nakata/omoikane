from __future__ import annotations

import unittest

from omoikane.self_construction import DifferentialEvaluatorService, PatchGeneratorService


class PatchGeneratorServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = {
            "request_id": "build-l5-0001",
            "target_subsystem": "L5.DifferentialEvaluator",
            "constraints": {
                "must_pass": ["evals/continuity/council_output_build_request_pipeline.yaml"],
                "forbidden": ["L1.EthicsEnforcer", "L1.ContinuityLedger"],
                "allowed_write_paths": [
                    "src/omoikane/self_construction/",
                    "tests/unit/",
                ],
            },
            "workspace_scope": ["src/", "tests/", "evals/"],
            "output_paths": [
                "src/omoikane/self_construction/",
                "tests/unit/",
            ],
            "spec_refs": [
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/interfaces/selfctor.diff_eval.v0.idl",
            ],
            "design_refs": ["docs/04-ai-governance/codex-as-builder.md"],
        }

    def test_validate_scope_rejects_missing_immutable_boundary(self) -> None:
        service = PatchGeneratorService()
        request = dict(self.request)
        request["constraints"] = dict(self.request["constraints"])
        request["constraints"]["forbidden"] = ["L1.EthicsEnforcer"]

        result = service.validate_scope(request)

        self.assertFalse(result["allowed"])
        self.assertIn(
            "immutable boundary missing from forbidden list: L1.ContinuityLedger",
            result["blocking_rules"],
        )

    def test_generate_patch_set_emits_ready_artifact_for_valid_scope(self) -> None:
        service = PatchGeneratorService()

        result = service.generate_patch_set(self.request)

        self.assertEqual("ready", result["status"])
        self.assertEqual(2, len(result["patches"]))
        self.assertEqual("pass", result["test_results"]["build_status"])
        self.assertEqual(
            "ledger://self-modify/build-l5-0001",
            result["continuity_log_ref"],
        )


class DifferentialEvaluatorServiceTests(unittest.TestCase):
    def test_select_suite_preserves_requested_eval_and_mandatory_guard(self) -> None:
        service = DifferentialEvaluatorService()

        result = service.select_suite(
            target_subsystem="L5.DifferentialEvaluator",
            requested_evals=["evals/continuity/council_output_build_request_pipeline.yaml"],
        )

        self.assertEqual(
            ["evals/continuity/council_output_build_request_pipeline.yaml"],
            result["selected_evals"],
        )

    def test_classify_rollout_uses_regression_as_hard_stop(self) -> None:
        service = DifferentialEvaluatorService()

        result = service.classify_rollout(outcomes=["pass", "regression"])

        self.assertEqual("rollback", result["decision"])


if __name__ == "__main__":
    unittest.main()
