"""Builder pipeline primitives for bounded self-construction."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


IMMUTABLE_BOUNDARIES = ("L1.EthicsEnforcer", "L1.ContinuityLedger")
MANDATORY_BUILD_PIPELINE_EVAL = "evals/continuity/council_output_build_request_pipeline.yaml"
MANDATORY_STAGED_ROLLOUT_EVAL = "evals/continuity/builder_staged_rollout_execution.yaml"
MANDATORY_ROLLBACK_EVAL = "evals/continuity/builder_rollback_execution.yaml"
MANDATORY_LIVE_ENACTMENT_EVAL = "evals/continuity/builder_live_enactment_execution.yaml"
ROLLOUT_STAGE_ORDER = (
    ("dark-launch", 0, "shadow-only", "shadow-match"),
    ("canary-5pct", 5, "limited-visible", "guardian-pass"),
    ("broad-50pct", 50, "shared-visible", "continuity-stable"),
    ("full-100pct", 100, "primary-visible", "promotion-complete"),
)


def _is_within_scope(candidate: str, scope_roots: Sequence[str]) -> bool:
    normalized_candidate = candidate.rstrip("/")
    for scope in scope_roots:
        normalized_scope = scope.rstrip("/")
        if normalized_candidate == normalized_scope or normalized_candidate.startswith(
            f"{normalized_scope}/"
        ):
            return True
    return False


def _first_matching_prefix(paths: Sequence[str], prefix: str, fallback: str) -> str:
    for path in paths:
        if path.startswith(prefix):
            return path
    return fallback


def _tail_text(text: str, *, limit: int = 160) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[-limit:]


def _run_shell_command(
    *,
    command: str,
    cwd: Path,
    timeout_seconds: int,
) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "status": "pass" if completed.returncode == 0 else "fail",
            "stdout_excerpt": _tail_text(completed.stdout),
            "stderr_excerpt": _tail_text(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": -1,
            "status": "timeout",
            "stdout_excerpt": _tail_text(exc.stdout or ""),
            "stderr_excerpt": _tail_text(exc.stderr or ""),
        }


def _run_argv_command(
    *,
    argv: Sequence[str],
    cwd: Path,
    timeout_seconds: int,
) -> Dict[str, Any]:
    command = shlex.join(argv)
    try:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "status": "pass" if completed.returncode == 0 else "fail",
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "stdout_excerpt": _tail_text(completed.stdout),
            "stderr_excerpt": _tail_text(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": -1,
            "status": "timeout",
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "stdout_excerpt": _tail_text(exc.stdout or ""),
            "stderr_excerpt": _tail_text(exc.stderr or ""),
        }


@dataclass(frozen=True)
class PatchGeneratorPolicy:
    """Deterministic policy for build-request scope validation and patch planning."""

    policy_id: str = "spec-driven-patch-descriptor-v0"
    immutable_boundaries: tuple[str, str] = IMMUTABLE_BOUNDARIES
    patch_format: str = "structured_patch"
    prohibited_targets: tuple[str, ...] = ("src/omoikane/kernel/",)
    requires_build_log: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "immutable_boundaries": list(self.immutable_boundaries),
            "patch_format": self.patch_format,
            "prohibited_targets": list(self.prohibited_targets),
            "requires_build_log": self.requires_build_log,
        }


class PatchGeneratorService:
    """Materialize bounded patch descriptors from approved build requests."""

    def __init__(self, policy: PatchGeneratorPolicy | None = None) -> None:
        self._policy = policy or PatchGeneratorPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def validate_scope(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        constraints = dict(request.get("constraints", {}))
        forbidden = list(constraints.get("forbidden", []))
        workspace_scope = list(request.get("workspace_scope", []))
        allowed_write_paths = list(constraints.get("allowed_write_paths", []))
        must_sync_docs = list(request.get("must_sync_docs", []))

        blocking_rules: list[str] = []
        design_delta_ref = str(request.get("design_delta_ref", ""))
        if not design_delta_ref.startswith("design://"):
            blocking_rules.append("design_delta_ref must start with design://")
        design_delta_digest = str(request.get("design_delta_digest", ""))
        if len(design_delta_digest) != 64:
            blocking_rules.append("design_delta_digest must be a sha256 hex digest")
        for boundary in self._policy.immutable_boundaries:
            if boundary not in forbidden:
                blocking_rules.append(f"immutable boundary missing from forbidden list: {boundary}")
        for path in allowed_write_paths:
            if not _is_within_scope(path, workspace_scope):
                blocking_rules.append(f"allowed write path escapes workspace scope: {path}")
        if not must_sync_docs:
            blocking_rules.append("must_sync_docs must not be empty")
        for path in must_sync_docs:
            if not path.startswith("docs/"):
                blocking_rules.append(f"must_sync_docs must stay under docs/: {path}")
            elif not _is_within_scope(path, workspace_scope):
                blocking_rules.append(f"must_sync_docs escapes workspace scope: {path}")
        if not allowed_write_paths:
            blocking_rules.append("allowed_write_paths must not be empty")
        if not workspace_scope:
            blocking_rules.append("workspace_scope must not be empty")

        return {
            "allowed": not blocking_rules,
            "blocking_rules": blocking_rules,
        }

    def generate_patch_set(self, request: Mapping[str, Any]) -> Dict[str, Any]:
        validation = self.validate_scope(request)
        artifact_id = new_id("artifact")
        build_artifact: Dict[str, Any] = {
            "kind": "build_artifact",
            "schema_version": "1.0.0",
            "artifact_id": artifact_id,
            "request_id": request["request_id"],
            "status": "blocked" if not validation["allowed"] else "ready",
            "summary": "",
            "generated_at": utc_now_iso(),
            "artifacts": [],
        }

        if not validation["allowed"]:
            build_artifact["summary"] = "Immutable boundary or workspace-scope validation failed."
            build_artifact["artifacts"] = [
                {
                    "artifact_kind": "build_log",
                    "ref": f"log://{artifact_id}",
                    "summary": "Build request was blocked before patch emission.",
                }
            ]
            build_artifact["blocking_rules"] = list(validation["blocking_rules"])
            build_artifact["test_results"] = {
                "build_status": "not-run",
                "eval_status": "not-run",
                "executed_evals": [],
            }
            return build_artifact

        output_paths = list(request.get("output_paths", []))
        source_dir = _first_matching_prefix(output_paths, "src/", "src/omoikane/self_construction/")
        test_dir = _first_matching_prefix(output_paths, "tests/", "tests/unit/")
        source_target = str(PurePosixPath(source_dir) / "builders.py")
        test_target = str(PurePosixPath(test_dir) / "test_builders.py")
        requested_evals = list(request.get("constraints", {}).get("must_pass", []))

        patches = [
            {
                "patch_id": new_id("patch"),
                "target_path": source_target,
                "action": "modify",
                "format": self._policy.patch_format,
                "summary": "Add deterministic patch generation and differential evaluation helpers.",
                "safety_impact": "medium",
                "rationale_refs": list(request.get("spec_refs", [])),
                "forbidden_patterns": list(self._policy.immutable_boundaries),
                "rollback_hint": "Restore previous L5 builder pipeline module snapshot.",
                "applies_cleanly": True,
            },
            {
                "patch_id": new_id("patch"),
                "target_path": test_target,
                "action": "create",
                "format": self._policy.patch_format,
                "summary": "Add bounded builder pipeline coverage for scope validation and rollout classification.",
                "safety_impact": "low",
                "rationale_refs": requested_evals or list(request.get("design_refs", [])),
                "forbidden_patterns": list(self._policy.immutable_boundaries),
                "rollback_hint": "Remove builder pipeline coverage and revert to previous tests.",
                "applies_cleanly": True,
            },
        ]
        build_artifact["summary"] = (
            "Patch descriptors, doc-sync handoff, and regression plan emitted for sandbox-only "
            "builder execution."
        )
        build_artifact["artifacts"] = [
            {
                "artifact_kind": "design_delta_manifest",
                "ref": request["design_delta_ref"],
                "summary": "DesignReader handoff was bound before patch emission.",
            },
            {
                "artifact_kind": "patch_descriptor",
                "ref": f"patch://{patches[0]['patch_id']}",
                "summary": patches[0]["summary"],
            },
            {
                "artifact_kind": "patch_descriptor",
                "ref": f"patch://{patches[1]['patch_id']}",
                "summary": patches[1]["summary"],
            },
            {
                "artifact_kind": "build_log",
                "ref": f"log://{artifact_id}",
                "summary": "Scope validation passed and patch descriptors were emitted.",
            },
            {
                "artifact_kind": "test_report",
                "ref": f"report://{artifact_id}/build",
                "summary": "Builder pipeline requires council-output continuity eval before promotion.",
            },
            {
                "artifact_kind": "rollback_plan",
                "ref": f"rollback://{request['request_id']}",
                "summary": "Rollback restores the prior sandbox snapshot and invalidates emitted patch refs.",
            },
        ]
        build_artifact["patches"] = patches
        build_artifact["test_results"] = {
            "build_status": "pass",
            "eval_status": "not-run",
            "executed_evals": [],
        }
        build_artifact["continuity_log_ref"] = f"ledger://self-modify/{request['request_id']}"
        return build_artifact

    @staticmethod
    def describe_patch(descriptor: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(descriptor)


@dataclass(frozen=True)
class DifferentialEvaluationPolicy:
    """Deterministic A/B evaluation policy for the builder pipeline."""

    policy_id: str = "council-build-request-ab-v0"
    mandatory_eval: str = MANDATORY_BUILD_PIPELINE_EVAL
    rollback_on_regression: bool = True
    hold_on_fail: bool = True
    target_eval_map: Dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "L5.PatchGenerator": (MANDATORY_BUILD_PIPELINE_EVAL,),
            "L5.DifferentialEvaluator": (MANDATORY_BUILD_PIPELINE_EVAL,),
            "L5.RollbackEngine": (
                MANDATORY_BUILD_PIPELINE_EVAL,
                MANDATORY_LIVE_ENACTMENT_EVAL,
                MANDATORY_STAGED_ROLLOUT_EVAL,
                MANDATORY_ROLLBACK_EVAL,
            ),
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "mandatory_eval": self.mandatory_eval,
            "rollback_on_regression": self.rollback_on_regression,
            "hold_on_fail": self.hold_on_fail,
            "target_eval_map": {key: list(value) for key, value in self.target_eval_map.items()},
        }


class DifferentialEvaluatorService:
    """Select eval suites and classify rollout decisions for sandboxed builds."""

    def __init__(self, policy: DifferentialEvaluationPolicy | None = None) -> None:
        self._policy = policy or DifferentialEvaluationPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def select_suite(
        self,
        *,
        target_subsystem: str,
        requested_evals: Sequence[str],
    ) -> Dict[str, Any]:
        selected: list[str] = []
        for eval_ref in requested_evals:
            if eval_ref.startswith("evals/") and eval_ref not in selected:
                selected.append(eval_ref)
        for subsystem_prefix, mandatory in self._policy.target_eval_map.items():
            if target_subsystem.startswith(subsystem_prefix):
                for eval_ref in mandatory:
                    if eval_ref not in selected:
                        selected.append(eval_ref)
        return {"selected_evals": selected}

    @staticmethod
    def run_ab_eval(
        *,
        eval_ref: str,
        baseline_ref: str,
        sandbox_ref: str,
    ) -> Dict[str, Any]:
        sandbox_lower = sandbox_ref.lower()
        baseline_lower = baseline_ref.lower()
        if "regression" in sandbox_lower or "rollback-breach" in sandbox_lower:
            outcome = "regression"
        elif "fail" in sandbox_lower or "mismatch" in sandbox_lower or "fail" in baseline_lower:
            outcome = "fail"
        else:
            outcome = "pass"
        return {
            "eval_ref": eval_ref,
            "outcome": outcome,
            "report_ref": f"report://{eval_ref.replace('/', ':')}",
        }

    @staticmethod
    def classify_rollout(*, outcomes: Sequence[str]) -> Dict[str, Any]:
        if "regression" in outcomes:
            decision = "rollback"
        elif "fail" in outcomes:
            decision = "hold"
        else:
            decision = "promote"
        return {"decision": decision}


@dataclass(frozen=True)
class SandboxApplyPolicy:
    """Deterministic policy for applying builder artifacts to Mirage Self."""

    policy_id: str = "mirage-self-apply-v0"
    sandbox_profile: str = "forked-self"
    require_clean_apply: bool = True
    require_rollback_plan: bool = True
    max_patch_count: int = 4
    external_effects_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "sandbox_profile": self.sandbox_profile,
            "require_clean_apply": self.require_clean_apply,
            "require_rollback_plan": self.require_rollback_plan,
            "max_patch_count": self.max_patch_count,
            "external_effects_allowed": self.external_effects_allowed,
        }


class SandboxApplyService:
    """Apply bounded patch descriptors to Mirage Self and emit a receipt."""

    def __init__(self, policy: SandboxApplyPolicy | None = None) -> None:
        self._policy = policy or SandboxApplyPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def apply_artifact(
        self,
        *,
        build_request: Mapping[str, Any],
        build_artifact: Mapping[str, Any],
    ) -> Dict[str, Any]:
        patches = list(build_artifact.get("patches", []))
        rollback_plan_ref = self._artifact_ref(build_artifact, "rollback_plan")
        build_log_ref = self._artifact_ref(build_artifact, "build_log")
        validation = {
            "clean_apply": bool(build_artifact.get("status") == "ready" and patches),
            "rollback_ready": bool(rollback_plan_ref),
            "immutable_boundaries_preserved": set(
                build_request.get("constraints", {}).get("forbidden", [])
            )
            == set(IMMUTABLE_BOUNDARIES),
            "external_effects_blocked": not self._policy.external_effects_allowed,
        }
        allowed = (
            validation["clean_apply"]
            and validation["rollback_ready"]
            and validation["immutable_boundaries_preserved"]
            and validation["external_effects_blocked"]
            and len(patches) <= self._policy.max_patch_count
        )

        receipt = {
            "kind": "sandbox_apply_receipt",
            "schema_version": "1.0",
            "receipt_id": new_id("sandbox-apply"),
            "request_id": build_request["request_id"],
            "artifact_id": build_artifact["artifact_id"],
            "policy": self.policy(),
            "status": "applied" if allowed else "blocked",
            "sandbox_snapshot_ref": (
                f"mirage://{build_request['request_id']}/snapshot/current" if allowed else ""
            ),
            "applied_patch_ids": [patch["patch_id"] for patch in patches] if allowed else [],
            "applied_patch_count": len(patches) if allowed else 0,
            "rollback_plan_ref": rollback_plan_ref,
            "build_log_ref": build_log_ref,
            "continuity_log_ref": build_artifact.get("continuity_log_ref", ""),
            "external_effects": [],
            "validation": validation,
            "preserved_invariants": [
                "no-external-effects",
                "rollback-ready",
                "immutable-boundaries-preserved",
            ],
            "applied_at": utc_now_iso(),
        }
        if not allowed:
            receipt["blocking_rules"] = [
                rule
                for rule, ok in (
                    ("build artifact must be ready with patch descriptors", validation["clean_apply"]),
                    ("rollback plan must be present before sandbox apply", validation["rollback_ready"]),
                    (
                        "immutable boundaries must remain in the forbidden set",
                        validation["immutable_boundaries_preserved"],
                    ),
                    ("external effects must stay blocked", validation["external_effects_blocked"]),
                    (
                        f"patch count must be <= {self._policy.max_patch_count}",
                        len(patches) <= self._policy.max_patch_count,
                    ),
                )
                if not ok
            ]
        return receipt

    @staticmethod
    def _artifact_ref(build_artifact: Mapping[str, Any], artifact_kind: str) -> str:
        for artifact in build_artifact.get("artifacts", []):
            if artifact.get("artifact_kind") == artifact_kind:
                return str(artifact.get("ref", ""))
        return ""

    @staticmethod
    def validate_receipt(receipt: Mapping[str, Any]) -> Dict[str, Any]:
        errors: list[str] = []
        if receipt.get("kind") != "sandbox_apply_receipt":
            errors.append("kind must equal sandbox_apply_receipt")
        if receipt.get("schema_version") != "1.0":
            errors.append("schema_version must equal 1.0")
        if receipt.get("status") not in {"applied", "blocked"}:
            errors.append("status must be applied or blocked")
        if receipt.get("status") == "applied":
            if not receipt.get("sandbox_snapshot_ref", "").startswith("mirage://"):
                errors.append("sandbox_snapshot_ref must start with mirage://")
            if int(receipt.get("applied_patch_count", 0)) < 1:
                errors.append("applied_patch_count must be >= 1 for applied receipts")
            if list(receipt.get("external_effects", [])):
                errors.append("external_effects must stay empty")
        validation = dict(receipt.get("validation", {}))
        for field in (
            "clean_apply",
            "rollback_ready",
            "immutable_boundaries_preserved",
            "external_effects_blocked",
        ):
            if field not in validation:
                errors.append(f"validation.{field} is required")
        return {"ok": not errors, "errors": errors}


@dataclass(frozen=True)
class RolloutPlannerPolicy:
    """Deterministic staged rollout policy for builder outputs."""

    policy_id: str = "bounded-builder-staged-rollout-v1"
    required_eval: str = MANDATORY_STAGED_ROLLOUT_EVAL
    guardian_gate_required: bool = True
    rollback_ready_required: bool = True
    stage_order: tuple[tuple[str, int, str, str], ...] = ROLLOUT_STAGE_ORDER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "required_eval": self.required_eval,
            "guardian_gate_required": self.guardian_gate_required,
            "rollback_ready_required": self.rollback_ready_required,
            "stage_order": [
                {
                    "stage_id": stage_id,
                    "traffic_percent": traffic_percent,
                    "delivery_mode": delivery_mode,
                    "promotion_signal": promotion_signal,
                }
                for stage_id, traffic_percent, delivery_mode, promotion_signal in self.stage_order
            ],
        }


class RolloutPlannerService:
    """Execute a bounded staged rollout after sandbox apply and A/B evals succeed."""

    def __init__(self, policy: RolloutPlannerPolicy | None = None) -> None:
        self._policy = policy or RolloutPlannerPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def execute_rollout(
        self,
        *,
        build_request: Mapping[str, Any],
        apply_receipt: Mapping[str, Any],
        eval_reports: Sequence[Mapping[str, Any]],
        decision: str,
        guardian_gate_status: str,
    ) -> Dict[str, Any]:
        rollback_ref = str(apply_receipt.get("rollback_plan_ref", ""))
        stages: list[Dict[str, Any]] = []
        for index, (stage_id, traffic_percent, delivery_mode, promotion_signal) in enumerate(
            self._policy.stage_order
        ):
            if decision == "promote":
                status = "completed"
            elif decision == "hold":
                status = "completed" if index == 0 else "blocked"
            else:
                status = "completed" if index == 0 else "rolled-back" if index == 1 else "blocked"
            stages.append(
                {
                    "stage_id": stage_id,
                    "traffic_percent": traffic_percent,
                    "delivery_mode": delivery_mode,
                    "status": status,
                    "guardian_gate": "observe" if traffic_percent == 0 else guardian_gate_status,
                    "rollback_ref": rollback_ref,
                    "promotion_signal": promotion_signal,
                }
            )

        completed_stage_count = sum(1 for stage in stages if stage["status"] == "completed")
        final_status = {
            "promote": "promoted",
            "hold": "held",
            "rollback": "rolled-back",
        }[decision]
        return {
            "kind": "staged_rollout_session",
            "schema_version": "1.0",
            "session_id": new_id("rollout-session"),
            "request_id": build_request["request_id"],
            "artifact_id": apply_receipt["artifact_id"],
            "apply_receipt_id": apply_receipt["receipt_id"],
            "policy": self.policy(),
            "decision": decision,
            "guardian_gate_status": guardian_gate_status,
            "status": final_status,
            "required_evals": [report["eval_ref"] for report in eval_reports],
            "completed_stage_count": completed_stage_count,
            "rollback_ready": bool(apply_receipt.get("validation", {}).get("rollback_ready")),
            "final_continuity_ref": str(apply_receipt.get("continuity_log_ref", "")),
            "stages": stages,
            "preserved_invariants": [
                "guardian-gated",
                "rollback-ready",
                "stage-ordered",
            ],
            "executed_at": utc_now_iso(),
        }

    def validate_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: list[str] = []
        if session.get("kind") != "staged_rollout_session":
            errors.append("kind must equal staged_rollout_session")
        if session.get("schema_version") != "1.0":
            errors.append("schema_version must equal 1.0")
        if session.get("decision") not in {"promote", "hold", "rollback"}:
            errors.append("decision must be promote, hold, or rollback")
        if session.get("status") not in {"promoted", "held", "rolled-back"}:
            errors.append("status must be promoted, held, or rolled-back")
        stages = list(session.get("stages", []))
        expected_order = [stage_id for stage_id, *_ in self._policy.stage_order]
        actual_order = [stage.get("stage_id") for stage in stages]
        if actual_order != expected_order:
            errors.append("stages must follow the fixed stage order")
        if not bool(session.get("rollback_ready")):
            errors.append("rollback_ready must be true")
        if session.get("decision") == "promote":
            if any(stage.get("status") != "completed" for stage in stages):
                errors.append("promote sessions must complete every stage")
            if int(session.get("completed_stage_count", 0)) != len(expected_order):
                errors.append("promote sessions must complete all stages")
        elif session.get("decision") == "hold":
            expected_statuses = ["completed", "blocked", "blocked", "blocked"]
            actual_statuses = [stage.get("status") for stage in stages]
            if actual_statuses != expected_statuses:
                errors.append("hold sessions must stop after dark-launch")
            if int(session.get("completed_stage_count", 0)) != 1:
                errors.append("hold sessions must complete only dark-launch")
        elif session.get("decision") == "rollback":
            expected_statuses = ["completed", "rolled-back", "blocked", "blocked"]
            actual_statuses = [stage.get("status") for stage in stages]
            if actual_statuses != expected_statuses:
                errors.append("rollback sessions must roll back during canary")
            if int(session.get("completed_stage_count", 0)) != 1:
                errors.append("rollback sessions must complete only dark-launch")
        return {"ok": not errors, "errors": errors}


@dataclass(frozen=True)
class RollbackEnginePolicy:
    """Deterministic rollback policy for builder sessions."""

    policy_id: str = "continuity-bound-builder-rollback-v5"
    required_eval: str = MANDATORY_ROLLBACK_EVAL
    require_append_only_continuity: bool = True
    require_pre_apply_snapshot: bool = True
    require_notifications: bool = True
    require_live_rollback_gate: bool = True
    require_reverse_apply_commands: bool = True
    require_repo_bound_verification: bool = True
    require_checkout_mutation_receipt: bool = True
    require_external_observer_receipts: bool = True
    rollback_workspace_prefix: str = "omoikane-builder-rollback-"
    checkout_mutation_strategy: str = "detached-git-worktree-overlay-v1"
    checkout_worktree_prefix: str = "omoikane-builder-rollback-worktree-"
    external_observer_profile: str = "repo-root-git-observer-v1"
    repo_binding_scope: str = "current-checkout-subtree"
    command_timeout_seconds: int = 15
    cleanup_after_run: bool = True
    max_reverted_patch_count: int = 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "required_eval": self.required_eval,
            "require_append_only_continuity": self.require_append_only_continuity,
            "require_pre_apply_snapshot": self.require_pre_apply_snapshot,
            "require_notifications": self.require_notifications,
            "require_live_rollback_gate": self.require_live_rollback_gate,
            "require_reverse_apply_commands": self.require_reverse_apply_commands,
            "require_repo_bound_verification": self.require_repo_bound_verification,
            "require_checkout_mutation_receipt": self.require_checkout_mutation_receipt,
            "require_external_observer_receipts": self.require_external_observer_receipts,
            "rollback_workspace_prefix": self.rollback_workspace_prefix,
            "checkout_mutation_strategy": self.checkout_mutation_strategy,
            "checkout_worktree_prefix": self.checkout_worktree_prefix,
            "external_observer_profile": self.external_observer_profile,
            "repo_binding_scope": self.repo_binding_scope,
            "command_timeout_seconds": self.command_timeout_seconds,
            "cleanup_after_run": self.cleanup_after_run,
            "max_reverted_patch_count": self.max_reverted_patch_count,
        }


class RollbackEngineService:
    """Restore the pre-apply Mirage Self snapshot after a failed builder rollout."""

    def __init__(self, policy: RollbackEnginePolicy | None = None) -> None:
        self._policy = policy or RollbackEnginePolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def execute_rollback(
        self,
        *,
        build_request: Mapping[str, Any],
        apply_receipt: Mapping[str, Any],
        rollout_session: Mapping[str, Any],
        live_enactment_session: Mapping[str, Any],
        repo_root: Path | str,
        trigger: str,
        reason: str,
        initiator: str,
    ) -> Dict[str, Any]:
        reverted_patch_ids = list(apply_receipt.get("applied_patch_ids", []))
        rollback_ready = bool(apply_receipt.get("validation", {}).get("rollback_ready"))
        continuity_ref = str(apply_receipt.get("continuity_log_ref", ""))
        live_enactment_ok = live_enactment_session.get("status") == "passed"
        reverse_apply_journal, reverse_cleanup_status = self._build_reverse_apply_journal(
            build_request=build_request,
            live_enactment_session=live_enactment_session,
            repo_root=repo_root,
        )
        repo_binding_summary = self._build_repo_binding_summary(
            build_request=build_request,
            reverse_apply_journal=reverse_apply_journal,
        )
        checkout_mutation_receipt = self._build_checkout_mutation_receipt(
            build_request=build_request,
            live_enactment_session=live_enactment_session,
            repo_root=repo_root,
        )
        continuity_event_refs = [
            ref
            for ref in (
                str(rollout_session.get("final_continuity_ref", "")),
                f"{continuity_ref}/rollback" if continuity_ref else "",
            )
            if ref
        ]
        reverted_stage_ids = [
            stage.get("stage_id")
            for stage in rollout_session.get("stages", [])
            if stage.get("status") in {"completed", "rolled-back"}
        ]
        notifications = [
            f"notify://self/{build_request['request_id']}",
            f"notify://council/{build_request['request_id']}",
            f"notify://guardian/{build_request['request_id']}",
        ]
        telemetry_gate = self._build_telemetry_gate(
            live_enactment_session=live_enactment_session,
            reverse_apply_journal=reverse_apply_journal,
            reverted_stage_ids=reverted_stage_ids,
            reverse_cleanup_status=reverse_cleanup_status,
            checkout_mutation_receipt=checkout_mutation_receipt,
        )
        allowed = (
            apply_receipt.get("status") == "applied"
            and rollback_ready
            and rollout_session.get("decision") == "rollback"
            and bool(continuity_event_refs)
            and len(reverted_patch_ids) <= self._policy.max_reverted_patch_count
            and live_enactment_ok
            and bool(reverse_apply_journal)
            and repo_binding_summary["verified_path_count"] == len(reverse_apply_journal)
            and checkout_mutation_receipt["status"] == "verified"
            and telemetry_gate["status"] == "rollback-approved"
        )

        return {
            "kind": "builder_rollback_session",
            "schema_version": "1.4",
            "rollback_session_id": new_id("rollback-session"),
            "request_id": build_request["request_id"],
            "artifact_id": apply_receipt["artifact_id"],
            "apply_receipt_id": apply_receipt["receipt_id"],
            "rollout_session_id": rollout_session["session_id"],
            "policy": self.policy(),
            "trigger": trigger,
            "initiator": initiator,
            "reason": reason,
            "status": "rolled-back" if allowed else "blocked",
            "live_enactment_session_id": (
                str(live_enactment_session.get("enactment_session_id", "")) if allowed else ""
            ),
            "restored_snapshot_ref": (
                f"mirage://{build_request['request_id']}/snapshot/pre-apply" if allowed else ""
            ),
            "rollback_plan_ref": str(apply_receipt.get("rollback_plan_ref", "")),
            "reverted_patch_ids": reverted_patch_ids if allowed else [],
            "reverted_patch_count": len(reverted_patch_ids) if allowed else 0,
            "reverted_stage_ids": reverted_stage_ids if allowed else [],
            "reverted_stage_count": len(reverted_stage_ids) if allowed else 0,
            "reverse_apply_journal": reverse_apply_journal if allowed else [],
            "repo_binding_summary": repo_binding_summary,
            "checkout_mutation_receipt": checkout_mutation_receipt,
            "telemetry_gate": (
                telemetry_gate if allowed else self._build_blocked_telemetry_gate(telemetry_gate)
            ),
            "continuity_event_refs": continuity_event_refs if allowed else continuity_event_refs[:1],
            "notification_refs": notifications if allowed else notifications[:1],
            "preserved_invariants": [
                "append-only-continuity",
                "restored-pre-apply-snapshot",
                "stakeholders-notified",
                "reverse-apply-journal-bound",
                "repo-baseline-bound",
                "checkout-bound-state-restored",
                "external-observer-evidence-bound",
            ],
            "executed_at": utc_now_iso(),
        }

    def validate_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: list[str] = []
        if session.get("kind") != "builder_rollback_session":
            errors.append("kind must equal builder_rollback_session")
        if session.get("schema_version") != "1.4":
            errors.append("schema_version must equal 1.4")
        if session.get("status") not in {"rolled-back", "blocked"}:
            errors.append("status must be rolled-back or blocked")
        if session.get("trigger") not in {"eval-regression", "guardian-veto", "manual-review"}:
            errors.append("trigger must be eval-regression, guardian-veto, or manual-review")
        repo_binding_summary = dict(session.get("repo_binding_summary", {}))
        if repo_binding_summary.get("binding_scope") != self._policy.repo_binding_scope:
            errors.append(
                f"repo_binding_summary.binding_scope must equal {self._policy.repo_binding_scope}"
            )
        if not str(repo_binding_summary.get("binding_root_ref", "")).startswith("repo://current-checkout/"):
            errors.append("repo_binding_summary.binding_root_ref must start with repo://current-checkout/")
        if len(str(repo_binding_summary.get("binding_digest", ""))) != 64:
            errors.append("repo_binding_summary.binding_digest must be a sha256 hex string")
        bound_paths = list(repo_binding_summary.get("bound_paths", []))
        if int(repo_binding_summary.get("bound_path_count", 0)) != len(bound_paths):
            errors.append("repo_binding_summary.bound_path_count must match bound_paths")
        checkout_mutation_receipt = dict(session.get("checkout_mutation_receipt", {}))
        if checkout_mutation_receipt.get("strategy") != self._policy.checkout_mutation_strategy:
            errors.append(
                "checkout_mutation_receipt.strategy must equal "
                f"{self._policy.checkout_mutation_strategy}"
            )
        if checkout_mutation_receipt.get("observed_path_count") != len(
            list(checkout_mutation_receipt.get("observed_paths", []))
        ):
            errors.append(
                "checkout_mutation_receipt.observed_path_count must match observed_paths"
            )
        if len(str(checkout_mutation_receipt.get("head_commit", ""))) != 40:
            errors.append("checkout_mutation_receipt.head_commit must be a git commit sha")
        if len(str(checkout_mutation_receipt.get("baseline_status_digest", ""))) != 64:
            errors.append("checkout_mutation_receipt.baseline_status_digest must be sha256")
        if len(str(checkout_mutation_receipt.get("restored_status_digest", ""))) != 64:
            errors.append("checkout_mutation_receipt.restored_status_digest must be sha256")
        if checkout_mutation_receipt.get("observer_profile") != self._policy.external_observer_profile:
            errors.append(
                "checkout_mutation_receipt.observer_profile must equal "
                f"{self._policy.external_observer_profile}"
            )
        observer_receipts = list(checkout_mutation_receipt.get("observer_receipts", []))
        if int(checkout_mutation_receipt.get("observer_receipt_count", 0)) != len(observer_receipts):
            errors.append(
                "checkout_mutation_receipt.observer_receipt_count must match observer_receipts"
            )
        if int(checkout_mutation_receipt.get("verified_path_count", 0)) != sum(
            receipt.get("status") == "pass"
            and receipt.get("result_state") in {"restored", "deleted"}
            for receipt in checkout_mutation_receipt.get("path_receipts", [])
        ):
            errors.append(
                "checkout_mutation_receipt.verified_path_count must match verified path_receipts"
            )
        telemetry_gate = dict(session.get("telemetry_gate", {}))
        if session.get("status") == "rolled-back":
            if not str(session.get("live_enactment_session_id", "")).startswith("enactment-session-"):
                errors.append("live_enactment_session_id must start with enactment-session-")
            if not str(session.get("restored_snapshot_ref", "")).startswith("mirage://"):
                errors.append("restored_snapshot_ref must start with mirage://")
            if not str(session.get("rollback_plan_ref", "")).startswith("rollback://"):
                errors.append("rollback_plan_ref must start with rollback://")
            if int(session.get("reverted_patch_count", 0)) < 1:
                errors.append("reverted_patch_count must be >= 1 for rolled-back sessions")
            if int(session.get("reverted_stage_count", 0)) < 1:
                errors.append("reverted_stage_count must be >= 1 for rolled-back sessions")
            reverse_apply_journal = list(session.get("reverse_apply_journal", []))
            if len(reverse_apply_journal) < 1:
                errors.append("reverse_apply_journal must include at least one entry")
            if len(reverse_apply_journal) != int(session.get("reverted_patch_count", 0)):
                errors.append("reverse_apply_journal must align with reverted_patch_count")
            if any(entry.get("status") != "pass" for entry in reverse_apply_journal):
                errors.append("reverse_apply_journal entries must all pass")
            if any(
                entry.get("result_state") not in {"restored", "deleted"}
                for entry in reverse_apply_journal
            ):
                errors.append(
                    "reverse_apply_journal entries must end in restored or deleted state"
                )
            if any(
                not str(entry.get("repo_binding_ref", "")).startswith("repo://current-checkout/")
                for entry in reverse_apply_journal
            ):
                errors.append(
                    "reverse_apply_journal entries must bind repo://current-checkout/ refs"
                )
            if any(len(str(entry.get("repo_source_digest", ""))) != 64 for entry in reverse_apply_journal):
                errors.append("reverse_apply_journal entries must include repo_source_digest")
            if any(entry.get("verification_status") != "pass" for entry in reverse_apply_journal):
                errors.append("reverse_apply_journal verification commands must all pass")
            if int(repo_binding_summary.get("bound_path_count", 0)) != len(reverse_apply_journal):
                errors.append("repo_binding_summary.bound_path_count must match reverse_apply_journal")
            if int(repo_binding_summary.get("verified_path_count", 0)) != len(reverse_apply_journal):
                errors.append(
                    "repo_binding_summary.verified_path_count must match reverse_apply_journal"
                )
            if checkout_mutation_receipt.get("status") != "verified":
                errors.append("checkout_mutation_receipt.status must equal verified")
            if not bool(checkout_mutation_receipt.get("mutation_detected")):
                errors.append("checkout_mutation_receipt must record a pre-rollback mutation")
            if not bool(checkout_mutation_receipt.get("restored_matches_baseline")):
                errors.append("checkout_mutation_receipt must restore checkout state to baseline")
            if checkout_mutation_receipt.get("observer_status") != "verified":
                errors.append("checkout_mutation_receipt.observer_status must equal verified")
            if not bool(checkout_mutation_receipt.get("observer_mutation_detected")):
                errors.append("checkout_mutation_receipt must record observer-detected mutation")
            if not bool(checkout_mutation_receipt.get("observer_restored_matches_baseline")):
                errors.append(
                    "checkout_mutation_receipt must restore observer-visible worktree state"
                )
            if not bool(checkout_mutation_receipt.get("observer_stash_state_preserved")):
                errors.append(
                    "checkout_mutation_receipt must preserve observer-visible stash state"
                )
            if checkout_mutation_receipt.get("cleanup_status") != "removed":
                errors.append("checkout_mutation_receipt.cleanup_status must equal removed")
            if int(checkout_mutation_receipt.get("observed_path_count", 0)) != len(reverse_apply_journal):
                errors.append(
                    "checkout_mutation_receipt.observed_path_count must match reverse_apply_journal"
                )
            if int(checkout_mutation_receipt.get("verified_path_count", 0)) != len(reverse_apply_journal):
                errors.append(
                    "checkout_mutation_receipt.verified_path_count must match reverse_apply_journal"
                )
            if int(checkout_mutation_receipt.get("observer_receipt_count", 0)) < 5:
                errors.append("checkout_mutation_receipt must include observer receipts for rollback")
            if len(list(session.get("continuity_event_refs", []))) < 2:
                errors.append("continuity_event_refs must include apply and rollback refs")
            if len(list(session.get("notification_refs", []))) != 3:
                errors.append("notification_refs must notify self, council, and guardian")
            if telemetry_gate.get("status") != "rollback-approved":
                errors.append("telemetry_gate.status must equal rollback-approved")
            if telemetry_gate.get("cleanup_status") != "removed":
                errors.append("telemetry_gate.cleanup_status must equal removed")
            if telemetry_gate.get("reverse_cleanup_status") != "removed":
                errors.append("telemetry_gate.reverse_cleanup_status must equal removed")
            if int(telemetry_gate.get("journal_entry_count", 0)) != len(reverse_apply_journal):
                errors.append("telemetry_gate.journal_entry_count must match reverse_apply_journal")
            if int(telemetry_gate.get("executed_reverse_command_count", 0)) != len(
                reverse_apply_journal
            ):
                errors.append(
                    "telemetry_gate.executed_reverse_command_count must match reverse_apply_journal"
                )
            if int(telemetry_gate.get("passed_reverse_command_count", 0)) != len(
                reverse_apply_journal
            ):
                errors.append(
                    "telemetry_gate.passed_reverse_command_count must match reverse_apply_journal"
                )
            if int(telemetry_gate.get("verified_reverse_command_count", 0)) != len(
                reverse_apply_journal
            ):
                errors.append(
                    "telemetry_gate.verified_reverse_command_count must match reverse_apply_journal"
                )
            if int(telemetry_gate.get("repo_bound_verified_command_count", 0)) != len(
                reverse_apply_journal
            ):
                errors.append(
                    "telemetry_gate.repo_bound_verified_command_count must match reverse_apply_journal"
                )
            if telemetry_gate.get("checkout_mutation_status") != "verified":
                errors.append("telemetry_gate.checkout_mutation_status must equal verified")
            if telemetry_gate.get("checkout_cleanup_status") != "removed":
                errors.append("telemetry_gate.checkout_cleanup_status must equal removed")
            if not bool(telemetry_gate.get("checkout_status_restored")):
                errors.append("telemetry_gate.checkout_status_restored must be true")
            if telemetry_gate.get("external_observer_status") != "verified":
                errors.append("telemetry_gate.external_observer_status must equal verified")
            if not bool(telemetry_gate.get("external_observer_restored")):
                errors.append("telemetry_gate.external_observer_restored must be true")
            if not bool(telemetry_gate.get("external_observer_stash_preserved")):
                errors.append(
                    "telemetry_gate.external_observer_stash_preserved must be true"
                )
            if not bool(telemetry_gate.get("external_observer_mutation_detected")):
                errors.append(
                    "telemetry_gate.external_observer_mutation_detected must be true"
                )
            if int(telemetry_gate.get("external_observer_receipt_count", 0)) != int(
                checkout_mutation_receipt.get("observer_receipt_count", 0)
            ):
                errors.append(
                    "telemetry_gate.external_observer_receipt_count must match observer_receipts"
                )
            if int(telemetry_gate.get("checkout_verified_path_count", 0)) != len(
                reverse_apply_journal
            ):
                errors.append(
                    "telemetry_gate.checkout_verified_path_count must match reverse_apply_journal"
                )
        return {"ok": not errors, "errors": errors}

    def _build_reverse_apply_journal(
        self,
        *,
        build_request: Mapping[str, Any],
        live_enactment_session: Mapping[str, Any],
        repo_root: Path | str,
    ) -> tuple[list[Dict[str, Any]], str]:
        repo_path = Path(repo_root)
        snapshot_refs = dict(live_enactment_session.get("workspace_snapshot_refs", {}))
        pre_apply_ref = str(snapshot_refs.get("pre_apply", ""))
        journal: list[Dict[str, Any]] = []
        temp_root = Path(tempfile.mkdtemp(prefix=self._policy.rollback_workspace_prefix))
        cleanup_status = "not-started"
        try:
            for index, item in enumerate(
                live_enactment_session.get("materialized_files", []), start=1
            ):
                target_path = str(item.get("path", ""))
                source_state = str(item.get("source_state", ""))
                rollback_action = (
                    "restore-copied-file" if source_state == "copied" else "delete-created-file"
                )
                marker = str(item.get("marker", ""))
                target = temp_root / target_path
                source = repo_path / target_path
                self._materialize_reverse_apply_target(
                    target=target,
                    source=source,
                    marker=marker,
                    source_state=source_state,
                )
                command = self._build_reverse_apply_command(
                    target_path=target_path,
                    source=source,
                    source_state=source_state,
                )
                command_run = self._run_command(command=command, workspace_root=temp_root)
                result_state = self._verify_reverse_apply_result(
                    target=target,
                    source=source,
                    source_state=source_state,
                )
                verification_command = self._build_repo_verification_command(
                    target_path=target_path,
                    source=source,
                    source_state=source_state,
                )
                verification_run = self._run_command(
                    command=verification_command,
                    workspace_root=temp_root,
                )
                repo_source_digest = sha256_text(
                    source.read_text(encoding="utf-8") if source.exists() else ""
                )
                journal.append(
                    {
                        "journal_ref": f"journal://{build_request['request_id']}/reverse/{index:02d}",
                        "path": target_path,
                        "patch_id": str(item.get("patch_id", "")),
                        "source_state": source_state,
                        "rollback_action": rollback_action,
                        "snapshot_ref": pre_apply_ref,
                        "marker": marker,
                        "repo_binding_ref": (
                            f"repo://current-checkout/{build_request['request_id']}/{index:02d}"
                        ),
                        "repo_source_digest": repo_source_digest,
                        "command": command_run["command"],
                        "exit_code": command_run["exit_code"],
                        "status": command_run["status"],
                        "stdout_excerpt": command_run["stdout_excerpt"],
                        "stderr_excerpt": command_run["stderr_excerpt"],
                        "verification_command": verification_run["command"],
                        "verification_exit_code": verification_run["exit_code"],
                        "verification_status": verification_run["status"],
                        "verification_stdout_excerpt": verification_run["stdout_excerpt"],
                        "verification_stderr_excerpt": verification_run["stderr_excerpt"],
                        "result_state": result_state,
                    }
                )
        finally:
            if self._policy.cleanup_after_run:
                shutil.rmtree(temp_root, ignore_errors=True)
                cleanup_status = "removed"
            else:
                cleanup_status = "retained"
        return journal, cleanup_status

    def _build_telemetry_gate(
        self,
        *,
        live_enactment_session: Mapping[str, Any],
        reverse_apply_journal: Sequence[Mapping[str, Any]],
        reverted_stage_ids: Sequence[str],
        reverse_cleanup_status: str,
        checkout_mutation_receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        command_runs = list(live_enactment_session.get("command_runs", []))
        passed_command_count = sum(run.get("status") == "pass" for run in command_runs)
        passed_reverse_command_count = sum(
            entry.get("status") == "pass" for entry in reverse_apply_journal
        )
        verified_reverse_command_count = sum(
            entry.get("result_state") in {"restored", "deleted"}
            for entry in reverse_apply_journal
        )
        repo_bound_verified_command_count = sum(
            entry.get("verification_status") == "pass" for entry in reverse_apply_journal
        )
        checkout_verified_path_count = sum(
            receipt.get("status") == "pass" and receipt.get("result_state") in {"restored", "deleted"}
            for receipt in checkout_mutation_receipt.get("path_receipts", [])
        )
        mutated_file_count = int(live_enactment_session.get("mutated_file_count", 0))
        cleanup_status = str(live_enactment_session.get("cleanup_status", "not-started"))
        checkout_cleanup_status = str(checkout_mutation_receipt.get("cleanup_status", "not-started"))
        checkout_mutation_status = str(checkout_mutation_receipt.get("status", "blocked"))
        checkout_status_restored = bool(checkout_mutation_receipt.get("restored_matches_baseline"))
        external_observer_status = str(
            checkout_mutation_receipt.get("observer_status", "blocked")
        )
        external_observer_receipt_count = int(
            checkout_mutation_receipt.get("observer_receipt_count", 0)
        )
        external_observer_restored = bool(
            checkout_mutation_receipt.get("observer_restored_matches_baseline")
        )
        external_observer_stash_preserved = bool(
            checkout_mutation_receipt.get("observer_stash_state_preserved")
        )
        external_observer_mutation_detected = bool(
            checkout_mutation_receipt.get("observer_mutation_detected")
        )
        blocking_reasons: list[str] = []
        if live_enactment_session.get("status") != "passed":
            blocking_reasons.append("live enactment must pass before rollback telemetry can approve")
        if cleanup_status != "removed":
            blocking_reasons.append("temp workspace cleanup must complete before rollback")
        if passed_command_count != len(command_runs):
            blocking_reasons.append("all live enactment commands must pass before rollback")
        if len(reverse_apply_journal) != mutated_file_count:
            blocking_reasons.append("reverse-apply journal must cover every materialized file")
        if passed_reverse_command_count != len(reverse_apply_journal):
            blocking_reasons.append("all reverse-apply commands must pass before rollback")
        if verified_reverse_command_count != len(reverse_apply_journal):
            blocking_reasons.append(
                "reverse-apply verification must restore or delete every materialized file"
            )
        if repo_bound_verified_command_count != len(reverse_apply_journal):
            blocking_reasons.append(
                "repo-bound verification must succeed for every reversed file"
            )
        if not bool(checkout_mutation_receipt.get("mutation_detected")):
            blocking_reasons.append(
                "checkout mutation receipt must observe a mutated checkout before rollback"
            )
        if checkout_verified_path_count != len(reverse_apply_journal):
            blocking_reasons.append(
                "checkout-bound rollback mutation must verify every reversed file"
            )
        if not checkout_status_restored:
            blocking_reasons.append("checkout-bound rollback mutation must restore baseline state")
        if external_observer_status != "verified":
            blocking_reasons.append(
                "external observer receipts must verify repo-root rollback state"
            )
        if not external_observer_restored:
            blocking_reasons.append(
                "external observer receipts must restore repo-root worktree view"
            )
        if not external_observer_stash_preserved:
            blocking_reasons.append(
                "external observer receipts must preserve repo-root stash state"
            )
        if not external_observer_mutation_detected:
            blocking_reasons.append(
                "external observer receipts must detect detached worktree mutation"
            )
        if checkout_cleanup_status != "removed":
            blocking_reasons.append("checkout-bound worktree cleanup must complete before approval")
        if checkout_mutation_status != "verified":
            blocking_reasons.append("checkout-bound mutation receipt must verify successfully")
        if reverse_cleanup_status != "removed":
            blocking_reasons.append("rollback temp workspace cleanup must complete before approval")
        if not reverted_stage_ids:
            blocking_reasons.append("rollback telemetry requires at least one reverted stage")

        return {
            "gate_id": new_id("telemetry-gate"),
            "source_enactment_session_id": str(
                live_enactment_session.get("enactment_session_id", "")
            ),
            "status": "rollback-approved" if not blocking_reasons else "blocked",
            "cleanup_status": cleanup_status,
            "executed_command_count": len(command_runs),
            "passed_command_count": passed_command_count,
            "reverse_cleanup_status": reverse_cleanup_status,
            "executed_reverse_command_count": len(reverse_apply_journal),
            "passed_reverse_command_count": passed_reverse_command_count,
            "verified_reverse_command_count": verified_reverse_command_count,
            "repo_bound_verified_command_count": repo_bound_verified_command_count,
            "checkout_mutation_status": checkout_mutation_status,
            "checkout_cleanup_status": checkout_cleanup_status,
            "checkout_verified_path_count": checkout_verified_path_count,
            "checkout_status_restored": checkout_status_restored,
            "external_observer_status": external_observer_status,
            "external_observer_receipt_count": external_observer_receipt_count,
            "external_observer_restored": external_observer_restored,
            "external_observer_stash_preserved": external_observer_stash_preserved,
            "external_observer_mutation_detected": external_observer_mutation_detected,
            "journal_entry_count": len(reverse_apply_journal),
            "reverted_stage_count": len(reverted_stage_ids),
            "decision_basis": [
                "temp-workspace-cleaned",
                "eval-command-receipts-preserved",
                "reverse-apply-journal-complete",
                "reverse-commands-verified",
                "checkout-state-restored",
            ],
            "blocking_reasons": blocking_reasons,
        }

    @staticmethod
    def _build_blocked_telemetry_gate(telemetry_gate: Mapping[str, Any]) -> Dict[str, Any]:
        gate = dict(telemetry_gate)
        gate["status"] = "blocked"
        blocking_reasons = list(gate.get("blocking_reasons", []))
        if not blocking_reasons:
            blocking_reasons.append("rollback preconditions were not satisfied")
        gate["blocking_reasons"] = blocking_reasons
        return gate

    def _materialize_reverse_apply_target(
        self,
        *,
        target: Path,
        source: Path,
        marker: str,
        source_state: str,
    ) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        base_text = source.read_text(encoding="utf-8") if source.exists() else ""
        if source_state == "copied" and base_text and not base_text.endswith("\n"):
            base_text += "\n"
        target.write_text(f"{base_text}{marker}\n", encoding="utf-8")

    def _build_checkout_mutation_receipt(
        self,
        *,
        build_request: Mapping[str, Any],
        live_enactment_session: Mapping[str, Any],
        repo_root: Path | str,
    ) -> Dict[str, Any]:
        repo_path = Path(repo_root).resolve()
        observed_paths = [
            str(item.get("path", ""))
            for item in live_enactment_session.get("materialized_files", [])
            if str(item.get("path", ""))
        ]
        temp_root = Path(tempfile.mkdtemp(prefix=self._policy.checkout_worktree_prefix))
        snapshot_root = temp_root / ".omoikane-baseline"
        git_status_argv = [
            "git",
            "status",
            "--short",
            "--untracked-files=all",
            "--",
            *observed_paths,
        ]
        git_diff_argv = [
            "git",
            "diff",
            "--no-ext-diff",
            "--binary",
            "--",
            *observed_paths,
        ]
        head_commit = "0" * 40
        baseline_status_text = ""
        baseline_diff_text = ""
        mutated_status_text = ""
        mutated_diff_text = ""
        restored_status_text = ""
        restored_diff_text = ""
        path_receipts: list[Dict[str, Any]] = []
        observer_receipts: list[Dict[str, Any]] = []
        cleanup_status = "not-started"
        added_worktree = False
        add_worktree_result: Dict[str, Any] | None = None
        git_worktree_list_argv = [
            "git",
            "-C",
            str(repo_path),
            "worktree",
            "list",
            "--porcelain",
        ]
        git_stash_list_argv = ["git", "-C", str(repo_path), "stash", "list"]

        def record_observer_receipt(
            stage: str,
            command_label: str,
            argv: Sequence[str],
        ) -> Dict[str, Any]:
            observer_run = _run_argv_command(
                argv=argv,
                cwd=repo_path,
                timeout_seconds=self._policy.command_timeout_seconds,
            )
            observer_receipts.append(
                {
                    "observer_ref": (
                        f"observer://current-checkout/{build_request['request_id']}/"
                        f"{stage}/{command_label}"
                    ),
                    "stage": stage,
                    "command_label": command_label,
                    "command": observer_run["command"],
                    "exit_code": observer_run["exit_code"],
                    "status": observer_run["status"],
                    "stdout_digest": sha256_text(observer_run.get("stdout", "")),
                    "stderr_digest": sha256_text(observer_run.get("stderr", "")),
                    "stdout_excerpt": observer_run["stdout_excerpt"],
                    "stderr_excerpt": observer_run["stderr_excerpt"],
                }
            )
            return observer_run

        try:
            record_observer_receipt("baseline", "git-worktree-list", git_worktree_list_argv)
            record_observer_receipt("baseline", "git-stash-list", git_stash_list_argv)
            add_worktree_result = _run_argv_command(
                argv=[
                    "git",
                    "-C",
                    str(repo_path),
                    "worktree",
                    "add",
                    "--detach",
                    "--force",
                    str(temp_root),
                    "HEAD",
                ],
                cwd=repo_path,
                timeout_seconds=self._policy.command_timeout_seconds,
            )
            if add_worktree_result["status"] == "pass":
                added_worktree = True
                record_observer_receipt("mutated", "git-worktree-list", git_worktree_list_argv)
                snapshot_root.mkdir(parents=True, exist_ok=True)
                head_result = _run_argv_command(
                    argv=["git", "rev-parse", "HEAD"],
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                if head_result["status"] == "pass":
                    head_commit = head_result["stdout"].strip() or head_commit

                for index, item in enumerate(
                    live_enactment_session.get("materialized_files", []), start=1
                ):
                    target_path = str(item.get("path", ""))
                    if not target_path:
                        continue
                    worktree_target = temp_root / target_path
                    repo_source = repo_path / target_path
                    baseline_snapshot = snapshot_root / target_path
                    if repo_source.exists():
                        worktree_target.parent.mkdir(parents=True, exist_ok=True)
                        baseline_snapshot.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(repo_source, worktree_target)
                        shutil.copy2(repo_source, baseline_snapshot)
                    else:
                        worktree_target.unlink(missing_ok=True)
                        baseline_snapshot.unlink(missing_ok=True)

                baseline_status = _run_argv_command(
                    argv=git_status_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                baseline_diff = _run_argv_command(
                    argv=git_diff_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                baseline_status_text = baseline_status["stdout"]
                baseline_diff_text = baseline_diff["stdout"]

                for item in live_enactment_session.get("materialized_files", []):
                    target_path = str(item.get("path", ""))
                    if not target_path:
                        continue
                    source_state = str(item.get("source_state", ""))
                    marker = str(item.get("marker", ""))
                    worktree_target = temp_root / target_path
                    self._materialize_reverse_apply_target(
                        target=worktree_target,
                        source=worktree_target,
                        marker=marker,
                        source_state=source_state,
                    )
                mutated_status = _run_argv_command(
                    argv=git_status_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                mutated_diff = _run_argv_command(
                    argv=git_diff_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                mutated_status_text = mutated_status["stdout"]
                mutated_diff_text = mutated_diff["stdout"]

                for index, item in enumerate(
                    live_enactment_session.get("materialized_files", []), start=1
                ):
                    target_path = str(item.get("path", ""))
                    if not target_path:
                        continue
                    source_state = str(item.get("source_state", ""))
                    baseline_snapshot = snapshot_root / target_path
                    command = self._build_reverse_apply_command(
                        target_path=target_path,
                        source=baseline_snapshot,
                        source_state=source_state,
                    )
                    command_run = self._run_command(command=command, workspace_root=temp_root)
                    result_state = self._verify_reverse_apply_result(
                        target=temp_root / target_path,
                        source=baseline_snapshot,
                        source_state=source_state,
                    )
                    path_receipts.append(
                        {
                            "path": target_path,
                            "source_state": source_state,
                            "baseline_snapshot_ref": (
                                f"baseline://{build_request['request_id']}/{index:02d}"
                            ),
                            "command": command_run["command"],
                            "exit_code": command_run["exit_code"],
                            "status": command_run["status"],
                            "stdout_excerpt": command_run["stdout_excerpt"],
                            "stderr_excerpt": command_run["stderr_excerpt"],
                            "result_state": result_state,
                        }
                    )

                restored_status = _run_argv_command(
                    argv=git_status_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                restored_diff = _run_argv_command(
                    argv=git_diff_argv,
                    cwd=temp_root,
                    timeout_seconds=self._policy.command_timeout_seconds,
                )
                restored_status_text = restored_status["stdout"]
                restored_diff_text = restored_diff["stdout"]
        finally:
            if self._policy.cleanup_after_run:
                if added_worktree:
                    _run_argv_command(
                        argv=[
                            "git",
                            "-C",
                            str(repo_path),
                            "worktree",
                            "remove",
                            "--force",
                            str(temp_root),
                        ],
                        cwd=repo_path,
                        timeout_seconds=self._policy.command_timeout_seconds,
                    )
                record_observer_receipt("restored", "git-worktree-list", git_worktree_list_argv)
                record_observer_receipt("restored", "git-stash-list", git_stash_list_argv)
                shutil.rmtree(temp_root, ignore_errors=True)
                cleanup_status = "removed"
            else:
                cleanup_status = "retained"

        if not added_worktree:
            return self._blocked_checkout_mutation_receipt(
                build_request=build_request,
                observed_paths=observed_paths,
                git_status_command=(
                    add_worktree_result["command"] if add_worktree_result else shlex.join(git_status_argv)
                ),
                git_diff_command=shlex.join(git_diff_argv),
                cleanup_status=cleanup_status,
                observer_receipts=observer_receipts,
            )

        observer_receipt_map = {
            (receipt["stage"], receipt["command_label"]): receipt for receipt in observer_receipts
        }
        baseline_worktree_digest = observer_receipt_map.get(
            ("baseline", "git-worktree-list"),
            {},
        ).get("stdout_digest", "")
        mutated_worktree_digest = observer_receipt_map.get(
            ("mutated", "git-worktree-list"),
            {},
        ).get("stdout_digest", "")
        restored_worktree_digest = observer_receipt_map.get(
            ("restored", "git-worktree-list"),
            {},
        ).get("stdout_digest", "")
        baseline_stash_digest = observer_receipt_map.get(
            ("baseline", "git-stash-list"),
            {},
        ).get("stdout_digest", "")
        restored_stash_digest = observer_receipt_map.get(
            ("restored", "git-stash-list"),
            {},
        ).get("stdout_digest", "")
        observer_mutation_detected = (
            bool(mutated_worktree_digest)
            and baseline_worktree_digest != mutated_worktree_digest
        )
        observer_restored_matches_baseline = (
            bool(baseline_worktree_digest)
            and baseline_worktree_digest == restored_worktree_digest
        )
        observer_stash_state_preserved = (
            bool(baseline_stash_digest)
            and baseline_stash_digest == restored_stash_digest
        )
        observer_status = (
            "verified"
            if observer_receipts
            and all(receipt["status"] == "pass" for receipt in observer_receipts)
            and observer_mutation_detected
            and observer_restored_matches_baseline
            and observer_stash_state_preserved
            else "blocked"
        )

        mutation_detected = (
            sha256_text(mutated_status_text) != sha256_text(baseline_status_text)
            or sha256_text(mutated_diff_text) != sha256_text(baseline_diff_text)
        )
        restored_matches_baseline = (
            restored_status_text == baseline_status_text
            and restored_diff_text == baseline_diff_text
            and all(
                receipt["status"] == "pass" and receipt["result_state"] in {"restored", "deleted"}
                for receipt in path_receipts
            )
        )
        verified_path_count = sum(
            receipt["status"] == "pass" and receipt["result_state"] in {"restored", "deleted"}
            for receipt in path_receipts
        )
        status = (
            "verified"
            if mutation_detected
            and restored_matches_baseline
            and observer_status == "verified"
            and cleanup_status == "removed"
            and verified_path_count == len(path_receipts)
            else "blocked"
        )
        return {
            "kind": "checkout_mutation_receipt",
            "receipt_id": new_id("checkout-receipt"),
            "strategy": self._policy.checkout_mutation_strategy,
            "worktree_ref": f"worktree://current-checkout/{build_request['request_id']}",
            "head_commit": head_commit,
            "status": status,
            "observed_paths": observed_paths,
            "observed_path_count": len(observed_paths),
            "verified_path_count": verified_path_count,
            "path_receipts": path_receipts,
            "git_status_command": shlex.join(git_status_argv),
            "git_diff_command": shlex.join(git_diff_argv),
            "observer_profile": self._policy.external_observer_profile,
            "observer_status": observer_status,
            "observer_receipt_count": len(observer_receipts),
            "observer_receipts": observer_receipts,
            "observer_mutation_detected": observer_mutation_detected,
            "observer_restored_matches_baseline": observer_restored_matches_baseline,
            "observer_stash_state_preserved": observer_stash_state_preserved,
            "baseline_status_digest": sha256_text(baseline_status_text),
            "baseline_diff_digest": sha256_text(baseline_diff_text),
            "mutated_status_digest": sha256_text(mutated_status_text),
            "mutated_diff_digest": sha256_text(mutated_diff_text),
            "restored_status_digest": sha256_text(restored_status_text),
            "restored_diff_digest": sha256_text(restored_diff_text),
            "mutation_detected": mutation_detected,
            "restored_matches_baseline": restored_matches_baseline,
            "cleanup_status": cleanup_status,
        }

    def _blocked_checkout_mutation_receipt(
        self,
        *,
        build_request: Mapping[str, Any],
        observed_paths: Sequence[str],
        git_status_command: str,
        git_diff_command: str,
        cleanup_status: str,
        observer_receipts: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "kind": "checkout_mutation_receipt",
            "receipt_id": new_id("checkout-receipt"),
            "strategy": self._policy.checkout_mutation_strategy,
            "worktree_ref": f"worktree://current-checkout/{build_request['request_id']}",
            "head_commit": "0" * 40,
            "status": "blocked",
            "observed_paths": list(observed_paths),
            "observed_path_count": len(observed_paths),
            "verified_path_count": 0,
            "path_receipts": [],
            "git_status_command": git_status_command,
            "git_diff_command": git_diff_command,
            "observer_profile": self._policy.external_observer_profile,
            "observer_status": "blocked",
            "observer_receipt_count": len(observer_receipts),
            "observer_receipts": [dict(receipt) for receipt in observer_receipts],
            "observer_mutation_detected": False,
            "observer_restored_matches_baseline": False,
            "observer_stash_state_preserved": False,
            "baseline_status_digest": sha256_text(""),
            "baseline_diff_digest": sha256_text(""),
            "mutated_status_digest": sha256_text(""),
            "mutated_diff_digest": sha256_text(""),
            "restored_status_digest": sha256_text(""),
            "restored_diff_digest": sha256_text(""),
            "mutation_detected": False,
            "restored_matches_baseline": False,
            "cleanup_status": cleanup_status,
        }

    @staticmethod
    def _build_reverse_apply_command(
        *,
        target_path: str,
        source: Path,
        source_state: str,
    ) -> str:
        if source_state == "copied":
            script = (
                "from pathlib import Path; "
                f"target = Path({json.dumps(target_path)}); "
                f"source = Path({json.dumps(str(source))}); "
                "target.parent.mkdir(parents=True, exist_ok=True); "
                "target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8'); "
                f"print({json.dumps(f'restored {target_path}')})"
            )
        else:
            script = (
                "from pathlib import Path; "
                f"target = Path({json.dumps(target_path)}); "
                "target.unlink(missing_ok=True); "
                f"print({json.dumps(f'deleted {target_path}')})"
            )
        return f"python3 -c {shlex.quote(script)}"

    @staticmethod
    def _build_repo_verification_command(
        *,
        target_path: str,
        source: Path,
        source_state: str,
    ) -> str:
        if source_state == "copied":
            script = (
                "from pathlib import Path; import sys; "
                f"target = Path({json.dumps(target_path)}); "
                f"source = Path({json.dumps(str(source))}); "
                "ok = ("
                "target.exists() and source.exists() and "
                "target.read_text(encoding='utf-8') == source.read_text(encoding='utf-8')"
                "); "
                f"print({json.dumps(f'repo-bound match {target_path}')} if ok else "
                f"{json.dumps(f'repo-bound mismatch {target_path}')}); "
                "sys.exit(0 if ok else 1)"
            )
        else:
            script = (
                "from pathlib import Path; import sys; "
                f"target = Path({json.dumps(target_path)}); "
                f"source = Path({json.dumps(str(source))}); "
                "ok = (not target.exists()) and (not source.exists()); "
                f"print({json.dumps(f'repo-bound absent {target_path}')} if ok else "
                f"{json.dumps(f'repo-bound mismatch {target_path}')}); "
                "sys.exit(0 if ok else 1)"
            )
        return f"python3 -c {shlex.quote(script)}"

    @staticmethod
    def _verify_reverse_apply_result(
        *,
        target: Path,
        source: Path,
        source_state: str,
    ) -> str:
        if source_state == "copied":
            if not source.exists() or not target.exists():
                return "mismatch"
            return (
                "restored"
                if target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")
                else "mismatch"
            )
        return "deleted" if not target.exists() else "mismatch"

    def _build_repo_binding_summary(
        self,
        *,
        build_request: Mapping[str, Any],
        reverse_apply_journal: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        path_bindings = [
            {
                "path": str(entry.get("path", "")),
                "repo_binding_ref": str(entry.get("repo_binding_ref", "")),
                "repo_source_digest": str(entry.get("repo_source_digest", "")),
            }
            for entry in reverse_apply_journal
        ]
        return {
            "binding_root_ref": f"repo://current-checkout/{build_request['request_id']}",
            "binding_scope": self._policy.repo_binding_scope,
            "bound_path_count": len(path_bindings),
            "verified_path_count": sum(
                entry.get("verification_status") == "pass" for entry in reverse_apply_journal
            ),
            "bound_paths": [binding["path"] for binding in path_bindings],
            "binding_digest": sha256_text(
                canonical_json(
                    {
                        "request_id": build_request["request_id"],
                        "binding_scope": self._policy.repo_binding_scope,
                        "paths": path_bindings,
                    }
                )
            ),
        }

    def _run_command(self, *, command: str, workspace_root: Path) -> Dict[str, Any]:
        return _run_shell_command(
            command=command,
            cwd=workspace_root,
            timeout_seconds=self._policy.command_timeout_seconds,
        )


@dataclass(frozen=True)
class LiveEnactmentPolicy:
    """Bounded live enactment policy for temp workspace mutation and eval execution."""

    policy_id: str = "builder-live-enactment-v1"
    workspace_prefix: str = "omoikane-builder-live-"
    max_materialized_files: int = 4
    command_timeout_seconds: int = 15
    cleanup_after_run: bool = True
    mandatory_eval: str = MANDATORY_LIVE_ENACTMENT_EVAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "workspace_prefix": self.workspace_prefix,
            "max_materialized_files": self.max_materialized_files,
            "command_timeout_seconds": self.command_timeout_seconds,
            "cleanup_after_run": self.cleanup_after_run,
            "mandatory_eval": self.mandatory_eval,
        }


class LiveEnactmentService:
    """Materialize builder patches in a temp workspace and run actual eval commands."""

    def __init__(self, policy: LiveEnactmentPolicy | None = None) -> None:
        self._policy = policy or LiveEnactmentPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def execute(
        self,
        *,
        build_request: Mapping[str, Any],
        build_artifact: Mapping[str, Any],
        eval_refs: Sequence[str],
        repo_root: Path | str,
    ) -> Dict[str, Any]:
        repo_path = Path(repo_root)
        patches = list(build_artifact.get("patches", []))
        allowed_write_paths = list(build_request.get("constraints", {}).get("allowed_write_paths", []))
        blocking_rules: list[str] = []

        if build_artifact.get("status") != "ready":
            blocking_rules.append("build artifact must be ready before live enactment")
        if not patches:
            blocking_rules.append("build artifact must include at least one patch descriptor")
        if len(patches) > self._policy.max_materialized_files:
            blocking_rules.append(
                f"materialized file count must be <= {self._policy.max_materialized_files}"
            )
        if not allowed_write_paths:
            blocking_rules.append("allowed_write_paths must not be empty")

        workspace_root = ""
        materialized_files: list[Dict[str, Any]] = []
        command_runs: list[Dict[str, Any]] = []
        cleanup_status = "not-started"
        snapshot_refs = {
            "pre_apply": f"mirage://{build_request['request_id']}/snapshot/live-pre-apply",
            "post_apply": f"mirage://{build_request['request_id']}/snapshot/live-post-apply",
        }

        if not blocking_rules:
            temp_root = Path(tempfile.mkdtemp(prefix=self._policy.workspace_prefix))
            workspace_root = str(temp_root)
            try:
                for patch in patches:
                    target_path = str(patch.get("target_path", ""))
                    if not _is_within_scope(target_path, allowed_write_paths):
                        blocking_rules.append(
                            f"patch target escapes allowed_write_paths: {target_path}"
                        )
                        continue
                    target = temp_root / target_path
                    source = repo_path / target_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source_state = "copied" if source.exists() else "created"
                    base_text = source.read_text(encoding="utf-8") if source.exists() else ""
                    marker = (
                        f"{self._comment_prefix(target)}workspace-enacted: "
                        f"{patch['patch_id']} target={target_path}"
                    )
                    if base_text and not base_text.endswith("\n"):
                        base_text += "\n"
                    target.write_text(f"{base_text}{marker}\n", encoding="utf-8")
                    materialized_files.append(
                        {
                            "path": target_path,
                            "patch_id": patch["patch_id"],
                            "source_state": source_state,
                            "marker": marker,
                        }
                    )

                eval_commands = self._resolve_eval_commands(eval_refs=eval_refs, repo_root=repo_path)
                if not eval_commands:
                    blocking_rules.append("eval refs must yield at least one command")

                for eval_ref, command in eval_commands:
                    command_runs.append(
                        self._run_command(
                            eval_ref=eval_ref,
                            command=command,
                            workspace_root=temp_root,
                        )
                    )
            finally:
                if self._policy.cleanup_after_run:
                    shutil.rmtree(temp_root, ignore_errors=True)
                    cleanup_status = "removed"
                else:
                    cleanup_status = "retained"

        all_commands_passed = bool(command_runs) and all(
            run["status"] == "pass" for run in command_runs
        )
        status = "blocked" if blocking_rules else "passed" if all_commands_passed else "failed"
        return {
            "kind": "builder_live_enactment_session",
            "schema_version": "1.0",
            "enactment_session_id": new_id("enactment-session"),
            "request_id": build_request["request_id"],
            "artifact_id": build_artifact.get("artifact_id", ""),
            "policy": self.policy(),
            "status": status,
            "workspace_root": workspace_root,
            "workspace_snapshot_refs": snapshot_refs,
            "materialized_files": materialized_files,
            "mutated_file_count": len(materialized_files),
            "eval_refs": list(eval_refs),
            "command_runs": command_runs,
            "executed_command_count": len(command_runs),
            "all_commands_passed": all_commands_passed,
            "cleanup_status": cleanup_status,
            "preserved_invariants": [
                "temp-workspace-only",
                "immutable-boundaries-preserved",
                "cleanup-after-run",
            ],
            "executed_at": utc_now_iso(),
            **({"blocking_rules": blocking_rules} if blocking_rules else {}),
        }

    def validate_session(self, session: Mapping[str, Any]) -> Dict[str, Any]:
        errors: list[str] = []
        if session.get("kind") != "builder_live_enactment_session":
            errors.append("kind must equal builder_live_enactment_session")
        if session.get("schema_version") != "1.0":
            errors.append("schema_version must equal 1.0")
        if session.get("status") not in {"passed", "failed", "blocked"}:
            errors.append("status must be passed, failed, or blocked")
        refs = dict(session.get("workspace_snapshot_refs", {}))
        for key in ("pre_apply", "post_apply"):
            if not str(refs.get(key, "")).startswith("mirage://"):
                errors.append(f"workspace_snapshot_refs.{key} must start with mirage://")
        if session.get("cleanup_status") not in {"removed", "retained", "not-started"}:
            errors.append("cleanup_status must be removed, retained, or not-started")
        if session.get("status") == "passed":
            if int(session.get("mutated_file_count", 0)) < 1:
                errors.append("mutated_file_count must be >= 1 for passed sessions")
            if int(session.get("executed_command_count", 0)) < 1:
                errors.append("executed_command_count must be >= 1 for passed sessions")
            if not bool(session.get("all_commands_passed")):
                errors.append("all_commands_passed must be true for passed sessions")
            if session.get("cleanup_status") != "removed":
                errors.append("cleanup_status must be removed for passed sessions")
        elif session.get("status") == "blocked" and not list(session.get("blocking_rules", [])):
            errors.append("blocked sessions must include blocking_rules")
        return {"ok": not errors, "errors": errors}

    @staticmethod
    def _comment_prefix(path: Path) -> str:
        if path.suffix in {".py", ".md", ".yaml", ".yml", ".txt", ".schema"}:
            return "# "
        return "// "

    @staticmethod
    def _resolve_eval_commands(
        *,
        eval_refs: Sequence[str],
        repo_root: Path,
    ) -> list[tuple[str, str]]:
        commands: list[tuple[str, str]] = []
        for eval_ref in eval_refs:
            eval_path = repo_root / eval_ref
            if not eval_path.exists():
                continue
            for line in eval_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("command:"):
                    commands.append((eval_ref, stripped.split(":", 1)[1].strip()))
        return commands

    def _run_command(
        self,
        *,
        eval_ref: str,
        command: str,
        workspace_root: Path,
    ) -> Dict[str, Any]:
        return {
            "eval_ref": eval_ref,
            **_run_shell_command(
                command=command,
                cwd=workspace_root,
                timeout_seconds=self._policy.command_timeout_seconds,
            ),
        }
