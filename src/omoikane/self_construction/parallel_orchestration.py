"""Parallel Codex worker result ingestion receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


PARALLEL_CODEX_WORKER_RESULT_PROFILE = "parallel-codex-worker-result-ingestion-v1"
PARALLEL_CODEX_INTEGRATION_POLICY_PROFILE = (
    "main-checkout-worker-result-ingestion-v1"
)
PARALLEL_CODEX_REFERENCE_RUNBOOK_REF = "references/parallel-codex-orchestration.md"
PARALLEL_CODEX_REQUIRED_VERIFICATIONS = (
    "PYTHONPATH=src python3 -m unittest discover -s tests -t .",
    "PYTHONPATH=src python3 -m omoikane.cli gap-report --json",
)
PARALLEL_CODEX_ALLOWED_WORKSPACE_PREFIXES = (
    "src/",
    "tests/",
    "specs/",
    "evals/",
    "docs/",
    "agents/",
    "meta/decision-log/",
    "references/",
)


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    ordered: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def _is_under_prefix(path: str, prefixes: Sequence[str]) -> bool:
    normalized = path.rstrip("/")
    for prefix in prefixes:
        scope = prefix.rstrip("/")
        if normalized == scope or normalized.startswith(f"{scope}/"):
            return True
    return False


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)


def _is_commit(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True)
class ParallelCodexOrchestrationPolicy:
    """Policy for accepting worker results into the main checkout."""

    profile_id: str = PARALLEL_CODEX_INTEGRATION_POLICY_PROFILE
    worker_result_profile: str = PARALLEL_CODEX_WORKER_RESULT_PROFILE
    reference_runbook_ref: str = PARALLEL_CODEX_REFERENCE_RUNBOOK_REF
    required_verifications: tuple[str, ...] = PARALLEL_CODEX_REQUIRED_VERIFICATIONS
    allowed_workspace_prefixes: tuple[str, ...] = PARALLEL_CODEX_ALLOWED_WORKSPACE_PREFIXES

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "worker_result_profile": self.worker_result_profile,
            "reference_runbook_ref": self.reference_runbook_ref,
            "required_verifications": list(self.required_verifications),
            "allowed_workspace_prefixes": list(self.allowed_workspace_prefixes),
            "raw_patch_payload_stored": False,
            "raw_transcript_payload_stored": False,
            "raw_verification_payload_stored": False,
        }


class ParallelCodexOrchestrationService:
    """Build and validate digest-only receipts for worker result handoff."""

    def __init__(self, policy: ParallelCodexOrchestrationPolicy | None = None) -> None:
        self._policy = policy or ParallelCodexOrchestrationPolicy()

    def policy(self) -> Dict[str, Any]:
        return self._policy.to_dict()

    def ingest_worker_result(
        self,
        *,
        worker_id: str,
        worker_role: str,
        worker_result_status: str,
        main_checkout_head: str,
        worker_base_commit: str,
        ownership_scope: Sequence[str],
        changed_files: Sequence[str],
        verification_results: Sequence[Mapping[str, Any]],
        result_summary: str,
        patch_digest: str = "",
    ) -> Dict[str, Any]:
        normalized_scope = _dedupe_strings(ownership_scope)
        normalized_files = _dedupe_strings(changed_files)
        normalized_verifications = self._normalize_verification_results(
            verification_results,
        )
        normalized_patch_digest = patch_digest.strip()
        if not _is_sha256(normalized_patch_digest):
            normalized_patch_digest = sha256_text(
                canonical_json(
                    {
                        "worker_id": worker_id,
                        "changed_files": normalized_files,
                        "result_summary": result_summary,
                    }
                )
            )

        receipt = {
            "kind": "parallel_codex_worker_result_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("parallel-codex-result"),
            "generated_at": utc_now_iso(),
            "profile_id": PARALLEL_CODEX_WORKER_RESULT_PROFILE,
            "integration_policy_profile": self._policy.profile_id,
            "reference_runbook_ref": self._policy.reference_runbook_ref,
            "worker_id": worker_id,
            "worker_role": worker_role,
            "worker_result_status": worker_result_status,
            "main_checkout_head": main_checkout_head,
            "worker_base_commit": worker_base_commit,
            "base_head_matches": main_checkout_head == worker_base_commit,
            "ownership_scope": normalized_scope,
            "changed_files": normalized_files,
            "changed_file_count": len(normalized_files),
            "changed_file_manifest_digest": self._changed_file_manifest_digest(
                normalized_files,
            ),
            "patch_digest": normalized_patch_digest,
            "verification_results": normalized_verifications,
            "verification_command_count": len(normalized_verifications),
            "verification_manifest_digest": self._verification_manifest_digest(
                normalized_verifications,
            ),
            "required_verifications_passed": self._required_verifications_passed(
                normalized_verifications,
            ),
            "blocking_reasons": [],
            "integration_decision": "blocked",
            "result_summary": result_summary,
            "raw_patch_payload_stored": False,
            "raw_transcript_payload_stored": False,
            "raw_verification_payload_stored": False,
            "receipt_digest": "",
        }
        receipt["receipt_ref"] = f"receipt://parallel-codex/{receipt['receipt_id']}"
        receipt["blocking_reasons"] = self._derive_blocking_reasons(receipt)
        receipt["integration_decision"] = (
            "blocked" if receipt["blocking_reasons"] else "accept-ready"
        )
        receipt["receipt_digest"] = self._receipt_digest(receipt)
        return receipt

    def validate_worker_result_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: list[str] = []
        changed_files = list(receipt.get("changed_files", []))
        verification_results = list(receipt.get("verification_results", []))
        expected_blocking_reasons = self._derive_blocking_reasons(receipt)
        expected_integration_decision = (
            "blocked" if expected_blocking_reasons else "accept-ready"
        )
        changed_digest_bound = (
            receipt.get("changed_file_manifest_digest")
            == self._changed_file_manifest_digest(changed_files)
        )
        verification_digest_bound = (
            receipt.get("verification_manifest_digest")
            == self._verification_manifest_digest(verification_results)
        )
        receipt_digest_bound = receipt.get("receipt_digest") == self._receipt_digest(
            receipt,
        )
        raw_patch_payload_redacted = receipt.get("raw_patch_payload_stored") is False
        raw_transcript_payload_redacted = (
            receipt.get("raw_transcript_payload_stored") is False
        )
        raw_verification_payload_redacted = (
            receipt.get("raw_verification_payload_stored") is False
        )

        if receipt.get("kind") != "parallel_codex_worker_result_receipt":
            errors.append("kind must be parallel_codex_worker_result_receipt")
        if receipt.get("profile_id") != PARALLEL_CODEX_WORKER_RESULT_PROFILE:
            errors.append("profile_id mismatch")
        if receipt.get("integration_policy_profile") != self._policy.profile_id:
            errors.append("integration_policy_profile mismatch")
        if receipt.get("reference_runbook_ref") != self._policy.reference_runbook_ref:
            errors.append("reference_runbook_ref mismatch")
        if receipt.get("base_head_matches") != (
            receipt.get("main_checkout_head") == receipt.get("worker_base_commit")
        ):
            errors.append("base_head_matches mismatch")
        if receipt.get("changed_file_count") != len(changed_files):
            errors.append("changed_file_count mismatch")
        if receipt.get("verification_command_count") != len(verification_results):
            errors.append("verification_command_count mismatch")
        if receipt.get("blocking_reasons") != expected_blocking_reasons:
            errors.append("blocking_reasons mismatch")
        if receipt.get("integration_decision") != expected_integration_decision:
            errors.append("integration_decision mismatch")
        if not changed_digest_bound:
            errors.append("changed_file_manifest_digest mismatch")
        if not verification_digest_bound:
            errors.append("verification_manifest_digest mismatch")
        if not receipt_digest_bound:
            errors.append("receipt_digest mismatch")
        if not (
            raw_patch_payload_redacted
            and raw_transcript_payload_redacted
            and raw_verification_payload_redacted
        ):
            errors.append("raw worker payload flags must be false")

        return {
            "ok": not errors,
            "errors": errors,
            "ready_for_main_checkout": (
                receipt.get("integration_decision") == "accept-ready"
                and not expected_blocking_reasons
            ),
            "base_head_matches": bool(receipt.get("base_head_matches")),
            "changed_file_manifest_digest_bound": changed_digest_bound,
            "verification_manifest_digest_bound": verification_digest_bound,
            "required_verifications_passed": self._required_verifications_passed(
                verification_results,
            ),
            "receipt_digest_bound": receipt_digest_bound,
            "raw_patch_payload_redacted": raw_patch_payload_redacted,
            "raw_transcript_payload_redacted": raw_transcript_payload_redacted,
            "raw_verification_payload_redacted": raw_verification_payload_redacted,
        }

    def _normalize_verification_results(
        self,
        verification_results: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        normalized: list[Dict[str, Any]] = []
        for result in verification_results:
            command = str(result.get("command", "")).strip()
            stdout_digest = str(result.get("stdout_digest", "")).strip()
            stderr_digest = str(result.get("stderr_digest", "")).strip()
            if not _is_sha256(stdout_digest):
                stdout_digest = sha256_text(str(result.get("stdout_excerpt", "")))
            if not _is_sha256(stderr_digest):
                stderr_digest = sha256_text(str(result.get("stderr_excerpt", "")))
            normalized.append(
                {
                    "command": command,
                    "status": str(result.get("status", "")).strip(),
                    "exit_code": int(result.get("exit_code", 0)),
                    "stdout_digest": stdout_digest,
                    "stderr_digest": stderr_digest,
                    "raw_stdout_stored": False,
                    "raw_stderr_stored": False,
                }
            )
        return normalized

    def _derive_blocking_reasons(self, receipt: Mapping[str, Any]) -> list[str]:
        reasons: list[str] = []
        worker_result_status = receipt.get("worker_result_status")
        ownership_scope = list(receipt.get("ownership_scope", []))
        changed_files = list(receipt.get("changed_files", []))
        verification_results = list(receipt.get("verification_results", []))

        if worker_result_status != "completed":
            reasons.append("worker_result_status must be completed before integration")
        if not _is_commit(receipt.get("main_checkout_head")):
            reasons.append("main_checkout_head must be a 40 character hex commit")
        if not _is_commit(receipt.get("worker_base_commit")):
            reasons.append("worker_base_commit must be a 40 character hex commit")
        if receipt.get("main_checkout_head") != receipt.get("worker_base_commit"):
            reasons.append("worker_base_commit must match main_checkout_head")
        if not ownership_scope:
            reasons.append("ownership_scope must not be empty")
        if not changed_files:
            reasons.append("changed_files must not be empty")
        for path in changed_files:
            if not _is_under_prefix(path, self._policy.allowed_workspace_prefixes):
                reasons.append(f"changed file outside allowed workspace prefixes: {path}")
            if ownership_scope and not _is_under_prefix(path, ownership_scope):
                reasons.append(f"changed file outside worker ownership scope: {path}")
        if not _is_sha256(receipt.get("patch_digest")):
            reasons.append("patch_digest must be a sha256 hex digest")
        for command in self._policy.required_verifications:
            matching = [
                result
                for result in verification_results
                if result.get("command") == command and result.get("status") == "pass"
            ]
            if not matching:
                reasons.append(f"required verification did not pass: {command}")
        return reasons

    @staticmethod
    def _changed_file_manifest_digest(changed_files: Sequence[str]) -> str:
        return sha256_text(canonical_json({"changed_files": list(changed_files)}))

    @staticmethod
    def _verification_manifest_digest(
        verification_results: Sequence[Mapping[str, Any]],
    ) -> str:
        digest_material = [
            {
                "command": result.get("command", ""),
                "status": result.get("status", ""),
                "exit_code": result.get("exit_code", 0),
                "stdout_digest": result.get("stdout_digest", ""),
                "stderr_digest": result.get("stderr_digest", ""),
            }
            for result in verification_results
        ]
        return sha256_text(canonical_json({"verification_results": digest_material}))

    def _required_verifications_passed(
        self,
        verification_results: Sequence[Mapping[str, Any]],
    ) -> bool:
        return all(
            any(
                result.get("command") == command and result.get("status") == "pass"
                for result in verification_results
            )
            for command in self._policy.required_verifications
        )

    @staticmethod
    def _receipt_digest_material(receipt: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            key: value
            for key, value in receipt.items()
            if key != "receipt_digest"
        }

    def _receipt_digest(self, receipt: Mapping[str, Any]) -> str:
        return sha256_text(canonical_json(self._receipt_digest_material(receipt)))
