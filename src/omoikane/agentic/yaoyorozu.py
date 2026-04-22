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
from .trust import TrustService


YAOYOROZU_WORKER_DISPATCH_PROFILE = "repo-local-subprocess-worker-dispatch-v1"
YAOYOROZU_WORKER_EXECUTION_PROFILE = "repo-local-subprocess-worker-execution-v1"
YAOYOROZU_WORKER_DISPATCH_SCOPE = "repo-local-subprocess"
YAOYOROZU_WORKER_SANDBOX_MODE = "temp-workspace-only"
YAOYOROZU_WORKER_ENTRYPOINT_REF = "python-module://omoikane.agentic.local_worker_stub"
YAOYOROZU_WORKSPACE_SCOPE = "repo-local"
YAOYOROZU_WORKER_TARGET_PATHS = {
    "runtime": ["src/omoikane/", "tests/unit/", "tests/integration/"],
    "schema": ["specs/interfaces/", "specs/schemas/"],
    "eval": ["evals/"],
    "docs": ["docs/", "meta/decision-log/"],
}
YAOYOROZU_WORKER_REPORT_KIND = "yaoyorozu_local_worker_report"
YAOYOROZU_WORKER_REPORT_FIELDS = [
    "kind",
    "agent_id",
    "role_id",
    "coverage_area",
    "dispatch_profile",
    "workspace_scope",
    "source_ref",
    "target_paths",
    "status",
]


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
    top_k_per_role: int = 1
    worker_target_paths: Dict[str, List[str]] = field(
        default_factory=lambda: {
            coverage_area: list(paths)
            for coverage_area, paths in YAOYOROZU_WORKER_TARGET_PATHS.items()
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
            }
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
                "--source-ref",
                _non_empty_string(selection.get("source_ref"), "builder_handoff.source_ref"),
            ]
            for target_path in target_paths:
                command_preview.extend(["--target-path", target_path])

            unit = {
                "unit_id": new_id("worker-dispatch"),
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
            "dispatch_id": new_id("yaoyorozu-dispatch"),
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
            if not report:
                report = {
                    "kind": YAOYOROZU_WORKER_REPORT_KIND,
                    "agent_id": unit["selected_agent_id"],
                    "role_id": unit["role_id"],
                    "coverage_area": unit["coverage_area"],
                    "dispatch_profile": dispatch_plan["dispatch_profile"],
                    "workspace_scope": self._policy.worker_workspace_scope,
                    "source_ref": unit["source_ref"],
                    "target_paths": list(unit["target_paths"]),
                    "status": "failed",
                }

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
                "report": report,
            }
            if process.returncode != 0 or report.get("status") != "ready":
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
            ),
            "failed_role_ids": failed_role_ids,
            "coverage_areas": [str(result["coverage_area"]) for result in results],
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
            if report.get("status") != "ready":
                errors.append("worker report status must be ready")
            if report.get("workspace_scope") != self._policy.worker_workspace_scope:
                errors.append("worker report workspace_scope must be repo-local")
            if report.get("dispatch_profile") != self._policy.worker_dispatch_profile:
                errors.append("worker report dispatch_profile mismatch")
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

    def _ensure_trust_seed(self, entry: YaoyorozuRegistryEntry) -> None:
        try:
            self._trust.snapshot(entry.agent_id)
            return
        except KeyError:
            pass

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
