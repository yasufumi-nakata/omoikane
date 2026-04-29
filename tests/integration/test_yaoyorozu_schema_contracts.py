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


class YaoyorozuSchemaContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = OmoikaneReferenceOS()

    def _assert_schema_valid(self, schema_path: str, payload: dict[str, Any]) -> None:
        schema = _load_schema(schema_path)
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            formatted = "\n".join(error.message for error in errors[:5])
            self.fail(f"{schema_path} validation failed:\n{formatted}")

    def test_yaoyorozu_registry_snapshot_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_registry_snapshot.schema",
            result["registry"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_source_manifest_ledger_binding.schema",
            result["source_manifest_ledger_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_source_manifest_public_verification_bundle.schema",
            result["source_manifest_ledger_binding"]["public_verification_bundle"],
        )
        self.assertTrue(result["source_manifest_ledger_binding"]["validation"]["ok"])
        self.assertTrue(
            result["source_manifest_ledger_binding"]["validation"][
                "public_verification_bundle_bound"
            ]
        )
        self.assertTrue(
            result["source_manifest_ledger_binding"]["validation"][
                "public_verification_bundle_digest_bound"
            ]
        )
        self.assertEqual(
            "yaoyorozu-agent-source-manifest",
            result["source_manifest_ledger_binding"]["continuity_ledger_category"],
        )
        self.assertEqual(
            ["self", "guardian"],
            result["source_manifest_ledger_binding"]["continuity_ledger_signature_roles"],
        )
        public_bundle = result["source_manifest_ledger_binding"]["public_verification_bundle"]
        self.assertTrue(public_bundle["public_verification_ready"])
        self.assertEqual(
            result["source_manifest_ledger_binding"]["public_verification_bundle_ref"],
            public_bundle["bundle_ref"],
        )
        self.assertEqual(
            result["source_manifest_ledger_binding"]["public_verification_bundle_digest"],
            public_bundle["bundle_digest"],
        )
        self.assertEqual(
            result["registry"]["registry_digest"],
            public_bundle["registry_digest"],
        )
        self.assertEqual(
            result["registry"]["source_manifest_digest"],
            public_bundle["source_manifest_digest"],
        )
        self.assertEqual(["self", "guardian"], public_bundle["continuity_ledger_signature_roles"])
        self.assertEqual({"self", "guardian"}, set(public_bundle["signature_digests"]))
        self.assertFalse(public_bundle["raw_source_payload_exposed"])
        self.assertFalse(public_bundle["raw_registry_payload_exposed"])
        self.assertFalse(public_bundle["raw_continuity_event_payload_exposed"])
        self.assertFalse(public_bundle["raw_signature_payload_exposed"])
        self.assertFalse(result["source_manifest_ledger_binding"]["raw_registry_payload_stored"])
        researcher_entries = [
            entry for entry in result["registry"]["entries"] if entry["role"] == "researcher"
        ]
        self.assertTrue(researcher_entries)
        for entry in researcher_entries:
            self.assertTrue(entry["research_domain_refs"], entry["agent_id"])
            self.assertTrue(entry["evidence_policy_ref"], entry["agent_id"])
            self.assertEqual(
                "specs/schemas/research_evidence_request.schema",
                entry["input_schema_ref"],
            )
            self.assertEqual(
                "specs/schemas/research_evidence_report.schema",
                entry["output_schema_ref"],
            )
        councilor_entries = [
            entry for entry in result["registry"]["entries"] if entry["role"] == "councilor"
        ]
        self.assertTrue(councilor_entries)
        for entry in councilor_entries:
            self.assertTrue(entry["deliberation_scope_refs"], entry["agent_id"])
            self.assertTrue(entry["deliberation_policy_ref"], entry["agent_id"])
        builder_entries = [
            entry for entry in result["registry"]["entries"] if entry["role"] == "builder"
        ]
        self.assertTrue(builder_entries)
        for entry in builder_entries:
            self.assertTrue(entry["build_surface_refs"], entry["agent_id"])
            self.assertTrue(entry["execution_policy_ref"], entry["agent_id"])
        guardian_entries = [
            entry for entry in result["registry"]["entries"] if entry["role"] == "guardian"
        ]
        self.assertTrue(guardian_entries)
        for entry in guardian_entries:
            self.assertTrue(entry["oversight_scope_refs"], entry["agent_id"])
            self.assertTrue(entry["attestation_policy_ref"], entry["agent_id"])

    def test_repo_agent_sources_match_public_schema(self) -> None:
        schema = _load_schema("specs/schemas/agent_source_definition.schema")
        validator = jsonschema.Draft202012Validator(schema)

        for source_path in sorted((REPO_ROOT / "agents").rglob("*.yaml")):
            payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
            errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
            if errors:
                formatted = "\n".join(error.message for error in errors[:5])
                self.fail(f"{source_path.relative_to(REPO_ROOT)} validation failed:\n{formatted}")

    def test_research_evidence_examples_match_public_schemas(self) -> None:
        for schema_path in (
            "specs/schemas/agent_registry_entry.schema",
            "specs/schemas/research_evidence_request.schema",
            "specs/schemas/research_evidence_report.schema",
            "specs/schemas/yaoyorozu_research_evidence_exchange.schema",
            "specs/schemas/yaoyorozu_research_evidence_synthesis.schema",
        ):
            schema = _load_schema(schema_path)
            validator = jsonschema.Draft202012Validator(schema)
            for index, payload in enumerate(schema.get("examples", []), start=1):
                errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
                if errors:
                    formatted = "\n".join(error.message for error in errors[:5])
                    self.fail(f"{schema_path} example {index} validation failed:\n{formatted}")

    def test_research_evidence_exchange_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()
        exchange = result["research_evidence_exchange"]

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_research_evidence_exchange.schema",
            exchange,
        )
        self.assertTrue(exchange["validation"]["ok"])
        self.assertEqual("neuroscience-scout", exchange["researcher_agent_id"])
        self.assertEqual(
            "specs/schemas/research_evidence_request.schema",
            exchange["input_schema_ref"],
        )
        self.assertEqual(
            "specs/schemas/research_evidence_report.schema",
            exchange["output_schema_ref"],
        )
        self.assertEqual(
            exchange["request_ref"],
            exchange["report"]["request_ref"],
        )
        self.assertTrue(exchange["validation"]["request_digest_bound"])
        self.assertTrue(exchange["validation"]["report_digest_bound"])
        self.assertTrue(exchange["validation"]["exchange_digest_bound"])
        self.assertTrue(exchange["validation"]["evidence_refs_bound"])
        self.assertTrue(exchange["validation"]["evidence_digests_bound"])
        self.assertTrue(exchange["validation"]["advisory_only"])
        self.assertTrue(exchange["validation"]["continuity_ledger_entry_appended"])
        self.assertEqual(
            ["council", "guardian"],
            exchange["continuity_ledger_signature_roles"],
        )
        self.assertFalse(exchange["validation"]["raw_research_payload_stored"])
        self.assertFalse(exchange["validation"]["decision_authority_claimed"])

    def test_research_evidence_synthesis_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()
        synthesis = result["research_evidence_synthesis"]

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_research_evidence_synthesis.schema",
            synthesis,
        )
        self.assertTrue(synthesis["validation"]["ok"])
        self.assertGreaterEqual(synthesis["exchange_count"], 2)
        self.assertGreaterEqual(len(synthesis["researcher_agent_ids"]), 2)
        self.assertEqual(
            [exchange["exchange_ref"] for exchange in result["research_evidence_exchanges"]],
            synthesis["exchange_refs"],
        )
        self.assertEqual(
            [
                exchange["exchange_digest"]
                for exchange in result["research_evidence_exchanges"]
            ],
            synthesis["exchange_digests"],
        )
        self.assertTrue(synthesis["validation"]["exchange_validations_bound"])
        self.assertTrue(synthesis["validation"]["evidence_digest_set_bound"])
        self.assertTrue(synthesis["validation"]["advisory_only"])
        self.assertTrue(synthesis["validation"]["continuity_ledger_entry_appended"])
        self.assertEqual(
            ["council", "guardian"],
            synthesis["continuity_ledger_signature_roles"],
        )
        self.assertFalse(synthesis["validation"]["raw_exchange_payload_stored"])
        self.assertFalse(synthesis["validation"]["raw_research_payload_stored"])
        self.assertFalse(synthesis["validation"]["decision_authority_claimed"])

    def test_workspace_discovery_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )

    def test_council_convocation_session_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self.assertTrue(result["convocation"]["validation"]["standing_role_scope_binding_ok"])
        self.assertTrue(result["convocation"]["validation"]["council_panel_scope_binding_ok"])
        self.assertTrue(result["convocation"]["validation"]["builder_handoff_scope_binding_ok"])
        self.assertFalse(result["convocation"]["validation"]["raw_selection_scope_payload_stored"])
        self.assertEqual(
            "oversight",
            result["convocation"]["standing_roles"]["guardian_liaison"]["role_scope_kind"],
        )
        self.assertEqual(
            "deliberation",
            result["convocation"]["council_panel"][0]["role_scope_kind"],
        )
        self.assertEqual(
            "build-surface",
            result["convocation"]["builder_handoff"][0]["role_scope_kind"],
        )
        self.assertEqual(
            "coverage-area-target-path-binding-v1",
            result["convocation"]["builder_handoff"][0]["coverage_scope_binding_profile"],
        )
        self.assertTrue(result["convocation"]["builder_handoff"][0]["coverage_targets_bound"])
        self.assertEqual(
            ["src/omoikane/", "tests/unit/", "tests/integration/"],
            result["convocation"]["builder_handoff"][0]["coverage_target_path_refs"],
        )
        self.assertFalse(
            result["convocation"]["builder_handoff"][0]["raw_role_scope_payload_stored"]
        )

    def test_worker_dispatch_plan_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )

    def test_worker_dispatch_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )

    def test_workspace_guardian_preseed_gate_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_guardian_preseed_gate.schema",
            result["dispatch_receipt"]["results"][0]["guardian_preseed_gate"],
        )

    def test_dependency_materialization_manifest_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()
        manifest = result["dispatch_receipt"]["results"][0]["dependency_materialization_manifest"]

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_dependency_materialization_manifest.schema",
            manifest,
        )
        self.assertEqual("materialized-dependency-lockfile-v1", manifest["lockfile_profile"])
        self.assertEqual("attested", manifest["lockfile_status"])
        self.assertEqual(
            "materialized-dependency-wheel-attestation-v1",
            manifest["wheel_attestation_profile"],
        )
        self.assertEqual("attested", manifest["wheel_artifact_status"])
        self.assertEqual(manifest["file_count"], manifest["attested_file_count"])

    def test_worker_workspace_delta_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_workspace_delta_receipt.schema",
            result["dispatch_receipt"]["results"][0]["report"]["workspace_delta_receipt"],
        )

    def test_worker_patch_candidate_receipt_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_patch_candidate_receipt.schema",
            result["dispatch_receipt"]["results"][0]["report"]["patch_candidate_receipt"],
        )

    def test_consensus_dispatch_binding_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
            result["consensus_dispatch"],
        )

    def test_task_graph_binding_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )

    def test_build_request_binding_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo()

        self._assert_schema_valid(
            "specs/schemas/build_request.yaml",
            result["build_request_binding"]["build_request"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )

    def test_memory_edit_profile_task_graph_binding_matches_public_schema(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(proposal_profile="memory-edit-v1")

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
            result["consensus_dispatch"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )

    def test_memory_edit_optional_schema_dispatch_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(
            proposal_profile="memory-edit-v1",
            include_optional_coverage=["schema"],
        )

        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )

    def test_fork_request_profile_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(proposal_profile="fork-request-v1")

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )
        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
            result["consensus_dispatch"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )

    def test_fork_request_optional_eval_dispatch_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(
            proposal_profile="fork-request-v1",
            include_optional_coverage=["eval"],
        )

        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )

    def test_inter_mind_negotiation_profile_matches_public_schemas(self) -> None:
        result = self.runtime.run_yaoyorozu_demo(proposal_profile="inter-mind-negotiation-v1")

        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_workspace_discovery.schema",
            result["workspace_discovery"],
        )
        self._assert_schema_valid(
            "specs/schemas/council_convocation_session.schema",
            result["convocation"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_plan.schema",
            result["dispatch_plan"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
            result["dispatch_receipt"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
            result["consensus_dispatch"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_task_graph_binding.schema",
            result["task_graph_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_build_request_binding.schema",
            result["build_request_binding"],
        )
        self._assert_schema_valid(
            "specs/schemas/yaoyorozu_execution_chain_binding.schema",
            result["execution_chain"],
        )
