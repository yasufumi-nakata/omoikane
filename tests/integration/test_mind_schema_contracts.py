from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from omoikane.reference_os import OmoikaneReferenceOS


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_schema(path: str) -> dict[str, Any]:
    schema_path = REPO_ROOT / path
    loaded = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    return _resolve_local_refs(loaded, schema_path.parent)


def _resolve_local_refs(node: Any, base_dir: Path) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#"):
            ref_path = (base_dir / ref).resolve()
            loaded = yaml.safe_load(ref_path.read_text(encoding="utf-8"))
            return _resolve_local_refs(loaded, ref_path.parent)
        return {key: _resolve_local_refs(value, base_dir) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_local_refs(item, base_dir) for item in node]
    return node


class MindSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_semantic_demo_snapshot_matches_public_schema(self) -> None:
        result = self.runtime.run_semantic_demo()

        self._assert_schema_valid(
            "specs/schemas/semantic_memory_snapshot.schema",
            result["semantic"]["snapshot"],
        )

    def test_memory_replication_demo_session_matches_public_schema(self) -> None:
        result = self.runtime.run_memory_replication_demo()

        self._assert_schema_valid(
            "specs/schemas/memory_replication_session.schema",
            result["memory_replication"]["session"],
        )
        self.assertFalse(
            result["memory_replication"]["session"]["key_succession"][
                "raw_key_material_stored"
            ]
        )
        self.assertFalse(
            result["memory_replication"]["session"]["key_succession"][
                "signer_roster_policy"
            ]["raw_signer_roster_payload_stored"]
        )
        signer_roster_quorum = result["memory_replication"]["session"]["key_succession"][
            "signer_roster_quorum"
        ]
        self.assertEqual(["JP-13", "SG-01"], signer_roster_quorum["accepted_jurisdictions"])
        self.assertEqual(2, len(signer_roster_quorum["jurisdiction_policy_digests"]))
        self.assertEqual(4, len(signer_roster_quorum["signature_digest_set"]))
        self.assertFalse(signer_roster_quorum["raw_jurisdiction_policy_payload_stored"])
        threshold_authority = signer_roster_quorum["threshold_policy_authority"]
        self.assertEqual(
            "key-succession-multi-jurisdiction-quorum-threshold-policy-v1",
            threshold_authority["policy_id"],
        )
        self.assertTrue(threshold_authority["threshold_policy_registry_bound"])
        self.assertFalse(threshold_authority["raw_threshold_policy_payload_stored"])
        self.assertFalse(threshold_authority["raw_policy_registry_payload_stored"])

    def test_semantic_demo_handoff_matches_public_schema(self) -> None:
        result = self.runtime.run_semantic_demo()

        self._assert_schema_valid(
            "specs/schemas/semantic_procedural_handoff.schema",
            result["semantic"]["procedural_handoff"],
        )

    def test_procedural_demo_snapshot_matches_public_schema(self) -> None:
        result = self.runtime.run_procedural_demo()

        self._assert_schema_valid(
            "specs/schemas/procedural_memory_preview.schema",
            result["procedural"]["snapshot"],
        )

    def test_procedural_enactment_demo_session_matches_public_schema(self) -> None:
        result = self.runtime.run_procedural_enactment_demo()
        session = result["procedural"]["skill_enactment_session"]

        self._assert_schema_valid(
            "specs/schemas/procedural_skill_enactment_session.schema",
            session,
        )
        self.assertIn(
            "evals/continuity/procedural_skill_enactment_execution.yaml",
            session["eval_refs"],
        )
        self.assertTrue(result["validation"]["enactment"]["command_eval_refs_bound"])

    def test_procedural_actuation_demo_bridge_matches_public_schema(self) -> None:
        result = self.runtime.run_procedural_actuation_demo()

        self._assert_schema_valid(
            "specs/schemas/procedural_actuation_bridge_session.schema",
            result["procedural"]["actuation_bridge_session"],
        )

    def test_self_model_demo_calibration_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_calibration_receipt.schema",
            result["calibration"],
        )
        self.assertTrue(result["validation"]["calibration"]["ok"])
        self.assertFalse(result["calibration"]["external_truth_claim_allowed"])
        self.assertFalse(result["calibration"]["forced_correction_allowed"])
        self.assertFalse(result["calibration"]["raw_external_testimony_stored"])

    def test_self_model_demo_pathology_escalation_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_pathological_self_assessment_escalation_receipt.schema",
            result["pathology_escalation"],
        )
        self.assertTrue(result["validation"]["pathology_escalation"]["ok"])
        self.assertTrue(result["pathology_escalation"]["care_handoff_required"])
        self.assertTrue(
            result["pathology_escalation"]["consent_or_emergency_review_required"]
        )
        self.assertFalse(result["pathology_escalation"]["internal_diagnosis_allowed"])
        self.assertFalse(result["pathology_escalation"]["self_model_writeback_allowed"])
        self.assertFalse(result["pathology_escalation"]["forced_correction_allowed"])
        self.assertFalse(result["pathology_escalation"]["raw_medical_payload_stored"])

    def test_self_model_demo_care_trustee_handoff_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_care_trustee_handoff_receipt.schema",
            result["care_trustee_handoff"],
        )
        self.assertTrue(result["validation"]["care_trustee_handoff"]["ok"])
        self.assertTrue(result["care_trustee_handoff"]["long_term_review_required"])
        self.assertTrue(result["care_trustee_handoff"]["external_adjudication_required"])
        self.assertEqual(
            result["pathology_escalation"]["receipt_digest"],
            result["care_trustee_handoff"]["source_escalation_receipt_digest"],
        )
        self.assertFalse(result["care_trustee_handoff"]["os_trustee_role_allowed"])
        self.assertFalse(result["care_trustee_handoff"]["os_medical_authority_allowed"])
        self.assertFalse(result["care_trustee_handoff"]["os_legal_guardianship_allowed"])
        self.assertFalse(result["care_trustee_handoff"]["self_model_writeback_allowed"])
        self.assertFalse(result["care_trustee_handoff"]["raw_trustee_payload_stored"])

    def test_self_model_demo_value_generation_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_generation_receipt.schema",
            result["value_generation"],
        )
        self.assertTrue(result["validation"]["value_generation"]["ok"])
        self.assertTrue(result["value_generation"]["autonomy_preserved"])
        self.assertFalse(result["value_generation"]["external_veto_allowed"])
        self.assertFalse(result["value_generation"]["forced_stability_lock_allowed"])
        self.assertFalse(result["value_generation"]["accepted_for_writeback"])
        self.assertFalse(result["value_generation"]["raw_value_payload_stored"])

    def test_self_model_demo_value_autonomy_review_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_autonomy_review_receipt.schema",
            result["value_autonomy_review"],
        )
        self.assertTrue(result["validation"]["value_autonomy_review"]["ok"])
        self.assertTrue(result["value_autonomy_review"]["candidate_set_unchanged"])
        self.assertTrue(result["value_autonomy_review"]["autonomy_preserved"])
        self.assertTrue(
            result["value_autonomy_review"]["future_self_acceptance_remains_required"]
        )
        self.assertFalse(result["value_autonomy_review"]["external_veto_allowed"])
        self.assertFalse(result["value_autonomy_review"]["council_override_allowed"])
        self.assertFalse(result["value_autonomy_review"]["candidate_rewrite_allowed"])
        self.assertFalse(result["value_autonomy_review"]["raw_witness_payload_stored"])

    def test_self_model_demo_value_acceptance_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_acceptance_receipt.schema",
            result["value_acceptance"],
        )
        self.assertTrue(result["validation"]["value_acceptance"]["ok"])
        self.assertTrue(result["value_acceptance"]["future_self_acceptance_satisfied"])
        self.assertTrue(result["value_acceptance"]["accepted_for_writeback"])
        self.assertTrue(result["value_acceptance"]["boundary_only_review"])
        self.assertFalse(result["value_acceptance"]["external_veto_allowed"])
        self.assertFalse(result["value_acceptance"]["raw_value_payload_stored"])

    def test_self_model_demo_value_reassessment_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_reassessment_receipt.schema",
            result["value_reassessment"],
        )
        self.assertTrue(result["validation"]["value_reassessment"]["ok"])
        self.assertTrue(
            result["validation"]["value_reassessment"][
                "future_self_reevaluation_satisfied"
            ]
        )
        self.assertTrue(result["value_reassessment"]["active_writeback_retired"])
        self.assertTrue(result["value_reassessment"]["historical_value_archived"])
        self.assertTrue(result["value_reassessment"]["boundary_only_review"])
        self.assertFalse(result["value_reassessment"]["external_veto_allowed"])
        self.assertFalse(result["value_reassessment"]["raw_value_payload_stored"])

    def test_self_model_demo_value_timeline_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_timeline_receipt.schema",
            result["value_timeline"],
        )
        self.assertTrue(result["validation"]["value_timeline"]["ok"])
        self.assertTrue(result["value_timeline"]["chronological_event_order_enforced"])
        self.assertTrue(result["value_timeline"]["active_retired_disjoint"])
        self.assertTrue(result["value_timeline"]["archive_retention_required"])
        self.assertTrue(result["value_timeline"]["boundary_only_review"])
        self.assertFalse(result["value_timeline"]["external_veto_allowed"])
        self.assertFalse(result["value_timeline"]["raw_value_payload_stored"])


if __name__ == "__main__":
    unittest.main()
