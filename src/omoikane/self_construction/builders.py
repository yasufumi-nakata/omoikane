"""Builder pipeline primitives for bounded self-construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Sequence

from ..common import new_id, utc_now_iso


IMMUTABLE_BOUNDARIES = ("L1.EthicsEnforcer", "L1.ContinuityLedger")
MANDATORY_BUILD_PIPELINE_EVAL = "evals/continuity/council_output_build_request_pipeline.yaml"


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

        blocking_rules: list[str] = []
        for boundary in self._policy.immutable_boundaries:
            if boundary not in forbidden:
                blocking_rules.append(f"immutable boundary missing from forbidden list: {boundary}")
        for path in allowed_write_paths:
            if not _is_within_scope(path, workspace_scope):
                blocking_rules.append(f"allowed write path escapes workspace scope: {path}")
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
        build_artifact["summary"] = "Patch descriptors and regression plan emitted for sandbox-only builder execution."
        build_artifact["artifacts"] = [
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
