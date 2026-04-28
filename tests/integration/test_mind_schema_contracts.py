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
        media_renewal = result["memory_replication"]["session"][
            "long_term_media_renewal"
        ]
        self.assertEqual("long-term-media-renewal-proof-v1", media_renewal["policy_id"])
        self.assertEqual(["coldstore", "trustee"], media_renewal["renewal_target_ids"])
        self.assertEqual(2, len(media_renewal["proof_digest_set"]))
        self.assertEqual(2, len(media_renewal["readback_digest_set"]))
        self.assertFalse(media_renewal["raw_media_payload_stored"])
        self.assertFalse(media_renewal["raw_media_readback_payload_stored"])
        cadence_policy = media_renewal["cadence_policy"]
        self.assertEqual(
            "long-term-media-renewal-cadence-policy-v1",
            cadence_policy["policy_id"],
        )
        self.assertEqual(3650, cadence_policy["effective_refresh_interval_days"])
        self.assertEqual(90, cadence_policy["effective_revocation_check_window_days"])
        self.assertFalse(cadence_policy["raw_identity_cadence_payload_stored"])
        self.assertFalse(cadence_policy["raw_jurisdiction_cadence_payload_stored"])
        refresh_window = media_renewal["refresh_window"]
        self.assertEqual(
            "long-term-media-renewal-refresh-window-v1",
            refresh_window["policy_id"],
        )
        self.assertEqual(
            cadence_policy["cadence_commit_digest"],
            refresh_window["cadence_policy_digest"],
        )
        self.assertEqual("current-not-revoked", refresh_window["source_proof_status"])
        self.assertEqual("within-window", refresh_window["refresh_status"])
        self.assertEqual(90, refresh_window["revocation_check_window_days"])
        self.assertTrue(refresh_window["stale_source_fail_closed"])
        self.assertTrue(refresh_window["revoked_source_fail_closed"])
        self.assertFalse(refresh_window["raw_revocation_payload_stored"])
        self.assertFalse(refresh_window["raw_refresh_payload_stored"])
        registry_verifier = refresh_window["registry_verifier"]
        endpoint_certificate_lifecycle = registry_verifier[
            "endpoint_certificate_lifecycle"
        ]
        self.assertEqual(
            "long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1",
            endpoint_certificate_lifecycle["policy_id"],
        )
        self.assertEqual(
            registry_verifier["response_digest_set"],
            endpoint_certificate_lifecycle["registry_response_digest_set"],
        )
        self.assertEqual(
            3,
            endpoint_certificate_lifecycle["certificate_lifecycle_generation_count"],
        )
        self.assertEqual(
            4,
            len(endpoint_certificate_lifecycle["previous_certificate_refs"]),
        )
        self.assertEqual(
            4,
            len(endpoint_certificate_lifecycle["previous_retirement_digest_set"]),
        )
        self.assertEqual("complete", endpoint_certificate_lifecycle["quorum_status"])
        self.assertEqual("current", endpoint_certificate_lifecycle["freshness_status"])
        self.assertEqual(
            "long-term-media-renewal-registry-endpoint-certificate-ct-log-readback-v1",
            endpoint_certificate_lifecycle["ct_log_readback_policy_id"],
        )
        self.assertEqual(
            "long-term-media-renewal-registry-endpoint-certificate-ct-log-quorum-v1",
            endpoint_certificate_lifecycle["ct_log_quorum_policy_id"],
        )
        self.assertEqual(
            "long-term-media-renewal-registry-endpoint-certificate-sct-policy-authority-v1",
            endpoint_certificate_lifecycle["sct_policy_authority_policy_id"],
        )
        self.assertEqual("current", endpoint_certificate_lifecycle["ct_log_readback_status"])
        self.assertEqual("complete", endpoint_certificate_lifecycle["ct_log_quorum_status"])
        self.assertEqual(
            "verified",
            endpoint_certificate_lifecycle["sct_policy_authority_status"],
        )
        self.assertEqual(2, len(endpoint_certificate_lifecycle["ct_log_refs"]))
        self.assertEqual(2, len(endpoint_certificate_lifecycle["ct_log_refs"][0]))
        self.assertEqual(2, len(endpoint_certificate_lifecycle["ct_log_quorum_digest_set"]))
        self.assertEqual(2, len(endpoint_certificate_lifecycle["sct_policy_authority_digest_set"]))
        self.assertFalse(
            endpoint_certificate_lifecycle["raw_certificate_payload_stored"]
        )
        self.assertFalse(
            endpoint_certificate_lifecycle[
                "raw_certificate_freshness_payload_stored"
            ]
        )
        self.assertFalse(
            endpoint_certificate_lifecycle[
                "raw_certificate_lifecycle_payload_stored"
            ]
        )
        self.assertFalse(
            endpoint_certificate_lifecycle[
                "raw_certificate_ct_log_payload_stored"
            ]
        )
        self.assertFalse(
            endpoint_certificate_lifecycle[
                "raw_sct_policy_authority_payload_stored"
            ]
        )

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

    def test_self_model_demo_external_adjudication_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_external_adjudication_result_receipt.schema",
            result["external_adjudication"],
        )
        self.assertTrue(result["validation"]["external_adjudication"]["ok"])
        self.assertTrue(
            result["external_adjudication"]["external_adjudication_result_bound"]
        )
        self.assertTrue(result["external_adjudication"]["jurisdiction_policy_bound"])
        self.assertTrue(
            result["external_adjudication"]["appeal_or_review_path_required"]
        )
        self.assertEqual(
            result["care_trustee_handoff"]["receipt_digest"],
            result["external_adjudication"]["source_handoff_receipt_digest"],
        )
        self.assertFalse(
            result["external_adjudication"]["os_adjudication_authority_allowed"]
        )
        self.assertFalse(result["external_adjudication"]["os_medical_authority_allowed"])
        self.assertFalse(result["external_adjudication"]["os_legal_authority_allowed"])
        self.assertFalse(result["external_adjudication"]["os_trustee_role_allowed"])
        self.assertFalse(result["external_adjudication"]["self_model_writeback_allowed"])
        self.assertFalse(
            result["external_adjudication"]["raw_medical_result_payload_stored"]
        )

    def test_self_model_demo_external_adjudication_verifier_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_external_adjudication_verifier_receipt.schema",
            result["external_adjudication_verifier"],
        )
        self.assertTrue(result["validation"]["external_adjudication_verifier"]["ok"])
        self.assertEqual(
            "complete",
            result["external_adjudication_verifier"]["verifier_quorum_status"],
        )
        self.assertTrue(
            result["external_adjudication_verifier"][
                "appeal_review_live_verifier_bound"
            ]
        )
        self.assertTrue(
            result["external_adjudication_verifier"][
                "jurisdiction_policy_live_verifier_bound"
            ]
        )
        self.assertTrue(result["external_adjudication_verifier"]["freshness_window_bound"])
        self.assertFalse(result["external_adjudication_verifier"]["stale_response_accepted"])
        self.assertFalse(result["external_adjudication_verifier"]["revoked_response_accepted"])
        self.assertFalse(
            result["external_adjudication_verifier"][
                "os_adjudication_authority_allowed"
            ]
        )
        self.assertFalse(
            result["external_adjudication_verifier"]["raw_verifier_payload_stored"]
        )

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

    def test_self_model_demo_value_archive_retention_proof_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_archive_retention_proof.schema",
            result["value_archive_retention_proof"],
        )
        self.assertTrue(result["validation"]["value_archive_retention_proof"]["ok"])
        self.assertTrue(
            result["value_archive_retention_proof"]["timeline_archive_retention_verified"]
        )
        self.assertTrue(result["value_archive_retention_proof"]["trustee_proof_bound"])
        self.assertTrue(
            result["value_archive_retention_proof"]["long_term_storage_proof_bound"]
        )
        self.assertTrue(result["value_archive_retention_proof"]["retention_policy_bound"])
        self.assertTrue(result["value_archive_retention_proof"]["retrieval_test_bound"])
        self.assertFalse(result["value_archive_retention_proof"]["archive_deletion_allowed"])
        self.assertFalse(result["value_archive_retention_proof"]["raw_archive_payload_stored"])

    def test_self_model_demo_value_archive_retention_refresh_matches_public_schema(self) -> None:
        result = self.runtime.run_self_model_demo()

        self._assert_schema_valid(
            "specs/schemas/self_model_value_archive_retention_refresh_receipt.schema",
            result["value_archive_retention_refresh"],
        )
        self.assertTrue(result["validation"]["value_archive_retention_refresh"]["ok"])
        self.assertTrue(result["value_archive_retention_refresh"]["refresh_window_bound"])
        self.assertTrue(result["value_archive_retention_refresh"]["revocation_check_bound"])
        self.assertTrue(
            result["value_archive_retention_refresh"]["retention_policy_still_bound"]
        )
        self.assertTrue(result["value_archive_retention_refresh"]["expiry_fail_closed"])
        self.assertFalse(result["value_archive_retention_refresh"]["source_proof_revoked"])
        self.assertFalse(
            result["value_archive_retention_refresh"]["expired_source_proof_accepted"]
        )
        self.assertFalse(result["value_archive_retention_refresh"]["archive_deletion_allowed"])
        self.assertFalse(result["value_archive_retention_refresh"]["raw_revocation_payload_stored"])


if __name__ == "__main__":
    unittest.main()
