"""Repo-local worker report generator used by the Yaoyorozu dispatch demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from ..common import canonical_json, sha256_text


YAOYOROZU_WORKER_REPORT_KIND = "yaoyorozu_local_worker_report"
YAOYOROZU_WORKER_REPORT_PROFILE = "repo-local-path-bound-worker-report-v1"
YAOYOROZU_WORKER_READY_GATE_PROFILE = "path-bound-target-scan-v1"
YAOYOROZU_WORKER_SAMPLE_ENTRY_LIMIT = 3


def build_worker_report_binding_digest(
    *,
    dispatch_plan_ref: str,
    dispatch_unit_ref: str,
    agent_id: str,
    role_id: str,
    coverage_area: str,
    dispatch_profile: str,
    workspace_scope: str,
    source_ref: str,
    workspace_root: str,
    target_paths: list[str],
) -> str:
    payload = {
        "dispatch_plan_ref": dispatch_plan_ref,
        "dispatch_unit_ref": dispatch_unit_ref,
        "agent_id": agent_id,
        "role_id": role_id,
        "coverage_area": coverage_area,
        "dispatch_profile": dispatch_profile,
        "workspace_scope": workspace_scope,
        "source_ref": source_ref,
        "workspace_root": workspace_root,
        "target_paths": target_paths,
    }
    return sha256_text(canonical_json(payload))


def _path_within_workspace(workspace_root: Path, candidate: Path) -> bool:
    try:
        common = os.path.commonpath([str(workspace_root), str(candidate)])
    except ValueError:
        return False
    return common == str(workspace_root)


def _sample_entries(path: Path) -> tuple[int, list[str]]:
    if path.is_dir():
        children = sorted(child.name for child in path.iterdir())
        return len(children), children[:YAOYOROZU_WORKER_SAMPLE_ENTRY_LIMIT]
    if path.is_file():
        return 1, [path.name]
    return 0, []


def _observe_target_paths(workspace_root: Path, target_paths: list[str]) -> list[dict[str, object]]:
    observations: list[dict[str, object]] = []
    for target_path in target_paths:
        resolved = (workspace_root / target_path).resolve()
        exists = resolved.exists()
        path_kind = "missing"
        if exists and resolved.is_dir():
            path_kind = "directory"
        elif exists and resolved.is_file():
            path_kind = "file"
        entry_count, sample_entries = _sample_entries(resolved) if exists else (0, [])
        observation = {
            "target_path": target_path,
            "resolved_path": str(resolved),
            "exists": exists,
            "path_kind": path_kind,
            "within_workspace": _path_within_workspace(workspace_root, resolved),
            "entry_count": entry_count,
            "sample_entries": sample_entries,
        }
        observation["observation_digest"] = sha256_text(canonical_json(observation))
        observations.append(observation)
    return observations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit one bounded Yaoyorozu worker report.")
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--role-id", required=True)
    parser.add_argument("--coverage-area", required=True)
    parser.add_argument("--dispatch-profile", required=True)
    parser.add_argument("--workspace-scope", required=True)
    parser.add_argument("--dispatch-plan-ref", required=True)
    parser.add_argument("--dispatch-unit-ref", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--target-path", action="append", dest="target_paths", default=[])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    workspace_root = Path(args.workspace_root).resolve()
    target_paths = list(args.target_paths)
    target_path_observations = _observe_target_paths(workspace_root, target_paths)
    coverage_evidence = {
        "expected_target_count": len(target_paths),
        "observed_target_count": len(target_path_observations),
        "existing_target_count": sum(
            1 for observation in target_path_observations if observation["exists"] is True
        ),
        "all_targets_exist": all(
            observation["exists"] is True for observation in target_path_observations
        ),
        "all_targets_within_workspace": all(
            observation["within_workspace"] is True for observation in target_path_observations
        ),
        "ready_gate": YAOYOROZU_WORKER_READY_GATE_PROFILE,
    }
    status = (
        "ready"
        if coverage_evidence["all_targets_exist"] and coverage_evidence["all_targets_within_workspace"]
        else "failed"
    )
    report = {
        "kind": YAOYOROZU_WORKER_REPORT_KIND,
        "report_profile": YAOYOROZU_WORKER_REPORT_PROFILE,
        "agent_id": args.agent_id,
        "role_id": args.role_id,
        "coverage_area": args.coverage_area,
        "dispatch_profile": args.dispatch_profile,
        "workspace_scope": args.workspace_scope,
        "dispatch_plan_ref": args.dispatch_plan_ref,
        "dispatch_unit_ref": args.dispatch_unit_ref,
        "source_ref": args.source_ref,
        "target_paths": target_paths,
        "workspace_root": str(workspace_root),
        "workspace_root_digest": sha256_text(str(workspace_root)),
        "invocation_digest": build_worker_report_binding_digest(
            dispatch_plan_ref=args.dispatch_plan_ref,
            dispatch_unit_ref=args.dispatch_unit_ref,
            agent_id=args.agent_id,
            role_id=args.role_id,
            coverage_area=args.coverage_area,
            dispatch_profile=args.dispatch_profile,
            workspace_scope=args.workspace_scope,
            source_ref=args.source_ref,
            workspace_root=str(workspace_root),
            target_paths=target_paths,
        ),
        "target_path_observations": target_path_observations,
        "coverage_evidence": coverage_evidence,
        "status": status,
    }
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
