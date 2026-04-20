"""DesignReader primitives for bounded self-construction handoff planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .builders import IMMUTABLE_BOUNDARIES, _is_within_scope


def _normalize_paths(paths: Sequence[str]) -> list[str]:
    ordered: list[str] = []
    for path in paths:
        if path not in ordered:
            ordered.append(path)
    return ordered


@dataclass(frozen=True)
class DesignReaderPolicy:
    """Deterministic policy for converting docs/spec references into a builder handoff."""

    policy_id: str = "doc-spec-design-delta-v0"
    required_design_prefix: str = "docs/"
    required_spec_prefix: str = "specs/"
    immutable_boundaries: tuple[str, str] = IMMUTABLE_BOUNDARIES
    sandbox_profile: str = "forked-self"
    required_alignment: str = "docs-specs-runtime"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "required_design_prefix": self.required_design_prefix,
            "required_spec_prefix": self.required_spec_prefix,
            "immutable_boundaries": list(self.immutable_boundaries),
            "sandbox_profile": self.sandbox_profile,
            "required_alignment": self.required_alignment,
        }


class DesignReaderService:
    """Read design/spec references and prepare a build-request handoff."""

    def __init__(self, policy: DesignReaderPolicy | None = None) -> None:
        self._policy = policy or DesignReaderPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def read_design_delta(
        self,
        *,
        target_subsystem: str,
        change_summary: str,
        design_refs: Sequence[str],
        spec_refs: Sequence[str],
        workspace_scope: Sequence[str],
        output_paths: Sequence[str],
        must_sync_docs: Sequence[str],
        repo_root: Path,
    ) -> Dict[str, Any]:
        normalized_design_refs = _normalize_paths(design_refs)
        normalized_spec_refs = _normalize_paths(spec_refs)
        normalized_must_sync_docs = _normalize_paths(must_sync_docs)
        normalized_workspace_scope = _normalize_paths(workspace_scope)
        normalized_output_paths = _normalize_paths(output_paths)
        source_digests: list[Dict[str, Any]] = []
        blocking_rules: list[str] = []

        for ref in normalized_design_refs:
            digest_record = self._digest_ref(
                ref=ref,
                repo_root=repo_root,
                kind="design",
                required_prefix=self._policy.required_design_prefix,
            )
            source_digests.append(digest_record)
            if digest_record["status"] != "ready":
                blocking_rules.append(digest_record["error"])
        for ref in normalized_spec_refs:
            digest_record = self._digest_ref(
                ref=ref,
                repo_root=repo_root,
                kind="spec",
                required_prefix=self._policy.required_spec_prefix,
            )
            source_digests.append(digest_record)
            if digest_record["status"] != "ready":
                blocking_rules.append(digest_record["error"])

        if not normalized_must_sync_docs:
            blocking_rules.append("must_sync_docs must not be empty")
        for ref in normalized_must_sync_docs:
            if ref not in normalized_design_refs:
                blocking_rules.append(f"must_sync_docs must be a subset of design_refs: {ref}")
        if not normalized_workspace_scope:
            blocking_rules.append("workspace_scope must not be empty")
        if not normalized_output_paths:
            blocking_rules.append("output_paths must not be empty")
        for path in normalized_output_paths:
            if not _is_within_scope(path, normalized_workspace_scope):
                blocking_rules.append(f"output_path escapes workspace_scope: {path}")

        invariants = self._derive_invariants()
        recommended_evals = ["evals/continuity/design_reader_handoff.yaml"]
        digest_material = {
            "target_subsystem": target_subsystem,
            "design_refs": normalized_design_refs,
            "spec_refs": normalized_spec_refs,
            "must_sync_docs": normalized_must_sync_docs,
            "workspace_scope": normalized_workspace_scope,
            "output_paths": normalized_output_paths,
            "source_digests": [
                {"ref": item["ref"], "digest": item["digest"], "kind": item["kind"]}
                for item in source_digests
                if item["status"] == "ready"
            ],
        }
        design_delta_digest = sha256_text(canonical_json(digest_material))
        ready = not blocking_rules

        return {
            "kind": "design_delta_manifest",
            "schema_version": "1.0.0",
            "manifest_id": new_id("design-delta"),
            "target_subsystem": target_subsystem,
            "status": "ready" if ready else "blocked",
            "summary": (
                "Design and spec references were reduced into a bounded builder handoff."
                if ready
                else "Design and spec references failed bounded handoff validation."
            ),
            "change_summary": change_summary,
            "generated_at": utc_now_iso(),
            "design_refs": normalized_design_refs,
            "spec_refs": normalized_spec_refs,
            "must_sync_docs": normalized_must_sync_docs,
            "workspace_scope": normalized_workspace_scope,
            "output_paths": normalized_output_paths,
            "immutable_boundaries": list(self._policy.immutable_boundaries),
            "invariants": invariants,
            "source_digests": source_digests,
            "recommended_evals": recommended_evals,
            "council_review_required": True,
            "guardian_review_required": True,
            "design_delta_ref": "",
            "design_delta_digest": design_delta_digest,
            "blocking_rules": blocking_rules,
        }

    def finalize_manifest(self, manifest: Mapping[str, Any]) -> Dict[str, Any]:
        finalized = dict(manifest)
        finalized["design_delta_ref"] = f"design://{manifest['manifest_id']}"
        return finalized

    def validate_manifest(self, manifest: Mapping[str, Any]) -> Dict[str, Any]:
        errors: list[str] = []
        if manifest.get("kind") != "design_delta_manifest":
            errors.append("kind must equal design_delta_manifest")
        if manifest.get("schema_version") != "1.0.0":
            errors.append("schema_version must equal 1.0.0")
        if manifest.get("status") not in {"ready", "blocked"}:
            errors.append("status must be ready or blocked")
        if not str(manifest.get("design_delta_ref", "")).startswith("design://"):
            errors.append("design_delta_ref must start with design://")
        if len(str(manifest.get("design_delta_digest", ""))) != 64:
            errors.append("design_delta_digest must be a sha256 hex digest")
        if not list(manifest.get("must_sync_docs", [])):
            errors.append("must_sync_docs must not be empty")
        if not list(manifest.get("design_refs", [])):
            errors.append("design_refs must not be empty")
        if not list(manifest.get("spec_refs", [])):
            errors.append("spec_refs must not be empty")
        if manifest.get("status") == "ready":
            for digest in manifest.get("source_digests", []):
                if digest.get("status") != "ready":
                    errors.append(f"source digest must be ready: {digest.get('ref', '')}")
        else:
            if not list(manifest.get("blocking_rules", [])):
                errors.append("blocked manifests must enumerate blocking_rules")
        return {"ok": not errors, "errors": errors}

    def prepare_build_request(
        self,
        *,
        manifest: Mapping[str, Any],
        request_id: str,
        change_class: str,
        must_pass: Sequence[str],
        council_session_id: str,
        guardian_gate: str,
    ) -> Dict[str, Any]:
        return {
            "kind": "build_request",
            "schema_version": "1.0.0",
            "request_id": request_id,
            "design_delta_ref": manifest["design_delta_ref"],
            "design_delta_digest": manifest["design_delta_digest"],
            "target_subsystem": manifest["target_subsystem"],
            "change_class": change_class,
            "change_summary": manifest["change_summary"],
            "design_refs": list(manifest["design_refs"]),
            "spec_refs": list(manifest["spec_refs"]),
            "invariants": list(manifest["invariants"]),
            "must_sync_docs": list(manifest["must_sync_docs"]),
            "constraints": {
                "must_pass": list(_normalize_paths(must_pass)),
                "forbidden": list(manifest["immutable_boundaries"]),
                "sandbox_profile": self._policy.sandbox_profile,
                "allowed_write_paths": list(manifest["output_paths"]),
            },
            "workspace_scope": list(manifest["workspace_scope"]),
            "output_paths": list(manifest["output_paths"]),
            "approval_context": {
                "council_session_id": council_session_id,
                "guardian_gate": guardian_gate,
            },
        }

    def _digest_ref(
        self,
        *,
        ref: str,
        repo_root: Path,
        kind: str,
        required_prefix: str,
    ) -> Dict[str, Any]:
        if not ref.startswith(required_prefix):
            return {
                "ref": ref,
                "kind": kind,
                "status": "missing",
                "digest": "",
                "bytes": 0,
                "error": f"{kind} ref must start with {required_prefix}: {ref}",
            }
        file_path = repo_root / ref
        if not file_path.is_file():
            return {
                "ref": ref,
                "kind": kind,
                "status": "missing",
                "digest": "",
                "bytes": 0,
                "error": f"{kind} ref does not exist: {ref}",
            }
        text = file_path.read_text(encoding="utf-8")
        return {
            "ref": ref,
            "kind": kind,
            "status": "ready",
            "digest": sha256_text(text),
            "bytes": len(text.encode("utf-8")),
            "error": "",
        }

    @staticmethod
    def _derive_invariants() -> list[str]:
        return [
            "docs/specs stay aligned before runtime promotion",
            "self_modify requires sandbox A/B + guardian_sig",
            "self_modify never targets EthicsEnforcer",
            "self_modify never weakens ContinuityLedger append-only guarantees",
        ]
