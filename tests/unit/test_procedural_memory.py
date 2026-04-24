from __future__ import annotations

from copy import deepcopy
import unittest

from omoikane.mind.connectome import ConnectomeModel
from omoikane.mind.memory import (
    MemoryCrystalStore,
    ProceduralActuationBridgeService,
    ProceduralMemoryProjector,
    ProceduralSkillEnactmentService,
    ProceduralSkillExecutor,
    ProceduralMemoryWritebackGate,
    SemanticMemoryProjector,
)
from omoikane.reference_os import OmoikaneReferenceOS


class ProceduralMemoryProjectorTests(unittest.TestCase):
    def test_reference_snapshot_validates(self) -> None:
        projector = ProceduralMemoryProjector()

        snapshot = projector.build_reference_snapshot("identity-demo")
        validation = projector.validate(snapshot)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["recommendation_count"])
        self.assertEqual(
            ["continuity_integrator->ethics_gate", "sensory_ingress->continuity_integrator"],
            sorted(validation["target_paths"]),
        )
        self.assertEqual(
            ["skill-execution"],
            validation["deferred_surfaces"],
        )

    def test_project_rejects_invalid_connectome_document(self) -> None:
        projector = ProceduralMemoryProjector()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        connectome_document["edges"][0]["target"] = connectome_document["edges"][0]["id"]

        with self.assertRaisesRegex(ValueError, "unknown node"):
            projector.project("identity-demo", manifest, connectome_document)

    def test_validate_rejects_recommendation_count_mismatch(self) -> None:
        projector = ProceduralMemoryProjector()
        snapshot = projector.build_reference_snapshot("identity-demo")
        snapshot["recommendation_count"] = 1

        validation = projector.validate(snapshot)

        self.assertFalse(validation["ok"])
        self.assertTrue(
            any("recommendation_count" in error for error in validation["errors"])
        )

    def test_project_from_handoff_returns_valid_preview(self) -> None:
        semantic = SemanticMemoryProjector()
        projector = ProceduralMemoryProjector()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        semantic_snapshot = semantic.project("identity-demo", manifest)
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        handoff = semantic.prepare_procedural_handoff(
            "identity-demo",
            semantic_snapshot,
            connectome_document,
        )

        snapshot = projector.project_from_handoff(
            "identity-demo",
            handoff,
            manifest,
            connectome_document,
        )
        validation = projector.validate(snapshot)

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["recommendation_count"])

    def test_project_from_handoff_rejects_connectome_digest_mismatch(self) -> None:
        semantic = SemanticMemoryProjector()
        projector = ProceduralMemoryProjector()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        semantic_snapshot = semantic.project("identity-demo", manifest)
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        handoff = semantic.prepare_procedural_handoff(
            "identity-demo",
            semantic_snapshot,
            connectome_document,
        )
        handoff["connectome_snapshot_digest"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "semantic procedural handoff"):
            projector.project_from_handoff(
                "identity-demo",
                handoff,
                manifest,
                connectome_document,
            )


class ProceduralMemoryWritebackGateTests(unittest.TestCase):
    def test_apply_returns_valid_receipt_and_updated_connectome(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)

        result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )
        validation = gate.validate(
            result["receipt"],
            result["updated_connectome_document"],
            preview_snapshot,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["applied_recommendation_count"])
        self.assertEqual(
            ["human://reviewers/alice", "human://reviewers/bob"],
            validation["human_reviewers"],
        )
        self.assertNotEqual(
            connectome_document["snapshot_id"],
            result["updated_connectome_document"]["snapshot_id"],
        )
        self.assertEqual("approved", result["receipt"]["status"])

    def test_apply_rejects_missing_human_quorum(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)

        with self.assertRaisesRegex(PermissionError, "at least 2 human reviewers"):
            gate.apply(
                "identity-demo",
                preview_snapshot,
                connectome_document,
                self_attestation_id="self://procedural-writeback/test-001",
                council_attestation_id="council://procedural-writeback/test-001",
                guardian_attestation_id="guardian://procedural-writeback/test-001",
                human_reviewers=["human://reviewers/alice"],
                approval_reason="reviewer quorum 不足",
            )


class ProceduralSkillExecutorTests(unittest.TestCase):
    def test_execute_returns_valid_sandbox_receipt(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        executor = ProceduralSkillExecutor()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)
        writeback_result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )

        receipt = executor.execute(
            "identity-demo",
            writeback_result["receipt"],
            writeback_result["updated_connectome_document"],
            sandbox_session_id="sandbox://procedural-skill/test-001",
            guardian_witness_id="guardian://procedural-skill/test-001",
        )
        validation = executor.validate(
            receipt,
            writeback_result["updated_connectome_document"],
            writeback_result["receipt"],
        )

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["execution_count"])
        self.assertEqual(
            ["guardian-review-rehearsal", "migration-handoff-rehearsal"],
            sorted(validation["skill_labels"]),
        )
        self.assertEqual("sandbox-complete", receipt["status"])
        self.assertEqual([], receipt["external_effects"])

    def test_execute_rejects_unknown_recommendation_id(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        executor = ProceduralSkillExecutor()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)
        writeback_result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )

        with self.assertRaisesRegex(ValueError, "unknown ids"):
            executor.execute(
                "identity-demo",
                writeback_result["receipt"],
                writeback_result["updated_connectome_document"],
                sandbox_session_id="sandbox://procedural-skill/test-001",
                guardian_witness_id="guardian://procedural-skill/test-001",
                selected_recommendation_ids=["procedural-missing"],
            )


class ProceduralSkillEnactmentServiceTests(unittest.TestCase):
    def test_execute_returns_valid_temp_workspace_session(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        executor = ProceduralSkillExecutor()
        enactment = ProceduralSkillEnactmentService()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)
        writeback_result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )
        execution_receipt = executor.execute(
            "identity-demo",
            writeback_result["receipt"],
            writeback_result["updated_connectome_document"],
            sandbox_session_id="sandbox://procedural-skill/test-001",
            guardian_witness_id="guardian://procedural-skill/test-001",
        )

        session = enactment.execute(
            "identity-demo",
            execution_receipt,
            writeback_result["updated_connectome_document"],
            eval_refs=["evals/continuity/procedural_skill_enactment_execution.yaml"],
        )
        validation = enactment.validate_session(
            session,
            writeback_result["updated_connectome_document"],
            execution_receipt,
        )

        self.assertTrue(validation["ok"])
        self.assertEqual(2, validation["materialized_skill_count"])
        self.assertEqual(2, validation["executed_command_count"])
        self.assertTrue(validation["all_commands_passed"])
        self.assertEqual("removed", validation["cleanup_status"])
        self.assertEqual("passed", validation["enactment_status"])
        self.assertEqual(
            ["guardian-review-rehearsal", "migration-handoff-rehearsal"],
            sorted(validation["skill_labels"]),
        )
        self.assertTrue(validation["rollback_token_preserved"])
        self.assertTrue(validation["mandatory_eval_bound"])
        self.assertTrue(validation["command_eval_refs_bound"])
        self.assertTrue(validation["temp_workspace_removed"])
        self.assertEqual("passed", session["status"])

    def test_validate_session_rejects_command_eval_ref_not_listed(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        executor = ProceduralSkillExecutor()
        enactment = ProceduralSkillEnactmentService()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)
        writeback_result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )
        execution_receipt = executor.execute(
            "identity-demo",
            writeback_result["receipt"],
            writeback_result["updated_connectome_document"],
            sandbox_session_id="sandbox://procedural-skill/test-001",
            guardian_witness_id="guardian://procedural-skill/test-001",
        )
        session = enactment.execute(
            "identity-demo",
            execution_receipt,
            writeback_result["updated_connectome_document"],
            eval_refs=["evals/continuity/procedural_skill_enactment_execution.yaml"],
        )
        tampered_session = deepcopy(session)
        tampered_session["command_runs"][0]["eval_ref"] = "evals/continuity/unlisted.yaml"

        validation = enactment.validate_session(
            tampered_session,
            writeback_result["updated_connectome_document"],
            execution_receipt,
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["command_eval_refs_bound"])
        self.assertTrue(
            any("eval_ref must be listed in eval_refs" in error for error in validation["errors"])
        )

    def test_execute_rejects_invalid_eval_refs(self) -> None:
        projector = ProceduralMemoryProjector()
        gate = ProceduralMemoryWritebackGate()
        executor = ProceduralSkillExecutor()
        enactment = ProceduralSkillEnactmentService()
        manifest = MemoryCrystalStore().build_reference_manifest("identity-demo")
        connectome_document = ConnectomeModel().build_reference_snapshot("identity-demo")
        preview_snapshot = projector.project("identity-demo", manifest, connectome_document)
        writeback_result = gate.apply(
            "identity-demo",
            preview_snapshot,
            connectome_document,
            self_attestation_id="self://procedural-writeback/test-001",
            council_attestation_id="council://procedural-writeback/test-001",
            guardian_attestation_id="guardian://procedural-writeback/test-001",
            human_reviewers=["human://reviewers/alice", "human://reviewers/bob"],
            approval_reason="bounded preview を writeback として適用する",
        )
        execution_receipt = executor.execute(
            "identity-demo",
            writeback_result["receipt"],
            writeback_result["updated_connectome_document"],
            sandbox_session_id="sandbox://procedural-skill/test-001",
            guardian_witness_id="guardian://procedural-skill/test-001",
        )

        with self.assertRaisesRegex(ValueError, "eval path"):
            enactment.execute(
                "identity-demo",
                execution_receipt,
                writeback_result["updated_connectome_document"],
                eval_refs=["procedural-skill-enactment"],
            )


class ProceduralActuationBridgeServiceTests(unittest.TestCase):
    def test_runtime_bridge_binds_enactment_to_ewa_authorization(self) -> None:
        runtime = OmoikaneReferenceOS()

        result = runtime.run_procedural_actuation_demo()
        bridge = result["procedural"]["actuation_bridge_session"]
        validation = result["validation"]["bridge"]

        self.assertTrue(result["validation"]["ok"])
        self.assertTrue(validation["ok"])
        self.assertTrue(validation["source_enactment_bound"])
        self.assertTrue(validation["authorization_digest_bound"])
        self.assertTrue(validation["authorization_validation_bound"])
        self.assertTrue(validation["command_bound_to_authorization"])
        self.assertTrue(validation["stop_signal_adapter_receipt_bound"])
        self.assertTrue(validation["legal_execution_bound"])
        self.assertTrue(validation["guardian_oversight_gate_bound"])
        self.assertTrue(validation["no_raw_instruction_text"])
        self.assertTrue(validation["rollback_token_preserved"])
        self.assertEqual(
            result["ewa"]["stop_signal_adapter_receipt"]["receipt_id"],
            bridge["command_binding"]["stop_signal_adapter_receipt_id"],
        )
        self.assertEqual("physical-device-actuation", validation["delivery_scope"])
        self.assertEqual("bridged", bridge["status"])
        self.assertEqual(
            1,
            result["ledger_verification"]["category_counts"][
                "procedural-actuation-bridge"
            ],
        )

    def test_validate_session_rejects_command_authorization_drift(self) -> None:
        runtime = OmoikaneReferenceOS()
        result = runtime.run_procedural_actuation_demo()
        tampered_command = dict(result["ewa"]["approved_command"])
        tampered_command["approval_path"] = dict(tampered_command["approval_path"])
        tampered_command["approval_path"]["authorization_id"] = "ewa-authz-tampered"

        validation = ProceduralActuationBridgeService().validate_session(
            result["procedural"]["actuation_bridge_session"],
            enactment_session=result["procedural"]["skill_enactment_session"],
            authorization=result["ewa"]["authorization"],
            approved_command=tampered_command,
            authorization_validation=result["ewa"]["authorization_validation"],
        )

        self.assertFalse(validation["ok"])
        self.assertFalse(validation["command_bound_to_authorization"])


if __name__ == "__main__":
    unittest.main()
