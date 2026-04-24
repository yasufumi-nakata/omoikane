"""Repo-local worker report generator used by the Yaoyorozu dispatch demo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any, Mapping

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


YAOYOROZU_WORKER_REPORT_KIND = "yaoyorozu_local_worker_report"
YAOYOROZU_WORKER_REPORT_PROFILE = "repo-local-path-bound-worker-report-v3"
YAOYOROZU_WORKER_READY_GATE_PROFILE = "path-bound-target-delta-patch-candidate-v3"
YAOYOROZU_WORKER_DELTA_SCAN_PROFILE = "git-target-path-delta-v1"
YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE = "target-delta-to-patch-candidate-v1"
YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE = "target-delta-priority-ranking-v1"
YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE = "materialized-dependency-module-origin-v1"
YAOYOROZU_WORKER_MODULE_NAME = "omoikane.agentic.local_worker_stub"
YAOYOROZU_WORKER_MODULE_RELATIVE_PATH = "omoikane/agentic/local_worker_stub.py"
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


def _path_matches_target_paths(relative_path: str, target_paths: list[str]) -> bool:
    for target_path in target_paths:
        normalized_target = target_path.rstrip("/")
        if relative_path == normalized_target or relative_path.startswith(f"{normalized_target}/"):
            return True
    return False


def _matching_target_path_scope(relative_path: str, target_paths: list[str]) -> str:
    matches = [
        target_path
        for target_path in target_paths
        if _path_matches_target_paths(relative_path, [target_path])
    ]
    if not matches:
        return ""
    return max(matches, key=len)


def _excerpt(text: str, *, limit: int = 240) -> str:
    compact = " ".join(str(text).split())
    return compact[:limit]


def _run_argv_command(
    *,
    argv: list[str],
    cwd: Path,
    timeout_seconds: int = 5,
) -> dict[str, object]:
    command = " ".join(shlex.quote(item) for item in argv)
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": 124,
            "status": "timeout",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }
    return {
        "command": command,
        "exit_code": completed.returncode,
        "status": "pass" if completed.returncode == 0 else "fail",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def worker_module_origin_digest_payload(origin: Mapping[str, Any]) -> dict[str, object]:
    return {
        "profile": origin["profile"],
        "module_name": origin["module_name"],
        "module_file": origin["module_file"],
        "module_digest": origin["module_digest"],
        "search_path_head": origin["search_path_head"],
    }


def build_worker_module_origin() -> dict[str, object]:
    module_file = Path(__file__).resolve()
    module_text = module_file.read_text(encoding="utf-8", errors="replace")
    search_path_head = [
        str(Path(path_entry or os.getcwd()).resolve())
        for path_entry in sys.path[:6]
    ]
    origin = {
        "profile": YAOYOROZU_DEPENDENCY_MODULE_ORIGIN_PROFILE,
        "module_name": YAOYOROZU_WORKER_MODULE_NAME,
        "module_file": str(module_file),
        "module_digest": sha256_text(module_text),
        "search_path_head": search_path_head,
    }
    origin["origin_digest"] = sha256_text(
        canonical_json(worker_module_origin_digest_payload(origin))
    )
    return origin


def _compact_command_receipt(label: str, result: dict[str, object]) -> dict[str, object]:
    return {
        "command_label": label,
        "command": str(result.get("command", "")),
        "exit_code": int(result.get("exit_code", -1)),
        "status": str(result.get("status", "fail")),
        "stdout_excerpt": _excerpt(str(result.get("stdout", ""))),
        "stderr_excerpt": _excerpt(str(result.get("stderr", ""))),
    }


def _normalize_git_status(code: str) -> str:
    if code == "??":
        return "added"
    if "D" in code:
        return "removed"
    if any(flag in code for flag in ("M", "A", "R", "C")):
        return "modified"
    return "clean"


def _parse_git_status_output(stdout: str, *, target_paths: list[str]) -> dict[str, str]:
    status_map: dict[str, str] = {}
    for line in stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _path_matches_target_paths(path, target_paths):
            status_map[path] = _normalize_git_status(code)
    return status_map


def build_workspace_delta_receipt(
    *,
    workspace_root: Path,
    dispatch_plan_ref: str,
    dispatch_unit_ref: str,
    target_paths: list[str],
) -> dict[str, object]:
    workspace_root = workspace_root.resolve()
    normalized_target_paths = list(target_paths)
    command_receipts: list[dict[str, object]] = []
    blocking_reasons: list[str] = []

    head_result = _run_argv_command(
        argv=["git", "-C", str(workspace_root), "rev-parse", "HEAD"],
        cwd=workspace_root,
    )
    command_receipts.append(_compact_command_receipt("git-rev-parse-head", head_result))
    head_commit = str(head_result.get("stdout", "")).strip()
    if head_result["status"] != "pass" or len(head_commit) != 40:
        blocking_reasons.append("git HEAD commit could not be resolved for the worker delta scan")
        head_commit = "0" * 40

    status_result = _run_argv_command(
        argv=[
            "git",
            "-C",
            str(workspace_root),
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            *normalized_target_paths,
        ],
        cwd=workspace_root,
    )
    command_receipts.append(_compact_command_receipt("git-status-short", status_result))
    if status_result["status"] != "pass":
        blocking_reasons.append("git status --short failed for the worker delta scan")
    status_map = _parse_git_status_output(
        str(status_result.get("stdout", "")),
        target_paths=normalized_target_paths,
    )

    entries: list[dict[str, object]] = []
    for relative_path, working_tree_state in sorted(status_map.items()):
        resolved_path = (workspace_root / relative_path).resolve()
        current_present = resolved_path.is_file()
        current_text = (
            resolved_path.read_text(encoding="utf-8", errors="replace")
            if current_present
            else ""
        )
        current_digest = sha256_text(current_text) if current_present else ""
        current_bytes = len(current_text.encode("utf-8")) if current_present else 0

        baseline_present = False
        baseline_text = ""
        if head_commit != "0" * 40:
            show_result = _run_argv_command(
                argv=["git", "-C", str(workspace_root), "show", f"{head_commit}:{relative_path}"],
                cwd=workspace_root,
            )
            if show_result["status"] == "pass":
                baseline_present = True
                baseline_text = str(show_result.get("stdout", ""))
            else:
                stderr_text = str(show_result.get("stderr", ""))
                missing_from_head = "exists on disk, but not in" in stderr_text
                missing_from_head = missing_from_head or "does not exist in" in stderr_text
                missing_from_head = missing_from_head or (
                    "fatal: path '" in stderr_text and "HEAD" in stderr_text
                )
                if not missing_from_head:
                    blocking_reasons.append(f"git show failed for worker delta path: {relative_path}")

        baseline_digest = sha256_text(baseline_text) if baseline_present else ""
        baseline_bytes = len(baseline_text.encode("utf-8")) if baseline_present else 0
        path_kind = "file" if current_present else "missing"
        if working_tree_state == "removed" or (baseline_present and not current_present):
            change_status = "removed"
        elif working_tree_state == "added" or (not baseline_present and current_present):
            change_status = "added"
        else:
            change_status = "modified"

        entry = {
            "path": relative_path,
            "path_kind": path_kind,
            "working_tree_state": working_tree_state,
            "change_status": change_status,
            "within_workspace": _path_within_workspace(workspace_root, resolved_path),
            "within_target_paths": _path_matches_target_paths(relative_path, normalized_target_paths),
            "baseline_present": baseline_present,
            "current_present": current_present,
            "baseline_digest": baseline_digest,
            "current_digest": current_digest,
            "baseline_bytes": baseline_bytes,
            "current_bytes": current_bytes,
        }
        entry["entry_digest"] = sha256_text(canonical_json(entry))
        entries.append(entry)

    status = "blocked"
    if not blocking_reasons:
        status = "delta-detected" if entries else "clean"

    digest_payload = {
        "workspace_root": str(workspace_root),
        "dispatch_plan_ref": dispatch_plan_ref,
        "dispatch_unit_ref": dispatch_unit_ref,
        "target_paths": normalized_target_paths,
        "head_commit": head_commit,
        "status": status,
        "changed_path_count": len(entries),
        "entries": [
            {
                "path": entry["path"],
                "working_tree_state": entry["working_tree_state"],
                "change_status": entry["change_status"],
                "baseline_digest": entry["baseline_digest"],
                "current_digest": entry["current_digest"],
            }
            for entry in entries
        ],
    }
    receipt = {
        "kind": "yaoyorozu_worker_workspace_delta_receipt",
        "schema_version": "1.0.0",
        "receipt_id": new_id("yaoyorozu-worker-delta"),
        "receipt_ref": "",
        "profile_id": YAOYOROZU_WORKER_DELTA_SCAN_PROFILE,
        "workspace_root": str(workspace_root),
        "workspace_root_digest": sha256_text(str(workspace_root)),
        "dispatch_plan_ref": dispatch_plan_ref,
        "dispatch_unit_ref": dispatch_unit_ref,
        "target_paths": normalized_target_paths,
        "scanned_at": utc_now_iso(),
        "head_commit": head_commit,
        "status": status,
        "changed_path_count": len(entries),
        "entries": entries,
        "command_receipts": command_receipts,
    }
    receipt["receipt_ref"] = f"worker-delta://{receipt['receipt_id']}"
    receipt["receipt_digest"] = sha256_text(canonical_json(digest_payload))
    if status == "blocked":
        receipt["blocking_reasons"] = blocking_reasons
    return receipt


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


def _worker_target_subsystem(coverage_area: str) -> str:
    return {
        "runtime": "L4.Yaoyorozu.RuntimeWorker",
        "schema": "L4.Yaoyorozu.SchemaWorker",
        "eval": "L4.Yaoyorozu.EvalWorker",
        "docs": "L4.Yaoyorozu.DocSyncWorker",
    }.get(coverage_area, "L4.Yaoyorozu.Worker")


def _candidate_action(change_status: str) -> str:
    return {
        "added": "create",
        "modified": "modify",
        "removed": "delete",
    }.get(change_status, "modify")


def _candidate_cue_kind(relative_path: str) -> str:
    if relative_path.startswith("tests/"):
        return "test-coverage"
    if relative_path.startswith("evals/"):
        return "eval-sync"
    if relative_path.startswith("docs/"):
        return "docs-sync"
    if relative_path.startswith("meta/decision-log/"):
        return "meta-decision-log"
    return "runtime-source"


def _candidate_safety_impact(relative_path: str, coverage_area: str) -> str:
    if relative_path.startswith("docs/"):
        return "cosmetic"
    if relative_path.startswith("meta/decision-log/"):
        return "low"
    if relative_path.startswith("tests/") or relative_path.startswith("evals/"):
        return "low"
    if coverage_area == "schema":
        return "medium"
    return "medium"


def _candidate_summary(relative_path: str, coverage_area: str, action: str) -> str:
    verbs = {
        "create": "Create",
        "modify": "Modify",
        "delete": "Delete",
    }
    coverage_labels = {
        "runtime": "runtime",
        "schema": "schema",
        "eval": "eval",
        "docs": "docs",
    }
    return (
        f"{verbs.get(action, 'Modify')} the "
        f"{coverage_labels.get(coverage_area, 'worker')} target {relative_path} "
        "from dispatch-bound git delta evidence."
    )


def _candidate_rollback_hint(relative_path: str, action: str) -> str:
    if action == "create":
        return f"Delete {relative_path} to revert the worker-derived candidate."
    return f"Restore {relative_path} from the dispatch-bound HEAD baseline."


def _candidate_section_labels(relative_path: str) -> list[str]:
    parts = [segment for segment in relative_path.split("/") if segment]
    return parts[:3]


def _candidate_priority_score(relative_path: str, action: str, cue_kind: str) -> int:
    base_by_cue_kind = {
        "runtime-source": 78,
        "test-coverage": 64,
        "eval-sync": 56,
        "docs-sync": 48,
        "meta-decision-log": 40,
    }
    action_bonus = {
        "delete": 10,
        "modify": 6,
        "create": 4,
    }.get(action, 0)
    scope_bonus = 0
    if relative_path.startswith("src/omoikane/"):
        scope_bonus = 6
    elif relative_path.startswith("specs/interfaces/"):
        scope_bonus = 5
    elif relative_path.startswith("specs/schemas/"):
        scope_bonus = 4
    elif relative_path.startswith("tests/integration/"):
        scope_bonus = 3
    elif relative_path.startswith("tests/unit/"):
        scope_bonus = 2
    elif relative_path.startswith("evals/"):
        scope_bonus = 2
    elif relative_path.startswith("docs/"):
        scope_bonus = 1
    return min(100, base_by_cue_kind.get(cue_kind, 50) + action_bonus + scope_bonus)


def _candidate_priority_tier(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 76:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _candidate_priority_reason(
    relative_path: str,
    *,
    cue_kind: str,
    action: str,
    score: int,
    tier: str,
) -> str:
    cue_label = {
        "runtime-source": "runtime source",
        "test-coverage": "test coverage",
        "eval-sync": "eval sync",
        "docs-sync": "docs sync",
        "meta-decision-log": "decision log",
    }.get(cue_kind, "repo-local")
    return (
        f"{cue_label} candidate on {relative_path} uses {action} and scores "
        f"{score} ({tier}) under {YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE}."
    )


def build_patch_candidate_receipt(
    *,
    workspace_root: Path,
    dispatch_plan_ref: str,
    dispatch_unit_ref: str,
    source_ref: str,
    coverage_area: str,
    target_paths: list[str],
    workspace_delta_receipt: Mapping[str, Any],
    target_path_observations: list[Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    workspace_root = workspace_root.resolve()
    observations = (
        list(target_path_observations)
        if target_path_observations is not None
        else _observe_target_paths(workspace_root, target_paths)
    )
    observation_index = {
        str(observation.get("target_path", "")): observation
        for observation in observations
        if isinstance(observation, Mapping)
    }
    delta_entries = workspace_delta_receipt.get("entries", [])
    if not isinstance(delta_entries, list):
        delta_entries = []
    blocking_reasons: list[str] = []
    patch_candidates: list[dict[str, object]] = []

    for entry in delta_entries:
        if not isinstance(entry, Mapping):
            blocking_reasons.append("worker delta receipt entries must remain mappings")
            continue
        relative_path = str(entry.get("path", "")).strip()
        if not relative_path:
            blocking_reasons.append("worker delta entry path must be a non-empty string")
            continue
        target_scope = _matching_target_path_scope(relative_path, target_paths)
        if not target_scope:
            blocking_reasons.append(
                f"worker delta path could not be rebound to a target scope: {relative_path}"
            )
            continue
        observation = observation_index.get(target_scope)
        if observation is None:
            blocking_reasons.append(
                f"worker target-path observation missing for scope {target_scope}"
            )
            continue

        action = _candidate_action(str(entry.get("change_status", "")))
        cue_kind = _candidate_cue_kind(relative_path)
        priority_score = _candidate_priority_score(relative_path, action, cue_kind)
        patch_descriptor = {
            "patch_id": new_id("worker-patch"),
            "target_path": relative_path,
            "action": action,
            "format": "structured_patch",
            "summary": _candidate_summary(relative_path, coverage_area, action),
            "safety_impact": _candidate_safety_impact(relative_path, coverage_area),
            "rationale_refs": [
                dispatch_plan_ref,
                dispatch_unit_ref,
                str(workspace_delta_receipt.get("receipt_ref", "")),
            ],
            "cue_kind": cue_kind,
            "source_refs": [source_ref, target_scope],
            "section_labels": _candidate_section_labels(relative_path),
            "target_subsystem": _worker_target_subsystem(coverage_area),
            "rollback_hint": _candidate_rollback_hint(relative_path, action),
            "applies_cleanly": True,
        }
        candidate = {
            "candidate_id": new_id("worker-patch-candidate"),
            "target_path": relative_path,
            "target_path_scope": target_scope,
            "target_path_observation_digest": str(observation.get("observation_digest", "")),
            "delta_entry_digest": str(entry.get("entry_digest", "")),
            "change_status": str(entry.get("change_status", "")),
            "patch_descriptor": patch_descriptor,
            "priority_score": priority_score,
        }
        patch_candidates.append(candidate)

    patch_candidates.sort(
        key=lambda candidate: (
            -int(candidate.get("priority_score", 0)),
            str(candidate.get("target_path", "")),
        )
    )
    for priority_rank, candidate in enumerate(patch_candidates, start=1):
        priority_score = int(candidate.get("priority_score", 0))
        priority_tier = _candidate_priority_tier(priority_score)
        candidate["priority_rank"] = priority_rank
        candidate["priority_tier"] = priority_tier
        candidate["priority_reason"] = _candidate_priority_reason(
            str(candidate.get("target_path", "")),
            cue_kind=str(candidate.get("patch_descriptor", {}).get("cue_kind", "")),
            action=str(candidate.get("patch_descriptor", {}).get("action", "")),
            score=priority_score,
            tier=priority_tier,
        )
        candidate["candidate_digest"] = sha256_text(canonical_json(candidate))

    delta_status = str(workspace_delta_receipt.get("status", "blocked"))
    all_delta_entries_materialized = len(patch_candidates) == len(delta_entries) and not blocking_reasons
    if delta_status == "blocked" or blocking_reasons:
        status = "blocked"
    elif delta_entries:
        status = "candidate-ready"
    else:
        status = "no-candidates"

    ranked_candidate_ids = [str(candidate["candidate_id"]) for candidate in patch_candidates]
    highest_priority_score = int(patch_candidates[0]["priority_score"]) if patch_candidates else 0
    highest_priority_tier = (
        str(patch_candidates[0]["priority_tier"]) if patch_candidates else "none"
    )

    digest_payload = {
        "workspace_root": str(workspace_root),
        "dispatch_plan_ref": dispatch_plan_ref,
        "dispatch_unit_ref": dispatch_unit_ref,
        "source_ref": source_ref,
        "coverage_area": coverage_area,
        "target_paths": list(target_paths),
        "delta_receipt_ref": workspace_delta_receipt.get("receipt_ref", ""),
        "delta_receipt_digest": workspace_delta_receipt.get("receipt_digest", ""),
        "status": status,
        "priority_profile": YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
        "highest_priority_tier": highest_priority_tier,
        "highest_priority_score": highest_priority_score,
        "ranked_candidate_ids": ranked_candidate_ids,
        "patch_candidate_count": len(patch_candidates),
        "all_delta_entries_materialized": all_delta_entries_materialized,
        "candidate_digests": [candidate["candidate_digest"] for candidate in patch_candidates],
    }
    receipt = {
        "kind": "yaoyorozu_worker_patch_candidate_receipt",
        "schema_version": "1.0.0",
        "receipt_id": new_id("yaoyorozu-worker-patch-candidate"),
        "receipt_ref": "",
        "profile_id": YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE,
        "workspace_root": str(workspace_root),
        "workspace_root_digest": sha256_text(str(workspace_root)),
        "dispatch_plan_ref": dispatch_plan_ref,
        "dispatch_unit_ref": dispatch_unit_ref,
        "source_ref": source_ref,
        "coverage_area": coverage_area,
        "target_paths": list(target_paths),
        "delta_receipt_ref": str(workspace_delta_receipt.get("receipt_ref", "")),
        "delta_receipt_digest": str(workspace_delta_receipt.get("receipt_digest", "")),
        "planned_at": utc_now_iso(),
        "status": status,
        "priority_profile": YAOYOROZU_WORKER_PATCH_PRIORITY_PROFILE,
        "highest_priority_tier": highest_priority_tier,
        "highest_priority_score": highest_priority_score,
        "ranked_candidate_ids": ranked_candidate_ids,
        "patch_candidate_count": len(patch_candidates),
        "all_delta_entries_materialized": all_delta_entries_materialized,
        "patch_candidates": patch_candidates,
    }
    receipt["receipt_ref"] = f"worker-patch://{receipt['receipt_id']}"
    receipt["receipt_digest"] = sha256_text(canonical_json(digest_payload))
    if status == "blocked":
        receipt["blocking_reasons"] = blocking_reasons or [
            "worker patch candidate materialization is blocked by the delta receipt state"
        ]
    return receipt


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
    workspace_delta_receipt = build_workspace_delta_receipt(
        workspace_root=workspace_root,
        dispatch_plan_ref=args.dispatch_plan_ref,
        dispatch_unit_ref=args.dispatch_unit_ref,
        target_paths=target_paths,
    )
    patch_candidate_receipt = build_patch_candidate_receipt(
        workspace_root=workspace_root,
        dispatch_plan_ref=args.dispatch_plan_ref,
        dispatch_unit_ref=args.dispatch_unit_ref,
        source_ref=args.source_ref,
        coverage_area=args.coverage_area,
        target_paths=target_paths,
        workspace_delta_receipt=workspace_delta_receipt,
        target_path_observations=target_path_observations,
    )
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
        "delta_receipt_ref": workspace_delta_receipt["receipt_ref"],
        "delta_status": workspace_delta_receipt["status"],
        "changed_path_count": workspace_delta_receipt["changed_path_count"],
        "delta_scan_profile": YAOYOROZU_WORKER_DELTA_SCAN_PROFILE,
        "patch_candidate_receipt_ref": patch_candidate_receipt["receipt_ref"],
        "patch_candidate_status": patch_candidate_receipt["status"],
        "patch_candidate_count": patch_candidate_receipt["patch_candidate_count"],
        "patch_candidate_profile": YAOYOROZU_WORKER_PATCH_CANDIDATE_PROFILE,
        "patch_priority_profile": patch_candidate_receipt["priority_profile"],
        "highest_patch_priority_tier": patch_candidate_receipt["highest_priority_tier"],
        "highest_patch_priority_score": patch_candidate_receipt["highest_priority_score"],
        "all_delta_entries_materialized": patch_candidate_receipt["all_delta_entries_materialized"],
        "ready_gate": YAOYOROZU_WORKER_READY_GATE_PROFILE,
    }
    status = (
        "ready"
        if coverage_evidence["all_targets_exist"]
        and coverage_evidence["all_targets_within_workspace"]
        and workspace_delta_receipt["status"] in {"clean", "delta-detected"}
        and patch_candidate_receipt["status"] in {"no-candidates", "candidate-ready"}
        and patch_candidate_receipt["all_delta_entries_materialized"] is True
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
        "workspace_delta_receipt": workspace_delta_receipt,
        "patch_candidate_receipt": patch_candidate_receipt,
        "worker_module_origin": build_worker_module_origin(),
        "coverage_evidence": coverage_evidence,
        "status": status,
    }
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
