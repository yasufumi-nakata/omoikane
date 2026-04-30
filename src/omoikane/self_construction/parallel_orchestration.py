"""Parallel Codex worker result ingestion receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


PARALLEL_CODEX_WORKER_RESULT_PROFILE = "parallel-codex-worker-result-ingestion-v1"
PARALLEL_CODEX_YAOYOROZU_BRIDGE_PROFILE = (
    "yaoyorozu-dispatch-to-parallel-codex-ingestion-v1"
)
PARALLEL_CODEX_INTEGRATION_POLICY_PROFILE = (
    "main-checkout-worker-result-ingestion-v1"
)
PARALLEL_CODEX_WORKER_IDENTITY_PROFILE = "signed-worker-identity-evidence-v1"
PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE = (
    "digest-bound-worker-identity-signature-v1"
)
PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE = "integrity-guardian"
PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM = "remote-branch-pr-worker-result"
PARALLEL_CODEX_REMOTE_METADATA_PROFILE = "remote-branch-pr-metadata-binding-v1"
PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE = "not-applicable"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE = (
    "remote-source-system-revocation-check-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE = (
    "remote-source-revocation-freshness-window-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE = (
    "remote-source-revocation-signed-provider-timestamp-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE = (
    "remote-source-revocation-provider-timestamp-signature-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS = "current-not-revoked"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS = "not-applicable"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS = "fresh"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_EXPIRED_STATUS = "expired"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS = "signed-current"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_STALE_STATUS = "stale"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_INVALID_STATUS = "invalid"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS = 900
PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE = (
    "integrity-guardian-remote-review-authority-v1"
)
PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF = (
    "policy://parallel-codex/accepted-source-systems/v1"
)
PARALLEL_CODEX_DEFAULT_REMOTE_REVIEW_AUTHORITY_REF = (
    "review-authority://integrity-guardian/remote-worker-review-v1"
)
PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_REF = (
    "revocation://parallel-codex/remote-source-systems/current-not-revoked/v1"
)
PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_FRESHNESS_REF = (
    "freshness://parallel-codex/remote-source-revocation/15m/v1"
)
PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REF = (
    "timestamp://parallel-codex/remote-source-revocation/provider-clock/v1"
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


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class ParallelCodexOrchestrationPolicy:
    """Policy for accepting worker results into the main checkout."""

    profile_id: str = PARALLEL_CODEX_INTEGRATION_POLICY_PROFILE
    worker_result_profile: str = PARALLEL_CODEX_WORKER_RESULT_PROFILE
    reference_runbook_ref: str = PARALLEL_CODEX_REFERENCE_RUNBOOK_REF
    required_verifications: tuple[str, ...] = PARALLEL_CODEX_REQUIRED_VERIFICATIONS
    allowed_workspace_prefixes: tuple[str, ...] = PARALLEL_CODEX_ALLOWED_WORKSPACE_PREFIXES
    accepted_source_systems: tuple[str, ...] = (
        "direct-worker-result",
        "yaoyorozu-worker-dispatch",
        PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "worker_result_profile": self.worker_result_profile,
            "yaoyorozu_bridge_profile": PARALLEL_CODEX_YAOYOROZU_BRIDGE_PROFILE,
            "reference_runbook_ref": self.reference_runbook_ref,
            "required_verifications": list(self.required_verifications),
            "allowed_workspace_prefixes": list(self.allowed_workspace_prefixes),
            "accepted_source_systems": list(self.accepted_source_systems),
            "worker_identity_profile": PARALLEL_CODEX_WORKER_IDENTITY_PROFILE,
            "worker_identity_signature_profile": (
                PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE
            ),
            "worker_identity_signature_role": (
                PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
            ),
            "remote_metadata_profile": PARALLEL_CODEX_REMOTE_METADATA_PROFILE,
            "remote_source_revocation_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
            ),
            "remote_source_revocation_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS
            ),
            "remote_source_revocation_freshness_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
            ),
            "remote_source_revocation_freshness_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS
            ),
            "remote_source_revocation_max_freshness_window_seconds": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS
            ),
            "remote_source_revocation_timestamp_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
            ),
            "remote_source_revocation_timestamp_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS
            ),
            "remote_source_revocation_timestamp_signature_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
            ),
            "remote_review_authority_profile": (
                PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE
            ),
            "accepted_source_policy_ref": PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF,
            "raw_patch_payload_stored": False,
            "raw_upstream_payload_stored": False,
            "raw_worker_identity_payload_stored": False,
            "raw_remote_metadata_payload_stored": False,
            "raw_remote_revocation_payload_stored": False,
            "raw_remote_revocation_freshness_payload_stored": False,
            "raw_remote_revocation_timestamp_payload_stored": False,
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
        worker_identity_ref: str = "",
        worker_identity_digest: str = "",
        worker_identity_signature_digest: str = "",
        main_checkout_head: str,
        worker_base_commit: str,
        ownership_scope: Sequence[str],
        changed_files: Sequence[str],
        verification_results: Sequence[Mapping[str, Any]],
        result_summary: str,
        patch_digest: str = "",
        source_system: str = "direct-worker-result",
        upstream_receipt_ref: str = "",
        upstream_receipt_digest: str = "",
        upstream_patch_candidate_receipt_refs: Sequence[str] = (),
        upstream_patch_candidate_receipt_digests: Sequence[str] = (),
        remote_branch_ref: str = "",
        remote_pr_ref: str = "",
        remote_review_authority_ref: str = "",
        remote_review_authority_digest: str = "",
        accepted_source_policy_ref: str = "",
        accepted_source_policy_digest: str = "",
        remote_source_revocation_ref: str = "",
        remote_source_revocation_status: str = "",
        remote_source_revocation_digest: str = "",
        remote_source_revocation_checked_at_ref: str = "",
        remote_source_revocation_freshness_window_seconds: int = (
            PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS
        ),
        remote_source_revocation_expires_at_ref: str = "",
        remote_source_revocation_freshness_status: str = "",
        remote_source_revocation_freshness_digest: str = "",
        remote_source_revocation_timestamp_ref: str = "",
        remote_source_revocation_timestamp_status: str = "",
        remote_source_revocation_timestamp_digest: str = "",
        remote_source_revocation_timestamp_signature_digest: str = "",
        remote_metadata_digest: str = "",
    ) -> Dict[str, Any]:
        normalized_source_system = source_system.strip() or "direct-worker-result"
        normalized_scope = _dedupe_strings(ownership_scope)
        normalized_files = _dedupe_strings(changed_files)
        normalized_upstream_refs = _dedupe_strings(upstream_patch_candidate_receipt_refs)
        normalized_upstream_digests = _dedupe_strings(
            upstream_patch_candidate_receipt_digests,
        )
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
        normalized_worker_identity_ref = worker_identity_ref.strip() or (
            f"worker://{normalized_source_system}/{worker_id}"
        )
        normalized_worker_identity_digest = worker_identity_digest.strip()
        if not _is_sha256(normalized_worker_identity_digest):
            normalized_worker_identity_digest = self._worker_identity_digest(
                source_system=normalized_source_system,
                worker_id=worker_id,
                worker_role=worker_role,
                worker_identity_ref=normalized_worker_identity_ref,
            )
        normalized_worker_identity_signature_digest = (
            worker_identity_signature_digest.strip()
        )
        expected_worker_identity_signature_digest = (
            self._worker_identity_signature_digest(
                worker_identity_ref=normalized_worker_identity_ref,
                worker_identity_digest=normalized_worker_identity_digest,
                main_checkout_head=main_checkout_head,
                worker_base_commit=worker_base_commit,
                patch_digest=normalized_patch_digest,
            )
        )
        if not _is_sha256(normalized_worker_identity_signature_digest):
            normalized_worker_identity_signature_digest = (
                expected_worker_identity_signature_digest
            )
        worker_identity_evidence_bound = (
            normalized_worker_identity_signature_digest
            == expected_worker_identity_signature_digest
        )
        remote_metadata = self._normalize_remote_metadata(
            source_system=normalized_source_system,
            remote_branch_ref=remote_branch_ref,
            remote_pr_ref=remote_pr_ref,
            remote_review_authority_ref=remote_review_authority_ref,
            remote_review_authority_digest=remote_review_authority_digest,
            accepted_source_policy_ref=accepted_source_policy_ref,
            accepted_source_policy_digest=accepted_source_policy_digest,
            remote_source_revocation_ref=remote_source_revocation_ref,
            remote_source_revocation_status=remote_source_revocation_status,
            remote_source_revocation_digest=remote_source_revocation_digest,
            remote_source_revocation_checked_at_ref=(
                remote_source_revocation_checked_at_ref
            ),
            remote_source_revocation_freshness_window_seconds=(
                remote_source_revocation_freshness_window_seconds
            ),
            remote_source_revocation_expires_at_ref=(
                remote_source_revocation_expires_at_ref
            ),
            remote_source_revocation_freshness_status=(
                remote_source_revocation_freshness_status
            ),
            remote_source_revocation_freshness_digest=(
                remote_source_revocation_freshness_digest
            ),
            remote_source_revocation_timestamp_ref=(
                remote_source_revocation_timestamp_ref
            ),
            remote_source_revocation_timestamp_status=(
                remote_source_revocation_timestamp_status
            ),
            remote_source_revocation_timestamp_digest=(
                remote_source_revocation_timestamp_digest
            ),
            remote_source_revocation_timestamp_signature_digest=(
                remote_source_revocation_timestamp_signature_digest
            ),
            remote_metadata_digest=remote_metadata_digest,
        )

        receipt = {
            "kind": "parallel_codex_worker_result_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("parallel-codex-result"),
            "generated_at": utc_now_iso(),
            "profile_id": PARALLEL_CODEX_WORKER_RESULT_PROFILE,
            "integration_policy_profile": self._policy.profile_id,
            "reference_runbook_ref": self._policy.reference_runbook_ref,
            "source_system": normalized_source_system,
            **remote_metadata,
            "worker_identity_profile": PARALLEL_CODEX_WORKER_IDENTITY_PROFILE,
            "worker_identity_ref": normalized_worker_identity_ref,
            "worker_identity_digest": normalized_worker_identity_digest,
            "worker_identity_signature_profile": (
                PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE
            ),
            "worker_identity_signature_role": (
                PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
            ),
            "worker_identity_signature_digest": (
                normalized_worker_identity_signature_digest
            ),
            "worker_identity_evidence_bound": worker_identity_evidence_bound,
            "upstream_receipt_ref": upstream_receipt_ref,
            "upstream_receipt_digest": upstream_receipt_digest,
            "upstream_patch_candidate_receipt_refs": normalized_upstream_refs,
            "upstream_patch_candidate_receipt_digests": normalized_upstream_digests,
            "upstream_binding_digest": self._upstream_binding_digest(
                source_system=normalized_source_system,
                upstream_receipt_ref=upstream_receipt_ref,
                upstream_receipt_digest=upstream_receipt_digest,
                upstream_patch_candidate_receipt_refs=normalized_upstream_refs,
                upstream_patch_candidate_receipt_digests=normalized_upstream_digests,
                changed_files=normalized_files,
            ),
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
            "raw_upstream_payload_stored": False,
            "raw_worker_identity_payload_stored": False,
            "raw_remote_metadata_payload_stored": False,
            "raw_remote_revocation_payload_stored": False,
            "raw_remote_revocation_freshness_payload_stored": False,
            "raw_remote_revocation_timestamp_payload_stored": False,
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

    def ingest_yaoyorozu_dispatch_receipt(
        self,
        *,
        dispatch_receipt: Mapping[str, Any],
        main_checkout_head: str,
        worker_base_commit: str,
        verification_results: Sequence[Mapping[str, Any]],
        result_summary: str = "",
        ownership_scope: Sequence[str] = (),
    ) -> Dict[str, Any]:
        changed_files = self._changed_files_from_yaoyorozu_dispatch(dispatch_receipt)
        patch_candidate_receipts = self._yaoyorozu_patch_candidate_receipts(
            dispatch_receipt,
        )
        upstream_refs = [
            str(receipt.get("receipt_ref", "")).strip()
            for receipt in patch_candidate_receipts
        ]
        upstream_digests = [
            str(receipt.get("receipt_digest", "")).strip()
            for receipt in patch_candidate_receipts
        ]
        normalized_ownership_scope = (
            _dedupe_strings(ownership_scope)
            if ownership_scope
            else self._ownership_scope_for_changed_files(changed_files)
        )
        receipt_id = str(dispatch_receipt.get("receipt_id", "")).strip()
        upstream_receipt_ref = str(dispatch_receipt.get("receipt_ref", "")).strip()
        if not upstream_receipt_ref and receipt_id:
            upstream_receipt_ref = f"dispatch-receipt://{receipt_id}"
        upstream_receipt_digest = str(dispatch_receipt.get("receipt_digest", "")).strip()
        patch_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_YAOYOROZU_BRIDGE_PROFILE,
                    "dispatch_plan_digest": dispatch_receipt.get(
                        "dispatch_plan_digest",
                        "",
                    ),
                    "dispatch_receipt_digest": upstream_receipt_digest,
                    "patch_candidate_receipt_digests": upstream_digests,
                    "changed_files": changed_files,
                }
            )
        )
        summary = result_summary or (
            "Yaoyorozu dispatch receipt, patch candidates, and changed files "
            "are reduced into one Parallel Codex ingestion receipt."
        )
        return self.ingest_worker_result(
            worker_id=f"yaoyorozu-dispatch-{receipt_id or 'unknown'}",
            worker_role="worker",
            worker_result_status=(
                "completed"
                if dispatch_receipt.get("kind") == "yaoyorozu_worker_dispatch_receipt"
                else "blocked"
            ),
            main_checkout_head=main_checkout_head,
            worker_base_commit=worker_base_commit,
            ownership_scope=normalized_ownership_scope,
            changed_files=changed_files,
            verification_results=verification_results,
            result_summary=summary,
            patch_digest=patch_digest,
            source_system="yaoyorozu-worker-dispatch",
            upstream_receipt_ref=upstream_receipt_ref,
            upstream_receipt_digest=upstream_receipt_digest,
            upstream_patch_candidate_receipt_refs=upstream_refs,
            upstream_patch_candidate_receipt_digests=upstream_digests,
        )

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
        remote_metadata_digest_bound = (
            receipt.get("remote_metadata_digest")
            == self._remote_metadata_digest(
                source_system=str(receipt.get("source_system", "")),
                remote_metadata_profile=str(
                    receipt.get("remote_metadata_profile", ""),
                ),
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                remote_review_authority_ref=str(
                    receipt.get("remote_review_authority_ref", ""),
                ),
                remote_review_authority_digest=str(
                    receipt.get("remote_review_authority_digest", ""),
                ),
                accepted_source_policy_ref=str(
                    receipt.get("accepted_source_policy_ref", ""),
                ),
                accepted_source_policy_digest=str(
                    receipt.get("accepted_source_policy_digest", ""),
                ),
                remote_source_revocation_profile=str(
                    receipt.get("remote_source_revocation_profile", ""),
                ),
                remote_source_revocation_ref=str(
                    receipt.get("remote_source_revocation_ref", ""),
                ),
                remote_source_revocation_status=str(
                    receipt.get("remote_source_revocation_status", ""),
                ),
                remote_source_revocation_digest=str(
                    receipt.get("remote_source_revocation_digest", ""),
                ),
                remote_source_revocation_freshness_profile=str(
                    receipt.get("remote_source_revocation_freshness_profile", ""),
                ),
                remote_source_revocation_checked_at_ref=str(
                    receipt.get("remote_source_revocation_checked_at_ref", ""),
                ),
                remote_source_revocation_freshness_window_seconds=_coerce_int(
                    receipt.get("remote_source_revocation_freshness_window_seconds", 0),
                ),
                remote_source_revocation_expires_at_ref=str(
                    receipt.get("remote_source_revocation_expires_at_ref", ""),
                ),
                remote_source_revocation_freshness_status=str(
                    receipt.get("remote_source_revocation_freshness_status", ""),
                ),
                remote_source_revocation_freshness_digest=str(
                    receipt.get("remote_source_revocation_freshness_digest", ""),
                ),
                remote_source_revocation_timestamp_profile=str(
                    receipt.get("remote_source_revocation_timestamp_profile", ""),
                ),
                remote_source_revocation_timestamp_ref=str(
                    receipt.get("remote_source_revocation_timestamp_ref", ""),
                ),
                remote_source_revocation_timestamp_status=str(
                    receipt.get("remote_source_revocation_timestamp_status", ""),
                ),
                remote_source_revocation_timestamp_digest=str(
                    receipt.get("remote_source_revocation_timestamp_digest", ""),
                ),
                remote_source_revocation_timestamp_signature_profile=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_signature_profile",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_signature_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_signature_digest",
                        "",
                    ),
                ),
            )
        )
        if receipt.get("source_system") == PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM:
            remote_source_revocation_timestamp_digest_bound = (
                receipt.get("remote_source_revocation_timestamp_digest")
                == self._remote_source_revocation_timestamp_digest(
                    remote_source_revocation_timestamp_ref=str(
                        receipt.get("remote_source_revocation_timestamp_ref", ""),
                    ),
                    remote_source_revocation_timestamp_status=str(
                        receipt.get("remote_source_revocation_timestamp_status", ""),
                    ),
                    remote_source_revocation_checked_at_ref=str(
                        receipt.get("remote_source_revocation_checked_at_ref", ""),
                    ),
                    remote_source_revocation_expires_at_ref=str(
                        receipt.get("remote_source_revocation_expires_at_ref", ""),
                    ),
                )
            )
            remote_source_revocation_timestamp_signature_bound = (
                receipt.get("remote_source_revocation_timestamp_signature_digest")
                == self._remote_source_revocation_timestamp_signature_digest(
                    remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                    remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                    remote_source_revocation_timestamp_ref=str(
                        receipt.get("remote_source_revocation_timestamp_ref", ""),
                    ),
                    remote_source_revocation_timestamp_digest=str(
                        receipt.get("remote_source_revocation_timestamp_digest", ""),
                    ),
                )
            )
            remote_source_revocation_freshness_digest_bound = (
                receipt.get("remote_source_revocation_freshness_digest")
                == self._remote_source_revocation_freshness_digest(
                    remote_source_revocation_checked_at_ref=str(
                        receipt.get("remote_source_revocation_checked_at_ref", ""),
                    ),
                    remote_source_revocation_freshness_window_seconds=_coerce_int(
                        receipt.get(
                            "remote_source_revocation_freshness_window_seconds",
                            0,
                        ),
                    ),
                    remote_source_revocation_expires_at_ref=str(
                        receipt.get("remote_source_revocation_expires_at_ref", ""),
                    ),
                    remote_source_revocation_freshness_status=str(
                        receipt.get("remote_source_revocation_freshness_status", ""),
                    ),
                    remote_source_revocation_timestamp_signature_digest=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_signature_digest",
                            "",
                        ),
                    ),
                )
            )
            remote_source_revocation_digest_bound = (
                receipt.get("remote_source_revocation_digest")
                == self._remote_source_revocation_digest(
                    remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                    remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                    accepted_source_policy_ref=str(
                        receipt.get("accepted_source_policy_ref", ""),
                    ),
                    accepted_source_policy_digest=str(
                        receipt.get("accepted_source_policy_digest", ""),
                    ),
                    remote_source_revocation_ref=str(
                        receipt.get("remote_source_revocation_ref", ""),
                    ),
                    remote_source_revocation_status=str(
                        receipt.get("remote_source_revocation_status", ""),
                    ),
                    remote_source_revocation_freshness_digest=str(
                        receipt.get("remote_source_revocation_freshness_digest", ""),
                    ),
                )
            )
        else:
            remote_source_revocation_timestamp_digest_bound = (
                receipt.get("remote_source_revocation_timestamp_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_revocation_timestamp_ref") == ""
                and receipt.get("remote_source_revocation_timestamp_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get("remote_source_revocation_timestamp_digest") == ""
                and receipt.get("remote_source_revocation_timestamp_signature_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get(
                    "remote_source_revocation_timestamp_signature_digest"
                )
                == ""
            )
            remote_source_revocation_timestamp_signature_bound = (
                remote_source_revocation_timestamp_digest_bound
            )
            remote_source_revocation_freshness_digest_bound = (
                receipt.get("remote_source_revocation_freshness_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_revocation_checked_at_ref") == ""
                and receipt.get("remote_source_revocation_freshness_window_seconds")
                == 0
                and receipt.get("remote_source_revocation_expires_at_ref") == ""
                and receipt.get("remote_source_revocation_freshness_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get("remote_source_revocation_freshness_digest") == ""
            )
            remote_source_revocation_digest_bound = (
                receipt.get("remote_source_revocation_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_revocation_ref") == ""
                and receipt.get("remote_source_revocation_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get("remote_source_revocation_digest") == ""
            )
        receipt_digest_bound = receipt.get("receipt_digest") == self._receipt_digest(
            receipt,
        )
        raw_patch_payload_redacted = receipt.get("raw_patch_payload_stored") is False
        raw_upstream_payload_redacted = (
            receipt.get("raw_upstream_payload_stored") is False
        )
        raw_worker_identity_payload_redacted = (
            receipt.get("raw_worker_identity_payload_stored") is False
        )
        raw_remote_metadata_payload_redacted = (
            receipt.get("raw_remote_metadata_payload_stored") is False
        )
        raw_remote_revocation_payload_redacted = (
            receipt.get("raw_remote_revocation_payload_stored") is False
        )
        raw_remote_revocation_freshness_payload_redacted = (
            receipt.get("raw_remote_revocation_freshness_payload_stored") is False
        )
        raw_remote_revocation_timestamp_payload_redacted = (
            receipt.get("raw_remote_revocation_timestamp_payload_stored") is False
        )
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
        if receipt.get("worker_identity_profile") != PARALLEL_CODEX_WORKER_IDENTITY_PROFILE:
            errors.append("worker_identity_profile mismatch")
        if (
            receipt.get("worker_identity_signature_profile")
            != PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE
        ):
            errors.append("worker_identity_signature_profile mismatch")
        if (
            receipt.get("worker_identity_signature_role")
            != PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
        ):
            errors.append("worker_identity_signature_role mismatch")
        worker_identity_signature_bound = (
            receipt.get("worker_identity_signature_digest")
            == self._worker_identity_signature_digest(
                worker_identity_ref=str(receipt.get("worker_identity_ref", "")),
                worker_identity_digest=str(
                    receipt.get("worker_identity_digest", ""),
                ),
                main_checkout_head=str(receipt.get("main_checkout_head", "")),
                worker_base_commit=str(receipt.get("worker_base_commit", "")),
                patch_digest=str(receipt.get("patch_digest", "")),
            )
        )
        worker_identity_evidence_bound = (
            bool(receipt.get("worker_identity_ref"))
            and _is_sha256(receipt.get("worker_identity_digest"))
            and worker_identity_signature_bound
            and receipt.get("worker_identity_evidence_bound") is True
        )
        if not worker_identity_signature_bound:
            errors.append("worker_identity_signature_digest mismatch")
        if receipt.get("worker_identity_evidence_bound") is not worker_identity_evidence_bound:
            errors.append("worker_identity_evidence_bound mismatch")
        remote_metadata_bound = (
            remote_metadata_digest_bound
            and remote_source_revocation_digest_bound
            and remote_source_revocation_freshness_digest_bound
            and remote_source_revocation_timestamp_digest_bound
            and remote_source_revocation_timestamp_signature_bound
            and _is_sha256(receipt.get("remote_metadata_digest"))
            and receipt.get("remote_metadata_bound") is True
        )
        if not remote_metadata_digest_bound:
            errors.append("remote_metadata_digest mismatch")
        if not remote_source_revocation_digest_bound:
            errors.append("remote_source_revocation_digest mismatch")
        if not remote_source_revocation_freshness_digest_bound:
            errors.append("remote_source_revocation_freshness_digest mismatch")
        if not remote_source_revocation_timestamp_digest_bound:
            errors.append("remote_source_revocation_timestamp_digest mismatch")
        if not remote_source_revocation_timestamp_signature_bound:
            errors.append(
                "remote_source_revocation_timestamp_signature_digest mismatch"
            )
        if receipt.get("remote_metadata_bound") is not remote_metadata_bound:
            errors.append("remote_metadata_bound mismatch")
        if receipt.get("upstream_binding_digest") != self._upstream_binding_digest(
            source_system=str(receipt.get("source_system", "")),
            upstream_receipt_ref=str(receipt.get("upstream_receipt_ref", "")),
            upstream_receipt_digest=str(receipt.get("upstream_receipt_digest", "")),
            upstream_patch_candidate_receipt_refs=list(
                receipt.get("upstream_patch_candidate_receipt_refs", []),
            ),
            upstream_patch_candidate_receipt_digests=list(
                receipt.get("upstream_patch_candidate_receipt_digests", []),
            ),
            changed_files=changed_files,
        ):
            errors.append("upstream_binding_digest mismatch")
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
            and raw_upstream_payload_redacted
            and raw_worker_identity_payload_redacted
            and raw_remote_metadata_payload_redacted
            and raw_remote_revocation_payload_redacted
            and raw_remote_revocation_freshness_payload_redacted
            and raw_remote_revocation_timestamp_payload_redacted
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
            "worker_identity_signature_bound": worker_identity_signature_bound,
            "worker_identity_evidence_bound": worker_identity_evidence_bound,
            "remote_metadata_digest_bound": remote_metadata_digest_bound,
            "remote_metadata_bound": remote_metadata_bound,
            "remote_source_revocation_digest_bound": (
                remote_source_revocation_digest_bound
            ),
            "remote_source_revocation_freshness_digest_bound": (
                remote_source_revocation_freshness_digest_bound
            ),
            "remote_source_revocation_timestamp_digest_bound": (
                remote_source_revocation_timestamp_digest_bound
            ),
            "remote_source_revocation_timestamp_signature_bound": (
                remote_source_revocation_timestamp_signature_bound
            ),
            "remote_source_revocation_not_revoked": (
                receipt.get("remote_source_revocation_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
            ),
            "remote_source_revocation_fresh": (
                receipt.get("remote_source_revocation_freshness_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
            ),
            "remote_source_revocation_timestamp_signed_current": (
                receipt.get("remote_source_revocation_timestamp_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
            ),
            "receipt_digest_bound": receipt_digest_bound,
            "raw_patch_payload_redacted": raw_patch_payload_redacted,
            "raw_upstream_payload_redacted": raw_upstream_payload_redacted,
            "raw_worker_identity_payload_redacted": raw_worker_identity_payload_redacted,
            "raw_remote_metadata_payload_redacted": (
                raw_remote_metadata_payload_redacted
            ),
            "raw_remote_revocation_payload_redacted": (
                raw_remote_revocation_payload_redacted
            ),
            "raw_remote_revocation_freshness_payload_redacted": (
                raw_remote_revocation_freshness_payload_redacted
            ),
            "raw_remote_revocation_timestamp_payload_redacted": (
                raw_remote_revocation_timestamp_payload_redacted
            ),
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
        source_system = receipt.get("source_system")
        upstream_receipt_digest = receipt.get("upstream_receipt_digest")
        upstream_patch_candidate_digests = list(
            receipt.get("upstream_patch_candidate_receipt_digests", []),
        )
        if source_system not in set(self._policy.accepted_source_systems):
            reasons.append("source_system must be an accepted worker result source")
        if source_system in {"direct-worker-result", PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM}:
            if receipt.get("upstream_receipt_ref") or upstream_receipt_digest:
                reasons.append(
                    f"{source_system} results must not carry upstream receipt refs",
                )
            if (
                receipt.get("upstream_patch_candidate_receipt_refs")
                or upstream_patch_candidate_digests
            ):
                reasons.append(
                    f"{source_system} results must not carry upstream patch candidates"
                )
        if source_system == PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM:
            if receipt.get("worker_role") != "external":
                reasons.append("remote branch / PR results must use worker_role=external")
            if receipt.get("remote_metadata_profile") != PARALLEL_CODEX_REMOTE_METADATA_PROFILE:
                reasons.append("remote_metadata_profile mismatch")
            if not receipt.get("remote_branch_ref"):
                reasons.append("remote branch metadata requires remote_branch_ref")
            if not receipt.get("remote_pr_ref"):
                reasons.append("remote PR metadata requires remote_pr_ref")
            if not receipt.get("remote_review_authority_ref"):
                reasons.append("remote review authority ref must not be empty")
            if not _is_sha256(receipt.get("remote_review_authority_digest")):
                reasons.append("remote_review_authority_digest must be sha256")
            if not receipt.get("accepted_source_policy_ref"):
                reasons.append("accepted_source_policy_ref must not be empty")
            if not _is_sha256(receipt.get("accepted_source_policy_digest")):
                reasons.append("accepted_source_policy_digest must be sha256")
            if (
                receipt.get("remote_source_revocation_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
            ):
                reasons.append("remote_source_revocation_profile mismatch")
            if not receipt.get("remote_source_revocation_ref"):
                reasons.append("remote source revocation ref must not be empty")
            if (
                receipt.get("remote_source_revocation_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS
            ):
                reasons.append(
                    "remote source revocation status must be current-not-revoked"
                )
            if (
                receipt.get("remote_source_revocation_freshness_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
            ):
                reasons.append("remote_source_revocation_freshness_profile mismatch")
            if not receipt.get("remote_source_revocation_checked_at_ref"):
                reasons.append("remote source revocation checked_at ref must not be empty")
            freshness_window_seconds = _coerce_int(
                receipt.get("remote_source_revocation_freshness_window_seconds"),
            )
            if not (
                0
                < freshness_window_seconds
                <= PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS
            ):
                reasons.append(
                    "remote source revocation freshness window must be between 1 and 900 seconds"
                )
            if not receipt.get("remote_source_revocation_expires_at_ref"):
                reasons.append("remote source revocation expires_at ref must not be empty")
            if (
                receipt.get("remote_source_revocation_freshness_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS
            ):
                reasons.append("remote source revocation freshness status must be fresh")
            if (
                receipt.get("remote_source_revocation_timestamp_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
            ):
                reasons.append("remote_source_revocation_timestamp_profile mismatch")
            if not receipt.get("remote_source_revocation_timestamp_ref"):
                reasons.append("remote source revocation timestamp ref must not be empty")
            if (
                receipt.get("remote_source_revocation_timestamp_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS
            ):
                reasons.append(
                    "remote source revocation timestamp status must be signed-current"
                )
            if not _is_sha256(
                receipt.get("remote_source_revocation_timestamp_digest")
            ):
                reasons.append("remote_source_revocation_timestamp_digest must be sha256")
            elif receipt.get(
                "remote_source_revocation_timestamp_digest"
            ) != self._remote_source_revocation_timestamp_digest(
                remote_source_revocation_timestamp_ref=str(
                    receipt.get("remote_source_revocation_timestamp_ref", ""),
                ),
                remote_source_revocation_timestamp_status=str(
                    receipt.get("remote_source_revocation_timestamp_status", ""),
                ),
                remote_source_revocation_checked_at_ref=str(
                    receipt.get("remote_source_revocation_checked_at_ref", ""),
                ),
                remote_source_revocation_expires_at_ref=str(
                    receipt.get("remote_source_revocation_expires_at_ref", ""),
                ),
            ):
                reasons.append("remote_source_revocation_timestamp_digest mismatch")
            if (
                receipt.get("remote_source_revocation_timestamp_signature_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_signature_profile mismatch"
                )
            if not _is_sha256(
                receipt.get("remote_source_revocation_timestamp_signature_digest")
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_signature_digest must be sha256"
                )
            elif receipt.get(
                "remote_source_revocation_timestamp_signature_digest"
            ) != self._remote_source_revocation_timestamp_signature_digest(
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                remote_source_revocation_timestamp_ref=str(
                    receipt.get("remote_source_revocation_timestamp_ref", ""),
                ),
                remote_source_revocation_timestamp_digest=str(
                    receipt.get("remote_source_revocation_timestamp_digest", ""),
                ),
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_signature_digest mismatch"
                )
            if not _is_sha256(
                receipt.get("remote_source_revocation_freshness_digest")
            ):
                reasons.append(
                    "remote_source_revocation_freshness_digest must be sha256"
                )
            elif receipt.get(
                "remote_source_revocation_freshness_digest"
            ) != self._remote_source_revocation_freshness_digest(
                remote_source_revocation_checked_at_ref=str(
                    receipt.get("remote_source_revocation_checked_at_ref", ""),
                ),
                remote_source_revocation_freshness_window_seconds=(
                    freshness_window_seconds
                ),
                remote_source_revocation_expires_at_ref=str(
                    receipt.get("remote_source_revocation_expires_at_ref", ""),
                ),
                remote_source_revocation_freshness_status=str(
                    receipt.get("remote_source_revocation_freshness_status", ""),
                ),
                remote_source_revocation_timestamp_signature_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_signature_digest",
                        "",
                    ),
                ),
            ):
                reasons.append("remote_source_revocation_freshness_digest mismatch")
            if not _is_sha256(receipt.get("remote_source_revocation_digest")):
                reasons.append("remote_source_revocation_digest must be sha256")
            elif receipt.get(
                "remote_source_revocation_digest"
            ) != self._remote_source_revocation_digest(
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                accepted_source_policy_ref=str(
                    receipt.get("accepted_source_policy_ref", ""),
                ),
                accepted_source_policy_digest=str(
                    receipt.get("accepted_source_policy_digest", ""),
                ),
                remote_source_revocation_ref=str(
                    receipt.get("remote_source_revocation_ref", ""),
                ),
                remote_source_revocation_status=str(
                    receipt.get("remote_source_revocation_status", ""),
                ),
                remote_source_revocation_freshness_digest=str(
                    receipt.get("remote_source_revocation_freshness_digest", ""),
                ),
            ):
                reasons.append("remote_source_revocation_digest mismatch")
        else:
            if (
                receipt.get("remote_metadata_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append("non-remote result must mark remote metadata not-applicable")
            remote_refs_or_digests = [
                receipt.get("remote_branch_ref"),
                receipt.get("remote_pr_ref"),
                receipt.get("remote_review_authority_ref"),
                receipt.get("remote_review_authority_digest"),
                receipt.get("accepted_source_policy_ref"),
                receipt.get("accepted_source_policy_digest"),
                receipt.get("remote_source_revocation_ref"),
                receipt.get("remote_source_revocation_digest"),
                receipt.get("remote_source_revocation_checked_at_ref"),
                receipt.get("remote_source_revocation_expires_at_ref"),
                receipt.get("remote_source_revocation_freshness_digest"),
                receipt.get("remote_source_revocation_timestamp_ref"),
                receipt.get("remote_source_revocation_timestamp_digest"),
                receipt.get("remote_source_revocation_timestamp_signature_digest"),
            ]
            if any(remote_refs_or_digests):
                reasons.append("non-remote result must not carry remote metadata refs")
            if (
                receipt.get("remote_source_revocation_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote revocation not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote revocation status not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_freshness_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote revocation freshness not-applicable"
                )
            if (
                _coerce_int(
                    receipt.get("remote_source_revocation_freshness_window_seconds"),
                )
                != 0
            ):
                reasons.append(
                    "non-remote result must use zero remote revocation freshness window"
                )
            if (
                receipt.get("remote_source_revocation_freshness_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote revocation freshness status not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote revocation timestamp not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote revocation timestamp status not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_signature_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote revocation timestamp signature not-applicable"
                )
        if not _is_sha256(receipt.get("remote_metadata_digest")):
            reasons.append("remote_metadata_digest must be a sha256 hex digest")
        elif receipt.get("remote_metadata_digest") != self._remote_metadata_digest(
            source_system=str(receipt.get("source_system", "")),
            remote_metadata_profile=str(receipt.get("remote_metadata_profile", "")),
            remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
            remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
            remote_review_authority_ref=str(
                receipt.get("remote_review_authority_ref", ""),
            ),
            remote_review_authority_digest=str(
                receipt.get("remote_review_authority_digest", ""),
            ),
            accepted_source_policy_ref=str(
                receipt.get("accepted_source_policy_ref", ""),
            ),
            accepted_source_policy_digest=str(
                receipt.get("accepted_source_policy_digest", ""),
            ),
            remote_source_revocation_profile=str(
                receipt.get("remote_source_revocation_profile", ""),
            ),
            remote_source_revocation_ref=str(
                receipt.get("remote_source_revocation_ref", ""),
            ),
            remote_source_revocation_status=str(
                receipt.get("remote_source_revocation_status", ""),
            ),
            remote_source_revocation_digest=str(
                receipt.get("remote_source_revocation_digest", ""),
            ),
            remote_source_revocation_freshness_profile=str(
                receipt.get("remote_source_revocation_freshness_profile", ""),
            ),
            remote_source_revocation_checked_at_ref=str(
                receipt.get("remote_source_revocation_checked_at_ref", ""),
            ),
            remote_source_revocation_freshness_window_seconds=_coerce_int(
                receipt.get("remote_source_revocation_freshness_window_seconds", 0),
            ),
            remote_source_revocation_expires_at_ref=str(
                receipt.get("remote_source_revocation_expires_at_ref", ""),
            ),
            remote_source_revocation_freshness_status=str(
                receipt.get("remote_source_revocation_freshness_status", ""),
            ),
            remote_source_revocation_freshness_digest=str(
                receipt.get("remote_source_revocation_freshness_digest", ""),
            ),
            remote_source_revocation_timestamp_profile=str(
                receipt.get("remote_source_revocation_timestamp_profile", ""),
            ),
            remote_source_revocation_timestamp_ref=str(
                receipt.get("remote_source_revocation_timestamp_ref", ""),
            ),
            remote_source_revocation_timestamp_status=str(
                receipt.get("remote_source_revocation_timestamp_status", ""),
            ),
            remote_source_revocation_timestamp_digest=str(
                receipt.get("remote_source_revocation_timestamp_digest", ""),
            ),
            remote_source_revocation_timestamp_signature_profile=str(
                receipt.get("remote_source_revocation_timestamp_signature_profile", ""),
            ),
            remote_source_revocation_timestamp_signature_digest=str(
                receipt.get(
                    "remote_source_revocation_timestamp_signature_digest",
                    "",
                ),
            ),
        ):
            reasons.append("remote_metadata_digest mismatch")
        if receipt.get("remote_metadata_bound") is not True:
            reasons.append("remote_metadata_bound must be true")
        if receipt.get("raw_remote_metadata_payload_stored") is not False:
            reasons.append("raw_remote_metadata_payload_stored must be false")
        if receipt.get("raw_remote_revocation_payload_stored") is not False:
            reasons.append("raw_remote_revocation_payload_stored must be false")
        if receipt.get("raw_remote_revocation_freshness_payload_stored") is not False:
            reasons.append(
                "raw_remote_revocation_freshness_payload_stored must be false"
            )
        if receipt.get("raw_remote_revocation_timestamp_payload_stored") is not False:
            reasons.append(
                "raw_remote_revocation_timestamp_payload_stored must be false"
            )
        if source_system == "yaoyorozu-worker-dispatch":
            if not receipt.get("upstream_receipt_ref"):
                reasons.append("yaoyorozu bridge requires upstream_receipt_ref")
            if not _is_sha256(upstream_receipt_digest):
                reasons.append(
                    "yaoyorozu bridge requires upstream_receipt_digest sha256"
                )
            if not upstream_patch_candidate_digests:
                reasons.append(
                    "yaoyorozu bridge requires patch candidate receipt digests"
                )
            for digest in upstream_patch_candidate_digests:
                if not _is_sha256(digest):
                    reasons.append(
                        "upstream patch candidate receipt digest must be sha256"
                    )
            if not receipt.get("upstream_patch_candidate_receipt_refs"):
                reasons.append(
                    "yaoyorozu bridge requires patch candidate receipt refs"
                )
        if not _is_sha256(receipt.get("upstream_binding_digest")):
            reasons.append("upstream_binding_digest must be a sha256 hex digest")
        if receipt.get("raw_upstream_payload_stored") is not False:
            reasons.append("raw_upstream_payload_stored must be false")
        if receipt.get("worker_identity_profile") != PARALLEL_CODEX_WORKER_IDENTITY_PROFILE:
            reasons.append("worker_identity_profile mismatch")
        if not receipt.get("worker_identity_ref"):
            reasons.append("worker_identity_ref must not be empty")
        if not _is_sha256(receipt.get("worker_identity_digest")):
            reasons.append("worker_identity_digest must be a sha256 hex digest")
        if (
            receipt.get("worker_identity_signature_profile")
            != PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE
        ):
            reasons.append("worker_identity_signature_profile mismatch")
        if (
            receipt.get("worker_identity_signature_role")
            != PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
        ):
            reasons.append("worker_identity_signature_role mismatch")
        if (
            receipt.get("worker_identity_signature_digest")
            != self._worker_identity_signature_digest(
                worker_identity_ref=str(receipt.get("worker_identity_ref", "")),
                worker_identity_digest=str(
                    receipt.get("worker_identity_digest", ""),
                ),
                main_checkout_head=str(receipt.get("main_checkout_head", "")),
                worker_base_commit=str(receipt.get("worker_base_commit", "")),
                patch_digest=str(receipt.get("patch_digest", "")),
            )
        ):
            reasons.append("worker_identity_signature_digest mismatch")
        if receipt.get("worker_identity_evidence_bound") is not True:
            reasons.append("worker_identity_evidence_bound must be true")
        if receipt.get("raw_worker_identity_payload_stored") is not False:
            reasons.append("raw_worker_identity_payload_stored must be false")
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
    def _worker_identity_digest(
        *,
        source_system: str,
        worker_id: str,
        worker_role: str,
        worker_identity_ref: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_WORKER_IDENTITY_PROFILE,
                    "source_system": source_system,
                    "worker_id": worker_id,
                    "worker_role": worker_role,
                    "worker_identity_ref": worker_identity_ref,
                }
            )
        )

    @staticmethod
    def _worker_identity_signature_digest(
        *,
        worker_identity_ref: str,
        worker_identity_digest: str,
        main_checkout_head: str,
        worker_base_commit: str,
        patch_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "signature_profile": PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_PROFILE,
                    "signature_role": PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE,
                    "worker_identity_ref": worker_identity_ref,
                    "worker_identity_digest": worker_identity_digest,
                    "main_checkout_head": main_checkout_head,
                    "worker_base_commit": worker_base_commit,
                    "patch_digest": patch_digest,
                }
            )
        )

    @staticmethod
    def _accepted_source_policy_digest() -> str:
        return sha256_text(
            canonical_json(
                {
                    "policy_ref": PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF,
                    "accepted_source_systems": [
                        "direct-worker-result",
                        "yaoyorozu-worker-dispatch",
                        PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM,
                    ],
                    "remote_metadata_profile": PARALLEL_CODEX_REMOTE_METADATA_PROFILE,
                    "remote_review_authority_profile": (
                        PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE
                    ),
                    "remote_source_revocation_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
                    ),
                    "remote_source_revocation_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS
                    ),
                    "remote_source_revocation_freshness_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
                    ),
                    "remote_source_revocation_freshness_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS
                    ),
                    "remote_source_revocation_max_freshness_window_seconds": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS
                    ),
                    "remote_source_revocation_timestamp_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
                    ),
                    "remote_source_revocation_timestamp_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS
                    ),
                    "remote_source_revocation_timestamp_signature_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
                    ),
                }
            )
        )

    @staticmethod
    def _remote_review_authority_digest(remote_review_authority_ref: str) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE,
                    "authority_ref": remote_review_authority_ref,
                    "required_signature_role": (
                        PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
                    ),
                    "accepted_source_policy_ref": (
                        PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF
                    ),
                    "remote_source_revocation_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
                    ),
                    "remote_source_revocation_freshness_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
                    ),
                    "remote_source_revocation_timestamp_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
                    ),
                    "remote_source_revocation_timestamp_signature_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
                    ),
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_timestamp_digest(
        *,
        remote_source_revocation_timestamp_ref: str,
        remote_source_revocation_timestamp_status: str,
        remote_source_revocation_checked_at_ref: str,
        remote_source_revocation_expires_at_ref: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
                    ),
                    "timestamp_ref": remote_source_revocation_timestamp_ref,
                    "timestamp_status": remote_source_revocation_timestamp_status,
                    "checked_at_ref": remote_source_revocation_checked_at_ref,
                    "expires_at_ref": remote_source_revocation_expires_at_ref,
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_timestamp_signature_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_source_revocation_timestamp_ref: str,
        remote_source_revocation_timestamp_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "signature_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
                    ),
                    "signature_role": (
                        PARALLEL_CODEX_WORKER_IDENTITY_SIGNATURE_ROLE
                    ),
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "timestamp_ref": remote_source_revocation_timestamp_ref,
                    "timestamp_digest": remote_source_revocation_timestamp_digest,
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_freshness_digest(
        *,
        remote_source_revocation_checked_at_ref: str,
        remote_source_revocation_freshness_window_seconds: int,
        remote_source_revocation_expires_at_ref: str,
        remote_source_revocation_freshness_status: str,
        remote_source_revocation_timestamp_signature_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
                    ),
                    "checked_at_ref": remote_source_revocation_checked_at_ref,
                    "freshness_window_seconds": (
                        remote_source_revocation_freshness_window_seconds
                    ),
                    "expires_at_ref": remote_source_revocation_expires_at_ref,
                    "freshness_status": remote_source_revocation_freshness_status,
                    "timestamp_signature_digest": (
                        remote_source_revocation_timestamp_signature_digest
                    ),
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        accepted_source_policy_ref: str,
        accepted_source_policy_digest: str,
        remote_source_revocation_ref: str,
        remote_source_revocation_status: str,
        remote_source_revocation_freshness_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "accepted_source_policy_ref": accepted_source_policy_ref,
                    "accepted_source_policy_digest": accepted_source_policy_digest,
                    "remote_source_revocation_ref": remote_source_revocation_ref,
                    "remote_source_revocation_status": remote_source_revocation_status,
                    "remote_source_revocation_freshness_digest": (
                        remote_source_revocation_freshness_digest
                    ),
                }
            )
        )

    @staticmethod
    def _remote_metadata_digest(
        *,
        source_system: str,
        remote_metadata_profile: str,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_review_authority_ref: str,
        remote_review_authority_digest: str,
        accepted_source_policy_ref: str,
        accepted_source_policy_digest: str,
        remote_source_revocation_profile: str,
        remote_source_revocation_ref: str,
        remote_source_revocation_status: str,
        remote_source_revocation_digest: str,
        remote_source_revocation_freshness_profile: str,
        remote_source_revocation_checked_at_ref: str,
        remote_source_revocation_freshness_window_seconds: int,
        remote_source_revocation_expires_at_ref: str,
        remote_source_revocation_freshness_status: str,
        remote_source_revocation_freshness_digest: str,
        remote_source_revocation_timestamp_profile: str,
        remote_source_revocation_timestamp_ref: str,
        remote_source_revocation_timestamp_status: str,
        remote_source_revocation_timestamp_digest: str,
        remote_source_revocation_timestamp_signature_profile: str,
        remote_source_revocation_timestamp_signature_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "source_system": source_system,
                    "remote_metadata_profile": remote_metadata_profile,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "remote_review_authority_ref": remote_review_authority_ref,
                    "remote_review_authority_digest": remote_review_authority_digest,
                    "accepted_source_policy_ref": accepted_source_policy_ref,
                    "accepted_source_policy_digest": accepted_source_policy_digest,
                    "remote_source_revocation_profile": (
                        remote_source_revocation_profile
                    ),
                    "remote_source_revocation_ref": remote_source_revocation_ref,
                    "remote_source_revocation_status": (
                        remote_source_revocation_status
                    ),
                    "remote_source_revocation_digest": (
                        remote_source_revocation_digest
                    ),
                    "remote_source_revocation_freshness_profile": (
                        remote_source_revocation_freshness_profile
                    ),
                    "remote_source_revocation_checked_at_ref": (
                        remote_source_revocation_checked_at_ref
                    ),
                    "remote_source_revocation_freshness_window_seconds": (
                        remote_source_revocation_freshness_window_seconds
                    ),
                    "remote_source_revocation_expires_at_ref": (
                        remote_source_revocation_expires_at_ref
                    ),
                    "remote_source_revocation_freshness_status": (
                        remote_source_revocation_freshness_status
                    ),
                    "remote_source_revocation_freshness_digest": (
                        remote_source_revocation_freshness_digest
                    ),
                    "remote_source_revocation_timestamp_profile": (
                        remote_source_revocation_timestamp_profile
                    ),
                    "remote_source_revocation_timestamp_ref": (
                        remote_source_revocation_timestamp_ref
                    ),
                    "remote_source_revocation_timestamp_status": (
                        remote_source_revocation_timestamp_status
                    ),
                    "remote_source_revocation_timestamp_digest": (
                        remote_source_revocation_timestamp_digest
                    ),
                    "remote_source_revocation_timestamp_signature_profile": (
                        remote_source_revocation_timestamp_signature_profile
                    ),
                    "remote_source_revocation_timestamp_signature_digest": (
                        remote_source_revocation_timestamp_signature_digest
                    ),
                }
            )
        )

    def _normalize_remote_metadata(
        self,
        *,
        source_system: str,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_review_authority_ref: str,
        remote_review_authority_digest: str,
        accepted_source_policy_ref: str,
        accepted_source_policy_digest: str,
        remote_source_revocation_ref: str,
        remote_source_revocation_status: str,
        remote_source_revocation_digest: str,
        remote_source_revocation_checked_at_ref: str,
        remote_source_revocation_freshness_window_seconds: int,
        remote_source_revocation_expires_at_ref: str,
        remote_source_revocation_freshness_status: str,
        remote_source_revocation_freshness_digest: str,
        remote_source_revocation_timestamp_ref: str,
        remote_source_revocation_timestamp_status: str,
        remote_source_revocation_timestamp_digest: str,
        remote_source_revocation_timestamp_signature_digest: str,
        remote_metadata_digest: str,
    ) -> Dict[str, Any]:
        if source_system != PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM:
            normalized_profile = PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            normalized_metadata = {
                "remote_metadata_profile": normalized_profile,
                "remote_branch_ref": "",
                "remote_pr_ref": "",
                "remote_review_authority_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_review_authority_ref": "",
                "remote_review_authority_digest": "",
                "accepted_source_policy_ref": "",
                "accepted_source_policy_digest": "",
                "remote_source_revocation_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_revocation_ref": "",
                "remote_source_revocation_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_revocation_digest": "",
                "remote_source_revocation_freshness_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_revocation_checked_at_ref": "",
                "remote_source_revocation_freshness_window_seconds": 0,
                "remote_source_revocation_expires_at_ref": "",
                "remote_source_revocation_freshness_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_revocation_freshness_digest": "",
                "remote_source_revocation_timestamp_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_revocation_timestamp_ref": "",
                "remote_source_revocation_timestamp_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_revocation_timestamp_digest": "",
                "remote_source_revocation_timestamp_signature_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_revocation_timestamp_signature_digest": "",
            }
            normalized_metadata["remote_metadata_digest"] = self._remote_metadata_digest(
                source_system=source_system,
                remote_metadata_profile=normalized_profile,
                remote_branch_ref="",
                remote_pr_ref="",
                remote_review_authority_ref="",
                remote_review_authority_digest="",
                accepted_source_policy_ref="",
                accepted_source_policy_digest="",
                remote_source_revocation_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_revocation_ref="",
                remote_source_revocation_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_revocation_digest="",
                remote_source_revocation_freshness_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_revocation_checked_at_ref="",
                remote_source_revocation_freshness_window_seconds=0,
                remote_source_revocation_expires_at_ref="",
                remote_source_revocation_freshness_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_revocation_freshness_digest="",
                remote_source_revocation_timestamp_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_revocation_timestamp_ref="",
                remote_source_revocation_timestamp_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_revocation_timestamp_digest="",
                remote_source_revocation_timestamp_signature_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_revocation_timestamp_signature_digest="",
            )
            normalized_metadata["remote_metadata_bound"] = True
            return normalized_metadata

        normalized_review_authority_ref = (
            remote_review_authority_ref.strip()
            or PARALLEL_CODEX_DEFAULT_REMOTE_REVIEW_AUTHORITY_REF
        )
        normalized_review_authority_digest = remote_review_authority_digest.strip()
        if not _is_sha256(normalized_review_authority_digest):
            normalized_review_authority_digest = self._remote_review_authority_digest(
                normalized_review_authority_ref,
            )
        normalized_policy_ref = (
            accepted_source_policy_ref.strip()
            or PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF
        )
        normalized_policy_digest = accepted_source_policy_digest.strip()
        if not _is_sha256(normalized_policy_digest):
            normalized_policy_digest = self._accepted_source_policy_digest()
        normalized_revocation_ref = (
            remote_source_revocation_ref.strip()
            or PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_REF
        )
        normalized_revocation_status = (
            remote_source_revocation_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS
        )
        remote_source_key = sha256_text(
            canonical_json(
                {
                    "remote_branch_ref": remote_branch_ref.strip(),
                    "remote_pr_ref": remote_pr_ref.strip(),
                    "revocation_ref": normalized_revocation_ref,
                }
            )
        )[:16]
        normalized_checked_at_ref = (
            remote_source_revocation_checked_at_ref.strip()
            or (
                f"{PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_FRESHNESS_REF}"
                f"/checked-at/{remote_source_key}"
            )
        )
        normalized_freshness_window_seconds = _coerce_int(
            remote_source_revocation_freshness_window_seconds,
            PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS,
        )
        if normalized_freshness_window_seconds <= 0:
            normalized_freshness_window_seconds = (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_MAX_FRESHNESS_WINDOW_SECONDS
            )
        normalized_expires_at_ref = (
            remote_source_revocation_expires_at_ref.strip()
            or (
                f"{PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_FRESHNESS_REF}"
                f"/expires-at/{remote_source_key}"
            )
        )
        normalized_timestamp_ref = (
            remote_source_revocation_timestamp_ref.strip()
            or (
                f"{PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REF}"
                f"/{remote_source_key}"
            )
        )
        normalized_timestamp_status = (
            remote_source_revocation_timestamp_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS
        )
        normalized_timestamp_digest = remote_source_revocation_timestamp_digest.strip()
        if not _is_sha256(normalized_timestamp_digest):
            normalized_timestamp_digest = (
                self._remote_source_revocation_timestamp_digest(
                    remote_source_revocation_timestamp_ref=normalized_timestamp_ref,
                    remote_source_revocation_timestamp_status=(
                        normalized_timestamp_status
                    ),
                    remote_source_revocation_checked_at_ref=normalized_checked_at_ref,
                    remote_source_revocation_expires_at_ref=normalized_expires_at_ref,
                )
            )
        normalized_timestamp_signature_digest = (
            remote_source_revocation_timestamp_signature_digest.strip()
        )
        if not _is_sha256(normalized_timestamp_signature_digest):
            normalized_timestamp_signature_digest = (
                self._remote_source_revocation_timestamp_signature_digest(
                    remote_branch_ref=remote_branch_ref.strip(),
                    remote_pr_ref=remote_pr_ref.strip(),
                    remote_source_revocation_timestamp_ref=normalized_timestamp_ref,
                    remote_source_revocation_timestamp_digest=(
                        normalized_timestamp_digest
                    ),
                )
            )
        normalized_freshness_status = (
            remote_source_revocation_freshness_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS
        )
        normalized_freshness_digest = (
            remote_source_revocation_freshness_digest.strip()
        )
        if not _is_sha256(normalized_freshness_digest):
            normalized_freshness_digest = (
                self._remote_source_revocation_freshness_digest(
                    remote_source_revocation_checked_at_ref=normalized_checked_at_ref,
                    remote_source_revocation_freshness_window_seconds=(
                        normalized_freshness_window_seconds
                    ),
                    remote_source_revocation_expires_at_ref=normalized_expires_at_ref,
                    remote_source_revocation_freshness_status=(
                        normalized_freshness_status
                    ),
                    remote_source_revocation_timestamp_signature_digest=(
                        normalized_timestamp_signature_digest
                    ),
                )
            )
        normalized_revocation_digest = remote_source_revocation_digest.strip()
        if not _is_sha256(normalized_revocation_digest):
            normalized_revocation_digest = self._remote_source_revocation_digest(
                remote_branch_ref=remote_branch_ref.strip(),
                remote_pr_ref=remote_pr_ref.strip(),
                accepted_source_policy_ref=normalized_policy_ref,
                accepted_source_policy_digest=normalized_policy_digest,
                remote_source_revocation_ref=normalized_revocation_ref,
                remote_source_revocation_status=normalized_revocation_status,
                remote_source_revocation_freshness_digest=normalized_freshness_digest,
            )
        expected_metadata_digest = self._remote_metadata_digest(
            source_system=source_system,
            remote_metadata_profile=PARALLEL_CODEX_REMOTE_METADATA_PROFILE,
            remote_branch_ref=remote_branch_ref.strip(),
            remote_pr_ref=remote_pr_ref.strip(),
            remote_review_authority_ref=normalized_review_authority_ref,
            remote_review_authority_digest=normalized_review_authority_digest,
            accepted_source_policy_ref=normalized_policy_ref,
            accepted_source_policy_digest=normalized_policy_digest,
            remote_source_revocation_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
            ),
            remote_source_revocation_ref=normalized_revocation_ref,
            remote_source_revocation_status=normalized_revocation_status,
            remote_source_revocation_digest=normalized_revocation_digest,
            remote_source_revocation_freshness_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
            ),
            remote_source_revocation_checked_at_ref=normalized_checked_at_ref,
            remote_source_revocation_freshness_window_seconds=(
                normalized_freshness_window_seconds
            ),
            remote_source_revocation_expires_at_ref=normalized_expires_at_ref,
            remote_source_revocation_freshness_status=normalized_freshness_status,
            remote_source_revocation_freshness_digest=normalized_freshness_digest,
            remote_source_revocation_timestamp_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
            ),
            remote_source_revocation_timestamp_ref=normalized_timestamp_ref,
            remote_source_revocation_timestamp_status=normalized_timestamp_status,
            remote_source_revocation_timestamp_digest=normalized_timestamp_digest,
            remote_source_revocation_timestamp_signature_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
            ),
            remote_source_revocation_timestamp_signature_digest=(
                normalized_timestamp_signature_digest
            ),
        )
        normalized_metadata_digest = remote_metadata_digest.strip()
        if not _is_sha256(normalized_metadata_digest):
            normalized_metadata_digest = expected_metadata_digest
        return {
            "remote_metadata_profile": PARALLEL_CODEX_REMOTE_METADATA_PROFILE,
            "remote_branch_ref": remote_branch_ref.strip(),
            "remote_pr_ref": remote_pr_ref.strip(),
            "remote_review_authority_profile": (
                PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE
            ),
            "remote_review_authority_ref": normalized_review_authority_ref,
            "remote_review_authority_digest": normalized_review_authority_digest,
            "accepted_source_policy_ref": normalized_policy_ref,
            "accepted_source_policy_digest": normalized_policy_digest,
            "remote_source_revocation_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_PROFILE
            ),
            "remote_source_revocation_ref": normalized_revocation_ref,
            "remote_source_revocation_status": normalized_revocation_status,
            "remote_source_revocation_digest": normalized_revocation_digest,
            "remote_source_revocation_freshness_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESHNESS_PROFILE
            ),
            "remote_source_revocation_checked_at_ref": normalized_checked_at_ref,
            "remote_source_revocation_freshness_window_seconds": (
                normalized_freshness_window_seconds
            ),
            "remote_source_revocation_expires_at_ref": normalized_expires_at_ref,
            "remote_source_revocation_freshness_status": normalized_freshness_status,
            "remote_source_revocation_freshness_digest": normalized_freshness_digest,
            "remote_source_revocation_timestamp_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_PROFILE
            ),
            "remote_source_revocation_timestamp_ref": normalized_timestamp_ref,
            "remote_source_revocation_timestamp_status": normalized_timestamp_status,
            "remote_source_revocation_timestamp_digest": normalized_timestamp_digest,
            "remote_source_revocation_timestamp_signature_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNATURE_PROFILE
            ),
            "remote_source_revocation_timestamp_signature_digest": (
                normalized_timestamp_signature_digest
            ),
            "remote_metadata_digest": normalized_metadata_digest,
            "remote_metadata_bound": (
                normalized_metadata_digest == expected_metadata_digest
            ),
        }

    @staticmethod
    def _upstream_binding_digest(
        *,
        source_system: str,
        upstream_receipt_ref: str,
        upstream_receipt_digest: str,
        upstream_patch_candidate_receipt_refs: Sequence[str],
        upstream_patch_candidate_receipt_digests: Sequence[str],
        changed_files: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "source_system": source_system,
                    "upstream_receipt_ref": upstream_receipt_ref,
                    "upstream_receipt_digest": upstream_receipt_digest,
                    "upstream_patch_candidate_receipt_refs": list(
                        upstream_patch_candidate_receipt_refs,
                    ),
                    "upstream_patch_candidate_receipt_digests": list(
                        upstream_patch_candidate_receipt_digests,
                    ),
                    "changed_files": list(changed_files),
                }
            )
        )

    @staticmethod
    def _yaoyorozu_patch_candidate_receipts(
        dispatch_receipt: Mapping[str, Any],
    ) -> list[Mapping[str, Any]]:
        receipts: list[Mapping[str, Any]] = []
        for result in dispatch_receipt.get("results", []):
            if not isinstance(result, Mapping):
                continue
            report = result.get("report", {})
            if not isinstance(report, Mapping):
                continue
            patch_candidate_receipt = report.get("patch_candidate_receipt", {})
            if isinstance(patch_candidate_receipt, Mapping):
                receipts.append(patch_candidate_receipt)
        return receipts

    def _changed_files_from_yaoyorozu_dispatch(
        self,
        dispatch_receipt: Mapping[str, Any],
    ) -> list[str]:
        changed_files: list[str] = []
        for receipt in self._yaoyorozu_patch_candidate_receipts(dispatch_receipt):
            candidates = receipt.get("patch_candidates", [])
            if not isinstance(candidates, list):
                continue
            for candidate in candidates:
                if not isinstance(candidate, Mapping):
                    continue
                target_path = str(candidate.get("target_path", "")).strip()
                if not target_path:
                    patch_descriptor = candidate.get("patch_descriptor", {})
                    if isinstance(patch_descriptor, Mapping):
                        target_path = str(
                            patch_descriptor.get("target_path", ""),
                        ).strip()
                if target_path:
                    changed_files.append(target_path)
        return _dedupe_strings(changed_files)

    def _ownership_scope_for_changed_files(
        self,
        changed_files: Sequence[str],
    ) -> list[str]:
        scopes: list[str] = []
        for path in changed_files:
            for prefix in self._policy.allowed_workspace_prefixes:
                if _is_under_prefix(path, [prefix]):
                    scopes.append(prefix)
                    break
        return _dedupe_strings(scopes)

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
