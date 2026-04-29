"""Repo-local Yaoyorozu registry and bounded council convocation helpers."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from ..self_construction.builders import PatchGeneratorService
from ..self_construction.design_reader import DesignReaderService
from .consensus_bus import CONSENSUS_BUS_PHASE_ORDER, CONSENSUS_BUS_TRANSPORT_PROFILE
from .local_worker_stub import (
    YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE,
    YAOYOROZU_WORKER_DELTA_SCAN_PROFILE,
    YAOYOROZU_WORKER_MODULE_NAME,
    YAOYOROZU_WORKER_MODULE_RELATIVE_PATH,
    YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE,
    YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
    YAOYOROZU_WORKER_READY_GATE_PROFILE,
    YAOYOROZU_WORKER_REPORT_KIND,
    YAOYOROZU_WORKER_REPORT_PROFILE,
    build_patch_candidate_receipt,
    build_workspace_delta_receipt,
    build_worker_report_binding_digest,
    worker_module_origin_digest_payload,
)
from .task_graph import TaskGraphService
from .trust import TrustService


YAOYOROZU_WORKER_DISPATCH_PROFILE = "repo-local-subprocess-worker-dispatch-v1"
YAOYOROZU_WORKER_EXECUTION_PROFILE = "repo-local-subprocess-worker-execution-v1"
YAOYOROZU_CONSENSUS_BINDING_PROFILE = "repo-local-yaoyorozu-consensus-bus-binding-v1"
YAOYOROZU_TASK_GRAPH_BINDING_PROFILE = "repo-local-yaoyorozu-task-graph-binding-v1"
YAOYOROZU_BUILD_REQUEST_BINDING_PROFILE = "repo-local-yaoyorozu-build-request-binding-v1"
YAOYOROZU_EXECUTION_CHAIN_BINDING_PROFILE = "repo-local-yaoyorozu-execution-chain-v1"
YAOYOROZU_WORKSPACE_DISCOVERY_PROFILE = "same-host-local-workspace-discovery-v1"
YAOYOROZU_WORKSPACE_DISCOVERY_SCOPE = "same-host-local-workspace-catalog"
YAOYOROZU_WORKSPACE_DISCOVERY_HOST_REF = "host://local-loopback"
YAOYOROZU_WORKSPACE_DISCOVERY_MAX_WORKSPACES = 3
YAOYOROZU_WORKER_DISPATCH_SCOPE = "repo-local-subprocess"
YAOYOROZU_WORKER_SANDBOX_MODE = "temp-workspace-only"
YAOYOROZU_WORKER_ENTRYPOINT_REF = "python-module://omoikane.agentic.local_worker_stub"
YAOYOROZU_WORKSPACE_SCOPE = "repo-local"
YAOYOROZU_EXTERNAL_WORKSPACE_SCOPE = "same-host-external-workspace"
YAOYOROZU_WORKSPACE_EXECUTION_POLICY_ID = "proposal-profile-aware-external-workspace-execution-v1"
YAOYOROZU_WORKSPACE_EXECUTION_TRANSPORT_PROFILE = "same-host-python-subprocess-v1"
YAOYOROZU_EXTERNAL_SANDBOX_SEED_STRATEGY = "source-target-snapshot-copy-v1"
YAOYOROZU_INLINE_SANDBOX_SEED_STRATEGY = "in-place-source-worktree-v1"
YAOYOROZU_DEPENDENCY_MATERIALIZATION_PROFILE = (
    "same-host-external-workspace-dependency-materialization-v1"
)
YAOYOROZU_EXTERNAL_DEPENDENCY_MATERIALIZATION_STRATEGY = (
    "source-runtime-dependency-snapshot-v1"
)
YAOYOROZU_INLINE_DEPENDENCY_MATERIALIZATION_STRATEGY = "in-place-source-runtime-v1"
YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT = ".yaoyorozu-dependencies"
YAOYOROZU_DEPENDENCY_LOCKFILE_PROFILE = "materialized-dependency-lockfile-v1"
YAOYOROZU_DEPENDENCY_WHEEL_ATTESTATION_PROFILE = (
    "materialized-dependency-wheel-attestation-v1"
)
YAOYOROZU_DEPENDENCY_WHEEL_ARTIFACT_NAME = (
    "omoikane_reference_runtime-0.0.0-py3-none-any.whl"
)
YAOYOROZU_DEPENDENCY_MATERIALIZATION_PATHS = [
    "pyproject.toml",
    "src/omoikane/__init__.py",
    "src/omoikane/common.py",
    "src/omoikane/agentic/__init__.py",
    "src/omoikane/agentic/local_worker_stub.py",
]
YAOYOROZU_DEPENDENCY_IMPORT_PRECEDENCE_PROFILE = (
    "materialized-dependency-sealed-import-v1"
)
YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS = "materialized-only"
YAOYOROZU_INLINE_DEPENDENCY_IMPORT_STATUS = "source-inline"
YAOYOROZU_WORKSPACE_GUARDIAN_GATE_PROFILE = (
    "same-host-external-workspace-preseed-guardian-gate-v1"
)
YAOYOROZU_WORKSPACE_GUARDIAN_OVERSIGHT_BINDING_PROFILE = (
    "human-oversight-channel-preseed-attestation-v1"
)
YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE = "registry-selection-scope-binding-v1"
YAOYOROZU_COVERAGE_SCOPE_BINDING_PROFILE = "coverage-area-target-path-binding-v1"
YAOYOROZU_AGENT_SOURCE_DIGEST_PROFILE = "repo-local-agent-source-digest-manifest-v1"
YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_BINDING_PROFILE = (
    "yaoyorozu-agent-source-manifest-continuity-ledger-binding-v1"
)
YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_CATEGORY = "yaoyorozu-agent-source-manifest"
YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_EVENT_TYPE = (
    "yaoyorozu.agent_source_manifest.bound"
)
YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_SIGNATURE_ROLES = ["self", "guardian"]
YAOYOROZU_AGENT_SOURCE_MANIFEST_PUBLIC_VERIFICATION_PROFILE = (
    "yaoyorozu-source-manifest-public-verification-bundle-v1"
)
YAOYOROZU_RESEARCH_EVIDENCE_EXCHANGE_PROFILE = (
    "repo-local-research-evidence-exchange-v1"
)
YAOYOROZU_RESEARCH_EVIDENCE_SYNTHESIS_PROFILE = (
    "repo-local-research-evidence-synthesis-v1"
)
YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_CATEGORY = "yaoyorozu-research-evidence"
YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_EVENT_TYPE = "yaoyorozu.research_evidence.bound"
YAOYOROZU_RESEARCH_EVIDENCE_SYNTHESIS_LEDGER_EVENT_TYPE = (
    "yaoyorozu.research_evidence.synthesized"
)
YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES = ["council", "guardian"]
AGENT_SOURCE_DEFINITION_SCHEMA_VERSION = "1.0.0"
AGENT_SOURCE_DEFINITION_POLICY_ID = "schema-bound-agent-source-definition-v1"
AGENT_SOURCE_ALLOWED_ROLES = {"councilor", "builder", "researcher", "guardian"}
AGENT_SOURCE_REQUIRED_STRING_FIELDS = (
    "name",
    "role",
    "version",
    "input_schema_ref",
    "output_schema_ref",
    "prompt_or_policy_ref",
    "when_to_invoke",
    "when_not_to_invoke",
)
AGENT_SOURCE_REQUIRED_LIST_FIELDS = (
    "capabilities",
    "substrate_requirements",
)
AGENT_SOURCE_COUNCILOR_REQUIRED_LIST_FIELDS = (
    "deliberation_scope_refs",
)
AGENT_SOURCE_COUNCILOR_REQUIRED_STRING_FIELDS = (
    "deliberation_policy_ref",
)
AGENT_SOURCE_COUNCILOR_SCOPE_PREFIXES = (
    "docs/",
    "specs/",
    "evals/",
    "agents/",
    "meta/",
    "src/",
    "tests/",
    "research/",
)
AGENT_SOURCE_RESEARCHER_REQUIRED_LIST_FIELDS = (
    "research_domain_refs",
)
AGENT_SOURCE_RESEARCHER_REQUIRED_STRING_FIELDS = (
    "evidence_policy_ref",
)
AGENT_SOURCE_RESEARCHER_INPUT_SCHEMA_REF = (
    "specs/schemas/research_evidence_request.schema"
)
AGENT_SOURCE_RESEARCHER_OUTPUT_SCHEMA_REF = (
    "specs/schemas/research_evidence_report.schema"
)
AGENT_SOURCE_BUILDER_REQUIRED_LIST_FIELDS = (
    "build_surface_refs",
)
AGENT_SOURCE_BUILDER_REQUIRED_STRING_FIELDS = (
    "execution_policy_ref",
)
AGENT_SOURCE_BUILDER_SURFACE_PREFIXES = (
    "src/",
    "tests/",
    "specs/",
    "evals/",
    "docs/",
    "agents/",
    "meta/",
    "research/",
)
AGENT_SOURCE_GUARDIAN_REQUIRED_LIST_FIELDS = (
    "oversight_scope_refs",
)
AGENT_SOURCE_GUARDIAN_REQUIRED_STRING_FIELDS = (
    "attestation_policy_ref",
)
AGENT_SOURCE_GUARDIAN_SCOPE_PREFIXES = (
    "docs/",
    "specs/",
    "evals/",
    "agents/",
    "meta/",
)
YAOYOROZU_WORKSPACE_GUARDIAN_ROLE = "integrity"
YAOYOROZU_WORKSPACE_GUARDIAN_CATEGORY = "attest"
YAOYOROZU_WORKSPACE_GUARDIAN_REQUIRED_BEFORE = [
    "workspace-seed",
    "execution-root-create",
    "dependency-materialization",
]
YAOYOROZU_WORKSPACE_GUARDIAN_REVIEWERS = [
    {
        "reviewer_id": "human-reviewer-yaoyorozu-integrity-001",
        "credential_id": "credential://yaoyorozu/integrity-reviewer-alpha",
        "proof_ref": "proof://yaoyorozu/preseed/integrity-reviewer-alpha/v1",
        "liability_mode": "joint",
        "legal_ack_ref": "legal://yaoyorozu/preseed/integrity-reviewer-alpha/v1",
        "verifier_ref": "verifier://guardian-oversight.jp/yaoyorozu-integrity-alpha",
        "jurisdiction": "JP-13",
        "jurisdiction_bundle_ref": "legal://jp-13/yaoyorozu-preseed/integrity-alpha/v1",
        "legal_policy_ref": "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
        "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
        "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
        "trust_root_digest": "sha256:guardian-oversight-jp-reviewer-live-pki-v1",
    },
    {
        "reviewer_id": "human-reviewer-yaoyorozu-integrity-002",
        "credential_id": "credential://yaoyorozu/integrity-reviewer-beta",
        "proof_ref": "proof://yaoyorozu/preseed/integrity-reviewer-beta/v1",
        "liability_mode": "joint",
        "legal_ack_ref": "legal://yaoyorozu/preseed/integrity-reviewer-beta/v1",
        "verifier_ref": "verifier://guardian-oversight.jp/yaoyorozu-integrity-beta",
        "jurisdiction": "JP-13",
        "jurisdiction_bundle_ref": "legal://jp-13/yaoyorozu-preseed/integrity-beta/v1",
        "legal_policy_ref": "policy://guardian-oversight/jp-13/reviewer-attestation/v1",
        "authority_chain_ref": "authority://guardian-oversight.jp/reviewer-attestation",
        "trust_root_ref": "root://guardian-oversight.jp/reviewer-live-pki",
        "trust_root_digest": "sha256:guardian-oversight-jp-reviewer-live-pki-v1",
    },
]
YAOYOROZU_PATCH_PRIORITY_TIER_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
YAOYOROZU_WORKER_TARGET_PATHS = {
    "runtime": ["src/omoikane/", "tests/unit/", "tests/integration/"],
    "schema": ["specs/interfaces/", "specs/schemas/"],
    "eval": ["evals/"],
    "docs": ["docs/", "meta/decision-log/"],
}
YAOYOROZU_BUILD_REQUEST_SCOPE_ROOTS = [
    "src/omoikane/",
    "tests/",
    "evals/",
    "docs/",
    "meta/decision-log/",
    "specs/",
]
YAOYOROZU_BUILD_REQUEST_TARGET_SUBSYSTEM = "L5.PatchGenerator"
YAOYOROZU_BUILD_REQUEST_CHANGE_CLASS = "feature-improvement"
YAOYOROZU_BUILD_REQUEST_CANDIDATE_LIMIT = 3
YAOYOROZU_BUILD_REQUEST_EVAL = "evals/agentic/yaoyorozu_build_request_binding.yaml"
YAOYOROZU_EXECUTION_CHAIN_EVAL = "evals/agentic/yaoyorozu_execution_chain_binding.yaml"
YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS = [
    "docs/02-subsystems/agentic/README.md",
    "docs/02-subsystems/agentic/yaoyorozu-roster.md",
    "docs/04-ai-governance/subagent-roster.md",
    "docs/07-reference-implementation/README.md",
]
YAOYOROZU_BUILD_REQUEST_SPEC_REFS = [
    "specs/interfaces/agentic.yaoyorozu.v0.idl",
    "specs/schemas/build_request.yaml",
    "specs/schemas/yaoyorozu_worker_dispatch_receipt.schema",
    "specs/schemas/yaoyorozu_consensus_dispatch_binding.schema",
    "specs/schemas/yaoyorozu_task_graph_binding.schema",
    "specs/schemas/yaoyorozu_build_request_binding.schema",
]
YAOYOROZU_EXECUTION_CHAIN_REQUIRED_EVALS = [
    YAOYOROZU_EXECUTION_CHAIN_EVAL,
    "evals/continuity/builder_live_enactment_execution.yaml",
    "evals/continuity/builder_staged_rollout_execution.yaml",
    "evals/continuity/builder_rollback_execution.yaml",
    "evals/continuity/builder_rollback_oversight_network.yaml",
]
YAOYOROZU_BUILD_REQUEST_STATIC_OUTPUT_PATHS = [
    "src/omoikane/self_construction/builders.py",
    "tests/unit/test_builders.py",
    "evals/continuity/council_output_build_request_pipeline.yaml",
    *YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS,
]
YAOYOROZU_PROFILE_BUILD_REQUEST_EVALS = {
    "self-modify-patch-v1": [
        "evals/agentic/yaoyorozu_local_worker_dispatch.yaml",
        "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
        "evals/agentic/yaoyorozu_consensus_dispatch.yaml",
        "evals/agentic/yaoyorozu_task_graph_binding.yaml",
    ],
    "memory-edit-v1": [
        "evals/agentic/yaoyorozu_memory_edit_profile.yaml",
        "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
        "evals/agentic/yaoyorozu_consensus_dispatch.yaml",
        "evals/agentic/yaoyorozu_task_graph_binding.yaml",
    ],
    "fork-request-v1": [
        "evals/agentic/yaoyorozu_fork_request_profile.yaml",
        "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
        "evals/agentic/yaoyorozu_consensus_dispatch.yaml",
        "evals/agentic/yaoyorozu_task_graph_binding.yaml",
    ],
    "inter-mind-negotiation-v1": [
        "evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml",
        "evals/agentic/yaoyorozu_external_workspace_execution.yaml",
        "evals/agentic/yaoyorozu_consensus_dispatch.yaml",
        "evals/agentic/yaoyorozu_task_graph_binding.yaml",
    ],
}
YAOYOROZU_WORKSPACE_COVERAGE_CAPABILITY_RULES = {
    "runtime": ("code.generate", "code.refactor", "code.test"),
    "schema": ("schema.generate", "schema.validate"),
    "eval": ("eval.generate", "eval.run"),
    "docs": ("design.delta.read", "sync.docs-to-impl", "sync.impl-to-docs"),
}
YAOYOROZU_WORKER_REPORT_FIELDS = [
    "kind",
    "report_profile",
    "agent_id",
    "role_id",
    "coverage_area",
    "dispatch_profile",
    "workspace_scope",
    "dispatch_plan_ref",
    "dispatch_unit_ref",
    "source_ref",
    "target_paths",
    "workspace_root",
    "workspace_root_digest",
    "invocation_digest",
    "target_path_observations",
    "workspace_delta_receipt",
    "patch_candidate_receipt",
    "coverage_evidence",
    "status",
]
YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES = {
    "self-modify-patch-v1": {
        "strategy_id": "self-modify-three-root-bundle-v1",
        "root_bundles": (
            {
                "bundle_role": "runtime-bundle",
                "coverage_areas": ("runtime",),
            },
            {
                "bundle_role": "schema-bundle",
                "coverage_areas": ("schema",),
            },
            {
                "bundle_role": "evidence-sync-bundle",
                "coverage_areas": ("eval", "docs"),
            },
        ),
    },
    "memory-edit-v1": {
        "strategy_id": "memory-edit-required-dispatch-three-root-v1",
        "root_bundles": (
            {
                "bundle_role": "memory-runtime-bundle",
                "coverage_areas": ("runtime",),
            },
            {
                "bundle_role": "memory-eval-bundle",
                "coverage_areas": ("eval",),
            },
            {
                "bundle_role": "memory-docs-bundle",
                "coverage_areas": ("docs",),
            },
        ),
    },
    "fork-request-v1": {
        "strategy_id": "fork-request-required-dispatch-three-root-v1",
        "root_bundles": (
            {
                "bundle_role": "identity-runtime-bundle",
                "coverage_areas": ("runtime",),
            },
            {
                "bundle_role": "fork-schema-bundle",
                "coverage_areas": ("schema",),
            },
            {
                "bundle_role": "fork-docs-bundle",
                "coverage_areas": ("docs",),
            },
        ),
    },
    "inter-mind-negotiation-v1": {
        "strategy_id": "inter-mind-negotiation-contract-sync-v1",
        "root_bundles": (
            {
                "bundle_role": "negotiation-runtime-bundle",
                "coverage_areas": ("runtime",),
            },
            {
                "bundle_role": "negotiation-contract-sync-bundle",
                "coverage_areas": ("schema", "docs"),
            },
            {
                "bundle_role": "negotiation-eval-bundle",
                "coverage_areas": ("eval",),
            },
        ),
    },
}
YAOYOROZU_OPTIONAL_DISPATCH_BUNDLE_STRATEGY_OVERRIDES = {
    "memory-edit-v1": {
        ("schema",): {
            "strategy_id": "memory-edit-optional-schema-dispatch-three-root-v1",
            "root_bundles": (
                {
                    "bundle_role": "memory-runtime-bundle",
                    "coverage_areas": ("runtime",),
                },
                {
                    "bundle_role": "memory-contract-eval-bundle",
                    "coverage_areas": ("eval", "schema"),
                },
                {
                    "bundle_role": "memory-docs-bundle",
                    "coverage_areas": ("docs",),
                },
            ),
        }
    },
    "fork-request-v1": {
        ("eval",): {
            "strategy_id": "fork-request-optional-eval-dispatch-three-root-v1",
            "root_bundles": (
                {
                    "bundle_role": "identity-runtime-bundle",
                    "coverage_areas": ("runtime",),
                },
                {
                    "bundle_role": "fork-schema-bundle",
                    "coverage_areas": ("schema",),
                },
                {
                    "bundle_role": "fork-evidence-docs-bundle",
                    "coverage_areas": ("docs", "eval"),
                },
            ),
        }
    },
}
YAOYOROZU_PROPOSAL_PROFILES = tuple(YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES)


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.replace("_", "-").split("-") if part)


def _normalize_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = ast.literal_eval(stripped)
            except (SyntaxError, ValueError):
                return [stripped.strip("'\"")]
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [stripped.strip("'\"")]
    return []


def _non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _ordered_unique(values: Sequence[str]) -> List[str]:
    ordered: List[str] = []
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_agent_definition(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if line.startswith(" "):
            index += 1
            continue
        if ":" not in line:
            index += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value in {"|", "|-", ">", ">-"}:
            index += 1
            block: List[str] = []
            while index < len(lines):
                candidate = lines[index]
                if candidate.startswith("  "):
                    block.append(candidate[2:])
                    index += 1
                    continue
                if not candidate.strip():
                    block.append("")
                    index += 1
                    continue
                break
            data[key] = "\n".join(block).rstrip()
            continue
        if not value:
            index += 1
            items: List[str] = []
            while index < len(lines):
                candidate = lines[index]
                if candidate.startswith("  - "):
                    items.append(candidate[4:].strip().strip("'\""))
                    index += 1
                    continue
                if not candidate.strip():
                    index += 1
                    continue
                break
            data[key] = items
            continue
        data[key] = value.strip().strip("'\"")
        index += 1
    return data


def _validate_agent_source_definition(
    data: Mapping[str, Any],
    path: Path,
    repo_root: Path,
) -> List[str]:
    errors: List[str] = []

    for field_name in AGENT_SOURCE_REQUIRED_STRING_FIELDS:
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field_name} must be a non-empty string")

    for field_name in AGENT_SOURCE_REQUIRED_LIST_FIELDS:
        values = _normalize_string_list(data.get(field_name, []))
        if not values:
            errors.append(f"{field_name} must contain at least one non-empty item")

    role = str(data.get("role", "")).strip()
    if role and role not in AGENT_SOURCE_ALLOWED_ROLES:
        errors.append(f"role must be one of {sorted(AGENT_SOURCE_ALLOWED_ROLES)}")

    version = str(data.get("version", "")).strip()
    version_parts = version.split(".")
    if version and (len(version_parts) != 3 or not all(part.isdigit() for part in version_parts)):
        errors.append("version must be semver-like MAJOR.MINOR.PATCH")

    try:
        trust_floor = float(data.get("trust_floor"))
    except (TypeError, ValueError):
        errors.append("trust_floor must be a number between 0 and 1")
    else:
        if not 0.0 <= trust_floor <= 1.0:
            errors.append("trust_floor must be between 0 and 1")

    for ref_field in ("input_schema_ref", "output_schema_ref", "prompt_or_policy_ref"):
        ref = str(data.get(ref_field, "")).strip()
        if ref and ref.startswith(("agents/", "specs/")) and not (repo_root / ref).is_file():
            errors.append(f"{ref_field} must reference an existing repo file: {ref}")

    if role == "councilor":
        for field_name in AGENT_SOURCE_COUNCILOR_REQUIRED_LIST_FIELDS:
            values = _normalize_string_list(data.get(field_name, []))
            if not values:
                errors.append(f"{field_name} must contain at least one non-empty item")
                continue
            for ref in values:
                if not ref.startswith(AGENT_SOURCE_COUNCILOR_SCOPE_PREFIXES):
                    errors.append(
                        f"{field_name} must reference deliberation surfaces under "
                        f"{AGENT_SOURCE_COUNCILOR_SCOPE_PREFIXES}: {ref}"
                    )
                    continue
                if not (repo_root / ref).exists():
                    errors.append(f"{field_name} must reference an existing repo path: {ref}")
        for field_name in AGENT_SOURCE_COUNCILOR_REQUIRED_STRING_FIELDS:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} must be a non-empty string")
                continue
            ref = value.strip()
            if ref.startswith(("agents/", "docs/", "specs/", "evals/", "meta/")) and not (
                repo_root / ref
            ).is_file():
                errors.append(f"{field_name} must reference an existing repo file: {ref}")

    if role == "researcher":
        for field_name in AGENT_SOURCE_RESEARCHER_REQUIRED_LIST_FIELDS:
            values = _normalize_string_list(data.get(field_name, []))
            if not values:
                errors.append(f"{field_name} must contain at least one non-empty item")
                continue
            for ref in values:
                if not ref.startswith(("docs/", "research/")):
                    errors.append(
                        f"{field_name} must reference research evidence surfaces under "
                        f"('docs/', 'research/'): {ref}"
                    )
                    continue
                if not (repo_root / ref).exists():
                    errors.append(f"{field_name} must reference an existing repo path: {ref}")
        for field_name in AGENT_SOURCE_RESEARCHER_REQUIRED_STRING_FIELDS:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} must be a non-empty string")
                continue
            ref = value.strip()
            if ref.startswith(("agents/", "docs/", "research/")) and not (repo_root / ref).is_file():
                errors.append(f"{field_name} must reference an existing repo file: {ref}")
        if str(data.get("input_schema_ref", "")).strip() != AGENT_SOURCE_RESEARCHER_INPUT_SCHEMA_REF:
            errors.append(
                "researcher input_schema_ref must equal "
                f"{AGENT_SOURCE_RESEARCHER_INPUT_SCHEMA_REF}"
            )
        if (
            str(data.get("output_schema_ref", "")).strip()
            != AGENT_SOURCE_RESEARCHER_OUTPUT_SCHEMA_REF
        ):
            errors.append(
                "researcher output_schema_ref must equal "
                f"{AGENT_SOURCE_RESEARCHER_OUTPUT_SCHEMA_REF}"
            )

    if role == "builder":
        for field_name in AGENT_SOURCE_BUILDER_REQUIRED_LIST_FIELDS:
            values = _normalize_string_list(data.get(field_name, []))
            if not values:
                errors.append(f"{field_name} must contain at least one non-empty item")
                continue
            for ref in values:
                if not ref.startswith(AGENT_SOURCE_BUILDER_SURFACE_PREFIXES):
                    errors.append(
                        f"{field_name} must reference repo build surfaces under "
                        f"{AGENT_SOURCE_BUILDER_SURFACE_PREFIXES}: {ref}"
                    )
                    continue
                if not (repo_root / ref).exists():
                    errors.append(f"{field_name} must reference an existing repo path: {ref}")
        for field_name in AGENT_SOURCE_BUILDER_REQUIRED_STRING_FIELDS:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} must be a non-empty string")
                continue
            ref = value.strip()
            if ref.startswith(("agents/", "docs/", "specs/", "evals/", "meta/")) and not (
                repo_root / ref
            ).is_file():
                errors.append(f"{field_name} must reference an existing repo file: {ref}")

    if role == "guardian":
        for field_name in AGENT_SOURCE_GUARDIAN_REQUIRED_LIST_FIELDS:
            values = _normalize_string_list(data.get(field_name, []))
            if not values:
                errors.append(f"{field_name} must contain at least one non-empty item")
                continue
            for ref in values:
                if not ref.startswith(AGENT_SOURCE_GUARDIAN_SCOPE_PREFIXES):
                    errors.append(
                        f"{field_name} must reference oversight surfaces under "
                        f"{AGENT_SOURCE_GUARDIAN_SCOPE_PREFIXES}: {ref}"
                    )
                    continue
                if not (repo_root / ref).exists():
                    errors.append(f"{field_name} must reference an existing repo path: {ref}")
        for field_name in AGENT_SOURCE_GUARDIAN_REQUIRED_STRING_FIELDS:
            value = data.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} must be a non-empty string")
                continue
            ref = value.strip()
            if ref.startswith(("agents/", "docs/", "specs/", "evals/", "meta/")) and not (
                repo_root / ref
            ).is_file():
                errors.append(f"{field_name} must reference an existing repo file: {ref}")

    source_ref = str(path.relative_to(repo_root)) if path.is_relative_to(repo_root) else str(path)
    if not source_ref.startswith("agents/"):
        errors.append("source definition must live under agents/")

    return errors


def _dispatch_unit_digest_payload(unit: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "unit_id": unit["unit_id"],
        "role_id": unit["role_id"],
        "coverage_area": unit["coverage_area"],
        "selected_agent_id": unit["selected_agent_id"],
        "source_ref": unit["source_ref"],
        "dispatch_scope": unit["dispatch_scope"],
        "sandbox_mode": unit["sandbox_mode"],
        "workspace_scope": unit["workspace_scope"],
        "entrypoint_ref": unit["entrypoint_ref"],
        "execution_workspace_ref": unit["execution_workspace_ref"],
        "execution_workspace_root": unit["execution_workspace_root"],
        "selected_workspace_root": unit["selected_workspace_root"],
        "selected_workspace_role": unit["selected_workspace_role"],
        "execution_host_ref": unit["execution_host_ref"],
        "execution_transport_profile": unit["execution_transport_profile"],
        "sandbox_seed_strategy": unit["sandbox_seed_strategy"],
        "workspace_target_digest": unit["workspace_target_digest"],
        "dependency_materialization_profile": unit["dependency_materialization_profile"],
        "dependency_materialization_strategy": unit["dependency_materialization_strategy"],
        "dependency_materialization_required": unit["dependency_materialization_required"],
        "dependency_materialization_paths": unit["dependency_materialization_paths"],
        "guardian_preseed_gate": unit["guardian_preseed_gate"],
        "command_preview": unit["command_preview"],
        "target_paths": unit["target_paths"],
    }


def _dispatch_plan_digest_payload(plan: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": plan["schema_version"],
        "dispatch_profile": plan["dispatch_profile"],
        "registry_snapshot_ref": plan["registry_snapshot_ref"],
        "convocation_session_ref": plan["convocation_session_ref"],
        "policy_id": plan["policy_id"],
        "proposal_profile": plan["proposal_profile"],
        "session_mode": plan["session_mode"],
        "target_identity_ref": plan["target_identity_ref"],
        "workspace_root": plan["workspace_root"],
        "dispatch_units": plan["dispatch_units"],
        "selection_summary": plan["selection_summary"],
        "validation": plan["validation"],
    }


def _dispatch_receipt_digest_payload(receipt: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": receipt["schema_version"],
        "dispatch_plan_ref": receipt["dispatch_plan_ref"],
        "dispatch_plan_digest": receipt["dispatch_plan_digest"],
        "dispatch_profile": receipt["dispatch_profile"],
        "execution_profile": receipt["execution_profile"],
        "workspace_root": receipt["workspace_root"],
        "results": receipt["results"],
        "execution_summary": receipt["execution_summary"],
        "validation": receipt["validation"],
    }


def _consensus_dispatch_binding_digest_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": binding["schema_version"],
        "binding_profile": binding["binding_profile"],
        "convocation_session_ref": binding["convocation_session_ref"],
        "convocation_session_digest": binding["convocation_session_digest"],
        "dispatch_plan_ref": binding["dispatch_plan_ref"],
        "dispatch_plan_digest": binding["dispatch_plan_digest"],
        "dispatch_receipt_ref": binding["dispatch_receipt_ref"],
        "dispatch_receipt_digest": binding["dispatch_receipt_digest"],
        "consensus_session_id": binding["consensus_session_id"],
        "transport_profile": binding["transport_profile"],
        "dispatch_claim_ids": binding["dispatch_claim_ids"],
        "messages": binding["messages"],
        "blocked_direct_attempt": binding["blocked_direct_attempt"],
        "audit_summary": binding["audit_summary"],
        "validation": binding["validation"],
    }


def _task_graph_digest_payload(graph: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "graph_id": graph["graph_id"],
        "intent": graph["intent"],
        "required_roles": graph["required_roles"],
        "nodes": graph["nodes"],
        "complexity_policy": graph["complexity_policy"],
        "created_at": graph["created_at"],
    }


def _task_graph_binding_digest_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": binding["schema_version"],
        "binding_profile": binding["binding_profile"],
        "proposal_profile": binding["proposal_profile"],
        "convocation_session_ref": binding["convocation_session_ref"],
        "convocation_session_digest": binding["convocation_session_digest"],
        "dispatch_plan_ref": binding["dispatch_plan_ref"],
        "dispatch_plan_digest": binding["dispatch_plan_digest"],
        "dispatch_receipt_ref": binding["dispatch_receipt_ref"],
        "dispatch_receipt_digest": binding["dispatch_receipt_digest"],
        "consensus_binding_ref": binding["consensus_binding_ref"],
        "consensus_binding_digest": binding["consensus_binding_digest"],
        "consensus_session_id": binding["consensus_session_id"],
        "bundle_strategy": binding["bundle_strategy"],
        "task_graph_ref": binding["task_graph_ref"],
        "task_graph_digest": binding["task_graph_digest"],
        "task_graph_dispatch_digest": binding["task_graph_dispatch_digest"],
        "task_graph_synthesis_digest": binding["task_graph_synthesis_digest"],
        "guardian_gate_message_digest": binding["guardian_gate_message_digest"],
        "resolve_message_digest": binding["resolve_message_digest"],
        "node_bindings": binding["node_bindings"],
        "validation": binding["validation"],
    }


def _build_request_binding_digest_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": binding["schema_version"],
        "binding_profile": binding["binding_profile"],
        "proposal_profile": binding["proposal_profile"],
        "convocation_session_ref": binding["convocation_session_ref"],
        "convocation_session_digest": binding["convocation_session_digest"],
        "dispatch_plan_ref": binding["dispatch_plan_ref"],
        "dispatch_plan_digest": binding["dispatch_plan_digest"],
        "dispatch_receipt_ref": binding["dispatch_receipt_ref"],
        "dispatch_receipt_digest": binding["dispatch_receipt_digest"],
        "consensus_binding_ref": binding["consensus_binding_ref"],
        "consensus_binding_digest": binding["consensus_binding_digest"],
        "task_graph_binding_ref": binding["task_graph_binding_ref"],
        "task_graph_binding_digest": binding["task_graph_binding_digest"],
        "council_action": binding["council_action"],
        "handoff_summary": binding["handoff_summary"],
        "selected_patch_candidates": binding["selected_patch_candidates"],
        "build_request_ref": binding["build_request_ref"],
        "build_request_digest": binding["build_request_digest"],
        "scope_validation": binding["scope_validation"],
        "validation": binding["validation"],
    }


def _execution_chain_binding_digest_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": binding["schema_version"],
        "binding_profile": binding["binding_profile"],
        "proposal_profile": binding["proposal_profile"],
        "build_request_binding_ref": binding["build_request_binding_ref"],
        "build_request_binding_digest": binding["build_request_binding_digest"],
        "build_artifact_ref": binding["build_artifact_ref"],
        "build_artifact_digest": binding["build_artifact_digest"],
        "sandbox_apply_receipt_ref": binding["sandbox_apply_receipt_ref"],
        "sandbox_apply_receipt_digest": binding["sandbox_apply_receipt_digest"],
        "live_enactment_session_ref": binding["live_enactment_session_ref"],
        "live_enactment_session_digest": binding["live_enactment_session_digest"],
        "rollout_session_ref": binding["rollout_session_ref"],
        "rollout_session_digest": binding["rollout_session_digest"],
        "rollback_session_ref": binding["rollback_session_ref"],
        "rollback_session_digest": binding["rollback_session_digest"],
        "digest_family": binding["digest_family"],
        "execution_summary": binding["execution_summary"],
        "validation": binding["validation"],
    }


def _artifact_ref(artifact_payload: Mapping[str, Any], artifact_kind: str) -> str:
    for artifact in artifact_payload.get("artifacts", []):
        if isinstance(artifact, Mapping) and artifact.get("artifact_kind") == artifact_kind:
            return str(artifact.get("ref", ""))
    return ""


def _workspace_ref_from_root(workspace_root: Path) -> str:
    normalized_name = "".join(
        character.lower() if character.isalnum() else "-"
        for character in workspace_root.name.strip()
    ).strip("-")
    while "--" in normalized_name:
        normalized_name = normalized_name.replace("--", "-")
    if not normalized_name:
        normalized_name = "workspace"
    suffix = sha256_text(str(workspace_root.resolve()))[:8]
    return f"workspace://{normalized_name}-{suffix}"


def _workspace_summary_digest_payload(summary: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "workspace_ref": summary["workspace_ref"],
        "workspace_name": summary["workspace_name"],
        "workspace_root": summary["workspace_root"],
        "registry_source_root": summary["registry_source_root"],
        "workspace_order": summary["workspace_order"],
        "workspace_role": summary["workspace_role"],
        "source_kind": summary["source_kind"],
        "agent_count": summary["agent_count"],
        "builder_agent_ids": summary["builder_agent_ids"],
        "role_index": summary["role_index"],
        "capability_index": summary["capability_index"],
        "supported_coverage_areas": summary["supported_coverage_areas"],
        "missing_coverage_areas": summary["missing_coverage_areas"],
        "proposal_profiles": summary["proposal_profiles"],
        "validation": summary["validation"],
    }


def _source_manifest_continuity_payload(binding: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "event_ref": binding["continuity_event_ref"],
        "category": binding["continuity_ledger_category"],
        "event_type": binding["continuity_ledger_event_type"],
        "binding_profile": binding["binding_profile"],
        "binding_id": binding["binding_id"],
        "registry_snapshot_ref": binding["registry_snapshot_ref"],
        "registry_digest": binding["registry_digest"],
        "policy_id": binding["policy_id"],
        "source_root": binding["source_root"],
        "source_digest_profile": binding["source_digest_profile"],
        "source_definition_count": binding["source_definition_count"],
        "source_definition_digests": binding["source_definition_digests"],
        "source_manifest_digest": binding["source_manifest_digest"],
        "raw_source_payload_stored": binding["raw_source_payload_stored"],
        "raw_registry_payload_stored": binding["raw_registry_payload_stored"],
        "raw_continuity_event_payload_stored": binding[
            "raw_continuity_event_payload_stored"
        ],
    }


def _source_manifest_public_verification_bundle_core(
    *,
    binding: Mapping[str, Any],
    ledger_entry: Any,
    source_definition_digest_set_digest: str,
    signature_digests: Mapping[str, str],
    verifier_key_refs: Mapping[str, str],
    public_verification_ready: bool,
) -> Dict[str, Any]:
    bundle_seed = {
        "binding_id": binding["binding_id"],
        "continuity_ledger_entry_hash": getattr(ledger_entry, "entry_hash", ""),
        "source_manifest_digest": binding["source_manifest_digest"],
    }
    bundle_id = (
        "yaoyorozu-source-manifest-public-verification-"
        f"{sha256_text(canonical_json(bundle_seed))[:12]}"
    )
    return {
        "kind": "yaoyorozu_source_manifest_public_verification_bundle",
        "schema_version": "1.0.0",
        "profile_id": YAOYOROZU_AGENT_SOURCE_MANIFEST_PUBLIC_VERIFICATION_PROFILE,
        "bundle_id": bundle_id,
        "bundle_ref": f"verification://yaoyorozu/source-manifest/{bundle_id}",
        "binding_id": binding["binding_id"],
        "binding_profile": binding["binding_profile"],
        "registry_snapshot_ref": binding["registry_snapshot_ref"],
        "registry_digest": binding["registry_digest"],
        "policy_id": binding["policy_id"],
        "source_root": binding["source_root"],
        "source_digest_profile": binding["source_digest_profile"],
        "source_definition_count": binding["source_definition_count"],
        "source_definition_digests": list(binding["source_definition_digests"]),
        "source_definition_digest_set_digest": source_definition_digest_set_digest,
        "source_manifest_digest": binding["source_manifest_digest"],
        "continuity_event_ref": binding["continuity_event_ref"],
        "continuity_event_digest": binding["continuity_event_digest"],
        "continuity_ledger_category": binding["continuity_ledger_category"],
        "continuity_ledger_event_type": binding["continuity_ledger_event_type"],
        "continuity_ledger_entry_ref": binding["continuity_ledger_entry_ref"],
        "continuity_ledger_entry_hash": binding["continuity_ledger_entry_hash"],
        "continuity_ledger_payload_ref": binding["continuity_ledger_payload_ref"],
        "continuity_ledger_signature_roles": list(
            binding["continuity_ledger_signature_roles"]
        ),
        "signature_digests": dict(signature_digests),
        "verifier_key_refs": dict(verifier_key_refs),
        "public_verification_ready": public_verification_ready,
        "raw_source_payload_exposed": False,
        "raw_registry_payload_exposed": False,
        "raw_continuity_event_payload_exposed": False,
        "raw_signature_payload_exposed": False,
    }


def _research_evidence_request_digest_payload(request: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": request["kind"],
        "schema_version": request["schema_version"],
        "request_id": request["request_id"],
        "requested_by_ref": request["requested_by_ref"],
        "research_domain_refs": request["research_domain_refs"],
        "evidence_policy_ref": request["evidence_policy_ref"],
        "question": request["question"],
        "seed_evidence_refs": request.get("seed_evidence_refs", []),
        "requested_output_sections": request["requested_output_sections"],
        "constraints": request["constraints"],
    }


def _research_evidence_report_digest_payload(report: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": report["kind"],
        "schema_version": report["schema_version"],
        "report_id": report["report_id"],
        "request_ref": report["request_ref"],
        "researcher_agent_id": report["researcher_agent_id"],
        "research_domain_refs": report["research_domain_refs"],
        "evidence_policy_ref": report["evidence_policy_ref"],
        "evidence_items": report["evidence_items"],
        "claim_ceiling": report["claim_ceiling"],
        "uncertainty_notes": report.get("uncertainty_notes", []),
        "advisory_design_implications": report["advisory_design_implications"],
        "raw_research_payload_stored": report["raw_research_payload_stored"],
        "decision_authority_claimed": report["decision_authority_claimed"],
    }


def _research_evidence_exchange_digest_payload(exchange: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": exchange["kind"],
        "schema_version": exchange["schema_version"],
        "exchange_id": exchange["exchange_id"],
        "exchange_ref": exchange["exchange_ref"],
        "recorded_at": exchange["recorded_at"],
        "profile_id": exchange["profile_id"],
        "registry_snapshot_ref": exchange["registry_snapshot_ref"],
        "registry_digest": exchange["registry_digest"],
        "source_manifest_digest": exchange["source_manifest_digest"],
        "researcher_agent_id": exchange["researcher_agent_id"],
        "researcher_source_ref": exchange["researcher_source_ref"],
        "researcher_source_digest": exchange["researcher_source_digest"],
        "research_domain_refs": exchange["research_domain_refs"],
        "evidence_policy_ref": exchange["evidence_policy_ref"],
        "input_schema_ref": exchange["input_schema_ref"],
        "output_schema_ref": exchange["output_schema_ref"],
        "requested_by_ref": exchange["requested_by_ref"],
        "request_ref": exchange["request_ref"],
        "request_digest": exchange["request_digest"],
        "report_ref": exchange["report_ref"],
        "report_digest": exchange["report_digest"],
        "evidence_refs": exchange["evidence_refs"],
        "evidence_ref_count": exchange["evidence_ref_count"],
        "claim_ceiling": exchange["claim_ceiling"],
        "advisory_only": exchange["advisory_only"],
        "raw_research_payload_stored": exchange["raw_research_payload_stored"],
        "decision_authority_claimed": exchange["decision_authority_claimed"],
        "request": exchange["request"],
        "report": exchange["report"],
        "continuity_event_ref": exchange["continuity_event_ref"],
        "continuity_event_digest": exchange["continuity_event_digest"],
        "continuity_ledger_category": exchange["continuity_ledger_category"],
        "continuity_ledger_event_type": exchange["continuity_ledger_event_type"],
        "continuity_ledger_signature_roles": exchange["continuity_ledger_signature_roles"],
        "continuity_ledger_appended": exchange["continuity_ledger_appended"],
        "continuity_ledger_entry_ref": exchange["continuity_ledger_entry_ref"],
        "continuity_ledger_entry_hash": exchange["continuity_ledger_entry_hash"],
        "continuity_ledger_payload_ref": exchange["continuity_ledger_payload_ref"],
    }


def _research_evidence_exchange_continuity_payload(
    exchange: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "event_ref": exchange["continuity_event_ref"],
        "category": exchange["continuity_ledger_category"],
        "event_type": exchange["continuity_ledger_event_type"],
        "profile_id": exchange["profile_id"],
        "exchange_id": exchange["exchange_id"],
        "exchange_ref": exchange["exchange_ref"],
        "registry_snapshot_ref": exchange["registry_snapshot_ref"],
        "registry_digest": exchange["registry_digest"],
        "source_manifest_digest": exchange["source_manifest_digest"],
        "researcher_agent_id": exchange["researcher_agent_id"],
        "researcher_source_ref": exchange["researcher_source_ref"],
        "researcher_source_digest": exchange["researcher_source_digest"],
        "request_ref": exchange["request_ref"],
        "request_digest": exchange["request_digest"],
        "report_ref": exchange["report_ref"],
        "report_digest": exchange["report_digest"],
        "evidence_refs": exchange["evidence_refs"],
        "evidence_ref_count": exchange["evidence_ref_count"],
        "claim_ceiling": exchange["claim_ceiling"],
        "advisory_only": exchange["advisory_only"],
        "raw_research_payload_stored": exchange["raw_research_payload_stored"],
        "decision_authority_claimed": exchange["decision_authority_claimed"],
    }


def _research_evidence_synthesis_digest_payload(
    synthesis: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": synthesis["kind"],
        "schema_version": synthesis["schema_version"],
        "synthesis_id": synthesis["synthesis_id"],
        "synthesis_ref": synthesis["synthesis_ref"],
        "recorded_at": synthesis["recorded_at"],
        "profile_id": synthesis["profile_id"],
        "registry_snapshot_ref": synthesis["registry_snapshot_ref"],
        "registry_digest": synthesis["registry_digest"],
        "source_manifest_digest": synthesis["source_manifest_digest"],
        "council_session_ref": synthesis["council_session_ref"],
        "exchange_refs": synthesis["exchange_refs"],
        "exchange_digests": synthesis["exchange_digests"],
        "exchange_count": synthesis["exchange_count"],
        "researcher_agent_ids": synthesis["researcher_agent_ids"],
        "research_domain_refs": synthesis["research_domain_refs"],
        "evidence_refs": synthesis["evidence_refs"],
        "evidence_digest_set": synthesis["evidence_digest_set"],
        "claim_ceiling": synthesis["claim_ceiling"],
        "synthesis_summary": synthesis["synthesis_summary"],
        "advisory_design_implications": synthesis["advisory_design_implications"],
        "raw_exchange_payload_stored": synthesis["raw_exchange_payload_stored"],
        "raw_research_payload_stored": synthesis["raw_research_payload_stored"],
        "decision_authority_claimed": synthesis["decision_authority_claimed"],
        "continuity_event_ref": synthesis["continuity_event_ref"],
        "continuity_event_digest": synthesis["continuity_event_digest"],
        "continuity_ledger_category": synthesis["continuity_ledger_category"],
        "continuity_ledger_event_type": synthesis["continuity_ledger_event_type"],
        "continuity_ledger_signature_roles": synthesis[
            "continuity_ledger_signature_roles"
        ],
        "continuity_ledger_appended": synthesis["continuity_ledger_appended"],
        "continuity_ledger_entry_ref": synthesis["continuity_ledger_entry_ref"],
        "continuity_ledger_entry_hash": synthesis["continuity_ledger_entry_hash"],
        "continuity_ledger_payload_ref": synthesis["continuity_ledger_payload_ref"],
    }


def _research_evidence_synthesis_continuity_payload(
    synthesis: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "event_ref": synthesis["continuity_event_ref"],
        "category": synthesis["continuity_ledger_category"],
        "event_type": synthesis["continuity_ledger_event_type"],
        "profile_id": synthesis["profile_id"],
        "synthesis_id": synthesis["synthesis_id"],
        "synthesis_ref": synthesis["synthesis_ref"],
        "registry_snapshot_ref": synthesis["registry_snapshot_ref"],
        "registry_digest": synthesis["registry_digest"],
        "source_manifest_digest": synthesis["source_manifest_digest"],
        "council_session_ref": synthesis["council_session_ref"],
        "exchange_refs": synthesis["exchange_refs"],
        "exchange_digests": synthesis["exchange_digests"],
        "exchange_count": synthesis["exchange_count"],
        "researcher_agent_ids": synthesis["researcher_agent_ids"],
        "research_domain_refs": synthesis["research_domain_refs"],
        "evidence_refs": synthesis["evidence_refs"],
        "evidence_digest_set": synthesis["evidence_digest_set"],
        "claim_ceiling": synthesis["claim_ceiling"],
        "raw_exchange_payload_stored": synthesis["raw_exchange_payload_stored"],
        "raw_research_payload_stored": synthesis["raw_research_payload_stored"],
        "decision_authority_claimed": synthesis["decision_authority_claimed"],
    }


def _workspace_discovery_digest_payload(discovery: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": discovery["schema_version"],
        "discovery_profile": discovery["discovery_profile"],
        "discovery_scope": discovery["discovery_scope"],
        "proposal_profile": discovery["proposal_profile"],
        "profile_policy": discovery["profile_policy"],
        "source_workspace_ref": discovery["source_workspace_ref"],
        "host_ref": discovery["host_ref"],
        "review_budget": discovery["review_budget"],
        "workspace_roots": discovery["workspace_roots"],
        "accepted_workspace_refs": discovery["accepted_workspace_refs"],
        "coverage_summary": discovery["coverage_summary"],
        "workspaces": discovery["workspaces"],
        "validation": discovery["validation"],
    }


def _workspace_execution_target_digest_payload(target: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "coverage_area": target["coverage_area"],
        "workspace_ref": target["workspace_ref"],
        "workspace_root": target["workspace_root"],
        "workspace_role": target["workspace_role"],
        "source_kind": target["source_kind"],
        "workspace_scope": target["workspace_scope"],
        "execution_transport_profile": target["execution_transport_profile"],
        "sandbox_seed_strategy": target["sandbox_seed_strategy"],
        "dependency_materialization_profile": target["dependency_materialization_profile"],
        "dependency_materialization_strategy": target["dependency_materialization_strategy"],
        "dependency_materialization_required": target["dependency_materialization_required"],
        "dependency_materialization_paths": target["dependency_materialization_paths"],
        "guardian_preseed_gate_required": target["guardian_preseed_gate_required"],
    }


def _guardian_preseed_gate_digest_payload(gate: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": gate["kind"],
        "schema_version": gate["schema_version"],
        "gate_id": gate["gate_id"],
        "gate_ref": gate["gate_ref"],
        "gate_profile": gate["gate_profile"],
        "dispatch_plan_ref": gate["dispatch_plan_ref"],
        "dispatch_unit_ref": gate["dispatch_unit_ref"],
        "proposal_profile": gate["proposal_profile"],
        "coverage_area": gate["coverage_area"],
        "workspace_ref": gate["workspace_ref"],
        "selected_workspace_root": gate["selected_workspace_root"],
        "execution_workspace_root": gate["execution_workspace_root"],
        "execution_host_ref": gate["execution_host_ref"],
        "workspace_scope": gate["workspace_scope"],
        "sandbox_seed_strategy": gate["sandbox_seed_strategy"],
        "target_digest": gate["target_digest"],
        "guardian_agent_id": gate["guardian_agent_id"],
        "guardian_role": gate["guardian_role"],
        "oversight_category": gate["oversight_category"],
        "oversight_binding_profile": gate["oversight_binding_profile"],
        "guardian_oversight_event_ref": gate["guardian_oversight_event_ref"],
        "guardian_oversight_event_digest": gate["guardian_oversight_event_digest"],
        "guardian_oversight_event_status": gate["guardian_oversight_event_status"],
        "reviewer_network_attested": gate["reviewer_network_attested"],
        "reviewer_quorum_required": gate["reviewer_quorum_required"],
        "reviewer_quorum_received": gate["reviewer_quorum_received"],
        "required_before": gate["required_before"],
        "gate_required": gate["gate_required"],
        "gate_status": gate["gate_status"],
        "decision_reason": gate["decision_reason"],
    }


def _dependency_materialization_manifest_digest_payload(
    manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": manifest["kind"],
        "schema_version": manifest["schema_version"],
        "manifest_id": manifest["manifest_id"],
        "manifest_ref": manifest["manifest_ref"],
        "profile": manifest["profile"],
        "strategy": manifest["strategy"],
        "dispatch_plan_ref": manifest["dispatch_plan_ref"],
        "dispatch_unit_ref": manifest["dispatch_unit_ref"],
        "coverage_area": manifest["coverage_area"],
        "workspace_root": manifest["workspace_root"],
        "dependency_root": manifest["dependency_root"],
        "manifest_path": manifest["manifest_path"],
        "required": manifest["required"],
        "status": manifest["status"],
        "file_count": manifest["file_count"],
        "files": manifest["files"],
        "lockfile_profile": manifest["lockfile_profile"],
        "lockfile_path": manifest["lockfile_path"],
        "lockfile_digest": manifest["lockfile_digest"],
        "lockfile_byte_count": manifest["lockfile_byte_count"],
        "lockfile_status": manifest["lockfile_status"],
        "wheel_artifact_ref": manifest["wheel_artifact_ref"],
        "wheel_artifact_path": manifest["wheel_artifact_path"],
        "wheel_artifact_digest": manifest["wheel_artifact_digest"],
        "wheel_artifact_byte_count": manifest["wheel_artifact_byte_count"],
        "wheel_artifact_status": manifest["wheel_artifact_status"],
        "wheel_attestation_profile": manifest["wheel_attestation_profile"],
        "wheel_attestation_digest": manifest["wheel_attestation_digest"],
        "attested_file_count": manifest["attested_file_count"],
    }


def _dependency_wheel_attestation_digest_payload(
    manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "profile": manifest["wheel_attestation_profile"],
        "dispatch_plan_ref": manifest["dispatch_plan_ref"],
        "dispatch_unit_ref": manifest["dispatch_unit_ref"],
        "coverage_area": manifest["coverage_area"],
        "manifest_ref": manifest["manifest_ref"],
        "lockfile_profile": manifest["lockfile_profile"],
        "lockfile_digest": manifest["lockfile_digest"],
        "wheel_artifact_ref": manifest["wheel_artifact_ref"],
        "wheel_artifact_digest": manifest["wheel_artifact_digest"],
        "attested_file_count": manifest["attested_file_count"],
        "file_entry_digests": [
            str(file_entry.get("entry_digest", ""))
            for file_entry in manifest["files"]
            if isinstance(file_entry, Mapping)
        ],
    }


def _build_preseed_oversight_event(
    *,
    gate_ref: str,
    dispatch_plan_ref: str,
    dispatch_unit_ref: str,
    proposal_profile: str,
    coverage_area: str,
    workspace_ref: str,
    target_digest: str,
) -> Dict[str, Any]:
    recorded_at = utc_now_iso()
    reviewer_bindings: List[Dict[str, Any]] = []
    for reviewer in YAOYOROZU_WORKSPACE_GUARDIAN_REVIEWERS:
        reviewer_id = str(reviewer["reviewer_id"])
        challenge_payload = {
            "gate_ref": gate_ref,
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_unit_ref": dispatch_unit_ref,
            "proposal_profile": proposal_profile,
            "coverage_area": coverage_area,
            "workspace_ref": workspace_ref,
            "target_digest": target_digest,
            "reviewer_id": reviewer_id,
        }
        challenge_digest = sha256_text(canonical_json(challenge_payload))
        jurisdiction_bundle_digest = sha256_text(
            canonical_json(
                {
                    "jurisdiction_bundle_ref": reviewer["jurisdiction_bundle_ref"],
                    "gate_ref": gate_ref,
                    "target_digest": target_digest,
                }
            )
        )
        legal_execution_digest = sha256_text(
            canonical_json(
                {
                    "legal_policy_ref": reviewer["legal_policy_ref"],
                    "jurisdiction_bundle_digest": jurisdiction_bundle_digest,
                    "reviewer_id": reviewer_id,
                    "coverage_area": coverage_area,
                }
            )
        )
        transport_exchange_digest = sha256_text(
            canonical_json(
                {
                    "verifier_ref": reviewer["verifier_ref"],
                    "challenge_digest": challenge_digest,
                    "payload_ref": gate_ref,
                }
            )
        )
        reviewer_bindings.append(
            {
                "reviewer_id": reviewer_id,
                "credential_id": reviewer["credential_id"],
                "proof_ref": reviewer["proof_ref"],
                "liability_mode": reviewer["liability_mode"],
                "legal_ack_ref": reviewer["legal_ack_ref"],
                "verification_id": new_id("reviewer-verification"),
                "verifier_ref": reviewer["verifier_ref"],
                "challenge_digest": challenge_digest,
                "transport_profile": "reviewer-live-proof-bridge-v1",
                "jurisdiction": reviewer["jurisdiction"],
                "jurisdiction_bundle_ref": reviewer["jurisdiction_bundle_ref"],
                "jurisdiction_bundle_digest": jurisdiction_bundle_digest,
                "legal_execution_id": new_id("legal-execution"),
                "legal_execution_digest": legal_execution_digest,
                "legal_policy_ref": reviewer["legal_policy_ref"],
                "network_receipt_id": new_id("verifier-network-receipt"),
                "transport_exchange_id": new_id("verifier-transport-exchange"),
                "transport_exchange_digest": transport_exchange_digest,
                "authority_chain_ref": reviewer["authority_chain_ref"],
                "trust_root_ref": reviewer["trust_root_ref"],
                "trust_root_digest": reviewer["trust_root_digest"],
                "guardian_role": YAOYOROZU_WORKSPACE_GUARDIAN_ROLE,
                "category": YAOYOROZU_WORKSPACE_GUARDIAN_CATEGORY,
                "attested_at": recorded_at,
            }
        )

    return {
        "kind": "guardian_oversight_event",
        "schema_version": "1.0.0",
        "event_id": new_id("oversight-event"),
        "recorded_at": recorded_at,
        "guardian_role": YAOYOROZU_WORKSPACE_GUARDIAN_ROLE,
        "category": YAOYOROZU_WORKSPACE_GUARDIAN_CATEGORY,
        "payload_ref": gate_ref,
        "human_attestation": {
            "required_quorum": 2,
            "received_quorum": len(reviewer_bindings),
            "reviewers": [binding["reviewer_id"] for binding in reviewer_bindings],
            "status": "satisfied",
            "escalation_window_seconds": 604800,
        },
        "reviewer_bindings": reviewer_bindings,
        "escalation_path": [
            "yaoyorozu-integrity-reviewer-pool",
            "external-workspace-execution-halt",
        ],
        "pin_breach_propagated": False,
    }


@dataclass(frozen=True)
class YaoyorozuRegistryEntry:
    """One repo-local agent definition with trust-bound runtime metadata."""

    agent_id: str
    display_name: str
    role: str
    source_ref: str
    capabilities: List[str] = field(default_factory=list)
    trust_floor: float = 0.3
    substrate_requirements: List[str] = field(default_factory=list)
    input_schema_ref: str = ""
    output_schema_ref: str = ""
    ethics_constraints: List[str] = field(default_factory=list)
    prompt_or_policy_ref: str = ""
    deliberation_scope_refs: List[str] = field(default_factory=list)
    deliberation_policy_ref: str = ""
    research_domain_refs: List[str] = field(default_factory=list)
    evidence_policy_ref: str = ""
    build_surface_refs: List[str] = field(default_factory=list)
    execution_policy_ref: str = ""
    oversight_scope_refs: List[str] = field(default_factory=list)
    attestation_policy_ref: str = ""

    def to_dict(self, trust_snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        entry = {
            "kind": "agent_registry_entry",
            "schema_version": "1.0.0",
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "role": self.role,
            "source_ref": self.source_ref,
            "capabilities": list(self.capabilities),
            "trust_floor": round(self.trust_floor, 3),
            "substrate_requirements": list(self.substrate_requirements),
            "input_schema_ref": self.input_schema_ref,
            "output_schema_ref": self.output_schema_ref,
            "ethics_constraints": list(self.ethics_constraints),
            "prompt_or_policy_ref": self.prompt_or_policy_ref,
            "trust_snapshot": dict(trust_snapshot),
        }
        if self.role == "councilor":
            entry["deliberation_scope_refs"] = list(self.deliberation_scope_refs)
            entry["deliberation_policy_ref"] = self.deliberation_policy_ref
        if self.role == "researcher":
            entry["research_domain_refs"] = list(self.research_domain_refs)
            entry["evidence_policy_ref"] = self.evidence_policy_ref
        if self.role == "builder":
            entry["build_surface_refs"] = list(self.build_surface_refs)
            entry["execution_policy_ref"] = self.execution_policy_ref
        if self.role == "guardian":
            entry["oversight_scope_refs"] = list(self.oversight_scope_refs)
            entry["attestation_policy_ref"] = self.attestation_policy_ref
        return entry


@dataclass(frozen=True)
class YaoyorozuRegistryPolicy:
    """Fixed reference policy for repo-local agent sync and convocation."""

    policy_id: str = "repo-local-yaoyorozu-registry-v1"
    cold_start_score: float = 0.3
    council_invite_floor: float = 0.5
    weighted_vote_floor: float = 0.6
    apply_floor: float = 0.8
    default_convocation_profile: str = "self-modify-patch-v1"
    worker_dispatch_profile: str = YAOYOROZU_WORKER_DISPATCH_PROFILE
    worker_execution_profile: str = YAOYOROZU_WORKER_EXECUTION_PROFILE
    worker_dispatch_scope: str = YAOYOROZU_WORKER_DISPATCH_SCOPE
    worker_sandbox_mode: str = YAOYOROZU_WORKER_SANDBOX_MODE
    worker_entrypoint_ref: str = YAOYOROZU_WORKER_ENTRYPOINT_REF
    worker_workspace_scope: str = YAOYOROZU_WORKSPACE_SCOPE
    external_workspace_scope: str = YAOYOROZU_EXTERNAL_WORKSPACE_SCOPE
    workspace_execution_policy_id: str = YAOYOROZU_WORKSPACE_EXECUTION_POLICY_ID
    workspace_execution_transport_profile: str = YAOYOROZU_WORKSPACE_EXECUTION_TRANSPORT_PROFILE
    inline_workspace_seed_strategy: str = YAOYOROZU_INLINE_SANDBOX_SEED_STRATEGY
    external_workspace_seed_strategy: str = YAOYOROZU_EXTERNAL_SANDBOX_SEED_STRATEGY
    dependency_materialization_profile: str = YAOYOROZU_DEPENDENCY_MATERIALIZATION_PROFILE
    dependency_lockfile_profile: str = YAOYOROZU_DEPENDENCY_LOCKFILE_PROFILE
    dependency_wheel_attestation_profile: str = YAOYOROZU_DEPENDENCY_WHEEL_ATTESTATION_PROFILE
    external_dependency_materialization_strategy: str = (
        YAOYOROZU_EXTERNAL_DEPENDENCY_MATERIALIZATION_STRATEGY
    )
    inline_dependency_materialization_strategy: str = (
        YAOYOROZU_INLINE_DEPENDENCY_MATERIALIZATION_STRATEGY
    )
    dependency_materialization_paths: List[str] = field(
        default_factory=lambda: list(YAOYOROZU_DEPENDENCY_MATERIALIZATION_PATHS)
    )
    dependency_import_precedence_profile: str = YAOYOROZU_DEPENDENCY_IMPORT_PRECEDENCE_PROFILE
    dependency_module_origin_profile: str = YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE
    workspace_guardian_gate_profile: str = YAOYOROZU_WORKSPACE_GUARDIAN_GATE_PROFILE
    workspace_guardian_role: str = YAOYOROZU_WORKSPACE_GUARDIAN_ROLE
    workspace_guardian_category: str = YAOYOROZU_WORKSPACE_GUARDIAN_CATEGORY
    workspace_guardian_required_before: List[str] = field(
        default_factory=lambda: list(YAOYOROZU_WORKSPACE_GUARDIAN_REQUIRED_BEFORE)
    )
    workspace_discovery_profile: str = YAOYOROZU_WORKSPACE_DISCOVERY_PROFILE
    workspace_discovery_scope: str = YAOYOROZU_WORKSPACE_DISCOVERY_SCOPE
    workspace_discovery_host_ref: str = YAOYOROZU_WORKSPACE_DISCOVERY_HOST_REF
    workspace_review_budget: int = YAOYOROZU_WORKSPACE_DISCOVERY_MAX_WORKSPACES
    task_graph_binding_profile: str = YAOYOROZU_TASK_GRAPH_BINDING_PROFILE
    build_request_binding_profile: str = YAOYOROZU_BUILD_REQUEST_BINDING_PROFILE
    execution_chain_binding_profile: str = YAOYOROZU_EXECUTION_CHAIN_BINDING_PROFILE
    build_request_target_subsystem: str = YAOYOROZU_BUILD_REQUEST_TARGET_SUBSYSTEM
    build_request_candidate_limit: int = YAOYOROZU_BUILD_REQUEST_CANDIDATE_LIMIT
    top_k_per_role: int = 1
    worker_target_paths: Dict[str, List[str]] = field(
        default_factory=lambda: {
            coverage_area: list(paths)
            for coverage_area, paths in YAOYOROZU_WORKER_TARGET_PATHS.items()
        }
    )
    workspace_coverage_capability_rules: Dict[str, List[str]] = field(
        default_factory=lambda: {
            coverage_area: [str(capability) for capability in capabilities]
            for coverage_area, capabilities in YAOYOROZU_WORKSPACE_COVERAGE_CAPABILITY_RULES.items()
        }
    )
    task_graph_bundle_strategies: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            proposal_profile: {
                "strategy_id": str(strategy["strategy_id"]),
                "root_bundles": [
                    {
                        "bundle_role": str(bundle["bundle_role"]),
                        "coverage_areas": [str(area) for area in bundle["coverage_areas"]],
                    }
                    for bundle in strategy["root_bundles"]
                ],
            }
            for proposal_profile, strategy in YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES.items()
        }
    )
    standing_roles: Dict[str, str] = field(
        default_factory=lambda: {
            "speaker": "design-architect",
            "recorder": "memory-archivist",
            "guardian_liaison": "integrity-guardian",
        }
    )
    council_profiles: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "self-modify-patch-v1": {
                "summary": "Prepare a bounded Council review and builder handoff for one self-modify patch.",
                "workspace_review_policy_id": "self-modify-cross-workspace-review-v1",
                "workspace_review_budget": 3,
                "required_workspace_coverage_areas": ["runtime", "schema", "eval", "docs"],
                "optional_workspace_coverage_areas": [],
                "council_roles": [
                    {
                        "role_id": "design-auditor",
                        "role_label": "DesignAuditor",
                        "candidate_agents": ["design-architect"],
                    },
                    {
                        "role_id": "change-advocate",
                        "role_label": "ChangeAdvocate",
                        "candidate_agents": ["change-advocate"],
                    },
                    {
                        "role_id": "conservatism-advocate",
                        "role_label": "ConservatismAdvocate",
                        "candidate_agents": ["conservatism-advocate"],
                    },
                    {
                        "role_id": "ethics-committee",
                        "role_label": "EthicsCommittee",
                        "candidate_agents": ["ethics-committee"],
                    },
                ],
                "builder_handoff": [
                    {
                        "coverage_area": "runtime",
                        "candidate_agents": ["codex-builder"],
                    },
                    {
                        "coverage_area": "schema",
                        "candidate_agents": ["schema-builder"],
                    },
                    {
                        "coverage_area": "eval",
                        "candidate_agents": ["eval-builder"],
                    },
                    {
                        "coverage_area": "docs",
                        "candidate_agents": ["doc-sync-builder"],
                    },
                ],
                "task_graph_bundle_strategy_id": YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES[
                    "self-modify-patch-v1"
                ]["strategy_id"],
            },
            "memory-edit-v1": {
                "summary": "Prepare a bounded Council review and reversible memory-edit handoff for one recall-affect-buffer session.",
                "workspace_review_policy_id": "memory-edit-cross-workspace-review-v1",
                "workspace_review_budget": 2,
                "required_workspace_coverage_areas": ["runtime", "eval", "docs"],
                "optional_workspace_coverage_areas": ["schema"],
                "council_roles": [
                    {
                        "role_id": "memory-archivist",
                        "role_label": "MemoryArchivist",
                        "candidate_agents": ["memory-archivist"],
                    },
                    {
                        "role_id": "design-auditor",
                        "role_label": "DesignAuditor",
                        "candidate_agents": ["design-architect"],
                    },
                    {
                        "role_id": "conservatism-advocate",
                        "role_label": "ConservatismAdvocate",
                        "candidate_agents": ["conservatism-advocate"],
                    },
                    {
                        "role_id": "ethics-committee",
                        "role_label": "EthicsCommittee",
                        "candidate_agents": ["ethics-committee"],
                    },
                ],
                "builder_handoff": [
                    {
                        "coverage_area": "runtime",
                        "candidate_agents": ["codex-builder"],
                    },
                    {
                        "coverage_area": "schema",
                        "candidate_agents": ["schema-builder"],
                    },
                    {
                        "coverage_area": "eval",
                        "candidate_agents": ["eval-builder"],
                    },
                    {
                        "coverage_area": "docs",
                        "candidate_agents": ["doc-sync-builder"],
                    },
                ],
                "task_graph_bundle_strategy_id": YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES[
                    "memory-edit-v1"
                ]["strategy_id"],
            },
            "fork-request-v1": {
                "summary": "Prepare a bounded Council review and triple-approval fork handoff for one identity fork request.",
                "workspace_review_policy_id": "fork-request-cross-workspace-review-v1",
                "workspace_review_budget": 3,
                "required_workspace_coverage_areas": ["runtime", "schema", "docs"],
                "optional_workspace_coverage_areas": ["eval"],
                "council_roles": [
                    {
                        "role_id": "identity-protector",
                        "role_label": "IdentityProtector",
                        "candidate_agents": ["identity-guardian"],
                    },
                    {
                        "role_id": "legal-scholar",
                        "role_label": "LegalScholar",
                        "candidate_agents": ["legal-scholar"],
                    },
                    {
                        "role_id": "conservatism-advocate",
                        "role_label": "ConservatismAdvocate",
                        "candidate_agents": ["conservatism-advocate"],
                    },
                    {
                        "role_id": "ethics-committee",
                        "role_label": "EthicsCommittee",
                        "candidate_agents": ["ethics-committee"],
                    },
                ],
                "builder_handoff": [
                    {
                        "coverage_area": "runtime",
                        "candidate_agents": ["codex-builder"],
                    },
                    {
                        "coverage_area": "schema",
                        "candidate_agents": ["schema-builder"],
                    },
                    {
                        "coverage_area": "eval",
                        "candidate_agents": ["eval-builder"],
                    },
                    {
                        "coverage_area": "docs",
                        "candidate_agents": ["doc-sync-builder"],
                    },
                ],
                "task_graph_bundle_strategy_id": YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES[
                    "fork-request-v1"
                ]["strategy_id"],
            },
            "inter-mind-negotiation-v1": {
                "summary": "Prepare a bounded Council review and inter-mind negotiation handoff for one disclosure, merge, or collective contract update.",
                "workspace_review_policy_id": "inter-mind-negotiation-cross-workspace-review-v1",
                "workspace_review_budget": 3,
                "required_workspace_coverage_areas": ["runtime", "schema", "eval", "docs"],
                "optional_workspace_coverage_areas": [],
                "council_roles": [
                    {
                        "role_id": "legal-scholar",
                        "role_label": "LegalScholar",
                        "candidate_agents": ["legal-scholar"],
                    },
                    {
                        "role_id": "design-auditor",
                        "role_label": "DesignAuditor",
                        "candidate_agents": ["design-architect"],
                    },
                    {
                        "role_id": "conservatism-advocate",
                        "role_label": "ConservatismAdvocate",
                        "candidate_agents": ["conservatism-advocate"],
                    },
                    {
                        "role_id": "ethics-committee",
                        "role_label": "EthicsCommittee",
                        "candidate_agents": ["ethics-committee"],
                    },
                ],
                "builder_handoff": [
                    {
                        "coverage_area": "runtime",
                        "candidate_agents": ["codex-builder"],
                    },
                    {
                        "coverage_area": "schema",
                        "candidate_agents": ["schema-builder"],
                    },
                    {
                        "coverage_area": "eval",
                        "candidate_agents": ["eval-builder"],
                    },
                    {
                        "coverage_area": "docs",
                        "candidate_agents": ["doc-sync-builder"],
                    },
                ],
                "task_graph_bundle_strategy_id": YAOYOROZU_TASK_GRAPH_BUNDLE_STRATEGIES[
                    "inter-mind-negotiation-v1"
                ]["strategy_id"],
            },
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class YaoyorozuRegistryService:
    """Sync repo-local agent definitions and derive deterministic convocation plans."""

    def __init__(
        self,
        *,
        trust_service: Optional[TrustService] = None,
        policy: Optional[YaoyorozuRegistryPolicy] = None,
        design_reader: Optional[DesignReaderService] = None,
        patch_generator: Optional[PatchGeneratorService] = None,
    ) -> None:
        self._trust = trust_service or TrustService()
        self._policy = policy or YaoyorozuRegistryPolicy()
        self._design_reader = design_reader or DesignReaderService()
        self._patch_generator = patch_generator or PatchGeneratorService()
        self._entries: Dict[str, YaoyorozuRegistryEntry] = {}
        self._agents_root: Optional[Path] = None
        self._last_snapshot_id: Optional[str] = None

    def policy_snapshot(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def _normalize_requested_optional_coverage_areas(
        self,
        proposal_profile: str,
        requested_optional_coverage_areas: Optional[Sequence[str]] = None,
    ) -> List[str]:
        profile_policy = self._proposal_profile_policy(proposal_profile)
        allowed_optional = list(profile_policy["optional_worker_coverage_areas"])
        if requested_optional_coverage_areas is None:
            return []

        requested = [
            _non_empty_string(str(area), "requested_optional_coverage_area")
            for area in requested_optional_coverage_areas
        ]
        if len(set(requested)) != len(requested):
            raise ValueError("requested_optional_coverage_areas must remain unique")
        invalid = [area for area in requested if area not in allowed_optional]
        if invalid:
            raise ValueError(
                "requested_optional_coverage_areas must stay within the proposal profile's optional worker coverage"
            )
        return [area for area in allowed_optional if area in requested]

    def _dispatch_coverage_areas(
        self,
        proposal_profile: str,
        requested_optional_coverage_areas: Optional[Sequence[str]] = None,
    ) -> List[str]:
        profile_policy = self._proposal_profile_policy(proposal_profile)
        requested_optional = self._normalize_requested_optional_coverage_areas(
            proposal_profile,
            requested_optional_coverage_areas,
        )
        return list(profile_policy["required_worker_coverage_areas"]) + requested_optional

    def _proposal_profile_policy(self, proposal_profile: str) -> Dict[str, Any]:
        profile = self._policy.council_profiles.get(proposal_profile)
        if not isinstance(profile, Mapping):
            raise ValueError(f"unsupported proposal profile: {proposal_profile}")

        review_budget = profile.get("workspace_review_budget")
        if not isinstance(review_budget, int):
            raise ValueError("workspace_review_budget must be an integer")
        if review_budget < 2 or review_budget > self._policy.workspace_review_budget:
            raise ValueError(
                f"workspace_review_budget must be between 2 and {self._policy.workspace_review_budget}"
            )

        required_coverage_areas = [
            _non_empty_string(area, "required_workspace_coverage_area")
            for area in profile.get("required_workspace_coverage_areas", [])
        ]
        optional_coverage_areas = [
            _non_empty_string(area, "optional_workspace_coverage_area")
            for area in profile.get("optional_workspace_coverage_areas", [])
        ]
        if not required_coverage_areas:
            raise ValueError("required_workspace_coverage_areas must not be empty")

        total_coverage_areas = required_coverage_areas + optional_coverage_areas
        if len(set(total_coverage_areas)) != len(total_coverage_areas):
            raise ValueError("workspace coverage areas must remain unique per proposal profile")
        if sorted(total_coverage_areas) != sorted(self._policy.worker_target_paths):
            raise ValueError(
                "workspace coverage areas must partition runtime, schema, eval, and docs"
            )

        return {
            "proposal_profile": proposal_profile,
            "workspace_review_policy_id": _non_empty_string(
                profile.get("workspace_review_policy_id"),
                "workspace_review_policy_id",
            ),
            "workspace_review_budget": review_budget,
            "required_workspace_coverage_areas": required_coverage_areas,
            "optional_workspace_coverage_areas": optional_coverage_areas,
            "required_worker_coverage_areas": list(required_coverage_areas),
            "optional_worker_coverage_areas": list(optional_coverage_areas),
            "task_graph_bundle_strategy_id": _non_empty_string(
                profile.get("task_graph_bundle_strategy_id"),
                "task_graph_bundle_strategy_id",
            ),
        }

    def _workspace_index(
        self,
        workspace_discovery: Mapping[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}
        for workspace in workspace_discovery.get("workspaces", []):
            if not isinstance(workspace, Mapping):
                continue
            workspace_ref = str(workspace.get("workspace_ref", "")).strip()
            if workspace_ref:
                index[workspace_ref] = dict(workspace)
        return index

    def _build_workspace_execution_binding(
        self,
        *,
        workspace_discovery: Mapping[str, Any],
        dispatch_builder_coverage: Sequence[str],
        required_builder_coverage: Sequence[str],
    ) -> Dict[str, Any]:
        workspace_index = self._workspace_index(workspace_discovery)
        source_workspace_ref = _non_empty_string(
            workspace_discovery.get("source_workspace_ref"),
            "workspace_discovery.source_workspace_ref",
        )
        source_workspace = workspace_index.get(source_workspace_ref)
        if source_workspace is None:
            raise ValueError("workspace_discovery source workspace must remain bound")

        coverage_summary = workspace_discovery.get("coverage_summary", {})
        if not isinstance(coverage_summary, Mapping):
            raise ValueError("workspace_discovery.coverage_summary must be a mapping")
        non_source_coverage_map = coverage_summary.get("non_source_coverage_to_workspace_refs", {})
        if not isinstance(non_source_coverage_map, Mapping):
            raise ValueError(
                "workspace_discovery.coverage_summary.non_source_coverage_to_workspace_refs must be a mapping"
            )

        execution_targets: List[Dict[str, Any]] = []
        candidate_bound_coverage_areas: List[str] = []
        source_bound_coverage_areas: List[str] = []
        for coverage_area in dispatch_builder_coverage:
            candidate_refs = non_source_coverage_map.get(coverage_area, [])
            if not isinstance(candidate_refs, list):
                candidate_refs = []
            selected_workspace = None
            selected_scope = self._policy.worker_workspace_scope
            sandbox_seed_strategy = self._policy.inline_workspace_seed_strategy
            if candidate_refs:
                for workspace_ref in candidate_refs:
                    workspace = workspace_index.get(str(workspace_ref))
                    if workspace is not None:
                        selected_workspace = workspace
                        break
            if selected_workspace is None:
                selected_workspace = source_workspace
                source_bound_coverage_areas.append(str(coverage_area))
            else:
                selected_scope = self._policy.external_workspace_scope
                sandbox_seed_strategy = self._policy.external_workspace_seed_strategy
                candidate_bound_coverage_areas.append(str(coverage_area))
            dependency_materialization_required = (
                selected_scope == self._policy.external_workspace_scope
            )
            dependency_materialization_strategy = (
                self._policy.external_dependency_materialization_strategy
                if dependency_materialization_required
                else self._policy.inline_dependency_materialization_strategy
            )
            dependency_materialization_paths = (
                list(self._policy.dependency_materialization_paths)
                if dependency_materialization_required
                else []
            )

            target = {
                "coverage_area": str(coverage_area),
                "workspace_ref": _non_empty_string(
                    selected_workspace.get("workspace_ref"),
                    f"workspace_execution_binding.{coverage_area}.workspace_ref",
                ),
                "workspace_root": _non_empty_string(
                    selected_workspace.get("workspace_root"),
                    f"workspace_execution_binding.{coverage_area}.workspace_root",
                ),
                "workspace_role": _non_empty_string(
                    selected_workspace.get("workspace_role"),
                    f"workspace_execution_binding.{coverage_area}.workspace_role",
                ),
                "source_kind": _non_empty_string(
                    selected_workspace.get("source_kind"),
                    f"workspace_execution_binding.{coverage_area}.source_kind",
                ),
                "workspace_scope": selected_scope,
                "execution_transport_profile": self._policy.workspace_execution_transport_profile,
                "sandbox_seed_strategy": sandbox_seed_strategy,
                "dependency_materialization_profile": (
                    self._policy.dependency_materialization_profile
                ),
                "dependency_materialization_strategy": dependency_materialization_strategy,
                "dependency_materialization_required": dependency_materialization_required,
                "dependency_materialization_paths": dependency_materialization_paths,
                "guardian_preseed_gate_required": (
                    selected_scope == self._policy.external_workspace_scope
                ),
            }
            target["target_digest"] = sha256_text(
                canonical_json(_workspace_execution_target_digest_payload(target))
            )
            execution_targets.append(target)

        dispatch_builder_coverage_list = list(dispatch_builder_coverage)
        required_builder_coverage_list = list(required_builder_coverage)
        binding = {
            "execution_policy_id": self._policy.workspace_execution_policy_id,
            "host_ref": self._policy.workspace_discovery_host_ref,
            "source_workspace_ref": source_workspace_ref,
            "source_workspace_root": _non_empty_string(
                source_workspace.get("workspace_root"),
                "workspace_discovery.source_workspace_root",
            ),
            "dispatch_builder_coverage_areas": dispatch_builder_coverage_list,
            "required_candidate_binding_areas": required_builder_coverage_list,
            "candidate_bound_coverage_areas": candidate_bound_coverage_areas,
            "source_bound_coverage_areas": source_bound_coverage_areas,
            "execution_targets": execution_targets,
        }
        binding["binding_digest"] = sha256_text(canonical_json(binding))
        return binding

    @staticmethod
    def _external_execution_workspace_root(
        selected_workspace_root: str,
        dispatch_id: str,
        coverage_area: str,
    ) -> Path:
        return (
            Path(selected_workspace_root).resolve()
            / ".yaoyorozu-external-execution"
            / dispatch_id
            / coverage_area
        )

    @staticmethod
    def _copy_target_path_into_workspace(
        *,
        source_root: Path,
        execution_root: Path,
        target_path: str,
    ) -> None:
        source_path = (source_root / target_path).resolve()
        destination_path = (execution_root / target_path).resolve()
        if not source_path.exists():
            raise ValueError(f"source target path does not exist for external execution: {target_path}")
        if source_path.is_dir():
            shutil.copytree(
                source_path,
                destination_path,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(
                    "__pycache__",
                    "*.pyc",
                    "*.pyo",
                    ".mypy_cache",
                    ".pytest_cache",
                    ".ruff_cache",
                ),
            )
            return
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

    def _seed_external_execution_workspace(
        self,
        *,
        source_root: Path,
        execution_root: Path,
        target_paths: Sequence[str],
    ) -> str:
        if execution_root.exists():
            shutil.rmtree(execution_root)
        execution_root.mkdir(parents=True, exist_ok=True)
        for target_path in target_paths:
            self._copy_target_path_into_workspace(
                source_root=source_root,
                execution_root=execution_root,
                target_path=str(target_path),
            )
        subprocess.run(
            ["git", "init"],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "yaoyorozu@example.local"],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Yaoyorozu External Dispatch"],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Seed external workspace dispatch sandbox"],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=execution_root,
            check=True,
            capture_output=True,
            text=True,
        )
        return head.stdout.strip()

    def _materialize_external_execution_dependencies(
        self,
        *,
        source_root: Path,
        execution_root: Path,
        dispatch_plan_ref: str,
        dispatch_unit_ref: str,
        coverage_area: str,
        dependency_paths: Sequence[str],
    ) -> Dict[str, Any]:
        dependency_root = execution_root / YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT
        if dependency_root.exists():
            shutil.rmtree(dependency_root)
        dependency_root.mkdir(parents=True, exist_ok=True)

        files: List[Dict[str, Any]] = []
        for dependency_path in dependency_paths:
            relative_path = str(dependency_path).strip()
            if not relative_path or relative_path.startswith("../") or relative_path.startswith("/"):
                raise ValueError("dependency materialization paths must stay repo-relative")
            source_path = (source_root / relative_path).resolve()
            if not source_path.is_file():
                raise ValueError(
                    f"dependency materialization source file does not exist: {relative_path}"
                )
            materialized_path = (dependency_root / relative_path).resolve()
            materialized_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, materialized_path)
            source_text = source_path.read_text(encoding="utf-8", errors="replace")
            materialized_text = materialized_path.read_text(encoding="utf-8", errors="replace")
            source_digest = sha256_text(source_text)
            materialized_digest = sha256_text(materialized_text)
            file_entry = {
                "source_path": relative_path,
                "materialized_path": str(materialized_path),
                "source_digest": source_digest,
                "materialized_digest": materialized_digest,
                "byte_count": len(materialized_text.encode("utf-8")),
                "status": "copied" if source_digest == materialized_digest else "mismatch",
            }
            file_entry["entry_digest"] = sha256_text(canonical_json(file_entry))
            files.append(file_entry)

        manifest_id = new_id("yaoyorozu-dependencies")
        lockfile_path = dependency_root / "dependency-lockfile.json"
        lockfile_payload = {
            "kind": "yaoyorozu_dependency_lockfile",
            "schema_version": "1.0.0",
            "lockfile_profile": self._policy.dependency_lockfile_profile,
            "manifest_ref": f"dependency-manifest://{manifest_id}",
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_unit_ref": dispatch_unit_ref,
            "coverage_area": coverage_area,
            "dependency_paths": [
                {
                    "source_path": file_entry["source_path"],
                    "source_digest": file_entry["source_digest"],
                    "materialized_digest": file_entry["materialized_digest"],
                    "byte_count": file_entry["byte_count"],
                    "entry_digest": file_entry["entry_digest"],
                }
                for file_entry in files
            ],
            "file_count": len(files),
        }
        lockfile_digest = sha256_text(canonical_json(lockfile_payload))
        lockfile_payload["lockfile_digest"] = lockfile_digest
        lockfile_path.write_text(
            json.dumps(lockfile_payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        wheel_dir = dependency_root / "sealed-wheel"
        wheel_dir.mkdir(parents=True, exist_ok=True)
        wheel_path = wheel_dir / YAOYOROZU_DEPENDENCY_WHEEL_ARTIFACT_NAME
        with zipfile.ZipFile(
            wheel_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for file_entry in files:
                source_path = str(file_entry["source_path"])
                materialized_path = Path(str(file_entry["materialized_path"]))
                archive_path = f"omoikane_reference_runtime/{source_path}"
                info = zipfile.ZipInfo(archive_path, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, materialized_path.read_bytes())
            lock_info = zipfile.ZipInfo(
                "omoikane_reference_runtime/dependency-lockfile.json",
                date_time=(2026, 1, 1, 0, 0, 0),
            )
            lock_info.compress_type = zipfile.ZIP_DEFLATED
            lock_info.external_attr = 0o644 << 16
            archive.writestr(lock_info, lockfile_path.read_bytes())
        wheel_bytes = wheel_path.read_bytes()
        wheel_artifact_ref = (
            f"wheel-artifact://{manifest_id}/{YAOYOROZU_DEPENDENCY_WHEEL_ARTIFACT_NAME}"
        )
        manifest_path = dependency_root / "manifest.json"
        manifest = {
            "kind": "yaoyorozu_dependency_materialization_manifest",
            "schema_version": "1.0.0",
            "manifest_id": manifest_id,
            "manifest_ref": f"dependency-manifest://{manifest_id}",
            "profile": self._policy.dependency_materialization_profile,
            "strategy": self._policy.external_dependency_materialization_strategy,
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_unit_ref": dispatch_unit_ref,
            "coverage_area": coverage_area,
            "workspace_root": str(execution_root),
            "dependency_root": str(dependency_root),
            "manifest_path": str(manifest_path),
            "required": True,
            "status": "materialized"
            if files and all(file_entry["status"] == "copied" for file_entry in files)
            else "blocked",
            "file_count": len(files),
            "files": files,
            "lockfile_profile": self._policy.dependency_lockfile_profile,
            "lockfile_path": str(lockfile_path),
            "lockfile_digest": lockfile_digest,
            "lockfile_byte_count": len(lockfile_path.read_bytes()),
            "lockfile_status": "attested" if files else "blocked",
            "wheel_artifact_ref": wheel_artifact_ref,
            "wheel_artifact_path": str(wheel_path),
            "wheel_artifact_digest": _sha256_bytes(wheel_bytes),
            "wheel_artifact_byte_count": len(wheel_bytes),
            "wheel_artifact_status": "attested" if files else "blocked",
            "wheel_attestation_profile": (
                self._policy.dependency_wheel_attestation_profile
            ),
            "wheel_attestation_digest": "",
            "attested_file_count": len(files),
        }
        manifest["wheel_attestation_digest"] = sha256_text(
            canonical_json(_dependency_wheel_attestation_digest_payload(manifest))
        )
        manifest["manifest_digest"] = sha256_text(
            canonical_json(_dependency_materialization_manifest_digest_payload(manifest))
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest

    def _validate_dependency_materialization_manifest(
        self,
        manifest: Mapping[str, Any] | None,
        *,
        dispatch_plan_ref: str,
        dispatch_unit_ref: str,
        coverage_area: str,
        workspace_root: str,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(manifest, Mapping):
            return {
                "ok": False,
                "status": "missing",
                "file_count": 0,
                "manifest_ref": "",
                "manifest_digest": "",
                "lockfile_attested": False,
                "wheel_attested": False,
                "errors": ["dependency_materialization_manifest must be bound"],
            }
        if manifest.get("kind") != "yaoyorozu_dependency_materialization_manifest":
            errors.append("dependency_materialization_manifest.kind mismatch")
        if manifest.get("schema_version") != "1.0.0":
            errors.append("dependency_materialization_manifest.schema_version mismatch")
        if manifest.get("profile") != self._policy.dependency_materialization_profile:
            errors.append("dependency_materialization_manifest.profile mismatch")
        if manifest.get("strategy") != self._policy.external_dependency_materialization_strategy:
            errors.append("dependency_materialization_manifest.strategy mismatch")
        if manifest.get("dispatch_plan_ref") != dispatch_plan_ref:
            errors.append("dependency_materialization_manifest.dispatch_plan_ref mismatch")
        if manifest.get("dispatch_unit_ref") != dispatch_unit_ref:
            errors.append("dependency_materialization_manifest.dispatch_unit_ref mismatch")
        if manifest.get("coverage_area") != coverage_area:
            errors.append("dependency_materialization_manifest.coverage_area mismatch")
        if manifest.get("workspace_root") != workspace_root:
            errors.append("dependency_materialization_manifest.workspace_root mismatch")
        if manifest.get("required") is not True:
            errors.append("dependency_materialization_manifest.required must be true")
        files = manifest.get("files", [])
        if not isinstance(files, list):
            errors.append("dependency_materialization_manifest.files must be a list")
            files = []
        if manifest.get("file_count") != len(files):
            errors.append("dependency_materialization_manifest.file_count mismatch")
        if manifest.get("file_count") != len(self._policy.dependency_materialization_paths):
            errors.append("dependency_materialization_manifest.file_count must match policy paths")
        if manifest.get("attested_file_count") != manifest.get("file_count"):
            errors.append("dependency_materialization_manifest.attested_file_count mismatch")
        expected_paths = list(self._policy.dependency_materialization_paths)
        observed_paths = [
            str(file_entry.get("source_path", ""))
            for file_entry in files
            if isinstance(file_entry, Mapping)
        ]
        if observed_paths != expected_paths:
            errors.append("dependency_materialization_manifest source paths mismatch")
        dependency_root = str(manifest.get("dependency_root", "")).strip()
        if not dependency_root.endswith(YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT):
            errors.append("dependency_materialization_manifest.dependency_root mismatch")
        for file_entry in files:
            if not isinstance(file_entry, Mapping):
                errors.append("dependency materialization file entries must be mappings")
                continue
            if file_entry.get("status") != "copied":
                errors.append("dependency materialization file status must be copied")
            if file_entry.get("source_digest") != file_entry.get("materialized_digest"):
                errors.append("dependency materialization file digest mismatch")
            if not str(file_entry.get("entry_digest", "")).strip():
                errors.append("dependency materialization file entry_digest must be present")
            materialized_path = str(file_entry.get("materialized_path", ""))
            if dependency_root and not materialized_path.startswith(f"{dependency_root}/"):
                errors.append("dependency materialization file must live under dependency_root")
        if manifest.get("lockfile_profile") != self._policy.dependency_lockfile_profile:
            errors.append("dependency_materialization_manifest.lockfile_profile mismatch")
        lockfile_path = str(manifest.get("lockfile_path", "")).strip()
        if dependency_root and not lockfile_path.startswith(f"{dependency_root}/"):
            errors.append("dependency lockfile must live under dependency_root")
        if manifest.get("lockfile_status") != "attested":
            errors.append("dependency lockfile status must be attested")
        lockfile_file = Path(lockfile_path) if lockfile_path else Path()
        if lockfile_file.is_file():
            try:
                lockfile_payload = json.loads(lockfile_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                lockfile_payload = {}
                errors.append("dependency lockfile must be valid JSON")
            if isinstance(lockfile_payload, Mapping):
                lockfile_payload_for_digest = dict(lockfile_payload)
                observed_lockfile_digest = str(
                    lockfile_payload_for_digest.pop("lockfile_digest", "")
                )
                expected_lockfile_digest = sha256_text(
                    canonical_json(lockfile_payload_for_digest)
                )
                if observed_lockfile_digest != expected_lockfile_digest:
                    errors.append("dependency lockfile embedded digest mismatch")
                if manifest.get("lockfile_digest") != expected_lockfile_digest:
                    errors.append("dependency lockfile digest mismatch")
                if lockfile_payload.get("file_count") != manifest.get("file_count"):
                    errors.append("dependency lockfile file_count mismatch")
        else:
            errors.append("dependency lockfile path must exist")
        try:
            lockfile_byte_count = lockfile_file.stat().st_size
        except OSError:
            lockfile_byte_count = -1
        if manifest.get("lockfile_byte_count") != lockfile_byte_count:
            errors.append("dependency lockfile byte_count mismatch")
        if (
            manifest.get("wheel_attestation_profile")
            != self._policy.dependency_wheel_attestation_profile
        ):
            errors.append("dependency wheel_attestation_profile mismatch")
        if manifest.get("wheel_artifact_status") != "attested":
            errors.append("dependency wheel artifact status must be attested")
        wheel_artifact_ref = str(manifest.get("wheel_artifact_ref", "")).strip()
        if not wheel_artifact_ref.startswith(f"wheel-artifact://{manifest.get('manifest_id', '')}/"):
            errors.append("dependency wheel_artifact_ref must bind manifest_id")
        wheel_artifact_path = str(manifest.get("wheel_artifact_path", "")).strip()
        if dependency_root and not wheel_artifact_path.startswith(f"{dependency_root}/"):
            errors.append("dependency wheel artifact must live under dependency_root")
        wheel_file = Path(wheel_artifact_path) if wheel_artifact_path else Path()
        if wheel_file.is_file():
            wheel_bytes = wheel_file.read_bytes()
            if manifest.get("wheel_artifact_digest") != _sha256_bytes(wheel_bytes):
                errors.append("dependency wheel artifact digest mismatch")
            if manifest.get("wheel_artifact_byte_count") != len(wheel_bytes):
                errors.append("dependency wheel artifact byte_count mismatch")
        else:
            errors.append("dependency wheel artifact path must exist")
        try:
            expected_attestation_digest = sha256_text(
                canonical_json(_dependency_wheel_attestation_digest_payload(manifest))
            )
        except KeyError:
            expected_attestation_digest = ""
            errors.append("dependency wheel attestation payload is missing required fields")
        if manifest.get("wheel_attestation_digest") != expected_attestation_digest:
            errors.append("dependency wheel attestation digest mismatch")
        try:
            expected_digest = sha256_text(
                canonical_json(_dependency_materialization_manifest_digest_payload(manifest))
            )
        except KeyError:
            expected_digest = ""
            errors.append("dependency_materialization_manifest digest payload is missing required fields")
        if manifest.get("manifest_digest") != expected_digest:
            errors.append("dependency_materialization_manifest.manifest_digest mismatch")
        return {
            "ok": not errors,
            "status": str(manifest.get("status", "")),
            "file_count": int(manifest.get("file_count", 0))
            if isinstance(manifest.get("file_count", 0), int)
            else 0,
            "manifest_ref": str(manifest.get("manifest_ref", "")),
            "manifest_digest": str(manifest.get("manifest_digest", "")),
            "lockfile_attested": (
                not errors
                and manifest.get("lockfile_status") == "attested"
                and bool(manifest.get("lockfile_digest"))
            ),
            "wheel_attested": (
                not errors
                and manifest.get("wheel_artifact_status") == "attested"
                and bool(manifest.get("wheel_attestation_digest"))
            ),
            "errors": errors,
        }

    def _validate_worker_module_origin(
        self,
        origin: Mapping[str, Any] | None,
        *,
        expected_module_root: str,
        source_src_root: str,
        workspace_scope: str,
        expected_module_digest: str = "",
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if not isinstance(origin, Mapping):
            return {
                "ok": False,
                "profile": self._policy.dependency_module_origin_profile,
                "module_file": "",
                "module_digest": "",
                "errors": ["worker_module_origin must be bound"],
            }
        if origin.get("profile") != self._policy.dependency_module_origin_profile:
            errors.append("worker_module_origin.profile mismatch")
        if origin.get("module_name") != YAOYOROZU_WORKER_MODULE_NAME:
            errors.append("worker_module_origin.module_name mismatch")
        expected_module_file = str(
            Path(expected_module_root) / YAOYOROZU_WORKER_MODULE_RELATIVE_PATH
        )
        module_file = str(origin.get("module_file", ""))
        if module_file != expected_module_file:
            errors.append("worker_module_origin.module_file mismatch")
        module_path = Path(module_file)
        if expected_module_digest:
            expected_digest = expected_module_digest
        elif module_path.is_file():
            expected_digest = sha256_text(
                module_path.read_text(encoding="utf-8", errors="replace")
            )
        else:
            expected_digest = ""
            errors.append("worker_module_origin.module_file must exist")
        if origin.get("module_digest") != expected_digest:
            errors.append("worker_module_origin.module_digest mismatch")
        search_path_head = origin.get("search_path_head", [])
        if not isinstance(search_path_head, list):
            search_path_head = []
            errors.append("worker_module_origin.search_path_head must be a list")
        expected_module_root_text = str(Path(expected_module_root).resolve())
        source_src_root_text = str(Path(source_src_root).resolve())
        search_path_text = [str(path) for path in search_path_head]
        if expected_module_root_text not in search_path_text:
            errors.append("worker_module_origin.search_path_head missing expected module root")
        if workspace_scope == self._policy.external_workspace_scope:
            if source_src_root_text in search_path_text:
                errors.append("worker_module_origin.search_path_head must omit source fallback root")
        try:
            expected_origin_digest = sha256_text(
                canonical_json(worker_module_origin_digest_payload(origin))
            )
        except KeyError:
            expected_origin_digest = ""
            errors.append("worker_module_origin digest payload is missing required fields")
        if origin.get("origin_digest") != expected_origin_digest:
            errors.append("worker_module_origin.origin_digest mismatch")
        return {
            "ok": not errors,
            "profile": str(origin.get("profile", "")),
            "module_file": module_file,
            "module_digest": str(origin.get("module_digest", "")),
            "errors": errors,
        }

    def _build_guardian_preseed_gate(
        self,
        *,
        dispatch_plan_ref: str,
        dispatch_unit_ref: str,
        proposal_profile: str,
        coverage_area: str,
        workspace_ref: str,
        selected_workspace_root: str,
        execution_workspace_root: str,
        execution_host_ref: str,
        workspace_scope: str,
        sandbox_seed_strategy: str,
        target_digest: str,
        guardian_agent_id: str,
    ) -> Dict[str, Any]:
        gate_required = workspace_scope == self._policy.external_workspace_scope
        gate_status = "pass" if gate_required else "not-required"
        gate_id = new_id("workspace-preseed-gate")
        gate_ref = f"guardian-preseed-gate://{gate_id}"
        oversight_event = (
            _build_preseed_oversight_event(
                gate_ref=gate_ref,
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=dispatch_unit_ref,
                proposal_profile=proposal_profile,
                coverage_area=coverage_area,
                workspace_ref=workspace_ref,
                target_digest=target_digest,
            )
            if gate_required
            else None
        )
        oversight_event_digest = (
            sha256_text(canonical_json(oversight_event)) if oversight_event is not None else ""
        )
        reviewer_quorum_required = (
            int(oversight_event["human_attestation"]["required_quorum"])
            if oversight_event is not None
            else 0
        )
        reviewer_quorum_received = (
            int(oversight_event["human_attestation"]["received_quorum"])
            if oversight_event is not None
            else 0
        )
        gate = {
            "kind": "yaoyorozu_workspace_guardian_preseed_gate",
            "schema_version": "1.0.0",
            "gate_id": gate_id,
            "gate_ref": gate_ref,
            "gate_profile": self._policy.workspace_guardian_gate_profile,
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_unit_ref": dispatch_unit_ref,
            "proposal_profile": proposal_profile,
            "coverage_area": coverage_area,
            "workspace_ref": workspace_ref,
            "selected_workspace_root": selected_workspace_root,
            "execution_workspace_root": execution_workspace_root,
            "execution_host_ref": execution_host_ref,
            "workspace_scope": workspace_scope,
            "sandbox_seed_strategy": sandbox_seed_strategy,
            "target_digest": target_digest,
            "guardian_agent_id": guardian_agent_id,
            "guardian_role": self._policy.workspace_guardian_role,
            "oversight_category": self._policy.workspace_guardian_category,
            "oversight_binding_profile": (
                YAOYOROZU_WORKSPACE_GUARDIAN_OVERSIGHT_BINDING_PROFILE
            ),
            "guardian_oversight_event_ref": (
                f"oversight://{oversight_event['event_id']}"
                if oversight_event is not None
                else ""
            ),
            "guardian_oversight_event_digest": oversight_event_digest,
            "guardian_oversight_event_status": (
                str(oversight_event["human_attestation"]["status"])
                if oversight_event is not None
                else "not-required"
            ),
            "guardian_oversight_event": oversight_event,
            "reviewer_network_attested": oversight_event is not None,
            "reviewer_quorum_required": reviewer_quorum_required,
            "reviewer_quorum_received": reviewer_quorum_received,
            "required_before": list(self._policy.workspace_guardian_required_before),
            "gate_required": gate_required,
            "gate_status": gate_status,
            "decision_reason": (
                "Integrity guardian and HumanOversightChannel reviewers attest that source target-path snapshot seeding, execution root creation, and dependency materialization remain same-host and digest-bound."
                if gate_required
                else "Repo-local dispatch does not create an external execution root, so the preseed gate is not required."
            ),
        }
        gate["gate_digest"] = sha256_text(canonical_json(_guardian_preseed_gate_digest_payload(gate)))
        return gate

    def _validate_guardian_preseed_gate(
        self,
        gate: Mapping[str, Any],
        *,
        dispatch_plan_ref: str,
        dispatch_unit_ref: str,
        proposal_profile: str,
        coverage_area: str,
        workspace_ref: str,
        selected_workspace_root: str,
        execution_workspace_root: str,
        execution_host_ref: str,
        workspace_scope: str,
        sandbox_seed_strategy: str,
        target_digest: str,
        guardian_agent_id: str,
    ) -> Dict[str, Any]:
        errors: List[str] = []
        gate_required = workspace_scope == self._policy.external_workspace_scope
        if not isinstance(gate, Mapping):
            return {
                "ok": False,
                "gate_required": gate_required,
                "gate_passed": False,
                "errors": ["guardian_preseed_gate must be a mapping"],
            }
        expected = {
            "kind": "yaoyorozu_workspace_guardian_preseed_gate",
            "schema_version": "1.0.0",
            "gate_profile": self._policy.workspace_guardian_gate_profile,
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_unit_ref": dispatch_unit_ref,
            "proposal_profile": proposal_profile,
            "coverage_area": coverage_area,
            "workspace_ref": workspace_ref,
            "selected_workspace_root": selected_workspace_root,
            "execution_workspace_root": execution_workspace_root,
            "execution_host_ref": execution_host_ref,
            "workspace_scope": workspace_scope,
            "sandbox_seed_strategy": sandbox_seed_strategy,
            "target_digest": target_digest,
            "guardian_agent_id": guardian_agent_id,
            "guardian_role": self._policy.workspace_guardian_role,
            "oversight_category": self._policy.workspace_guardian_category,
            "oversight_binding_profile": (
                YAOYOROZU_WORKSPACE_GUARDIAN_OVERSIGHT_BINDING_PROFILE
            ),
            "required_before": list(self._policy.workspace_guardian_required_before),
            "gate_required": gate_required,
            "gate_status": "pass" if gate_required else "not-required",
        }
        for key, expected_value in expected.items():
            if gate.get(key) != expected_value:
                errors.append(f"guardian_preseed_gate.{key} mismatch")
        gate_id = str(gate.get("gate_id", "")).strip()
        if not gate_id.startswith("workspace-preseed-gate-"):
            errors.append("guardian_preseed_gate.gate_id must use workspace-preseed-gate prefix")
        if gate.get("gate_ref") != f"guardian-preseed-gate://{gate_id}":
            errors.append("guardian_preseed_gate.gate_ref must bind gate_id")
        if not str(gate.get("decision_reason", "")).strip():
            errors.append("guardian_preseed_gate.decision_reason must be non-empty")
        oversight_event = gate.get("guardian_oversight_event")
        oversight_event_satisfied = False
        reviewer_network_attested = False
        reviewer_quorum_required = 0
        reviewer_quorum_received = 0
        if gate_required:
            if not isinstance(oversight_event, Mapping):
                errors.append("guardian_preseed_gate.guardian_oversight_event must be bound")
            else:
                human_attestation = oversight_event.get("human_attestation", {})
                reviewer_bindings = oversight_event.get("reviewer_bindings", [])
                if oversight_event.get("kind") != "guardian_oversight_event":
                    errors.append("guardian_oversight_event.kind mismatch")
                if oversight_event.get("guardian_role") != self._policy.workspace_guardian_role:
                    errors.append("guardian_oversight_event.guardian_role mismatch")
                if oversight_event.get("category") != self._policy.workspace_guardian_category:
                    errors.append("guardian_oversight_event.category mismatch")
                if oversight_event.get("payload_ref") != gate.get("gate_ref"):
                    errors.append("guardian_oversight_event.payload_ref must bind gate_ref")
                if not isinstance(human_attestation, Mapping):
                    errors.append("guardian_oversight_event.human_attestation must be a mapping")
                else:
                    reviewer_quorum_required = int(
                        human_attestation.get("required_quorum", 0)
                        if isinstance(human_attestation.get("required_quorum", 0), int)
                        else 0
                    )
                    reviewer_quorum_received = int(
                        human_attestation.get("received_quorum", 0)
                        if isinstance(human_attestation.get("received_quorum", 0), int)
                        else 0
                    )
                    oversight_event_satisfied = (
                        human_attestation.get("status") == "satisfied"
                        and reviewer_quorum_required >= 2
                        and reviewer_quorum_received >= reviewer_quorum_required
                    )
                    if not oversight_event_satisfied:
                        errors.append(
                            "guardian_oversight_event.human_attestation must satisfy reviewer quorum"
                        )
                if not isinstance(reviewer_bindings, list) or not reviewer_bindings:
                    errors.append("guardian_oversight_event.reviewer_bindings must be non-empty")
                else:
                    reviewer_network_attested = all(
                        isinstance(binding, Mapping)
                        and binding.get("guardian_role") == self._policy.workspace_guardian_role
                        and binding.get("category") == self._policy.workspace_guardian_category
                        and bool(binding.get("network_receipt_id"))
                        and bool(binding.get("transport_exchange_digest"))
                        and bool(binding.get("legal_execution_digest"))
                        and bool(binding.get("authority_chain_ref"))
                        and bool(binding.get("trust_root_ref"))
                        and bool(binding.get("trust_root_digest"))
                        for binding in reviewer_bindings
                    )
                    if not reviewer_network_attested:
                        errors.append(
                            "guardian_oversight_event reviewer bindings must carry verifier-network receipts"
                        )
                event_id = str(oversight_event.get("event_id", "")).strip()
                event_ref = f"oversight://{event_id}" if event_id else ""
                event_digest = sha256_text(canonical_json(oversight_event))
                if gate.get("guardian_oversight_event_ref") != event_ref:
                    errors.append("guardian_preseed_gate.guardian_oversight_event_ref mismatch")
                if gate.get("guardian_oversight_event_digest") != event_digest:
                    errors.append("guardian_preseed_gate.guardian_oversight_event_digest mismatch")
                if gate.get("guardian_oversight_event_status") != "satisfied":
                    errors.append("guardian_preseed_gate.guardian_oversight_event_status mismatch")
                if gate.get("reviewer_network_attested") is not reviewer_network_attested:
                    errors.append("guardian_preseed_gate.reviewer_network_attested mismatch")
                if gate.get("reviewer_quorum_required") != reviewer_quorum_required:
                    errors.append("guardian_preseed_gate.reviewer_quorum_required mismatch")
                if gate.get("reviewer_quorum_received") != reviewer_quorum_received:
                    errors.append("guardian_preseed_gate.reviewer_quorum_received mismatch")
        else:
            if oversight_event is not None:
                errors.append("repo-local guardian_preseed_gate must not bind oversight event")
            if gate.get("guardian_oversight_event_ref") != "":
                errors.append("repo-local guardian_oversight_event_ref must be empty")
            if gate.get("guardian_oversight_event_digest") != "":
                errors.append("repo-local guardian_oversight_event_digest must be empty")
            if gate.get("guardian_oversight_event_status") != "not-required":
                errors.append("repo-local guardian_oversight_event_status must be not-required")
            if gate.get("reviewer_network_attested") is not False:
                errors.append("repo-local reviewer_network_attested must be false")
            if gate.get("reviewer_quorum_required") != 0:
                errors.append("repo-local reviewer_quorum_required must be 0")
            if gate.get("reviewer_quorum_received") != 0:
                errors.append("repo-local reviewer_quorum_received must be 0")
        try:
            expected_digest = sha256_text(
                canonical_json(_guardian_preseed_gate_digest_payload(gate))
            )
        except KeyError:
            expected_digest = ""
            errors.append("guardian_preseed_gate digest payload is missing required fields")
        if gate.get("gate_digest") != expected_digest:
            errors.append("guardian_preseed_gate.gate_digest mismatch")
        gate_passed = gate.get("gate_status") == ("pass" if gate_required else "not-required")
        return {
            "ok": not errors,
            "gate_required": gate_required,
            "gate_passed": gate_passed and not errors,
            "oversight_event_satisfied": (
                oversight_event_satisfied if gate_required else True
            ),
            "reviewer_network_attested": (
                reviewer_network_attested if gate_required else True
            ),
            "errors": errors,
        }

    def _task_graph_bundle_strategy(
        self,
        proposal_profile: str,
        requested_optional_coverage_areas: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        requested_optional = self._normalize_requested_optional_coverage_areas(
            proposal_profile,
            requested_optional_coverage_areas,
        )
        requested_optional_key = tuple(requested_optional)
        strategy = None
        if requested_optional_key:
            strategy = (
                YAOYOROZU_OPTIONAL_DISPATCH_BUNDLE_STRATEGY_OVERRIDES.get(proposal_profile, {})
            ).get(requested_optional_key)
            if not isinstance(strategy, Mapping):
                raise ValueError(
                    "unsupported optional dispatch coverage for the selected proposal profile"
                )
        if strategy is None:
            strategy = self._policy.task_graph_bundle_strategies.get(proposal_profile)
        if not isinstance(strategy, Mapping):
            raise ValueError(
                f"unsupported TaskGraph bundle strategy for proposal profile: {proposal_profile}"
            )

        root_bundles = [
            {
                "bundle_role": _non_empty_string(bundle.get("bundle_role"), "bundle_role"),
                "coverage_areas": [
                    _non_empty_string(area, "coverage_area")
                    for area in bundle.get("coverage_areas", [])
                ],
            }
            for bundle in strategy.get("root_bundles", [])
            if isinstance(bundle, Mapping)
        ]
        if len(root_bundles) != 3:
            raise ValueError("TaskGraph bundle strategy must expose exactly 3 root bundles")
        profile_policy = self._proposal_profile_policy(proposal_profile)
        expected_coverage = self._dispatch_coverage_areas(
            proposal_profile,
            requested_optional,
        )
        flat_coverage = [area for bundle in root_bundles for area in bundle["coverage_areas"]]
        if sorted(flat_coverage) != sorted(expected_coverage):
            raise ValueError(
                "TaskGraph bundle strategy must cover the selected dispatch coverage exactly once"
            )
        if len(set(flat_coverage)) != len(flat_coverage):
            raise ValueError("TaskGraph bundle strategy coverage_areas must remain unique")
        return {
            "strategy_id": _non_empty_string(strategy.get("strategy_id"), "strategy_id"),
            "proposal_profile": proposal_profile,
            "requested_optional_coverage_areas": requested_optional,
            "dispatch_coverage_areas": expected_coverage,
            "root_bundle_count": len(root_bundles),
            "max_parallelism": 3,
            "root_bundles": root_bundles,
        }

    def discover_workspace_workers(
        self,
        workspace_roots: Sequence[str | Path],
        *,
        proposal_profile: Optional[str] = None,
        review_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        if len(workspace_roots) < 2:
            raise ValueError("workspace_roots must contain at least two local workspaces")
        profile_id = proposal_profile or self._policy.default_convocation_profile
        profile_policy = self._proposal_profile_policy(profile_id)
        workspace_profile_policy = {
            "proposal_profile": profile_policy["proposal_profile"],
            "workspace_review_policy_id": profile_policy["workspace_review_policy_id"],
            "workspace_review_budget": profile_policy["workspace_review_budget"],
            "required_workspace_coverage_areas": list(
                profile_policy["required_workspace_coverage_areas"]
            ),
            "optional_workspace_coverage_areas": list(
                profile_policy["optional_workspace_coverage_areas"]
            ),
            "task_graph_bundle_strategy_id": profile_policy["task_graph_bundle_strategy_id"],
        }
        budget = review_budget or int(profile_policy["workspace_review_budget"])
        if budget < 2 or budget > self._policy.workspace_review_budget:
            raise ValueError(
                f"review_budget must be between 2 and {self._policy.workspace_review_budget}"
            )

        normalized_roots = [
            Path(_non_empty_string(str(root), "workspace_root")).resolve()
            for root in workspace_roots
        ]
        if len(normalized_roots) > self._policy.workspace_review_budget:
            raise ValueError(
                f"workspace_roots must not exceed {self._policy.workspace_review_budget} explicit roots"
            )
        if len({str(root) for root in normalized_roots}) != len(normalized_roots):
            raise ValueError("workspace_roots must be distinct")

        required_coverage = list(self._policy.worker_target_paths)
        coverage_rules = {
            coverage_area: set(capabilities)
            for coverage_area, capabilities in self._policy.workspace_coverage_capability_rules.items()
        }
        coverage_to_workspace_refs = {coverage_area: [] for coverage_area in required_coverage}
        non_source_coverage_to_workspace_refs = {
            coverage_area: [] for coverage_area in required_coverage
        }
        discovered_workspaces: List[Dict[str, Any]] = []
        for workspace_index, workspace_root in enumerate(normalized_roots, start=1):
            agents_root = workspace_root / "agents"
            if not agents_root.is_dir():
                raise ValueError(f"workspace_root must contain agents/: {workspace_root}")

            role_index: Dict[str, List[str]] = {}
            capability_index: Dict[str, List[str]] = {}
            builder_agent_ids: List[str] = []
            builder_capabilities: set[str] = set()
            agent_count = 0
            for definition_path in sorted(agents_root.rglob("*.yaml")):
                parsed = _parse_agent_definition(definition_path)
                agent_id = str(parsed.get("name") or definition_path.stem).strip()
                role = str(parsed.get("role", "unknown")).strip() or "unknown"
                capabilities = _normalize_string_list(parsed.get("capabilities", []))
                role_index.setdefault(role, []).append(agent_id)
                for capability in capabilities:
                    capability_index.setdefault(capability, []).append(agent_id)
                if role == "builder":
                    builder_agent_ids.append(agent_id)
                    builder_capabilities.update(capabilities)
                agent_count += 1

            supported_coverage_areas = [
                coverage_area
                for coverage_area in required_coverage
                if builder_capabilities.intersection(coverage_rules[coverage_area])
            ]
            if agent_count == 0:
                raise ValueError(f"workspace_root must contain at least one agent definition: {workspace_root}")
            if not builder_agent_ids:
                raise ValueError(f"workspace_root must expose at least one builder agent: {workspace_root}")
            if not supported_coverage_areas:
                raise ValueError(
                    f"workspace_root builders must advertise at least one supported coverage area: {workspace_root}"
                )
            missing_coverage_areas = [
                coverage_area
                for coverage_area in required_coverage
                if coverage_area not in supported_coverage_areas
            ]
            workspace = {
                "workspace_ref": _workspace_ref_from_root(workspace_root),
                "workspace_name": workspace_root.name,
                "workspace_root": str(workspace_root),
                "registry_source_root": str(agents_root),
                "workspace_order": workspace_index,
                "workspace_role": "source" if workspace_index == 1 else "candidate",
                "source_kind": "local-workspace",
                "agent_count": agent_count,
                "builder_agent_ids": builder_agent_ids,
                "role_index": role_index,
                "capability_index": capability_index,
                "supported_coverage_areas": supported_coverage_areas,
                "missing_coverage_areas": missing_coverage_areas,
                "proposal_profiles": (
                    list(self._policy.council_profiles)
                    if builder_agent_ids
                    else []
                ),
                "validation": {
                    "has_agents_root": True,
                    "builder_roles_present": bool(builder_agent_ids),
                    "coverage_summary_machine_readable": sorted(
                        {*supported_coverage_areas, *missing_coverage_areas}
                    )
                    == sorted(required_coverage),
                    "same_host_local": True,
                },
            }
            workspace["validation"]["ok"] = all(workspace["validation"].values())
            workspace["workspace_digest"] = sha256_text(
                canonical_json(_workspace_summary_digest_payload(workspace))
            )
            discovered_workspaces.append(workspace)

        source_workspace = discovered_workspaces[0]
        candidate_workspaces = discovered_workspaces[1:]
        candidate_budget = budget - 1
        if candidate_budget < 1:
            raise ValueError("review_budget must leave room for at least one candidate workspace")
        selected_candidates = candidate_workspaces
        if len(candidate_workspaces) > candidate_budget:
            required_candidate_coverage = set(profile_policy["required_workspace_coverage_areas"])
            optional_candidate_coverage = set(profile_policy["optional_workspace_coverage_areas"])
            best_subset: Optional[Sequence[Dict[str, Any]]] = None
            best_score: Optional[tuple[Any, ...]] = None
            max_subset_size = min(len(candidate_workspaces), candidate_budget)
            for subset_size in range(1, max_subset_size + 1):
                for subset in combinations(candidate_workspaces, subset_size):
                    supported = {
                        coverage_area
                        for workspace in subset
                        for coverage_area in workspace["supported_coverage_areas"]
                    }
                    required_supported = required_candidate_coverage.intersection(supported)
                    optional_supported = optional_candidate_coverage.intersection(supported)
                    score = (
                        len(required_candidate_coverage) - len(required_supported),
                        -len(required_supported),
                        subset_size,
                        -len(optional_supported),
                        tuple(int(workspace["workspace_order"]) for workspace in subset),
                    )
                    if best_score is None or score < best_score:
                        best_score = score
                        best_subset = subset
            if best_subset is None:
                raise ValueError("unable to select candidate workspaces within the bounded review budget")
            selected_candidates = list(best_subset)

        workspaces = [source_workspace, *selected_candidates]
        for workspace in workspaces:
            for coverage_area in workspace["supported_coverage_areas"]:
                coverage_to_workspace_refs[coverage_area].append(workspace["workspace_ref"])
                if workspace["workspace_role"] == "candidate":
                    non_source_coverage_to_workspace_refs[coverage_area].append(
                        workspace["workspace_ref"]
                    )

        supported_coverage_areas = [
            coverage_area
            for coverage_area in required_coverage
            if coverage_to_workspace_refs[coverage_area]
        ]
        missing_coverage_areas = [
            coverage_area
            for coverage_area in required_coverage
            if coverage_area not in supported_coverage_areas
        ]
        non_source_supported_coverage_areas = [
            coverage_area
            for coverage_area in required_coverage
            if non_source_coverage_to_workspace_refs[coverage_area]
        ]
        non_source_missing_coverage_areas = [
            coverage_area
            for coverage_area in required_coverage
            if coverage_area not in non_source_supported_coverage_areas
        ]
        profile_required_coverage = list(profile_policy["required_workspace_coverage_areas"])
        profile_optional_coverage = list(profile_policy["optional_workspace_coverage_areas"])
        profile_supported_coverage_areas = [
            coverage_area
            for coverage_area in profile_required_coverage
            if coverage_area in supported_coverage_areas
        ]
        profile_missing_coverage_areas = [
            coverage_area
            for coverage_area in profile_required_coverage
            if coverage_area not in profile_supported_coverage_areas
        ]
        non_source_profile_supported_coverage_areas = [
            coverage_area
            for coverage_area in profile_required_coverage
            if coverage_area in non_source_supported_coverage_areas
        ]
        non_source_profile_missing_coverage_areas = [
            coverage_area
            for coverage_area in profile_required_coverage
            if coverage_area not in non_source_profile_supported_coverage_areas
        ]
        coverage_summary = {
            "required_coverage_areas": required_coverage,
            "supported_coverage_areas": supported_coverage_areas,
            "missing_coverage_areas": missing_coverage_areas,
            "non_source_supported_coverage_areas": non_source_supported_coverage_areas,
            "non_source_missing_coverage_areas": non_source_missing_coverage_areas,
            "profile_required_coverage_areas": profile_required_coverage,
            "profile_optional_coverage_areas": profile_optional_coverage,
            "profile_supported_coverage_areas": profile_supported_coverage_areas,
            "profile_missing_coverage_areas": profile_missing_coverage_areas,
            "non_source_profile_supported_coverage_areas": non_source_profile_supported_coverage_areas,
            "non_source_profile_missing_coverage_areas": non_source_profile_missing_coverage_areas,
            "coverage_to_workspace_refs": coverage_to_workspace_refs,
            "non_source_coverage_to_workspace_refs": non_source_coverage_to_workspace_refs,
            "workspace_count": len(workspaces),
            "non_source_workspace_count": max(len(workspaces) - 1, 0),
            "builder_workspace_count": sum(1 for workspace in workspaces if workspace["builder_agent_ids"]),
        }
        validation = {
            "review_budget_respected": len(workspaces) <= budget,
            "workspace_roots_distinct": len({workspace["workspace_root"] for workspace in workspaces})
            == len(workspaces),
            "source_workspace_bound": workspaces[0]["workspace_role"] == "source",
            "same_host_local": all(
                workspace["validation"]["same_host_local"] for workspace in workspaces
            ),
            "accepted_workspaces_have_builders": all(
                workspace["validation"]["builder_roles_present"] for workspace in workspaces
            ),
            "coverage_summary_machine_readable": (
                sorted(
                    {
                        *coverage_summary["supported_coverage_areas"],
                        *coverage_summary["missing_coverage_areas"],
                    }
                )
                == sorted(required_coverage)
                and sorted(
                    {
                        *coverage_summary["non_source_supported_coverage_areas"],
                        *coverage_summary["non_source_missing_coverage_areas"],
                    }
                )
                == sorted(required_coverage)
            ),
            "cross_workspace_ready": coverage_summary["non_source_workspace_count"] >= 1,
            "proposal_profile_bound": True,
            "profile_policy_bound": True,
            "cross_workspace_coverage_complete": not non_source_profile_missing_coverage_areas,
        }
        validation["ok"] = all(validation.values())
        discovery = {
            "kind": "yaoyorozu_workspace_discovery",
            "schema_version": "1.0.0",
            "discovery_id": new_id("yaoyorozu-workspace-discovery"),
            "discovered_at": utc_now_iso(),
            "discovery_profile": self._policy.workspace_discovery_profile,
            "discovery_scope": self._policy.workspace_discovery_scope,
            "proposal_profile": profile_id,
            "profile_policy": workspace_profile_policy,
            "source_workspace_ref": workspaces[0]["workspace_ref"],
            "host_ref": self._policy.workspace_discovery_host_ref,
            "review_budget": budget,
            "workspace_roots": [str(workspace_root) for workspace_root in normalized_roots],
            "accepted_workspace_refs": [
                str(workspace["workspace_ref"]) for workspace in workspaces
            ],
            "coverage_summary": coverage_summary,
            "workspaces": workspaces,
            "validation": validation,
        }
        discovery["discovery_digest"] = sha256_text(
            canonical_json(_workspace_discovery_digest_payload(discovery))
        )
        return discovery

    def validate_workspace_discovery(
        self,
        workspace_discovery: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if workspace_discovery.get("kind") != "yaoyorozu_workspace_discovery":
            errors.append("kind must equal yaoyorozu_workspace_discovery")
        if (
            workspace_discovery.get("discovery_profile")
            != self._policy.workspace_discovery_profile
        ):
            errors.append("discovery_profile mismatch")
        if (
            workspace_discovery.get("discovery_scope")
            != self._policy.workspace_discovery_scope
        ):
            errors.append("discovery_scope mismatch")
        if workspace_discovery.get("host_ref") != self._policy.workspace_discovery_host_ref:
            errors.append("host_ref mismatch")

        review_budget = workspace_discovery.get("review_budget")
        if (
            not isinstance(review_budget, int)
            or review_budget < 2
            or review_budget > self._policy.workspace_review_budget
        ):
            errors.append("review_budget must stay within the bounded workspace review budget")
        proposal_profile = workspace_discovery.get("proposal_profile")
        if proposal_profile not in self._policy.council_profiles:
            errors.append("proposal_profile must map to one supported proposal profile")
            expected_profile_policy: Dict[str, Any] = {}
        else:
            full_profile_policy = self._proposal_profile_policy(str(proposal_profile))
            expected_profile_policy = {
                "proposal_profile": full_profile_policy["proposal_profile"],
                "workspace_review_policy_id": full_profile_policy["workspace_review_policy_id"],
                "workspace_review_budget": full_profile_policy["workspace_review_budget"],
                "required_workspace_coverage_areas": list(
                    full_profile_policy["required_workspace_coverage_areas"]
                ),
                "optional_workspace_coverage_areas": list(
                    full_profile_policy["optional_workspace_coverage_areas"]
                ),
                "task_graph_bundle_strategy_id": full_profile_policy["task_graph_bundle_strategy_id"],
            }
        profile_policy = workspace_discovery.get("profile_policy", {})
        if not isinstance(profile_policy, Mapping):
            errors.append("profile_policy must be a mapping")
            profile_policy = {}
        elif expected_profile_policy and dict(profile_policy) != expected_profile_policy:
            errors.append("profile_policy must match the selected proposal profile policy")
        workspace_roots = workspace_discovery.get("workspace_roots", [])
        if not isinstance(workspace_roots, list) or len(workspace_roots) < 2:
            errors.append("workspace_roots must list at least two workspaces")
            workspace_roots = []
        workspaces = workspace_discovery.get("workspaces", [])
        if not isinstance(workspaces, list) or len(workspaces) < 2:
            errors.append("workspaces must contain at least two accepted workspaces")
            workspaces = []

        required_coverage = list(self._policy.worker_target_paths)
        source_workspace_ref = workspace_discovery.get("source_workspace_ref")
        coverage_summary = workspace_discovery.get("coverage_summary", {})
        if not isinstance(coverage_summary, Mapping):
            errors.append("coverage_summary must be a mapping")
            coverage_summary = {}

        previous_order = 0
        builder_workspace_count = 0
        for workspace in workspaces:
            if not isinstance(workspace, Mapping):
                errors.append("workspaces entries must be mappings")
                continue
            if workspace.get("workspace_order", 0) <= previous_order:
                errors.append("workspace_order must remain strictly increasing")
            previous_order = int(workspace.get("workspace_order", 0))
            if workspace.get("workspace_role") == "source" and workspace.get("workspace_ref") != source_workspace_ref:
                errors.append("source workspace ref must match the first accepted workspace")
            if workspace.get("source_kind") != "local-workspace":
                errors.append("workspace source_kind must remain local-workspace")
            if not isinstance(workspace.get("builder_agent_ids"), list) or not workspace.get(
                "builder_agent_ids"
            ):
                errors.append("accepted workspaces must expose builder_agent_ids")
            else:
                builder_workspace_count += 1
            supported_coverage_areas = workspace.get("supported_coverage_areas", [])
            missing_coverage_areas = workspace.get("missing_coverage_areas", [])
            if sorted({*supported_coverage_areas, *missing_coverage_areas}) != sorted(required_coverage):
                errors.append("workspace coverage summary must partition the required coverage areas")
            validation = workspace.get("validation", {})
            if not isinstance(validation, Mapping) or validation.get("ok") is not True:
                errors.append("workspace validation must be ok")

        accepted_workspace_refs = workspace_discovery.get("accepted_workspace_refs", [])
        if accepted_workspace_refs != [
            workspace.get("workspace_ref")
            for workspace in workspaces
            if isinstance(workspace, Mapping)
        ]:
            errors.append("accepted_workspace_refs must preserve accepted workspace order")

        supported_coverage_areas = coverage_summary.get("supported_coverage_areas", [])
        missing_coverage_areas = coverage_summary.get("missing_coverage_areas", [])
        non_source_supported = coverage_summary.get("non_source_supported_coverage_areas", [])
        non_source_missing = coverage_summary.get("non_source_missing_coverage_areas", [])
        profile_required = coverage_summary.get("profile_required_coverage_areas", [])
        profile_optional = coverage_summary.get("profile_optional_coverage_areas", [])
        profile_supported = coverage_summary.get("profile_supported_coverage_areas", [])
        profile_missing = coverage_summary.get("profile_missing_coverage_areas", [])
        non_source_profile_supported = coverage_summary.get(
            "non_source_profile_supported_coverage_areas",
            [],
        )
        non_source_profile_missing = coverage_summary.get(
            "non_source_profile_missing_coverage_areas",
            [],
        )
        if sorted({*supported_coverage_areas, *missing_coverage_areas}) != sorted(required_coverage):
            errors.append("coverage_summary must partition the required coverage areas")
        if sorted({*non_source_supported, *non_source_missing}) != sorted(required_coverage):
            errors.append("non_source coverage summary must partition the required coverage areas")
        if expected_profile_policy:
            expected_required = expected_profile_policy["required_workspace_coverage_areas"]
            expected_optional = expected_profile_policy["optional_workspace_coverage_areas"]
            if profile_required != expected_required:
                errors.append("coverage_summary.profile_required_coverage_areas mismatch")
            if profile_optional != expected_optional:
                errors.append("coverage_summary.profile_optional_coverage_areas mismatch")
            if sorted({*profile_supported, *profile_missing}) != sorted(expected_required):
                errors.append(
                    "coverage_summary profile-supported/profile-missing coverage must partition the required profile coverage"
                )
            if sorted({*non_source_profile_supported, *non_source_profile_missing}) != sorted(expected_required):
                errors.append(
                    "coverage_summary non_source profile-supported/profile-missing coverage must partition the required profile coverage"
                )
        if coverage_summary.get("workspace_count") != len(workspaces):
            errors.append("coverage_summary.workspace_count must match accepted workspaces")
        if coverage_summary.get("non_source_workspace_count") != max(len(workspaces) - 1, 0):
            errors.append(
                "coverage_summary.non_source_workspace_count must match accepted non-source workspaces"
            )
        if coverage_summary.get("builder_workspace_count") != builder_workspace_count:
            errors.append("coverage_summary.builder_workspace_count must match builder-ready workspaces")

        return {
            "ok": not errors,
            "workspace_count": len(workspaces),
            "non_source_workspace_count": max(len(workspaces) - 1, 0),
            "builder_workspace_count": builder_workspace_count,
            "review_budget_respected": len(workspaces) <= int(review_budget or 0),
            "proposal_profile": proposal_profile,
            "cross_workspace_coverage_complete": not non_source_profile_missing,
            "errors": errors,
        }

    def sync_from_agents_directory(self, agents_root: Path) -> Dict[str, Any]:
        repo_root = agents_root.resolve().parent
        self._entries = {}
        source_definition_digests: List[Dict[str, Any]] = []
        for definition_path in sorted(agents_root.resolve().rglob("*.yaml")):
            parsed = _parse_agent_definition(definition_path)
            source_errors = _validate_agent_source_definition(parsed, definition_path, repo_root)
            if source_errors:
                source_ref = str(definition_path.relative_to(repo_root))
                raise ValueError(
                    f"{source_ref} violates {AGENT_SOURCE_DEFINITION_POLICY_ID}: "
                    + "; ".join(source_errors)
                )
            agent_id = str(parsed.get("name") or definition_path.stem).strip()
            source_ref = str(definition_path.relative_to(repo_root))
            source_text = definition_path.read_text(encoding="utf-8")
            source_definition_digests.append(
                {
                    "source_ref": source_ref,
                    "agent_id": agent_id,
                    "role": str(parsed.get("role", "unknown")).strip() or "unknown",
                    "sha256": sha256_text(source_text),
                    "byte_length": len(source_text.encode("utf-8")),
                }
            )
            entry = YaoyorozuRegistryEntry(
                agent_id=agent_id,
                display_name=_pascal_case(agent_id),
                role=str(parsed.get("role", "unknown")).strip() or "unknown",
                source_ref=source_ref,
                capabilities=_normalize_string_list(parsed.get("capabilities", [])),
                trust_floor=float(parsed.get("trust_floor", self._policy.cold_start_score)),
                substrate_requirements=_normalize_string_list(
                    parsed.get("substrate_requirements", [])
                ),
                input_schema_ref=str(parsed.get("input_schema_ref", "")).strip(),
                output_schema_ref=str(parsed.get("output_schema_ref", "")).strip(),
                ethics_constraints=_normalize_string_list(parsed.get("ethics_constraints", [])),
                prompt_or_policy_ref=str(parsed.get("prompt_or_policy_ref", "")).strip(),
                deliberation_scope_refs=_normalize_string_list(
                    parsed.get("deliberation_scope_refs", [])
                ),
                deliberation_policy_ref=str(parsed.get("deliberation_policy_ref", "")).strip(),
                research_domain_refs=_normalize_string_list(
                    parsed.get("research_domain_refs", [])
                ),
                evidence_policy_ref=str(parsed.get("evidence_policy_ref", "")).strip(),
                build_surface_refs=_normalize_string_list(parsed.get("build_surface_refs", [])),
                execution_policy_ref=str(parsed.get("execution_policy_ref", "")).strip(),
                oversight_scope_refs=_normalize_string_list(
                    parsed.get("oversight_scope_refs", [])
                ),
                attestation_policy_ref=str(parsed.get("attestation_policy_ref", "")).strip(),
            )
            self._entries[agent_id] = entry
            self._ensure_trust_seed(entry)

        self._agents_root = agents_root.resolve()
        role_index: Dict[str, List[str]] = {}
        capability_index: Dict[str, List[str]] = {}
        entries: List[Dict[str, Any]] = []
        for agent_id in sorted(self._entries):
            entry = self._entries[agent_id]
            trust_snapshot = self._trust.snapshot(agent_id)
            role_index.setdefault(entry.role, []).append(agent_id)
            for capability in entry.capabilities:
                capability_index.setdefault(capability, []).append(agent_id)
            entries.append(entry.to_dict(trust_snapshot))

        source_manifest_digest = sha256_text(
            canonical_json({"source_definition_digests": source_definition_digests})
        )
        snapshot_body = {
            "policy_id": self._policy.policy_id,
            "source_root": str(self._agents_root.relative_to(repo_root)),
            "source_digest_profile": YAOYOROZU_AGENT_SOURCE_DIGEST_PROFILE,
            "source_definition_count": len(source_definition_digests),
            "source_definition_digests": source_definition_digests,
            "source_manifest_digest": source_manifest_digest,
            "raw_source_payload_stored": False,
            "entry_count": len(entries),
            "role_index": role_index,
            "capability_index": capability_index,
            "selection_ready_counts": {
                "invite_ready": sum(
                    1
                    for entry in entries
                    if entry["trust_snapshot"]["eligibility"]["invite_to_council"]
                ),
                "weighted_vote_ready": sum(
                    1
                    for entry in entries
                    if entry["trust_snapshot"]["eligibility"]["count_for_weighted_vote"]
                ),
                "apply_ready": sum(
                    1
                    for entry in entries
                    if entry["trust_snapshot"]["eligibility"]["apply_to_runtime"]
                ),
                "guardian_ready": sum(
                    1
                    for entry in entries
                    if entry["trust_snapshot"]["eligibility"]["guardian_role"]
                ),
            },
            "entries": entries,
        }
        snapshot_id = new_id("yaoyorozu-registry")
        self._last_snapshot_id = snapshot_id
        return {
            "kind": "yaoyorozu_registry_snapshot",
            "schema_version": "1.0.0",
            "registry_id": snapshot_id,
            "synced_at": utc_now_iso(),
            "registry_digest": sha256_text(canonical_json(snapshot_body)),
            **snapshot_body,
        }

    def build_source_manifest_ledger_binding(
        self,
        registry_snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Build a digest-only receipt for appending the source manifest to ContinuityLedger."""
        source_definition_digests = list(registry_snapshot.get("source_definition_digests", []))
        source_manifest_digest = str(registry_snapshot.get("source_manifest_digest", "")).strip()
        expected_manifest_digest = sha256_text(
            canonical_json({"source_definition_digests": source_definition_digests})
        )
        source_manifest_bound = (
            bool(source_definition_digests)
            and source_manifest_digest == expected_manifest_digest
            and registry_snapshot.get("source_definition_count") == len(source_definition_digests)
            and registry_snapshot.get("raw_source_payload_stored") is False
        )
        binding_id = new_id("yaoyorozu-source-manifest")
        binding: Dict[str, Any] = {
            "kind": "yaoyorozu_source_manifest_ledger_binding",
            "schema_version": "1.0.0",
            "binding_id": binding_id,
            "recorded_at": utc_now_iso(),
            "binding_profile": YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_BINDING_PROFILE,
            "registry_snapshot_ref": f"registry://{registry_snapshot['registry_id']}",
            "registry_digest": str(registry_snapshot.get("registry_digest", "")),
            "policy_id": str(registry_snapshot.get("policy_id", "")),
            "source_root": str(registry_snapshot.get("source_root", "")),
            "source_digest_profile": str(registry_snapshot.get("source_digest_profile", "")),
            "source_definition_count": int(registry_snapshot.get("source_definition_count", 0)),
            "source_definition_digests": source_definition_digests,
            "source_manifest_digest": source_manifest_digest,
            "continuity_event_ref": f"ledger://yaoyorozu/source-manifest/{binding_id}",
            "continuity_event_digest": "",
            "continuity_ledger_category": YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_CATEGORY,
            "continuity_ledger_event_type": YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_EVENT_TYPE,
            "continuity_ledger_signature_roles": list(
                YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_SIGNATURE_ROLES
            ),
            "continuity_ledger_appended": False,
            "continuity_ledger_entry_ref": None,
            "continuity_ledger_entry_hash": None,
            "continuity_ledger_payload_ref": None,
            "raw_source_payload_stored": False,
            "raw_registry_payload_stored": False,
            "raw_continuity_event_payload_stored": False,
            "validation": {
                "ok": False,
                "source_manifest_bound": source_manifest_bound,
                "source_manifest_digest_bound": source_manifest_bound,
                "registry_digest_bound": bool(registry_snapshot.get("registry_digest")),
                "continuity_event_digest_bound": False,
                "continuity_ledger_entry_appended": False,
                "continuity_ledger_entry_digest_bound": False,
                "continuity_ledger_payload_ref_bound": False,
                "continuity_ledger_signature_roles_bound": False,
                "raw_source_payload_stored": False,
                "raw_registry_payload_stored": False,
                "raw_continuity_event_payload_stored": False,
            },
        }
        binding["continuity_event_digest"] = sha256_text(
            canonical_json(_source_manifest_continuity_payload(binding))
        )
        binding["validation"]["continuity_event_digest_bound"] = bool(
            binding["continuity_event_digest"]
        )
        return binding

    def source_manifest_continuity_event_payload(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Return the digest-only source manifest payload for ContinuityLedger append."""
        return _source_manifest_continuity_payload(binding)

    def bind_source_manifest_ledger_entry(
        self,
        binding: Dict[str, Any],
        ledger_entry: Any,
    ) -> Dict[str, Any]:
        """Attach a real ContinuityLedger entry to one source manifest binding receipt."""
        expected_payload = self.source_manifest_continuity_event_payload(binding)
        event_digest_bound = str(binding.get("continuity_event_digest", "")) == sha256_text(
            canonical_json(expected_payload)
        )
        expected_payload_ref = f"cas://sha256/{sha256_text(canonical_json(expected_payload))}"
        expected_roles = list(YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_SIGNATURE_ROLES)
        observed_roles = list(getattr(ledger_entry, "signatures", {}).keys())
        entry_digest_bound = (
            getattr(ledger_entry, "payload", None) == expected_payload
            and getattr(ledger_entry, "category", None)
            == YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_CATEGORY
            and getattr(ledger_entry, "event_type", None)
            == YAOYOROZU_AGENT_SOURCE_MANIFEST_LEDGER_EVENT_TYPE
            and getattr(ledger_entry, "layer", None) == "L4"
        )
        payload_ref_bound = getattr(ledger_entry, "payload_ref", None) == expected_payload_ref
        signature_roles_bound = observed_roles == expected_roles

        binding["continuity_ledger_appended"] = True
        binding["continuity_ledger_entry_ref"] = f"ledger://continuity-ledger/{ledger_entry.entry_id}"
        binding["continuity_ledger_entry_hash"] = ledger_entry.entry_hash
        binding["continuity_ledger_payload_ref"] = ledger_entry.payload_ref
        binding["validation"]["continuity_ledger_entry_appended"] = True
        binding["validation"]["continuity_event_digest_bound"] = event_digest_bound
        binding["validation"]["continuity_ledger_entry_digest_bound"] = entry_digest_bound
        binding["validation"]["continuity_ledger_payload_ref_bound"] = payload_ref_bound
        binding["validation"]["continuity_ledger_signature_roles_bound"] = signature_roles_bound
        source_definition_digest_set_digest = sha256_text(
            canonical_json({"source_definition_digests": binding["source_definition_digests"]})
        )
        signature_digests = {
            role: sha256_text(str(getattr(ledger_entry, "signatures", {}).get(role, "")))
            for role in expected_roles
        }
        verifier_key_refs = {
            role: f"key://continuity-ledger/{role}/reference-verifier/v1"
            for role in expected_roles
        }
        public_verification_ready = (
            binding["validation"]["source_manifest_bound"]
            and binding["validation"]["registry_digest_bound"]
            and event_digest_bound
            and entry_digest_bound
            and payload_ref_bound
            and signature_roles_bound
            and all(signature_digests.values())
        )
        public_bundle_core = _source_manifest_public_verification_bundle_core(
            binding=binding,
            ledger_entry=ledger_entry,
            source_definition_digest_set_digest=source_definition_digest_set_digest,
            signature_digests=signature_digests,
            verifier_key_refs=verifier_key_refs,
            public_verification_ready=public_verification_ready,
        )
        public_bundle = {
            **public_bundle_core,
            "bundle_digest": sha256_text(canonical_json(public_bundle_core)),
        }
        public_bundle_bound = (
            public_bundle["public_verification_ready"] is True
            and public_bundle["source_definition_count"] == binding["source_definition_count"]
            and public_bundle["source_definition_digests"] == binding["source_definition_digests"]
            and public_bundle["source_manifest_digest"] == binding["source_manifest_digest"]
            and public_bundle["source_definition_digest_set_digest"]
            == source_definition_digest_set_digest
            and public_bundle["continuity_ledger_entry_ref"]
            == binding["continuity_ledger_entry_ref"]
            and public_bundle["continuity_ledger_entry_hash"]
            == binding["continuity_ledger_entry_hash"]
            and public_bundle["continuity_ledger_payload_ref"]
            == binding["continuity_ledger_payload_ref"]
            and public_bundle["continuity_ledger_signature_roles"] == expected_roles
            and public_bundle["signature_digests"] == signature_digests
            and public_bundle["verifier_key_refs"] == verifier_key_refs
            and public_bundle["raw_source_payload_exposed"] is False
            and public_bundle["raw_registry_payload_exposed"] is False
            and public_bundle["raw_continuity_event_payload_exposed"] is False
            and public_bundle["raw_signature_payload_exposed"] is False
        )
        public_bundle_digest_bound = (
            public_bundle["bundle_digest"] == sha256_text(canonical_json(public_bundle_core))
        )
        binding["public_verification_bundle_ref"] = public_bundle["bundle_ref"]
        binding["public_verification_bundle_digest"] = public_bundle["bundle_digest"]
        binding["public_verification_bundle"] = public_bundle
        binding["validation"]["public_verification_bundle_bound"] = public_bundle_bound
        binding["validation"]["public_verification_bundle_digest_bound"] = (
            public_bundle_digest_bound
        )
        binding["validation"]["raw_signature_payload_exposed"] = False
        binding["validation"]["ok"] = (
            binding["validation"]["source_manifest_bound"]
            and binding["validation"]["registry_digest_bound"]
            and event_digest_bound
            and entry_digest_bound
            and payload_ref_bound
            and signature_roles_bound
            and public_bundle_bound
            and public_bundle_digest_bound
            and binding["raw_source_payload_stored"] is False
            and binding["raw_registry_payload_stored"] is False
            and binding["raw_continuity_event_payload_stored"] is False
            and public_bundle["raw_signature_payload_exposed"] is False
        )
        return binding

    def build_research_evidence_exchange(
        self,
        registry_snapshot: Mapping[str, Any],
        *,
        requested_by_ref: str,
        preferred_researcher_agent_id: str = "neuroscience-scout",
    ) -> Dict[str, Any]:
        """Build one advisory-only researcher request/report exchange receipt."""
        if self._agents_root is None:
            raise ValueError("registry must be synced before binding research evidence")
        researcher_entries = [
            entry
            for entry in registry_snapshot.get("entries", [])
            if isinstance(entry, Mapping) and entry.get("role") == "researcher"
        ]
        if not researcher_entries:
            raise ValueError("registry snapshot must include at least one researcher entry")
        selected_entry = next(
            (
                entry
                for entry in researcher_entries
                if entry.get("agent_id") == preferred_researcher_agent_id
            ),
            researcher_entries[0],
        )
        agent_id = _non_empty_string(selected_entry.get("agent_id"), "researcher_agent_id")
        research_domain_refs = [
            _non_empty_string(ref, "research_domain_ref")
            for ref in selected_entry.get("research_domain_refs", [])
        ]
        if not research_domain_refs:
            raise ValueError("researcher entry must expose research_domain_refs")
        evidence_policy_ref = _non_empty_string(
            selected_entry.get("evidence_policy_ref"),
            "evidence_policy_ref",
        )
        evidence_ref = research_domain_refs[0]
        repo_root = self._agents_root.parent
        evidence_path = repo_root / evidence_ref
        if not evidence_path.is_file():
            raise ValueError(f"research evidence ref must resolve to a repo file: {evidence_ref}")
        source_digests = {
            str(source.get("source_ref", "")): str(source.get("sha256", ""))
            for source in registry_snapshot.get("source_definition_digests", [])
            if isinstance(source, Mapping)
        }
        source_ref = _non_empty_string(selected_entry.get("source_ref"), "researcher_source_ref")
        researcher_source_digest = source_digests.get(source_ref, "")
        if not researcher_source_digest:
            source_path = repo_root / source_ref
            if source_path.is_file():
                researcher_source_digest = sha256_text(source_path.read_text(encoding="utf-8"))
        request_id = new_id("research-evidence-request")
        request_ref = f"research-evidence-request://{request_id}"
        request = {
            "kind": "research_evidence_request",
            "schema_version": "1.0.0",
            "request_id": request_id,
            "requested_by_ref": _non_empty_string(requested_by_ref, "requested_by_ref"),
            "research_domain_refs": list(research_domain_refs),
            "evidence_policy_ref": evidence_policy_ref,
            "question": (
                "Summarize implementation evidence ceilings and competing explanations "
                f"for {evidence_ref} without authorizing a Council resolution."
            ),
            "seed_evidence_refs": [evidence_ref],
            "requested_output_sections": [
                "summary",
                "source_refs",
                "competing_explanations",
                "uncertainty",
                "claim_ceiling",
                "design_implications",
            ],
            "constraints": {
                "allowed_source_classes": ["repo-local-doc"],
                "forbidden_actions": [
                    "council-resolution",
                    "runtime-write",
                    "raw-payload-retention",
                    "clinical-or-legal-authority-claim",
                ],
                "raw_source_payload_allowed": False,
                "decision_authority_allowed": False,
            },
        }
        request_digest = sha256_text(
            canonical_json(_research_evidence_request_digest_payload(request))
        )
        report_core = {
            "kind": "research_evidence_report",
            "schema_version": "1.0.0",
            "report_id": new_id("research-evidence-report"),
            "request_ref": request_ref,
            "researcher_agent_id": agent_id,
            "research_domain_refs": list(research_domain_refs),
            "evidence_policy_ref": evidence_policy_ref,
            "evidence_items": [
                {
                    "evidence_ref": evidence_ref,
                    "evidence_digest": sha256_text(
                        evidence_path.read_text(encoding="utf-8")
                    ),
                    "source_class": "repo-local-doc",
                    "claim_scope": "constrains",
                }
            ],
            "claim_ceiling": "implementation-advisory",
            "uncertainty_notes": [
                "Repo-local research-frontier notes constrain implementation wording but do not authorize runtime writes.",
                "Competing explanations remain reviewer-facing context rather than Council decisions.",
            ],
            "advisory_design_implications": [
                {
                    "implication_id": new_id("research-implication"),
                    "summary": (
                        "Keep Yaoyorozu researcher output as advisory evidence with "
                        "digest-bound source refs before Council synthesis."
                    ),
                    "target_ref": evidence_ref,
                    "authority_level": "advisory-only",
                }
            ],
            "raw_research_payload_stored": False,
            "decision_authority_claimed": False,
        }
        report = {
            **report_core,
            "report_digest": sha256_text(
                canonical_json(_research_evidence_report_digest_payload(report_core))
            ),
        }
        exchange_id = new_id("yaoyorozu-research-evidence-exchange")
        exchange: Dict[str, Any] = {
            "kind": "yaoyorozu_research_evidence_exchange",
            "schema_version": "1.0.0",
            "exchange_id": exchange_id,
            "exchange_ref": f"research-evidence-exchange://{exchange_id}",
            "recorded_at": utc_now_iso(),
            "profile_id": YAOYOROZU_RESEARCH_EVIDENCE_EXCHANGE_PROFILE,
            "registry_snapshot_ref": f"registry://{registry_snapshot['registry_id']}",
            "registry_digest": str(registry_snapshot.get("registry_digest", "")),
            "source_manifest_digest": str(
                registry_snapshot.get("source_manifest_digest", "")
            ),
            "researcher_agent_id": agent_id,
            "researcher_source_ref": source_ref,
            "researcher_source_digest": researcher_source_digest,
            "research_domain_refs": list(research_domain_refs),
            "evidence_policy_ref": evidence_policy_ref,
            "input_schema_ref": str(selected_entry.get("input_schema_ref", "")),
            "output_schema_ref": str(selected_entry.get("output_schema_ref", "")),
            "requested_by_ref": request["requested_by_ref"],
            "request_ref": request_ref,
            "request_digest": request_digest,
            "report_ref": f"research-evidence-report://{report['report_id']}",
            "report_digest": report["report_digest"],
            "evidence_refs": [evidence_ref],
            "evidence_ref_count": 1,
            "claim_ceiling": report["claim_ceiling"],
            "advisory_only": True,
            "raw_research_payload_stored": False,
            "decision_authority_claimed": False,
            "request": request,
            "report": report,
            "continuity_event_ref": f"ledger://yaoyorozu/research-evidence/{exchange_id}",
            "continuity_event_digest": "",
            "continuity_ledger_category": YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_CATEGORY,
            "continuity_ledger_event_type": YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_EVENT_TYPE,
            "continuity_ledger_signature_roles": list(
                YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES
            ),
            "continuity_ledger_appended": False,
            "continuity_ledger_entry_ref": None,
            "continuity_ledger_entry_hash": None,
            "continuity_ledger_payload_ref": None,
        }
        exchange["continuity_event_digest"] = sha256_text(
            canonical_json(_research_evidence_exchange_continuity_payload(exchange))
        )
        exchange["exchange_digest"] = sha256_text(
            canonical_json(_research_evidence_exchange_digest_payload(exchange))
        )
        exchange["validation"] = self.validate_research_evidence_exchange(
            exchange,
            registry_snapshot,
        )
        return exchange

    def research_evidence_exchange_continuity_event_payload(
        self,
        exchange: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Return the digest-only researcher exchange payload for ContinuityLedger append."""
        return _research_evidence_exchange_continuity_payload(exchange)

    def bind_research_evidence_exchange_ledger_entry(
        self,
        exchange: Dict[str, Any],
        ledger_entry: Any,
        registry_snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Attach a real ContinuityLedger entry to one researcher exchange receipt."""
        expected_payload = self.research_evidence_exchange_continuity_event_payload(exchange)
        expected_payload_digest = sha256_text(canonical_json(expected_payload))
        expected_payload_ref = f"cas://sha256/{expected_payload_digest}"
        expected_roles = list(YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES)
        observed_roles = list(getattr(ledger_entry, "signatures", {}).keys())
        entry_bound = (
            getattr(ledger_entry, "payload", None) == expected_payload
            and getattr(ledger_entry, "category", None)
            == YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_CATEGORY
            and getattr(ledger_entry, "event_type", None)
            == YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_EVENT_TYPE
            and getattr(ledger_entry, "layer", None) == "L4"
        )
        payload_ref_bound = getattr(ledger_entry, "payload_ref", None) == expected_payload_ref
        signature_roles_bound = observed_roles == expected_roles
        exchange["continuity_event_digest"] = expected_payload_digest
        exchange["continuity_ledger_appended"] = bool(
            entry_bound and payload_ref_bound and signature_roles_bound
        )
        exchange["continuity_ledger_entry_ref"] = (
            f"ledger://continuity-ledger/{ledger_entry.entry_id}"
        )
        exchange["continuity_ledger_entry_hash"] = ledger_entry.entry_hash
        exchange["continuity_ledger_payload_ref"] = ledger_entry.payload_ref
        exchange["exchange_digest"] = sha256_text(
            canonical_json(_research_evidence_exchange_digest_payload(exchange))
        )
        exchange["validation"] = self.validate_research_evidence_exchange(
            exchange,
            registry_snapshot,
        )
        return exchange

    def validate_research_evidence_exchange(
        self,
        exchange: Mapping[str, Any],
        registry_snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Validate one digest-bound researcher request/report exchange receipt."""
        errors: List[str] = []
        entries = {
            str(entry.get("agent_id", "")): entry
            for entry in registry_snapshot.get("entries", [])
            if isinstance(entry, Mapping)
        }
        researcher_agent_id = str(exchange.get("researcher_agent_id", ""))
        researcher_entry = entries.get(researcher_agent_id)
        researcher_entry_bound = (
            isinstance(researcher_entry, Mapping)
            and researcher_entry.get("role") == "researcher"
            and researcher_entry.get("source_ref") == exchange.get("researcher_source_ref")
            and researcher_entry.get("research_domain_refs") == exchange.get("research_domain_refs")
            and researcher_entry.get("evidence_policy_ref") == exchange.get("evidence_policy_ref")
            and researcher_entry.get("input_schema_ref")
            == AGENT_SOURCE_RESEARCHER_INPUT_SCHEMA_REF
            and researcher_entry.get("output_schema_ref")
            == AGENT_SOURCE_RESEARCHER_OUTPUT_SCHEMA_REF
        )
        if not researcher_entry_bound:
            errors.append("researcher entry must bind role-specific evidence scope and schemas")

        source_digests = {
            str(source.get("source_ref", "")): str(source.get("sha256", ""))
            for source in registry_snapshot.get("source_definition_digests", [])
            if isinstance(source, Mapping)
        }
        researcher_source_digest_bound = (
            bool(exchange.get("researcher_source_digest"))
            and source_digests.get(str(exchange.get("researcher_source_ref", "")))
            == exchange.get("researcher_source_digest")
        )
        if not researcher_source_digest_bound:
            errors.append("researcher source digest must bind the registry source manifest")

        request = exchange.get("request", {})
        report = exchange.get("report", {})
        request_ref = str(exchange.get("request_ref", ""))
        report_ref = str(exchange.get("report_ref", ""))
        request_digest_bound = False
        report_digest_bound = False
        exchange_digest_bound = False
        continuity_event_digest_bound = False
        try:
            request_digest_bound = (
                exchange.get("request_digest")
                == sha256_text(
                    canonical_json(_research_evidence_request_digest_payload(request))
                )
            )
        except (KeyError, TypeError):
            errors.append("research evidence request digest payload is incomplete")
        if not request_digest_bound:
            errors.append("request_digest must bind research evidence request")
        try:
            report_digest_bound = (
                report.get("report_digest")
                == exchange.get("report_digest")
                == sha256_text(
                    canonical_json(_research_evidence_report_digest_payload(report))
                )
            )
        except (KeyError, TypeError):
            errors.append("research evidence report digest payload is incomplete")
        if not report_digest_bound:
            errors.append("report_digest must bind research evidence report")
        try:
            continuity_event_digest_bound = (
                exchange.get("continuity_event_digest")
                == sha256_text(
                    canonical_json(_research_evidence_exchange_continuity_payload(exchange))
                )
            )
        except (KeyError, TypeError):
            errors.append("research evidence continuity payload is incomplete")
        if not continuity_event_digest_bound:
            errors.append("continuity_event_digest must bind exchange evidence")
        try:
            exchange_digest_bound = (
                exchange.get("exchange_digest")
                == sha256_text(
                    canonical_json(_research_evidence_exchange_digest_payload(exchange))
                )
            )
        except (KeyError, TypeError):
            errors.append("research evidence exchange digest payload is incomplete")
        if not exchange_digest_bound:
            errors.append("exchange_digest must bind exchange receipt")

        request_constraints = request.get("constraints", {}) if isinstance(request, Mapping) else {}
        request_forbids_authority = (
            request.get("request_id") and request_ref == f"research-evidence-request://{request['request_id']}"
            and request.get("requested_by_ref") == exchange.get("requested_by_ref")
            and request.get("research_domain_refs") == exchange.get("research_domain_refs")
            and request.get("evidence_policy_ref") == exchange.get("evidence_policy_ref")
            and isinstance(request_constraints, Mapping)
            and request_constraints.get("raw_source_payload_allowed") is False
            and request_constraints.get("decision_authority_allowed") is False
            and {
                "council-resolution",
                "runtime-write",
                "raw-payload-retention",
                "clinical-or-legal-authority-claim",
            }.issubset(set(request_constraints.get("forbidden_actions", [])))
        )
        if not request_forbids_authority:
            errors.append("research request must forbid authority and raw payload retention")

        evidence_items = report.get("evidence_items", []) if isinstance(report, Mapping) else []
        evidence_item_refs = [
            str(item.get("evidence_ref", ""))
            for item in evidence_items
            if isinstance(item, Mapping)
        ]
        evidence_refs_bound = (
            report.get("request_ref") == request_ref
            and report_ref == f"research-evidence-report://{report.get('report_id')}"
            and report.get("researcher_agent_id") == researcher_agent_id
            and report.get("research_domain_refs") == exchange.get("research_domain_refs")
            and report.get("evidence_policy_ref") == exchange.get("evidence_policy_ref")
            and exchange.get("evidence_refs") == evidence_item_refs
            and exchange.get("evidence_ref_count") == len(evidence_item_refs)
            and bool(evidence_item_refs)
        )
        repo_root = self._agents_root.parent if self._agents_root is not None else Path(".")
        evidence_digests_bound = True
        for item in evidence_items:
            if not isinstance(item, Mapping):
                evidence_digests_bound = False
                continue
            evidence_ref = str(item.get("evidence_ref", ""))
            evidence_path = repo_root / evidence_ref
            if not evidence_path.is_file():
                evidence_digests_bound = False
                continue
            if item.get("evidence_digest") != sha256_text(
                evidence_path.read_text(encoding="utf-8")
            ):
                evidence_digests_bound = False
        if not evidence_refs_bound or not evidence_digests_bound:
            errors.append("evidence refs and digests must bind repo-local evidence items")

        advisory_only = (
            exchange.get("claim_ceiling") == "implementation-advisory"
            and exchange.get("advisory_only") is True
            and report.get("claim_ceiling") == "implementation-advisory"
            and all(
                isinstance(item, Mapping)
                and item.get("authority_level") == "advisory-only"
                for item in report.get("advisory_design_implications", [])
            )
        )
        if not advisory_only:
            errors.append("research evidence report must remain advisory-only")
        raw_payload_clean = (
            exchange.get("raw_research_payload_stored") is False
            and report.get("raw_research_payload_stored") is False
        )
        decision_authority_clean = (
            exchange.get("decision_authority_claimed") is False
            and report.get("decision_authority_claimed") is False
        )
        if not raw_payload_clean:
            errors.append("raw research payload must not be stored")
        if not decision_authority_clean:
            errors.append("researcher must not claim decision authority")

        expected_roles = list(YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES)
        continuity_ledger_signature_roles_bound = (
            exchange.get("continuity_ledger_signature_roles") == expected_roles
        )
        continuity_ledger_entry_appended = exchange.get("continuity_ledger_appended") is True
        continuity_ledger_entry_digest_bound = (
            continuity_ledger_entry_appended
            and str(exchange.get("continuity_ledger_entry_ref", "")).startswith(
                "ledger://continuity-ledger/"
            )
            and bool(exchange.get("continuity_ledger_entry_hash"))
        )
        continuity_ledger_payload_ref_bound = (
            continuity_ledger_entry_appended
            and exchange.get("continuity_ledger_payload_ref")
            == f"cas://sha256/{exchange.get('continuity_event_digest')}"
        )
        if not continuity_ledger_signature_roles_bound:
            errors.append("research evidence ledger signature roles must be council+guardian")
        if not continuity_ledger_entry_appended:
            errors.append("research evidence exchange must be appended to ContinuityLedger")
        if not continuity_ledger_entry_digest_bound:
            errors.append("continuity ledger entry ref/hash must be bound")
        if not continuity_ledger_payload_ref_bound:
            errors.append("continuity ledger payload ref must bind event digest")

        return {
            "ok": not errors,
            "researcher_entry_bound": researcher_entry_bound,
            "researcher_source_digest_bound": researcher_source_digest_bound,
            "request_digest_bound": request_digest_bound,
            "report_digest_bound": report_digest_bound,
            "exchange_digest_bound": exchange_digest_bound,
            "continuity_event_digest_bound": continuity_event_digest_bound,
            "evidence_refs_bound": evidence_refs_bound,
            "evidence_digests_bound": evidence_digests_bound,
            "request_forbids_authority": bool(request_forbids_authority),
            "advisory_only": advisory_only,
            "raw_research_payload_stored": not raw_payload_clean,
            "decision_authority_claimed": not decision_authority_clean,
            "continuity_ledger_entry_appended": continuity_ledger_entry_appended,
            "continuity_ledger_entry_digest_bound": continuity_ledger_entry_digest_bound,
            "continuity_ledger_payload_ref_bound": continuity_ledger_payload_ref_bound,
            "continuity_ledger_signature_roles_bound": (
                continuity_ledger_signature_roles_bound
            ),
            "errors": errors,
        }

    def build_research_evidence_exchanges(
        self,
        registry_snapshot: Mapping[str, Any],
        *,
        requested_by_ref: str,
        preferred_researcher_agent_ids: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Build a deterministic multi-researcher exchange set for Council synthesis."""
        researcher_entries = [
            entry
            for entry in registry_snapshot.get("entries", [])
            if isinstance(entry, Mapping) and entry.get("role") == "researcher"
        ]
        if len(researcher_entries) < 2:
            raise ValueError("at least two researcher entries are required for synthesis")
        available_ids = [
            _non_empty_string(entry.get("agent_id"), "researcher_agent_id")
            for entry in researcher_entries
        ]
        preferred_ids = list(
            preferred_researcher_agent_ids
            or ("neuroscience-scout", "legal-scholar")
        )
        selected_ids = _ordered_unique(
            [agent_id for agent_id in preferred_ids if agent_id in available_ids]
        )
        for agent_id in available_ids:
            if len(selected_ids) >= 2:
                break
            if agent_id not in selected_ids:
                selected_ids.append(agent_id)
        if len(selected_ids) < 2:
            raise ValueError("research evidence synthesis requires two distinct researchers")

        return [
            self.build_research_evidence_exchange(
                registry_snapshot,
                requested_by_ref=requested_by_ref,
                preferred_researcher_agent_id=agent_id,
            )
            for agent_id in selected_ids
        ]

    def build_research_evidence_synthesis(
        self,
        exchange_receipts: Sequence[Mapping[str, Any]],
        registry_snapshot: Mapping[str, Any],
        *,
        council_session_ref: str,
    ) -> Dict[str, Any]:
        """Synthesize multiple advisory researcher exchanges for Council deliberation."""
        exchanges = [dict(exchange) for exchange in exchange_receipts]
        if len(exchanges) < 2:
            raise ValueError("research evidence synthesis requires at least two exchanges")
        exchange_refs = [_non_empty_string(exchange.get("exchange_ref"), "exchange_ref") for exchange in exchanges]
        exchange_digests = [
            _non_empty_string(exchange.get("exchange_digest"), "exchange_digest")
            for exchange in exchanges
        ]
        researcher_agent_ids = _ordered_unique(
            [
                _non_empty_string(exchange.get("researcher_agent_id"), "researcher_agent_id")
                for exchange in exchanges
            ]
        )
        research_domain_refs = _ordered_unique(
            [
                str(ref)
                for exchange in exchanges
                for ref in exchange.get("research_domain_refs", [])
            ]
        )
        evidence_refs = _ordered_unique(
            [
                str(ref)
                for exchange in exchanges
                for ref in exchange.get("evidence_refs", [])
            ]
        )
        evidence_digest_set: List[Dict[str, Any]] = []
        for exchange in exchanges:
            report = exchange.get("report", {})
            for item in report.get("evidence_items", []) if isinstance(report, Mapping) else []:
                if not isinstance(item, Mapping):
                    continue
                evidence_digest_set.append(
                    {
                        "exchange_ref": exchange["exchange_ref"],
                        "researcher_agent_id": exchange["researcher_agent_id"],
                        "evidence_ref": item["evidence_ref"],
                        "evidence_digest": item["evidence_digest"],
                        "claim_scope": item["claim_scope"],
                    }
                )
        advisory_design_implications = [
            {
                "implication_id": new_id("research-implication"),
                "summary": (
                    "Treat multi-researcher Yaoyorozu evidence as Council input only; "
                    "do not grant runtime write or decision authority."
                ),
                "target_ref": "docs/07-reference-implementation/README.md",
                "authority_level": "advisory-only",
                "source_exchange_refs": list(exchange_refs),
            }
        ]
        synthesis_id = new_id("yaoyorozu-research-evidence-synthesis")
        synthesis: Dict[str, Any] = {
            "kind": "yaoyorozu_research_evidence_synthesis",
            "schema_version": "1.0.0",
            "synthesis_id": synthesis_id,
            "synthesis_ref": f"research-evidence-synthesis://{synthesis_id}",
            "recorded_at": utc_now_iso(),
            "profile_id": YAOYOROZU_RESEARCH_EVIDENCE_SYNTHESIS_PROFILE,
            "registry_snapshot_ref": f"registry://{registry_snapshot['registry_id']}",
            "registry_digest": str(registry_snapshot.get("registry_digest", "")),
            "source_manifest_digest": str(
                registry_snapshot.get("source_manifest_digest", "")
            ),
            "council_session_ref": _non_empty_string(council_session_ref, "council_session_ref"),
            "exchange_refs": exchange_refs,
            "exchange_digests": exchange_digests,
            "exchange_count": len(exchanges),
            "researcher_agent_ids": researcher_agent_ids,
            "research_domain_refs": research_domain_refs,
            "evidence_refs": evidence_refs,
            "evidence_digest_set": evidence_digest_set,
            "claim_ceiling": "implementation-advisory",
            "synthesis_summary": (
                "Multiple Yaoyorozu researcher exchanges were reduced to digest-only, "
                "advisory Council input with no raw research payload retention."
            ),
            "advisory_design_implications": advisory_design_implications,
            "raw_exchange_payload_stored": False,
            "raw_research_payload_stored": False,
            "decision_authority_claimed": False,
            "continuity_event_ref": f"ledger://yaoyorozu/research-evidence/{synthesis_id}",
            "continuity_event_digest": "",
            "continuity_ledger_category": YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_CATEGORY,
            "continuity_ledger_event_type": (
                YAOYOROZU_RESEARCH_EVIDENCE_SYNTHESIS_LEDGER_EVENT_TYPE
            ),
            "continuity_ledger_signature_roles": list(
                YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES
            ),
            "continuity_ledger_appended": False,
            "continuity_ledger_entry_ref": None,
            "continuity_ledger_entry_hash": None,
            "continuity_ledger_payload_ref": None,
            "exchange_receipts": exchanges,
        }
        synthesis["continuity_event_digest"] = sha256_text(
            canonical_json(_research_evidence_synthesis_continuity_payload(synthesis))
        )
        synthesis["synthesis_digest"] = sha256_text(
            canonical_json(_research_evidence_synthesis_digest_payload(synthesis))
        )
        synthesis["validation"] = self.validate_research_evidence_synthesis(
            synthesis,
            registry_snapshot,
        )
        return synthesis

    def research_evidence_synthesis_continuity_event_payload(
        self,
        synthesis: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Return the digest-only multi-researcher synthesis payload for ledger append."""
        return _research_evidence_synthesis_continuity_payload(synthesis)

    def bind_research_evidence_synthesis_ledger_entry(
        self,
        synthesis: Dict[str, Any],
        ledger_entry: Any,
        registry_snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Attach a real ContinuityLedger entry to one synthesis receipt."""
        expected_payload = self.research_evidence_synthesis_continuity_event_payload(
            synthesis
        )
        expected_payload_digest = sha256_text(canonical_json(expected_payload))
        expected_payload_ref = f"cas://sha256/{expected_payload_digest}"
        expected_roles = list(YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES)
        observed_roles = list(getattr(ledger_entry, "signatures", {}).keys())
        entry_bound = (
            getattr(ledger_entry, "payload", None) == expected_payload
            and getattr(ledger_entry, "category", None)
            == YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_CATEGORY
            and getattr(ledger_entry, "event_type", None)
            == YAOYOROZU_RESEARCH_EVIDENCE_SYNTHESIS_LEDGER_EVENT_TYPE
            and getattr(ledger_entry, "layer", None) == "L4"
        )
        payload_ref_bound = getattr(ledger_entry, "payload_ref", None) == expected_payload_ref
        signature_roles_bound = observed_roles == expected_roles
        synthesis["continuity_event_digest"] = expected_payload_digest
        synthesis["continuity_ledger_appended"] = bool(
            entry_bound and payload_ref_bound and signature_roles_bound
        )
        synthesis["continuity_ledger_entry_ref"] = (
            f"ledger://continuity-ledger/{ledger_entry.entry_id}"
        )
        synthesis["continuity_ledger_entry_hash"] = ledger_entry.entry_hash
        synthesis["continuity_ledger_payload_ref"] = ledger_entry.payload_ref
        synthesis["synthesis_digest"] = sha256_text(
            canonical_json(_research_evidence_synthesis_digest_payload(synthesis))
        )
        synthesis["validation"] = self.validate_research_evidence_synthesis(
            synthesis,
            registry_snapshot,
        )
        return synthesis

    def validate_research_evidence_synthesis(
        self,
        synthesis: Mapping[str, Any],
        registry_snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Validate a multi-researcher digest-only synthesis receipt."""
        errors: List[str] = []
        exchanges = [
            exchange
            for exchange in synthesis.get("exchange_receipts", [])
            if isinstance(exchange, Mapping)
        ]
        exchange_refs = [str(exchange.get("exchange_ref", "")) for exchange in exchanges]
        exchange_digests = [
            str(exchange.get("exchange_digest", "")) for exchange in exchanges
        ]
        researcher_agent_ids = _ordered_unique(
            [str(exchange.get("researcher_agent_id", "")) for exchange in exchanges]
        )
        evidence_digest_set: List[Dict[str, Any]] = []
        for exchange in exchanges:
            report = exchange.get("report", {})
            if not isinstance(report, Mapping):
                continue
            for item in report.get("evidence_items", []):
                if not isinstance(item, Mapping):
                    continue
                evidence_digest_set.append(
                    {
                        "exchange_ref": exchange.get("exchange_ref"),
                        "researcher_agent_id": exchange.get("researcher_agent_id"),
                        "evidence_ref": item.get("evidence_ref"),
                        "evidence_digest": item.get("evidence_digest"),
                        "claim_scope": item.get("claim_scope"),
                    }
                )

        registry_bound = (
            synthesis.get("registry_snapshot_ref")
            == f"registry://{registry_snapshot.get('registry_id')}"
            and synthesis.get("registry_digest") == registry_snapshot.get("registry_digest")
            and synthesis.get("source_manifest_digest")
            == registry_snapshot.get("source_manifest_digest")
        )
        if not registry_bound:
            errors.append("synthesis must bind the registry snapshot and source manifest")

        exchange_count_bound = (
            len(exchanges) >= 2
            and synthesis.get("exchange_count") == len(exchanges)
            and synthesis.get("exchange_refs") == exchange_refs
        )
        if not exchange_count_bound:
            errors.append("synthesis must bind at least two exchange refs")

        researcher_diversity_bound = (
            len(researcher_agent_ids) >= 2
            and synthesis.get("researcher_agent_ids") == researcher_agent_ids
        )
        if not researcher_diversity_bound:
            errors.append("synthesis must bind at least two distinct researchers")

        exchange_validations_bound = all(
            isinstance(exchange.get("validation"), Mapping)
            and exchange["validation"].get("ok") is True
            and exchange.get("continuity_ledger_appended") is True
            and exchange.get("registry_digest") == synthesis.get("registry_digest")
            and exchange.get("source_manifest_digest")
            == synthesis.get("source_manifest_digest")
            for exchange in exchanges
        )
        if not exchange_validations_bound:
            errors.append("all source exchanges must be valid ledger-appended receipts")

        exchange_digests_bound = (
            synthesis.get("exchange_digests") == exchange_digests
            and all(len(digest) == 64 for digest in exchange_digests)
        )
        if not exchange_digests_bound:
            errors.append("synthesis exchange digests must match source exchange receipts")

        evidence_refs = _ordered_unique(
            [
                str(ref)
                for exchange in exchanges
                for ref in exchange.get("evidence_refs", [])
            ]
        )
        research_domain_refs = _ordered_unique(
            [
                str(ref)
                for exchange in exchanges
                for ref in exchange.get("research_domain_refs", [])
            ]
        )
        evidence_digest_set_bound = (
            synthesis.get("evidence_refs") == evidence_refs
            and synthesis.get("research_domain_refs") == research_domain_refs
            and synthesis.get("evidence_digest_set") == evidence_digest_set
            and bool(evidence_digest_set)
        )
        if not evidence_digest_set_bound:
            errors.append("synthesis must bind evidence refs and evidence digests")

        advisory_only = (
            synthesis.get("claim_ceiling") == "implementation-advisory"
            and synthesis.get("raw_exchange_payload_stored") is False
            and synthesis.get("raw_research_payload_stored") is False
            and synthesis.get("decision_authority_claimed") is False
            and all(
                isinstance(implication, Mapping)
                and implication.get("authority_level") == "advisory-only"
                for implication in synthesis.get("advisory_design_implications", [])
            )
            and all(
                exchange.get("claim_ceiling") == "implementation-advisory"
                and exchange.get("advisory_only") is True
                and exchange.get("raw_research_payload_stored") is False
                and exchange.get("decision_authority_claimed") is False
                for exchange in exchanges
            )
        )
        if not advisory_only:
            errors.append("synthesis must remain advisory-only with no raw payload retention")

        try:
            continuity_event_digest_bound = (
                synthesis.get("continuity_event_digest")
                == sha256_text(
                    canonical_json(_research_evidence_synthesis_continuity_payload(synthesis))
                )
            )
        except (KeyError, TypeError):
            continuity_event_digest_bound = False
            errors.append("research evidence synthesis continuity payload is incomplete")
        if not continuity_event_digest_bound:
            errors.append("continuity_event_digest must bind synthesis evidence")

        try:
            synthesis_digest_bound = (
                synthesis.get("synthesis_digest")
                == sha256_text(
                    canonical_json(_research_evidence_synthesis_digest_payload(synthesis))
                )
            )
        except (KeyError, TypeError):
            synthesis_digest_bound = False
            errors.append("research evidence synthesis digest payload is incomplete")
        if not synthesis_digest_bound:
            errors.append("synthesis_digest must bind synthesis receipt")

        expected_roles = list(YAOYOROZU_RESEARCH_EVIDENCE_LEDGER_SIGNATURE_ROLES)
        continuity_ledger_signature_roles_bound = (
            synthesis.get("continuity_ledger_signature_roles") == expected_roles
        )
        continuity_ledger_entry_appended = synthesis.get("continuity_ledger_appended") is True
        continuity_ledger_entry_digest_bound = (
            continuity_ledger_entry_appended
            and str(synthesis.get("continuity_ledger_entry_ref", "")).startswith(
                "ledger://continuity-ledger/"
            )
            and bool(synthesis.get("continuity_ledger_entry_hash"))
        )
        continuity_ledger_payload_ref_bound = (
            continuity_ledger_entry_appended
            and synthesis.get("continuity_ledger_payload_ref")
            == f"cas://sha256/{synthesis.get('continuity_event_digest')}"
        )
        if not continuity_ledger_signature_roles_bound:
            errors.append("synthesis ledger signature roles must be council+guardian")
        if not continuity_ledger_entry_appended:
            errors.append("research evidence synthesis must be appended to ContinuityLedger")
        if not continuity_ledger_entry_digest_bound:
            errors.append("synthesis ledger entry ref/hash must be bound")
        if not continuity_ledger_payload_ref_bound:
            errors.append("synthesis ledger payload ref must bind event digest")

        return {
            "ok": not errors,
            "registry_bound": registry_bound,
            "exchange_count_bound": exchange_count_bound,
            "researcher_diversity_bound": researcher_diversity_bound,
            "exchange_validations_bound": exchange_validations_bound,
            "exchange_digests_bound": exchange_digests_bound,
            "evidence_digest_set_bound": evidence_digest_set_bound,
            "advisory_only": advisory_only,
            "raw_exchange_payload_stored": bool(
                synthesis.get("raw_exchange_payload_stored")
            ),
            "raw_research_payload_stored": bool(
                synthesis.get("raw_research_payload_stored")
            ),
            "decision_authority_claimed": bool(
                synthesis.get("decision_authority_claimed")
            ),
            "continuity_event_digest_bound": continuity_event_digest_bound,
            "synthesis_digest_bound": synthesis_digest_bound,
            "continuity_ledger_entry_appended": continuity_ledger_entry_appended,
            "continuity_ledger_entry_digest_bound": continuity_ledger_entry_digest_bound,
            "continuity_ledger_payload_ref_bound": continuity_ledger_payload_ref_bound,
            "continuity_ledger_signature_roles_bound": (
                continuity_ledger_signature_roles_bound
            ),
            "errors": errors,
        }

    def prepare_council_convocation(
        self,
        *,
        proposal_profile: str | None = None,
        session_mode: str = "standard",
        target_identity_ref: str = "identity://primary",
        workspace_discovery: Optional[Mapping[str, Any]] = None,
        requested_optional_builder_coverage_areas: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        if not self._entries:
            raise ValueError("registry must be synced before preparing a convocation")
        profile_id = proposal_profile or self._policy.default_convocation_profile
        if profile_id not in self._policy.council_profiles:
            raise ValueError(f"unsupported convocation profile: {profile_id}")

        profile = self._policy.council_profiles[profile_id]
        profile_policy = self._proposal_profile_policy(profile_id)
        required_builder_coverage = list(profile_policy["required_worker_coverage_areas"])
        optional_builder_coverage = list(profile_policy["optional_worker_coverage_areas"])
        requested_optional_builder_coverage = self._normalize_requested_optional_coverage_areas(
            profile_id,
            requested_optional_builder_coverage_areas,
        )
        dispatch_builder_coverage = self._dispatch_coverage_areas(
            profile_id,
            requested_optional_builder_coverage,
        )
        workspace_discovery_binding: Dict[str, Any] | None = None
        workspace_execution_binding: Dict[str, Any] | None = None
        workspace_profile_policy_ready = True
        workspace_execution_policy_ready = True
        if workspace_discovery is not None:
            workspace_discovery_validation = self.validate_workspace_discovery(workspace_discovery)
            if workspace_discovery.get("proposal_profile") != profile_id:
                raise ValueError("workspace_discovery proposal_profile must match the convocation profile")
            if not workspace_discovery_validation["ok"]:
                raise ValueError("workspace_discovery must validate before preparing a convocation")
            if not workspace_discovery_validation["cross_workspace_coverage_complete"]:
                raise ValueError(
                    "workspace_discovery must satisfy the profile-required cross-workspace coverage"
                )
            workspace_discovery_binding = {
                "workspace_discovery_ref": (
                    f"workspace-discovery://{workspace_discovery['discovery_id']}"
                ),
                "workspace_discovery_digest": _non_empty_string(
                    workspace_discovery.get("discovery_digest"),
                    "workspace_discovery.discovery_digest",
                ),
                "proposal_profile": profile_id,
                "workspace_review_budget": int(profile_policy["workspace_review_budget"]),
                "required_workspace_coverage_areas": list(
                    profile_policy["required_workspace_coverage_areas"]
                ),
                "optional_workspace_coverage_areas": list(
                    profile_policy["optional_workspace_coverage_areas"]
                ),
                "accepted_workspace_refs": list(workspace_discovery["accepted_workspace_refs"]),
                "cross_workspace_coverage_complete": bool(
                    workspace_discovery_validation["cross_workspace_coverage_complete"]
                ),
            }
            workspace_execution_binding = self._build_workspace_execution_binding(
                workspace_discovery=workspace_discovery,
                dispatch_builder_coverage=dispatch_builder_coverage,
                required_builder_coverage=required_builder_coverage,
            )
            workspace_profile_policy_ready = (
                workspace_discovery_binding["workspace_review_budget"]
                == workspace_discovery.get("review_budget")
                and workspace_discovery_binding["required_workspace_coverage_areas"]
                == workspace_discovery.get("profile_policy", {}).get(
                    "required_workspace_coverage_areas"
                )
                and workspace_discovery_binding["optional_workspace_coverage_areas"]
                == workspace_discovery.get("profile_policy", {}).get(
                    "optional_workspace_coverage_areas"
                )
            )
            workspace_execution_policy_ready = (
                workspace_execution_binding["dispatch_builder_coverage_areas"]
                == list(dispatch_builder_coverage)
                and workspace_execution_binding["required_candidate_binding_areas"]
                == list(required_builder_coverage)
                and all(
                    coverage_area in workspace_execution_binding["candidate_bound_coverage_areas"]
                    for coverage_area in required_builder_coverage
                )
                and not any(
                    coverage_area in workspace_execution_binding["source_bound_coverage_areas"]
                    for coverage_area in required_builder_coverage
                )
            )

        standing_roles = {
            "speaker": self._select_named_agent(
                role_id="speaker",
                role_label="Speaker",
                candidate_agents=[self._policy.standing_roles["speaker"]],
                required_eligibility="count_for_weighted_vote",
            ),
            "recorder": self._select_named_agent(
                role_id="recorder",
                role_label="Recorder",
                candidate_agents=[self._policy.standing_roles["recorder"]],
                required_eligibility="invite_to_council",
            ),
            "guardian_liaison": self._select_named_agent(
                role_id="guardian-liaison",
                role_label="GuardianLiaison",
                candidate_agents=[self._policy.standing_roles["guardian_liaison"]],
                required_eligibility="guardian_role",
            ),
            "self_liaison": {
                "role_id": "self-liaison",
                "role_label": "SelfLiaison",
                "selected_agent_id": "self-liaison://primary",
                "display_name": "SelfLiaison",
                "source_ref": target_identity_ref,
                "selected_role": "self-liaison",
                "role_scope_kind": "identity-liaison",
                "role_scope_refs": [target_identity_ref],
                "role_policy_ref": "policy://yaoyorozu/self-liaison-explicit-veto/v1",
                "selection_scope_binding_profile": YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE,
                "raw_role_scope_payload_stored": False,
                "status": "selected",
                "trust_score": 1.0,
                "invite_eligible": True,
                "weighted_vote_eligible": True,
                "apply_to_runtime_eligible": False,
                "candidate_count": 1,
                "candidate_agent_ids": ["self-liaison://primary"],
                "selection_reason": "Primary identity remains an explicit veto holder in every Council session.",
            },
        }

        council_panel = [
            self._select_named_agent(
                role_id=str(spec["role_id"]),
                role_label=str(spec["role_label"]),
                candidate_agents=list(spec["candidate_agents"]),
                required_eligibility="count_for_weighted_vote",
            )
            for spec in profile["council_roles"]
        ]
        builder_handoff = [
            self._select_named_agent(
                role_id=f"builder-{spec['coverage_area']}",
                role_label="BuilderHandoff",
                candidate_agents=list(spec["candidate_agents"]),
                required_eligibility="apply_to_runtime",
                coverage_area=str(spec["coverage_area"]),
            )
            for spec in profile["builder_handoff"]
            if str(spec["coverage_area"]) in dispatch_builder_coverage
        ]

        standing_role_scope_binding_ok = (
            self._selection_scope_bound(standing_roles["speaker"], "deliberation")
            and self._selection_scope_bound(standing_roles["recorder"], "deliberation")
            and self._selection_scope_bound(standing_roles["guardian_liaison"], "oversight")
            and self._selection_scope_bound(standing_roles["self_liaison"], "identity-liaison")
        )
        council_panel_scope_binding_ok = all(
            self._selection_has_registry_scope(
                selection,
                ("deliberation", "oversight", "research-evidence"),
            )
            for selection in council_panel
        )
        builder_handoff_scope_binding_ok = all(
            self._builder_selection_scope_bound(selection)
            for selection in builder_handoff
        )
        missing_council_roles = [
            selection["role_id"] for selection in council_panel if selection["status"] != "selected"
        ]
        missing_builder_coverage = [
            selection["coverage_area"]
            for selection in builder_handoff
            if selection["status"] != "selected"
        ]
        weighted_vote_ready_count = sum(
            1 for selection in council_panel if selection["weighted_vote_eligible"]
        )
        validation = {
            "standing_roles_ready": all(
                selection["status"] == "selected"
                for selection in standing_roles.values()
                if isinstance(selection, dict)
            ),
            "guardian_liaison_ready": standing_roles["guardian_liaison"]["status"] == "selected",
            "self_liaison_bound": standing_roles["self_liaison"]["status"] == "selected",
            "council_role_coverage_ok": not missing_council_roles,
            "weighted_vote_quorum_ready": weighted_vote_ready_count >= 3,
            "builder_handoff_coverage_ok": not missing_builder_coverage,
            "builder_profile_policy_ready": sorted(
                selection["coverage_area"]
                for selection in builder_handoff
                if isinstance(selection, Mapping) and selection.get("coverage_area")
            )
            == sorted(dispatch_builder_coverage)
            and requested_optional_builder_coverage
            == self._normalize_requested_optional_coverage_areas(
                profile_id,
                requested_optional_builder_coverage,
            ),
            "workspace_discovery_bound": workspace_discovery_binding is not None,
            "workspace_profile_policy_ready": workspace_profile_policy_ready,
            "workspace_execution_bound": workspace_execution_binding is not None,
            "workspace_execution_policy_ready": workspace_execution_policy_ready,
            "standing_role_scope_binding_ok": standing_role_scope_binding_ok,
            "council_panel_scope_binding_ok": council_panel_scope_binding_ok,
            "builder_handoff_scope_binding_ok": builder_handoff_scope_binding_ok,
            "raw_selection_scope_payload_stored": False,
        }
        validation["ok"] = all(
            value
            for key, value in validation.items()
            if key
            not in {
                "workspace_discovery_bound",
                "workspace_execution_bound",
                "raw_selection_scope_payload_stored",
            }
        )
        session_body = {
            "registry_snapshot_ref": (
                f"registry://{self._last_snapshot_id}" if self._last_snapshot_id else ""
            ),
            "policy_id": self._policy.policy_id,
            "proposal_profile": profile_id,
            "summary": str(profile["summary"]),
            "session_mode": session_mode,
            "target_identity_ref": target_identity_ref,
            "standing_roles": standing_roles,
            "council_panel": council_panel,
            "builder_handoff": builder_handoff,
            "selection_summary": {
                "required_council_role_count": len(profile["council_roles"]),
                "selected_council_role_count": len(council_panel) - len(missing_council_roles),
                "weighted_vote_ready_count": weighted_vote_ready_count,
                "required_builder_coverage_areas": list(required_builder_coverage),
                "optional_builder_coverage_areas": list(optional_builder_coverage),
                "requested_optional_builder_coverage_areas": list(
                    requested_optional_builder_coverage
                ),
                "dispatch_builder_coverage_areas": list(dispatch_builder_coverage),
                "selected_builder_coverage_count": len(builder_handoff) - len(missing_builder_coverage),
                "missing_council_roles": missing_council_roles,
                "missing_builder_coverage": missing_builder_coverage,
            },
            "validation": validation,
        }
        if workspace_discovery_binding is not None:
            session_body["workspace_discovery_binding"] = workspace_discovery_binding
        if workspace_execution_binding is not None:
            session_body["workspace_execution_binding"] = workspace_execution_binding
        return {
            "kind": "council_convocation_session",
            "schema_version": "1.0.0",
            "session_id": new_id("council-convocation"),
            "recorded_at": utc_now_iso(),
            "session_digest": sha256_text(canonical_json(session_body)),
            **session_body,
        }

    def prepare_worker_dispatch(self, convocation_session: Mapping[str, Any]) -> Dict[str, Any]:
        if not self._entries or self._agents_root is None:
            raise ValueError("registry must be synced before preparing worker dispatch")
        if convocation_session.get("kind") != "council_convocation_session":
            raise ValueError("convocation_session.kind must equal council_convocation_session")

        builder_handoff = convocation_session.get("builder_handoff", [])
        if not isinstance(builder_handoff, list):
            raise ValueError("convocation_session.builder_handoff must be a list")

        repo_root = self._agents_root.parent
        dispatch_id = new_id("yaoyorozu-dispatch")
        dispatch_plan_ref = f"dispatch://{dispatch_id}"
        workspace_execution_binding = convocation_session.get("workspace_execution_binding", {})
        execution_target_index: Dict[str, Dict[str, Any]] = {}
        if isinstance(workspace_execution_binding, Mapping):
            for target in workspace_execution_binding.get("execution_targets", []):
                if isinstance(target, Mapping):
                    coverage_area = str(target.get("coverage_area", "")).strip()
                    if coverage_area:
                        execution_target_index[coverage_area] = dict(target)
        standing_roles = convocation_session.get("standing_roles", {})
        guardian_liaison = (
            standing_roles.get("guardian_liaison", {})
            if isinstance(standing_roles, Mapping)
            else {}
        )
        guardian_agent_id = _non_empty_string(
            guardian_liaison.get("selected_agent_id"),
            "convocation_session.standing_roles.guardian_liaison.selected_agent_id",
        )
        proposal_profile = _non_empty_string(
            convocation_session.get("proposal_profile"),
            "convocation_session.proposal_profile",
        )
        dispatch_units: List[Dict[str, Any]] = []
        selected_coverage: List[str] = []
        for selection in builder_handoff:
            if not isinstance(selection, Mapping):
                raise ValueError("builder_handoff entries must be mappings")
            coverage_area = _non_empty_string(selection.get("coverage_area"), "builder_handoff.coverage_area")
            if coverage_area not in self._policy.worker_target_paths:
                raise ValueError(f"unsupported coverage area: {coverage_area}")
            if selection.get("status") != "selected":
                continue

            target_paths = list(self._policy.worker_target_paths[coverage_area])
            execution_target = execution_target_index.get(coverage_area)
            selected_workspace_ref = _workspace_ref_from_root(repo_root)
            selected_workspace_root = str(repo_root)
            selected_workspace_role = "source"
            selected_workspace_source_kind = "local-workspace"
            workspace_scope = self._policy.worker_workspace_scope
            sandbox_seed_strategy = self._policy.inline_workspace_seed_strategy
            workspace_target_digest = ""
            if execution_target is not None:
                selected_workspace_ref = _non_empty_string(
                    execution_target.get("workspace_ref"),
                    "workspace_execution_binding.workspace_ref",
                )
                selected_workspace_root = _non_empty_string(
                    execution_target.get("workspace_root"),
                    "workspace_execution_binding.workspace_root",
                )
                selected_workspace_role = _non_empty_string(
                    execution_target.get("workspace_role"),
                    "workspace_execution_binding.workspace_role",
                )
                selected_workspace_source_kind = _non_empty_string(
                    execution_target.get("source_kind"),
                    "workspace_execution_binding.source_kind",
                )
                workspace_scope = _non_empty_string(
                    execution_target.get("workspace_scope"),
                    "workspace_execution_binding.workspace_scope",
                )
                sandbox_seed_strategy = _non_empty_string(
                    execution_target.get("sandbox_seed_strategy"),
                    "workspace_execution_binding.sandbox_seed_strategy",
                )
                workspace_target_digest = _non_empty_string(
                    execution_target.get("target_digest"),
                    "workspace_execution_binding.target_digest",
                )
            if not workspace_target_digest:
                workspace_target = {
                    "coverage_area": coverage_area,
                    "workspace_ref": selected_workspace_ref,
                    "workspace_root": selected_workspace_root,
                    "workspace_role": selected_workspace_role,
                    "source_kind": selected_workspace_source_kind,
                    "workspace_scope": workspace_scope,
                    "execution_transport_profile": self._policy.workspace_execution_transport_profile,
                    "sandbox_seed_strategy": sandbox_seed_strategy,
                    "dependency_materialization_profile": (
                        self._policy.dependency_materialization_profile
                    ),
                    "dependency_materialization_strategy": (
                        self._policy.external_dependency_materialization_strategy
                        if workspace_scope == self._policy.external_workspace_scope
                        else self._policy.inline_dependency_materialization_strategy
                    ),
                    "dependency_materialization_required": (
                        workspace_scope == self._policy.external_workspace_scope
                    ),
                    "dependency_materialization_paths": (
                        list(self._policy.dependency_materialization_paths)
                        if workspace_scope == self._policy.external_workspace_scope
                        else []
                    ),
                    "guardian_preseed_gate_required": (
                        workspace_scope == self._policy.external_workspace_scope
                    ),
                }
                workspace_target_digest = sha256_text(
                    canonical_json(_workspace_execution_target_digest_payload(workspace_target))
                )
            execution_workspace_root = (
                str(
                    self._external_execution_workspace_root(
                        selected_workspace_root,
                        dispatch_id,
                        coverage_area,
                    )
                )
                if workspace_scope == self._policy.external_workspace_scope
                else str(repo_root)
            )
            dependency_materialization_required = (
                workspace_scope == self._policy.external_workspace_scope
            )
            dependency_materialization_strategy = (
                self._policy.external_dependency_materialization_strategy
                if dependency_materialization_required
                else self._policy.inline_dependency_materialization_strategy
            )
            dependency_materialization_paths = (
                list(self._policy.dependency_materialization_paths)
                if dependency_materialization_required
                else []
            )
            unit_id = new_id("worker-dispatch")
            command_preview = [
                "python3",
                "-m",
                "omoikane.agentic.local_worker_stub",
                "--agent-id",
                _non_empty_string(selection.get("selected_agent_id"), "builder_handoff.selected_agent_id"),
                "--role-id",
                _non_empty_string(selection.get("role_id"), "builder_handoff.role_id"),
                "--coverage-area",
                coverage_area,
                "--dispatch-profile",
                self._policy.worker_dispatch_profile,
                "--workspace-scope",
                workspace_scope,
                "--dispatch-plan-ref",
                dispatch_plan_ref,
                "--dispatch-unit-ref",
                unit_id,
                "--workspace-root",
                execution_workspace_root,
                "--source-ref",
                _non_empty_string(selection.get("source_ref"), "builder_handoff.source_ref"),
            ]
            for target_path in target_paths:
                command_preview.extend(["--target-path", target_path])

            guardian_preseed_gate = self._build_guardian_preseed_gate(
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=unit_id,
                proposal_profile=proposal_profile,
                coverage_area=coverage_area,
                workspace_ref=selected_workspace_ref,
                selected_workspace_root=selected_workspace_root,
                execution_workspace_root=execution_workspace_root,
                execution_host_ref=self._policy.workspace_discovery_host_ref,
                workspace_scope=workspace_scope,
                sandbox_seed_strategy=sandbox_seed_strategy,
                target_digest=workspace_target_digest,
                guardian_agent_id=guardian_agent_id,
            )
            unit = {
                "unit_id": unit_id,
                "role_id": _non_empty_string(selection.get("role_id"), "builder_handoff.role_id"),
                "coverage_area": coverage_area,
                "selected_agent_id": _non_empty_string(
                    selection.get("selected_agent_id"),
                    "builder_handoff.selected_agent_id",
                ),
                "display_name": _non_empty_string(selection.get("display_name"), "builder_handoff.display_name"),
                "source_ref": _non_empty_string(selection.get("source_ref"), "builder_handoff.source_ref"),
                "source_kind": "repo-local-agent",
                "dispatch_scope": self._policy.worker_dispatch_scope,
                "sandbox_mode": self._policy.worker_sandbox_mode,
                "workspace_scope": workspace_scope,
                "entrypoint_ref": self._policy.worker_entrypoint_ref,
                "command_preview": command_preview,
                "target_paths": target_paths,
                "execution_workspace_ref": selected_workspace_ref,
                "execution_workspace_root": execution_workspace_root,
                "selected_workspace_root": selected_workspace_root,
                "selected_workspace_role": selected_workspace_role,
                "execution_host_ref": self._policy.workspace_discovery_host_ref,
                "execution_transport_profile": self._policy.workspace_execution_transport_profile,
                "sandbox_seed_strategy": sandbox_seed_strategy,
                "workspace_target_digest": workspace_target_digest,
                "dependency_materialization_profile": (
                    self._policy.dependency_materialization_profile
                ),
                "dependency_materialization_strategy": dependency_materialization_strategy,
                "dependency_materialization_required": dependency_materialization_required,
                "dependency_materialization_paths": dependency_materialization_paths,
                "guardian_preseed_gate": guardian_preseed_gate,
                "expected_report_fields": list(YAOYOROZU_WORKER_REPORT_FIELDS),
            }
            unit["command_digest"] = sha256_text(canonical_json(_dispatch_unit_digest_payload(unit)))
            dispatch_units.append(unit)
            selected_coverage.append(coverage_area)

        profile_policy = self._proposal_profile_policy(proposal_profile)
        selection_summary = convocation_session.get("selection_summary", {})
        required_coverage = (
            list(selection_summary.get("required_builder_coverage_areas", []))
            if isinstance(selection_summary, Mapping)
            else []
        )
        optional_coverage = (
            list(selection_summary.get("optional_builder_coverage_areas", []))
            if isinstance(selection_summary, Mapping)
            else []
        )
        requested_optional_coverage = (
            list(selection_summary.get("requested_optional_builder_coverage_areas", []))
            if isinstance(selection_summary, Mapping)
            else []
        )
        dispatch_coverage = (
            list(selection_summary.get("dispatch_builder_coverage_areas", []))
            if isinstance(selection_summary, Mapping)
            else []
        )
        if not required_coverage:
            required_coverage = list(profile_policy["required_worker_coverage_areas"])
        if not optional_coverage:
            optional_coverage = list(profile_policy["optional_worker_coverage_areas"])
        normalized_requested_optional_coverage = self._normalize_requested_optional_coverage_areas(
            proposal_profile,
            requested_optional_coverage,
        )
        if not dispatch_coverage:
            dispatch_coverage = self._dispatch_coverage_areas(
                proposal_profile,
                normalized_requested_optional_coverage,
            )
        missing_coverage = [coverage for coverage in dispatch_coverage if coverage not in selected_coverage]
        unexpected_coverage = [
            coverage for coverage in selected_coverage if coverage not in dispatch_coverage
        ]
        unique_command_digests = len({unit["command_digest"] for unit in dispatch_units}) == len(dispatch_units)
        guardian_gate_validations = [
            self._validate_guardian_preseed_gate(
                unit["guardian_preseed_gate"],
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=str(unit["unit_id"]),
                proposal_profile=proposal_profile,
                coverage_area=str(unit["coverage_area"]),
                workspace_ref=str(unit["execution_workspace_ref"]),
                selected_workspace_root=str(unit["selected_workspace_root"]),
                execution_workspace_root=str(unit["execution_workspace_root"]),
                execution_host_ref=str(unit["execution_host_ref"]),
                workspace_scope=str(unit["workspace_scope"]),
                sandbox_seed_strategy=str(unit["sandbox_seed_strategy"]),
                target_digest=str(unit["workspace_target_digest"]),
                guardian_agent_id=guardian_agent_id,
            )
            for unit in dispatch_units
        ]
        external_guardian_gate_validations = [
            validation
            for validation in guardian_gate_validations
            if validation["gate_required"]
        ]
        validation = {
            "registry_bound": bool(self._last_snapshot_id),
            "convocation_bound": bool(convocation_session.get("session_id")),
            "builder_coverage_ok": (
                not missing_coverage
                and not unexpected_coverage
                and len(dispatch_units) == len(dispatch_coverage)
            ),
            "unique_command_digests": unique_command_digests,
            "workspace_execution_bound": any(
                unit["workspace_scope"] == self._policy.external_workspace_scope
                for unit in dispatch_units
            ),
            "same_host_scope_only": all(
                unit["dispatch_scope"] == self._policy.worker_dispatch_scope
                and unit["workspace_scope"]
                in {self._policy.worker_workspace_scope, self._policy.external_workspace_scope}
                for unit in dispatch_units
            ),
            "guardian_preseed_gate_bound": all(
                gate_validation["ok"] for gate_validation in guardian_gate_validations
            ),
            "external_preseed_gate_required": bool(external_guardian_gate_validations),
            "all_external_preseed_gates_ready": all(
                gate_validation["gate_passed"]
                for gate_validation in external_guardian_gate_validations
            ),
            "guardian_preseed_oversight_bound": all(
                gate_validation["oversight_event_satisfied"]
                and gate_validation["reviewer_network_attested"]
                for gate_validation in guardian_gate_validations
            ),
            "all_external_preseed_oversight_satisfied": all(
                gate_validation["oversight_event_satisfied"]
                and gate_validation["reviewer_network_attested"]
                for gate_validation in external_guardian_gate_validations
            ),
            "dependency_materialization_bound": all(
                unit["dependency_materialization_profile"]
                == self._policy.dependency_materialization_profile
                and unit["dependency_materialization_required"]
                == (unit["workspace_scope"] == self._policy.external_workspace_scope)
                and unit["dependency_materialization_strategy"]
                == (
                    self._policy.external_dependency_materialization_strategy
                    if unit["workspace_scope"] == self._policy.external_workspace_scope
                    else self._policy.inline_dependency_materialization_strategy
                )
                and (
                    unit["dependency_materialization_paths"]
                    == list(self._policy.dependency_materialization_paths)
                    if unit["workspace_scope"] == self._policy.external_workspace_scope
                    else unit["dependency_materialization_paths"] == []
                )
                for unit in dispatch_units
            ),
            "profile_policy_ready": (
                required_coverage == list(profile_policy["required_worker_coverage_areas"])
                and optional_coverage == list(profile_policy["optional_worker_coverage_areas"])
                and normalized_requested_optional_coverage == requested_optional_coverage
                and dispatch_coverage
                == self._dispatch_coverage_areas(
                    proposal_profile,
                    normalized_requested_optional_coverage,
                )
            ),
        }
        validation["ok"] = all(
            value
            for key, value in validation.items()
            if key not in {"workspace_execution_bound", "external_preseed_gate_required"}
        )
        dispatch_body = {
            "dispatch_profile": self._policy.worker_dispatch_profile,
            "registry_snapshot_ref": (
                f"registry://{self._last_snapshot_id}" if self._last_snapshot_id else ""
            ),
            "convocation_session_ref": (
                f"convocation://{convocation_session['session_id']}"
                if convocation_session.get("session_id")
                else ""
            ),
            "policy_id": self._policy.policy_id,
            "proposal_profile": _non_empty_string(
                convocation_session.get("proposal_profile"),
                "convocation_session.proposal_profile",
            ),
            "session_mode": _non_empty_string(
                convocation_session.get("session_mode"),
                "convocation_session.session_mode",
            ),
            "target_identity_ref": _non_empty_string(
                convocation_session.get("target_identity_ref"),
                "convocation_session.target_identity_ref",
            ),
            "workspace_root": str(repo_root),
            "dispatch_units": dispatch_units,
            "selection_summary": {
                "required_worker_count": len(required_coverage),
                "required_coverage_areas": list(required_coverage),
                "optional_coverage_areas": list(optional_coverage),
                "requested_optional_coverage_areas": list(normalized_requested_optional_coverage),
                "dispatch_coverage_areas": list(dispatch_coverage),
                "selected_worker_count": len(dispatch_units),
                "unique_coverage_areas": sorted(set(selected_coverage)),
                "missing_coverage": missing_coverage,
                "candidate_bound_worker_count": sum(
                    1
                    for unit in dispatch_units
                    if unit["workspace_scope"] == self._policy.external_workspace_scope
                ),
                "source_bound_worker_count": sum(
                    1
                    for unit in dispatch_units
                    if unit["workspace_scope"] == self._policy.worker_workspace_scope
                ),
                "guardian_preseed_gate_count": len(guardian_gate_validations),
                "external_preseed_gate_count": len(external_guardian_gate_validations),
                "guardian_preseed_oversight_event_count": sum(
                    1
                    for unit in dispatch_units
                    if unit["guardian_preseed_gate"]["guardian_oversight_event_ref"]
                ),
                "external_preseed_oversight_satisfied_count": sum(
                    1
                    for gate_validation in external_guardian_gate_validations
                    if gate_validation["oversight_event_satisfied"]
                    and gate_validation["reviewer_network_attested"]
                ),
                "dependency_materialization_required_count": sum(
                    1
                    for unit in dispatch_units
                    if unit["dependency_materialization_required"]
                ),
                "runtime_exec_ready": bool(dispatch_units),
            },
            "validation": validation,
        }
        dispatch = {
            "kind": "yaoyorozu_worker_dispatch_plan",
            "schema_version": "1.0.0",
            "dispatch_id": dispatch_id,
            "planned_at": utc_now_iso(),
            **dispatch_body,
        }
        dispatch["dispatch_digest"] = sha256_text(canonical_json(_dispatch_plan_digest_payload(dispatch)))
        return dispatch

    def validate_worker_dispatch_plan(self, dispatch_plan: Mapping[str, Any]) -> Dict[str, Any]:
        errors: List[str] = []
        units = dispatch_plan.get("dispatch_units", [])
        if dispatch_plan.get("kind") != "yaoyorozu_worker_dispatch_plan":
            errors.append("kind must equal yaoyorozu_worker_dispatch_plan")
        if dispatch_plan.get("dispatch_profile") != self._policy.worker_dispatch_profile:
            errors.append("dispatch_profile mismatch")
        if not isinstance(units, list) or not units:
            errors.append("dispatch_units must be a non-empty list")
            units = []
        proposal_profile = dispatch_plan.get("proposal_profile")
        if proposal_profile not in self._policy.council_profiles:
            errors.append("proposal_profile must map to one supported proposal profile")
            expected_profile_policy: Dict[str, Any] = {}
        else:
            expected_profile_policy = self._proposal_profile_policy(str(proposal_profile))
        selection_summary = dispatch_plan.get("selection_summary", {})
        if not isinstance(selection_summary, Mapping):
            errors.append("selection_summary must be a mapping")
            selection_summary = {}

        required_coverage = selection_summary.get("required_coverage_areas", [])
        optional_coverage = selection_summary.get("optional_coverage_areas", [])
        requested_optional_coverage = selection_summary.get("requested_optional_coverage_areas", [])
        dispatch_coverage = selection_summary.get("dispatch_coverage_areas", [])
        if not isinstance(required_coverage, list) or not required_coverage:
            errors.append("selection_summary.required_coverage_areas must be a non-empty list")
            required_coverage = []
        if not isinstance(optional_coverage, list):
            errors.append("selection_summary.optional_coverage_areas must be a list")
            optional_coverage = []
        if not isinstance(requested_optional_coverage, list):
            errors.append("selection_summary.requested_optional_coverage_areas must be a list")
            requested_optional_coverage = []
        if not isinstance(dispatch_coverage, list) or not dispatch_coverage:
            errors.append("selection_summary.dispatch_coverage_areas must be a non-empty list")
            dispatch_coverage = []
        if expected_profile_policy:
            if required_coverage != expected_profile_policy["required_worker_coverage_areas"]:
                errors.append("selection_summary.required_coverage_areas mismatch")
            if optional_coverage != expected_profile_policy["optional_worker_coverage_areas"]:
                errors.append("selection_summary.optional_coverage_areas mismatch")
            normalized_requested_optional = self._normalize_requested_optional_coverage_areas(
                str(proposal_profile),
                requested_optional_coverage,
            )
            if requested_optional_coverage != normalized_requested_optional:
                errors.append("selection_summary.requested_optional_coverage_areas mismatch")
            if dispatch_coverage != self._dispatch_coverage_areas(
                str(proposal_profile),
                requested_optional_coverage,
            ):
                errors.append("selection_summary.dispatch_coverage_areas mismatch")
        else:
            normalized_requested_optional = []

        coverage_areas: List[str] = []
        digests: List[str] = []
        candidate_bound_worker_count = 0
        source_bound_worker_count = 0
        guardian_preseed_gate_count = 0
        external_preseed_gate_count = 0
        guardian_preseed_oversight_event_count = 0
        external_preseed_oversight_satisfied_count = 0
        dependency_materialization_required_count = 0
        guardian_preseed_gate_bound = True
        all_external_preseed_gates_ready = True
        guardian_preseed_oversight_bound = True
        all_external_preseed_oversight_satisfied = True
        dependency_materialization_bound = True
        for unit in units:
            if not isinstance(unit, Mapping):
                errors.append("dispatch_units entries must be mappings")
                continue
            coverage_area = unit.get("coverage_area")
            if coverage_area not in self._policy.worker_target_paths:
                errors.append("dispatch unit coverage_area is invalid")
                continue
            coverage_areas.append(str(coverage_area))
            digests.append(str(unit.get("command_digest", "")))
            if unit.get("dispatch_scope") != self._policy.worker_dispatch_scope:
                errors.append("dispatch unit must remain repo-local-subprocess scoped")
            if unit.get("sandbox_mode") != self._policy.worker_sandbox_mode:
                errors.append("dispatch unit sandbox_mode must be temp-workspace-only")
            if unit.get("workspace_scope") not in {
                self._policy.worker_workspace_scope,
                self._policy.external_workspace_scope,
            }:
                errors.append("dispatch unit workspace_scope must stay within the same-host policy")
            elif unit.get("workspace_scope") == self._policy.external_workspace_scope:
                candidate_bound_worker_count += 1
            else:
                source_bound_worker_count += 1
            if unit.get("entrypoint_ref") != self._policy.worker_entrypoint_ref:
                errors.append("dispatch unit entrypoint_ref mismatch")
            if not str(unit.get("execution_workspace_ref", "")).strip():
                errors.append("dispatch unit execution_workspace_ref must be a non-empty string")
            if not str(unit.get("execution_workspace_root", "")).strip():
                errors.append("dispatch unit execution_workspace_root must be a non-empty string")
            if not str(unit.get("selected_workspace_root", "")).strip():
                errors.append("dispatch unit selected_workspace_root must be a non-empty string")
            if str(unit.get("selected_workspace_role", "")).strip() not in {"source", "candidate"}:
                errors.append("dispatch unit selected_workspace_role mismatch")
            if unit.get("execution_host_ref") != self._policy.workspace_discovery_host_ref:
                errors.append("dispatch unit execution_host_ref mismatch")
            if unit.get("execution_transport_profile") != self._policy.workspace_execution_transport_profile:
                errors.append("dispatch unit execution_transport_profile mismatch")
            sandbox_seed_strategy = unit.get("sandbox_seed_strategy")
            if sandbox_seed_strategy not in {
                self._policy.inline_workspace_seed_strategy,
                self._policy.external_workspace_seed_strategy,
            }:
                errors.append("dispatch unit sandbox_seed_strategy mismatch")
            dependency_required = unit.get("dependency_materialization_required")
            expected_dependency_required = (
                unit.get("workspace_scope") == self._policy.external_workspace_scope
            )
            if dependency_required is not expected_dependency_required:
                dependency_materialization_bound = False
                errors.append("dispatch unit dependency_materialization_required mismatch")
            if (
                unit.get("dependency_materialization_profile")
                != self._policy.dependency_materialization_profile
            ):
                dependency_materialization_bound = False
                errors.append("dispatch unit dependency_materialization_profile mismatch")
            expected_dependency_strategy = (
                self._policy.external_dependency_materialization_strategy
                if expected_dependency_required
                else self._policy.inline_dependency_materialization_strategy
            )
            if unit.get("dependency_materialization_strategy") != expected_dependency_strategy:
                dependency_materialization_bound = False
                errors.append("dispatch unit dependency_materialization_strategy mismatch")
            dependency_paths = unit.get("dependency_materialization_paths", [])
            if expected_dependency_required:
                dependency_materialization_required_count += 1
                if dependency_paths != list(self._policy.dependency_materialization_paths):
                    dependency_materialization_bound = False
                    errors.append("external dispatch dependency_materialization_paths mismatch")
            elif dependency_paths != []:
                dependency_materialization_bound = False
                errors.append("repo-local dispatch dependency_materialization_paths must be empty")
            workspace_target_digest = str(unit.get("workspace_target_digest", "")).strip()
            if len(workspace_target_digest) != 64:
                errors.append("dispatch unit workspace_target_digest must be a sha256 digest")
            guardian_gate = unit.get("guardian_preseed_gate", {})
            gate_validation = self._validate_guardian_preseed_gate(
                guardian_gate if isinstance(guardian_gate, Mapping) else {},
                dispatch_plan_ref=f"dispatch://{dispatch_plan.get('dispatch_id', '')}",
                dispatch_unit_ref=str(unit.get("unit_id", "")),
                proposal_profile=str(proposal_profile),
                coverage_area=str(coverage_area),
                workspace_ref=str(unit.get("execution_workspace_ref", "")),
                selected_workspace_root=str(unit.get("selected_workspace_root", "")),
                execution_workspace_root=str(unit.get("execution_workspace_root", "")),
                execution_host_ref=str(unit.get("execution_host_ref", "")),
                workspace_scope=str(unit.get("workspace_scope", "")),
                sandbox_seed_strategy=str(sandbox_seed_strategy),
                target_digest=workspace_target_digest,
                guardian_agent_id=str(
                    (guardian_gate if isinstance(guardian_gate, Mapping) else {}).get(
                        "guardian_agent_id", ""
                    )
                ),
            )
            guardian_preseed_gate_count += 1
            if gate_validation["gate_required"]:
                external_preseed_gate_count += 1
                if (
                    gate_validation["oversight_event_satisfied"]
                    and gate_validation["reviewer_network_attested"]
                ):
                    external_preseed_oversight_satisfied_count += 1
                else:
                    all_external_preseed_oversight_satisfied = False
            if (
                isinstance(guardian_gate, Mapping)
                and str(guardian_gate.get("guardian_oversight_event_ref", "")).strip()
            ):
                guardian_preseed_oversight_event_count += 1
            if not gate_validation["ok"]:
                guardian_preseed_gate_bound = False
                errors.extend(gate_validation["errors"])
            if not (
                gate_validation["oversight_event_satisfied"]
                and gate_validation["reviewer_network_attested"]
            ):
                guardian_preseed_oversight_bound = False
            if gate_validation["gate_required"] and not gate_validation["gate_passed"]:
                all_external_preseed_gates_ready = False
            command_preview = unit.get("command_preview", [])
            if f"dispatch://{dispatch_plan.get('dispatch_id', '')}" not in command_preview:
                errors.append("dispatch unit command preview must bind the dispatch plan ref")
            if str(unit.get("unit_id", "")) not in command_preview:
                errors.append("dispatch unit command preview must bind the dispatch unit ref")
            if str(unit.get("execution_workspace_root", "")) not in command_preview:
                errors.append("dispatch unit command preview must bind the execution workspace root")

        missing_coverage = [coverage for coverage in dispatch_coverage if coverage not in coverage_areas]
        unexpected_coverage = [
            coverage for coverage in coverage_areas if coverage not in dispatch_coverage
        ]
        if len(set(digests)) != len(digests):
            errors.append("dispatch unit command digests must be unique")
        if selection_summary.get("required_worker_count") != len(required_coverage):
            errors.append("selection_summary.required_worker_count must match required_coverage_areas")
        if selection_summary.get("selected_worker_count") != len(units):
            errors.append("selection_summary.selected_worker_count must match dispatch_units")
        if selection_summary.get("unique_coverage_areas") != sorted(set(coverage_areas)):
            errors.append("selection_summary.unique_coverage_areas must match dispatch unit coverage")
        if selection_summary.get("missing_coverage") != missing_coverage:
            errors.append("selection_summary.missing_coverage must match required coverage delta")
        if selection_summary.get("candidate_bound_worker_count") != candidate_bound_worker_count:
            errors.append(
                "selection_summary.candidate_bound_worker_count must match external workspace units"
            )
        if selection_summary.get("source_bound_worker_count") != source_bound_worker_count:
            errors.append(
                "selection_summary.source_bound_worker_count must match repo-local units"
            )
        if selection_summary.get("guardian_preseed_gate_count") != guardian_preseed_gate_count:
            errors.append(
                "selection_summary.guardian_preseed_gate_count must match dispatch units"
            )
        if selection_summary.get("external_preseed_gate_count") != external_preseed_gate_count:
            errors.append(
                "selection_summary.external_preseed_gate_count must match external workspace units"
            )
        if (
            selection_summary.get("guardian_preseed_oversight_event_count")
            != guardian_preseed_oversight_event_count
        ):
            errors.append(
                "selection_summary.guardian_preseed_oversight_event_count must match bound oversight events"
            )
        if (
            selection_summary.get("external_preseed_oversight_satisfied_count")
            != external_preseed_oversight_satisfied_count
        ):
            errors.append(
                "selection_summary.external_preseed_oversight_satisfied_count must match satisfied external oversight events"
            )
        if (
            selection_summary.get("dependency_materialization_required_count")
            != dependency_materialization_required_count
        ):
            errors.append(
                "selection_summary.dependency_materialization_required_count must match external workspace units"
            )
        validation = dispatch_plan.get("validation", {})
        if isinstance(validation, Mapping):
            if validation.get("guardian_preseed_gate_bound") != guardian_preseed_gate_bound:
                errors.append("validation.guardian_preseed_gate_bound mismatch")
            if validation.get("external_preseed_gate_required") != bool(external_preseed_gate_count):
                errors.append("validation.external_preseed_gate_required mismatch")
            if validation.get("all_external_preseed_gates_ready") != all_external_preseed_gates_ready:
                errors.append("validation.all_external_preseed_gates_ready mismatch")
            if validation.get("guardian_preseed_oversight_bound") != guardian_preseed_oversight_bound:
                errors.append("validation.guardian_preseed_oversight_bound mismatch")
            if (
                validation.get("all_external_preseed_oversight_satisfied")
                != all_external_preseed_oversight_satisfied
            ):
                errors.append("validation.all_external_preseed_oversight_satisfied mismatch")
            if validation.get("dependency_materialization_bound") != dependency_materialization_bound:
                errors.append("validation.dependency_materialization_bound mismatch")
        else:
            errors.append("validation must be a mapping")

        return {
            "ok": not errors and not missing_coverage and not unexpected_coverage,
            "dispatch_unit_count": len(units),
            "unique_coverage_areas": sorted(set(coverage_areas)),
            "missing_coverage": missing_coverage,
            "unexpected_coverage": unexpected_coverage,
            "required_coverage_areas": list(required_coverage),
            "optional_coverage_areas": list(optional_coverage),
            "requested_optional_coverage_areas": list(normalized_requested_optional),
            "dispatch_coverage_areas": list(dispatch_coverage),
            "runtime_exec_ready": bool(units),
            "guardian_preseed_gate_bound": guardian_preseed_gate_bound,
            "external_preseed_gate_count": external_preseed_gate_count,
            "all_external_preseed_gates_ready": all_external_preseed_gates_ready,
            "guardian_preseed_oversight_bound": guardian_preseed_oversight_bound,
            "all_external_preseed_oversight_satisfied": all_external_preseed_oversight_satisfied,
            "dependency_materialization_bound": dependency_materialization_bound,
            "dependency_materialization_required_count": dependency_materialization_required_count,
            "errors": errors,
        }

    def execute_worker_dispatch(self, dispatch_plan: Mapping[str, Any]) -> Dict[str, Any]:
        if dispatch_plan.get("kind") != "yaoyorozu_worker_dispatch_plan":
            raise ValueError("dispatch_plan.kind must equal yaoyorozu_worker_dispatch_plan")

        repo_root = Path(
            _non_empty_string(dispatch_plan.get("workspace_root"), "dispatch_plan.workspace_root")
        ).resolve()
        dispatch_plan_ref = f"dispatch://{dispatch_plan['dispatch_id']}"
        units = dispatch_plan.get("dispatch_units", [])
        if not isinstance(units, list) or not units:
            raise ValueError("dispatch_plan.dispatch_units must be a non-empty list")

        env = os.environ.copy()
        src_root = repo_root / "src"
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            str(src_root)
            if not existing_pythonpath
            else f"{src_root}{os.pathsep}{existing_pythonpath}"
        )

        results: List[Dict[str, Any]] = []
        failed_role_ids: List[str] = []
        for launch_index, unit in enumerate(units, start=1):
            if not isinstance(unit, Mapping):
                raise ValueError("dispatch_plan.dispatch_units entries must be mappings")
            preview = unit.get("command_preview")
            if not isinstance(preview, list) or not all(isinstance(item, str) for item in preview):
                raise ValueError("dispatch unit command_preview must be a list of strings")
            workspace_scope = _non_empty_string(unit.get("workspace_scope"), "unit.workspace_scope")
            selected_workspace_root = Path(
                _non_empty_string(unit.get("selected_workspace_root"), "unit.selected_workspace_root")
            ).resolve()
            execution_root = Path(
                _non_empty_string(unit.get("execution_workspace_root"), "unit.execution_workspace_root")
            ).resolve()
            guardian_preseed_gate = unit.get("guardian_preseed_gate", {})
            guardian_gate_validation = self._validate_guardian_preseed_gate(
                guardian_preseed_gate if isinstance(guardian_preseed_gate, Mapping) else {},
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=str(unit["unit_id"]),
                proposal_profile=str(dispatch_plan["proposal_profile"]),
                coverage_area=str(unit["coverage_area"]),
                workspace_ref=str(unit["execution_workspace_ref"]),
                selected_workspace_root=str(unit["selected_workspace_root"]),
                execution_workspace_root=str(execution_root),
                execution_host_ref=str(unit["execution_host_ref"]),
                workspace_scope=workspace_scope,
                sandbox_seed_strategy=str(unit["sandbox_seed_strategy"]),
                target_digest=str(unit["workspace_target_digest"]),
                guardian_agent_id=str(
                    guardian_preseed_gate.get("guardian_agent_id", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
            )
            if workspace_scope == self._policy.external_workspace_scope and not guardian_gate_validation[
                "gate_passed"
            ]:
                raise ValueError(
                    "external workspace dispatch requires a passing guardian preseed gate before seeding"
                )
            workspace_seed_status = "inline"
            workspace_seed_head_commit = ""
            dependency_materialization_status = "inline"
            dependency_materialization_manifest: Dict[str, Any] | None = None
            dependency_materialization_manifest_ref = ""
            dependency_materialization_manifest_digest = ""
            dependency_materialization_file_count = 0
            command_env = env.copy()
            dependency_import_root = ""
            dependency_import_path_order = [str(src_root)]
            dependency_import_precedence_status = YAOYOROZU_INLINE_DEPENDENCY_IMPORT_STATUS
            dependency_import_precedence_bound = True
            if workspace_scope == self._policy.external_workspace_scope:
                workspace_seed_head_commit = self._seed_external_execution_workspace(
                    source_root=repo_root,
                    execution_root=execution_root,
                    target_paths=list(unit["target_paths"]),
                )
                workspace_seed_status = "seeded"
                dependency_materialization_manifest = (
                    self._materialize_external_execution_dependencies(
                        source_root=repo_root,
                        execution_root=execution_root,
                        dispatch_plan_ref=dispatch_plan_ref,
                        dispatch_unit_ref=str(unit["unit_id"]),
                        coverage_area=str(unit["coverage_area"]),
                        dependency_paths=list(unit["dependency_materialization_paths"]),
                    )
                )
                dependency_materialization_status = str(
                    dependency_materialization_manifest["status"]
                )
                dependency_materialization_manifest_ref = str(
                    dependency_materialization_manifest["manifest_ref"]
                )
                dependency_materialization_manifest_digest = str(
                    dependency_materialization_manifest["manifest_digest"]
                )
                dependency_materialization_file_count = int(
                    dependency_materialization_manifest["file_count"]
                )
                materialized_src_root = (
                    execution_root
                    / YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT
                    / "src"
                )
                dependency_import_root = str(materialized_src_root)
                dependency_import_path_order = [dependency_import_root]
                dependency_import_precedence_status = (
                    YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                    if dependency_materialization_status == "materialized"
                    else "blocked"
                )
                dependency_import_precedence_bound = (
                    dependency_import_precedence_status
                    == YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                    and dependency_import_path_order[0] == dependency_import_root
                )
                command_env["PYTHONPATH"] = dependency_import_root
            command = [sys.executable if preview[0] == "python3" else preview[0], *preview[1:]]
            process = subprocess.Popen(
                command,
                cwd=execution_root,
                env=command_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout_text, stderr_text = process.communicate()
            stdout_text = stdout_text.strip()
            stderr_text = stderr_text.strip()
            report: Dict[str, Any]
            try:
                loaded = json.loads(stdout_text) if stdout_text else {}
                report = loaded if isinstance(loaded, dict) else {}
            except json.JSONDecodeError:
                report = {}
            expected_binding_digest = build_worker_report_binding_digest(
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=str(unit["unit_id"]),
                agent_id=str(unit["selected_agent_id"]),
                role_id=str(unit["role_id"]),
                coverage_area=str(unit["coverage_area"]),
                dispatch_profile=str(dispatch_plan["dispatch_profile"]),
                workspace_scope=workspace_scope,
                source_ref=str(unit["source_ref"]),
                workspace_root=str(execution_root),
                target_paths=list(unit["target_paths"]),
            )
            workspace_delta_receipt = build_workspace_delta_receipt(
                workspace_root=execution_root,
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=str(unit["unit_id"]),
                target_paths=list(unit["target_paths"]),
            )
            patch_candidate_receipt = build_patch_candidate_receipt(
                workspace_root=execution_root,
                dispatch_plan_ref=dispatch_plan_ref,
                dispatch_unit_ref=str(unit["unit_id"]),
                source_ref=str(unit["source_ref"]),
                coverage_area=str(unit["coverage_area"]),
                target_paths=list(unit["target_paths"]),
                workspace_delta_receipt=workspace_delta_receipt,
            )
            if not report:
                report = {
                    "kind": YAOYOROZU_WORKER_REPORT_KIND,
                    "report_profile": YAOYOROZU_WORKER_REPORT_PROFILE,
                    "agent_id": unit["selected_agent_id"],
                    "role_id": unit["role_id"],
                    "coverage_area": unit["coverage_area"],
                    "dispatch_profile": dispatch_plan["dispatch_profile"],
                    "workspace_scope": workspace_scope,
                    "dispatch_plan_ref": dispatch_plan_ref,
                    "dispatch_unit_ref": unit["unit_id"],
                    "source_ref": unit["source_ref"],
                    "target_paths": list(unit["target_paths"]),
                    "workspace_root": str(execution_root),
                    "workspace_root_digest": sha256_text(str(execution_root)),
                    "invocation_digest": expected_binding_digest,
                    "target_path_observations": [],
                    "workspace_delta_receipt": workspace_delta_receipt,
                    "patch_candidate_receipt": patch_candidate_receipt,
                    "worker_module_origin": {
                        "profile": self._policy.dependency_module_origin_profile,
                        "module_name": YAOYOROZU_WORKER_MODULE_NAME,
                        "module_file": "",
                        "module_digest": "",
                        "search_path_head": [],
                        "origin_digest": "",
                    },
                    "coverage_evidence": {
                        "expected_target_count": len(unit["target_paths"]),
                        "observed_target_count": 0,
                        "existing_target_count": 0,
                        "all_targets_exist": False,
                        "all_targets_within_workspace": False,
                        "delta_receipt_ref": workspace_delta_receipt["receipt_ref"],
                        "delta_status": workspace_delta_receipt["status"],
                        "changed_path_count": workspace_delta_receipt["changed_path_count"],
                        "delta_scan_profile": YAOYOROZU_WORKER_DELTA_SCAN_PROFILE,
                        "patch_candidate_receipt_ref": patch_candidate_receipt["receipt_ref"],
                        "patch_candidate_status": patch_candidate_receipt["status"],
                        "patch_candidate_count": patch_candidate_receipt["patch_candidate_count"],
                        "patch_candidate_profile": YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE,
                        "patch_priority_profile": YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
                        "highest_patch_priority_tier": patch_candidate_receipt[
                            "highest_priority_tier"
                        ],
                        "highest_patch_priority_score": patch_candidate_receipt[
                            "highest_priority_score"
                        ],
                        "all_delta_entries_materialized": patch_candidate_receipt[
                            "all_delta_entries_materialized"
                        ],
                        "ready_gate": YAOYOROZU_WORKER_READY_GATE_PROFILE,
                    },
                    "status": "failed",
                }
            worker_module_origin = (
                report.get("worker_module_origin", {}) if isinstance(report, Mapping) else {}
            )
            expected_module_origin_root = (
                dependency_import_root
                if workspace_scope == self._policy.external_workspace_scope
                else str(src_root)
            )
            module_origin_validation = self._validate_worker_module_origin(
                worker_module_origin if isinstance(worker_module_origin, Mapping) else {},
                expected_module_root=expected_module_origin_root,
                source_src_root=str(src_root),
                workspace_scope=workspace_scope,
            )
            coverage_evidence = report.get("coverage_evidence", {})
            delta_receipt = report.get("workspace_delta_receipt", {})
            patch_candidate_receipt = report.get("patch_candidate_receipt", {})
            delta_entries = delta_receipt.get("entries", []) if isinstance(delta_receipt, Mapping) else []
            patch_candidates = (
                patch_candidate_receipt.get("patch_candidates", [])
                if isinstance(patch_candidate_receipt, Mapping)
                else []
            )
            report_binding_ok = (
                report.get("report_profile") == YAOYOROZU_WORKER_REPORT_PROFILE
                and report.get("dispatch_plan_ref") == dispatch_plan_ref
                and report.get("dispatch_unit_ref") == unit["unit_id"]
                and report.get("workspace_root") == str(execution_root)
                and report.get("workspace_scope") == workspace_scope
                and report.get("invocation_digest") == expected_binding_digest
                and report.get("source_ref") == unit["source_ref"]
                and report.get("target_paths") == unit["target_paths"]
            )
            delta_receipt_ok = (
                isinstance(delta_receipt, Mapping)
                and delta_receipt.get("kind") == "yaoyorozu_worker_workspace_delta_receipt"
                and delta_receipt.get("profile_id") == YAOYOROZU_WORKER_DELTA_SCAN_PROFILE
                and delta_receipt.get("dispatch_plan_ref") == dispatch_plan_ref
                and delta_receipt.get("dispatch_unit_ref") == unit["unit_id"]
                and delta_receipt.get("workspace_root") == str(execution_root)
                and delta_receipt.get("target_paths") == unit["target_paths"]
                and delta_receipt.get("status") in {"clean", "delta-detected"}
                and isinstance(delta_entries, list)
                and delta_receipt.get("changed_path_count") == len(delta_entries)
                and isinstance(coverage_evidence, Mapping)
                and coverage_evidence.get("delta_receipt_ref") == delta_receipt.get("receipt_ref")
                and coverage_evidence.get("delta_status") == delta_receipt.get("status")
                and coverage_evidence.get("changed_path_count") == delta_receipt.get("changed_path_count")
                and coverage_evidence.get("delta_scan_profile") == YAOYOROZU_WORKER_DELTA_SCAN_PROFILE
            )
            patch_candidate_receipt_ok = (
                isinstance(patch_candidate_receipt, Mapping)
                and patch_candidate_receipt.get("kind") == "yaoyorozu_worker_patch_candidate_receipt"
                and patch_candidate_receipt.get("profile_id")
                == YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE
                and patch_candidate_receipt.get("dispatch_plan_ref") == dispatch_plan_ref
                and patch_candidate_receipt.get("dispatch_unit_ref") == unit["unit_id"]
                and patch_candidate_receipt.get("workspace_root") == str(execution_root)
                and patch_candidate_receipt.get("source_ref") == unit["source_ref"]
                and patch_candidate_receipt.get("coverage_area") == unit["coverage_area"]
                and patch_candidate_receipt.get("target_paths") == unit["target_paths"]
                and patch_candidate_receipt.get("delta_receipt_ref") == delta_receipt.get("receipt_ref")
                and patch_candidate_receipt.get("delta_receipt_digest") == delta_receipt.get("receipt_digest")
                and patch_candidate_receipt.get("status") in {"no-candidates", "candidate-ready"}
                and patch_candidate_receipt.get("priority_profile")
                == YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE
                and patch_candidate_receipt.get("all_delta_entries_materialized") is True
                and isinstance(patch_candidates, list)
                and patch_candidate_receipt.get("patch_candidate_count") == len(patch_candidates)
                and isinstance(patch_candidate_receipt.get("ranked_candidate_ids"), list)
                and patch_candidate_receipt.get("ranked_candidate_ids")
                == [candidate.get("candidate_id") for candidate in patch_candidates]
                and isinstance(coverage_evidence, Mapping)
                and coverage_evidence.get("patch_candidate_receipt_ref")
                == patch_candidate_receipt.get("receipt_ref")
                and coverage_evidence.get("patch_candidate_status") == patch_candidate_receipt.get("status")
                and coverage_evidence.get("patch_candidate_count")
                == patch_candidate_receipt.get("patch_candidate_count")
                and coverage_evidence.get("patch_candidate_profile")
                == YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE
                and coverage_evidence.get("patch_priority_profile")
                == YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE
                and coverage_evidence.get("highest_patch_priority_tier")
                == patch_candidate_receipt.get("highest_priority_tier")
                and coverage_evidence.get("highest_patch_priority_score")
                == patch_candidate_receipt.get("highest_priority_score")
                and coverage_evidence.get("all_delta_entries_materialized") is True
            )
            target_paths_ready = (
                isinstance(coverage_evidence, Mapping)
                and coverage_evidence.get("expected_target_count") == len(unit["target_paths"])
                and coverage_evidence.get("observed_target_count") == len(unit["target_paths"])
                and coverage_evidence.get("existing_target_count") == len(unit["target_paths"])
                and coverage_evidence.get("all_targets_exist") is True
                and coverage_evidence.get("all_targets_within_workspace") is True
                and coverage_evidence.get("ready_gate") == YAOYOROZU_WORKER_READY_GATE_PROFILE
            )

            result = {
                "unit_id": unit["unit_id"],
                "launch_index": launch_index,
                "role_id": unit["role_id"],
                "coverage_area": unit["coverage_area"],
                "selected_agent_id": unit["selected_agent_id"],
                "command_digest": unit["command_digest"],
                "process_id": process.pid,
                "process_status": "completed" if process.returncode == 0 else "failed",
                "exit_code": process.returncode,
                "reported_status": report.get("status", "failed"),
                "stdout_digest": sha256_text(stdout_text),
                "stderr_digest": sha256_text(stderr_text),
                "report_digest": sha256_text(canonical_json(report)),
                "report_binding_ok": report_binding_ok,
                "delta_receipt_ok": delta_receipt_ok,
                "patch_candidate_receipt_ok": patch_candidate_receipt_ok,
                "target_paths_ready": target_paths_ready,
                "workspace_scope": workspace_scope,
                "execution_workspace_ref": unit["execution_workspace_ref"],
                "execution_workspace_root": str(execution_root),
                "selected_workspace_root": str(selected_workspace_root),
                "selected_workspace_role": unit["selected_workspace_role"],
                "execution_host_ref": unit["execution_host_ref"],
                "execution_transport_profile": unit["execution_transport_profile"],
                "sandbox_seed_strategy": unit["sandbox_seed_strategy"],
                "workspace_target_digest": unit["workspace_target_digest"],
                "workspace_seed_status": workspace_seed_status,
                "workspace_seed_head_commit": workspace_seed_head_commit,
                "dependency_materialization_status": dependency_materialization_status,
                "dependency_materialization_manifest_ref": dependency_materialization_manifest_ref,
                "dependency_materialization_manifest_digest": (
                    dependency_materialization_manifest_digest
                ),
                "dependency_materialization_file_count": dependency_materialization_file_count,
                "dependency_materialization_manifest": dependency_materialization_manifest,
                "dependency_import_precedence_profile": (
                    self._policy.dependency_import_precedence_profile
                ),
                "dependency_import_root": dependency_import_root,
                "dependency_import_path_order": dependency_import_path_order,
                "dependency_import_precedence_status": dependency_import_precedence_status,
                "dependency_import_precedence_bound": dependency_import_precedence_bound,
                "dependency_module_origin_profile": module_origin_validation["profile"],
                "dependency_module_origin_path": module_origin_validation["module_file"],
                "dependency_module_origin_digest": module_origin_validation["module_digest"],
                "dependency_module_origin_bound": module_origin_validation["ok"],
                "guardian_preseed_gate": dict(guardian_preseed_gate)
                if isinstance(guardian_preseed_gate, Mapping)
                else {},
                "guardian_preseed_gate_status": (
                    guardian_preseed_gate.get("gate_status", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
                "guardian_preseed_gate_digest": (
                    guardian_preseed_gate.get("gate_digest", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
                "guardian_preseed_gate_bound": guardian_gate_validation["ok"],
                "guardian_oversight_event_ref": (
                    guardian_preseed_gate.get("guardian_oversight_event_ref", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
                "guardian_oversight_event_digest": (
                    guardian_preseed_gate.get("guardian_oversight_event_digest", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
                "guardian_oversight_event_status": (
                    guardian_preseed_gate.get("guardian_oversight_event_status", "")
                    if isinstance(guardian_preseed_gate, Mapping)
                    else ""
                ),
                "guardian_preseed_oversight_bound": (
                    guardian_gate_validation["oversight_event_satisfied"]
                    and guardian_gate_validation["reviewer_network_attested"]
                ),
                "reviewer_network_attested": (
                    guardian_preseed_gate.get("reviewer_network_attested", False)
                    if isinstance(guardian_preseed_gate, Mapping)
                    else False
                ),
                "reviewer_quorum_required": (
                    guardian_preseed_gate.get("reviewer_quorum_required", 0)
                    if isinstance(guardian_preseed_gate, Mapping)
                    else 0
                ),
                "reviewer_quorum_received": (
                    guardian_preseed_gate.get("reviewer_quorum_received", 0)
                    if isinstance(guardian_preseed_gate, Mapping)
                    else 0
                ),
                "report": report,
            }
            if (
                process.returncode != 0
                or report.get("status") != "ready"
                or not report_binding_ok
                or not delta_receipt_ok
                or not patch_candidate_receipt_ok
                or not target_paths_ready
                or not module_origin_validation["ok"]
            ):
                failed_role_ids.append(str(unit["role_id"]))
            results.append(result)

        highest_patch_priority_score = max(
            (
                int(
                    result["report"]["patch_candidate_receipt"].get("highest_priority_score", 0)
                )
                for result in results
            ),
            default=0,
        )
        highest_patch_priority_tier = max(
            (
                str(
                    result["report"]["patch_candidate_receipt"].get(
                        "highest_priority_tier",
                        "none",
                    )
                )
                for result in results
            ),
            key=lambda tier: YAOYOROZU_PATCH_PRIORITY_TIER_ORDER.get(tier, -1),
            default="none",
        )

        execution_summary = {
            "launched_process_count": len(results),
            "completed_process_count": sum(
                1 for result in results if result["process_status"] == "completed"
            ),
            "successful_process_count": sum(
                1
                for result in results
                if result["process_status"] == "completed"
                and result["exit_code"] == 0
                and result["reported_status"] == "ready"
                and result["report_binding_ok"]
                and result["delta_receipt_ok"]
                and result["patch_candidate_receipt_ok"]
                and result["target_paths_ready"]
                and result["dependency_module_origin_bound"]
            ),
            "failed_role_ids": failed_role_ids,
            "required_coverage_areas": list(dispatch_plan["selection_summary"]["required_coverage_areas"]),
            "optional_coverage_areas": list(dispatch_plan["selection_summary"]["optional_coverage_areas"]),
            "requested_optional_coverage_areas": list(
                dispatch_plan["selection_summary"]["requested_optional_coverage_areas"]
            ),
            "dispatch_coverage_areas": list(
                dispatch_plan["selection_summary"]["dispatch_coverage_areas"]
            ),
            "coverage_areas": [str(result["coverage_area"]) for result in results],
            "candidate_bound_success_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["process_status"] == "completed"
                and result["exit_code"] == 0
                and result["reported_status"] == "ready"
                and result["dependency_module_origin_bound"]
            ),
            "source_bound_success_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.worker_workspace_scope
                and result["process_status"] == "completed"
                and result["exit_code"] == 0
                and result["reported_status"] == "ready"
                and result["dependency_module_origin_bound"]
            ),
            "target_ready_count": sum(1 for result in results if result["target_paths_ready"]),
            "delta_bound_count": sum(1 for result in results if result["delta_receipt_ok"]),
            "patch_candidate_bound_count": sum(
                1 for result in results if result["patch_candidate_receipt_ok"]
            ),
            "ready_gate_profile": YAOYOROZU_WORKER_READY_GATE_PROFILE,
            "delta_scan_profile": YAOYOROZU_WORKER_DELTA_SCAN_PROFILE,
            "patch_candidate_profile": YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE,
            "patch_priority_profile": YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
            "highest_patch_priority_tier": highest_patch_priority_tier,
            "highest_patch_priority_score": highest_patch_priority_score,
            "preseed_gate_profile": self._policy.workspace_guardian_gate_profile,
            "preseed_oversight_binding_profile": (
                YAOYOROZU_WORKSPACE_GUARDIAN_OVERSIGHT_BINDING_PROFILE
            ),
            "guardian_preseed_gate_count": len(results),
            "external_preseed_gate_pass_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["guardian_preseed_gate_bound"]
                and result["guardian_preseed_gate_status"] == "pass"
            ),
            "guardian_preseed_oversight_event_count": sum(
                1 for result in results if result["guardian_oversight_event_ref"]
            ),
            "external_preseed_oversight_satisfied_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["guardian_preseed_oversight_bound"]
                and result["guardian_oversight_event_status"] == "satisfied"
                and result["reviewer_network_attested"]
            ),
            "dependency_materialization_profile": self._policy.dependency_materialization_profile,
            "dependency_materialization_strategy": (
                self._policy.external_dependency_materialization_strategy
            ),
            "dependency_materialization_required_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
            ),
            "external_dependency_materialized_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["dependency_materialization_status"] == "materialized"
                and result["dependency_materialization_file_count"]
                == len(self._policy.dependency_materialization_paths)
            ),
            "dependency_materialization_file_count": sum(
                int(result["dependency_materialization_file_count"]) for result in results
            ),
            "dependency_lockfile_profile": self._policy.dependency_lockfile_profile,
            "external_dependency_lockfile_attested_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and isinstance(result["dependency_materialization_manifest"], Mapping)
                and result["dependency_materialization_manifest"].get("lockfile_status")
                == "attested"
                and bool(result["dependency_materialization_manifest"].get("lockfile_digest"))
            ),
            "dependency_wheel_attestation_profile": (
                self._policy.dependency_wheel_attestation_profile
            ),
            "external_dependency_wheel_attested_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and isinstance(result["dependency_materialization_manifest"], Mapping)
                and result["dependency_materialization_manifest"].get(
                    "wheel_artifact_status"
                )
                == "attested"
                and bool(
                    result["dependency_materialization_manifest"].get(
                        "wheel_attestation_digest"
                    )
                )
            ),
            "dependency_import_precedence_profile": (
                self._policy.dependency_import_precedence_profile
            ),
            "external_dependency_import_precedence_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["dependency_import_precedence_bound"]
                and result["dependency_import_precedence_status"]
                == YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
            ),
            "dependency_module_origin_profile": self._policy.dependency_module_origin_profile,
            "external_dependency_module_origin_count": sum(
                1
                for result in results
                if result["workspace_scope"] == self._policy.external_workspace_scope
                and result["dependency_module_origin_bound"]
            ),
        }
        validation = {
            "command_digests_match": all(
                any(
                    isinstance(unit, Mapping)
                    and unit.get("unit_id") == result["unit_id"]
                    and unit.get("command_digest") == result["command_digest"]
                    for unit in units
                )
                for result in results
            ),
            "all_processes_exited_zero": all(result["exit_code"] == 0 for result in results),
            "all_reports_ready": all(result["reported_status"] == "ready" for result in results),
            "same_host_scope_only": all(
                result["workspace_scope"]
                in {self._policy.worker_workspace_scope, self._policy.external_workspace_scope}
                for result in results
            ),
            "external_workspace_seeded": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or (
                        result["workspace_seed_status"] == "seeded"
                        and len(result["workspace_seed_head_commit"]) == 40
                    )
                )
                for result in results
            ),
            "external_dependencies_materialized": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or (
                        result["dependency_materialization_status"] == "materialized"
                        and result["dependency_materialization_manifest_ref"]
                        and result["dependency_materialization_manifest_digest"]
                        and result["dependency_materialization_file_count"]
                        == len(self._policy.dependency_materialization_paths)
                    )
                )
                for result in results
            ),
            "external_dependency_lockfile_attested": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or (
                        isinstance(result["dependency_materialization_manifest"], Mapping)
                        and result["dependency_materialization_manifest"].get(
                            "lockfile_profile"
                        )
                        == self._policy.dependency_lockfile_profile
                        and result["dependency_materialization_manifest"].get(
                            "lockfile_status"
                        )
                        == "attested"
                        and bool(
                            result["dependency_materialization_manifest"].get(
                                "lockfile_digest"
                            )
                        )
                    )
                )
                for result in results
            ),
            "external_dependency_wheel_attested": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or (
                        isinstance(result["dependency_materialization_manifest"], Mapping)
                        and result["dependency_materialization_manifest"].get(
                            "wheel_attestation_profile"
                        )
                        == self._policy.dependency_wheel_attestation_profile
                        and result["dependency_materialization_manifest"].get(
                            "wheel_artifact_status"
                        )
                        == "attested"
                        and bool(
                            result["dependency_materialization_manifest"].get(
                                "wheel_attestation_digest"
                            )
                        )
                    )
                )
                for result in results
            ),
            "external_dependency_import_precedence_bound": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or (
                        result["dependency_import_precedence_bound"]
                        and result["dependency_import_precedence_status"]
                        == YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                        and result["dependency_import_path_order"]
                        and len(result["dependency_import_path_order"]) == 1
                        and result["dependency_import_path_order"][0]
                        == result["dependency_import_root"]
                    )
                )
                for result in results
            ),
            "external_dependency_module_origin_bound": all(
                (
                    result["workspace_scope"] != self._policy.external_workspace_scope
                    or result["dependency_module_origin_bound"]
                )
                for result in results
            ),
            "profile_coverage_bound": (
                execution_summary["required_coverage_areas"]
                == list(dispatch_plan["selection_summary"]["required_coverage_areas"])
                and execution_summary["optional_coverage_areas"]
                == list(dispatch_plan["selection_summary"]["optional_coverage_areas"])
                and execution_summary["requested_optional_coverage_areas"]
                == list(dispatch_plan["selection_summary"]["requested_optional_coverage_areas"])
                and execution_summary["dispatch_coverage_areas"]
                == list(dispatch_plan["selection_summary"]["dispatch_coverage_areas"])
            ),
            "coverage_complete": sorted(execution_summary["coverage_areas"])
            == sorted(execution_summary["dispatch_coverage_areas"]),
            "all_reports_bound_to_dispatch": all(
                result["report_binding_ok"] for result in results
            ),
            "all_delta_receipts_bound": all(
                result["delta_receipt_ok"] for result in results
            ),
            "all_patch_candidate_receipts_bound": all(
                result["patch_candidate_receipt_ok"] for result in results
            ),
            "all_target_paths_ready": all(result["target_paths_ready"] for result in results),
            "all_guardian_preseed_gates_bound": all(
                result["guardian_preseed_gate_bound"] for result in results
            ),
            "all_external_preseed_gates_passed": all(
                result["workspace_scope"] != self._policy.external_workspace_scope
                or result["guardian_preseed_gate_status"] == "pass"
                for result in results
            ),
            "guardian_preseed_oversight_bound": all(
                result["guardian_preseed_oversight_bound"] for result in results
            ),
            "all_external_preseed_oversight_satisfied": all(
                result["workspace_scope"] != self._policy.external_workspace_scope
                or (
                    result["guardian_oversight_event_status"] == "satisfied"
                    and result["reviewer_network_attested"]
                    and result["guardian_preseed_oversight_bound"]
                )
                for result in results
            ),
        }
        validation["ok"] = all(validation.values())
        receipt = {
            "kind": "yaoyorozu_worker_dispatch_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("yaoyorozu-dispatch-receipt"),
            "executed_at": utc_now_iso(),
            "dispatch_plan_ref": f"dispatch://{dispatch_plan['dispatch_id']}",
            "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
            "dispatch_profile": dispatch_plan["dispatch_profile"],
            "execution_profile": self._policy.worker_execution_profile,
            "proposal_profile": dispatch_plan["proposal_profile"],
            "workspace_root": str(repo_root),
            "results": results,
            "execution_summary": execution_summary,
            "validation": validation,
        }
        receipt["receipt_digest"] = sha256_text(canonical_json(_dispatch_receipt_digest_payload(receipt)))
        return receipt

    def validate_worker_dispatch_receipt(
        self,
        dispatch_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        results = dispatch_receipt.get("results", [])
        if dispatch_receipt.get("kind") != "yaoyorozu_worker_dispatch_receipt":
            errors.append("kind must equal yaoyorozu_worker_dispatch_receipt")
        if dispatch_receipt.get("dispatch_profile") != self._policy.worker_dispatch_profile:
            errors.append("dispatch_profile mismatch")
        if dispatch_receipt.get("execution_profile") != self._policy.worker_execution_profile:
            errors.append("execution_profile mismatch")
        proposal_profile = dispatch_receipt.get("proposal_profile")
        if proposal_profile not in self._policy.council_profiles:
            errors.append("proposal_profile must map to one supported proposal profile")
            expected_profile_policy = {}
        else:
            expected_profile_policy = self._proposal_profile_policy(str(proposal_profile))
        if not isinstance(results, list) or not results:
            errors.append("results must be a non-empty list")
            results = []
        execution_summary = dispatch_receipt.get("execution_summary", {})
        if not isinstance(execution_summary, Mapping):
            errors.append("execution_summary must be a mapping")
            execution_summary = {}
        required_coverage = execution_summary.get("required_coverage_areas", [])
        optional_coverage = execution_summary.get("optional_coverage_areas", [])
        requested_optional_coverage = execution_summary.get("requested_optional_coverage_areas", [])
        dispatch_coverage = execution_summary.get("dispatch_coverage_areas", [])
        if not isinstance(required_coverage, list) or not required_coverage:
            errors.append("execution_summary.required_coverage_areas must be a non-empty list")
            required_coverage = []
        if not isinstance(optional_coverage, list):
            errors.append("execution_summary.optional_coverage_areas must be a list")
            optional_coverage = []
        if not isinstance(requested_optional_coverage, list):
            errors.append("execution_summary.requested_optional_coverage_areas must be a list")
            requested_optional_coverage = []
        if not isinstance(dispatch_coverage, list) or not dispatch_coverage:
            errors.append("execution_summary.dispatch_coverage_areas must be a non-empty list")
            dispatch_coverage = []
        if expected_profile_policy:
            if required_coverage != expected_profile_policy["required_worker_coverage_areas"]:
                errors.append("execution_summary.required_coverage_areas mismatch")
            if optional_coverage != expected_profile_policy["optional_worker_coverage_areas"]:
                errors.append("execution_summary.optional_coverage_areas mismatch")
            normalized_requested_optional = self._normalize_requested_optional_coverage_areas(
                str(proposal_profile),
                requested_optional_coverage,
            )
            if requested_optional_coverage != normalized_requested_optional:
                errors.append("execution_summary.requested_optional_coverage_areas mismatch")
            if dispatch_coverage != self._dispatch_coverage_areas(
                str(proposal_profile),
                requested_optional_coverage,
            ):
                errors.append("execution_summary.dispatch_coverage_areas mismatch")
        else:
            normalized_requested_optional = []

        coverage_areas: List[str] = []
        candidate_bound_success_count = 0
        source_bound_success_count = 0
        completed_process_count = 0
        failed_role_ids: List[str] = []
        target_ready_count = 0
        delta_bound_count = 0
        patch_candidate_bound_count = 0
        guardian_preseed_gate_count = 0
        external_preseed_gate_pass_count = 0
        guardian_preseed_oversight_event_count = 0
        external_preseed_oversight_satisfied_count = 0
        dependency_materialization_required_count = 0
        external_dependency_materialized_count = 0
        dependency_materialization_file_count = 0
        external_dependency_lockfile_attested_count = 0
        external_dependency_wheel_attested_count = 0
        external_dependency_import_precedence_count = 0
        external_dependency_module_origin_count = 0
        external_dependency_module_origin_bound = True
        source_src_root = str(
            Path(str(dispatch_receipt.get("workspace_root", ""))).resolve() / "src"
        )
        for result in results:
            if not isinstance(result, Mapping):
                errors.append("results entries must be mappings")
                continue
            coverage_areas.append(str(result.get("coverage_area", "")))
            if result.get("process_status") == "completed":
                completed_process_count += 1
            workspace_scope = result.get("workspace_scope")
            if workspace_scope not in {
                self._policy.worker_workspace_scope,
                self._policy.external_workspace_scope,
            }:
                errors.append("worker result workspace_scope must stay within the same-host policy")
            execution_workspace_ref = str(result.get("execution_workspace_ref", "")).strip()
            if not execution_workspace_ref:
                errors.append("worker result execution_workspace_ref must be a non-empty string")
            execution_workspace_root = str(result.get("execution_workspace_root", "")).strip()
            if not execution_workspace_root:
                errors.append("worker result execution_workspace_root must be a non-empty string")
            selected_workspace_root = str(result.get("selected_workspace_root", "")).strip()
            if not selected_workspace_root:
                errors.append("worker result selected_workspace_root must be a non-empty string")
            selected_workspace_role = str(result.get("selected_workspace_role", "")).strip()
            if not selected_workspace_role:
                errors.append("worker result selected_workspace_role must be a non-empty string")
            execution_host_ref = str(result.get("execution_host_ref", "")).strip()
            if execution_host_ref != self._policy.workspace_discovery_host_ref:
                errors.append("worker result execution_host_ref mismatch")
            if result.get("execution_transport_profile") != self._policy.workspace_execution_transport_profile:
                errors.append("worker result execution_transport_profile mismatch")
            sandbox_seed_strategy = result.get("sandbox_seed_strategy")
            if sandbox_seed_strategy not in {
                self._policy.inline_workspace_seed_strategy,
                self._policy.external_workspace_seed_strategy,
            }:
                errors.append("worker result sandbox_seed_strategy mismatch")
            workspace_seed_status = result.get("workspace_seed_status")
            workspace_seed_head_commit = str(result.get("workspace_seed_head_commit", "")).strip()
            if workspace_scope == self._policy.external_workspace_scope:
                expected_module_digest = ""
                if workspace_seed_status != "seeded":
                    errors.append("external workspace results must record workspace_seed_status=seeded")
                if len(workspace_seed_head_commit) != 40:
                    errors.append("external workspace results must record a 40-char workspace_seed_head_commit")
                dependency_materialization_required_count += 1
                dependency_validation = self._validate_dependency_materialization_manifest(
                    result.get("dependency_materialization_manifest"),
                    dispatch_plan_ref=str(dispatch_receipt.get("dispatch_plan_ref", "")),
                    dispatch_unit_ref=str(result.get("unit_id", "")),
                    coverage_area=str(result.get("coverage_area", "")),
                    workspace_root=execution_workspace_root,
                )
                if not dependency_validation["ok"]:
                    errors.extend(dependency_validation["errors"])
                if result.get("dependency_materialization_status") != dependency_validation["status"]:
                    errors.append("worker result dependency_materialization_status mismatch")
                if (
                    result.get("dependency_materialization_manifest_ref")
                    != dependency_validation["manifest_ref"]
                ):
                    errors.append("worker result dependency_materialization_manifest_ref mismatch")
                if (
                    result.get("dependency_materialization_manifest_digest")
                    != dependency_validation["manifest_digest"]
                ):
                    errors.append("worker result dependency_materialization_manifest_digest mismatch")
                if (
                    result.get("dependency_materialization_file_count")
                    != dependency_validation["file_count"]
                ):
                    errors.append("worker result dependency_materialization_file_count mismatch")
                dependency_materialization_file_count += int(
                    dependency_validation["file_count"]
                )
                if (
                    dependency_validation["ok"]
                    and dependency_validation["status"] == "materialized"
                    and dependency_validation["file_count"]
                    == len(self._policy.dependency_materialization_paths)
                ):
                    external_dependency_materialized_count += 1
                if dependency_validation["lockfile_attested"]:
                    external_dependency_lockfile_attested_count += 1
                if dependency_validation["wheel_attested"]:
                    external_dependency_wheel_attested_count += 1
                expected_import_root = str(
                    Path(execution_workspace_root)
                    / YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT
                    / "src"
                )
                dependency_import_path_order = result.get("dependency_import_path_order", [])
                if result.get(
                    "dependency_import_precedence_profile"
                ) != self._policy.dependency_import_precedence_profile:
                    errors.append("worker result dependency_import_precedence_profile mismatch")
                if result.get("dependency_import_root") != expected_import_root:
                    errors.append("external worker dependency_import_root mismatch")
                if not isinstance(dependency_import_path_order, list):
                    errors.append("worker result dependency_import_path_order must be a list")
                    dependency_import_path_order = []
                if (
                    len(dependency_import_path_order) != 1
                    or dependency_import_path_order[0] != expected_import_root
                ):
                    errors.append(
                        "external worker dependency import path order must contain only materialized src"
                    )
                if (
                    result.get("dependency_import_precedence_status")
                    != YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                ):
                    errors.append("external worker dependency_import_precedence_status mismatch")
                if result.get("dependency_import_precedence_bound") is not True:
                    errors.append("external worker dependency_import_precedence_bound must be true")
                if (
                    isinstance(dependency_import_path_order, list)
                    and len(dependency_import_path_order) == 1
                    and dependency_import_path_order[0] == expected_import_root
                    and result.get("dependency_import_precedence_status")
                    == YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                    and result.get("dependency_import_precedence_bound") is True
                ):
                    external_dependency_import_precedence_count += 1
                manifest_for_origin = result.get("dependency_materialization_manifest")
                manifest_files = (
                    manifest_for_origin.get("files", [])
                    if isinstance(manifest_for_origin, Mapping)
                    else []
                )
                for file_entry in manifest_files:
                    if not isinstance(file_entry, Mapping):
                        continue
                    if file_entry.get("source_path") == (
                        f"src/{YAOYOROZU_WORKER_MODULE_RELATIVE_PATH}"
                    ):
                        expected_module_digest = str(
                            file_entry.get("materialized_digest", "")
                        )
                        break
                expected_module_root = expected_import_root
            else:
                expected_module_digest = ""
                if workspace_seed_status != "inline":
                    errors.append("repo-local workspace results must record workspace_seed_status=inline")
                if workspace_seed_head_commit:
                    errors.append("repo-local workspace results must not record workspace_seed_head_commit")
                if result.get("dependency_materialization_status") != "inline":
                    errors.append("repo-local dependency_materialization_status must be inline")
                if result.get("dependency_materialization_manifest_ref") != "":
                    errors.append("repo-local dependency_materialization_manifest_ref must be empty")
                if result.get("dependency_materialization_manifest_digest") != "":
                    errors.append("repo-local dependency_materialization_manifest_digest must be empty")
                if result.get("dependency_materialization_file_count") != 0:
                    errors.append("repo-local dependency_materialization_file_count must be 0")
                if result.get("dependency_materialization_manifest") is not None:
                    errors.append("repo-local dependency_materialization_manifest must be null")
                dependency_import_path_order = result.get("dependency_import_path_order", [])
                if result.get(
                    "dependency_import_precedence_profile"
                ) != self._policy.dependency_import_precedence_profile:
                    errors.append("worker result dependency_import_precedence_profile mismatch")
                if result.get("dependency_import_root") != "":
                    errors.append("repo-local dependency_import_root must be empty")
                if dependency_import_path_order != [source_src_root]:
                    errors.append("repo-local dependency_import_path_order must contain source src only")
                if (
                    result.get("dependency_import_precedence_status")
                    != YAOYOROZU_INLINE_DEPENDENCY_IMPORT_STATUS
                ):
                    errors.append("repo-local dependency_import_precedence_status mismatch")
                if result.get("dependency_import_precedence_bound") is not True:
                    errors.append("repo-local dependency_import_precedence_bound must be true")
                expected_module_root = source_src_root
            report_for_origin = result.get("report", {})
            module_origin = (
                report_for_origin.get("worker_module_origin", {})
                if isinstance(report_for_origin, Mapping)
                else {}
            )
            module_origin_validation = self._validate_worker_module_origin(
                module_origin if isinstance(module_origin, Mapping) else {},
                expected_module_root=expected_module_root,
                source_src_root=source_src_root,
                workspace_scope=str(workspace_scope),
                expected_module_digest=expected_module_digest,
            )
            if not module_origin_validation["ok"]:
                errors.extend(module_origin_validation["errors"])
            if (
                result.get("dependency_module_origin_profile")
                != self._policy.dependency_module_origin_profile
            ):
                errors.append("worker result dependency_module_origin_profile mismatch")
            if (
                result.get("dependency_module_origin_path")
                != module_origin_validation["module_file"]
            ):
                errors.append("worker result dependency_module_origin_path mismatch")
            if (
                result.get("dependency_module_origin_digest")
                != module_origin_validation["module_digest"]
            ):
                errors.append("worker result dependency_module_origin_digest mismatch")
            if result.get("dependency_module_origin_bound") != module_origin_validation["ok"]:
                errors.append("worker result dependency_module_origin_bound mismatch")
            if (
                workspace_scope == self._policy.external_workspace_scope
                and module_origin_validation["ok"]
            ):
                external_dependency_module_origin_count += 1
            if (
                workspace_scope == self._policy.external_workspace_scope
                and not module_origin_validation["ok"]
            ):
                external_dependency_module_origin_bound = False
            workspace_target_digest = str(result.get("workspace_target_digest", "")).strip()
            if len(workspace_target_digest) != 64:
                errors.append("worker result workspace_target_digest must be a sha256 digest")
            guardian_gate = result.get("guardian_preseed_gate", {})
            gate_validation = self._validate_guardian_preseed_gate(
                guardian_gate if isinstance(guardian_gate, Mapping) else {},
                dispatch_plan_ref=str(dispatch_receipt.get("dispatch_plan_ref", "")),
                dispatch_unit_ref=str(result.get("unit_id", "")),
                proposal_profile=str(proposal_profile),
                coverage_area=str(result.get("coverage_area", "")),
                workspace_ref=execution_workspace_ref,
                selected_workspace_root=selected_workspace_root,
                execution_workspace_root=execution_workspace_root,
                execution_host_ref=execution_host_ref,
                workspace_scope=str(workspace_scope),
                sandbox_seed_strategy=str(sandbox_seed_strategy),
                target_digest=workspace_target_digest,
                guardian_agent_id=str(
                    (guardian_gate if isinstance(guardian_gate, Mapping) else {}).get(
                        "guardian_agent_id", ""
                    )
                ),
            )
            guardian_preseed_gate_count += 1
            if not gate_validation["ok"]:
                errors.extend(gate_validation["errors"])
            if result.get("guardian_preseed_gate_bound") != gate_validation["ok"]:
                errors.append("worker result guardian_preseed_gate_bound mismatch")
            if result.get("guardian_preseed_gate_status") != (
                "pass" if gate_validation["gate_required"] else "not-required"
            ):
                errors.append("worker result guardian_preseed_gate_status mismatch")
            if result.get("guardian_preseed_gate_digest") != (
                guardian_gate.get("gate_digest") if isinstance(guardian_gate, Mapping) else ""
            ):
                errors.append("worker result guardian_preseed_gate_digest mismatch")
            if gate_validation["gate_required"] and gate_validation["gate_passed"]:
                external_preseed_gate_pass_count += 1
            gate_event_ref = (
                str(guardian_gate.get("guardian_oversight_event_ref", "")).strip()
                if isinstance(guardian_gate, Mapping)
                else ""
            )
            gate_event_digest = (
                str(guardian_gate.get("guardian_oversight_event_digest", "")).strip()
                if isinstance(guardian_gate, Mapping)
                else ""
            )
            gate_event_status = (
                str(guardian_gate.get("guardian_oversight_event_status", "")).strip()
                if isinstance(guardian_gate, Mapping)
                else ""
            )
            gate_reviewer_network_attested = (
                guardian_gate.get("reviewer_network_attested") is True
                if isinstance(guardian_gate, Mapping)
                else False
            )
            if gate_event_ref:
                guardian_preseed_oversight_event_count += 1
            if (
                gate_validation["gate_required"]
                and gate_validation["oversight_event_satisfied"]
                and gate_validation["reviewer_network_attested"]
            ):
                external_preseed_oversight_satisfied_count += 1
            if result.get("guardian_oversight_event_ref") != gate_event_ref:
                errors.append("worker result guardian_oversight_event_ref mismatch")
            if result.get("guardian_oversight_event_digest") != gate_event_digest:
                errors.append("worker result guardian_oversight_event_digest mismatch")
            if result.get("guardian_oversight_event_status") != gate_event_status:
                errors.append("worker result guardian_oversight_event_status mismatch")
            if result.get("guardian_preseed_oversight_bound") != (
                gate_validation["oversight_event_satisfied"]
                and gate_validation["reviewer_network_attested"]
            ):
                errors.append("worker result guardian_preseed_oversight_bound mismatch")
            if result.get("reviewer_network_attested") is not gate_reviewer_network_attested:
                errors.append("worker result reviewer_network_attested mismatch")
            if result.get("reviewer_quorum_required") != (
                guardian_gate.get("reviewer_quorum_required")
                if isinstance(guardian_gate, Mapping)
                else 0
            ):
                errors.append("worker result reviewer_quorum_required mismatch")
            if result.get("reviewer_quorum_received") != (
                guardian_gate.get("reviewer_quorum_received")
                if isinstance(guardian_gate, Mapping)
                else 0
            ):
                errors.append("worker result reviewer_quorum_received mismatch")
            report = result.get("report", {})
            if not isinstance(report, Mapping):
                errors.append("result.report must be a mapping")
                continue
            if report.get("kind") != YAOYOROZU_WORKER_REPORT_KIND:
                errors.append("worker report kind mismatch")
            if report.get("report_profile") != YAOYOROZU_WORKER_REPORT_PROFILE:
                errors.append("worker report profile mismatch")
            if report.get("status") != "ready":
                errors.append("worker report status must be ready")
            if report.get("workspace_scope") != workspace_scope:
                errors.append("worker report workspace_scope must match the result workspace_scope")
            if report.get("dispatch_profile") != self._policy.worker_dispatch_profile:
                errors.append("worker report dispatch_profile mismatch")
            if report.get("dispatch_plan_ref") != dispatch_receipt.get("dispatch_plan_ref"):
                errors.append("worker report dispatch_plan_ref must match receipt")
            if report.get("workspace_root") != execution_workspace_root:
                errors.append("worker report workspace_root must match execution_workspace_root")
            if result.get("report_binding_ok") is not True:
                errors.append("worker report must remain bound to the dispatch unit")
            if result.get("delta_receipt_ok") is not True:
                errors.append("worker report must keep a dispatch-bound delta receipt")
            if result.get("patch_candidate_receipt_ok") is not True:
                errors.append("worker report must keep a delta-derived patch candidate receipt")
            if result.get("target_paths_ready") is not True:
                errors.append("worker report must prove target path readiness")
            successful_result = (
                result.get("process_status") == "completed"
                and result.get("exit_code") == 0
                and result.get("reported_status") == "ready"
                and result.get("report_binding_ok") is True
                and result.get("delta_receipt_ok") is True
                and result.get("patch_candidate_receipt_ok") is True
                and result.get("target_paths_ready") is True
                and result.get("dependency_module_origin_bound") is True
            )
            if successful_result and workspace_scope == self._policy.external_workspace_scope:
                candidate_bound_success_count += 1
            elif successful_result and workspace_scope == self._policy.worker_workspace_scope:
                source_bound_success_count += 1
            if not successful_result:
                failed_role_ids.append(str(result.get("role_id", "")))
            if result.get("target_paths_ready") is True:
                target_ready_count += 1
            if result.get("delta_receipt_ok") is True:
                delta_bound_count += 1
            if result.get("patch_candidate_receipt_ok") is True:
                patch_candidate_bound_count += 1
            coverage_evidence = report.get("coverage_evidence", {})
            if not isinstance(coverage_evidence, Mapping):
                errors.append("worker report coverage_evidence must be a mapping")
            else:
                if coverage_evidence.get("ready_gate") != YAOYOROZU_WORKER_READY_GATE_PROFILE:
                    errors.append("worker report ready_gate mismatch")
                if coverage_evidence.get("all_targets_exist") is not True:
                    errors.append("worker report must confirm all target paths exist")
                if coverage_evidence.get("all_targets_within_workspace") is not True:
                    errors.append("worker report must confirm workspace-bounded target paths")
                if coverage_evidence.get("delta_scan_profile") != YAOYOROZU_WORKER_DELTA_SCAN_PROFILE:
                    errors.append("worker report delta_scan_profile mismatch")
                if (
                    coverage_evidence.get("patch_candidate_profile")
                    != YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE
                ):
                    errors.append("worker report patch_candidate_profile mismatch")
                if (
                    coverage_evidence.get("patch_priority_profile")
                    != YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE
                ):
                    errors.append("worker report patch_priority_profile mismatch")
                if coverage_evidence.get("all_delta_entries_materialized") is not True:
                    errors.append("worker report must fully materialize delta entries into patch candidates")
            delta_receipt = report.get("workspace_delta_receipt", {})
            if not isinstance(delta_receipt, Mapping):
                errors.append("worker report workspace_delta_receipt must be a mapping")
            else:
                if delta_receipt.get("kind") != "yaoyorozu_worker_workspace_delta_receipt":
                    errors.append("worker delta receipt kind mismatch")
                if delta_receipt.get("profile_id") != YAOYOROZU_WORKER_DELTA_SCAN_PROFILE:
                    errors.append("worker delta receipt profile mismatch")
                if delta_receipt.get("dispatch_plan_ref") != dispatch_receipt.get("dispatch_plan_ref"):
                    errors.append("worker delta receipt dispatch_plan_ref must match receipt")
                if delta_receipt.get("dispatch_unit_ref") != result.get("unit_id"):
                    errors.append("worker delta receipt dispatch_unit_ref must match the result unit")
                if delta_receipt.get("workspace_root") != execution_workspace_root:
                    errors.append("worker delta receipt workspace_root must match execution_workspace_root")
                if delta_receipt.get("status") not in {"clean", "delta-detected"}:
                    errors.append("worker delta receipt must stay clean or delta-detected")
                entries = delta_receipt.get("entries", [])
                if not isinstance(entries, list):
                    errors.append("worker delta receipt entries must be a list")
                elif delta_receipt.get("changed_path_count") != len(entries):
                    errors.append("worker delta receipt changed_path_count must match entries")
                if coverage_evidence.get("delta_receipt_ref") != delta_receipt.get("receipt_ref"):
                    errors.append("worker report must bind the delta receipt ref")
                if coverage_evidence.get("delta_status") != delta_receipt.get("status"):
                    errors.append("worker report must bind the delta receipt status")
                if coverage_evidence.get("changed_path_count") != delta_receipt.get("changed_path_count"):
                    errors.append("worker report must bind the delta receipt changed_path_count")
            patch_candidate_receipt = report.get("patch_candidate_receipt", {})
            if not isinstance(patch_candidate_receipt, Mapping):
                errors.append("worker report patch_candidate_receipt must be a mapping")
            else:
                if patch_candidate_receipt.get("kind") != "yaoyorozu_worker_patch_candidate_receipt":
                    errors.append("worker patch candidate receipt kind mismatch")
                if (
                    patch_candidate_receipt.get("profile_id")
                    != YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE
                ):
                    errors.append("worker patch candidate receipt profile mismatch")
                if patch_candidate_receipt.get("dispatch_plan_ref") != dispatch_receipt.get("dispatch_plan_ref"):
                    errors.append("worker patch candidate receipt dispatch_plan_ref must match receipt")
                if patch_candidate_receipt.get("dispatch_unit_ref") != result.get("unit_id"):
                    errors.append("worker patch candidate receipt dispatch_unit_ref must match the result unit")
                if patch_candidate_receipt.get("workspace_root") != execution_workspace_root:
                    errors.append(
                        "worker patch candidate receipt workspace_root must match execution_workspace_root"
                    )
                if patch_candidate_receipt.get("status") not in {"no-candidates", "candidate-ready"}:
                    errors.append("worker patch candidate receipt must stay no-candidates or candidate-ready")
                if (
                    patch_candidate_receipt.get("priority_profile")
                    != YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE
                ):
                    errors.append("worker patch candidate receipt priority_profile mismatch")
                if patch_candidate_receipt.get("all_delta_entries_materialized") is not True:
                    errors.append("worker patch candidate receipt must fully materialize delta entries")
                candidates = patch_candidate_receipt.get("patch_candidates", [])
                if not isinstance(candidates, list):
                    errors.append("worker patch candidate receipt patch_candidates must be a list")
                elif patch_candidate_receipt.get("patch_candidate_count") != len(candidates):
                    errors.append(
                        "worker patch candidate receipt patch_candidate_count must match patch_candidates"
                    )
                ranked_candidate_ids = patch_candidate_receipt.get("ranked_candidate_ids", [])
                if not isinstance(ranked_candidate_ids, list):
                    errors.append("worker patch candidate receipt ranked_candidate_ids must be a list")
                    ranked_candidate_ids = []
                elif ranked_candidate_ids != [
                    candidate.get("candidate_id")
                    for candidate in candidates
                    if isinstance(candidate, Mapping)
                ]:
                    errors.append("worker patch candidate receipt ranked_candidate_ids must match candidate order")
                expected_highest_tier = (
                    candidates[0].get("priority_tier") if candidates and isinstance(candidates[0], Mapping) else "none"
                )
                expected_highest_score = (
                    candidates[0].get("priority_score") if candidates and isinstance(candidates[0], Mapping) else 0
                )
                if patch_candidate_receipt.get("highest_priority_tier") != expected_highest_tier:
                    errors.append("worker patch candidate receipt highest_priority_tier mismatch")
                if patch_candidate_receipt.get("highest_priority_score") != expected_highest_score:
                    errors.append("worker patch candidate receipt highest_priority_score mismatch")
                for priority_rank, candidate in enumerate(candidates, start=1):
                    if not isinstance(candidate, Mapping):
                        errors.append("worker patch candidate entries must remain mappings")
                        continue
                    if candidate.get("priority_rank") != priority_rank:
                        errors.append("worker patch candidate priority_rank must preserve candidate order")
                    if candidate.get("priority_tier") not in YAOYOROZU_PATCH_PRIORITY_TIER_ORDER:
                        errors.append("worker patch candidate priority_tier is invalid")
                    if not isinstance(candidate.get("priority_reason"), str) or not str(
                        candidate.get("priority_reason")
                    ).strip():
                        errors.append("worker patch candidate priority_reason must be a non-empty string")
                if patch_candidate_receipt.get("delta_receipt_ref") != delta_receipt.get("receipt_ref"):
                    errors.append("worker patch candidate receipt must bind the delta receipt ref")
                if patch_candidate_receipt.get("delta_receipt_digest") != delta_receipt.get("receipt_digest"):
                    errors.append("worker patch candidate receipt must bind the delta receipt digest")
                if (
                    coverage_evidence.get("patch_candidate_receipt_ref")
                    != patch_candidate_receipt.get("receipt_ref")
                ):
                    errors.append("worker report must bind the patch candidate receipt ref")
                if coverage_evidence.get("patch_candidate_status") != patch_candidate_receipt.get("status"):
                    errors.append("worker report must bind the patch candidate receipt status")
                if (
                    coverage_evidence.get("patch_candidate_count")
                    != patch_candidate_receipt.get("patch_candidate_count")
                ):
                    errors.append("worker report must bind the patch candidate count")
                if (
                    coverage_evidence.get("highest_patch_priority_tier")
                    != patch_candidate_receipt.get("highest_priority_tier")
                ):
                    errors.append("worker report must bind the highest patch priority tier")
                if (
                    coverage_evidence.get("highest_patch_priority_score")
                    != patch_candidate_receipt.get("highest_priority_score")
                ):
                    errors.append("worker report must bind the highest patch priority score")
            if result.get("exit_code") != 0:
                errors.append("worker process exit_code must be 0")

        missing_coverage = [coverage for coverage in dispatch_coverage if coverage not in coverage_areas]
        unexpected_coverage = [
            coverage for coverage in coverage_areas if coverage not in dispatch_coverage
        ]
        if execution_summary.get("coverage_areas") != coverage_areas:
            errors.append("execution_summary.coverage_areas must match result coverage order")
        if execution_summary.get("patch_priority_profile") != YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE:
            errors.append("execution_summary.patch_priority_profile mismatch")
        expected_highest_patch_priority_score = max(
            (
                int(
                    result.get("report", {})
                    .get("patch_candidate_receipt", {})
                    .get("highest_priority_score", 0)
                )
                for result in results
                if isinstance(result, Mapping)
            ),
            default=0,
        )
        expected_highest_patch_priority_tier = max(
            (
                str(
                    result.get("report", {})
                    .get("patch_candidate_receipt", {})
                    .get("highest_priority_tier", "none")
                )
                for result in results
                if isinstance(result, Mapping)
            ),
            key=lambda tier: YAOYOROZU_PATCH_PRIORITY_TIER_ORDER.get(tier, -1),
            default="none",
        )
        if execution_summary.get("highest_patch_priority_score") != expected_highest_patch_priority_score:
            errors.append("execution_summary.highest_patch_priority_score mismatch")
        if execution_summary.get("highest_patch_priority_tier") != expected_highest_patch_priority_tier:
            errors.append("execution_summary.highest_patch_priority_tier mismatch")
        success_count = (
            candidate_bound_success_count + source_bound_success_count
        )
        if execution_summary.get("launched_process_count") != len(results):
            errors.append("execution_summary.launched_process_count must match results")
        if execution_summary.get("completed_process_count") != completed_process_count:
            errors.append("execution_summary.completed_process_count mismatch")
        if execution_summary.get("successful_process_count") != success_count:
            errors.append("execution_summary.successful_process_count mismatch")
        if execution_summary.get("failed_role_ids") != failed_role_ids:
            errors.append("execution_summary.failed_role_ids must match failed results")
        if execution_summary.get("candidate_bound_success_count") != candidate_bound_success_count:
            errors.append("execution_summary.candidate_bound_success_count mismatch")
        if execution_summary.get("source_bound_success_count") != source_bound_success_count:
            errors.append("execution_summary.source_bound_success_count mismatch")
        if execution_summary.get("target_ready_count") != target_ready_count:
            errors.append("execution_summary.target_ready_count mismatch")
        if execution_summary.get("delta_bound_count") != delta_bound_count:
            errors.append("execution_summary.delta_bound_count mismatch")
        if execution_summary.get("patch_candidate_bound_count") != patch_candidate_bound_count:
            errors.append("execution_summary.patch_candidate_bound_count mismatch")
        if execution_summary.get("ready_gate_profile") != YAOYOROZU_WORKER_READY_GATE_PROFILE:
            errors.append("execution_summary.ready_gate_profile mismatch")
        if execution_summary.get("delta_scan_profile") != YAOYOROZU_WORKER_DELTA_SCAN_PROFILE:
            errors.append("execution_summary.delta_scan_profile mismatch")
        if (
            execution_summary.get("patch_candidate_profile")
            != YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE
        ):
            errors.append("execution_summary.patch_candidate_profile mismatch")
        if execution_summary.get("preseed_gate_profile") != self._policy.workspace_guardian_gate_profile:
            errors.append("execution_summary.preseed_gate_profile mismatch")
        if (
            execution_summary.get("preseed_oversight_binding_profile")
            != YAOYOROZU_WORKSPACE_GUARDIAN_OVERSIGHT_BINDING_PROFILE
        ):
            errors.append("execution_summary.preseed_oversight_binding_profile mismatch")
        if execution_summary.get("guardian_preseed_gate_count") != guardian_preseed_gate_count:
            errors.append("execution_summary.guardian_preseed_gate_count mismatch")
        if (
            execution_summary.get("external_preseed_gate_pass_count")
            != external_preseed_gate_pass_count
        ):
            errors.append("execution_summary.external_preseed_gate_pass_count mismatch")
        if (
            execution_summary.get("guardian_preseed_oversight_event_count")
            != guardian_preseed_oversight_event_count
        ):
            errors.append("execution_summary.guardian_preseed_oversight_event_count mismatch")
        if (
            execution_summary.get("external_preseed_oversight_satisfied_count")
            != external_preseed_oversight_satisfied_count
        ):
            errors.append(
                "execution_summary.external_preseed_oversight_satisfied_count mismatch"
            )
        if (
            execution_summary.get("dependency_materialization_profile")
            != self._policy.dependency_materialization_profile
        ):
            errors.append("execution_summary.dependency_materialization_profile mismatch")
        if (
            execution_summary.get("dependency_materialization_strategy")
            != self._policy.external_dependency_materialization_strategy
        ):
            errors.append("execution_summary.dependency_materialization_strategy mismatch")
        if (
            execution_summary.get("dependency_materialization_required_count")
            != dependency_materialization_required_count
        ):
            errors.append("execution_summary.dependency_materialization_required_count mismatch")
        if (
            execution_summary.get("external_dependency_materialized_count")
            != external_dependency_materialized_count
        ):
            errors.append("execution_summary.external_dependency_materialized_count mismatch")
        if (
            execution_summary.get("dependency_materialization_file_count")
            != dependency_materialization_file_count
        ):
            errors.append("execution_summary.dependency_materialization_file_count mismatch")
        if (
            execution_summary.get("dependency_lockfile_profile")
            != self._policy.dependency_lockfile_profile
        ):
            errors.append("execution_summary.dependency_lockfile_profile mismatch")
        if (
            execution_summary.get("external_dependency_lockfile_attested_count")
            != external_dependency_lockfile_attested_count
        ):
            errors.append(
                "execution_summary.external_dependency_lockfile_attested_count mismatch"
            )
        if (
            execution_summary.get("dependency_wheel_attestation_profile")
            != self._policy.dependency_wheel_attestation_profile
        ):
            errors.append("execution_summary.dependency_wheel_attestation_profile mismatch")
        if (
            execution_summary.get("external_dependency_wheel_attested_count")
            != external_dependency_wheel_attested_count
        ):
            errors.append(
                "execution_summary.external_dependency_wheel_attested_count mismatch"
            )
        if (
            execution_summary.get("dependency_import_precedence_profile")
            != self._policy.dependency_import_precedence_profile
        ):
            errors.append("execution_summary.dependency_import_precedence_profile mismatch")
        if (
            execution_summary.get("external_dependency_import_precedence_count")
            != external_dependency_import_precedence_count
        ):
            errors.append("execution_summary.external_dependency_import_precedence_count mismatch")
        if (
            execution_summary.get("dependency_module_origin_profile")
            != self._policy.dependency_module_origin_profile
        ):
            errors.append("execution_summary.dependency_module_origin_profile mismatch")
        if (
            execution_summary.get("external_dependency_module_origin_count")
            != external_dependency_module_origin_count
        ):
            errors.append("execution_summary.external_dependency_module_origin_count mismatch")
        validation = dispatch_receipt.get("validation", {})
        if not isinstance(validation, Mapping):
            errors.append("validation must be a mapping")
            validation = {}
        expected_validation = {
            "command_digests_match": all(
                isinstance(result, Mapping) and str(result.get("command_digest", "")).strip()
                for result in results
            ),
            "all_processes_exited_zero": all(result.get("exit_code") == 0 for result in results),
            "all_reports_ready": all(result.get("reported_status") == "ready" for result in results),
            "same_host_scope_only": all(
                result.get("workspace_scope")
                in {self._policy.worker_workspace_scope, self._policy.external_workspace_scope}
                for result in results
            ),
            "external_workspace_seeded": all(
                result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    result.get("workspace_seed_status") == "seeded"
                    and len(str(result.get("workspace_seed_head_commit", "")).strip()) == 40
                )
                for result in results
            ),
            "external_dependencies_materialized": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    result.get("dependency_materialization_status") == "materialized"
                    and result.get("dependency_materialization_manifest_ref")
                    and result.get("dependency_materialization_manifest_digest")
                    and result.get("dependency_materialization_file_count")
                    == len(self._policy.dependency_materialization_paths)
                )
                for result in results
            ),
            "external_dependency_lockfile_attested": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    isinstance(result.get("dependency_materialization_manifest"), Mapping)
                    and result["dependency_materialization_manifest"].get(
                        "lockfile_profile"
                    )
                    == self._policy.dependency_lockfile_profile
                    and result["dependency_materialization_manifest"].get(
                        "lockfile_status"
                    )
                    == "attested"
                    and bool(
                        result["dependency_materialization_manifest"].get(
                            "lockfile_digest"
                        )
                    )
                )
                for result in results
            ),
            "external_dependency_wheel_attested": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    isinstance(result.get("dependency_materialization_manifest"), Mapping)
                    and result["dependency_materialization_manifest"].get(
                        "wheel_attestation_profile"
                    )
                    == self._policy.dependency_wheel_attestation_profile
                    and result["dependency_materialization_manifest"].get(
                        "wheel_artifact_status"
                    )
                    == "attested"
                    and bool(
                        result["dependency_materialization_manifest"].get(
                            "wheel_attestation_digest"
                        )
                    )
                )
                for result in results
            ),
            "external_dependency_import_precedence_bound": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    result.get("dependency_import_precedence_status")
                    == YAOYOROZU_EXTERNAL_DEPENDENCY_IMPORT_STATUS
                    and result.get("dependency_import_precedence_bound") is True
                    and isinstance(result.get("dependency_import_path_order"), list)
                    and len(result.get("dependency_import_path_order", [])) == 1
                    and result.get("dependency_import_path_order", [None])[0]
                    == str(
                        Path(str(result.get("execution_workspace_root", "")))
                        / YAOYOROZU_DEPENDENCY_MATERIALIZATION_ROOT
                        / "src"
                    )
                )
                for result in results
            ),
            "external_dependency_module_origin_bound": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    result.get("dependency_module_origin_bound") is True
                    and external_dependency_module_origin_bound
                )
                for result in results
            ),
            "profile_coverage_bound": (
                execution_summary.get("required_coverage_areas") == list(required_coverage)
                and execution_summary.get("optional_coverage_areas") == list(optional_coverage)
                and execution_summary.get("requested_optional_coverage_areas")
                == list(normalized_requested_optional)
                and execution_summary.get("dispatch_coverage_areas") == list(dispatch_coverage)
            ),
            "coverage_complete": not missing_coverage and not unexpected_coverage,
            "all_reports_bound_to_dispatch": all(
                isinstance(result, Mapping) and result.get("report_binding_ok") is True
                for result in results
            ),
            "all_delta_receipts_bound": all(
                isinstance(result, Mapping) and result.get("delta_receipt_ok") is True
                for result in results
            ),
            "all_patch_candidate_receipts_bound": all(
                isinstance(result, Mapping) and result.get("patch_candidate_receipt_ok") is True
                for result in results
            ),
            "all_target_paths_ready": all(
                isinstance(result, Mapping) and result.get("target_paths_ready") is True
                for result in results
            ),
            "all_guardian_preseed_gates_bound": all(
                isinstance(result, Mapping)
                and result.get("guardian_preseed_gate_bound") is True
                for result in results
            ),
            "all_external_preseed_gates_passed": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or result.get("guardian_preseed_gate_status") == "pass"
                for result in results
            ),
            "guardian_preseed_oversight_bound": all(
                isinstance(result, Mapping)
                and result.get("guardian_preseed_oversight_bound") is True
                for result in results
            ),
            "all_external_preseed_oversight_satisfied": all(
                not isinstance(result, Mapping)
                or result.get("workspace_scope") != self._policy.external_workspace_scope
                or (
                    result.get("guardian_oversight_event_status") == "satisfied"
                    and result.get("reviewer_network_attested") is True
                    and result.get("guardian_preseed_oversight_bound") is True
                )
                for result in results
            ),
        }
        expected_validation["ok"] = all(expected_validation.values())
        for key, expected_value in expected_validation.items():
            if validation.get(key) != expected_value:
                errors.append(f"validation.{key} mismatch")
        return {
            "ok": not errors and not missing_coverage and not unexpected_coverage,
            "completed_process_count": completed_process_count,
            "success_count": success_count,
            "coverage_complete": not missing_coverage and not unexpected_coverage,
            "missing_coverage": missing_coverage,
            "unexpected_coverage": unexpected_coverage,
            "required_coverage_areas": list(required_coverage),
            "optional_coverage_areas": list(optional_coverage),
            "requested_optional_coverage_areas": list(normalized_requested_optional),
            "dispatch_coverage_areas": list(dispatch_coverage),
            "all_reports_bound_to_dispatch": expected_validation["all_reports_bound_to_dispatch"],
            "all_delta_receipts_bound": expected_validation["all_delta_receipts_bound"],
            "all_patch_candidate_receipts_bound": expected_validation[
                "all_patch_candidate_receipts_bound"
            ],
            "all_target_paths_ready": expected_validation["all_target_paths_ready"],
            "same_host_scope_only": expected_validation["same_host_scope_only"],
            "external_workspace_seeded": expected_validation["external_workspace_seeded"],
            "external_dependencies_materialized": expected_validation[
                "external_dependencies_materialized"
            ],
            "external_dependency_lockfile_attested": expected_validation[
                "external_dependency_lockfile_attested"
            ],
            "external_dependency_wheel_attested": expected_validation[
                "external_dependency_wheel_attested"
            ],
            "external_dependency_import_precedence_bound": expected_validation[
                "external_dependency_import_precedence_bound"
            ],
            "external_dependency_module_origin_bound": expected_validation[
                "external_dependency_module_origin_bound"
            ],
            "all_guardian_preseed_gates_bound": expected_validation[
                "all_guardian_preseed_gates_bound"
            ],
            "all_external_preseed_gates_passed": expected_validation[
                "all_external_preseed_gates_passed"
            ],
            "guardian_preseed_oversight_bound": expected_validation[
                "guardian_preseed_oversight_bound"
            ],
            "all_external_preseed_oversight_satisfied": expected_validation[
                "all_external_preseed_oversight_satisfied"
            ],
            "errors": errors,
        }

    def bind_consensus_dispatch(
        self,
        *,
        convocation_session: Mapping[str, Any],
        dispatch_plan: Mapping[str, Any],
        dispatch_receipt: Mapping[str, Any],
        messages: Sequence[Mapping[str, Any]],
        blocked_direct_attempt: Mapping[str, Any],
        audit_summary: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if convocation_session.get("kind") != "council_convocation_session":
            raise ValueError("convocation_session.kind must equal council_convocation_session")
        if dispatch_plan.get("kind") != "yaoyorozu_worker_dispatch_plan":
            raise ValueError("dispatch_plan.kind must equal yaoyorozu_worker_dispatch_plan")
        if dispatch_receipt.get("kind") != "yaoyorozu_worker_dispatch_receipt":
            raise ValueError("dispatch_receipt.kind must equal yaoyorozu_worker_dispatch_receipt")
        if not isinstance(messages, Sequence) or not messages:
            raise ValueError("messages must be a non-empty sequence")

        session_id = _non_empty_string(convocation_session.get("session_id"), "convocation_session.session_id")
        convocation_session_ref = f"convocation://{session_id}"
        if dispatch_plan.get("convocation_session_ref") != convocation_session_ref:
            raise ValueError("dispatch plan must remain bound to the same convocation session")

        dispatch_plan_ref = f"dispatch://{dispatch_plan['dispatch_id']}"
        if dispatch_receipt.get("dispatch_plan_ref") != dispatch_plan_ref:
            raise ValueError("dispatch receipt must remain bound to the same dispatch plan")
        if dispatch_receipt.get("dispatch_plan_digest") != dispatch_plan.get("dispatch_digest"):
            raise ValueError("dispatch receipt digest binding must match dispatch plan digest")

        normalized_messages = [dict(message) for message in messages]
        report_message_count = sum(
            1
            for message in normalized_messages
            if message.get("intent") == "report" and message.get("phase") == "opening"
        )
        same_session_bound = (
            all(message.get("session_id") == session_id for message in normalized_messages)
            and blocked_direct_attempt.get("session_id") == session_id
            and audit_summary.get("session_id") == session_id
        )
        expected_claim_ids = [
            str(dispatch_plan["dispatch_id"]),
            str(dispatch_receipt["receipt_id"]),
            *[
                str(unit["unit_id"])
                for unit in dispatch_plan.get("dispatch_units", [])
                if isinstance(unit, Mapping) and unit.get("unit_id")
            ],
        ]
        audit_claim_ids = {
            str(claim_id)
            for claim_id in audit_summary.get("related_claim_ids", [])
            if isinstance(claim_id, str)
        }
        gate_payload_bound = any(
            message.get("phase") == "gate"
            and isinstance(message.get("payload"), Mapping)
            and message["payload"].get("dispatch_receipt_digest") == dispatch_receipt.get("receipt_digest")
            for message in normalized_messages
        )
        resolve_payload_bound = any(
            message.get("phase") == "resolve"
            and isinstance(message.get("payload"), Mapping)
            and message["payload"].get("dispatch_receipt_digest") == dispatch_receipt.get("receipt_digest")
            for message in normalized_messages
        )
        validation = {
            "same_session_bound": same_session_bound,
            "dispatch_plan_bound": dispatch_receipt.get("dispatch_plan_ref") == dispatch_plan_ref,
            "dispatch_receipt_coverage_complete": bool(
                dispatch_receipt.get("validation", {}).get("coverage_complete")
            ),
            "all_transport_bus_only": all(
                message.get("transport_profile") == CONSENSUS_BUS_TRANSPORT_PROFILE
                for message in normalized_messages
            )
            and audit_summary.get("all_transport_bus_only") is True,
            "ordered_phases": bool(audit_summary.get("ordered_phases")),
            "dispatch_claims_tracked": set(expected_claim_ids).issubset(audit_claim_ids),
            "worker_reports_routed": report_message_count
            == len(dispatch_receipt.get("results", [])),
            "guardian_gate_present": bool(audit_summary.get("guardian_gate_present")) and gate_payload_bound,
            "resolve_present": bool(audit_summary.get("resolve_present")) and resolve_payload_bound,
            "direct_handoff_blocked": (
                blocked_direct_attempt.get("status") == "blocked"
                and blocked_direct_attempt.get("enforced_policy")
                == CONSENSUS_BUS_TRANSPORT_PROFILE
                and audit_summary.get("blocked_direct_attempts") == 1
            ),
        }
        validation["ok"] = all(validation.values())
        binding = {
            "kind": "yaoyorozu_consensus_dispatch_binding",
            "schema_version": "1.0.0",
            "binding_id": new_id("yaoyorozu-consensus"),
            "bound_at": utc_now_iso(),
            "binding_profile": YAOYOROZU_CONSENSUS_BINDING_PROFILE,
            "convocation_session_ref": convocation_session_ref,
            "convocation_session_digest": convocation_session["session_digest"],
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
            "dispatch_receipt_ref": f"dispatch-receipt://{dispatch_receipt['receipt_id']}",
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_session_id": session_id,
            "transport_profile": CONSENSUS_BUS_TRANSPORT_PROFILE,
            "dispatch_claim_ids": expected_claim_ids,
            "messages": normalized_messages,
            "blocked_direct_attempt": dict(blocked_direct_attempt),
            "audit_summary": dict(audit_summary),
            "validation": validation,
        }
        binding["binding_digest"] = sha256_text(
            canonical_json(_consensus_dispatch_binding_digest_payload(binding))
        )
        return binding

    def validate_consensus_dispatch_binding(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        messages = binding.get("messages", [])
        audit_summary = binding.get("audit_summary", {})
        blocked_direct_attempt = binding.get("blocked_direct_attempt", {})
        session_id = binding.get("consensus_session_id")
        if binding.get("kind") != "yaoyorozu_consensus_dispatch_binding":
            errors.append("kind must equal yaoyorozu_consensus_dispatch_binding")
        if binding.get("binding_profile") != YAOYOROZU_CONSENSUS_BINDING_PROFILE:
            errors.append("binding_profile mismatch")
        if binding.get("transport_profile") != CONSENSUS_BUS_TRANSPORT_PROFILE:
            errors.append("transport_profile mismatch")
        if not isinstance(messages, list) or not messages:
            errors.append("messages must be a non-empty list")
            messages = []
        if not isinstance(audit_summary, Mapping):
            errors.append("audit_summary must be a mapping")
            audit_summary = {}
        if not isinstance(blocked_direct_attempt, Mapping):
            errors.append("blocked_direct_attempt must be a mapping")
            blocked_direct_attempt = {}
        if not isinstance(session_id, str) or not session_id.strip():
            errors.append("consensus_session_id must be a non-empty string")

        tracked_claim_ids = {
            str(claim_id)
            for claim_id in audit_summary.get("related_claim_ids", [])
            if isinstance(claim_id, str)
        }
        expected_claim_ids = {
            str(claim_id)
            for claim_id in binding.get("dispatch_claim_ids", [])
            if isinstance(claim_id, str)
        }
        report_message_count = 0
        previous_phase_order = -1
        for message in messages:
            if not isinstance(message, Mapping):
                errors.append("messages entries must be mappings")
                continue
            if message.get("session_id") != session_id:
                errors.append("every bus message must reuse the same convocation session_id")
            if message.get("transport_profile") != CONSENSUS_BUS_TRANSPORT_PROFILE:
                errors.append("every bus message must remain consensus-bus-only")
            phase = str(message.get("phase", ""))
            if phase not in CONSENSUS_BUS_PHASE_ORDER:
                errors.append("bus message phase is invalid")
                continue
            current_phase_order = CONSENSUS_BUS_PHASE_ORDER[phase]
            if current_phase_order < previous_phase_order:
                errors.append("bus message phases must remain ordered")
            previous_phase_order = current_phase_order
            if message.get("intent") == "report" and phase == "opening":
                report_message_count += 1

        if blocked_direct_attempt.get("session_id") != session_id:
            errors.append("blocked direct attempt must reuse the same session_id")
        if blocked_direct_attempt.get("status") != "blocked":
            errors.append("blocked direct attempt status must equal blocked")
        if blocked_direct_attempt.get("enforced_policy") != CONSENSUS_BUS_TRANSPORT_PROFILE:
            errors.append("blocked direct attempt must enforce consensus-bus-only")
        if audit_summary.get("session_id") != session_id:
            errors.append("audit summary must reuse the same session_id")
        if audit_summary.get("all_transport_bus_only") is not True:
            errors.append("audit summary must report all_transport_bus_only")
        if audit_summary.get("guardian_gate_present") is not True:
            errors.append("audit summary must report guardian_gate_present")
        if audit_summary.get("resolve_present") is not True:
            errors.append("audit summary must report resolve_present")
        if audit_summary.get("ordered_phases") is not True:
            errors.append("audit summary must report ordered phases")
        if audit_summary.get("blocked_direct_attempts") != 1:
            errors.append("audit summary must report exactly one blocked direct attempt")
        if not expected_claim_ids.issubset(tracked_claim_ids):
            errors.append("audit summary must track dispatch claim ids")

        return {
            "ok": not errors,
            "message_count": len(messages),
            "tracked_claim_count": len(tracked_claim_ids),
            "report_message_count": report_message_count,
            "blocked_direct_attempts": audit_summary.get("blocked_direct_attempts", 0),
            "errors": errors,
        }

    def bind_task_graph_dispatch(
        self,
        *,
        convocation_session: Mapping[str, Any],
        dispatch_plan: Mapping[str, Any],
        dispatch_receipt: Mapping[str, Any],
        consensus_binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if convocation_session.get("kind") != "council_convocation_session":
            raise ValueError("convocation_session.kind must equal council_convocation_session")
        if dispatch_plan.get("kind") != "yaoyorozu_worker_dispatch_plan":
            raise ValueError("dispatch_plan.kind must equal yaoyorozu_worker_dispatch_plan")
        if dispatch_receipt.get("kind") != "yaoyorozu_worker_dispatch_receipt":
            raise ValueError("dispatch_receipt.kind must equal yaoyorozu_worker_dispatch_receipt")
        if consensus_binding.get("kind") != "yaoyorozu_consensus_dispatch_binding":
            raise ValueError("consensus_binding.kind must equal yaoyorozu_consensus_dispatch_binding")

        session_id = _non_empty_string(convocation_session.get("session_id"), "convocation_session.session_id")
        convocation_session_ref = f"convocation://{session_id}"
        dispatch_plan_ref = f"dispatch://{dispatch_plan['dispatch_id']}"
        dispatch_receipt_ref = f"dispatch-receipt://{dispatch_receipt['receipt_id']}"
        consensus_binding_ref = f"consensus-binding://{consensus_binding['binding_id']}"
        if dispatch_plan.get("convocation_session_ref") != convocation_session_ref:
            raise ValueError("dispatch plan must remain bound to the same convocation session")
        if dispatch_receipt.get("dispatch_plan_ref") != dispatch_plan_ref:
            raise ValueError("dispatch receipt must remain bound to the same dispatch plan")
        if consensus_binding.get("convocation_session_ref") != convocation_session_ref:
            raise ValueError("consensus binding must remain bound to the same convocation session")
        if consensus_binding.get("dispatch_plan_ref") != dispatch_plan_ref:
            raise ValueError("consensus binding must remain bound to the same dispatch plan")
        if consensus_binding.get("dispatch_receipt_ref") != dispatch_receipt_ref:
            raise ValueError("consensus binding must remain bound to the same dispatch receipt")
        if consensus_binding.get("dispatch_receipt_digest") != dispatch_receipt.get("receipt_digest"):
            raise ValueError("consensus binding must reuse the same dispatch receipt digest")
        if consensus_binding.get("consensus_session_id") != session_id:
            raise ValueError("consensus binding must reuse the same session id")
        proposal_profile = _non_empty_string(
            convocation_session.get("proposal_profile"),
            "convocation_session.proposal_profile",
        )
        requested_optional_coverage = (
            convocation_session.get("selection_summary", {}).get(
                "requested_optional_builder_coverage_areas",
                [],
            )
            if isinstance(convocation_session.get("selection_summary"), Mapping)
            else []
        )
        if (
            dispatch_plan.get("selection_summary", {}).get("requested_optional_coverage_areas", [])
            != requested_optional_coverage
        ):
            raise ValueError(
                "dispatch plan requested_optional_coverage_areas must match the convocation session"
            )
        bundle_strategy = self._task_graph_bundle_strategy(
            proposal_profile,
            requested_optional_coverage,
        )

        messages = consensus_binding.get("messages", [])
        if not isinstance(messages, list) or not messages:
            raise ValueError("consensus binding must expose non-empty messages")

        dispatch_units = [
            dict(unit)
            for unit in dispatch_plan.get("dispatch_units", [])
            if isinstance(unit, Mapping)
        ]
        if not dispatch_units:
            raise ValueError("dispatch plan must expose dispatch units")
        dispatch_units_by_coverage = {
            str(unit["coverage_area"]): unit for unit in dispatch_units if unit.get("coverage_area")
        }
        expected_unit_ids = {str(unit["unit_id"]) for unit in dispatch_units if unit.get("unit_id")}
        report_message_by_unit_id: Dict[str, Dict[str, Any]] = {}
        for message in messages:
            if not isinstance(message, Mapping):
                continue
            if message.get("intent") != "report" or message.get("phase") != "opening":
                continue
            related_claim_ids = message.get("related_claim_ids", [])
            if not isinstance(related_claim_ids, list):
                continue
            for claim_id in related_claim_ids:
                if not isinstance(claim_id, str) or claim_id not in expected_unit_ids:
                    continue
                report_message_by_unit_id[claim_id] = dict(message)

        guardian_gate_message = next(
            (
                dict(message)
                for message in messages
                if isinstance(message, Mapping)
                and message.get("phase") == "gate"
                and message.get("intent") == "gate"
            ),
            None,
        )
        if guardian_gate_message is None:
            raise ValueError("consensus binding must expose one guardian gate message")
        resolve_message = next(
            (
                dict(message)
                for message in messages
                if isinstance(message, Mapping)
                and message.get("phase") == "resolve"
                and message.get("intent") == "resolve"
            ),
            None,
        )
        if resolve_message is None:
            raise ValueError("consensus binding must expose one resolve message")

        bundle_specs: List[Dict[str, Any]] = []
        for bundle in bundle_strategy["root_bundles"]:
            coverage_areas = [str(area) for area in bundle["coverage_areas"]]
            grouped_units: List[Dict[str, Any]] = []
            for coverage_area in coverage_areas:
                unit = dispatch_units_by_coverage.get(coverage_area)
                if unit is None:
                    raise ValueError(f"dispatch unit missing for coverage area {coverage_area}")
                grouped_units.append(unit)
            bundle_specs.append(
                {
                    "bundle_role": str(bundle["bundle_role"]),
                    "coverage_areas": coverage_areas,
                    "dispatch_units": grouped_units,
                }
            )

        task_graph_service = TaskGraphService()
        graph = task_graph_service.build_graph(
            intent=(
                f"{_non_empty_string(convocation_session.get('summary'), 'convocation_session.summary')} "
                "into same-session builder execution bundles"
            ),
            required_roles=[bundle["bundle_role"] for bundle in bundle_specs],
        )
        root_nodes = graph["nodes"][: len(bundle_specs)]
        review_node = graph["nodes"][len(bundle_specs)]
        synthesis_node = graph["nodes"][len(bundle_specs) + 1]
        if review_node.get("id") != "node-council-review":
            raise ValueError("TaskGraph review node must remain node-council-review")
        if synthesis_node.get("id") != "node-result-synthesis":
            raise ValueError("TaskGraph synthesis node must remain node-result-synthesis")

        node_bindings: List[Dict[str, Any]] = []
        result_refs: List[str] = []
        for node, bundle in zip(root_nodes, bundle_specs):
            dispatch_unit_ids = [str(unit["unit_id"]) for unit in bundle["dispatch_units"]]
            selected_agent_ids = [
                str(unit["selected_agent_id"])
                for unit in bundle["dispatch_units"]
                if unit.get("selected_agent_id")
            ]
            report_messages: List[Dict[str, Any]] = []
            for unit_id in dispatch_unit_ids:
                report_message = report_message_by_unit_id.get(unit_id)
                if report_message is None:
                    raise ValueError(f"worker report message missing for dispatch unit {unit_id}")
                report_messages.append(report_message)
            target_paths = sorted(
                {
                    str(target_path)
                    for unit in bundle["dispatch_units"]
                    for target_path in unit.get("target_paths", [])
                    if isinstance(target_path, str)
                }
            )
            node["input_spec"] = {
                **dict(node["input_spec"]),
                "session_id": session_id,
                "convocation_session_ref": convocation_session_ref,
                "dispatch_plan_ref": dispatch_plan_ref,
                "dispatch_receipt_ref": dispatch_receipt_ref,
                "consensus_binding_ref": consensus_binding_ref,
                "coverage_areas": list(bundle["coverage_areas"]),
                "dispatch_unit_ids": dispatch_unit_ids,
                "selected_agent_ids": selected_agent_ids,
                "consensus_claim_ids": dispatch_unit_ids,
            }
            output_spec = (
                dict(node["output_spec"])
                if isinstance(node.get("output_spec"), dict)
                else {"artifact_ref": str(node.get("output_spec", ""))}
            )
            output_spec.update(
                {
                    "artifact_ref": f"artifact://{node['id']}",
                    "review_target": "node-council-review",
                    "report_message_digests": [
                        str(message["message_digest"]) for message in report_messages
                    ],
                }
            )
            node["output_spec"] = output_spec
            result_ref = f"artifact://{node['id']}"
            result_refs.append(result_ref)
            node_bindings.append(
                {
                    "task_node_id": node["id"],
                    "task_node_role": node["role"],
                    "coverage_areas": list(bundle["coverage_areas"]),
                    "dispatch_unit_ids": dispatch_unit_ids,
                    "selected_agent_ids": selected_agent_ids,
                    "report_message_ids": [str(message["message_id"]) for message in report_messages],
                    "report_message_digests": [
                        str(message["message_digest"]) for message in report_messages
                    ],
                    "consensus_claim_ids": dispatch_unit_ids,
                    "target_paths": target_paths,
                    "result_ref": result_ref,
                }
            )

        review_node["input_spec"] = {
            **dict(review_node["input_spec"]),
            "session_id": session_id,
            "dispatch_receipt_ref": dispatch_receipt_ref,
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_binding_ref": consensus_binding_ref,
            "guardian_gate_message_digest": guardian_gate_message["message_digest"],
        }
        review_output = (
            dict(review_node["output_spec"])
            if isinstance(review_node.get("output_spec"), dict)
            else {"artifact_ref": str(review_node.get("output_spec", ""))}
        )
        review_output.update(
            {
                "guardian_gate_message_digest": guardian_gate_message["message_digest"],
                "resolve_target": "node-result-synthesis",
            }
        )
        review_node["output_spec"] = review_output

        synthesis_node["input_spec"] = {
            **dict(synthesis_node["input_spec"]),
            "session_id": session_id,
            "dispatch_receipt_ref": dispatch_receipt_ref,
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_binding_ref": consensus_binding_ref,
            "resolve_message_digest": resolve_message["message_digest"],
            "result_refs": list(result_refs),
        }
        synthesis_output = (
            dict(synthesis_node["output_spec"])
            if isinstance(synthesis_node.get("output_spec"), dict)
            else {"artifact_ref": str(synthesis_node.get("output_spec", ""))}
        )
        synthesis_output.update(
            {
                "artifact_ref": "artifact://yaoyorozu-task-graph-bundle",
                "resolve_message_digest": resolve_message["message_digest"],
            }
        )
        synthesis_node["output_spec"] = synthesis_output

        task_graph_validation = task_graph_service.validate_graph(graph)
        task_graph_dispatch = task_graph_service.dispatch_graph(
            graph_id=graph["graph_id"],
            nodes=graph["nodes"],
            complexity_policy=graph["complexity_policy"],
        )
        task_graph_synthesis = task_graph_service.synthesize_results(
            graph_id=graph["graph_id"],
            result_refs=result_refs,
            complexity_policy=graph["complexity_policy"],
        )

        actual_dispatch_unit_ids = sorted(
            unit_id
            for node_binding in node_bindings
            for unit_id in node_binding["dispatch_unit_ids"]
        )
        expected_dispatch_unit_ids = sorted(expected_unit_ids)
        coverage_groups = sorted(
            ",".join(sorted(node_binding["coverage_areas"])) for node_binding in node_bindings
        )
        expected_coverage_groups = sorted(
            ",".join(sorted(bundle["coverage_areas"])) for bundle in bundle_strategy["root_bundles"]
        )
        validation = {
            "same_session_bound": (
                all(
                    isinstance(node.get("input_spec"), Mapping)
                    and node["input_spec"].get("session_id") == session_id
                    for node in graph["nodes"]
                )
                and consensus_binding.get("consensus_session_id") == session_id
            ),
            "consensus_binding_bound": (
                consensus_binding.get("convocation_session_ref") == convocation_session_ref
                and consensus_binding.get("dispatch_plan_ref") == dispatch_plan_ref
                and consensus_binding.get("dispatch_receipt_ref") == dispatch_receipt_ref
            ),
            "complexity_policy_ok": (
                task_graph_validation["ok"]
                and task_graph_validation["root_count"]
                <= graph["complexity_policy"]["max_parallelism"]
            ),
            "root_bundle_count_ok": (
                task_graph_validation["root_count"] == len(bundle_specs)
                and task_graph_dispatch["dispatched_count"] == len(bundle_specs)
            ),
            "dispatch_units_bound": actual_dispatch_unit_ids == expected_dispatch_unit_ids,
            "bundle_strategy_ok": (
                bundle_strategy["strategy_id"]
                == self._task_graph_bundle_strategy(
                    proposal_profile,
                    requested_optional_coverage,
                )["strategy_id"]
                and bundle_strategy["proposal_profile"] == proposal_profile
                and bundle_strategy["requested_optional_coverage_areas"]
                == list(requested_optional_coverage)
                and bundle_strategy["dispatch_coverage_areas"]
                == list(dispatch_plan["selection_summary"]["dispatch_coverage_areas"])
                and bundle_strategy["root_bundle_count"] == len(bundle_specs)
                and bundle_strategy["max_parallelism"] == graph["complexity_policy"]["max_parallelism"]
                and task_graph_validation["root_count"] == bundle_strategy["root_bundle_count"]
                and graph["required_roles"]
                == [bundle["bundle_role"] for bundle in bundle_strategy["root_bundles"]]
                and bundle_strategy["root_bundles"]
                == [
                    {
                        "bundle_role": bundle["bundle_role"],
                        "coverage_areas": list(bundle["coverage_areas"]),
                    }
                    for bundle in bundle_specs
                ]
            ),
            "coverage_grouping_ok": coverage_groups == expected_coverage_groups,
            "worker_claims_bound": (
                all(
                    set(node_binding["consensus_claim_ids"]).issubset(
                        set(consensus_binding.get("dispatch_claim_ids", []))
                    )
                    for node_binding in node_bindings
                )
                and all(
                    expected_unit_ids.issuperset(set(node_binding["dispatch_unit_ids"]))
                    for node_binding in node_bindings
                )
            ),
            "guardian_gate_bound": (
                isinstance(review_node.get("input_spec"), Mapping)
                and review_node["input_spec"].get("guardian_gate_message_digest")
                == guardian_gate_message["message_digest"]
            ),
            "resolve_bound": (
                isinstance(synthesis_node.get("input_spec"), Mapping)
                and synthesis_node["input_spec"].get("resolve_message_digest")
                == resolve_message["message_digest"]
            ),
            "synthesis_bound": (
                task_graph_synthesis["accepted_result_count"] == len(result_refs)
                and sorted(task_graph_dispatch["ready_node_ids"])
                == sorted(node_binding["task_node_id"] for node_binding in node_bindings)
            ),
        }
        validation["ok"] = all(validation.values())

        binding = {
            "kind": "yaoyorozu_task_graph_binding",
            "schema_version": "1.0.0",
            "binding_id": new_id("yaoyorozu-task-graph"),
            "bound_at": utc_now_iso(),
            "binding_profile": self._policy.task_graph_binding_profile,
            "proposal_profile": proposal_profile,
            "convocation_session_ref": convocation_session_ref,
            "convocation_session_digest": convocation_session["session_digest"],
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
            "dispatch_receipt_ref": dispatch_receipt_ref,
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_binding_ref": consensus_binding_ref,
            "consensus_binding_digest": consensus_binding["binding_digest"],
            "consensus_session_id": session_id,
            "bundle_strategy": bundle_strategy,
            "task_graph_ref": f"task-graph://{graph['graph_id']}",
            "task_graph_digest": sha256_text(canonical_json(_task_graph_digest_payload(graph))),
            "task_graph_dispatch_digest": sha256_text(canonical_json(task_graph_dispatch)),
            "task_graph_synthesis_digest": sha256_text(canonical_json(task_graph_synthesis)),
            "guardian_gate_message_digest": guardian_gate_message["message_digest"],
            "resolve_message_digest": resolve_message["message_digest"],
            "task_graph": graph,
            "task_graph_validation": task_graph_validation,
            "task_graph_dispatch": task_graph_dispatch,
            "task_graph_synthesis": task_graph_synthesis,
            "node_bindings": node_bindings,
            "validation": validation,
        }
        binding["binding_digest"] = sha256_text(
            canonical_json(_task_graph_binding_digest_payload(binding))
        )
        return binding

    def validate_task_graph_dispatch_binding(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if binding.get("kind") != "yaoyorozu_task_graph_binding":
            errors.append("kind must equal yaoyorozu_task_graph_binding")
        if binding.get("binding_profile") != self._policy.task_graph_binding_profile:
            errors.append("binding_profile mismatch")
        proposal_profile = binding.get("proposal_profile")
        if proposal_profile not in self._policy.task_graph_bundle_strategies:
            errors.append("proposal_profile must map to one supported TaskGraph bundle strategy")
            expected_bundle_strategy = {}
        else:
            requested_optional_coverage = binding.get("bundle_strategy", {}).get(
                "requested_optional_coverage_areas",
                [],
            )
            expected_bundle_strategy = self._task_graph_bundle_strategy(
                str(proposal_profile),
                requested_optional_coverage,
            )
        bundle_strategy = binding.get("bundle_strategy", {})
        if not isinstance(bundle_strategy, Mapping):
            errors.append("bundle_strategy must be a mapping")
            bundle_strategy = {}
        elif expected_bundle_strategy:
            if bundle_strategy.get("strategy_id") != expected_bundle_strategy["strategy_id"]:
                errors.append("bundle_strategy.strategy_id mismatch")
            if bundle_strategy.get("proposal_profile") != proposal_profile:
                errors.append("bundle_strategy.proposal_profile mismatch")
            if bundle_strategy.get("root_bundle_count") != expected_bundle_strategy["root_bundle_count"]:
                errors.append("bundle_strategy.root_bundle_count mismatch")
            if bundle_strategy.get("max_parallelism") != expected_bundle_strategy["max_parallelism"]:
                errors.append("bundle_strategy.max_parallelism mismatch")
            if bundle_strategy.get("root_bundles") != expected_bundle_strategy["root_bundles"]:
                errors.append("bundle_strategy.root_bundles mismatch")
            if (
                bundle_strategy.get("requested_optional_coverage_areas")
                != expected_bundle_strategy["requested_optional_coverage_areas"]
            ):
                errors.append("bundle_strategy.requested_optional_coverage_areas mismatch")
            if (
                bundle_strategy.get("dispatch_coverage_areas")
                != expected_bundle_strategy["dispatch_coverage_areas"]
            ):
                errors.append("bundle_strategy.dispatch_coverage_areas mismatch")

        task_graph = binding.get("task_graph", {})
        task_graph_validation = binding.get("task_graph_validation", {})
        task_graph_dispatch = binding.get("task_graph_dispatch", {})
        task_graph_synthesis = binding.get("task_graph_synthesis", {})
        node_bindings = binding.get("node_bindings", [])
        validation = binding.get("validation", {})
        if not isinstance(task_graph, Mapping):
            errors.append("task_graph must be a mapping")
            task_graph = {}
        if not isinstance(task_graph_validation, Mapping):
            errors.append("task_graph_validation must be a mapping")
            task_graph_validation = {}
        if not isinstance(task_graph_dispatch, Mapping):
            errors.append("task_graph_dispatch must be a mapping")
            task_graph_dispatch = {}
        if not isinstance(task_graph_synthesis, Mapping):
            errors.append("task_graph_synthesis must be a mapping")
            task_graph_synthesis = {}
        if not isinstance(node_bindings, list) or not node_bindings:
            errors.append("node_bindings must be a non-empty list")
            node_bindings = []
        if not isinstance(validation, Mapping):
            errors.append("validation must be a mapping")
            validation = {}

        graph_id = task_graph.get("graph_id")
        if not isinstance(graph_id, str) or not graph_id.strip():
            errors.append("task_graph.graph_id must be a non-empty string")

        nodes = task_graph.get("nodes", [])
        if not isinstance(nodes, list) or not nodes:
            errors.append("task_graph.nodes must be a non-empty list")
            nodes = []
        ready_node_ids = task_graph_dispatch.get("ready_node_ids", [])
        if not isinstance(ready_node_ids, list) or not ready_node_ids:
            errors.append("task_graph_dispatch.ready_node_ids must be a non-empty list")
            ready_node_ids = []
        review_node = next(
            (
                node
                for node in nodes
                if isinstance(node, Mapping) and node.get("id") == "node-council-review"
            ),
            {},
        )
        synthesis_node = next(
            (
                node
                for node in nodes
                if isinstance(node, Mapping) and node.get("id") == "node-result-synthesis"
            ),
            {},
        )

        bound_dispatch_unit_ids: List[str] = []
        for node_binding in node_bindings:
            if not isinstance(node_binding, Mapping):
                errors.append("node_bindings entries must be mappings")
                continue
            task_node_id = node_binding.get("task_node_id")
            if task_node_id not in ready_node_ids:
                errors.append("task_node_id must remain one of the ready root nodes")
            dispatch_unit_ids = node_binding.get("dispatch_unit_ids", [])
            if not isinstance(dispatch_unit_ids, list) or not dispatch_unit_ids:
                errors.append("dispatch_unit_ids must be a non-empty list")
                continue
            bound_dispatch_unit_ids.extend(str(unit_id) for unit_id in dispatch_unit_ids)
            report_message_digests = node_binding.get("report_message_digests", [])
            if not isinstance(report_message_digests, list) or len(report_message_digests) != len(
                dispatch_unit_ids
            ):
                errors.append("report_message_digests must align with dispatch_unit_ids")

        if len(set(bound_dispatch_unit_ids)) != len(bound_dispatch_unit_ids):
            errors.append("dispatch unit bindings must remain unique across root bundles")
        if task_graph_validation.get("ok") is not True:
            errors.append("task_graph_validation must remain ok")
        if task_graph_dispatch.get("graph_id") != graph_id:
            errors.append("task_graph_dispatch.graph_id must match task_graph.graph_id")
        if task_graph_synthesis.get("graph_id") != graph_id:
            errors.append("task_graph_synthesis.graph_id must match task_graph.graph_id")
        if task_graph_synthesis.get("accepted_result_count") != len(ready_node_ids):
            errors.append("task_graph_synthesis must accept exactly one result per ready root node")
        if task_graph_dispatch.get("dispatched_count") != len(ready_node_ids):
            errors.append("task_graph_dispatch.dispatched_count must match ready_node_ids count")
        if expected_bundle_strategy and task_graph.get("required_roles") != [
            bundle["bundle_role"] for bundle in expected_bundle_strategy["root_bundles"]
        ]:
            errors.append("task_graph.required_roles must match the selected bundle strategy")
        if not isinstance(review_node.get("input_spec"), Mapping) or review_node["input_spec"].get(
            "guardian_gate_message_digest"
        ) != binding.get("guardian_gate_message_digest"):
            errors.append("review node must bind guardian gate digest")
        if not isinstance(synthesis_node.get("input_spec"), Mapping) or synthesis_node["input_spec"].get(
            "resolve_message_digest"
        ) != binding.get("resolve_message_digest"):
            errors.append("synthesis node must bind resolve digest")
        if validation.get("ok") is not True:
            errors.append("binding validation must remain ok")

        return {
            "ok": not errors,
            "ready_node_count": len(ready_node_ids),
            "dispatch_unit_count": len(set(bound_dispatch_unit_ids)),
            "synthesis_count": int(task_graph_synthesis.get("accepted_result_count", 0)),
            "guardian_gate_bound": (
                isinstance(review_node.get("input_spec"), Mapping)
                and review_node["input_spec"].get("guardian_gate_message_digest")
                == binding.get("guardian_gate_message_digest")
            ),
            "bundle_strategy_ok": validation.get("bundle_strategy_ok") is True,
            "worker_claims_bound": validation.get("worker_claims_bound") is True,
            "coverage_grouping_ok": validation.get("coverage_grouping_ok") is True,
            "errors": errors,
        }

    def _repo_root(self) -> Path:
        if self._agents_root is None:
            raise ValueError(
                "agents directory must be synced before build_request handoff binding can be prepared"
            )
        return self._agents_root.parent.resolve()

    def _build_request_eval_refs(self, proposal_profile: str) -> List[str]:
        profile_evals = YAOYOROZU_PROFILE_BUILD_REQUEST_EVALS.get(proposal_profile)
        if not isinstance(profile_evals, list) or not profile_evals:
            raise ValueError(f"unsupported proposal profile for build_request handoff: {proposal_profile}")
        return _ordered_unique(
            [
                "evals/continuity/council_output_build_request_pipeline.yaml",
                YAOYOROZU_BUILD_REQUEST_EVAL,
                *profile_evals,
            ]
        )

    def _sorted_patch_candidates(
        self,
        dispatch_receipt: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        ranked_candidates: List[Dict[str, Any]] = []
        for result in dispatch_receipt.get("results", []):
            if not isinstance(result, Mapping):
                continue
            report = result.get("report", {})
            if not isinstance(report, Mapping):
                continue
            patch_candidate_receipt = report.get("patch_candidate_receipt", {})
            if not isinstance(patch_candidate_receipt, Mapping):
                continue
            patch_candidates = patch_candidate_receipt.get("patch_candidates", [])
            if not isinstance(patch_candidates, list):
                continue
            for candidate in patch_candidates:
                if not isinstance(candidate, Mapping):
                    continue
                patch_descriptor = candidate.get("patch_descriptor", {})
                if not isinstance(patch_descriptor, Mapping):
                    patch_descriptor = {}
                ranked_candidates.append(
                    {
                        "dispatch_unit_ref": str(result.get("unit_id", "")),
                        "coverage_area": str(result.get("coverage_area", "")),
                        "selected_agent_id": str(result.get("selected_agent_id", "")),
                        "patch_candidate_receipt_ref": str(
                            patch_candidate_receipt.get("receipt_ref", "")
                        ),
                        "patch_candidate_receipt_digest": str(
                            patch_candidate_receipt.get("receipt_digest", "")
                        ),
                        "candidate_id": str(candidate.get("candidate_id", "")),
                        "candidate_digest": str(candidate.get("candidate_digest", "")),
                        "priority_rank": int(candidate.get("priority_rank", 0)),
                        "priority_score": int(candidate.get("priority_score", 0)),
                        "priority_tier": str(candidate.get("priority_tier", "none")),
                        "target_path": str(candidate.get("target_path", "")),
                        "patch_descriptor": dict(patch_descriptor),
                    }
                )
        ranked_candidates.sort(
            key=lambda candidate: (
                -int(candidate["priority_score"]),
                int(candidate["priority_rank"]),
                str(candidate["coverage_area"]),
                str(candidate["candidate_id"]),
            )
        )
        for review_rank, candidate in enumerate(ranked_candidates, start=1):
            candidate["review_rank"] = review_rank
        return ranked_candidates

    def bind_build_request_handoff(
        self,
        *,
        convocation_session: Mapping[str, Any],
        dispatch_plan: Mapping[str, Any],
        dispatch_receipt: Mapping[str, Any],
        consensus_binding: Mapping[str, Any],
        task_graph_binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if convocation_session.get("kind") != "council_convocation_session":
            raise ValueError("convocation_session.kind must equal council_convocation_session")
        if dispatch_plan.get("kind") != "yaoyorozu_worker_dispatch_plan":
            raise ValueError("dispatch_plan.kind must equal yaoyorozu_worker_dispatch_plan")
        if dispatch_receipt.get("kind") != "yaoyorozu_worker_dispatch_receipt":
            raise ValueError("dispatch_receipt.kind must equal yaoyorozu_worker_dispatch_receipt")
        if consensus_binding.get("kind") != "yaoyorozu_consensus_dispatch_binding":
            raise ValueError(
                "consensus_binding.kind must equal yaoyorozu_consensus_dispatch_binding"
            )
        if task_graph_binding.get("kind") != "yaoyorozu_task_graph_binding":
            raise ValueError("task_graph_binding.kind must equal yaoyorozu_task_graph_binding")

        proposal_profile = str(convocation_session.get("proposal_profile", ""))
        if proposal_profile != dispatch_plan.get("proposal_profile") or proposal_profile != dispatch_receipt.get(
            "proposal_profile"
        ):
            raise ValueError("proposal_profile must remain aligned across convocation, plan, and receipt")
        if proposal_profile != task_graph_binding.get("proposal_profile"):
            raise ValueError("task_graph_binding.proposal_profile must match convocation_session")

        repo_root = self._repo_root()
        session_id = str(convocation_session.get("session_id", ""))
        dispatch_plan_ref = f"dispatch://{dispatch_plan['dispatch_id']}"
        dispatch_receipt_ref = f"dispatch-receipt://{dispatch_receipt['receipt_id']}"
        consensus_binding_ref = f"consensus-binding://{consensus_binding['binding_id']}"
        task_graph_binding_ref = f"task-graph-binding://{task_graph_binding['binding_id']}"

        ranked_candidates = self._sorted_patch_candidates(dispatch_receipt)
        selected_candidates = [
            {
                "dispatch_unit_ref": str(candidate["dispatch_unit_ref"]),
                "coverage_area": str(candidate["coverage_area"]),
                "selected_agent_id": str(candidate["selected_agent_id"]),
                "patch_candidate_receipt_ref": str(candidate["patch_candidate_receipt_ref"]),
                "patch_candidate_receipt_digest": str(candidate["patch_candidate_receipt_digest"]),
                "candidate_id": str(candidate["candidate_id"]),
                "candidate_digest": str(candidate["candidate_digest"]),
                "review_rank": int(candidate["review_rank"]),
                "priority_rank": int(candidate["priority_rank"]),
                "priority_score": int(candidate["priority_score"]),
                "priority_tier": str(candidate["priority_tier"]),
                "target_path": str(candidate["target_path"]),
                "patch_descriptor": dict(candidate["patch_descriptor"]),
            }
            for candidate in ranked_candidates[: self._policy.build_request_candidate_limit]
        ]

        request_id = new_id("build")
        output_paths = _ordered_unique(
            list(YAOYOROZU_BUILD_REQUEST_STATIC_OUTPUT_PATHS)
            + [f"meta/decision-log/{request_id}.md"]
            + [str(candidate["target_path"]) for candidate in ranked_candidates if candidate["target_path"]]
        )
        must_pass_evals = self._build_request_eval_refs(proposal_profile)
        change_summary = (
            f"Promote the {proposal_profile} Yaoyorozu dispatch bundle into an "
            f"{self._policy.build_request_target_subsystem} handoff with candidate-bound review hints."
        )
        manifest = self._design_reader.finalize_manifest(
            self._design_reader.read_design_delta(
                target_subsystem=self._policy.build_request_target_subsystem,
                change_summary=change_summary,
                design_refs=list(YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS),
                spec_refs=list(YAOYOROZU_BUILD_REQUEST_SPEC_REFS),
                workspace_scope=list(YAOYOROZU_BUILD_REQUEST_SCOPE_ROOTS),
                output_paths=output_paths,
                must_sync_docs=list(YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS),
                repo_root=repo_root,
            )
        )
        build_request = self._design_reader.prepare_build_request(
            manifest=manifest,
            request_id=request_id,
            change_class=YAOYOROZU_BUILD_REQUEST_CHANGE_CLASS,
            must_pass=must_pass_evals,
            council_session_id=session_id,
            guardian_gate="pass",
        )
        build_request_ref = f"build://{build_request['request_id']}"
        build_request_digest = sha256_text(canonical_json(build_request))
        scope_validation = self._patch_generator.validate_scope(build_request)

        ranked_candidate_ids = [str(candidate["candidate_id"]) for candidate in ranked_candidates]
        selected_candidate_ids = [
            str(candidate["candidate_id"]) for candidate in selected_candidates
        ]
        handoff_summary = {
            "target_subsystem": self._policy.build_request_target_subsystem,
            "change_class": YAOYOROZU_BUILD_REQUEST_CHANGE_CLASS,
            "dispatch_coverage_areas": list(dispatch_plan["selection_summary"]["dispatch_coverage_areas"]),
            "workspace_scope": list(build_request["workspace_scope"]),
            "output_paths": list(build_request["output_paths"]),
            "must_sync_docs": list(build_request["must_sync_docs"]),
            "must_pass_evals": list(build_request["constraints"]["must_pass"]),
            "candidate_signal": "candidate-ready" if ranked_candidates else "no-candidates",
            "candidate_count": len(ranked_candidates),
            "selected_candidate_count": len(selected_candidates),
            "selected_candidate_limit": self._policy.build_request_candidate_limit,
            "patch_priority_profile": str(
                dispatch_receipt["execution_summary"]["patch_priority_profile"]
            ),
            "highest_priority_tier": str(
                dispatch_receipt["execution_summary"]["highest_patch_priority_tier"]
            ),
            "highest_priority_score": int(
                dispatch_receipt["execution_summary"]["highest_patch_priority_score"]
            ),
            "ranked_candidate_ids": ranked_candidate_ids,
            "selected_candidate_ids": selected_candidate_ids,
        }
        council_action = {
            "session_id": session_id,
            "approved_action": "emit_build_request",
            "guardian_gate_status": "pass",
            "resolution_status": "ready-for-patch-generator",
            "guardian_gate_message_digest": str(task_graph_binding["guardian_gate_message_digest"]),
            "resolve_message_digest": str(task_graph_binding["resolve_message_digest"]),
        }

        def _scope_contains(path: str, scopes: Sequence[str]) -> bool:
            normalized_path = path.rstrip("/")
            for scope in scopes:
                normalized_scope = str(scope).rstrip("/")
                if normalized_path == normalized_scope or normalized_path.startswith(
                    f"{normalized_scope}/"
                ):
                    return True
            return False

        validation = {
            "same_session_bound": (
                build_request["approval_context"]["council_session_id"] == session_id
                and consensus_binding.get("consensus_session_id") == session_id
                and task_graph_binding.get("consensus_session_id") == session_id
                and council_action["session_id"] == session_id
            ),
            "consensus_task_graph_bound": (
                consensus_binding.get("convocation_session_ref")
                == f"convocation://{convocation_session['session_id']}"
                and consensus_binding.get("dispatch_plan_ref") == dispatch_plan_ref
                and consensus_binding.get("dispatch_receipt_ref") == dispatch_receipt_ref
                and task_graph_binding.get("convocation_session_ref")
                == f"convocation://{convocation_session['session_id']}"
                and task_graph_binding.get("dispatch_plan_ref") == dispatch_plan_ref
                and task_graph_binding.get("dispatch_receipt_ref") == dispatch_receipt_ref
                and task_graph_binding.get("consensus_binding_ref") == consensus_binding_ref
            ),
            "build_request_ref_bound": (
                build_request_ref == f"build://{build_request['request_id']}"
                and build_request["target_subsystem"] == self._policy.build_request_target_subsystem
                and build_request["change_class"] == YAOYOROZU_BUILD_REQUEST_CHANGE_CLASS
                and build_request["approval_context"]["guardian_gate"]
                == council_action["guardian_gate_status"]
            ),
            "build_request_scope_allowed": (
                scope_validation["allowed"] is True and not scope_validation["blocking_rules"]
            ),
            "must_pass_bound": list(build_request["constraints"]["must_pass"]) == must_pass_evals,
            "output_paths_bound": (
                list(build_request["output_paths"]) == output_paths
                and list(build_request["constraints"]["allowed_write_paths"]) == output_paths
                and all(
                    _scope_contains(path, build_request["workspace_scope"])
                    for path in build_request["output_paths"]
                )
            ),
            "patch_candidate_summary_bound": (
                handoff_summary["patch_priority_profile"]
                == dispatch_receipt["execution_summary"]["patch_priority_profile"]
                and handoff_summary["highest_priority_tier"]
                == dispatch_receipt["execution_summary"]["highest_patch_priority_tier"]
                and handoff_summary["highest_priority_score"]
                == dispatch_receipt["execution_summary"]["highest_patch_priority_score"]
                and handoff_summary["candidate_count"] == len(ranked_candidates)
                and handoff_summary["selected_candidate_count"] == len(selected_candidates)
                and handoff_summary["selected_candidate_ids"] == selected_candidate_ids
            ),
            "selected_candidates_sorted": (
                selected_candidate_ids == ranked_candidate_ids[: len(selected_candidates)]
                and [candidate["review_rank"] for candidate in selected_candidates]
                == list(range(1, len(selected_candidates) + 1))
            ),
        }
        validation["ok"] = all(validation.values())

        binding = {
            "kind": "yaoyorozu_build_request_binding",
            "schema_version": "1.0.0",
            "binding_id": new_id("yaoyorozu-build-request"),
            "binding_ref": "",
            "bound_at": utc_now_iso(),
            "binding_profile": self._policy.build_request_binding_profile,
            "proposal_profile": proposal_profile,
            "convocation_session_ref": f"convocation://{convocation_session['session_id']}",
            "convocation_session_digest": convocation_session["session_digest"],
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
            "dispatch_receipt_ref": dispatch_receipt_ref,
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_binding_ref": consensus_binding_ref,
            "consensus_binding_digest": consensus_binding["binding_digest"],
            "task_graph_binding_ref": task_graph_binding_ref,
            "task_graph_binding_digest": task_graph_binding["binding_digest"],
            "council_action": council_action,
            "handoff_summary": handoff_summary,
            "selected_patch_candidates": selected_candidates,
            "build_request_ref": build_request_ref,
            "build_request_digest": build_request_digest,
            "build_request": build_request,
            "scope_validation": dict(scope_validation),
            "validation": validation,
        }
        binding["binding_ref"] = f"build-request-binding://{binding['binding_id']}"
        binding["binding_digest"] = sha256_text(
            canonical_json(_build_request_binding_digest_payload(binding))
        )
        return binding

    def validate_build_request_handoff(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if binding.get("kind") != "yaoyorozu_build_request_binding":
            errors.append("kind must equal yaoyorozu_build_request_binding")
        if binding.get("binding_profile") != self._policy.build_request_binding_profile:
            errors.append("binding_profile mismatch")

        proposal_profile = binding.get("proposal_profile")
        if proposal_profile not in self._policy.council_profiles:
            errors.append("proposal_profile must remain one supported Yaoyorozu proposal profile")

        handoff_summary = binding.get("handoff_summary", {})
        build_request = binding.get("build_request", {})
        scope_validation = binding.get("scope_validation", {})
        selected_patch_candidates = binding.get("selected_patch_candidates", [])
        council_action = binding.get("council_action", {})
        validation = binding.get("validation", {})
        if not isinstance(handoff_summary, Mapping):
            errors.append("handoff_summary must be a mapping")
            handoff_summary = {}
        if not isinstance(build_request, Mapping):
            errors.append("build_request must be a mapping")
            build_request = {}
        if not isinstance(scope_validation, Mapping):
            errors.append("scope_validation must be a mapping")
            scope_validation = {}
        if not isinstance(selected_patch_candidates, list):
            errors.append("selected_patch_candidates must be a list")
            selected_patch_candidates = []
        if not isinstance(council_action, Mapping):
            errors.append("council_action must be a mapping")
            council_action = {}
        if not isinstance(validation, Mapping):
            errors.append("validation must be a mapping")
            validation = {}

        if build_request:
            if binding.get("build_request_ref") != f"build://{build_request.get('request_id', '')}":
                errors.append("build_request_ref must bind build_request.request_id")
            expected_build_request_digest = sha256_text(canonical_json(build_request))
            if binding.get("build_request_digest") != expected_build_request_digest:
                errors.append("build_request_digest mismatch")
            if build_request.get("target_subsystem") != self._policy.build_request_target_subsystem:
                errors.append("build_request.target_subsystem mismatch")
            if build_request.get("change_class") != YAOYOROZU_BUILD_REQUEST_CHANGE_CLASS:
                errors.append("build_request.change_class mismatch")
            if build_request.get("design_refs") != list(YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS):
                errors.append("build_request.design_refs mismatch")
            if build_request.get("spec_refs") != list(YAOYOROZU_BUILD_REQUEST_SPEC_REFS):
                errors.append("build_request.spec_refs mismatch")
            if build_request.get("must_sync_docs") != list(YAOYOROZU_BUILD_REQUEST_MUST_SYNC_DOCS):
                errors.append("build_request.must_sync_docs mismatch")

        if proposal_profile in self._policy.council_profiles and build_request:
            expected_must_pass = self._build_request_eval_refs(str(proposal_profile))
            if build_request.get("constraints", {}).get("must_pass") != expected_must_pass:
                errors.append("build_request.constraints.must_pass mismatch")
            if handoff_summary.get("must_pass_evals") != expected_must_pass:
                errors.append("handoff_summary.must_pass_evals mismatch")

        if build_request and handoff_summary:
            if build_request.get("output_paths") != handoff_summary.get("output_paths"):
                errors.append("handoff_summary.output_paths must mirror build_request.output_paths")
            if build_request.get("workspace_scope") != handoff_summary.get("workspace_scope"):
                errors.append(
                    "handoff_summary.workspace_scope must mirror build_request.workspace_scope"
                )
            if build_request.get("must_sync_docs") != handoff_summary.get("must_sync_docs"):
                errors.append("handoff_summary.must_sync_docs mismatch")
            if build_request.get("constraints", {}).get("allowed_write_paths") != build_request.get(
                "output_paths"
            ):
                errors.append("build_request allowed_write_paths must equal output_paths")

        if build_request and council_action:
            if build_request.get("approval_context", {}).get("council_session_id") != council_action.get(
                "session_id"
            ):
                errors.append("council_action.session_id must bind build_request approval_context")
            if build_request.get("approval_context", {}).get("guardian_gate") != council_action.get(
                "guardian_gate_status"
            ):
                errors.append(
                    "council_action.guardian_gate_status must bind build_request approval_context"
                )

        if scope_validation.get("allowed") is not True:
            errors.append("scope_validation.allowed must remain true")
        if list(scope_validation.get("blocking_rules", [])):
            errors.append("scope_validation.blocking_rules must remain empty")

        selected_candidate_ids = [
            str(candidate.get("candidate_id", ""))
            for candidate in selected_patch_candidates
            if isinstance(candidate, Mapping)
        ]
        if handoff_summary:
            ranked_candidate_ids = handoff_summary.get("ranked_candidate_ids", [])
            if handoff_summary.get("selected_candidate_ids") != selected_candidate_ids:
                errors.append("handoff_summary.selected_candidate_ids mismatch")
            if selected_candidate_ids != ranked_candidate_ids[: len(selected_candidate_ids)]:
                errors.append("selected_patch_candidates must preserve ranked candidate order")
            if handoff_summary.get("selected_candidate_count") != len(selected_patch_candidates):
                errors.append("handoff_summary.selected_candidate_count mismatch")
            if (
                handoff_summary.get("candidate_signal") == "no-candidates"
                and handoff_summary.get("candidate_count") != 0
            ):
                errors.append("candidate_signal no-candidates requires candidate_count == 0")
            if (
                handoff_summary.get("candidate_signal") == "candidate-ready"
                and handoff_summary.get("candidate_count", 0) < 1
            ):
                errors.append("candidate-ready requires candidate_count >= 1")

        review_ranks = [
            int(candidate.get("review_rank", 0))
            for candidate in selected_patch_candidates
            if isinstance(candidate, Mapping)
        ]
        if review_ranks and review_ranks != list(range(1, len(review_ranks) + 1)):
            errors.append("selected_patch_candidates.review_rank must remain consecutive")
        if validation.get("ok") is not True:
            errors.append("binding validation must remain ok")

        return {
            "ok": not errors,
            "selected_candidate_count": len(selected_patch_candidates),
            "must_pass_count": len(build_request.get("constraints", {}).get("must_pass", []))
            if isinstance(build_request, Mapping)
            else 0,
            "output_path_count": len(build_request.get("output_paths", []))
            if isinstance(build_request, Mapping)
            else 0,
            "scope_allowed": scope_validation.get("allowed") is True,
            "errors": errors,
        }

    def bind_execution_chain(
        self,
        *,
        build_request_binding: Mapping[str, Any],
        build_artifact: Mapping[str, Any],
        sandbox_apply_receipt: Mapping[str, Any],
        live_enactment_session: Mapping[str, Any],
        rollout_session: Mapping[str, Any],
        rollback_session: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if build_request_binding.get("kind") != "yaoyorozu_build_request_binding":
            raise ValueError(
                "build_request_binding.kind must equal yaoyorozu_build_request_binding"
            )
        if build_artifact.get("kind") != "build_artifact":
            raise ValueError("build_artifact.kind must equal build_artifact")
        if sandbox_apply_receipt.get("kind") != "sandbox_apply_receipt":
            raise ValueError("sandbox_apply_receipt.kind must equal sandbox_apply_receipt")
        if live_enactment_session.get("kind") != "builder_live_enactment_session":
            raise ValueError(
                "live_enactment_session.kind must equal builder_live_enactment_session"
            )
        if rollout_session.get("kind") != "staged_rollout_session":
            raise ValueError("rollout_session.kind must equal staged_rollout_session")
        if rollback_session.get("kind") != "builder_rollback_session":
            raise ValueError("rollback_session.kind must equal builder_rollback_session")

        build_request = build_request_binding.get("build_request", {})
        if not isinstance(build_request, Mapping):
            raise ValueError("build_request_binding.build_request must be a mapping")

        request_id = str(build_request.get("request_id", ""))
        artifact_id = str(build_artifact.get("artifact_id", ""))
        apply_receipt_id = str(sandbox_apply_receipt.get("receipt_id", ""))
        enactment_session_id = str(live_enactment_session.get("enactment_session_id", ""))
        rollout_session_id = str(rollout_session.get("session_id", ""))
        rollback_session_id = str(rollback_session.get("rollback_session_id", ""))

        build_artifact_ref = f"artifact://{artifact_id}"
        sandbox_apply_receipt_ref = f"sandbox-apply://{apply_receipt_id}"
        live_enactment_session_ref = f"enactment-session://{enactment_session_id}"
        rollout_session_ref = f"rollout-session://{rollout_session_id}"
        rollback_session_ref = f"rollback-session://{rollback_session_id}"

        build_artifact_digest = sha256_text(canonical_json(build_artifact))
        sandbox_apply_receipt_digest = sha256_text(canonical_json(sandbox_apply_receipt))
        live_enactment_session_digest = sha256_text(canonical_json(live_enactment_session))
        rollout_session_digest = sha256_text(canonical_json(rollout_session))
        rollback_session_digest = sha256_text(canonical_json(rollback_session))

        rollback_plan_ref = _artifact_ref(build_artifact, "rollback_plan")
        build_request_ref = str(build_request_binding.get("build_request_ref", ""))
        build_request_digest = str(build_request_binding.get("build_request_digest", ""))
        selected_patch_candidates = list(build_request_binding.get("selected_patch_candidates", []))
        patch_targets = [
            str(patch.get("target_path", ""))
            for patch in build_artifact.get("patches", [])
            if isinstance(patch, Mapping)
        ]
        selected_candidate_targets = [
            str(candidate.get("target_path", ""))
            for candidate in selected_patch_candidates
            if isinstance(candidate, Mapping)
        ]
        required_eval_refs = _ordered_unique(
            [
                *list(build_request.get("constraints", {}).get("must_pass", [])),
                *YAOYOROZU_EXECUTION_CHAIN_REQUIRED_EVALS,
            ]
        )
        digest_family = {
            "request_id": request_id,
            "artifact_id": artifact_id,
            "apply_receipt_id": apply_receipt_id,
            "live_enactment_session_id": enactment_session_id,
            "rollout_session_id": rollout_session_id,
            "rollback_session_id": rollback_session_id,
            "build_request_digest": build_request_digest,
            "build_artifact_digest": build_artifact_digest,
            "sandbox_apply_receipt_digest": sandbox_apply_receipt_digest,
            "live_enactment_session_digest": live_enactment_session_digest,
            "rollout_session_digest": rollout_session_digest,
            "rollback_session_digest": rollback_session_digest,
        }
        digest_family["family_digest"] = sha256_text(canonical_json(digest_family))

        execution_summary = {
            "execution_profile": "rollback-witness-same-request-v1",
            "target_subsystem": str(build_request.get("target_subsystem", "")),
            "candidate_review_signal": str(
                build_request_binding.get("handoff_summary", {}).get("candidate_signal", "no-candidates")
            ),
            "selected_candidate_count": len(selected_patch_candidates),
            "matched_candidate_target_count": sum(
                target in patch_targets for target in selected_candidate_targets
            ),
            "patch_count": len(build_artifact.get("patches", [])),
            "applied_patch_count": int(sandbox_apply_receipt.get("applied_patch_count", 0)),
            "live_eval_refs": list(live_enactment_session.get("eval_refs", [])),
            "live_command_count": int(live_enactment_session.get("executed_command_count", 0)),
            "required_eval_refs": required_eval_refs,
            "rollout_decision": str(rollout_session.get("decision", "")),
            "rollback_trigger": str(rollback_session.get("trigger", "")),
            "reverted_patch_count": int(rollback_session.get("reverted_patch_count", 0)),
            "reverted_stage_ids": list(rollback_session.get("reverted_stage_ids", [])),
            "reviewer_network_attested": (
                bool(live_enactment_session.get("oversight_gate", {}).get("reviewer_network_attested"))
                and bool(rollback_session.get("telemetry_gate", {}).get("reviewer_network_attested"))
            ),
        }

        validation = {
            "build_request_binding_ok": build_request_binding.get("validation", {}).get("ok") is True,
            "artifact_request_bound": (
                build_artifact.get("request_id") == request_id and build_artifact.get("status") == "ready"
            ),
            "sandbox_apply_bound": (
                sandbox_apply_receipt.get("request_id") == request_id
                and sandbox_apply_receipt.get("artifact_id") == artifact_id
                and sandbox_apply_receipt.get("status") == "applied"
                and sandbox_apply_receipt.get("rollback_plan_ref") == rollback_plan_ref
            ),
            "live_enactment_bound": (
                live_enactment_session.get("request_id") == request_id
                and live_enactment_session.get("artifact_id") == artifact_id
                and live_enactment_session.get("status") == "passed"
                and live_enactment_session.get("guardian_oversight_event", {}).get("payload_ref")
                == build_artifact_ref
            ),
            "rollout_bound": (
                rollout_session.get("request_id") == request_id
                and rollout_session.get("artifact_id") == artifact_id
                and rollout_session.get("apply_receipt_id") == apply_receipt_id
                and rollout_session.get("decision") == "rollback"
                and rollout_session.get("status") == "rolled-back"
            ),
            "rollback_bound": (
                rollback_session.get("request_id") == request_id
                and rollback_session.get("artifact_id") == artifact_id
                and rollback_session.get("apply_receipt_id") == apply_receipt_id
                and rollback_session.get("rollout_session_id") == rollout_session_id
                and rollback_session.get("live_enactment_session_id") == enactment_session_id
                and rollback_session.get("rollback_plan_ref") == rollback_plan_ref
                and rollback_session.get("status") == "rolled-back"
            ),
            "candidate_hints_bound": (
                build_request_binding.get("handoff_summary", {}).get("selected_candidate_count")
                == len(selected_patch_candidates)
                and all(
                    target_path in list(build_request.get("output_paths", []))
                    for target_path in selected_candidate_targets
                )
            ),
            "digest_family_bound": (
                digest_family["build_request_digest"] == build_request_digest
                and digest_family["build_artifact_digest"] == build_artifact_digest
                and digest_family["sandbox_apply_receipt_digest"] == sandbox_apply_receipt_digest
                and digest_family["live_enactment_session_digest"] == live_enactment_session_digest
                and digest_family["rollout_session_digest"] == rollout_session_digest
                and digest_family["rollback_session_digest"] == rollback_session_digest
            ),
            "reviewer_network_attested": execution_summary["reviewer_network_attested"] is True,
            "required_eval_refs_bound": (
                execution_summary["required_eval_refs"] == required_eval_refs
                and YAOYOROZU_EXECUTION_CHAIN_EVAL in required_eval_refs
            ),
        }
        validation["ok"] = all(validation.values())

        binding = {
            "kind": "yaoyorozu_execution_chain_binding",
            "schema_version": "1.0.0",
            "binding_id": new_id("yaoyorozu-execution-chain"),
            "binding_ref": "",
            "bound_at": utc_now_iso(),
            "binding_profile": self._policy.execution_chain_binding_profile,
            "proposal_profile": str(build_request_binding.get("proposal_profile", "")),
            "build_request_binding_ref": str(build_request_binding.get("binding_ref", "")),
            "build_request_binding_digest": str(build_request_binding.get("binding_digest", "")),
            "build_request_binding": dict(build_request_binding),
            "build_artifact_ref": build_artifact_ref,
            "build_artifact_digest": build_artifact_digest,
            "build_artifact": dict(build_artifact),
            "sandbox_apply_receipt_ref": sandbox_apply_receipt_ref,
            "sandbox_apply_receipt_digest": sandbox_apply_receipt_digest,
            "sandbox_apply_receipt": dict(sandbox_apply_receipt),
            "live_enactment_session_ref": live_enactment_session_ref,
            "live_enactment_session_digest": live_enactment_session_digest,
            "live_enactment_session": dict(live_enactment_session),
            "rollout_session_ref": rollout_session_ref,
            "rollout_session_digest": rollout_session_digest,
            "rollout_session": dict(rollout_session),
            "rollback_session_ref": rollback_session_ref,
            "rollback_session_digest": rollback_session_digest,
            "rollback_session": dict(rollback_session),
            "digest_family": digest_family,
            "execution_summary": execution_summary,
            "validation": validation,
        }
        binding["binding_ref"] = f"execution-chain-binding://{binding['binding_id']}"
        binding["binding_digest"] = sha256_text(
            canonical_json(_execution_chain_binding_digest_payload(binding))
        )
        return binding

    def validate_execution_chain(
        self,
        binding: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: List[str] = []
        if binding.get("kind") != "yaoyorozu_execution_chain_binding":
            errors.append("kind must equal yaoyorozu_execution_chain_binding")
        if binding.get("binding_profile") != self._policy.execution_chain_binding_profile:
            errors.append("binding_profile mismatch")

        build_request_binding = binding.get("build_request_binding", {})
        build_artifact = binding.get("build_artifact", {})
        sandbox_apply_receipt = binding.get("sandbox_apply_receipt", {})
        live_enactment_session = binding.get("live_enactment_session", {})
        rollout_session = binding.get("rollout_session", {})
        rollback_session = binding.get("rollback_session", {})
        digest_family = binding.get("digest_family", {})
        execution_summary = binding.get("execution_summary", {})
        validation = binding.get("validation", {})

        if not isinstance(build_request_binding, Mapping):
            errors.append("build_request_binding must be a mapping")
            build_request_binding = {}
        if not isinstance(build_artifact, Mapping):
            errors.append("build_artifact must be a mapping")
            build_artifact = {}
        if not isinstance(sandbox_apply_receipt, Mapping):
            errors.append("sandbox_apply_receipt must be a mapping")
            sandbox_apply_receipt = {}
        if not isinstance(live_enactment_session, Mapping):
            errors.append("live_enactment_session must be a mapping")
            live_enactment_session = {}
        if not isinstance(rollout_session, Mapping):
            errors.append("rollout_session must be a mapping")
            rollout_session = {}
        if not isinstance(rollback_session, Mapping):
            errors.append("rollback_session must be a mapping")
            rollback_session = {}
        if not isinstance(digest_family, Mapping):
            errors.append("digest_family must be a mapping")
            digest_family = {}
        if not isinstance(execution_summary, Mapping):
            errors.append("execution_summary must be a mapping")
            execution_summary = {}
        if not isinstance(validation, Mapping):
            errors.append("validation must be a mapping")
            validation = {}

        if build_request_binding.get("kind") != "yaoyorozu_build_request_binding":
            errors.append("build_request_binding.kind must equal yaoyorozu_build_request_binding")
        if build_artifact.get("kind") != "build_artifact":
            errors.append("build_artifact.kind must equal build_artifact")
        if sandbox_apply_receipt.get("kind") != "sandbox_apply_receipt":
            errors.append("sandbox_apply_receipt.kind must equal sandbox_apply_receipt")
        if live_enactment_session.get("kind") != "builder_live_enactment_session":
            errors.append("live_enactment_session.kind must equal builder_live_enactment_session")
        if rollout_session.get("kind") != "staged_rollout_session":
            errors.append("rollout_session.kind must equal staged_rollout_session")
        if rollback_session.get("kind") != "builder_rollback_session":
            errors.append("rollback_session.kind must equal builder_rollback_session")

        build_request = build_request_binding.get("build_request", {})
        request_id = str(build_request.get("request_id", ""))
        artifact_id = str(build_artifact.get("artifact_id", ""))
        apply_receipt_id = str(sandbox_apply_receipt.get("receipt_id", ""))
        enactment_session_id = str(live_enactment_session.get("enactment_session_id", ""))
        rollout_session_id = str(rollout_session.get("session_id", ""))
        rollback_session_id = str(rollback_session.get("rollback_session_id", ""))

        if binding.get("build_request_binding_ref") != build_request_binding.get("binding_ref"):
            errors.append("build_request_binding_ref must bind build_request_binding.binding_ref")
        if binding.get("build_request_binding_digest") != build_request_binding.get("binding_digest"):
            errors.append(
                "build_request_binding_digest must bind build_request_binding.binding_digest"
            )
        if binding.get("build_artifact_ref") != f"artifact://{artifact_id}":
            errors.append("build_artifact_ref must bind build_artifact.artifact_id")
        if binding.get("build_artifact_digest") != sha256_text(canonical_json(build_artifact)):
            errors.append("build_artifact_digest mismatch")
        if binding.get("sandbox_apply_receipt_ref") != f"sandbox-apply://{apply_receipt_id}":
            errors.append("sandbox_apply_receipt_ref must bind sandbox_apply_receipt.receipt_id")
        if binding.get("sandbox_apply_receipt_digest") != sha256_text(
            canonical_json(sandbox_apply_receipt)
        ):
            errors.append("sandbox_apply_receipt_digest mismatch")
        if binding.get("live_enactment_session_ref") != f"enactment-session://{enactment_session_id}":
            errors.append(
                "live_enactment_session_ref must bind live_enactment_session.enactment_session_id"
            )
        if binding.get("live_enactment_session_digest") != sha256_text(
            canonical_json(live_enactment_session)
        ):
            errors.append("live_enactment_session_digest mismatch")
        if binding.get("rollout_session_ref") != f"rollout-session://{rollout_session_id}":
            errors.append("rollout_session_ref must bind rollout_session.session_id")
        if binding.get("rollout_session_digest") != sha256_text(canonical_json(rollout_session)):
            errors.append("rollout_session_digest mismatch")
        if binding.get("rollback_session_ref") != f"rollback-session://{rollback_session_id}":
            errors.append("rollback_session_ref must bind rollback_session.rollback_session_id")
        if binding.get("rollback_session_digest") != sha256_text(canonical_json(rollback_session)):
            errors.append("rollback_session_digest mismatch")

        expected_required_eval_refs = _ordered_unique(
            [
                *list(build_request.get("constraints", {}).get("must_pass", [])),
                *YAOYOROZU_EXECUTION_CHAIN_REQUIRED_EVALS,
            ]
        )
        if execution_summary.get("required_eval_refs") != expected_required_eval_refs:
            errors.append("execution_summary.required_eval_refs mismatch")
        if execution_summary.get("target_subsystem") != self._policy.build_request_target_subsystem:
            errors.append("execution_summary.target_subsystem mismatch")
        if execution_summary.get("rollout_decision") != "rollback":
            errors.append("execution_summary.rollout_decision must equal rollback")
        if execution_summary.get("rollback_trigger") != "eval-regression":
            errors.append("execution_summary.rollback_trigger must equal eval-regression")
        if not bool(execution_summary.get("reviewer_network_attested")):
            errors.append("execution_summary.reviewer_network_attested must be true")

        expected_digest_family = {
            "request_id": request_id,
            "artifact_id": artifact_id,
            "apply_receipt_id": apply_receipt_id,
            "live_enactment_session_id": enactment_session_id,
            "rollout_session_id": rollout_session_id,
            "rollback_session_id": rollback_session_id,
            "build_request_digest": str(build_request_binding.get("build_request_digest", "")),
            "build_artifact_digest": str(binding.get("build_artifact_digest", "")),
            "sandbox_apply_receipt_digest": str(binding.get("sandbox_apply_receipt_digest", "")),
            "live_enactment_session_digest": str(binding.get("live_enactment_session_digest", "")),
            "rollout_session_digest": str(binding.get("rollout_session_digest", "")),
            "rollback_session_digest": str(binding.get("rollback_session_digest", "")),
        }
        expected_digest_family["family_digest"] = sha256_text(canonical_json(expected_digest_family))
        if dict(digest_family) != expected_digest_family:
            errors.append("digest_family mismatch")

        if validation.get("ok") is not True:
            errors.append("validation.ok must remain true")

        return {
            "ok": not errors,
            "patch_count": int(execution_summary.get("patch_count", 0)),
            "applied_patch_count": int(execution_summary.get("applied_patch_count", 0)),
            "reverted_patch_count": int(execution_summary.get("reverted_patch_count", 0)),
            "reviewer_network_attested": bool(execution_summary.get("reviewer_network_attested")),
            "errors": errors,
        }

    def _ensure_trust_seed(self, entry: YaoyorozuRegistryEntry) -> None:
        if self._trust.has_agent(entry.agent_id):
            return

        initial_score = max(self._policy.cold_start_score, entry.trust_floor)
        default_domain = "documentation"
        if entry.role in {"councilor", "guardian"}:
            default_domain = "council_deliberation"
        elif entry.role == "builder":
            default_domain = "self_modify"
        self._trust.register_agent(
            entry.agent_id,
            initial_score=initial_score,
            per_domain={default_domain: initial_score},
        )

    @staticmethod
    def _entry_scope_binding(
        entry: YaoyorozuRegistryEntry,
    ) -> Dict[str, Any]:
        if entry.role == "councilor":
            return {
                "role_scope_kind": "deliberation",
                "role_scope_refs": list(entry.deliberation_scope_refs),
                "role_policy_ref": entry.deliberation_policy_ref,
            }
        if entry.role == "builder":
            return {
                "role_scope_kind": "build-surface",
                "role_scope_refs": list(entry.build_surface_refs),
                "role_policy_ref": entry.execution_policy_ref,
            }
        if entry.role == "researcher":
            return {
                "role_scope_kind": "research-evidence",
                "role_scope_refs": list(entry.research_domain_refs),
                "role_policy_ref": entry.evidence_policy_ref,
            }
        if entry.role == "guardian":
            return {
                "role_scope_kind": "oversight",
                "role_scope_refs": list(entry.oversight_scope_refs),
                "role_policy_ref": entry.attestation_policy_ref,
            }
        return {
            "role_scope_kind": "unbound",
            "role_scope_refs": [],
            "role_policy_ref": "",
        }

    @staticmethod
    def _selection_scope_bound(
        selection: Mapping[str, Any],
        expected_kind: str,
    ) -> bool:
        if selection.get("status") != "selected":
            return False
        return (
            selection.get("role_scope_kind") == expected_kind
            and bool(selection.get("role_scope_refs"))
            and bool(selection.get("role_policy_ref"))
            and selection.get("selection_scope_binding_profile")
            == YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE
            and selection.get("raw_role_scope_payload_stored") is False
        )

    @staticmethod
    def _selection_has_registry_scope(
        selection: Mapping[str, Any],
        allowed_kinds: Sequence[str],
    ) -> bool:
        if selection.get("status") != "selected":
            return False
        return (
            selection.get("role_scope_kind") in set(allowed_kinds)
            and bool(selection.get("role_scope_refs"))
            and bool(selection.get("role_policy_ref"))
            and selection.get("selection_scope_binding_profile")
            == YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE
            and selection.get("raw_role_scope_payload_stored") is False
        )

    @classmethod
    def _builder_selection_scope_bound(cls, selection: Mapping[str, Any]) -> bool:
        if not cls._selection_scope_bound(selection, "build-surface"):
            return False
        coverage_area = str(selection.get("coverage_area", "")).strip()
        target_path_refs = [str(ref) for ref in selection.get("coverage_target_path_refs", [])]
        expected_targets = list(YAOYOROZU_WORKER_TARGET_PATHS.get(coverage_area, []))
        scope_refs = [str(ref) for ref in selection.get("role_scope_refs", [])]
        target_paths_bound = bool(expected_targets) and target_path_refs == expected_targets
        target_paths_bound = target_paths_bound and all(
            any(
                target_ref == scope_ref or target_ref.startswith(scope_ref)
                for scope_ref in scope_refs
            )
            for target_ref in target_path_refs
        )
        return (
            target_paths_bound
            and selection.get("coverage_scope_binding_profile")
            == YAOYOROZU_COVERAGE_SCOPE_BINDING_PROFILE
            and selection.get("coverage_targets_bound") is True
        )

    def _select_named_agent(
        self,
        *,
        role_id: str,
        role_label: str,
        candidate_agents: Sequence[str],
        required_eligibility: str,
        coverage_area: str = "",
    ) -> Dict[str, Any]:
        ranked: List[Dict[str, Any]] = []
        for agent_id in candidate_agents:
            entry = self._entries.get(agent_id)
            if entry is None:
                continue
            trust_snapshot = self._trust.snapshot(agent_id)
            invite_eligible = (
                trust_snapshot["eligibility"]["invite_to_council"]
                and trust_snapshot["global_score"] >= max(entry.trust_floor, self._policy.council_invite_floor)
            )
            weighted_vote_eligible = (
                trust_snapshot["eligibility"]["count_for_weighted_vote"]
                and trust_snapshot["global_score"] >= max(entry.trust_floor, self._policy.weighted_vote_floor)
            )
            apply_to_runtime_eligible = (
                trust_snapshot["eligibility"]["apply_to_runtime"]
                and trust_snapshot["global_score"] >= max(entry.trust_floor, self._policy.apply_floor)
            )
            scope_binding = self._entry_scope_binding(entry)
            selected_ok = {
                "invite_to_council": invite_eligible,
                "count_for_weighted_vote": weighted_vote_eligible,
                "guardian_role": trust_snapshot["eligibility"]["guardian_role"],
                "apply_to_runtime": apply_to_runtime_eligible,
            }[required_eligibility]
            ranked.append(
                {
                    "agent_id": agent_id,
                    "display_name": entry.display_name,
                    "source_ref": entry.source_ref,
                    "selected_role": entry.role,
                    "role_scope_kind": scope_binding["role_scope_kind"],
                    "role_scope_refs": scope_binding["role_scope_refs"],
                    "role_policy_ref": scope_binding["role_policy_ref"],
                    "selection_scope_binding_profile": YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE,
                    "raw_role_scope_payload_stored": False,
                    "trust_score": round(trust_snapshot["global_score"], 3),
                    "invite_eligible": invite_eligible,
                    "weighted_vote_eligible": weighted_vote_eligible,
                    "apply_to_runtime_eligible": apply_to_runtime_eligible,
                    "selected_ok": selected_ok,
                    "sort_key": (
                        1 if selected_ok else 0,
                        round(trust_snapshot["global_score"], 3),
                        agent_id,
                    ),
                }
            )
        ranked.sort(key=lambda candidate: candidate["sort_key"], reverse=True)
        selected = ranked[0] if ranked else None
        result = {
            "role_id": role_id,
            "role_label": role_label,
            "selected_agent_id": selected["agent_id"] if selected and selected["selected_ok"] else "",
            "display_name": selected["display_name"] if selected else "",
            "source_ref": selected["source_ref"] if selected else "",
            "selected_role": selected["selected_role"] if selected else "",
            "role_scope_kind": selected["role_scope_kind"] if selected else "unbound",
            "role_scope_refs": list(selected["role_scope_refs"]) if selected else [],
            "role_policy_ref": selected["role_policy_ref"] if selected else "",
            "selection_scope_binding_profile": (
                selected["selection_scope_binding_profile"]
                if selected
                else YAOYOROZU_SELECTION_SCOPE_BINDING_PROFILE
            ),
            "raw_role_scope_payload_stored": False,
            "status": "selected" if selected and selected["selected_ok"] else ("blocked" if ranked else "missing"),
            "trust_score": selected["trust_score"] if selected else 0.0,
            "invite_eligible": selected["invite_eligible"] if selected else False,
            "weighted_vote_eligible": selected["weighted_vote_eligible"] if selected else False,
            "apply_to_runtime_eligible": selected["apply_to_runtime_eligible"] if selected else False,
            "candidate_count": len(ranked),
            "candidate_agent_ids": [candidate["agent_id"] for candidate in ranked],
            "selection_reason": (
                f"Top-{self._policy.top_k_per_role} deterministic candidate selected from repo-local agent registry."
                if selected and selected["selected_ok"]
                else f"No candidate satisfied {required_eligibility}."
            ),
        }
        if coverage_area:
            result["coverage_area"] = coverage_area
            target_path_refs = list(self._policy.worker_target_paths.get(coverage_area, []))
            scope_refs = [str(ref) for ref in result["role_scope_refs"]]
            result["coverage_target_path_refs"] = target_path_refs
            result["coverage_scope_binding_profile"] = YAOYOROZU_COVERAGE_SCOPE_BINDING_PROFILE
            result["coverage_targets_bound"] = bool(target_path_refs) and all(
                any(
                    target_ref == scope_ref or target_ref.startswith(scope_ref)
                    for scope_ref in scope_refs
                )
                for target_ref in target_path_refs
            )
        return result
