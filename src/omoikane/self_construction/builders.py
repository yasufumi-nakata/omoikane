"""Builder pipeline primitives for bounded self-construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Sequence

from ..common import new_id, utc_now_iso


IMMUTABLE_BOUNDARIES = ("L1.EthicsEnforcer", "L1.ContinuityLedger")
MANDATORY_BUILD_PIPELINE_EVAL = "evals/continuity/council_output_build_request_pipeline.yaml"
MANDATORY_STAGED_ROLLOUT_EVAL = "evals/continuity/builder_staged_rollout_execution.yaml"
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
        return {"ok": not errors, "errors": errors}
