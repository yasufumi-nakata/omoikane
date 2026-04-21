"""DesignReader primitives for bounded self-construction handoff planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso
from .builders import (
    IMMUTABLE_BOUNDARIES,
    _is_within_scope,
    _run_argv_command,
)


DESIGN_DELTA_SCAN_PROFILE = "git-head-design-delta-v1"
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TOP_LEVEL_KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s.*)?$")
PLANNING_CUE_ORDER = (
    ("runtime-source", 0),
    ("test-coverage", 1),
    ("eval-sync", 2),
    ("docs-sync", 3),
    ("meta-decision-log", 4),
)


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


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
        source_delta_receipt: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        normalized_design_refs = _normalize_paths(design_refs)
        normalized_spec_refs = _normalize_paths(spec_refs)
        normalized_must_sync_docs = _normalize_paths(must_sync_docs)
        normalized_workspace_scope = _normalize_paths(workspace_scope)
        normalized_output_paths = _normalize_paths(output_paths)
        source_digests: list[Dict[str, Any]] = []
        blocking_rules: list[str] = []
        normalized_source_delta_receipt: Dict[str, Any] | None = None

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

        if source_delta_receipt is not None:
            normalized_source_delta_receipt = dict(source_delta_receipt)
            blocking_rules.extend(
                self._validate_source_delta_receipt(
                    normalized_source_delta_receipt,
                    design_refs=normalized_design_refs,
                    spec_refs=normalized_spec_refs,
                )
            )

        invariants = self._derive_invariants()
        recommended_evals = ["evals/continuity/design_reader_handoff.yaml"]
        if normalized_source_delta_receipt is not None:
            recommended_evals.append("evals/continuity/design_reader_git_delta_scan.yaml")
        planning_cues = self._derive_planning_cues(
            target_subsystem=target_subsystem,
            design_refs=normalized_design_refs,
            spec_refs=normalized_spec_refs,
            must_sync_docs=normalized_must_sync_docs,
            output_paths=normalized_output_paths,
            source_delta_receipt=normalized_source_delta_receipt,
        )
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
        if normalized_source_delta_receipt is not None:
            digest_material["source_delta_receipt"] = {
                "receipt_ref": normalized_source_delta_receipt.get("receipt_ref", ""),
                "receipt_digest": normalized_source_delta_receipt.get("receipt_digest", ""),
                "status": normalized_source_delta_receipt.get("status", ""),
                "changed_ref_count": normalized_source_delta_receipt.get("changed_ref_count", 0),
            }
        digest_material["planning_cues"] = planning_cues
        design_delta_digest = sha256_text(canonical_json(digest_material))
        ready = not blocking_rules

        manifest = {
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
            "planning_cues": planning_cues,
            "council_review_required": True,
            "guardian_review_required": True,
            "design_delta_ref": "",
            "design_delta_digest": design_delta_digest,
            "blocking_rules": blocking_rules,
        }
        if normalized_source_delta_receipt is not None:
            manifest["source_delta_receipt"] = normalized_source_delta_receipt
        return manifest

    def scan_repo_delta(
        self,
        *,
        design_refs: Sequence[str],
        spec_refs: Sequence[str],
        repo_root: Path,
    ) -> Dict[str, Any]:
        normalized_design_refs = _normalize_paths(design_refs)
        normalized_spec_refs = _normalize_paths(spec_refs)
        ref_kinds = {
            **{ref: "design" for ref in normalized_design_refs},
            **{ref: "spec" for ref in normalized_spec_refs},
        }
        refs = list(ref_kinds)
        blocking_reasons: list[str] = []
        command_receipts: list[Dict[str, Any]] = []
        repo_root = repo_root.resolve()

        head_result = _run_argv_command(
            argv=["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            cwd=repo_root,
            timeout_seconds=5,
        )
        command_receipts.append(self._compact_command_receipt("git-rev-parse-head", head_result))
        head_commit = str(head_result.get("stdout", "")).strip()
        if head_result["status"] != "pass" or len(head_commit) != 40:
            blocking_reasons.append("git HEAD commit could not be resolved for design delta scan")
            head_commit = "0" * 40

        status_result = _run_argv_command(
            argv=["git", "-C", str(repo_root), "status", "--short", "--", *refs],
            cwd=repo_root,
            timeout_seconds=5,
        )
        command_receipts.append(self._compact_command_receipt("git-status-short", status_result))
        status_map = self._parse_git_status_output(str(status_result.get("stdout", "")))
        if status_result["status"] != "pass":
            blocking_reasons.append("git status --short failed for design delta scan")

        entries: list[Dict[str, Any]] = []
        changed_ref_count = 0
        changed_design_ref_count = 0
        changed_spec_ref_count = 0
        for ref in refs:
            entry, entry_error = self._scan_repo_delta_entry(
                ref=ref,
                kind=ref_kinds[ref],
                repo_root=repo_root,
                working_tree_state=status_map.get(ref, "clean"),
                head_commit=head_commit,
            )
            entries.append(entry)
            if entry_error:
                blocking_reasons.append(entry_error)
            if entry["change_status"] != "unchanged":
                changed_ref_count += 1
                if entry["kind"] == "design":
                    changed_design_ref_count += 1
                else:
                    changed_spec_ref_count += 1

        status = "blocked"
        if not blocking_reasons:
            status = "delta-detected" if changed_ref_count else "clean"

        digest_material = {
            "profile_id": DESIGN_DELTA_SCAN_PROFILE,
            "repo_root": str(repo_root),
            "head_commit": head_commit,
            "status": status,
            "entries": [
                {
                    "ref": entry["ref"],
                    "kind": entry["kind"],
                    "working_tree_state": entry["working_tree_state"],
                    "change_status": entry["change_status"],
                    "baseline_digest": entry["baseline_digest"],
                    "current_digest": entry["current_digest"],
                }
                for entry in entries
            ],
            "changed_ref_count": changed_ref_count,
            "changed_design_ref_count": changed_design_ref_count,
            "changed_spec_ref_count": changed_spec_ref_count,
            "changed_section_count": sum(
                int(entry.get("changed_section_count", 0)) for entry in entries
            ),
        }
        receipt_digest = sha256_text(canonical_json(digest_material))
        receipt = {
            "kind": "design_delta_scan_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("design-delta-scan"),
            "receipt_ref": "",
            "profile_id": DESIGN_DELTA_SCAN_PROFILE,
            "repo_root": str(repo_root),
            "head_commit": head_commit,
            "status": status,
            "scanned_at": utc_now_iso(),
            "ref_count": len(refs),
            "changed_ref_count": changed_ref_count,
            "changed_design_ref_count": changed_design_ref_count,
            "changed_spec_ref_count": changed_spec_ref_count,
            "changed_section_count": digest_material["changed_section_count"],
            "entries": entries,
            "command_receipts": command_receipts,
            "receipt_digest": receipt_digest,
        }
        receipt["receipt_ref"] = f"design-scan://{receipt['receipt_id']}"
        if status == "blocked":
            receipt["blocking_reasons"] = blocking_reasons
        return receipt

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
        if not list(manifest.get("planning_cues", [])):
            errors.append("planning_cues must not be empty")
        source_delta_receipt = dict(manifest.get("source_delta_receipt", {}))
        if source_delta_receipt:
            if source_delta_receipt.get("kind") != "design_delta_scan_receipt":
                errors.append("source_delta_receipt.kind must equal design_delta_scan_receipt")
            if not str(source_delta_receipt.get("receipt_ref", "")).startswith("design-scan://"):
                errors.append("source_delta_receipt.receipt_ref must start with design-scan://")
            if len(str(source_delta_receipt.get("receipt_digest", ""))) != 64:
                errors.append("source_delta_receipt.receipt_digest must be a sha256 hex digest")
            if source_delta_receipt.get("status") == "blocked":
                errors.append("source_delta_receipt must not be blocked for a finalized manifest")
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
        validation = self.validate_manifest(manifest)
        if not validation["ok"] or manifest.get("status") != "ready":
            raise ValueError(
                "design_delta_manifest must validate and stay ready before build_request emission"
            )
        normalized_must_pass = _normalize_paths(must_pass)
        if not normalized_must_pass:
            raise ValueError("must_pass must not be empty")
        if not str(council_session_id).strip():
            raise ValueError("council_session_id must not be empty")
        if guardian_gate not in {"pass", "veto", "escalate"}:
            raise ValueError("guardian_gate must be pass, veto, or escalate")
        planning_cues = list(manifest.get("planning_cues", []))
        eval_sync_cue = self._build_eval_sync_cue(
            target_subsystem=str(manifest.get("target_subsystem", "")),
            must_pass=normalized_must_pass,
            planning_cues=planning_cues,
        )
        if eval_sync_cue is not None:
            planning_cues.append(eval_sync_cue)
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
            "planning_cues": planning_cues,
            "constraints": {
                "must_pass": normalized_must_pass,
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

    def _validate_source_delta_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        design_refs: Sequence[str],
        spec_refs: Sequence[str],
    ) -> list[str]:
        errors: list[str] = []
        if receipt.get("kind") != "design_delta_scan_receipt":
            errors.append("source_delta_receipt.kind must equal design_delta_scan_receipt")
            return errors
        if receipt.get("status") == "blocked":
            errors.append("source_delta_receipt must not be blocked")
        if not str(receipt.get("receipt_ref", "")).startswith("design-scan://"):
            errors.append("source_delta_receipt.receipt_ref must start with design-scan://")
        if len(str(receipt.get("receipt_digest", ""))) != 64:
            errors.append("source_delta_receipt.receipt_digest must be a sha256 hex digest")
        expected_refs = set(design_refs) | set(spec_refs)
        receipt_refs = {str(entry.get("ref", "")) for entry in receipt.get("entries", [])}
        if expected_refs != receipt_refs:
            errors.append("source_delta_receipt entries must cover every design/spec ref exactly once")
        if int(receipt.get("ref_count", 0)) != len(expected_refs):
            errors.append("source_delta_receipt.ref_count must match the covered ref count")
        return errors

    @staticmethod
    def _compact_command_receipt(label: str, command_result: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "command_label": label,
            "command": str(command_result.get("command", "")),
            "exit_code": int(command_result.get("exit_code", -1)),
            "status": str(command_result.get("status", "fail")),
            "stdout_excerpt": str(command_result.get("stdout_excerpt", "")),
            "stderr_excerpt": str(command_result.get("stderr_excerpt", "")),
        }

    @staticmethod
    def _parse_git_status_output(stdout: str) -> Dict[str, str]:
        status_map: Dict[str, str] = {}
        for line in stdout.splitlines():
            if len(line) < 4:
                continue
            code = line[:2]
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            status_map[path] = DesignReaderService._normalize_git_status(code)
        return status_map

    @staticmethod
    def _normalize_git_status(code: str) -> str:
        if code == "??":
            return "added"
        if "D" in code:
            return "removed"
        if any(flag in code for flag in ("M", "A", "R", "C")):
            return "modified"
        return "clean"

    def _scan_repo_delta_entry(
        self,
        *,
        ref: str,
        kind: str,
        repo_root: Path,
        working_tree_state: str,
        head_commit: str,
    ) -> tuple[Dict[str, Any], str | None]:
        file_path = repo_root / ref
        current_present = file_path.is_file()
        current_text = file_path.read_text(encoding="utf-8") if current_present else ""
        current_digest = sha256_text(current_text) if current_present else ""
        current_bytes = len(current_text.encode("utf-8")) if current_present else 0

        baseline_present = False
        baseline_text = ""
        entry_error: str | None = None
        if len(head_commit) == 40 and head_commit != "0" * 40:
            show_result = _run_argv_command(
                argv=["git", "-C", str(repo_root), "show", f"{head_commit}:{ref}"],
                cwd=repo_root,
                timeout_seconds=5,
            )
            if show_result["status"] == "pass":
                baseline_present = True
                baseline_text = str(show_result.get("stdout", ""))
            else:
                missing_blob = "exists on disk, but not in" in str(show_result.get("stderr", ""))
                missing_blob = missing_blob or "path '" in str(show_result.get("stderr", ""))
                if not missing_blob:
                    entry_error = f"git show failed for {ref}"
        baseline_digest = sha256_text(baseline_text) if baseline_present else ""
        baseline_bytes = len(baseline_text.encode("utf-8")) if baseline_present else 0

        if baseline_present and current_present:
            change_status = "unchanged" if baseline_digest == current_digest else "modified"
        elif baseline_present and not current_present:
            change_status = "removed"
        elif not baseline_present and current_present:
            change_status = "added"
        else:
            change_status = "missing"
            entry_error = entry_error or f"ref missing from HEAD and working tree: {ref}"
        section_changes = self._compare_section_changes(
            ref=ref,
            baseline_text=baseline_text,
            current_text=current_text,
        )

        return (
            {
                "ref": ref,
                "kind": kind,
                "working_tree_state": working_tree_state,
                "change_status": change_status,
                "baseline_present": baseline_present,
                "current_present": current_present,
                "baseline_digest": baseline_digest,
                "current_digest": current_digest,
                "baseline_bytes": baseline_bytes,
                "current_bytes": current_bytes,
                "changed_section_count": len(section_changes),
                "section_changes": section_changes,
            },
            entry_error,
        )

    @staticmethod
    def _derive_invariants() -> list[str]:
        return [
            "docs/specs stay aligned before runtime promotion",
            "self_modify requires sandbox A/B + guardian_sig",
            "self_modify never targets EthicsEnforcer",
            "self_modify never weakens ContinuityLedger append-only guarantees",
        ]

    def _derive_planning_cues(
        self,
        *,
        target_subsystem: str,
        design_refs: Sequence[str],
        spec_refs: Sequence[str],
        must_sync_docs: Sequence[str],
        output_paths: Sequence[str],
        source_delta_receipt: Mapping[str, Any] | None,
    ) -> list[Dict[str, Any]]:
        available_paths = list(output_paths)
        all_labels = self._section_labels_for_refs(
            source_delta_receipt=source_delta_receipt,
            refs=list(design_refs) + list(spec_refs),
        )
        docs_labels = self._section_labels_for_refs(
            source_delta_receipt=source_delta_receipt,
            refs=must_sync_docs,
        )
        planning_cues: list[Dict[str, Any]] = []
        if any(path.startswith("src/") for path in available_paths):
            planning_cues.append(
                self._make_planning_cue(
                    cue_kind="runtime-source",
                    target_subsystem=target_subsystem,
                    summary=(
                        f"Align {target_subsystem} runtime surface with the changed design/spec sections."
                    ),
                    source_refs=list(spec_refs) + list(design_refs),
                    section_labels=all_labels,
                )
            )
        if any(path.startswith("tests/") for path in available_paths):
            planning_cues.append(
                self._make_planning_cue(
                    cue_kind="test-coverage",
                    target_subsystem=target_subsystem,
                    summary=f"Refresh regression coverage for {target_subsystem} against the new handoff.",
                    source_refs=list(spec_refs),
                    section_labels=all_labels,
                )
            )
        if any(_is_within_scope(ref, available_paths) for ref in must_sync_docs):
            planning_cues.append(
                self._make_planning_cue(
                    cue_kind="docs-sync",
                    target_subsystem=target_subsystem,
                    summary="Keep must_sync_docs aligned with the approved builder handoff semantics.",
                    source_refs=list(must_sync_docs),
                    section_labels=docs_labels,
                )
            )
        if any(path.startswith("meta/decision-log/") for path in available_paths):
            planning_cues.append(
                self._make_planning_cue(
                    cue_kind="meta-decision-log",
                    target_subsystem=target_subsystem,
                    summary=f"Record the {target_subsystem} builder decision in meta/decision-log.",
                    source_refs=list(design_refs) + list(spec_refs),
                    section_labels=all_labels,
                )
            )
        return planning_cues

    def _build_eval_sync_cue(
        self,
        *,
        target_subsystem: str,
        must_pass: Sequence[str],
        planning_cues: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any] | None:
        if not must_pass:
            return None
        section_labels = _dedupe_strings(
            label
            for cue in planning_cues
            for label in cue.get("section_labels", [])
        ) or ["document-body"]
        return self._make_planning_cue(
            cue_kind="eval-sync",
            target_subsystem=target_subsystem,
            summary=f"Sync the primary continuity eval for {target_subsystem} with the approved handoff.",
            source_refs=list(must_pass),
            section_labels=section_labels,
        )

    @staticmethod
    def _make_planning_cue(
        *,
        cue_kind: str,
        target_subsystem: str,
        summary: str,
        source_refs: Sequence[str],
        section_labels: Sequence[str],
    ) -> Dict[str, Any]:
        priority = dict(PLANNING_CUE_ORDER)[cue_kind]
        payload = {
            "cue_kind": cue_kind,
            "target_subsystem": target_subsystem,
            "source_refs": _normalize_paths(source_refs),
            "section_labels": _dedupe_strings(section_labels) or ["document-body"],
            "priority": priority,
        }
        cue_id = f"planning-cue-{sha256_text(canonical_json(payload))[:12]}"
        return {
            "cue_id": cue_id,
            "cue_kind": cue_kind,
            "summary": summary,
            "priority": priority,
            "source_refs": payload["source_refs"],
            "section_labels": payload["section_labels"],
            "target_subsystem": target_subsystem,
        }

    @staticmethod
    def _section_labels_for_refs(
        *,
        source_delta_receipt: Mapping[str, Any] | None,
        refs: Sequence[str],
    ) -> list[str]:
        if source_delta_receipt is None:
            return ["document-body"]
        labels: list[str] = []
        receipt_entries = {
            str(entry.get("ref", "")): entry for entry in source_delta_receipt.get("entries", [])
        }
        for ref in refs:
            entry = receipt_entries.get(ref)
            if entry is None:
                continue
            labels.extend(
                str(change.get("section_label", ""))
                for change in entry.get("section_changes", [])
                if str(change.get("section_label", "")).strip()
            )
        return _dedupe_strings(labels) or ["document-body"]

    @staticmethod
    def _extract_sections(*, ref: str, text: str) -> list[Dict[str, Any]]:
        if not text:
            return []
        if ref.endswith(".md"):
            section_seeds = DesignReaderService._extract_markdown_sections(text)
        else:
            section_seeds = DesignReaderService._extract_structured_sections(text)
        if not section_seeds:
            section_seeds = [("document-body", "document-body", text)]
        seen: Dict[str, int] = {}
        sections: list[Dict[str, Any]] = []
        for label, section_kind, section_text in section_seeds:
            normalized_label = label.strip() or "document-body"
            count = seen.get(normalized_label, 0)
            seen[normalized_label] = count + 1
            if count:
                normalized_label = f"{normalized_label} ({count + 1})"
            section_bytes = len(section_text.encode("utf-8"))
            sections.append(
                {
                    "section_label": normalized_label,
                    "section_kind": section_kind,
                    "digest": sha256_text(section_text),
                    "bytes": section_bytes,
                }
            )
        return sections

    @staticmethod
    def _extract_markdown_sections(text: str) -> list[tuple[str, str, str]]:
        sections: list[tuple[str, str, str]] = []
        current_label = "document-body"
        current_kind = "document-body"
        current_lines: list[str] = []
        for line in text.splitlines():
            match = MARKDOWN_HEADING_RE.match(line)
            if match:
                if current_lines:
                    sections.append((current_label, current_kind, "\n".join(current_lines)))
                current_label = match.group(2).strip()
                current_kind = "markdown-heading"
                current_lines = [line]
                continue
            current_lines.append(line)
        if current_lines:
            sections.append((current_label, current_kind, "\n".join(current_lines)))
        return sections

    @staticmethod
    def _extract_structured_sections(text: str) -> list[tuple[str, str, str]]:
        sections: list[tuple[str, str, str]] = []
        current_label = "document-body"
        current_kind = "document-body"
        current_lines: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            is_top_level = line == stripped and not stripped.startswith(("#", "-"))
            match = TOP_LEVEL_KEY_RE.match(stripped) if is_top_level else None
            if match:
                if current_lines:
                    sections.append((current_label, current_kind, "\n".join(current_lines)))
                current_label = match.group(1).strip()
                current_kind = "top-level-key"
                current_lines = [line]
                continue
            current_lines.append(line)
        if current_lines:
            sections.append((current_label, current_kind, "\n".join(current_lines)))
        return sections

    @classmethod
    def _compare_section_changes(
        cls,
        *,
        ref: str,
        baseline_text: str,
        current_text: str,
    ) -> list[Dict[str, Any]]:
        baseline_sections = {
            section["section_label"]: section
            for section in cls._extract_sections(ref=ref, text=baseline_text)
        }
        current_sections = {
            section["section_label"]: section
            for section in cls._extract_sections(ref=ref, text=current_text)
        }
        ordered_labels = list(baseline_sections)
        ordered_labels.extend(label for label in current_sections if label not in ordered_labels)
        changes: list[Dict[str, Any]] = []
        for label in ordered_labels:
            baseline_section = baseline_sections.get(label)
            current_section = current_sections.get(label)
            if baseline_section is not None and current_section is not None:
                change_status = (
                    "unchanged"
                    if baseline_section["digest"] == current_section["digest"]
                    else "modified"
                )
            elif baseline_section is not None:
                change_status = "removed"
            else:
                change_status = "added"
            if change_status == "unchanged":
                continue
            section_kind = (
                str(current_section.get("section_kind"))
                if current_section is not None
                else str(baseline_section.get("section_kind"))
            )
            changes.append(
                {
                    "section_label": label,
                    "section_kind": section_kind,
                    "change_status": change_status,
                    "baseline_digest": (
                        str(baseline_section.get("digest", "")) if baseline_section is not None else ""
                    ),
                    "current_digest": (
                        str(current_section.get("digest", "")) if current_section is not None else ""
                    ),
                    "baseline_bytes": (
                        int(baseline_section.get("bytes", 0)) if baseline_section is not None else 0
                    ),
                    "current_bytes": (
                        int(current_section.get("bytes", 0)) if current_section is not None else 0
                    ),
                }
            )
        return changes
