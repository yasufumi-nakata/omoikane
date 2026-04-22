from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from omoikane.governance import OversightService
from omoikane.self_construction import (
    DesignReaderService,
    DifferentialEvaluatorService,
    LiveEnactmentService,
    PatchGeneratorService,
    RollbackEngineService,
    RolloutPlannerService,
    SandboxApplyService,
)


@contextmanager
def _design_reader_demo_repo(
    *,
    design_refs: list[str],
    spec_refs: list[str],
):
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="omoikane-design-reader-test-") as temp_dir:
        fixture_root = Path(temp_dir)
        refs = design_refs + spec_refs
        for ref in refs:
            source_path = repo_root / ref
            target_path = fixture_root / ref
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

        for argv in (
            ["git", "init", "-q"],
            ["git", "config", "user.name", "Codex Builder"],
            ["git", "config", "user.email", "codex@example.invalid"],
            ["git", "add", *refs],
            ["git", "commit", "-q", "-m", "baseline"],
        ):
            completed = subprocess.run(
                argv,
                cwd=fixture_root,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"fixture command failed: {' '.join(argv)} :: {completed.stderr}")

        design_path = fixture_root / design_refs[0]
        design_path.write_text(
            design_path.read_text(encoding="utf-8")
            + "\n- delta-scan note: builder handoff narrowed before emission\n",
            encoding="utf-8",
        )
        spec_path = fixture_root / spec_refs[0]
        spec_path.write_text(
            spec_path.read_text(encoding="utf-8")
            + "\n# delta-scan note: git-bound receipt required when available\n",
            encoding="utf-8",
        )
        yield fixture_root


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
            output_paths=output_paths
            or [
                "src/omoikane/self_construction/",
                "tests/unit/",
                "docs/02-subsystems/self-construction/",
                "docs/04-ai-governance/",
                "evals/continuity/",
                "meta/decision-log/",
            ],
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


def _rollback_oversight_event(*, rollback_plan_ref: str) -> dict[str, object]:
    oversight = OversightService()
    for reviewer_id, display_name, challenge_digest, verified_at in (
        (
            "human-reviewer-rollback-alpha",
            "Rollback Review Alpha",
            "sha256:rollback-reviewer-alpha-20260421",
            "2026-04-21T00:00:00+00:00",
        ),
        (
            "human-reviewer-rollback-beta",
            "Rollback Review Beta",
            "sha256:rollback-reviewer-beta-20260421",
            "2026-04-21T00:05:00+00:00",
        ),
    ):
        oversight.register_reviewer(
            reviewer_id=reviewer_id,
            display_name=display_name,
            credential_id=f"credential-{reviewer_id}",
            attestation_type="institutional-badge",
            proof_ref=f"proof://rollback/{reviewer_id}/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-21T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref=f"legal://rollback/{reviewer_id}/v1",
            escalation_contact=f"mailto:{reviewer_id}@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        oversight.verify_reviewer_from_network(
            reviewer_id,
            verifier_ref=f"verifier://guardian-oversight.jp/{reviewer_id}",
            challenge_ref=f"challenge://rollback/{reviewer_id}/2026-04-21T00:00:00Z",
            challenge_digest=challenge_digest,
            jurisdiction_bundle_ref="legal://jp-13/rollback-integrity/v1",
            jurisdiction_bundle_digest="sha256:jp13-rollback-integrity-v1",
            verified_at=verified_at,
            valid_until="2026-10-21T00:00:00+00:00",
        )
    event = oversight.record(
        guardian_role="integrity",
        category="attest",
        payload_ref=rollback_plan_ref,
        escalation_path=["guardian-oversight.jp", "rollback-review-board"],
    )
    event = oversight.attest(event["event_id"], reviewer_id="human-reviewer-rollback-alpha")
    event = oversight.attest(event["event_id"], reviewer_id="human-reviewer-rollback-beta")
    return event


def _live_enactment_oversight_event(*, artifact_ref: str) -> dict[str, object]:
    oversight = OversightService()
    for reviewer_id, display_name, challenge_digest, verified_at in (
        (
            "human-reviewer-live-enactment-alpha",
            "Live Enactment Review Alpha",
            "sha256:live-enactment-reviewer-alpha-20260422",
            "2026-04-22T00:00:00+00:00",
        ),
        (
            "human-reviewer-live-enactment-beta",
            "Live Enactment Review Beta",
            "sha256:live-enactment-reviewer-beta-20260422",
            "2026-04-22T00:05:00+00:00",
        ),
    ):
        oversight.register_reviewer(
            reviewer_id=reviewer_id,
            display_name=display_name,
            credential_id=f"credential-{reviewer_id}",
            attestation_type="institutional-badge",
            proof_ref=f"proof://live-enactment/{reviewer_id}/v1",
            jurisdiction="JP-13",
            valid_until="2027-04-22T00:00:00+00:00",
            liability_mode="joint",
            legal_ack_ref=f"legal://live-enactment/{reviewer_id}/v1",
            escalation_contact=f"mailto:{reviewer_id}@example.invalid",
            allowed_guardian_roles=["integrity"],
            allowed_categories=["attest"],
        )
        oversight.verify_reviewer_from_network(
            reviewer_id,
            verifier_ref=f"verifier://guardian-oversight.jp/{reviewer_id}",
            challenge_ref=f"challenge://live-enactment/{reviewer_id}/2026-04-22T00:00:00Z",
            challenge_digest=challenge_digest,
            jurisdiction_bundle_ref="legal://jp-13/live-enactment/v1",
            jurisdiction_bundle_digest="sha256:jp13-live-enactment-v1",
            verified_at=verified_at,
            valid_until="2026-10-22T00:00:00+00:00",
        )
    event = oversight.record(
        guardian_role="integrity",
        category="attest",
        payload_ref=artifact_ref,
        escalation_path=["guardian-oversight.jp", "live-enactment-review-board"],
    )
    event = oversight.attest(
        event["event_id"], reviewer_id="human-reviewer-live-enactment-alpha"
    )
    event = oversight.attest(
        event["event_id"], reviewer_id="human-reviewer-live-enactment-beta"
    )
    return event


class DesignReaderServiceTests(unittest.TestCase):
    def test_scan_repo_delta_detects_modified_design_and_spec_refs(self) -> None:
        reader = DesignReaderService()
        design_refs = [
            "docs/02-subsystems/self-construction/README.md",
            "docs/04-ai-governance/codex-as-builder.md",
        ]
        spec_refs = [
            "specs/interfaces/selfctor.design_reader.v0.idl",
            "specs/schemas/design_delta_manifest.schema",
        ]

        with _design_reader_demo_repo(design_refs=design_refs, spec_refs=spec_refs) as fixture_root:
            receipt = reader.scan_repo_delta(
                design_refs=design_refs,
                spec_refs=spec_refs,
                repo_root=fixture_root,
            )

        self.assertEqual("delta-detected", receipt["status"])
        self.assertEqual(4, receipt["ref_count"])
        self.assertEqual(2, receipt["changed_ref_count"])
        self.assertEqual(1, receipt["changed_design_ref_count"])
        self.assertEqual(1, receipt["changed_spec_ref_count"])
        self.assertEqual(2, receipt["changed_section_count"])
        self.assertEqual(2, len(receipt["command_receipts"]))
        self.assertTrue(str(receipt["receipt_ref"]).startswith("design-scan://"))
        changed_refs = {
            entry["ref"]: entry["change_status"]
            for entry in receipt["entries"]
            if entry["change_status"] != "unchanged"
        }
        self.assertEqual(
            {
                "docs/02-subsystems/self-construction/README.md": "modified",
                "specs/interfaces/selfctor.design_reader.v0.idl": "modified",
            },
            changed_refs,
        )
        changed_sections = {
            entry["ref"]: entry["changed_section_count"]
            for entry in receipt["entries"]
            if entry["change_status"] != "unchanged"
        }
        self.assertEqual(
            {
                "docs/02-subsystems/self-construction/README.md": 1,
                "specs/interfaces/selfctor.design_reader.v0.idl": 1,
            },
            changed_sections,
        )

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
                "meta/decision-log/",
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
        self.assertEqual(
            [
                "runtime-source",
                "test-coverage",
                "docs-sync",
                "meta-decision-log",
                "eval-sync",
            ],
            [cue["cue_kind"] for cue in request["planning_cues"]],
        )

    def test_prepare_build_request_rejects_blocked_manifest(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        reader = DesignReaderService()
        blocked_manifest = reader.finalize_manifest(
            reader.read_design_delta(
                target_subsystem="L5.DesignReader",
                change_summary="Blocked manifest",
                design_refs=["docs/02-subsystems/self-construction/README.md"],
                spec_refs=["specs/interfaces/selfctor.design_reader.v0.idl"],
                workspace_scope=["src/", "tests/", "specs/", "evals/", "docs/", "meta/decision-log/"],
                output_paths=["src/omoikane/self_construction/"],
                must_sync_docs=["docs/04-ai-governance/codex-as-builder.md"],
                repo_root=repo_root,
            )
        )

        self.assertEqual("blocked", blocked_manifest["status"])
        with self.assertRaises(ValueError):
            reader.prepare_build_request(
                manifest=blocked_manifest,
                request_id="build-l5-design-reader-blocked",
                change_class="feature-improvement",
                must_pass=["evals/continuity/design_reader_handoff.yaml"],
                council_session_id="sess-build-l5-design-reader-blocked",
                guardian_gate="pass",
            )


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
        self.assertEqual(5, len(result["patches"]))
        self.assertEqual(
            [
                "runtime-source",
                "test-coverage",
                "eval-sync",
                "docs-sync",
                "meta-decision-log",
            ],
            [patch["cue_kind"] for patch in result["patches"]],
        )
        self.assertEqual(
            [
                "src/omoikane/self_construction/builders.py",
                "tests/unit/test_builders.py",
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "docs/02-subsystems/self-construction/README.md",
                "meta/decision-log/build-l5-0001.md",
            ],
            [patch["target_path"] for patch in result["patches"]],
        )
        self.assertEqual("pass", result["test_results"]["build_status"])
        self.assertEqual(
            "ledger://self-modify/build-l5-0001",
            result["continuity_log_ref"],
        )

    def test_generate_patch_set_uses_design_reader_target_when_requested(self) -> None:
        service = PatchGeneratorService()
        request = _design_backed_request(
            target_subsystem="L5.DesignReader",
            request_id="build-l5-design-reader-0002",
            must_pass=["evals/continuity/design_reader_handoff.yaml"],
        )

        result = service.generate_patch_set(request)

        self.assertEqual("ready", result["status"])
        self.assertEqual(
            "src/omoikane/self_construction/design_reader.py",
            result["patches"][0]["target_path"],
        )
        self.assertIn("L5.DesignReader", result["patches"][0]["summary"])
        self.assertEqual(
            "tests/unit/test_builders.py",
            result["patches"][1]["target_path"],
        )
        self.assertEqual(
            "evals/continuity/design_reader_handoff.yaml",
            result["patches"][2]["target_path"],
        )


class DifferentialEvaluatorServiceTests(unittest.TestCase):
    def test_select_suite_preserves_requested_eval_and_mandatory_guard(self) -> None:
        service = DifferentialEvaluatorService()

        result = service.select_suite(
            target_subsystem="L5.DifferentialEvaluator",
            requested_evals=["evals/continuity/council_output_build_request_pipeline.yaml"],
        )

        self.assertEqual(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                "evals/continuity/differential_eval_execution_binding.yaml",
            ],
            result["selected_evals"],
        )

    def test_run_ab_eval_emits_structured_evidence_for_pass(self) -> None:
        service = DifferentialEvaluatorService()

        result = service.run_ab_eval(
            eval_ref="evals/continuity/council_output_build_request_pipeline.yaml",
            baseline_ref="runtime://baseline/current",
            sandbox_ref="mirage://build-l5-0001/snapshot/current",
        )

        self.assertEqual("pass", result["outcome"])
        self.assertEqual("builder-handoff-ab-evidence-v1", result["profile_id"])
        self.assertEqual("runtime", result["baseline_observation"]["scheme"])
        self.assertEqual("mirage", result["sandbox_observation"]["scheme"])
        self.assertEqual("current", result["sandbox_observation"]["state"])
        self.assertIn("sandbox-state-pass:current", result["triggered_rules"])
        self.assertFalse(result["execution_bound"])
        self.assertEqual(64, len(result["comparison_digest"]))

    def test_run_ab_eval_binds_actual_execution_receipt_when_enactment_session_exists(self) -> None:
        request = _design_backed_request(
            target_subsystem="L5.DifferentialEvaluator",
            request_id="build-l5-exec-0001",
            must_pass=["evals/continuity/differential_eval_execution_binding.yaml"],
        )
        artifact = PatchGeneratorService().generate_patch_set(request)
        enactment_session = LiveEnactmentService().execute(
            build_request=request,
            build_artifact=artifact,
            eval_refs=["evals/continuity/differential_eval_execution_binding.yaml"],
            repo_root=Path(__file__).resolve().parents[2],
            guardian_oversight_event=_live_enactment_oversight_event(
                artifact_ref=f"artifact://{artifact['artifact_id']}"
            ),
        )

        result = DifferentialEvaluatorService().run_ab_eval(
            eval_ref="evals/continuity/differential_eval_execution_binding.yaml",
            baseline_ref="runtime://baseline/current",
            sandbox_ref="mirage://build-l5-exec-0001/snapshot/current",
            enactment_session=enactment_session,
        )

        self.assertEqual("pass", result["outcome"])
        self.assertTrue(result["execution_bound"])
        self.assertEqual(
            "mirage-temp-workspace-command-binding-v1",
            result["execution_receipt"]["execution_profile_id"],
        )
        self.assertEqual(2, result["execution_receipt"]["executed_command_count"])
        self.assertTrue(result["execution_receipt"]["all_commands_passed"])
        self.assertEqual("removed", result["execution_receipt"]["cleanup_status"])
        self.assertEqual(64, len(result["execution_receipt_digest"]))
        self.assertIn("execution-commands-pass:2", result["triggered_rules"])

    def test_run_ab_eval_marks_rollback_breach_as_regression(self) -> None:
        service = DifferentialEvaluatorService()

        result = service.run_ab_eval(
            eval_ref="evals/continuity/builder_rollback_execution.yaml",
            baseline_ref="runtime://baseline/current",
            sandbox_ref="mirage://build-l5-rollback-0001/snapshot/rollback-breach",
        )

        self.assertEqual("regression", result["outcome"])
        self.assertEqual("builder-rollback-trigger-evidence-v1", result["profile_id"])
        self.assertIn("rollback", result["sandbox_observation"]["state_tokens"])
        self.assertIn("breach", result["sandbox_observation"]["state_tokens"])
        self.assertIn("sandbox-regression-tokens:breach+rollback", result["triggered_rules"])

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
        self.assertEqual(5, receipt["applied_patch_count"])


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
        request = _design_backed_request(
            target_subsystem="L5.RollbackEngine",
            request_id="build-l5-rollback-0001",
            must_pass=["evals/continuity/builder_live_enactment_execution.yaml"],
        )
        artifact = PatchGeneratorService().generate_patch_set(request)
        live_enactment_session = LiveEnactmentService().execute(
            build_request=request,
            build_artifact=artifact,
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=Path(__file__).resolve().parents[2],
            guardian_oversight_event=_live_enactment_oversight_event(
                artifact_ref=f"artifact://{artifact['artifact_id']}"
            ),
        )

        session = service.execute_rollback(
            build_request={"request_id": "build-l5-rollback-0001"},
            apply_receipt={
                "receipt_id": "sandbox-apply-0123456789ab",
                "artifact_id": "artifact-0123456789ab",
                "rollback_plan_ref": "rollback://build-l5-rollback-0001",
                "continuity_log_ref": "ledger://self-modify/build-l5-rollback-0001",
                "status": "applied",
                "applied_patch_ids": [
                    "patch-111111111111",
                    "patch-222222222222",
                    "patch-333333333333",
                    "patch-444444444444",
                    "patch-555555555555",
                ],
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
            repo_root=Path(__file__).resolve().parents[2],
            trigger="eval-regression",
            reason="Regression detected during canary rollout.",
            initiator="IntegrityGuardian",
            guardian_oversight_event=_rollback_oversight_event(
                rollback_plan_ref="rollback://build-l5-rollback-0001"
            ),
        )

        self.assertEqual("rolled-back", session["status"])
        self.assertEqual("1.6", session["schema_version"])
        self.assertEqual(
            live_enactment_session["enactment_session_id"],
            session["live_enactment_session_id"],
        )
        self.assertEqual(
            "mirage://build-l5-rollback-0001/snapshot/pre-apply",
            session["restored_snapshot_ref"],
        )
        self.assertEqual(5, session["reverted_patch_count"])
        self.assertEqual(["dark-launch", "canary-5pct"], session["reverted_stage_ids"])
        self.assertEqual(5, len(session["reverse_apply_journal"]))
        self.assertTrue(all(entry["status"] == "pass" for entry in session["reverse_apply_journal"]))
        self.assertTrue(
            all(
                entry["result_state"] in {"restored", "deleted"}
                for entry in session["reverse_apply_journal"]
            )
        )
        self.assertTrue(
            all(entry["verification_status"] == "pass" for entry in session["reverse_apply_journal"])
        )
        self.assertEqual("current-checkout-subtree", session["repo_binding_summary"]["binding_scope"])
        self.assertEqual(5, session["repo_binding_summary"]["bound_path_count"])
        self.assertEqual(5, session["repo_binding_summary"]["verified_path_count"])
        self.assertEqual("verified", session["checkout_mutation_receipt"]["status"])
        self.assertTrue(session["checkout_mutation_receipt"]["mutation_detected"])
        self.assertTrue(session["checkout_mutation_receipt"]["restored_matches_baseline"])
        self.assertEqual(5, session["checkout_mutation_receipt"]["observed_path_count"])
        self.assertEqual(5, session["checkout_mutation_receipt"]["verified_path_count"])
        self.assertEqual("verified", session["current_worktree_mutation_receipt"]["status"])
        self.assertTrue(session["current_worktree_mutation_receipt"]["mutation_detected"])
        self.assertTrue(
            session["current_worktree_mutation_receipt"]["restored_matches_baseline"]
        )
        self.assertEqual(5, session["current_worktree_mutation_receipt"]["observed_path_count"])
        self.assertEqual(5, session["current_worktree_mutation_receipt"]["verified_path_count"])
        self.assertEqual("removed", session["current_worktree_mutation_receipt"]["cleanup_status"])
        self.assertEqual(
            "repo-root-git-observer-v1",
            session["checkout_mutation_receipt"]["observer_profile"],
        )
        self.assertEqual("verified", session["checkout_mutation_receipt"]["observer_status"])
        self.assertEqual(5, session["checkout_mutation_receipt"]["observer_receipt_count"])
        self.assertTrue(session["checkout_mutation_receipt"]["observer_mutation_detected"])
        self.assertTrue(
            session["checkout_mutation_receipt"]["observer_restored_matches_baseline"]
        )
        self.assertTrue(session["checkout_mutation_receipt"]["observer_stash_state_preserved"])
        self.assertEqual("removed", session["checkout_mutation_receipt"]["cleanup_status"])
        self.assertEqual("attest", session["guardian_oversight_event"]["category"])
        self.assertEqual("integrity", session["guardian_oversight_event"]["guardian_role"])
        self.assertEqual(
            "rollback://build-l5-rollback-0001",
            session["guardian_oversight_event"]["payload_ref"],
        )
        self.assertEqual(
            "satisfied",
            session["guardian_oversight_event"]["human_attestation"]["status"],
        )
        self.assertEqual(
            2,
            session["guardian_oversight_event"]["human_attestation"]["received_quorum"],
        )
        self.assertEqual(2, len(session["guardian_oversight_event"]["reviewer_bindings"]))
        self.assertTrue(
            all(
                binding["network_receipt_id"] and binding["trust_root_ref"]
                for binding in session["guardian_oversight_event"]["reviewer_bindings"]
            )
        )
        self.assertEqual("rollback-approved", session["telemetry_gate"]["status"])
        self.assertEqual("removed", session["telemetry_gate"]["cleanup_status"])
        self.assertEqual(2, session["telemetry_gate"]["executed_command_count"])
        self.assertEqual("removed", session["telemetry_gate"]["reverse_cleanup_status"])
        self.assertEqual(5, session["telemetry_gate"]["executed_reverse_command_count"])
        self.assertEqual(5, session["telemetry_gate"]["verified_reverse_command_count"])
        self.assertEqual(5, session["telemetry_gate"]["repo_bound_verified_command_count"])
        self.assertEqual("verified", session["telemetry_gate"]["checkout_mutation_status"])
        self.assertEqual("removed", session["telemetry_gate"]["checkout_cleanup_status"])
        self.assertEqual(5, session["telemetry_gate"]["checkout_verified_path_count"])
        self.assertTrue(session["telemetry_gate"]["checkout_status_restored"])
        self.assertEqual("verified", session["telemetry_gate"]["current_worktree_mutation_status"])
        self.assertEqual("removed", session["telemetry_gate"]["current_worktree_cleanup_status"])
        self.assertEqual(5, session["telemetry_gate"]["current_worktree_verified_path_count"])
        self.assertTrue(session["telemetry_gate"]["current_worktree_status_restored"])
        self.assertTrue(session["telemetry_gate"]["current_worktree_mutation_detected"])
        self.assertEqual("verified", session["telemetry_gate"]["external_observer_status"])
        self.assertEqual(5, session["telemetry_gate"]["external_observer_receipt_count"])
        self.assertTrue(session["telemetry_gate"]["external_observer_restored"])
        self.assertTrue(session["telemetry_gate"]["external_observer_stash_preserved"])
        self.assertTrue(session["telemetry_gate"]["external_observer_mutation_detected"])
        self.assertEqual("satisfied", session["telemetry_gate"]["reviewer_oversight_status"])
        self.assertEqual(2, session["telemetry_gate"]["reviewer_quorum_required"])
        self.assertEqual(2, session["telemetry_gate"]["reviewer_quorum_received"])
        self.assertEqual(2, session["telemetry_gate"]["reviewer_binding_count"])
        self.assertEqual(2, session["telemetry_gate"]["reviewer_network_receipt_count"])
        self.assertTrue(session["telemetry_gate"]["reviewer_network_attested"])
        self.assertEqual(3, len(session["notification_refs"]))
        self.assertTrue(service.validate_session(session)["ok"])


class LiveEnactmentServiceTests(unittest.TestCase):
    def test_execute_materializes_temp_workspace_and_runs_eval_commands(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        request = _design_backed_request(
            target_subsystem="L5.LiveEnactment",
            request_id="build-l5-live-0001",
            must_pass=[
                "evals/continuity/builder_live_enactment_execution.yaml",
                "evals/continuity/builder_live_oversight_network.yaml",
            ],
        )
        artifact = PatchGeneratorService().generate_patch_set(request)

        session = LiveEnactmentService().execute(
            build_request=request,
            build_artifact=artifact,
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=repo_root,
            guardian_oversight_event=_live_enactment_oversight_event(
                artifact_ref=f"artifact://{artifact['artifact_id']}"
            ),
        )

        self.assertEqual("passed", session["status"])
        self.assertEqual("1.1", session["schema_version"])
        self.assertEqual(5, session["mutated_file_count"])
        self.assertEqual(2, session["executed_command_count"])
        self.assertTrue(session["all_commands_passed"])
        self.assertEqual("removed", session["cleanup_status"])
        self.assertEqual("satisfied", session["guardian_oversight_event"]["human_attestation"]["status"])
        self.assertEqual("enactment-approved", session["oversight_gate"]["status"])
        self.assertTrue(session["oversight_gate"]["reviewer_network_attested"])
        self.assertTrue(LiveEnactmentService().validate_session(session)["ok"])

    def test_execute_blocks_without_network_attested_oversight_event(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        request = _design_backed_request(
            target_subsystem="L5.LiveEnactment",
            request_id="build-l5-live-blocked-0001",
            must_pass=["evals/continuity/builder_live_enactment_execution.yaml"],
        )
        artifact = PatchGeneratorService().generate_patch_set(request)

        session = LiveEnactmentService().execute(
            build_request=request,
            build_artifact=artifact,
            eval_refs=["evals/continuity/builder_live_enactment_execution.yaml"],
            repo_root=repo_root,
        )

        self.assertEqual("blocked", session["status"])
        self.assertEqual(0, session["executed_command_count"])
        self.assertEqual("blocked", session["oversight_gate"]["status"])
        self.assertIn("guardian_oversight_event.kind must equal guardian_oversight_event", session["blocking_rules"])


if __name__ == "__main__":
    unittest.main()
