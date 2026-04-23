"""Repo-local Yaoyorozu registry and bounded council convocation helpers."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .consensus_bus import CONSENSUS_BUS_PHASE_ORDER, CONSENSUS_BUS_TRANSPORT_PROFILE
from .local_worker_stub import (
    YAOYOROZU_WORKER_READY_GATE_PROFILE,
    YAOYOROZU_WORKER_REPORT_KIND,
    YAOYOROZU_WORKER_REPORT_PROFILE,
    build_worker_report_binding_digest,
)
from .task_graph import TaskGraphService
from .trust import TrustService


YAOYOROZU_WORKER_DISPATCH_PROFILE = "repo-local-subprocess-worker-dispatch-v1"
YAOYOROZU_WORKER_EXECUTION_PROFILE = "repo-local-subprocess-worker-execution-v1"
YAOYOROZU_CONSENSUS_BINDING_PROFILE = "repo-local-yaoyorozu-consensus-bus-binding-v1"
YAOYOROZU_TASK_GRAPH_BINDING_PROFILE = "repo-local-yaoyorozu-task-graph-binding-v1"
YAOYOROZU_WORKSPACE_DISCOVERY_PROFILE = "same-host-local-workspace-discovery-v1"
YAOYOROZU_WORKSPACE_DISCOVERY_SCOPE = "same-host-local-workspace-catalog"
YAOYOROZU_WORKSPACE_DISCOVERY_HOST_REF = "host://local-loopback"
YAOYOROZU_WORKSPACE_DISCOVERY_MAX_WORKSPACES = 3
YAOYOROZU_WORKER_DISPATCH_SCOPE = "repo-local-subprocess"
YAOYOROZU_WORKER_SANDBOX_MODE = "temp-workspace-only"
YAOYOROZU_WORKER_ENTRYPOINT_REF = "python-module://omoikane.agentic.local_worker_stub"
YAOYOROZU_WORKSPACE_SCOPE = "repo-local"
YAOYOROZU_PROPOSAL_PROFILES = (
    "self-modify-patch-v1",
    "memory-edit-v1",
    "fork-request-v1",
)
YAOYOROZU_WORKER_TARGET_PATHS = {
    "runtime": ["src/omoikane/", "tests/unit/", "tests/integration/"],
    "schema": ["specs/interfaces/", "specs/schemas/"],
    "eval": ["evals/"],
    "docs": ["docs/", "meta/decision-log/"],
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
    "coverage_evidence",
    "status",
]
YAOYOROZU_TASK_GRAPH_ROOT_BUNDLES = (
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
)


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
        "convocation_session_ref": binding["convocation_session_ref"],
        "convocation_session_digest": binding["convocation_session_digest"],
        "dispatch_plan_ref": binding["dispatch_plan_ref"],
        "dispatch_plan_digest": binding["dispatch_plan_digest"],
        "dispatch_receipt_ref": binding["dispatch_receipt_ref"],
        "dispatch_receipt_digest": binding["dispatch_receipt_digest"],
        "consensus_binding_ref": binding["consensus_binding_ref"],
        "consensus_binding_digest": binding["consensus_binding_digest"],
        "consensus_session_id": binding["consensus_session_id"],
        "task_graph_ref": binding["task_graph_ref"],
        "task_graph_digest": binding["task_graph_digest"],
        "task_graph_dispatch_digest": binding["task_graph_dispatch_digest"],
        "task_graph_synthesis_digest": binding["task_graph_synthesis_digest"],
        "guardian_gate_message_digest": binding["guardian_gate_message_digest"],
        "resolve_message_digest": binding["resolve_message_digest"],
        "node_bindings": binding["node_bindings"],
        "validation": binding["validation"],
    }


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


def _workspace_discovery_digest_payload(discovery: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": discovery["schema_version"],
        "discovery_profile": discovery["discovery_profile"],
        "discovery_scope": discovery["discovery_scope"],
        "source_workspace_ref": discovery["source_workspace_ref"],
        "host_ref": discovery["host_ref"],
        "review_budget": discovery["review_budget"],
        "workspace_roots": discovery["workspace_roots"],
        "accepted_workspace_refs": discovery["accepted_workspace_refs"],
        "coverage_summary": discovery["coverage_summary"],
        "workspaces": discovery["workspaces"],
        "validation": discovery["validation"],
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

    def to_dict(self, trust_snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        return {
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
    workspace_discovery_profile: str = YAOYOROZU_WORKSPACE_DISCOVERY_PROFILE
    workspace_discovery_scope: str = YAOYOROZU_WORKSPACE_DISCOVERY_SCOPE
    workspace_discovery_host_ref: str = YAOYOROZU_WORKSPACE_DISCOVERY_HOST_REF
    workspace_review_budget: int = YAOYOROZU_WORKSPACE_DISCOVERY_MAX_WORKSPACES
    task_graph_binding_profile: str = YAOYOROZU_TASK_GRAPH_BINDING_PROFILE
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
    task_graph_root_bundles: List[Dict[str, Any]] = field(
        default_factory=lambda: [
            {
                "bundle_role": str(bundle["bundle_role"]),
                "coverage_areas": [str(area) for area in bundle["coverage_areas"]],
            }
            for bundle in YAOYOROZU_TASK_GRAPH_ROOT_BUNDLES
        ]
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
            },
            "memory-edit-v1": {
                "summary": "Prepare a bounded Council review and reversible memory-edit handoff for one recall-affect-buffer session.",
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
            },
            "fork-request-v1": {
                "summary": "Prepare a bounded Council review and triple-approval fork handoff for one identity fork request.",
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
    ) -> None:
        self._trust = trust_service or TrustService()
        self._policy = policy or YaoyorozuRegistryPolicy()
        self._entries: Dict[str, YaoyorozuRegistryEntry] = {}
        self._agents_root: Optional[Path] = None
        self._last_snapshot_id: Optional[str] = None

    def policy_snapshot(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def discover_workspace_workers(
        self,
        workspace_roots: Sequence[str | Path],
        *,
        review_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        if len(workspace_roots) < 2:
            raise ValueError("workspace_roots must contain at least two local workspaces")
        budget = review_budget or self._policy.workspace_review_budget
        if budget < 2 or budget > self._policy.workspace_review_budget:
            raise ValueError(
                f"review_budget must be between 2 and {self._policy.workspace_review_budget}"
            )

        normalized_roots = [
            Path(_non_empty_string(str(root), "workspace_root")).resolve()
            for root in workspace_roots
        ]
        if len(normalized_roots) > budget:
            raise ValueError("workspace_roots must not exceed review_budget")
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
        workspaces: List[Dict[str, Any]] = []
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
            workspaces.append(workspace)
            for coverage_area in supported_coverage_areas:
                coverage_to_workspace_refs[coverage_area].append(workspace["workspace_ref"])
                if workspace_index > 1:
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
        coverage_summary = {
            "required_coverage_areas": required_coverage,
            "supported_coverage_areas": supported_coverage_areas,
            "missing_coverage_areas": missing_coverage_areas,
            "non_source_supported_coverage_areas": non_source_supported_coverage_areas,
            "non_source_missing_coverage_areas": non_source_missing_coverage_areas,
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
            "cross_workspace_coverage_complete": not non_source_missing_coverage_areas,
        }
        validation["ok"] = all(validation.values())
        discovery = {
            "kind": "yaoyorozu_workspace_discovery",
            "schema_version": "1.0.0",
            "discovery_id": new_id("yaoyorozu-workspace-discovery"),
            "discovered_at": utc_now_iso(),
            "discovery_profile": self._policy.workspace_discovery_profile,
            "discovery_scope": self._policy.workspace_discovery_scope,
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
        if sorted({*supported_coverage_areas, *missing_coverage_areas}) != sorted(required_coverage):
            errors.append("coverage_summary must partition the required coverage areas")
        if sorted({*non_source_supported, *non_source_missing}) != sorted(required_coverage):
            errors.append("non_source coverage summary must partition the required coverage areas")
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
            "cross_workspace_coverage_complete": not non_source_missing,
            "errors": errors,
        }

    def sync_from_agents_directory(self, agents_root: Path) -> Dict[str, Any]:
        repo_root = agents_root.resolve().parent
        self._entries = {}
        for definition_path in sorted(agents_root.resolve().rglob("*.yaml")):
            parsed = _parse_agent_definition(definition_path)
            agent_id = str(parsed.get("name") or definition_path.stem).strip()
            entry = YaoyorozuRegistryEntry(
                agent_id=agent_id,
                display_name=_pascal_case(agent_id),
                role=str(parsed.get("role", "unknown")).strip() or "unknown",
                source_ref=str(definition_path.relative_to(repo_root)),
                capabilities=_normalize_string_list(parsed.get("capabilities", [])),
                trust_floor=float(parsed.get("trust_floor", self._policy.cold_start_score)),
                substrate_requirements=_normalize_string_list(
                    parsed.get("substrate_requirements", [])
                ),
                input_schema_ref=str(parsed.get("input_schema_ref", "")).strip(),
                output_schema_ref=str(parsed.get("output_schema_ref", "")).strip(),
                ethics_constraints=_normalize_string_list(parsed.get("ethics_constraints", [])),
                prompt_or_policy_ref=str(parsed.get("prompt_or_policy_ref", "")).strip(),
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

        snapshot_body = {
            "policy_id": self._policy.policy_id,
            "source_root": str(self._agents_root.relative_to(repo_root)),
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

    def prepare_council_convocation(
        self,
        *,
        proposal_profile: str | None = None,
        session_mode: str = "standard",
        target_identity_ref: str = "identity://primary",
    ) -> Dict[str, Any]:
        if not self._entries:
            raise ValueError("registry must be synced before preparing a convocation")
        profile_id = proposal_profile or self._policy.default_convocation_profile
        if profile_id not in self._policy.council_profiles:
            raise ValueError(f"unsupported convocation profile: {profile_id}")

        profile = self._policy.council_profiles[profile_id]
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
        ]

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
        }
        validation["ok"] = all(validation.values())
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
                "selected_builder_coverage_count": len(builder_handoff) - len(missing_builder_coverage),
                "missing_council_roles": missing_council_roles,
                "missing_builder_coverage": missing_builder_coverage,
            },
            "validation": validation,
        }
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
                self._policy.worker_workspace_scope,
                "--dispatch-plan-ref",
                dispatch_plan_ref,
                "--dispatch-unit-ref",
                unit_id,
                "--workspace-root",
                str(repo_root),
                "--source-ref",
                _non_empty_string(selection.get("source_ref"), "builder_handoff.source_ref"),
            ]
            for target_path in target_paths:
                command_preview.extend(["--target-path", target_path])

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
                "workspace_scope": self._policy.worker_workspace_scope,
                "entrypoint_ref": self._policy.worker_entrypoint_ref,
                "command_preview": command_preview,
                "target_paths": target_paths,
                "expected_report_fields": list(YAOYOROZU_WORKER_REPORT_FIELDS),
            }
            unit["command_digest"] = sha256_text(canonical_json(_dispatch_unit_digest_payload(unit)))
            dispatch_units.append(unit)
            selected_coverage.append(coverage_area)

        required_coverage = list(self._policy.worker_target_paths)
        missing_coverage = [coverage for coverage in required_coverage if coverage not in selected_coverage]
        unique_command_digests = len({unit["command_digest"] for unit in dispatch_units}) == len(dispatch_units)
        validation = {
            "registry_bound": bool(self._last_snapshot_id),
            "convocation_bound": bool(convocation_session.get("session_id")),
            "builder_coverage_ok": not missing_coverage and len(dispatch_units) == len(required_coverage),
            "unique_command_digests": unique_command_digests,
            "repo_local_scope_only": all(
                unit["dispatch_scope"] == self._policy.worker_dispatch_scope
                and unit["workspace_scope"] == self._policy.worker_workspace_scope
                for unit in dispatch_units
            ),
        }
        validation["ok"] = all(validation.values())
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
                "selected_worker_count": len(dispatch_units),
                "unique_coverage_areas": sorted(set(selected_coverage)),
                "missing_coverage": missing_coverage,
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

        coverage_areas: List[str] = []
        digests: List[str] = []
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
            if unit.get("workspace_scope") != self._policy.worker_workspace_scope:
                errors.append("dispatch unit workspace_scope must be repo-local")
            if unit.get("entrypoint_ref") != self._policy.worker_entrypoint_ref:
                errors.append("dispatch unit entrypoint_ref mismatch")
            command_preview = unit.get("command_preview", [])
            if f"dispatch://{dispatch_plan.get('dispatch_id', '')}" not in command_preview:
                errors.append("dispatch unit command preview must bind the dispatch plan ref")
            if str(unit.get("unit_id", "")) not in command_preview:
                errors.append("dispatch unit command preview must bind the dispatch unit ref")

        missing_coverage = [
            coverage for coverage in self._policy.worker_target_paths if coverage not in coverage_areas
        ]
        if len(set(digests)) != len(digests):
            errors.append("dispatch unit command digests must be unique")

        return {
            "ok": not errors and not missing_coverage,
            "dispatch_unit_count": len(units),
            "unique_coverage_areas": sorted(set(coverage_areas)),
            "missing_coverage": missing_coverage,
            "runtime_exec_ready": bool(units),
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
            command = [sys.executable if preview[0] == "python3" else preview[0], *preview[1:]]
            process = subprocess.Popen(
                command,
                cwd=repo_root,
                env=env,
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
                workspace_scope=self._policy.worker_workspace_scope,
                source_ref=str(unit["source_ref"]),
                workspace_root=str(repo_root),
                target_paths=list(unit["target_paths"]),
            )
            if not report:
                report = {
                    "kind": YAOYOROZU_WORKER_REPORT_KIND,
                    "report_profile": YAOYOROZU_WORKER_REPORT_PROFILE,
                    "agent_id": unit["selected_agent_id"],
                    "role_id": unit["role_id"],
                    "coverage_area": unit["coverage_area"],
                    "dispatch_profile": dispatch_plan["dispatch_profile"],
                    "workspace_scope": self._policy.worker_workspace_scope,
                    "dispatch_plan_ref": dispatch_plan_ref,
                    "dispatch_unit_ref": unit["unit_id"],
                    "source_ref": unit["source_ref"],
                    "target_paths": list(unit["target_paths"]),
                    "workspace_root": str(repo_root),
                    "workspace_root_digest": sha256_text(str(repo_root)),
                    "invocation_digest": expected_binding_digest,
                    "target_path_observations": [],
                    "coverage_evidence": {
                        "expected_target_count": len(unit["target_paths"]),
                        "observed_target_count": 0,
                        "existing_target_count": 0,
                        "all_targets_exist": False,
                        "all_targets_within_workspace": False,
                        "ready_gate": YAOYOROZU_WORKER_READY_GATE_PROFILE,
                    },
                    "status": "failed",
                }
            coverage_evidence = report.get("coverage_evidence", {})
            report_binding_ok = (
                report.get("report_profile") == YAOYOROZU_WORKER_REPORT_PROFILE
                and report.get("dispatch_plan_ref") == dispatch_plan_ref
                and report.get("dispatch_unit_ref") == unit["unit_id"]
                and report.get("workspace_root") == str(repo_root)
                and report.get("invocation_digest") == expected_binding_digest
                and report.get("source_ref") == unit["source_ref"]
                and report.get("target_paths") == unit["target_paths"]
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
                "target_paths_ready": target_paths_ready,
                "report": report,
            }
            if (
                process.returncode != 0
                or report.get("status") != "ready"
                or not report_binding_ok
                or not target_paths_ready
            ):
                failed_role_ids.append(str(unit["role_id"]))
            results.append(result)

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
                and result["target_paths_ready"]
            ),
            "failed_role_ids": failed_role_ids,
            "coverage_areas": [str(result["coverage_area"]) for result in results],
            "target_ready_count": sum(1 for result in results if result["target_paths_ready"]),
            "ready_gate_profile": YAOYOROZU_WORKER_READY_GATE_PROFILE,
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
            "coverage_complete": sorted(execution_summary["coverage_areas"])
            == sorted(
                [
                    str(unit["coverage_area"])
                    for unit in units
                    if isinstance(unit, Mapping)
                ]
            ),
            "all_reports_bound_to_dispatch": all(
                result["report_binding_ok"] for result in results
            ),
            "all_target_paths_ready": all(result["target_paths_ready"] for result in results),
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
        if not isinstance(results, list) or not results:
            errors.append("results must be a non-empty list")
            results = []

        coverage_areas: List[str] = []
        for result in results:
            if not isinstance(result, Mapping):
                errors.append("results entries must be mappings")
                continue
            coverage_areas.append(str(result.get("coverage_area", "")))
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
            if report.get("workspace_scope") != self._policy.worker_workspace_scope:
                errors.append("worker report workspace_scope must be repo-local")
            if report.get("dispatch_profile") != self._policy.worker_dispatch_profile:
                errors.append("worker report dispatch_profile mismatch")
            if report.get("dispatch_plan_ref") != dispatch_receipt.get("dispatch_plan_ref"):
                errors.append("worker report dispatch_plan_ref must match receipt")
            if result.get("report_binding_ok") is not True:
                errors.append("worker report must remain bound to the dispatch unit")
            if result.get("target_paths_ready") is not True:
                errors.append("worker report must prove target path readiness")
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
            if result.get("exit_code") != 0:
                errors.append("worker process exit_code must be 0")

        missing_coverage = [
            coverage for coverage in self._policy.worker_target_paths if coverage not in coverage_areas
        ]
        return {
            "ok": not errors and not missing_coverage,
            "completed_process_count": sum(
                1
                for result in results
                if isinstance(result, Mapping) and result.get("process_status") == "completed"
            ),
            "success_count": sum(
                1
                for result in results
                if isinstance(result, Mapping)
                and result.get("process_status") == "completed"
                and result.get("exit_code") == 0
                and result.get("reported_status") == "ready"
            ),
            "coverage_complete": not missing_coverage,
            "missing_coverage": missing_coverage,
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
        for bundle in self._policy.task_graph_root_bundles:
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
            ",".join(sorted(bundle["coverage_areas"])) for bundle in bundle_specs
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
            "convocation_session_ref": convocation_session_ref,
            "convocation_session_digest": convocation_session["session_digest"],
            "dispatch_plan_ref": dispatch_plan_ref,
            "dispatch_plan_digest": dispatch_plan["dispatch_digest"],
            "dispatch_receipt_ref": dispatch_receipt_ref,
            "dispatch_receipt_digest": dispatch_receipt["receipt_digest"],
            "consensus_binding_ref": consensus_binding_ref,
            "consensus_binding_digest": consensus_binding["binding_digest"],
            "consensus_session_id": session_id,
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
            "worker_claims_bound": validation.get("worker_claims_bound") is True,
            "coverage_grouping_ok": validation.get("coverage_grouping_ok") is True,
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
        return result
