from __future__ import annotations

import unittest
from pathlib import Path

from omoikane.self_construction import (
    DesignReaderService,
    DifferentialEvaluatorService,
    LiveEnactmentService,
    PatchGeneratorService,
    RollbackEngineService,
    RolloutPlannerService,
    SandboxApplyService,
)


def _design_backed_request(
    *,
    target_subsystem: str,
    request_id: str,
    must_pass: list[str],
    output_paths: list[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[2]
    reader = DesignReaderService()
    design_manifest = reader.finalize_manifest(
        reader.read_design_delta(
            target_subsystem=target_subsystem,
            change_summary="Unit-test DesignReader handoff.",
            design_refs=[
                "docs/02-subsystems/self-construction/README.md",
                "docs/04-ai-governance/codex-as-builder.md",
            ],
            spec_refs=[
                "specs/interfaces/selfctor.design_reader.v0.idl",
                "specs/interfaces/selfctor.patch_generator.v0.idl",
                "specs/schemas/design_delta_manifest.schema",
                "specs/schemas/build_request.yaml",
            ],
            workspace_scope=["src/", "tests/", "specs/", "evals/", "docs/", "meta/decision-log/"],
            output_paths=output_paths or ["src/omoikane/self_construction/", "tests/unit/"],
            must_sync_docs=[
                "docs/02-subsystems/self-construction/README.md",
                "docs/04-ai-governance/codex-as-builder.md",
            ],
            repo_root=repo_root,
        )
    )
    return reader.prepare_build_request(
        manifest=design_manifest,
        request_id=request_id,
        change_class="feature-improvement",
        must_pass=must_pass,
        council_session_id=f"sess-{request_id}",
        guardian_gate="pass",
    )


class DesignReaderServiceTests(unittest.TestCase):
    def test_prepare_build_request_binds_design_delta_manifest(self) -> None:
        request = _design_backed_request(
            target_subsystem="L5.DesignReader",
            request_id="build-l5-design-reader-0001",
            must_pass=["evals/continuity/design_reader_handoff.yaml"],
            output_paths=[
                "src/omoikane/self_construction/",
                "tests/unit/",
                "docs/02-subsystems/self-construction/",
                "evals/continuity/",
            ],
        )

        self.assertTrue(str(request["design_delta_ref"]).startswith("design://"))
        self.assertEqual(64, len(str(request["design_delta_digest"])))
        self.assertEqual(
            [
                "docs/02-subsystems/self-construction/README.md",
                "docs/04-ai-governance/codex-as-builder.md",
            ],
            request["must_sync_docs"],
        )
        self.assertIn("evals/continuity/design_reader_handoff.yaml", request["constraints"]["must_pass"])


class PatchGeneratorServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = _design_backed_request(
            target_subsystem="L5.DifferentialEvaluator",
            request_id="build-l5-0001",
            must_pass=["evals/continuity/council_output_build_request_pipeline.yaml"],
        )

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


class SandboxApplyServiceTests(unittest.TestCase):
    def test_apply_artifact_emits_receipt_with_rollback_ready_invariants(self) -> None:
        request = _design_backed_request(
            target_subsystem="L5.DifferentialEvaluator",
            request_id="build-l5-0001",
            must_pass=["evals/continuity/council_output_build_request_pipeline.yaml"],
        )
        build_artifact = PatchGeneratorService().generate_patch_set(request)

        receipt = SandboxApplyService().apply_artifact(
            build_request=request,
            build_artifact=build_artifact,
        )

        self.assertEqual("applied", receipt["status"])
        self.assertTrue(receipt["validation"]["rollback_ready"])
        self.assertEqual([], receipt["external_effects"])
        self.assertEqual(2, receipt["applied_patch_count"])


class RolloutPlannerServiceTests(unittest.TestCase):
    def test_execute_rollout_completes_fixed_stage_order_for_promote(self) -> None:
        service = RolloutPlannerService()

        session = service.execute_rollout(
            build_request={"request_id": "build-l5-0001"},
            apply_receipt={
                "receipt_id": "sandbox-apply-0123456789ab",
                "artifact_id": "artifact-0123456789ab",
                "rollback_plan_ref": "rollback://build-l5-0001",
                "continuity_log_ref": "ledger://self-modify/build-l5-0001",
                "validation": {"rollback_ready": True},
            },
            eval_reports=[
                {"eval_ref": "evals/continuity/council_output_build_request_pipeline.yaml"},
                {"eval_ref": "evals/continuity/builder_staged_rollout_execution.yaml"},
            ],
            decision="promote",
            guardian_gate_status="pass",
        )

        self.assertEqual("promoted", session["status"])
        self.assertEqual(4, session["completed_stage_count"])
        self.assertEqual(
            ["dark-launch", "canary-5pct", "broad-50pct", "full-100pct"],
            [stage["stage_id"] for stage in session["stages"]],
        )
        self.assertTrue(service.validate_session(session)["ok"])

    def test_execute_rollout_marks_canary_rollback_for_regression(self) -> None:
        service = RolloutPlannerService()

        session = service.execute_rollout(
            build_request={"request_id": "build-l5-rollback-0001"},
            apply_receipt={
                "receipt_id": "sandbox-apply-0123456789ab",
                "artifact_id": "artifact-0123456789ab",
                "rollback_plan_ref": "rollback://build-l5-rollback-0001",
                "continuity_log_ref": "ledger://self-modify/build-l5-rollback-0001",
                "validation": {"rollback_ready": True},
            },
            eval_reports=[
                {"eval_ref": "evals/continuity/council_output_build_request_pipeline.yaml"},
                {"eval_ref": "evals/continuity/builder_staged_rollout_execution.yaml"},
                {"eval_ref": "evals/continuity/builder_rollback_execution.yaml"},
            ],
            decision="rollback",
            guardian_gate_status="pass",
        )

        self.assertEqual("rolled-back", session["status"])
        self.assertEqual(
            ["completed", "rolled-back", "blocked", "blocked"],
            [stage["status"] for stage in session["stages"]],
        )
        self.assertTrue(service.validate_session(session)["ok"])


class RollbackEngineServiceTests(unittest.TestCase):
    def test_execute_rollback_restores_pre_apply_snapshot_and_notifies_watchers(self) -> None:
        service = RollbackEngineService()
        live_enactment_session = LiveEnactmentService().execute(
            build_request=_design_backed_request(
                target_subsystem="L5.RollbackEngine",
                request_id="build-l5-rollback-0001",
                must_pass=["evals/continuity/builder_live_enactment_execution.yaml"],
            ),
            build_artifact=PatchGeneratorService().generate_patch_set(
                _design_backed_request(
                    target_subsystem="L5.RollbackEngine",
                    request_id="build-l5-rollback-0001",
                    must_pass=["evals/continuity/builder_live_enactment_execution.yaml"],
                )
            ),
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=Path(__file__).resolve().parents[2],
        )

        session = service.execute_rollback(
            build_request={"request_id": "build-l5-rollback-0001"},
            apply_receipt={
                "receipt_id": "sandbox-apply-0123456789ab",
                "artifact_id": "artifact-0123456789ab",
                "rollback_plan_ref": "rollback://build-l5-rollback-0001",
                "continuity_log_ref": "ledger://self-modify/build-l5-rollback-0001",
                "status": "applied",
                "applied_patch_ids": ["patch-111111111111", "patch-222222222222"],
                "validation": {"rollback_ready": True},
            },
            rollout_session={
                "session_id": "rollout-session-0123456789ab",
                "decision": "rollback",
                "final_continuity_ref": "ledger://self-modify/build-l5-rollback-0001",
                "stages": [
                    {"stage_id": "dark-launch", "status": "completed"},
                    {"stage_id": "canary-5pct", "status": "rolled-back"},
                    {"stage_id": "broad-50pct", "status": "blocked"},
                    {"stage_id": "full-100pct", "status": "blocked"},
                ],
            },
            live_enactment_session=live_enactment_session,
            trigger="eval-regression",
            reason="Regression detected during canary rollout.",
            initiator="IntegrityGuardian",
        )

        self.assertEqual("rolled-back", session["status"])
        self.assertEqual(
            live_enactment_session["enactment_session_id"],
            session["live_enactment_session_id"],
        )
        self.assertEqual(
            "mirage://build-l5-rollback-0001/snapshot/pre-apply",
            session["restored_snapshot_ref"],
        )
        self.assertEqual(2, session["reverted_patch_count"])
        self.assertEqual(["dark-launch", "canary-5pct"], session["reverted_stage_ids"])
        self.assertEqual(2, len(session["reverse_apply_journal"]))
        self.assertEqual("rollback-approved", session["telemetry_gate"]["status"])
        self.assertEqual("removed", session["telemetry_gate"]["cleanup_status"])
        self.assertEqual(2, session["telemetry_gate"]["executed_command_count"])
        self.assertEqual(3, len(session["notification_refs"]))
        self.assertTrue(service.validate_session(session)["ok"])


class LiveEnactmentServiceTests(unittest.TestCase):
    def test_execute_materializes_temp_workspace_and_runs_eval_commands(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        request = _design_backed_request(
            target_subsystem="L5.LiveEnactment",
            request_id="build-l5-live-0001",
            must_pass=["evals/continuity/builder_live_enactment_execution.yaml"],
        )
        artifact = PatchGeneratorService().generate_patch_set(request)

        session = LiveEnactmentService().execute(
            build_request=request,
            build_artifact=artifact,
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=repo_root,
        )

        self.assertEqual("passed", session["status"])
        self.assertEqual(2, session["mutated_file_count"])
        self.assertEqual(2, session["executed_command_count"])
        self.assertTrue(session["all_commands_passed"])
        self.assertEqual("removed", session["cleanup_status"])
        self.assertTrue(LiveEnactmentService().validate_session(session)["ok"])


if __name__ == "__main__":
    unittest.main()
