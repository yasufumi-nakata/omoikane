"""Parallel Codex worker result ingestion receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence

from ..common import canonical_json, new_id, sha256_text, utc_now_iso


PARALLEL_CODEX_WORKER_RESULT_PROFILE = "parallel-codex-worker-result-ingestion-v1"
PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE = (
    "parallel-codex-integration-batch-arbitration-v1"
)
PARALLEL_CODEX_INTEGRATION_BATCH_ORDERING_PROFILE = (
    "receipt-digest-then-ref-deterministic-v1"
)
PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE = (
    "disjoint-changed-file-conflict-arbitration-v1"
)
PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE = (
    "blocked-receipt-quarantine-manifest-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_PROFILE = (
    "parallel-codex-integration-execution-plan-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE = (
    "ordered-receipt-apply-plan-digest-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE = (
    "pre-apply-dry-run-check-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE = (
    "command-bound-git-apply-check-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE = (
    "repo-local-patch-artifact-binding-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE = (
    "repo-local-patch-file"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE = (
    "repo-local-patch-artifact-cleanup-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_PROFILE = (
    "post-apply-required-verification-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE = (
    "post-apply-verification-apply-context-binding-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE = (
    "main-checkout-mutation-attestation-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE = (
    "digest-bound-checkout-mutation-event-v1"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_SOURCE = (
    "reference-runtime-checkout-mutation-attestation"
)
PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE = (
    "main-checkout-commit-finalization-gate-v1"
)
PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE = (
    "origin-main-post-commit-publication-v1"
)
PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE = (
    "command-bound-git-push-origin-main-v1"
)
PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE = (
    "command-bound-git-ls-remote-origin-main-v1"
)
PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE = (
    "ls-remote-head-ref-output-binding-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE = (
    "protected-branch-provider-policy-receipt-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESHNESS_PROFILE = (
    "protected-branch-provider-policy-freshness-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_PROFILE = (
    "protected-branch-provider-policy-signed-timestamp-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNATURE_PROFILE = (
    "protected-branch-provider-policy-timestamp-signature-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAY_PROFILE = (
    "protected-branch-provider-policy-timestamp-replay-guard-v1"
)
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE = (
    "post-push-provider-status-check-suite-v1"
)
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_RUN_PROFILE = (
    "post-push-provider-status-check-run-v1"
)
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESHNESS_PROFILE = (
    "post-push-provider-status-check-suite-freshness-v1"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS = "protected"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS = "fresh"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_EXPIRED_STATUS = "expired"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS = (
    "signed-current"
)
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_STALE_STATUS = "stale"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_INVALID_STATUS = "invalid"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS = "unique"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAYED_STATUS = "replayed"
PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS = 900
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_PROVIDER = "github"
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS = "completed"
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION = "success"
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS = "fresh"
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_EXPIRED_STATUS = "expired"
PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_UNKNOWN_STATUS = "unknown"
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
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE = (
    "remote-source-revocation-timestamp-replay-guard-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE = (
    "remote-source-content-identity-binding-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE = (
    "remote-source-main-ancestry-binding-v1"
)
PARALLEL_CODEX_WORKSPACE_MARKER_HYGIENE_PROFILE = (
    "workspace-enacted-marker-hygiene-v1"
)
PARALLEL_CODEX_WORKSPACE_MARKER_CLASSIFIER_PROFILE = (
    "repo-local-workspace-marker-diff-classifier-v1"
)
PARALLEL_CODEX_WORKSPACE_MARKER_DIFF_LINE_EVIDENCE_PROFILE = (
    "repo-local-diff-line-classifier-v1"
)
PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE = (
    "structured-patch-segment-manifest-v1"
)
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_OK_STATUS = "current-not-revoked"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS = "not-applicable"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_FRESH_STATUS = "fresh"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_EXPIRED_STATUS = "expired"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_SIGNED_STATUS = "signed-current"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_STALE_STATUS = "stale"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_INVALID_STATUS = "invalid"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS = "unique"
PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAYED_STATUS = "replayed"
PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS = "bound"
PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_MISMATCH_STATUS = "mismatch"
PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS = "ancestor-bound"
PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_UNRELATED_STATUS = "unrelated"
PARALLEL_CODEX_WORKSPACE_MARKER_CLEAN_STATUS = "clean"
PARALLEL_CODEX_WORKSPACE_MARKER_REVIEWED_STATUS = "marker-only-reviewed"
PARALLEL_CODEX_WORKSPACE_MARKER_BLOCKED_STATUS = "marker-only-blocked"
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
PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_TIMESTAMP_NONCE_REF = (
    "nonce://parallel-codex/remote-source-revocation/provider-clock/v1"
)
PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_CONTENT_REF = (
    "content://parallel-codex/remote-branch-pr/content-identity/v1"
)
PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER = "github"
PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_REF = (
    "provider://github/protected-branch/origin-main/v1"
)
PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_CHECKED_AT_REF = (
    "provider://github/protected-branch/origin-main/checked-at/v1"
)
PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_REF = (
    "timestamp://github/protected-branch/origin-main/provider-clock/v1"
)
PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_NONCE_REF = (
    "nonce://github/protected-branch/origin-main/provider-clock/v1"
)
PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_REF = (
    "checks://github/omoikane/refs/heads/main"
)
PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_CHECKED_AT_REF = (
    "checks://github/omoikane/refs/heads/main/checked-at/v1"
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
            "integration_batch_profile": PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE,
            "integration_batch_ordering_profile": (
                PARALLEL_CODEX_INTEGRATION_BATCH_ORDERING_PROFILE
            ),
            "integration_batch_conflict_arbitration_profile": (
                PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE
            ),
            "integration_batch_quarantine_profile": (
                PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE
            ),
            "integration_execution_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PROFILE
            ),
            "integration_execution_apply_plan_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE
            ),
            "integration_execution_dry_run_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE
            ),
            "integration_execution_dry_run_command_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE
            ),
            "integration_execution_patch_artifact_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
            ),
            "integration_execution_patch_artifact_source": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
            ),
            "integration_execution_patch_artifact_cleanup_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE
            ),
            "integration_execution_post_verify_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_PROFILE
            ),
            "integration_execution_post_verify_context_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE
            ),
            "integration_execution_checkout_mutation_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE
            ),
            "integration_execution_checkout_mutation_event_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE
            ),
            "integration_execution_commit_finalization_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE
            ),
            "post_commit_publication_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE
            ),
            "post_commit_publication_push_command_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
            ),
            "post_commit_publication_remote_verify_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
            ),
            "post_commit_publication_protected_branch_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
            ),
            "post_commit_publication_protected_branch_freshness_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESHNESS_PROFILE
            ),
            "post_commit_publication_protected_branch_timestamp_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_PROFILE
            ),
            "post_commit_publication_protected_branch_timestamp_replay_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAY_PROFILE
            ),
            "post_commit_publication_status_check_suite_profile": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE
            ),
            "post_commit_publication_status_check_run_profile": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_RUN_PROFILE
            ),
            "post_commit_publication_status_check_freshness_profile": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESHNESS_PROFILE
            ),
            "post_commit_publication_protected_branch_required_status": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS
            ),
            "post_commit_publication_protected_branch_required_freshness_status": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS
            ),
            "post_commit_publication_protected_branch_required_timestamp_status": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS
            ),
            "post_commit_publication_protected_branch_required_timestamp_replay_status": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS
            ),
            "post_commit_publication_protected_branch_max_freshness_window_seconds": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
            ),
            "post_commit_publication_status_check_required_status": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS
            ),
            "post_commit_publication_status_check_required_conclusion": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION
            ),
            "post_commit_publication_status_check_required_freshness_status": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS
            ),
            "post_commit_publication_status_check_max_freshness_window_seconds": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
            ),
            "default_protected_branch_provider": (
                PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER
            ),
            "default_protected_branch_policy_ref": (
                PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_REF
            ),
            "default_protected_branch_policy_checked_at_ref": (
                PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_CHECKED_AT_REF
            ),
            "default_protected_branch_policy_timestamp_ref": (
                PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_REF
            ),
            "default_protected_branch_policy_timestamp_nonce_ref": (
                PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_NONCE_REF
            ),
            "default_status_check_suite_ref": (
                PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_REF
            ),
            "default_status_check_suite_checked_at_ref": (
                PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_CHECKED_AT_REF
            ),
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
            "workspace_marker_hygiene_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_HYGIENE_PROFILE
            ),
            "workspace_marker_classifier_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_CLASSIFIER_PROFILE
            ),
            "workspace_marker_diff_line_evidence_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_DIFF_LINE_EVIDENCE_PROFILE
            ),
            "workspace_marker_patch_segment_evidence_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE
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
            "remote_source_revocation_timestamp_replay_guard_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
            ),
            "remote_source_revocation_timestamp_replay_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS
            ),
            "remote_source_content_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE
            ),
            "remote_source_content_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS
            ),
            "remote_source_ancestry_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
            ),
            "remote_source_ancestry_required_status": (
                PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS
            ),
            "remote_review_authority_profile": (
                PARALLEL_CODEX_REMOTE_REVIEW_AUTHORITY_PROFILE
            ),
            "accepted_source_policy_ref": PARALLEL_CODEX_ACCEPTED_SOURCE_POLICY_REF,
            "raw_patch_payload_stored": False,
            "raw_upstream_payload_stored": False,
            "raw_worker_identity_payload_stored": False,
            "raw_workspace_marker_payload_stored": False,
            "raw_remote_metadata_payload_stored": False,
            "raw_remote_revocation_payload_stored": False,
            "raw_remote_revocation_freshness_payload_stored": False,
            "raw_remote_revocation_timestamp_payload_stored": False,
            "raw_remote_revocation_timestamp_replay_guard_payload_stored": False,
            "raw_remote_source_content_payload_stored": False,
            "raw_remote_source_ancestry_payload_stored": False,
            "raw_worker_receipt_payload_stored": False,
            "raw_conflict_payload_stored": False,
            "raw_batch_payload_stored": False,
            "raw_apply_plan_payload_stored": False,
            "raw_pre_apply_dry_run_payload_stored": False,
            "raw_patch_artifact_cleanup_payload_stored": False,
            "raw_checkout_mutation_payload_stored": False,
            "raw_commit_finalization_payload_stored": False,
            "raw_post_commit_publication_payload_stored": False,
            "raw_push_stdout_stored": False,
            "raw_push_stderr_stored": False,
            "raw_remote_verification_stdout_stored": False,
            "raw_remote_verification_stderr_stored": False,
            "raw_protected_branch_provider_payload_stored": False,
            "raw_protected_branch_policy_freshness_payload_stored": False,
            "raw_protected_branch_provider_timestamp_payload_stored": False,
            "raw_protected_branch_provider_timestamp_replay_guard_payload_stored": (
                False
            ),
            "raw_status_check_provider_payload_stored": False,
            "raw_status_check_suite_freshness_payload_stored": False,
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
        workspace_marker_only_changed_files: Sequence[str] = (),
        workspace_diff_by_file: Mapping[str, str] | None = None,
        workspace_patch_segments_by_file: (
            Mapping[str, Sequence[Mapping[str, Any]]] | None
        ) = None,
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
        remote_source_revocation_timestamp_nonce_ref: str = "",
        remote_source_revocation_timestamp_previous_nonce_digest: str = "",
        remote_source_revocation_timestamp_replay_status: str = "",
        remote_source_revocation_timestamp_replay_guard_digest: str = "",
        remote_source_content_ref: str = "",
        remote_source_content_status: str = "",
        remote_source_head_commit: str = "",
        remote_source_tree_digest: str = "",
        remote_source_diff_digest: str = "",
        remote_source_content_digest: str = "",
        remote_source_base_commit: str = "",
        remote_source_merge_base_commit: str = "",
        remote_source_ancestry_status: str = "",
        remote_source_ancestry_digest: str = "",
        remote_metadata_digest: str = "",
    ) -> Dict[str, Any]:
        normalized_source_system = source_system.strip() or "direct-worker-result"
        normalized_scope = _dedupe_strings(ownership_scope)
        normalized_files = _dedupe_strings(changed_files)
        workspace_marker_diff_summaries = self.classify_workspace_marker_diff_summaries(
            changed_files=normalized_files,
            workspace_diff_by_file=workspace_diff_by_file or {},
            workspace_patch_segments_by_file=workspace_patch_segments_by_file or {},
        )
        classifier_marker_files = self._workspace_marker_classifier_marker_files(
            workspace_marker_diff_summaries,
        )
        normalized_workspace_marker_files = _dedupe_strings(
            [
                *workspace_marker_only_changed_files,
                *classifier_marker_files,
            ],
        )
        workspace_marker_classifier_digest = (
            self._workspace_marker_classifier_digest(
                workspace_marker_diff_summaries=workspace_marker_diff_summaries,
                workspace_marker_only_changed_files=(
                    normalized_workspace_marker_files
                ),
            )
        )
        workspace_marker_hygiene_status = self._workspace_marker_hygiene_status(
            changed_files=normalized_files,
            workspace_marker_only_changed_files=normalized_workspace_marker_files,
        )
        workspace_marker_hygiene_digest = self._workspace_marker_hygiene_digest(
            changed_files=normalized_files,
            workspace_marker_only_changed_files=normalized_workspace_marker_files,
            workspace_marker_hygiene_status=workspace_marker_hygiene_status,
            workspace_marker_classifier_digest=workspace_marker_classifier_digest,
        )
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
            changed_files=normalized_files,
            patch_digest=normalized_patch_digest,
            workspace_marker_hygiene_digest=workspace_marker_hygiene_digest,
            worker_base_commit=worker_base_commit,
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
            remote_source_revocation_timestamp_nonce_ref=(
                remote_source_revocation_timestamp_nonce_ref
            ),
            remote_source_revocation_timestamp_previous_nonce_digest=(
                remote_source_revocation_timestamp_previous_nonce_digest
            ),
            remote_source_revocation_timestamp_replay_status=(
                remote_source_revocation_timestamp_replay_status
            ),
            remote_source_revocation_timestamp_replay_guard_digest=(
                remote_source_revocation_timestamp_replay_guard_digest
            ),
            remote_source_content_ref=remote_source_content_ref,
            remote_source_content_status=remote_source_content_status,
            remote_source_head_commit=remote_source_head_commit,
            remote_source_tree_digest=remote_source_tree_digest,
            remote_source_diff_digest=remote_source_diff_digest,
            remote_source_content_digest=remote_source_content_digest,
            remote_source_base_commit=remote_source_base_commit,
            remote_source_merge_base_commit=remote_source_merge_base_commit,
            remote_source_ancestry_status=remote_source_ancestry_status,
            remote_source_ancestry_digest=remote_source_ancestry_digest,
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
            "workspace_marker_hygiene_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_HYGIENE_PROFILE
            ),
            "workspace_marker_classifier_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_CLASSIFIER_PROFILE
            ),
            "workspace_marker_diff_summaries": workspace_marker_diff_summaries,
            "workspace_marker_diff_summary_count": len(
                workspace_marker_diff_summaries,
            ),
            "workspace_marker_classifier_digest": (
                workspace_marker_classifier_digest
            ),
            "workspace_marker_only_changed_files": normalized_workspace_marker_files,
            "workspace_marker_only_change_count": len(
                normalized_workspace_marker_files,
            ),
            "workspace_marker_hygiene_status": workspace_marker_hygiene_status,
            "workspace_marker_hygiene_digest": workspace_marker_hygiene_digest,
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
            "raw_workspace_marker_payload_stored": False,
            "raw_remote_metadata_payload_stored": False,
            "raw_remote_revocation_payload_stored": False,
            "raw_remote_revocation_freshness_payload_stored": False,
            "raw_remote_revocation_timestamp_payload_stored": False,
            "raw_remote_revocation_timestamp_replay_guard_payload_stored": False,
            "raw_remote_source_content_payload_stored": False,
            "raw_remote_source_ancestry_payload_stored": False,
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

    def plan_integration_batch(
        self,
        *,
        receipts: Sequence[Mapping[str, Any]],
        main_checkout_head: str,
        verification_results: Sequence[Mapping[str, Any]],
        result_summary: str,
    ) -> Dict[str, Any]:
        normalized_verifications = self._normalize_verification_results(
            verification_results,
        )
        normalized_receipts = self._normalize_batch_receipts(
            receipts=receipts,
            main_checkout_head=main_checkout_head,
        )
        accept_ready_receipts = [
            receipt
            for receipt in normalized_receipts
            if receipt["accept_ready_for_batch"]
        ]
        quarantined_receipts = [
            receipt
            for receipt in normalized_receipts
            if not receipt["accept_ready_for_batch"]
        ]
        ordered_receipts = sorted(
            accept_ready_receipts,
            key=lambda receipt: (receipt["receipt_digest"], receipt["receipt_ref"]),
        )
        changed_file_owners = self._integration_batch_changed_file_owners(
            ordered_receipts,
        )
        changed_file_conflicts = self._integration_batch_changed_file_conflicts(
            changed_file_owners,
        )
        ordered_refs = [receipt["receipt_ref"] for receipt in ordered_receipts]
        ordered_digests = [receipt["receipt_digest"] for receipt in ordered_receipts]
        input_refs = [receipt["receipt_ref"] for receipt in normalized_receipts]
        input_digests = [receipt["receipt_digest"] for receipt in normalized_receipts]
        quarantined_refs = [
            receipt["receipt_ref"] for receipt in quarantined_receipts
        ]
        quarantined_digests = [
            receipt["receipt_digest"] for receipt in quarantined_receipts
        ]
        batch_main_head_status = (
            "consistent"
            if all(
                receipt["main_checkout_head"] == main_checkout_head
                for receipt in ordered_receipts
            )
            else "mismatch"
        )
        mismatched_main_head_receipts = [
            receipt
            for receipt in normalized_receipts
            if receipt["main_checkout_head"]
            and receipt["main_checkout_head"] != main_checkout_head
        ]
        batch_receipt = {
            "kind": "parallel_codex_integration_batch_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("parallel-codex-batch"),
            "generated_at": utc_now_iso(),
            "profile_id": PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE,
            "integration_policy_profile": self._policy.profile_id,
            "reference_runbook_ref": self._policy.reference_runbook_ref,
            "main_checkout_head": main_checkout_head,
            "batch_ordering_profile": PARALLEL_CODEX_INTEGRATION_BATCH_ORDERING_PROFILE,
            "conflict_arbitration_profile": (
                PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE
            ),
            "source_receipt_count": len(normalized_receipts),
            "input_receipt_refs": input_refs,
            "input_receipt_digests": input_digests,
            "input_receipt_set_digest": self._integration_batch_receipt_set_digest(
                input_receipt_refs=input_refs,
                input_receipt_digests=input_digests,
            ),
            "accept_ready_receipt_refs": ordered_refs,
            "accept_ready_receipt_digests": ordered_digests,
            "quarantined_receipt_refs": quarantined_refs,
            "quarantined_receipt_digests": quarantined_digests,
            "quarantined_receipt_count": len(quarantined_receipts),
            "blocked_receipts_quarantined": True,
            "quarantine_profile": (
                PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE
            ),
            "quarantined_receipt_set_digest": (
                self._integration_batch_quarantined_receipt_digest(
                    quarantined_receipt_refs=quarantined_refs,
                    quarantined_receipt_digests=quarantined_digests,
                )
            ),
            "ordered_integration_receipt_refs": ordered_refs,
            "ordered_integration_receipt_digests": ordered_digests,
            "ordered_integration_digest": (
                self._integration_batch_ordered_receipt_digest(
                    ordered_receipt_refs=ordered_refs,
                    ordered_receipt_digests=ordered_digests,
                )
            ),
            "changed_file_owners": changed_file_owners,
            "changed_file_owner_manifest_digest": (
                self._integration_batch_changed_file_owner_manifest_digest(
                    changed_file_owners=changed_file_owners,
                )
            ),
            "changed_file_conflicts": changed_file_conflicts,
            "conflict_count": len(changed_file_conflicts),
            "conflict_digest": self._integration_batch_conflict_digest(
                changed_file_conflicts=changed_file_conflicts,
            ),
            "batch_main_head_status": batch_main_head_status,
            "mismatched_main_head_receipt_refs": [
                receipt["receipt_ref"] for receipt in mismatched_main_head_receipts
            ],
            "mismatched_main_head_receipt_digests": [
                receipt["receipt_digest"] for receipt in mismatched_main_head_receipts
            ],
            "verification_results": normalized_verifications,
            "verification_command_count": len(normalized_verifications),
            "verification_manifest_digest": self._verification_manifest_digest(
                normalized_verifications,
            ),
            "required_verifications_passed": self._required_verifications_passed(
                normalized_verifications,
            ),
            "blocking_reasons": [],
            "batch_decision": "blocked",
            "result_summary": result_summary,
            "raw_worker_receipt_payload_stored": False,
            "raw_conflict_payload_stored": False,
            "raw_verification_payload_stored": False,
            "receipt_digest": "",
        }
        batch_receipt["receipt_ref"] = (
            f"receipt://parallel-codex/{batch_receipt['receipt_id']}"
        )
        batch_receipt["blocking_reasons"] = self._derive_batch_blocking_reasons(
            batch_receipt,
        )
        batch_receipt["batch_decision"] = (
            "blocked"
            if batch_receipt["blocking_reasons"]
            else "integration-ready"
        )
        batch_receipt["receipt_digest"] = self._receipt_digest(batch_receipt)
        return batch_receipt

    def validate_integration_batch_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: list[str] = []
        input_refs = list(receipt.get("input_receipt_refs", []))
        input_digests = list(receipt.get("input_receipt_digests", []))
        ordered_refs = list(receipt.get("ordered_integration_receipt_refs", []))
        ordered_digests = list(receipt.get("ordered_integration_receipt_digests", []))
        changed_file_owners = list(receipt.get("changed_file_owners", []))
        changed_file_conflicts = list(receipt.get("changed_file_conflicts", []))
        verification_results = list(receipt.get("verification_results", []))
        expected_blocking_reasons = self._derive_batch_blocking_reasons(receipt)
        expected_decision = (
            "blocked" if expected_blocking_reasons else "integration-ready"
        )
        input_receipt_set_digest_bound = (
            receipt.get("input_receipt_set_digest")
            == self._integration_batch_receipt_set_digest(
                input_receipt_refs=input_refs,
                input_receipt_digests=input_digests,
            )
        )
        ordered_integration_digest_bound = (
            receipt.get("ordered_integration_digest")
            == self._integration_batch_ordered_receipt_digest(
                ordered_receipt_refs=ordered_refs,
                ordered_receipt_digests=ordered_digests,
            )
        )
        changed_file_owner_manifest_digest_bound = (
            receipt.get("changed_file_owner_manifest_digest")
            == self._integration_batch_changed_file_owner_manifest_digest(
                changed_file_owners=changed_file_owners,
            )
        )
        quarantined_receipt_set_digest_bound = (
            receipt.get("quarantined_receipt_set_digest")
            == self._integration_batch_quarantined_receipt_digest(
                quarantined_receipt_refs=list(
                    receipt.get("quarantined_receipt_refs", []),
                ),
                quarantined_receipt_digests=list(
                    receipt.get("quarantined_receipt_digests", []),
                ),
            )
        )
        conflict_digest_bound = (
            receipt.get("conflict_digest")
            == self._integration_batch_conflict_digest(
                changed_file_conflicts=changed_file_conflicts,
            )
        )
        verification_manifest_digest_bound = (
            receipt.get("verification_manifest_digest")
            == self._verification_manifest_digest(verification_results)
        )
        receipt_digest_bound = receipt.get("receipt_digest") == self._receipt_digest(
            receipt,
        )

        if receipt.get("kind") != "parallel_codex_integration_batch_receipt":
            errors.append("kind must be parallel_codex_integration_batch_receipt")
        if receipt.get("profile_id") != PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE:
            errors.append("profile_id mismatch")
        if receipt.get("integration_policy_profile") != self._policy.profile_id:
            errors.append("integration_policy_profile mismatch")
        if receipt.get("reference_runbook_ref") != self._policy.reference_runbook_ref:
            errors.append("reference_runbook_ref mismatch")
        if (
            receipt.get("batch_ordering_profile")
            != PARALLEL_CODEX_INTEGRATION_BATCH_ORDERING_PROFILE
        ):
            errors.append("batch_ordering_profile mismatch")
        if (
            receipt.get("conflict_arbitration_profile")
            != PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE
        ):
            errors.append("conflict_arbitration_profile mismatch")
        if (
            receipt.get("quarantine_profile")
            != PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE
        ):
            errors.append("quarantine_profile mismatch")
        if receipt.get("source_receipt_count") != len(input_refs):
            errors.append("source_receipt_count mismatch")
        if len(input_refs) != len(input_digests):
            errors.append("input receipt refs and digests must have equal length")
        if receipt.get("quarantined_receipt_count") != len(
            receipt.get("quarantined_receipt_refs", []),
        ):
            errors.append("quarantined_receipt_count mismatch")
        if len(receipt.get("quarantined_receipt_refs", [])) != len(
            receipt.get("quarantined_receipt_digests", []),
        ):
            errors.append("quarantined receipt refs and digests must have equal length")
        if receipt.get("conflict_count") != len(changed_file_conflicts):
            errors.append("conflict_count mismatch")
        if receipt.get("verification_command_count") != len(verification_results):
            errors.append("verification_command_count mismatch")
        if not input_receipt_set_digest_bound:
            errors.append("input_receipt_set_digest mismatch")
        if not ordered_integration_digest_bound:
            errors.append("ordered_integration_digest mismatch")
        if not changed_file_owner_manifest_digest_bound:
            errors.append("changed_file_owner_manifest_digest mismatch")
        if not quarantined_receipt_set_digest_bound:
            errors.append("quarantined_receipt_set_digest mismatch")
        if not conflict_digest_bound:
            errors.append("conflict_digest mismatch")
        if not verification_manifest_digest_bound:
            errors.append("verification_manifest_digest mismatch")
        if receipt.get("blocking_reasons") != expected_blocking_reasons:
            errors.append("blocking_reasons mismatch")
        if receipt.get("batch_decision") != expected_decision:
            errors.append("batch_decision mismatch")
        if not receipt_digest_bound:
            errors.append("receipt_digest mismatch")
        if receipt.get("raw_worker_receipt_payload_stored") is not False:
            errors.append("raw_worker_receipt_payload_stored must be false")
        if receipt.get("raw_conflict_payload_stored") is not False:
            errors.append("raw_conflict_payload_stored must be false")
        if receipt.get("raw_verification_payload_stored") is not False:
            errors.append("raw_verification_payload_stored must be false")
        return {
            "ok": not errors,
            "ready_for_integration": (
                receipt.get("batch_decision") == "integration-ready"
                and not expected_blocking_reasons
            ),
            "errors": errors,
            "input_receipt_set_digest_bound": input_receipt_set_digest_bound,
            "ordered_integration_digest_bound": ordered_integration_digest_bound,
            "changed_file_owner_manifest_digest_bound": (
                changed_file_owner_manifest_digest_bound
            ),
            "quarantined_receipt_set_digest_bound": (
                quarantined_receipt_set_digest_bound
            ),
            "conflict_digest_bound": conflict_digest_bound,
            "verification_manifest_digest_bound": verification_manifest_digest_bound,
            "receipt_digest_bound": receipt_digest_bound,
            "blocked_receipts_quarantined": (
                receipt.get("blocked_receipts_quarantined") is True
            ),
            "conflict_free": receipt.get("conflict_count") == 0,
            "conflict_blocked": (
                receipt.get("conflict_count", 0) > 0
                and receipt.get("batch_decision") == "blocked"
            ),
            "required_verifications_passed": self._required_verifications_passed(
                verification_results,
            ),
            "raw_worker_receipt_payload_redacted": (
                receipt.get("raw_worker_receipt_payload_stored") is False
            ),
            "raw_conflict_payload_redacted": (
                receipt.get("raw_conflict_payload_stored") is False
            ),
            "raw_verification_payload_redacted": (
                receipt.get("raw_verification_payload_stored") is False
            ),
        }

    def plan_integration_execution(
        self,
        *,
        batch_receipt: Mapping[str, Any],
        current_checkout_head: str,
        pre_apply_dry_run_results: Sequence[Mapping[str, Any]] | None = None,
        post_apply_verification_results: Sequence[Mapping[str, Any]],
        checkout_mutation_attestation: Mapping[str, Any] | None = None,
        patch_artifact_cleanup_receipt: Mapping[str, Any] | None = None,
        result_summary: str,
    ) -> Dict[str, Any]:
        batch_validation = self.validate_integration_batch_receipt(batch_receipt)
        ordered_refs = list(batch_receipt.get("ordered_integration_receipt_refs", []))
        ordered_digests = list(
            batch_receipt.get("ordered_integration_receipt_digests", []),
        )
        changed_file_owners = list(batch_receipt.get("changed_file_owners", []))
        apply_steps = self._integration_execution_apply_steps(
            ordered_receipt_refs=ordered_refs,
            ordered_receipt_digests=ordered_digests,
            changed_file_owners=changed_file_owners,
        )
        normalized_dry_runs = self._normalize_pre_apply_dry_run_results(
            pre_apply_dry_run_results,
            apply_steps=apply_steps,
        )
        normalized_verifications = self._normalize_verification_results(
            post_apply_verification_results,
        )
        apply_plan_digest = self._integration_execution_apply_plan_digest(
            apply_steps=apply_steps,
        )
        patch_artifact_manifest_digest = (
            self._integration_execution_patch_artifact_manifest_digest(
                apply_steps=apply_steps,
            )
        )
        pre_apply_dry_run_manifest_digest = self._pre_apply_dry_run_manifest_digest(
            normalized_dry_runs,
        )
        post_apply_verification_manifest_digest = self._verification_manifest_digest(
            normalized_verifications,
        )
        batch_receipt_digest = str(batch_receipt.get("receipt_digest", "")).strip()
        source_batch_digest_bound = (
            batch_receipt_digest == self._receipt_digest(batch_receipt)
        )
        main_checkout_head = str(batch_receipt.get("main_checkout_head", "")).strip()
        normalized_current_head = current_checkout_head.strip()
        post_apply_verification_context_digest = (
            self._post_apply_verification_context_digest(
                source_batch_receipt_digest=batch_receipt_digest,
                current_checkout_head=normalized_current_head,
                apply_plan_digest=apply_plan_digest,
                patch_artifact_manifest_digest=patch_artifact_manifest_digest,
                pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
                post_apply_verification_manifest_digest=(
                    post_apply_verification_manifest_digest
                ),
            )
        )
        checkout_mutation = self._normalize_checkout_mutation_attestation(
            checkout_mutation_attestation=checkout_mutation_attestation,
            source_batch_receipt_digest=batch_receipt_digest,
            current_checkout_head=normalized_current_head,
            apply_plan_digest=apply_plan_digest,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            post_apply_verification_context_digest=(
                post_apply_verification_context_digest
            ),
            changed_file_owner_manifest_digest=str(
                batch_receipt.get("changed_file_owner_manifest_digest", ""),
            ).strip(),
        )
        repo_local_patch_artifacts_bound = (
            self._integration_execution_repo_local_patch_artifacts_bound(
                apply_steps=apply_steps,
            )
        )
        pre_apply_dry_run_passed = self._pre_apply_dry_run_passed(
            normalized_dry_runs,
            apply_steps=apply_steps,
        )
        post_apply_verification_context_bound = (
            _is_sha256(post_apply_verification_context_digest)
        )
        required_verifications_passed = self._required_verifications_passed(
            normalized_verifications,
        )
        source_batch_ready_for_execution = bool(
            batch_validation["ready_for_integration"],
        )
        current_head_matches_batch = normalized_current_head == main_checkout_head
        patch_artifact_cleanup = self._normalize_patch_artifact_cleanup_receipt(
            patch_artifact_cleanup_receipt=patch_artifact_cleanup_receipt,
            apply_steps=apply_steps,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            checkout_mutation_event_digest=str(
                checkout_mutation.get("checkout_mutation_event_digest", ""),
            ),
            checkout_mutation_post_apply_head=str(
                checkout_mutation.get("checkout_mutation_post_apply_head", ""),
            ),
        )
        patch_artifact_cleanup_verified = bool(
            patch_artifact_cleanup.get("patch_artifact_cleanup_verified", False),
        )
        commit_finalization = self._normalize_commit_finalization_gate(
            source_batch_receipt_digest=batch_receipt_digest,
            current_checkout_head=normalized_current_head,
            apply_plan_digest=apply_plan_digest,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            post_apply_verification_context_digest=(
                post_apply_verification_context_digest
            ),
            checkout_mutation_event_digest=str(
                checkout_mutation.get("checkout_mutation_event_digest", ""),
            ),
            checkout_mutation_post_apply_head=str(
                checkout_mutation.get("checkout_mutation_post_apply_head", ""),
            ),
            patch_artifact_cleanup_digest=str(
                patch_artifact_cleanup.get("patch_artifact_cleanup_digest", ""),
            ),
            patch_artifact_cleanup_verified=patch_artifact_cleanup_verified,
            changed_file_owner_manifest_digest=str(
                batch_receipt.get("changed_file_owner_manifest_digest", ""),
            ).strip(),
            required_verifications_passed=required_verifications_passed,
            source_batch_ready_for_execution=source_batch_ready_for_execution,
            current_head_matches_batch=current_head_matches_batch,
            pre_apply_dry_run_passed=pre_apply_dry_run_passed,
            post_apply_verification_context_bound=(
                post_apply_verification_context_bound
            ),
            checkout_mutation_attested=bool(
                checkout_mutation.get("checkout_mutation_attested", False),
            ),
            repo_local_patch_artifacts_bound=repo_local_patch_artifacts_bound,
        )
        receipt = {
            "kind": "parallel_codex_integration_execution_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("parallel-codex-execution"),
            "generated_at": utc_now_iso(),
            "profile_id": PARALLEL_CODEX_INTEGRATION_EXECUTION_PROFILE,
            "integration_policy_profile": self._policy.profile_id,
            "reference_runbook_ref": self._policy.reference_runbook_ref,
            "source_batch_receipt_ref": str(
                batch_receipt.get("receipt_ref", ""),
            ).strip(),
            "source_batch_receipt_digest": batch_receipt_digest,
            "source_batch_receipt_digest_bound": source_batch_digest_bound,
            "source_batch_decision": str(
                batch_receipt.get("batch_decision", ""),
            ).strip(),
            "source_batch_ready_for_execution": source_batch_ready_for_execution,
            "main_checkout_head": main_checkout_head,
            "current_checkout_head": normalized_current_head,
            "current_head_matches_batch": current_head_matches_batch,
            "ordered_integration_receipt_refs": ordered_refs,
            "ordered_integration_receipt_digests": ordered_digests,
            "ordered_integration_digest": str(
                batch_receipt.get("ordered_integration_digest", ""),
            ).strip(),
            "changed_file_owner_manifest_digest": str(
                batch_receipt.get("changed_file_owner_manifest_digest", ""),
            ).strip(),
            "quarantined_receipt_set_digest": str(
                batch_receipt.get("quarantined_receipt_set_digest", ""),
            ).strip(),
            "conflict_digest": str(batch_receipt.get("conflict_digest", "")).strip(),
            "apply_plan_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE
            ),
            "apply_steps": apply_steps,
            "apply_step_count": len(apply_steps),
            "apply_plan_digest": apply_plan_digest,
            "patch_artifact_binding_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
            ),
            "patch_artifact_manifest_digest": patch_artifact_manifest_digest,
            "repo_local_patch_artifact_count": (
                self._integration_execution_repo_local_patch_artifact_count(
                    apply_steps=apply_steps,
                )
            ),
            "repo_local_patch_artifacts_bound": repo_local_patch_artifacts_bound,
            "pre_apply_dry_run_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE
            ),
            "pre_apply_dry_run_results": normalized_dry_runs,
            "pre_apply_dry_run_result_count": len(normalized_dry_runs),
            "pre_apply_dry_run_manifest_digest": pre_apply_dry_run_manifest_digest,
            "pre_apply_dry_run_passed": pre_apply_dry_run_passed,
            "post_apply_verification_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_PROFILE
            ),
            "post_apply_verification_context_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE
            ),
            "post_apply_verification_results": normalized_verifications,
            "post_apply_verification_command_count": len(normalized_verifications),
            "post_apply_verification_manifest_digest": (
                post_apply_verification_manifest_digest
            ),
            "post_apply_verification_apply_plan_digest_bound": (
                _is_sha256(apply_plan_digest)
            ),
            "post_apply_verification_patch_artifact_manifest_digest_bound": (
                _is_sha256(patch_artifact_manifest_digest)
            ),
            "post_apply_verification_pre_apply_manifest_digest_bound": (
                _is_sha256(pre_apply_dry_run_manifest_digest)
            ),
            "post_apply_verification_context_digest": (
                post_apply_verification_context_digest
            ),
            "post_apply_verification_context_bound": (
                post_apply_verification_context_bound
            ),
            **checkout_mutation,
            **patch_artifact_cleanup,
            **commit_finalization,
            "required_verifications_passed": required_verifications_passed,
            "blocking_reasons": [],
            "execution_decision": "blocked",
            "result_summary": result_summary,
            "raw_batch_payload_stored": False,
            "raw_apply_plan_payload_stored": False,
            "raw_pre_apply_dry_run_payload_stored": False,
            "raw_checkout_mutation_payload_stored": False,
            "raw_patch_artifact_cleanup_payload_stored": False,
            "raw_commit_finalization_payload_stored": False,
            "raw_worker_receipt_payload_stored": False,
            "raw_verification_payload_stored": False,
            "receipt_digest": "",
        }
        receipt["receipt_ref"] = (
            f"receipt://parallel-codex/{receipt['receipt_id']}"
        )
        receipt["blocking_reasons"] = self._derive_execution_blocking_reasons(
            receipt,
        )
        receipt["execution_decision"] = (
            "blocked" if receipt["blocking_reasons"] else "ready-to-apply"
        )
        receipt["receipt_digest"] = self._receipt_digest(receipt)
        return receipt

    def validate_integration_execution_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: list[str] = []
        apply_steps = list(receipt.get("apply_steps", []))
        pre_apply_dry_run_results = list(
            receipt.get("pre_apply_dry_run_results", []),
        )
        verification_results = list(
            receipt.get("post_apply_verification_results", []),
        )
        expected_blocking_reasons = self._derive_execution_blocking_reasons(receipt)
        expected_decision = (
            "blocked" if expected_blocking_reasons else "ready-to-apply"
        )
        apply_plan_digest_bound = (
            receipt.get("apply_plan_digest")
            == self._integration_execution_apply_plan_digest(
                apply_steps=apply_steps,
            )
        )
        patch_artifact_manifest_digest_bound = (
            receipt.get("patch_artifact_manifest_digest")
            == self._integration_execution_patch_artifact_manifest_digest(
                apply_steps=apply_steps,
            )
        )
        repo_local_patch_artifacts_bound = (
            receipt.get("repo_local_patch_artifacts_bound") is True
            and receipt.get("repo_local_patch_artifact_count")
            == self._integration_execution_repo_local_patch_artifact_count(
                apply_steps=apply_steps,
            )
            and self._integration_execution_repo_local_patch_artifacts_bound(
                apply_steps=apply_steps,
            )
        )
        post_apply_verification_manifest_digest_bound = (
            receipt.get("post_apply_verification_manifest_digest")
            == self._verification_manifest_digest(verification_results)
        )
        pre_apply_dry_run_manifest_digest_bound = (
            receipt.get("pre_apply_dry_run_manifest_digest")
            == self._pre_apply_dry_run_manifest_digest(pre_apply_dry_run_results)
        )
        post_apply_verification_apply_plan_digest_bound = (
            receipt.get("post_apply_verification_apply_plan_digest_bound") is True
            and apply_plan_digest_bound
            and _is_sha256(receipt.get("apply_plan_digest"))
        )
        post_apply_verification_patch_artifact_manifest_digest_bound = (
            receipt.get(
                "post_apply_verification_patch_artifact_manifest_digest_bound",
            )
            is True
            and patch_artifact_manifest_digest_bound
            and _is_sha256(receipt.get("patch_artifact_manifest_digest"))
        )
        post_apply_verification_pre_apply_manifest_digest_bound = (
            receipt.get("post_apply_verification_pre_apply_manifest_digest_bound")
            is True
            and pre_apply_dry_run_manifest_digest_bound
            and _is_sha256(receipt.get("pre_apply_dry_run_manifest_digest"))
        )
        post_apply_verification_context_digest_bound = (
            receipt.get("post_apply_verification_context_digest")
            == self._post_apply_verification_context_digest(
                source_batch_receipt_digest=str(
                    receipt.get("source_batch_receipt_digest", ""),
                ),
                current_checkout_head=str(receipt.get("current_checkout_head", "")),
                apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
                patch_artifact_manifest_digest=str(
                    receipt.get("patch_artifact_manifest_digest", ""),
                ),
                pre_apply_dry_run_manifest_digest=str(
                    receipt.get("pre_apply_dry_run_manifest_digest", ""),
                ),
                post_apply_verification_manifest_digest=str(
                    receipt.get("post_apply_verification_manifest_digest", ""),
                ),
            )
        )
        post_apply_verification_context_bound = (
            receipt.get("post_apply_verification_context_bound") is True
            and post_apply_verification_context_digest_bound
            and post_apply_verification_apply_plan_digest_bound
            and post_apply_verification_patch_artifact_manifest_digest_bound
            and post_apply_verification_pre_apply_manifest_digest_bound
            and post_apply_verification_manifest_digest_bound
        )
        checkout_mutation_event_digest_bound = (
            receipt.get("checkout_mutation_event_digest")
            == self._checkout_mutation_event_digest(
                checkout_mutation_source=str(
                    receipt.get("checkout_mutation_source", ""),
                ),
                checkout_mutation_event_ref=str(
                    receipt.get("checkout_mutation_event_ref", ""),
                ),
                source_batch_receipt_digest=str(
                    receipt.get("source_batch_receipt_digest", ""),
                ),
                current_checkout_head=str(receipt.get("current_checkout_head", "")),
                checkout_mutation_pre_apply_head=str(
                    receipt.get("checkout_mutation_pre_apply_head", ""),
                ),
                checkout_mutation_post_apply_head=str(
                    receipt.get("checkout_mutation_post_apply_head", ""),
                ),
                apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
                patch_artifact_manifest_digest=str(
                    receipt.get("patch_artifact_manifest_digest", ""),
                ),
                pre_apply_dry_run_manifest_digest=str(
                    receipt.get("pre_apply_dry_run_manifest_digest", ""),
                ),
                post_apply_verification_context_digest=str(
                    receipt.get("post_apply_verification_context_digest", ""),
                ),
                changed_file_owner_manifest_digest=str(
                    receipt.get("changed_file_owner_manifest_digest", ""),
                ),
            )
        )
        checkout_mutation_heads_bound = (
            receipt.get("checkout_mutation_pre_apply_head")
            == receipt.get("current_checkout_head")
            and _is_commit(receipt.get("checkout_mutation_post_apply_head"))
            and receipt.get("checkout_mutation_post_apply_head")
            != receipt.get("checkout_mutation_pre_apply_head")
        )
        checkout_mutation_context_bound = (
            receipt.get("checkout_mutation_apply_plan_digest_bound") is True
            and apply_plan_digest_bound
            and receipt.get("checkout_mutation_patch_artifact_manifest_digest_bound")
            is True
            and patch_artifact_manifest_digest_bound
            and receipt.get("checkout_mutation_pre_apply_dry_run_manifest_digest_bound")
            is True
            and pre_apply_dry_run_manifest_digest_bound
            and receipt.get(
                "checkout_mutation_post_apply_verification_context_digest_bound",
            )
            is True
            and post_apply_verification_context_digest_bound
            and receipt.get(
                "checkout_mutation_changed_file_owner_manifest_digest_bound",
            )
            is True
            and _is_sha256(receipt.get("changed_file_owner_manifest_digest"))
        )
        checkout_mutation_attested = (
            receipt.get("checkout_mutation_status") == "attested"
            and receipt.get("checkout_mutation_attested") is True
            and checkout_mutation_event_digest_bound
            and checkout_mutation_heads_bound
            and checkout_mutation_context_bound
            and receipt.get("raw_checkout_mutation_payload_stored") is False
        )
        patch_artifact_cleanup_artifact_paths = list(
            receipt.get("patch_artifact_cleanup_artifact_paths", []),
        )
        expected_patch_artifact_cleanup_paths = (
            self._patch_artifact_cleanup_artifact_paths(apply_steps=apply_steps)
        )
        patch_artifact_cleanup_digest_bound = (
            receipt.get("patch_artifact_cleanup_digest")
            == self._patch_artifact_cleanup_digest(
                patch_artifact_cleanup_ref=str(
                    receipt.get("patch_artifact_cleanup_ref", ""),
                ),
                patch_artifact_cleanup_status=str(
                    receipt.get("patch_artifact_cleanup_status", ""),
                ),
                patch_artifact_cleanup_artifact_paths=(
                    patch_artifact_cleanup_artifact_paths
                ),
                patch_artifact_cleanup_artifact_count=_coerce_int(
                    receipt.get("patch_artifact_cleanup_artifact_count"),
                    0,
                ),
                patch_artifact_manifest_digest=str(
                    receipt.get("patch_artifact_manifest_digest", ""),
                ),
                pre_apply_dry_run_manifest_digest=str(
                    receipt.get("pre_apply_dry_run_manifest_digest", ""),
                ),
                checkout_mutation_event_digest=str(
                    receipt.get("checkout_mutation_event_digest", ""),
                ),
                checkout_mutation_post_apply_head=str(
                    receipt.get("checkout_mutation_post_apply_head", ""),
                ),
            )
        )
        patch_artifact_cleanup_artifact_paths_bound = (
            receipt.get("patch_artifact_cleanup_artifact_paths_bound") is True
            and patch_artifact_cleanup_artifact_paths
            == expected_patch_artifact_cleanup_paths
        )
        patch_artifact_cleanup_artifact_count_bound = (
            receipt.get("patch_artifact_cleanup_artifact_count_bound") is True
            and receipt.get("patch_artifact_cleanup_artifact_count")
            == len(expected_patch_artifact_cleanup_paths)
        )
        patch_artifact_cleanup_manifest_digest_bound = (
            receipt.get("patch_artifact_cleanup_manifest_digest_bound") is True
            and patch_artifact_manifest_digest_bound
        )
        patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound = (
            receipt.get(
                "patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound",
            )
            is True
            and pre_apply_dry_run_manifest_digest_bound
        )
        patch_artifact_cleanup_checkout_mutation_event_digest_bound = (
            receipt.get(
                "patch_artifact_cleanup_checkout_mutation_event_digest_bound",
            )
            is True
            and checkout_mutation_event_digest_bound
        )
        patch_artifact_cleanup_post_apply_head_bound = (
            receipt.get("patch_artifact_cleanup_post_apply_head_bound") is True
            and _is_commit(receipt.get("checkout_mutation_post_apply_head"))
        )
        expected_patch_artifact_cleanup_verified = (
            receipt.get("patch_artifact_cleanup_status") == "removed"
            and patch_artifact_cleanup_digest_bound
            and bool(expected_patch_artifact_cleanup_paths)
            and patch_artifact_cleanup_artifact_paths_bound
            and patch_artifact_cleanup_artifact_count_bound
            and patch_artifact_cleanup_manifest_digest_bound
            and patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound
            and patch_artifact_cleanup_checkout_mutation_event_digest_bound
            and patch_artifact_cleanup_post_apply_head_bound
            and receipt.get("raw_patch_artifact_cleanup_payload_stored") is False
        )
        patch_artifact_cleanup_verified = (
            receipt.get("patch_artifact_cleanup_verified")
            == expected_patch_artifact_cleanup_verified
        )
        commit_finalization_digest_bound = (
            receipt.get("commit_finalization_digest")
            == self._commit_finalization_digest(
                source_batch_receipt_digest=str(
                    receipt.get("source_batch_receipt_digest", ""),
                ),
                current_checkout_head=str(receipt.get("current_checkout_head", "")),
                apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
                patch_artifact_manifest_digest=str(
                    receipt.get("patch_artifact_manifest_digest", ""),
                ),
                pre_apply_dry_run_manifest_digest=str(
                    receipt.get("pre_apply_dry_run_manifest_digest", ""),
                ),
                post_apply_verification_context_digest=str(
                    receipt.get("post_apply_verification_context_digest", ""),
                ),
                checkout_mutation_event_digest=str(
                    receipt.get("checkout_mutation_event_digest", ""),
                ),
                checkout_mutation_post_apply_head=str(
                    receipt.get("checkout_mutation_post_apply_head", ""),
                ),
                patch_artifact_cleanup_digest=str(
                    receipt.get("patch_artifact_cleanup_digest", ""),
                ),
                patch_artifact_cleanup_verified=bool(
                    receipt.get("patch_artifact_cleanup_verified", False),
                ),
                changed_file_owner_manifest_digest=str(
                    receipt.get("changed_file_owner_manifest_digest", ""),
                ),
                required_verifications_passed=bool(
                    receipt.get("required_verifications_passed", False),
                ),
                source_batch_ready_for_execution=bool(
                    receipt.get("source_batch_ready_for_execution", False),
                ),
                pre_apply_dry_run_passed=bool(
                    receipt.get("pre_apply_dry_run_passed", False),
                ),
                post_apply_verification_context_bound=bool(
                    receipt.get("post_apply_verification_context_bound", False),
                ),
                checkout_mutation_attested=bool(
                    receipt.get("checkout_mutation_attested", False),
                ),
            )
        )
        expected_commit_finalization_ready = (
            receipt.get("source_batch_ready_for_execution") is True
            and receipt.get("current_head_matches_batch") is True
            and self._pre_apply_dry_run_passed(
                pre_apply_dry_run_results,
                apply_steps=apply_steps,
            )
            and post_apply_verification_context_bound
            and checkout_mutation_attested
            and expected_patch_artifact_cleanup_verified
            and self._required_verifications_passed(verification_results)
            and repo_local_patch_artifacts_bound
        )
        commit_finalization_context_bound = (
            receipt.get("commit_finalization_source_batch_digest_bound") is True
            and _is_sha256(receipt.get("source_batch_receipt_digest"))
            and receipt.get("commit_finalization_apply_plan_digest_bound") is True
            and apply_plan_digest_bound
            and receipt.get(
                "commit_finalization_patch_artifact_manifest_digest_bound",
            )
            is True
            and patch_artifact_manifest_digest_bound
            and receipt.get(
                "commit_finalization_pre_apply_dry_run_manifest_digest_bound",
            )
            is True
            and pre_apply_dry_run_manifest_digest_bound
            and receipt.get(
                "commit_finalization_post_apply_verification_context_digest_bound",
            )
            is True
            and post_apply_verification_context_digest_bound
            and receipt.get(
                "commit_finalization_checkout_mutation_event_digest_bound",
            )
            is True
            and checkout_mutation_event_digest_bound
            and receipt.get(
                "commit_finalization_patch_artifact_cleanup_digest_bound",
            )
            is True
            and patch_artifact_cleanup_digest_bound
            and receipt.get(
                "commit_finalization_changed_file_owner_manifest_digest_bound",
            )
            is True
            and _is_sha256(receipt.get("changed_file_owner_manifest_digest"))
            and receipt.get("commit_finalization_required_verifications_bound")
            == self._required_verifications_passed(verification_results)
        )
        commit_finalization_ready = (
            receipt.get("commit_finalization_status")
            == ("ready" if expected_commit_finalization_ready else "blocked")
            and receipt.get("commit_finalization_ready")
            == expected_commit_finalization_ready
            and commit_finalization_digest_bound
            and commit_finalization_context_bound
            and receipt.get("raw_commit_finalization_payload_stored") is False
        )
        apply_step_patch_artifact_digest_bound = all(
            step.get("patch_artifact_digest")
            == self._integration_execution_patch_artifact_digest(
                receipt_ref=str(step.get("receipt_ref", "")),
                receipt_digest=str(step.get("receipt_digest", "")),
                changed_file_manifest_digest=str(
                    step.get("changed_file_manifest_digest", ""),
                ),
                patch_artifact_ref=str(step.get("patch_artifact_ref", "")),
                patch_artifact_path=str(step.get("patch_artifact_path", "")),
                patch_artifact_source=str(step.get("patch_artifact_source", "")),
                patch_artifact_profile=str(step.get("patch_artifact_profile", "")),
            )
            for step in apply_steps
        )
        pre_apply_patch_artifact_digest_bound = all(
            result.get("patch_artifact_digest_bound") is True
            for result in pre_apply_dry_run_results
        )
        pre_apply_command_bound = all(
            result.get("command_profile")
            == PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE
            and result.get("command")
            == f"git apply --check {result.get('patch_artifact_command_target', '')}"
            for result in pre_apply_dry_run_results
        )
        pre_apply_command_receipt_digest_bound = all(
            result.get("command_receipt_digest")
            == self._pre_apply_dry_run_command_receipt_digest(result)
            for result in pre_apply_dry_run_results
        )
        receipt_digest_bound = receipt.get("receipt_digest") == self._receipt_digest(
            receipt,
        )

        if receipt.get("kind") != "parallel_codex_integration_execution_receipt":
            errors.append("kind must be parallel_codex_integration_execution_receipt")
        if receipt.get("profile_id") != PARALLEL_CODEX_INTEGRATION_EXECUTION_PROFILE:
            errors.append("profile_id mismatch")
        if receipt.get("integration_policy_profile") != self._policy.profile_id:
            errors.append("integration_policy_profile mismatch")
        if receipt.get("reference_runbook_ref") != self._policy.reference_runbook_ref:
            errors.append("reference_runbook_ref mismatch")
        if (
            receipt.get("apply_plan_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE
        ):
            errors.append("apply_plan_profile mismatch")
        if (
            receipt.get("patch_artifact_binding_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
        ):
            errors.append("patch_artifact_binding_profile mismatch")
        if (
            receipt.get("pre_apply_dry_run_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE
        ):
            errors.append("pre_apply_dry_run_profile mismatch")
        if (
            receipt.get("post_apply_verification_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_PROFILE
        ):
            errors.append("post_apply_verification_profile mismatch")
        if (
            receipt.get("post_apply_verification_context_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE
        ):
            errors.append("post_apply_verification_context_profile mismatch")
        if (
            receipt.get("checkout_mutation_attestation_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE
        ):
            errors.append("checkout_mutation_attestation_profile mismatch")
        if (
            receipt.get("checkout_mutation_event_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE
        ):
            errors.append("checkout_mutation_event_profile mismatch")
        if (
            receipt.get("patch_artifact_cleanup_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE
        ):
            errors.append("patch_artifact_cleanup_profile mismatch")
        if (
            receipt.get("commit_finalization_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE
        ):
            errors.append("commit_finalization_profile mismatch")
        if len(receipt.get("ordered_integration_receipt_refs", [])) != len(
            receipt.get("ordered_integration_receipt_digests", []),
        ):
            errors.append("ordered receipt refs and digests must have equal length")
        if receipt.get("apply_step_count") != len(apply_steps):
            errors.append("apply_step_count mismatch")
        if receipt.get("pre_apply_dry_run_result_count") != len(
            pre_apply_dry_run_results,
        ):
            errors.append("pre_apply_dry_run_result_count mismatch")
        if receipt.get("post_apply_verification_command_count") != len(
            verification_results,
        ):
            errors.append("post_apply_verification_command_count mismatch")
        if not apply_plan_digest_bound:
            errors.append("apply_plan_digest mismatch")
        if not patch_artifact_manifest_digest_bound:
            errors.append("patch_artifact_manifest_digest mismatch")
        if not repo_local_patch_artifacts_bound:
            errors.append("repo_local_patch_artifacts not bound")
        if not apply_step_patch_artifact_digest_bound:
            errors.append("apply step patch_artifact_digest mismatch")
        if not pre_apply_dry_run_manifest_digest_bound:
            errors.append("pre_apply_dry_run_manifest_digest mismatch")
        if pre_apply_dry_run_results and not pre_apply_patch_artifact_digest_bound:
            errors.append("pre_apply patch_artifact_digest unbound")
        if pre_apply_dry_run_results and not pre_apply_command_bound:
            errors.append("pre_apply command must be git apply --check patch artifact")
        if pre_apply_dry_run_results and not pre_apply_command_receipt_digest_bound:
            errors.append("pre_apply command_receipt_digest mismatch")
        if not post_apply_verification_manifest_digest_bound:
            errors.append("post_apply_verification_manifest_digest mismatch")
        if not post_apply_verification_apply_plan_digest_bound:
            errors.append("post_apply verification apply_plan_digest unbound")
        if not post_apply_verification_patch_artifact_manifest_digest_bound:
            errors.append(
                "post_apply verification patch_artifact_manifest_digest unbound",
            )
        if not post_apply_verification_pre_apply_manifest_digest_bound:
            errors.append("post_apply verification pre_apply manifest unbound")
        if not post_apply_verification_context_digest_bound:
            errors.append("post_apply_verification_context_digest mismatch")
        if not post_apply_verification_context_bound:
            errors.append("post_apply_verification_context_bound mismatch")
        if not checkout_mutation_event_digest_bound:
            errors.append("checkout_mutation_event_digest mismatch")
        if not checkout_mutation_heads_bound:
            errors.append("checkout mutation heads must bind current and post-apply heads")
        if not checkout_mutation_context_bound:
            errors.append("checkout mutation context digest binding mismatch")
        if not patch_artifact_cleanup_digest_bound:
            errors.append("patch_artifact_cleanup_digest mismatch")
        if not patch_artifact_cleanup_artifact_paths_bound:
            errors.append("patch_artifact_cleanup_artifact_paths mismatch")
        if not patch_artifact_cleanup_artifact_count_bound:
            errors.append("patch_artifact_cleanup_artifact_count mismatch")
        if not patch_artifact_cleanup_manifest_digest_bound:
            errors.append("patch_artifact_cleanup manifest digest unbound")
        if not patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound:
            errors.append("patch_artifact_cleanup pre-apply digest unbound")
        if not patch_artifact_cleanup_checkout_mutation_event_digest_bound:
            errors.append("patch_artifact_cleanup checkout mutation digest unbound")
        if not patch_artifact_cleanup_post_apply_head_bound:
            errors.append("patch_artifact_cleanup post-apply head unbound")
        if not patch_artifact_cleanup_verified:
            errors.append("patch_artifact_cleanup_verified mismatch")
        if not commit_finalization_digest_bound:
            errors.append("commit_finalization_digest mismatch")
        if not commit_finalization_context_bound:
            errors.append("commit finalization context digest binding mismatch")
        if not commit_finalization_ready:
            errors.append("commit finalization readiness mismatch")
        if receipt.get("blocking_reasons") != expected_blocking_reasons:
            errors.append("blocking_reasons mismatch")
        if receipt.get("execution_decision") != expected_decision:
            errors.append("execution_decision mismatch")
        if not receipt_digest_bound:
            errors.append("receipt_digest mismatch")
        if receipt.get("raw_batch_payload_stored") is not False:
            errors.append("raw_batch_payload_stored must be false")
        if receipt.get("raw_apply_plan_payload_stored") is not False:
            errors.append("raw_apply_plan_payload_stored must be false")
        if receipt.get("raw_pre_apply_dry_run_payload_stored") is not False:
            errors.append("raw_pre_apply_dry_run_payload_stored must be false")
        if receipt.get("raw_checkout_mutation_payload_stored") is not False:
            errors.append("raw_checkout_mutation_payload_stored must be false")
        if receipt.get("raw_patch_artifact_cleanup_payload_stored") is not False:
            errors.append("raw_patch_artifact_cleanup_payload_stored must be false")
        if receipt.get("raw_commit_finalization_payload_stored") is not False:
            errors.append("raw_commit_finalization_payload_stored must be false")
        if receipt.get("raw_worker_receipt_payload_stored") is not False:
            errors.append("raw_worker_receipt_payload_stored must be false")
        if receipt.get("raw_verification_payload_stored") is not False:
            errors.append("raw_verification_payload_stored must be false")

        return {
            "ok": not errors,
            "ready_to_apply": (
                receipt.get("execution_decision") == "ready-to-apply"
                and not expected_blocking_reasons
            ),
            "errors": errors,
            "source_batch_receipt_digest_bound": (
                receipt.get("source_batch_receipt_digest_bound") is True
            ),
            "current_head_matches_batch": (
                receipt.get("current_head_matches_batch") is True
            ),
            "apply_plan_digest_bound": apply_plan_digest_bound,
            "patch_artifact_manifest_digest_bound": (
                patch_artifact_manifest_digest_bound
            ),
            "repo_local_patch_artifacts_bound": repo_local_patch_artifacts_bound,
            "apply_step_patch_artifact_digest_bound": (
                apply_step_patch_artifact_digest_bound
            ),
            "pre_apply_dry_run_manifest_digest_bound": (
                pre_apply_dry_run_manifest_digest_bound
            ),
            "pre_apply_patch_artifact_digest_bound": (
                pre_apply_patch_artifact_digest_bound
            ),
            "pre_apply_command_bound": pre_apply_command_bound,
            "pre_apply_command_receipt_digest_bound": (
                pre_apply_command_receipt_digest_bound
            ),
            "pre_apply_dry_run_passed": self._pre_apply_dry_run_passed(
                pre_apply_dry_run_results,
                apply_steps=apply_steps,
            ),
            "post_apply_verification_manifest_digest_bound": (
                post_apply_verification_manifest_digest_bound
            ),
            "post_apply_verification_apply_plan_digest_bound": (
                post_apply_verification_apply_plan_digest_bound
            ),
            "post_apply_verification_patch_artifact_manifest_digest_bound": (
                post_apply_verification_patch_artifact_manifest_digest_bound
            ),
            "post_apply_verification_pre_apply_manifest_digest_bound": (
                post_apply_verification_pre_apply_manifest_digest_bound
            ),
            "post_apply_verification_context_digest_bound": (
                post_apply_verification_context_digest_bound
            ),
            "post_apply_verification_context_bound": (
                post_apply_verification_context_bound
            ),
            "checkout_mutation_event_digest_bound": (
                checkout_mutation_event_digest_bound
            ),
            "checkout_mutation_heads_bound": checkout_mutation_heads_bound,
            "checkout_mutation_context_bound": checkout_mutation_context_bound,
            "checkout_mutation_attested": checkout_mutation_attested,
            "patch_artifact_cleanup_digest_bound": (
                patch_artifact_cleanup_digest_bound
            ),
            "patch_artifact_cleanup_artifact_paths_bound": (
                patch_artifact_cleanup_artifact_paths_bound
            ),
            "patch_artifact_cleanup_artifact_count_bound": (
                patch_artifact_cleanup_artifact_count_bound
            ),
            "patch_artifact_cleanup_manifest_digest_bound": (
                patch_artifact_cleanup_manifest_digest_bound
            ),
            "patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound": (
                patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound
            ),
            "patch_artifact_cleanup_checkout_mutation_event_digest_bound": (
                patch_artifact_cleanup_checkout_mutation_event_digest_bound
            ),
            "patch_artifact_cleanup_post_apply_head_bound": (
                patch_artifact_cleanup_post_apply_head_bound
            ),
            "patch_artifact_cleanup_verified": (
                expected_patch_artifact_cleanup_verified
                and receipt.get("patch_artifact_cleanup_verified") is True
            ),
            "commit_finalization_digest_bound": commit_finalization_digest_bound,
            "commit_finalization_context_bound": commit_finalization_context_bound,
            "commit_finalization_patch_artifact_cleanup_digest_bound": (
                receipt.get(
                    "commit_finalization_patch_artifact_cleanup_digest_bound",
                )
                is True
                and patch_artifact_cleanup_digest_bound
            ),
            "commit_finalization_ready": (
                expected_commit_finalization_ready
                and receipt.get("commit_finalization_ready") is True
                and commit_finalization_digest_bound
                and commit_finalization_context_bound
            ),
            "commit_finalization_consistent": commit_finalization_ready,
            "required_verifications_passed": self._required_verifications_passed(
                verification_results,
            ),
            "source_batch_ready_for_execution": (
                receipt.get("source_batch_ready_for_execution") is True
            ),
            "blocked_on_source_batch": (
                receipt.get("source_batch_decision") != "integration-ready"
                and receipt.get("execution_decision") == "blocked"
            ),
            "receipt_digest_bound": receipt_digest_bound,
            "raw_batch_payload_redacted": (
                receipt.get("raw_batch_payload_stored") is False
            ),
            "raw_apply_plan_payload_redacted": (
                receipt.get("raw_apply_plan_payload_stored") is False
            ),
            "raw_pre_apply_dry_run_payload_redacted": (
                receipt.get("raw_pre_apply_dry_run_payload_stored") is False
            ),
            "raw_checkout_mutation_payload_redacted": (
                receipt.get("raw_checkout_mutation_payload_stored") is False
            ),
            "raw_patch_artifact_cleanup_payload_redacted": (
                receipt.get("raw_patch_artifact_cleanup_payload_stored") is False
            ),
            "raw_commit_finalization_payload_redacted": (
                receipt.get("raw_commit_finalization_payload_stored") is False
            ),
            "raw_worker_receipt_payload_redacted": (
                receipt.get("raw_worker_receipt_payload_stored") is False
            ),
            "raw_verification_payload_redacted": (
                receipt.get("raw_verification_payload_stored") is False
            ),
        }

    def plan_post_commit_publication(
        self,
        *,
        execution_receipt: Mapping[str, Any],
        local_commit_head: str,
        remote_head: str,
        result_summary: str,
        pre_push_remote_head: str = "",
        remote_name: str = "origin",
        remote_ref: str = "refs/heads/main",
        pre_push_remote_verification_result: Mapping[str, Any] | None = None,
        push_result: Mapping[str, Any] | None = None,
        remote_verification_result: Mapping[str, Any] | None = None,
        protected_branch_provider: str = (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER
        ),
        protected_branch_policy_ref: str = (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_REF
        ),
        protected_branch_policy_digest: str = "",
        protected_branch_status: str = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS
        ),
        protected_branch_required_checks: Sequence[str] | None = None,
        protected_branch_policy_checked_at_ref: str = (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_CHECKED_AT_REF
        ),
        protected_branch_policy_freshness_window_seconds: int = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
        ),
        protected_branch_policy_freshness_status: str = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS
        ),
        protected_branch_provider_timestamp_ref: str = (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_REF
        ),
        protected_branch_provider_timestamp_status: str = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS
        ),
        protected_branch_provider_timestamp_signature_digest: str = "",
        protected_branch_provider_timestamp_nonce_ref: str = (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_NONCE_REF
        ),
        protected_branch_provider_timestamp_replay_status: str = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS
        ),
        protected_branch_receipt_digest: str = "",
        status_check_provider: str = PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_PROVIDER,
        status_check_suite_ref: str = PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_REF,
        status_check_commit_head: str = "",
        status_check_results: Sequence[Mapping[str, Any]] | None = None,
        status_check_suite_digest: str = "",
        status_check_suite_checked_at_ref: str = (
            PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_CHECKED_AT_REF
        ),
        status_check_suite_freshness_window_seconds: int = (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
        ),
        status_check_suite_freshness_status: str = (
            PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS
        ),
        status_check_suite_freshness_digest: str = "",
    ) -> Dict[str, Any]:
        execution_validation = self.validate_integration_execution_receipt(
            execution_receipt,
        )
        normalized_local_head = local_commit_head.strip()
        normalized_remote_head = remote_head.strip()
        normalized_remote_name = remote_name.strip() or "origin"
        normalized_remote_ref = remote_ref.strip() or "refs/heads/main"
        source_current_checkout_head = str(
            execution_receipt.get("current_checkout_head", ""),
        ).strip()
        normalized_pre_push_remote_head = (
            pre_push_remote_head.strip() or source_current_checkout_head
        )
        remote_tracking_ref = normalized_remote_ref.replace(
            "refs/heads/",
            f"refs/remotes/{normalized_remote_name}/",
            1,
        )
        push_command = (
            f"git push {normalized_remote_name} HEAD:{normalized_remote_ref}"
        )
        remote_verification_command = (
            f"git ls-remote {normalized_remote_name} {normalized_remote_ref}"
        )
        raw_pre_push_remote_verification_result = (
            pre_push_remote_verification_result
            or {
                "stdout_excerpt": (
                    f"{normalized_pre_push_remote_head}\t{normalized_remote_ref}"
                ),
            }
        )
        normalized_pre_push_remote_verification_result = (
            self._normalize_post_commit_publication_command(
                raw_pre_push_remote_verification_result,
                default_command=remote_verification_command,
                command_profile=(
                    PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
                ),
            )
        )
        normalized_push_result = self._normalize_post_commit_publication_command(
            push_result or {},
            default_command=push_command,
            command_profile=(
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
            ),
        )
        raw_remote_verification_result = remote_verification_result or {
            "stdout_excerpt": f"{normalized_remote_head}\t{normalized_remote_ref}",
        }
        normalized_remote_verification_result = (
            self._normalize_post_commit_publication_command(
                raw_remote_verification_result,
                default_command=remote_verification_command,
                command_profile=(
                    PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
                ),
            )
        )
        source_execution_digest = str(
            execution_receipt.get("receipt_digest", ""),
        ).strip()
        source_post_apply_head = str(
            execution_receipt.get("checkout_mutation_post_apply_head", ""),
        ).strip()
        source_commit_finalization_digest = str(
            execution_receipt.get("commit_finalization_digest", ""),
        ).strip()
        normalized_protected_branch_provider = (
            protected_branch_provider.strip()
            or PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER
        )
        normalized_protected_branch_policy_ref = (
            protected_branch_policy_ref.strip()
            or PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_REF
        )
        normalized_protected_branch_checks = _dedupe_strings(
            list(
                protected_branch_required_checks
                if protected_branch_required_checks is not None
                else self._policy.required_verifications
            )
        )
        normalized_protected_branch_status = (
            protected_branch_status.strip()
            or PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS
        )
        normalized_policy_checked_at_ref = (
            protected_branch_policy_checked_at_ref.strip()
            or PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_CHECKED_AT_REF
        )
        normalized_policy_freshness_window_seconds = _coerce_int(
            protected_branch_policy_freshness_window_seconds,
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS,
        )
        normalized_policy_freshness_status = (
            protected_branch_policy_freshness_status.strip()
            or PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS
        )
        normalized_provider_timestamp_ref = (
            protected_branch_provider_timestamp_ref.strip()
            or PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_REF
        )
        normalized_provider_timestamp_status = (
            protected_branch_provider_timestamp_status.strip()
            or PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS
        )
        normalized_provider_timestamp_signature_digest = (
            protected_branch_provider_timestamp_signature_digest.strip()
        )
        if not _is_sha256(normalized_provider_timestamp_signature_digest):
            normalized_provider_timestamp_signature_digest = sha256_text(
                canonical_json(
                    {
                        "profile_id": (
                            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNATURE_PROFILE
                        ),
                        "provider": normalized_protected_branch_provider,
                        "branch_ref": normalized_remote_ref,
                        "timestamp_ref": normalized_provider_timestamp_ref,
                        "timestamp_status": normalized_provider_timestamp_status,
                        "raw_provider_timestamp_payload_stored": False,
                    }
                )
            )
        normalized_provider_timestamp_nonce_ref = (
            protected_branch_provider_timestamp_nonce_ref.strip()
            or PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_POLICY_TIMESTAMP_NONCE_REF
        )
        normalized_provider_timestamp_replay_status = (
            protected_branch_provider_timestamp_replay_status.strip()
            or PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS
        )
        normalized_protected_branch_policy_digest = (
            protected_branch_policy_digest.strip()
        )
        expected_protected_branch_policy_digest = (
            self._post_commit_protected_branch_policy_digest(
                provider=normalized_protected_branch_provider,
                branch_ref=normalized_remote_ref,
                policy_ref=normalized_protected_branch_policy_ref,
                required_checks=normalized_protected_branch_checks,
            )
        )
        if not _is_sha256(normalized_protected_branch_policy_digest):
            normalized_protected_branch_policy_digest = (
                expected_protected_branch_policy_digest
            )
        protected_branch_policy_bound = (
            normalized_protected_branch_policy_digest
            == expected_protected_branch_policy_digest
        )
        protected_branch_policy_freshness_digest = (
            self._post_commit_protected_branch_freshness_digest(
                provider=normalized_protected_branch_provider,
                branch_ref=normalized_remote_ref,
                policy_ref=normalized_protected_branch_policy_ref,
                policy_digest=normalized_protected_branch_policy_digest,
                checked_at_ref=normalized_policy_checked_at_ref,
                freshness_window_seconds=normalized_policy_freshness_window_seconds,
                freshness_status=normalized_policy_freshness_status,
            )
        )
        protected_branch_policy_freshness_bound = _is_sha256(
            protected_branch_policy_freshness_digest,
        )
        protected_branch_provider_timestamp_digest = (
            self._post_commit_protected_branch_timestamp_digest(
                provider=normalized_protected_branch_provider,
                branch_ref=normalized_remote_ref,
                policy_digest=normalized_protected_branch_policy_digest,
                timestamp_ref=normalized_provider_timestamp_ref,
                timestamp_status=normalized_provider_timestamp_status,
                timestamp_signature_digest=(
                    normalized_provider_timestamp_signature_digest
                ),
            )
        )
        protected_branch_provider_timestamp_bound = (
            _is_sha256(protected_branch_provider_timestamp_digest)
        )
        protected_branch_provider_timestamp_replay_digest = (
            self._post_commit_protected_branch_timestamp_replay_digest(
                provider=normalized_protected_branch_provider,
                branch_ref=normalized_remote_ref,
                timestamp_ref=normalized_provider_timestamp_ref,
                nonce_ref=normalized_provider_timestamp_nonce_ref,
                replay_status=normalized_provider_timestamp_replay_status,
            )
        )
        protected_branch_provider_timestamp_replay_bound = (
            _is_sha256(protected_branch_provider_timestamp_replay_digest)
        )
        normalized_status_check_provider = (
            status_check_provider.strip()
            or PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_PROVIDER
        )
        normalized_status_check_suite_ref = (
            status_check_suite_ref.strip()
            or PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_REF
        )
        normalized_status_check_commit_head = (
            status_check_commit_head.strip() or normalized_remote_head
        )
        normalized_status_check_results = (
            self._normalize_post_commit_status_check_results(
                provider=normalized_status_check_provider,
                commit_head=normalized_status_check_commit_head,
                required_checks=normalized_protected_branch_checks,
                status_check_results=status_check_results,
            )
        )
        status_check_results_bound = self._post_commit_status_check_results_bound(
            normalized_status_check_results,
        )
        status_check_all_required_passed = (
            self._post_commit_status_check_all_required_passed(
                required_checks=normalized_protected_branch_checks,
                commit_head=normalized_status_check_commit_head,
                status_check_results=normalized_status_check_results,
            )
        )
        normalized_status_check_suite_digest = status_check_suite_digest.strip()
        expected_status_check_suite_digest = (
            self._post_commit_status_check_suite_digest(
                provider=normalized_status_check_provider,
                suite_ref=normalized_status_check_suite_ref,
                commit_head=normalized_status_check_commit_head,
                required_checks=normalized_protected_branch_checks,
                status_check_results=normalized_status_check_results,
                all_required_passed=status_check_all_required_passed,
            )
        )
        if not _is_sha256(normalized_status_check_suite_digest):
            normalized_status_check_suite_digest = expected_status_check_suite_digest
        status_check_suite_digest_bound = (
            normalized_status_check_suite_digest
            == expected_status_check_suite_digest
        )
        normalized_status_check_suite_checked_at_ref = (
            status_check_suite_checked_at_ref.strip()
            or PARALLEL_CODEX_DEFAULT_STATUS_CHECK_SUITE_CHECKED_AT_REF
        )
        normalized_status_check_suite_freshness_window_seconds = _coerce_int(
            status_check_suite_freshness_window_seconds,
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS,
        )
        normalized_status_check_suite_freshness_status = (
            status_check_suite_freshness_status.strip()
            or PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS
        )
        normalized_status_check_suite_freshness_digest = (
            status_check_suite_freshness_digest.strip()
        )
        expected_status_check_suite_freshness_digest = (
            self._post_commit_status_check_suite_freshness_digest(
                provider=normalized_status_check_provider,
                suite_ref=normalized_status_check_suite_ref,
                suite_digest=normalized_status_check_suite_digest,
                checked_at_ref=normalized_status_check_suite_checked_at_ref,
                freshness_window_seconds=(
                    normalized_status_check_suite_freshness_window_seconds
                ),
                freshness_status=normalized_status_check_suite_freshness_status,
            )
        )
        if not _is_sha256(normalized_status_check_suite_freshness_digest):
            normalized_status_check_suite_freshness_digest = (
                expected_status_check_suite_freshness_digest
            )
        status_check_suite_freshness_digest_bound = (
            normalized_status_check_suite_freshness_digest
            == expected_status_check_suite_freshness_digest
        )
        (
            pre_push_remote_verification_observed_head,
            pre_push_remote_verification_observed_ref,
        ) = self._post_commit_remote_verification_observed_output(
            raw_pre_push_remote_verification_result,
            expected_head=normalized_pre_push_remote_head,
            expected_ref=normalized_remote_ref,
            stdout_digest=normalized_pre_push_remote_verification_result[
                "stdout_digest"
            ],
        )
        pre_push_remote_verification_output_digest = (
            self._post_commit_remote_verification_output_digest(
                observed_head=pre_push_remote_verification_observed_head,
                observed_ref=pre_push_remote_verification_observed_ref,
                stdout_digest=normalized_pre_push_remote_verification_result[
                    "stdout_digest"
                ],
            )
        )
        pre_push_remote_verification_output_digest_bound = (
            pre_push_remote_verification_observed_head
            == normalized_pre_push_remote_head
            and pre_push_remote_verification_observed_ref == normalized_remote_ref
            and self._post_commit_remote_verification_stdout_digest_matches(
                normalized_pre_push_remote_verification_result["stdout_digest"],
                head=pre_push_remote_verification_observed_head,
                ref=pre_push_remote_verification_observed_ref,
            )
        )
        (
            remote_verification_observed_head,
            remote_verification_observed_ref,
        ) = self._post_commit_remote_verification_observed_output(
            raw_remote_verification_result,
            expected_head=normalized_remote_head,
            expected_ref=normalized_remote_ref,
            stdout_digest=normalized_remote_verification_result["stdout_digest"],
        )
        remote_verification_output_digest = (
            self._post_commit_remote_verification_output_digest(
                observed_head=remote_verification_observed_head,
                observed_ref=remote_verification_observed_ref,
                stdout_digest=normalized_remote_verification_result[
                    "stdout_digest"
                ],
            )
        )
        remote_verification_output_digest_bound = (
            remote_verification_observed_head == normalized_remote_head
            and remote_verification_observed_ref == normalized_remote_ref
            and self._post_commit_remote_verification_stdout_digest_matches(
                normalized_remote_verification_result["stdout_digest"],
                head=remote_verification_observed_head,
                ref=remote_verification_observed_ref,
            )
        )
        receipt = {
            "kind": "parallel_codex_post_commit_publication_receipt",
            "schema_version": "1.0.0",
            "receipt_id": new_id("parallel-codex-publication"),
            "generated_at": utc_now_iso(),
            "profile_id": PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE,
            "integration_policy_profile": self._policy.profile_id,
            "reference_runbook_ref": self._policy.reference_runbook_ref,
            "source_execution_receipt_ref": str(
                execution_receipt.get("receipt_ref", ""),
            ).strip(),
            "source_execution_receipt_digest": source_execution_digest,
            "source_execution_receipt_digest_bound": (
                _is_sha256(source_execution_digest)
                and source_execution_digest
                == self._receipt_digest(execution_receipt)
            ),
            "source_execution_decision": str(
                execution_receipt.get("execution_decision", ""),
            ).strip(),
            "source_execution_ready_to_apply": execution_validation[
                "ready_to_apply"
            ],
            "source_execution_commit_finalization_ref": str(
                execution_receipt.get("commit_finalization_ref", ""),
            ).strip(),
            "source_execution_commit_finalization_digest": (
                source_commit_finalization_digest
            ),
            "source_execution_commit_finalization_ready": (
                execution_validation["commit_finalization_ready"]
            ),
            "source_execution_current_checkout_head": source_current_checkout_head,
            "source_execution_post_apply_head": source_post_apply_head,
            "local_commit_head": normalized_local_head,
            "local_commit_head_matches_source": (
                normalized_local_head == source_post_apply_head
            ),
            "remote_name": normalized_remote_name,
            "remote_ref": normalized_remote_ref,
            "remote_tracking_ref": remote_tracking_ref,
            "pre_push_remote_head": normalized_pre_push_remote_head,
            "pre_push_remote_head_matches_source": (
                normalized_pre_push_remote_head == source_current_checkout_head
            ),
            "pre_push_remote_verification_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
            ),
            "pre_push_remote_verification_result": (
                normalized_pre_push_remote_verification_result
            ),
            "pre_push_remote_verification_command_receipt_digest": (
                normalized_pre_push_remote_verification_result[
                    "command_receipt_digest"
                ]
            ),
            "pre_push_remote_verification_output_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
            ),
            "pre_push_remote_verification_observed_head": (
                pre_push_remote_verification_observed_head
            ),
            "pre_push_remote_verification_observed_ref": (
                pre_push_remote_verification_observed_ref
            ),
            "pre_push_remote_verification_output_digest": (
                pre_push_remote_verification_output_digest
            ),
            "pre_push_remote_verification_output_digest_bound": (
                pre_push_remote_verification_output_digest_bound
            ),
            "remote_head": normalized_remote_head,
            "remote_head_matches_local_commit": (
                normalized_remote_head == normalized_local_head
            ),
            "push_command_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
            ),
            "push_command_result": normalized_push_result,
            "push_command_receipt_digest": normalized_push_result[
                "command_receipt_digest"
            ],
            "remote_verification_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
            ),
            "remote_verification_result": normalized_remote_verification_result,
            "remote_verification_command_receipt_digest": (
                normalized_remote_verification_result["command_receipt_digest"]
            ),
            "remote_verification_output_profile": (
                PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
            ),
            "remote_verification_observed_head": (
                remote_verification_observed_head
            ),
            "remote_verification_observed_ref": remote_verification_observed_ref,
            "remote_verification_output_digest": remote_verification_output_digest,
            "remote_verification_output_digest_bound": (
                remote_verification_output_digest_bound
            ),
            "protected_branch_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
            ),
            "protected_branch_provider": normalized_protected_branch_provider,
            "protected_branch_ref": normalized_remote_ref,
            "protected_branch_policy_ref": normalized_protected_branch_policy_ref,
            "protected_branch_policy_digest": (
                normalized_protected_branch_policy_digest
            ),
            "protected_branch_policy_bound": protected_branch_policy_bound,
            "protected_branch_status": normalized_protected_branch_status,
            "protected_branch_required_checks": normalized_protected_branch_checks,
            "protected_branch_required_check_count": len(
                normalized_protected_branch_checks,
            ),
            "protected_branch_policy_freshness_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESHNESS_PROFILE
            ),
            "protected_branch_policy_checked_at_ref": (
                normalized_policy_checked_at_ref
            ),
            "protected_branch_policy_freshness_window_seconds": (
                normalized_policy_freshness_window_seconds
            ),
            "protected_branch_policy_freshness_status": (
                normalized_policy_freshness_status
            ),
            "protected_branch_policy_freshness_digest": (
                protected_branch_policy_freshness_digest
            ),
            "protected_branch_policy_freshness_digest_bound": (
                protected_branch_policy_freshness_bound
            ),
            "protected_branch_provider_timestamp_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_PROFILE
            ),
            "protected_branch_provider_timestamp_ref": (
                normalized_provider_timestamp_ref
            ),
            "protected_branch_provider_timestamp_status": (
                normalized_provider_timestamp_status
            ),
            "protected_branch_provider_timestamp_signature_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNATURE_PROFILE
            ),
            "protected_branch_provider_timestamp_signature_digest": (
                normalized_provider_timestamp_signature_digest
            ),
            "protected_branch_provider_timestamp_digest": (
                protected_branch_provider_timestamp_digest
            ),
            "protected_branch_provider_timestamp_digest_bound": (
                protected_branch_provider_timestamp_bound
            ),
            "protected_branch_provider_timestamp_replay_profile": (
                PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAY_PROFILE
            ),
            "protected_branch_provider_timestamp_nonce_ref": (
                normalized_provider_timestamp_nonce_ref
            ),
            "protected_branch_provider_timestamp_replay_status": (
                normalized_provider_timestamp_replay_status
            ),
            "protected_branch_provider_timestamp_replay_digest": (
                protected_branch_provider_timestamp_replay_digest
            ),
            "protected_branch_provider_timestamp_replay_digest_bound": (
                protected_branch_provider_timestamp_replay_bound
            ),
            "status_check_profile": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE
            ),
            "status_check_provider": normalized_status_check_provider,
            "status_check_suite_ref": normalized_status_check_suite_ref,
            "status_check_commit_head": normalized_status_check_commit_head,
            "status_check_required_checks": normalized_protected_branch_checks,
            "status_check_results": normalized_status_check_results,
            "status_check_result_count": len(normalized_status_check_results),
            "status_check_results_bound": status_check_results_bound,
            "status_check_all_required_passed": status_check_all_required_passed,
            "status_check_suite_digest": normalized_status_check_suite_digest,
            "status_check_suite_digest_bound": status_check_suite_digest_bound,
            "status_check_suite_freshness_profile": (
                PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESHNESS_PROFILE
            ),
            "status_check_suite_checked_at_ref": (
                normalized_status_check_suite_checked_at_ref
            ),
            "status_check_suite_freshness_window_seconds": (
                normalized_status_check_suite_freshness_window_seconds
            ),
            "status_check_suite_freshness_status": (
                normalized_status_check_suite_freshness_status
            ),
            "status_check_suite_freshness_digest": (
                normalized_status_check_suite_freshness_digest
            ),
            "status_check_suite_freshness_digest_bound": (
                status_check_suite_freshness_digest_bound
            ),
            "protected_branch_receipt_digest": "",
            "protected_branch_receipt_digest_bound": False,
            "publication_digest": "",
            "publication_status": "blocked",
            "ready_for_github_handoff": False,
            "blocking_reasons": [],
            "result_summary": result_summary,
            "raw_execution_payload_stored": False,
            "raw_post_commit_publication_payload_stored": False,
            "raw_pre_push_remote_verification_stdout_stored": False,
            "raw_pre_push_remote_verification_stderr_stored": False,
            "raw_push_stdout_stored": False,
            "raw_push_stderr_stored": False,
            "raw_remote_verification_stdout_stored": False,
            "raw_remote_verification_stderr_stored": False,
            "raw_protected_branch_provider_payload_stored": False,
            "raw_protected_branch_policy_freshness_payload_stored": False,
            "raw_protected_branch_provider_timestamp_payload_stored": False,
            "raw_protected_branch_provider_timestamp_replay_guard_payload_stored": (
                False
            ),
            "raw_status_check_provider_payload_stored": False,
            "raw_status_check_suite_freshness_payload_stored": False,
            "receipt_digest": "",
        }
        normalized_protected_branch_receipt_digest = (
            protected_branch_receipt_digest.strip()
        )
        if not _is_sha256(normalized_protected_branch_receipt_digest):
            normalized_protected_branch_receipt_digest = (
                self._post_commit_protected_branch_receipt_digest(receipt)
            )
        receipt["protected_branch_receipt_digest"] = (
            normalized_protected_branch_receipt_digest
        )
        receipt["protected_branch_receipt_digest_bound"] = (
            normalized_protected_branch_receipt_digest
            == self._post_commit_protected_branch_receipt_digest(receipt)
        )
        receipt["publication_digest"] = self._post_commit_publication_digest(
            receipt,
        )
        receipt["receipt_ref"] = (
            f"receipt://parallel-codex/{receipt['receipt_id']}"
        )
        receipt["blocking_reasons"] = (
            self._derive_post_commit_publication_blocking_reasons(receipt)
        )
        receipt["publication_status"] = (
            "blocked" if receipt["blocking_reasons"] else "published"
        )
        receipt["ready_for_github_handoff"] = not receipt["blocking_reasons"]
        receipt["receipt_digest"] = self._receipt_digest(receipt)
        return receipt

    def validate_post_commit_publication_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: list[str] = []
        expected_blocking_reasons = (
            self._derive_post_commit_publication_blocking_reasons(receipt)
        )
        expected_status = (
            "blocked" if expected_blocking_reasons else "published"
        )
        push_command = (
            f"git push {receipt.get('remote_name', '')} "
            f"HEAD:{receipt.get('remote_ref', '')}"
        )
        remote_verification_command = (
            f"git ls-remote {receipt.get('remote_name', '')} "
            f"{receipt.get('remote_ref', '')}"
        )
        push_result = dict(receipt.get("push_command_result", {}))
        pre_push_remote_verification_result = dict(
            receipt.get("pre_push_remote_verification_result", {}),
        )
        remote_verification_result = dict(
            receipt.get("remote_verification_result", {}),
        )
        push_command_digest_bound = (
            receipt.get("push_command_receipt_digest")
            == self._post_commit_publication_command_receipt_digest(push_result)
            and push_result.get("command_receipt_digest")
            == receipt.get("push_command_receipt_digest")
        )
        pre_push_remote_verification_digest_bound = (
            receipt.get("pre_push_remote_verification_command_receipt_digest")
            == self._post_commit_publication_command_receipt_digest(
                pre_push_remote_verification_result,
            )
            and pre_push_remote_verification_result.get("command_receipt_digest")
            == receipt.get("pre_push_remote_verification_command_receipt_digest")
        )
        remote_verification_digest_bound = (
            receipt.get("remote_verification_command_receipt_digest")
            == self._post_commit_publication_command_receipt_digest(
                remote_verification_result,
            )
            and remote_verification_result.get("command_receipt_digest")
            == receipt.get("remote_verification_command_receipt_digest")
        )
        pre_push_remote_verification_output_digest_bound = (
            receipt.get("pre_push_remote_verification_output_digest")
            == self._post_commit_remote_verification_output_digest(
                observed_head=str(
                    receipt.get("pre_push_remote_verification_observed_head", ""),
                ),
                observed_ref=str(
                    receipt.get("pre_push_remote_verification_observed_ref", ""),
                ),
                stdout_digest=str(
                    pre_push_remote_verification_result.get("stdout_digest", ""),
                ),
            )
            and receipt.get("pre_push_remote_verification_output_digest_bound") is True
            and receipt.get("pre_push_remote_verification_observed_head")
            == receipt.get("pre_push_remote_head")
            and receipt.get("pre_push_remote_verification_observed_ref")
            == receipt.get("remote_ref")
            and self._post_commit_remote_verification_stdout_digest_matches(
                str(pre_push_remote_verification_result.get("stdout_digest", "")),
                head=str(
                    receipt.get("pre_push_remote_verification_observed_head", ""),
                ),
                ref=str(
                    receipt.get("pre_push_remote_verification_observed_ref", ""),
                ),
            )
        )
        remote_verification_output_digest_bound = (
            receipt.get("remote_verification_output_digest")
            == self._post_commit_remote_verification_output_digest(
                observed_head=str(
                    receipt.get("remote_verification_observed_head", ""),
                ),
                observed_ref=str(
                    receipt.get("remote_verification_observed_ref", ""),
                ),
                stdout_digest=str(
                    remote_verification_result.get("stdout_digest", ""),
                ),
            )
            and receipt.get("remote_verification_output_digest_bound") is True
            and receipt.get("remote_verification_observed_head")
            == receipt.get("remote_head")
            and receipt.get("remote_verification_observed_ref")
            == receipt.get("remote_ref")
            and self._post_commit_remote_verification_stdout_digest_matches(
                str(remote_verification_result.get("stdout_digest", "")),
                head=str(receipt.get("remote_verification_observed_head", "")),
                ref=str(receipt.get("remote_verification_observed_ref", "")),
            )
        )
        publication_digest_bound = (
            receipt.get("publication_digest")
            == self._post_commit_publication_digest(receipt)
        )
        protected_branch_policy_digest_bound = (
            receipt.get("protected_branch_policy_digest")
            == self._post_commit_protected_branch_policy_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_ref=str(receipt.get("protected_branch_policy_ref", "")),
                required_checks=receipt.get("protected_branch_required_checks", []),
            )
            and receipt.get("protected_branch_policy_bound") is True
        )
        protected_branch_receipt_digest_bound = (
            receipt.get("protected_branch_receipt_digest")
            == self._post_commit_protected_branch_receipt_digest(receipt)
            and receipt.get("protected_branch_receipt_digest_bound") is True
        )
        protected_branch_policy_freshness_digest_bound = (
            receipt.get("protected_branch_policy_freshness_digest")
            == self._post_commit_protected_branch_freshness_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_ref=str(receipt.get("protected_branch_policy_ref", "")),
                policy_digest=str(receipt.get("protected_branch_policy_digest", "")),
                checked_at_ref=str(
                    receipt.get("protected_branch_policy_checked_at_ref", ""),
                ),
                freshness_window_seconds=_coerce_int(
                    receipt.get("protected_branch_policy_freshness_window_seconds"),
                    0,
                ),
                freshness_status=str(
                    receipt.get("protected_branch_policy_freshness_status", ""),
                ),
            )
            and receipt.get("protected_branch_policy_freshness_digest_bound") is True
        )
        protected_branch_provider_timestamp_digest_bound = (
            receipt.get("protected_branch_provider_timestamp_digest")
            == self._post_commit_protected_branch_timestamp_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_digest=str(receipt.get("protected_branch_policy_digest", "")),
                timestamp_ref=str(
                    receipt.get("protected_branch_provider_timestamp_ref", ""),
                ),
                timestamp_status=str(
                    receipt.get("protected_branch_provider_timestamp_status", ""),
                ),
                timestamp_signature_digest=str(
                    receipt.get(
                        "protected_branch_provider_timestamp_signature_digest",
                        "",
                    ),
                ),
            )
            and receipt.get("protected_branch_provider_timestamp_digest_bound") is True
        )
        protected_branch_provider_timestamp_replay_digest_bound = (
            receipt.get("protected_branch_provider_timestamp_replay_digest")
            == self._post_commit_protected_branch_timestamp_replay_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                timestamp_ref=str(
                    receipt.get("protected_branch_provider_timestamp_ref", ""),
                ),
                nonce_ref=str(
                    receipt.get("protected_branch_provider_timestamp_nonce_ref", ""),
                ),
                replay_status=str(
                    receipt.get(
                        "protected_branch_provider_timestamp_replay_status",
                        "",
                    ),
                ),
            )
            and receipt.get(
                "protected_branch_provider_timestamp_replay_digest_bound",
            )
            is True
        )
        status_check_results = list(receipt.get("status_check_results", []))
        status_check_results_bound = (
            self._post_commit_status_check_results_bound(status_check_results)
            and receipt.get("status_check_results_bound") is True
        )
        status_check_all_required_passed = (
            self._post_commit_status_check_all_required_passed(
                required_checks=receipt.get("status_check_required_checks", []),
                commit_head=str(receipt.get("status_check_commit_head", "")),
                status_check_results=status_check_results,
            )
            and receipt.get("status_check_all_required_passed") is True
        )
        status_check_suite_digest_bound = (
            receipt.get("status_check_suite_digest")
            == self._post_commit_status_check_suite_digest(
                provider=str(receipt.get("status_check_provider", "")),
                suite_ref=str(receipt.get("status_check_suite_ref", "")),
                commit_head=str(receipt.get("status_check_commit_head", "")),
                required_checks=receipt.get("status_check_required_checks", []),
                status_check_results=status_check_results,
                all_required_passed=bool(
                    receipt.get("status_check_all_required_passed", False),
                ),
            )
            and receipt.get("status_check_suite_digest_bound") is True
        )
        status_check_suite_freshness_digest_bound = (
            receipt.get("status_check_suite_freshness_digest")
            == self._post_commit_status_check_suite_freshness_digest(
                provider=str(receipt.get("status_check_provider", "")),
                suite_ref=str(receipt.get("status_check_suite_ref", "")),
                suite_digest=str(receipt.get("status_check_suite_digest", "")),
                checked_at_ref=str(
                    receipt.get("status_check_suite_checked_at_ref", ""),
                ),
                freshness_window_seconds=_coerce_int(
                    receipt.get("status_check_suite_freshness_window_seconds"),
                    0,
                ),
                freshness_status=str(
                    receipt.get("status_check_suite_freshness_status", ""),
                ),
            )
            and receipt.get("status_check_suite_freshness_digest_bound") is True
        )
        receipt_digest_bound = (
            receipt.get("receipt_digest") == self._receipt_digest(receipt)
        )

        if receipt.get("kind") != "parallel_codex_post_commit_publication_receipt":
            errors.append("kind must be parallel_codex_post_commit_publication_receipt")
        if receipt.get("profile_id") != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE:
            errors.append("profile_id mismatch")
        if receipt.get("integration_policy_profile") != self._policy.profile_id:
            errors.append("integration_policy_profile mismatch")
        if receipt.get("reference_runbook_ref") != self._policy.reference_runbook_ref:
            errors.append("reference_runbook_ref mismatch")
        if (
            receipt.get("push_command_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
        ):
            errors.append("push_command_profile mismatch")
        if (
            receipt.get("remote_verification_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            errors.append("remote_verification_profile mismatch")
        if (
            receipt.get("pre_push_remote_verification_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            errors.append("pre_push_remote_verification_profile mismatch")
        if (
            receipt.get("remote_verification_output_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
        ):
            errors.append("remote_verification_output_profile mismatch")
        if (
            receipt.get("pre_push_remote_verification_output_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
        ):
            errors.append("pre_push_remote_verification_output_profile mismatch")
        if (
            receipt.get("protected_branch_profile")
            != PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
        ):
            errors.append("protected_branch_profile mismatch")
        if receipt.get("protected_branch_provider") != (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER
        ):
            errors.append("protected_branch_provider must be github")
        if receipt.get("protected_branch_ref") != "refs/heads/main":
            errors.append("protected_branch_ref must be refs/heads/main")
        if not protected_branch_policy_digest_bound:
            errors.append("protected_branch_policy_digest mismatch")
        if not protected_branch_receipt_digest_bound:
            errors.append("protected_branch_receipt_digest mismatch")
        if not protected_branch_policy_freshness_digest_bound:
            errors.append("protected_branch_policy_freshness_digest mismatch")
        if not protected_branch_provider_timestamp_digest_bound:
            errors.append("protected_branch_provider_timestamp_digest mismatch")
        if not protected_branch_provider_timestamp_replay_digest_bound:
            errors.append(
                "protected_branch_provider_timestamp_replay_digest mismatch",
            )
        if (
            receipt.get("status_check_profile")
            != PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE
        ):
            errors.append("status_check_profile mismatch")
        if receipt.get("status_check_provider") != (
            PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_PROVIDER
        ):
            errors.append("status_check_provider must be github")
        if receipt.get("status_check_result_count") != len(status_check_results):
            errors.append("status_check_result_count mismatch")
        if not status_check_results_bound:
            errors.append("status_check_results digest mismatch")
        if not status_check_suite_digest_bound:
            errors.append("status_check_suite_digest mismatch")
        if not status_check_suite_freshness_digest_bound:
            errors.append("status_check_suite_freshness_digest mismatch")
        if push_result.get("command") != push_command:
            errors.append("push command must target origin main")
        if pre_push_remote_verification_result.get("command") != (
            remote_verification_command
        ):
            errors.append("pre-push remote verification command mismatch")
        if remote_verification_result.get("command") != remote_verification_command:
            errors.append("remote verification command mismatch")
        if not push_command_digest_bound:
            errors.append("push_command_receipt_digest mismatch")
        if not pre_push_remote_verification_digest_bound:
            errors.append("pre_push_remote_verification_command_receipt_digest mismatch")
        if not pre_push_remote_verification_output_digest_bound:
            errors.append("pre_push_remote_verification_output_digest mismatch")
        if not remote_verification_digest_bound:
            errors.append("remote_verification_command_receipt_digest mismatch")
        if not publication_digest_bound:
            errors.append("publication_digest mismatch")
        if receipt.get("blocking_reasons") != expected_blocking_reasons:
            errors.append("blocking_reasons mismatch")
        if receipt.get("publication_status") != expected_status:
            errors.append("publication_status mismatch")
        if receipt.get("ready_for_github_handoff") != (
            expected_status == "published"
        ):
            errors.append("ready_for_github_handoff mismatch")
        if not receipt_digest_bound:
            errors.append("receipt_digest mismatch")
        if receipt.get("raw_execution_payload_stored") is not False:
            errors.append("raw_execution_payload_stored must be false")
        if receipt.get("raw_post_commit_publication_payload_stored") is not False:
            errors.append("raw_post_commit_publication_payload_stored must be false")
        if (
            receipt.get("raw_pre_push_remote_verification_stdout_stored")
            is not False
        ):
            errors.append(
                "raw_pre_push_remote_verification_stdout_stored must be false",
            )
        if (
            receipt.get("raw_pre_push_remote_verification_stderr_stored")
            is not False
        ):
            errors.append(
                "raw_pre_push_remote_verification_stderr_stored must be false",
            )
        if receipt.get("raw_push_stdout_stored") is not False:
            errors.append("raw_push_stdout_stored must be false")
        if receipt.get("raw_push_stderr_stored") is not False:
            errors.append("raw_push_stderr_stored must be false")
        if receipt.get("raw_remote_verification_stdout_stored") is not False:
            errors.append("raw_remote_verification_stdout_stored must be false")
        if receipt.get("raw_remote_verification_stderr_stored") is not False:
            errors.append("raw_remote_verification_stderr_stored must be false")
        if receipt.get("raw_protected_branch_provider_payload_stored") is not False:
            errors.append("raw_protected_branch_provider_payload_stored must be false")
        if (
            receipt.get("raw_protected_branch_policy_freshness_payload_stored")
            is not False
        ):
            errors.append(
                "raw_protected_branch_policy_freshness_payload_stored must be false",
            )
        if (
            receipt.get("raw_protected_branch_provider_timestamp_payload_stored")
            is not False
        ):
            errors.append(
                "raw_protected_branch_provider_timestamp_payload_stored must be false",
            )
        if (
            receipt.get(
                "raw_protected_branch_provider_timestamp_replay_guard_payload_stored",
            )
            is not False
        ):
            errors.append(
                "raw_protected_branch_provider_timestamp_replay_guard_payload_stored must be false",
            )
        if receipt.get("raw_status_check_provider_payload_stored") is not False:
            errors.append("raw_status_check_provider_payload_stored must be false")
        if receipt.get("raw_status_check_suite_freshness_payload_stored") is not False:
            errors.append(
                "raw_status_check_suite_freshness_payload_stored must be false",
            )

        return {
            "ok": not errors,
            "ready_for_github_handoff": (
                receipt.get("ready_for_github_handoff") is True
                and expected_status == "published"
                and not expected_blocking_reasons
            ),
            "errors": errors,
            "source_execution_receipt_digest_bound": (
                receipt.get("source_execution_receipt_digest_bound") is True
                and _is_sha256(receipt.get("source_execution_receipt_digest"))
            ),
            "source_execution_ready_to_apply": (
                receipt.get("source_execution_ready_to_apply") is True
            ),
            "source_execution_commit_finalization_ready": (
                receipt.get("source_execution_commit_finalization_ready") is True
            ),
            "source_execution_current_checkout_head_bound": _is_commit(
                receipt.get("source_execution_current_checkout_head"),
            ),
            "local_commit_head_bound": _is_commit(
                receipt.get("local_commit_head"),
            ),
            "local_commit_head_matches_source": (
                receipt.get("local_commit_head_matches_source") is True
            ),
            "pre_push_remote_head_matches_source": (
                receipt.get("pre_push_remote_head_matches_source") is True
            ),
            "pre_push_remote_verification_digest_bound": (
                pre_push_remote_verification_digest_bound
            ),
            "pre_push_remote_verification_passed": (
                pre_push_remote_verification_result.get("status") == "pass"
                and pre_push_remote_verification_result.get("exit_code") == 0
            ),
            "pre_push_remote_verification_output_digest_bound": (
                pre_push_remote_verification_output_digest_bound
            ),
            "pre_push_remote_verification_observed_head_matches": (
                receipt.get("pre_push_remote_verification_observed_head")
                == receipt.get("pre_push_remote_head")
            ),
            "pre_push_remote_verification_observed_ref_matches": (
                receipt.get("pre_push_remote_verification_observed_ref")
                == receipt.get("remote_ref")
            ),
            "remote_head_matches_local_commit": (
                receipt.get("remote_head_matches_local_commit") is True
            ),
            "push_command_digest_bound": push_command_digest_bound,
            "push_command_passed": (
                push_result.get("status") == "pass"
                and push_result.get("exit_code") == 0
            ),
            "remote_verification_digest_bound": (
                remote_verification_digest_bound
            ),
            "remote_verification_passed": (
                remote_verification_result.get("status") == "pass"
                and remote_verification_result.get("exit_code") == 0
            ),
            "remote_verification_output_digest_bound": (
                remote_verification_output_digest_bound
            ),
            "remote_verification_observed_head_matches": (
                receipt.get("remote_verification_observed_head")
                == receipt.get("remote_head")
            ),
            "remote_verification_observed_ref_matches": (
                receipt.get("remote_verification_observed_ref")
                == receipt.get("remote_ref")
            ),
            "protected_branch_policy_digest_bound": (
                protected_branch_policy_digest_bound
            ),
            "protected_branch_receipt_digest_bound": (
                protected_branch_receipt_digest_bound
            ),
            "protected_branch_status_protected": (
                receipt.get("protected_branch_status")
                == PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS
            ),
            "protected_branch_required_checks_bound": (
                self._protected_branch_required_checks_bound(
                    receipt.get("protected_branch_required_checks", []),
                )
            ),
            "protected_branch_policy_freshness_digest_bound": (
                protected_branch_policy_freshness_digest_bound
            ),
            "protected_branch_policy_fresh": (
                receipt.get("protected_branch_policy_freshness_status")
                == PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS
            ),
            "protected_branch_policy_freshness_window_bound": (
                0
                < _coerce_int(
                    receipt.get("protected_branch_policy_freshness_window_seconds"),
                    0,
                )
                <= PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
            ),
            "protected_branch_provider_timestamp_digest_bound": (
                protected_branch_provider_timestamp_digest_bound
            ),
            "protected_branch_provider_timestamp_signed_current": (
                receipt.get("protected_branch_provider_timestamp_status")
                == PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS
            ),
            "protected_branch_provider_timestamp_replay_digest_bound": (
                protected_branch_provider_timestamp_replay_digest_bound
            ),
            "protected_branch_provider_timestamp_unique": (
                receipt.get("protected_branch_provider_timestamp_replay_status")
                == PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS
            ),
            "status_check_commit_matches_remote": (
                receipt.get("status_check_commit_head") == receipt.get("remote_head")
            ),
            "status_check_required_checks_bound": (
                receipt.get("status_check_required_checks")
                == receipt.get("protected_branch_required_checks")
            ),
            "status_check_results_bound": status_check_results_bound,
            "status_check_all_required_passed": status_check_all_required_passed,
            "status_check_suite_digest_bound": status_check_suite_digest_bound,
            "status_check_suite_freshness_digest_bound": (
                status_check_suite_freshness_digest_bound
            ),
            "status_check_suite_fresh": (
                receipt.get("status_check_suite_freshness_status")
                == PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS
            ),
            "status_check_suite_freshness_window_bound": (
                0
                < _coerce_int(
                    receipt.get("status_check_suite_freshness_window_seconds"),
                    0,
                )
                <= PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
            ),
            "publication_digest_bound": publication_digest_bound,
            "receipt_digest_bound": receipt_digest_bound,
            "raw_publication_payload_redacted": (
                receipt.get("raw_post_commit_publication_payload_stored")
                is False
            ),
            "raw_pre_push_remote_verification_output_redacted": (
                receipt.get("raw_pre_push_remote_verification_stdout_stored")
                is False
                and receipt.get("raw_pre_push_remote_verification_stderr_stored")
                is False
                and pre_push_remote_verification_result.get("raw_stdout_stored")
                is False
                and pre_push_remote_verification_result.get("raw_stderr_stored")
                is False
            ),
            "raw_push_output_redacted": (
                receipt.get("raw_push_stdout_stored") is False
                and receipt.get("raw_push_stderr_stored") is False
                and push_result.get("raw_stdout_stored") is False
                and push_result.get("raw_stderr_stored") is False
            ),
            "raw_remote_verification_output_redacted": (
                receipt.get("raw_remote_verification_stdout_stored") is False
                and receipt.get("raw_remote_verification_stderr_stored") is False
                and remote_verification_result.get("raw_stdout_stored") is False
                and remote_verification_result.get("raw_stderr_stored") is False
            ),
            "raw_protected_branch_provider_payload_redacted": (
                receipt.get("raw_protected_branch_provider_payload_stored")
                is False
            ),
            "raw_protected_branch_policy_freshness_payload_redacted": (
                receipt.get("raw_protected_branch_policy_freshness_payload_stored")
                is False
            ),
            "raw_protected_branch_provider_timestamp_payload_redacted": (
                receipt.get("raw_protected_branch_provider_timestamp_payload_stored")
                is False
            ),
            "raw_protected_branch_provider_timestamp_replay_guard_payload_redacted": (
                receipt.get(
                    "raw_protected_branch_provider_timestamp_replay_guard_payload_stored",
                )
                is False
            ),
            "raw_status_check_provider_payload_redacted": (
                receipt.get("raw_status_check_provider_payload_stored") is False
                and all(
                    result.get("raw_status_check_payload_stored") is False
                    for result in status_check_results
                )
            ),
            "raw_status_check_suite_freshness_payload_redacted": (
                receipt.get("raw_status_check_suite_freshness_payload_stored")
                is False
            ),
        }

    def validate_worker_result_receipt(
        self,
        receipt: Mapping[str, Any],
    ) -> Dict[str, Any]:
        errors: list[str] = []
        changed_files = list(receipt.get("changed_files", []))
        workspace_marker_only_changed_files = list(
            receipt.get("workspace_marker_only_changed_files", []),
        )
        workspace_marker_diff_summaries = list(
            receipt.get("workspace_marker_diff_summaries", []),
        )
        verification_results = list(receipt.get("verification_results", []))
        expected_blocking_reasons = self._derive_blocking_reasons(receipt)
        expected_integration_decision = (
            "blocked" if expected_blocking_reasons else "accept-ready"
        )
        expected_workspace_marker_classifier_digest = (
            self._workspace_marker_classifier_digest(
                workspace_marker_diff_summaries=workspace_marker_diff_summaries,
                workspace_marker_only_changed_files=(
                    workspace_marker_only_changed_files
                ),
            )
        )
        workspace_marker_classifier_digest_bound = (
            receipt.get("workspace_marker_classifier_digest")
            == expected_workspace_marker_classifier_digest
        )
        expected_workspace_marker_hygiene_status = (
            self._workspace_marker_hygiene_status(
                changed_files=changed_files,
                workspace_marker_only_changed_files=(
                    workspace_marker_only_changed_files
                ),
            )
        )
        changed_digest_bound = (
            receipt.get("changed_file_manifest_digest")
            == self._changed_file_manifest_digest(changed_files)
        )
        workspace_marker_hygiene_digest_bound = (
            receipt.get("workspace_marker_hygiene_digest")
            == self._workspace_marker_hygiene_digest(
                changed_files=changed_files,
                workspace_marker_only_changed_files=(
                    workspace_marker_only_changed_files
                ),
                workspace_marker_hygiene_status=(
                    expected_workspace_marker_hygiene_status
                ),
                workspace_marker_classifier_digest=(
                    expected_workspace_marker_classifier_digest
                ),
            )
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
                remote_source_revocation_timestamp_replay_guard_profile=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_replay_guard_profile",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_nonce_ref=str(
                    receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
                ),
                remote_source_revocation_timestamp_previous_nonce_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_previous_nonce_digest",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_replay_status=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_replay_status",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_replay_guard_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_replay_guard_digest",
                        "",
                    ),
                ),
                remote_source_content_profile=str(
                    receipt.get("remote_source_content_profile", ""),
                ),
                remote_source_content_ref=str(
                    receipt.get("remote_source_content_ref", ""),
                ),
                remote_source_content_status=str(
                    receipt.get("remote_source_content_status", ""),
                ),
                remote_source_head_commit=str(
                    receipt.get("remote_source_head_commit", ""),
                ),
                remote_source_tree_digest=str(
                    receipt.get("remote_source_tree_digest", ""),
                ),
                remote_source_diff_digest=str(
                    receipt.get("remote_source_diff_digest", ""),
                ),
                remote_source_content_digest=str(
                    receipt.get("remote_source_content_digest", ""),
                ),
                remote_source_ancestry_profile=str(
                    receipt.get("remote_source_ancestry_profile", ""),
                ),
                remote_source_base_commit=str(
                    receipt.get("remote_source_base_commit", ""),
                ),
                remote_source_merge_base_commit=str(
                    receipt.get("remote_source_merge_base_commit", ""),
                ),
                remote_source_ancestry_status=str(
                    receipt.get("remote_source_ancestry_status", ""),
                ),
                remote_source_ancestry_digest=str(
                    receipt.get("remote_source_ancestry_digest", ""),
                ),
            )
        )
        if receipt.get("source_system") == PARALLEL_CODEX_REMOTE_SOURCE_SYSTEM:
            remote_source_content_digest_bound = (
                receipt.get("remote_source_content_digest")
                == self._remote_source_content_digest(
                    remote_source_content_ref=str(
                        receipt.get("remote_source_content_ref", ""),
                    ),
                    remote_source_content_status=str(
                        receipt.get("remote_source_content_status", ""),
                    ),
                    remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                    remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                    remote_source_head_commit=str(
                        receipt.get("remote_source_head_commit", ""),
                    ),
                    remote_source_tree_digest=str(
                        receipt.get("remote_source_tree_digest", ""),
                    ),
                    remote_source_diff_digest=str(
                        receipt.get("remote_source_diff_digest", ""),
                    ),
                )
            )
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
                    remote_source_revocation_timestamp_nonce_ref=str(
                        receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
                    ),
                    remote_source_revocation_timestamp_previous_nonce_digest=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_previous_nonce_digest",
                            "",
                        ),
                    ),
                )
            )
            remote_source_revocation_timestamp_replay_guard_digest_bound = (
                receipt.get("remote_source_revocation_timestamp_replay_guard_digest")
                == self._remote_source_revocation_timestamp_replay_guard_digest(
                    remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                    remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                    remote_source_revocation_timestamp_nonce_ref=str(
                        receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
                    ),
                    remote_source_revocation_timestamp_previous_nonce_digest=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_previous_nonce_digest",
                            "",
                        ),
                    ),
                    remote_source_revocation_timestamp_signature_digest=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_signature_digest",
                            "",
                        ),
                    ),
                    remote_source_revocation_timestamp_replay_status=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_replay_status",
                            "",
                        ),
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
                    remote_source_revocation_timestamp_replay_guard_digest=str(
                        receipt.get(
                            "remote_source_revocation_timestamp_replay_guard_digest",
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
            remote_source_ancestry_digest_bound = (
                receipt.get("remote_source_ancestry_digest")
                == self._remote_source_ancestry_digest(
                    remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                    remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                    worker_base_commit=str(receipt.get("worker_base_commit", "")),
                    remote_source_head_commit=str(
                        receipt.get("remote_source_head_commit", ""),
                    ),
                    remote_source_base_commit=str(
                        receipt.get("remote_source_base_commit", ""),
                    ),
                    remote_source_merge_base_commit=str(
                        receipt.get("remote_source_merge_base_commit", ""),
                    ),
                    remote_source_ancestry_status=str(
                        receipt.get("remote_source_ancestry_status", ""),
                    ),
                    remote_source_content_digest=str(
                        receipt.get("remote_source_content_digest", ""),
                    ),
                )
            )
        else:
            remote_source_content_digest_bound = (
                receipt.get("remote_source_content_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_content_ref") == ""
                and receipt.get("remote_source_content_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get("remote_source_head_commit") == ""
                and receipt.get("remote_source_tree_digest") == ""
                and receipt.get("remote_source_diff_digest") == ""
                and receipt.get("remote_source_content_digest") == ""
                and receipt.get("remote_source_content_bound") is True
            )
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
                and receipt.get("remote_source_revocation_timestamp_replay_guard_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_revocation_timestamp_nonce_ref") == ""
                and receipt.get(
                    "remote_source_revocation_timestamp_previous_nonce_digest"
                )
                == ""
                and receipt.get("remote_source_revocation_timestamp_replay_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get(
                    "remote_source_revocation_timestamp_replay_guard_digest"
                )
                == ""
            )
            remote_source_revocation_timestamp_signature_bound = (
                remote_source_revocation_timestamp_digest_bound
            )
            remote_source_revocation_timestamp_replay_guard_digest_bound = (
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
            remote_source_ancestry_digest_bound = (
                receipt.get("remote_source_ancestry_profile")
                == PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                and receipt.get("remote_source_base_commit") == ""
                and receipt.get("remote_source_merge_base_commit") == ""
                and receipt.get("remote_source_ancestry_status")
                == PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                and receipt.get("remote_source_ancestry_digest") == ""
                and receipt.get("remote_source_ancestry_bound") is True
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
        raw_workspace_marker_payload_redacted = (
            receipt.get("raw_workspace_marker_payload_stored") is False
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
            and remote_source_revocation_timestamp_replay_guard_digest_bound
            and remote_source_content_digest_bound
            and remote_source_ancestry_digest_bound
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
        if not remote_source_revocation_timestamp_replay_guard_digest_bound:
            errors.append(
                "remote_source_revocation_timestamp_replay_guard_digest mismatch"
            )
        if not remote_source_content_digest_bound:
            errors.append("remote_source_content_digest mismatch")
        if not remote_source_ancestry_digest_bound:
            errors.append("remote_source_ancestry_digest mismatch")
        if receipt.get("remote_source_content_bound") is not remote_source_content_digest_bound:
            errors.append("remote_source_content_bound mismatch")
        if receipt.get("remote_source_ancestry_bound") is not remote_source_ancestry_digest_bound:
            errors.append("remote_source_ancestry_bound mismatch")
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
        if receipt.get("workspace_marker_only_change_count") != len(
            workspace_marker_only_changed_files,
        ):
            errors.append("workspace_marker_only_change_count mismatch")
        if receipt.get("workspace_marker_diff_summary_count") != len(
            workspace_marker_diff_summaries,
        ):
            errors.append("workspace_marker_diff_summary_count mismatch")
        if (
            receipt.get("workspace_marker_hygiene_status")
            != expected_workspace_marker_hygiene_status
        ):
            errors.append("workspace_marker_hygiene_status mismatch")
        if not workspace_marker_classifier_digest_bound:
            errors.append("workspace_marker_classifier_digest mismatch")
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
        if not workspace_marker_hygiene_digest_bound:
            errors.append("workspace_marker_hygiene_digest mismatch")
        if not receipt_digest_bound:
            errors.append("receipt_digest mismatch")
        if not (
            raw_patch_payload_redacted
            and raw_upstream_payload_redacted
            and raw_worker_identity_payload_redacted
            and raw_workspace_marker_payload_redacted
            and raw_remote_metadata_payload_redacted
            and raw_remote_revocation_payload_redacted
            and raw_remote_revocation_freshness_payload_redacted
            and raw_remote_revocation_timestamp_payload_redacted
            and receipt.get(
                "raw_remote_revocation_timestamp_replay_guard_payload_stored"
            )
            is False
            and receipt.get("raw_remote_source_content_payload_stored") is False
            and receipt.get("raw_remote_source_ancestry_payload_stored") is False
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
            "workspace_marker_hygiene_digest_bound": (
                workspace_marker_hygiene_digest_bound
            ),
            "workspace_marker_classifier_digest_bound": (
                workspace_marker_classifier_digest_bound
            ),
            "workspace_marker_classifier_marker_only_detected": bool(
                self._workspace_marker_classifier_marker_files(
                    workspace_marker_diff_summaries,
                )
            ),
            "workspace_marker_hygiene_clean": (
                receipt.get("workspace_marker_hygiene_status")
                == PARALLEL_CODEX_WORKSPACE_MARKER_CLEAN_STATUS
            ),
            "workspace_marker_only_change_blocked": (
                receipt.get("workspace_marker_hygiene_status")
                == PARALLEL_CODEX_WORKSPACE_MARKER_BLOCKED_STATUS
            ),
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
            "remote_source_revocation_timestamp_replay_guard_digest_bound": (
                remote_source_revocation_timestamp_replay_guard_digest_bound
            ),
            "remote_source_content_digest_bound": remote_source_content_digest_bound,
            "remote_source_content_bound": (
                receipt.get("remote_source_content_bound") is True
            ),
            "remote_source_ancestry_digest_bound": (
                remote_source_ancestry_digest_bound
            ),
            "remote_source_ancestry_bound": (
                receipt.get("remote_source_ancestry_bound") is True
            ),
            "remote_source_ancestry_status_bound": (
                receipt.get("remote_source_ancestry_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
            ),
            "remote_source_base_commit_matches_worker": (
                receipt.get("remote_source_base_commit", "")
                in {"", receipt.get("worker_base_commit")}
                and receipt.get("remote_source_merge_base_commit", "")
                in {"", receipt.get("worker_base_commit")}
            ),
            "remote_source_content_status_bound": (
                receipt.get("remote_source_content_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
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
            "remote_source_revocation_timestamp_unique": (
                receipt.get("remote_source_revocation_timestamp_replay_status")
                in {
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS,
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS,
                }
            ),
            "receipt_digest_bound": receipt_digest_bound,
            "raw_patch_payload_redacted": raw_patch_payload_redacted,
            "raw_upstream_payload_redacted": raw_upstream_payload_redacted,
            "raw_worker_identity_payload_redacted": raw_worker_identity_payload_redacted,
            "raw_workspace_marker_payload_redacted": (
                raw_workspace_marker_payload_redacted
            ),
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
            "raw_remote_revocation_timestamp_replay_guard_payload_redacted": (
                receipt.get(
                    "raw_remote_revocation_timestamp_replay_guard_payload_stored"
                )
                is False
            ),
            "raw_remote_source_content_payload_redacted": (
                receipt.get("raw_remote_source_content_payload_stored") is False
            ),
            "raw_remote_source_ancestry_payload_redacted": (
                receipt.get("raw_remote_source_ancestry_payload_stored") is False
            ),
            "raw_transcript_payload_redacted": raw_transcript_payload_redacted,
            "raw_verification_payload_redacted": raw_verification_payload_redacted,
        }

    def _normalize_batch_receipts(
        self,
        *,
        receipts: Sequence[Mapping[str, Any]],
        main_checkout_head: str,
    ) -> list[Dict[str, Any]]:
        normalized: list[Dict[str, Any]] = []
        for index, receipt in enumerate(receipts):
            validation = self.validate_worker_result_receipt(receipt)
            receipt_id = str(receipt.get("receipt_id", "")).strip()
            receipt_ref = str(receipt.get("receipt_ref", "")).strip()
            if not receipt_ref:
                receipt_ref = (
                    f"receipt://parallel-codex/missing-worker-result-{index:03d}"
                )
            receipt_digest = str(receipt.get("receipt_digest", "")).strip()
            if not _is_sha256(receipt_digest):
                receipt_digest = sha256_text(
                    canonical_json(
                        {
                            "receipt_ref": receipt_ref,
                            "receipt_id": receipt_id,
                            "index": index,
                        }
                    )
                )
            input_main_head = str(receipt.get("main_checkout_head", "")).strip()
            accept_ready_for_batch = (
                validation["ok"]
                and validation["ready_for_main_checkout"]
                and input_main_head == main_checkout_head
                and bool(receipt_ref)
                and _is_sha256(receipt_digest)
            )
            normalized.append(
                {
                    "receipt_ref": receipt_ref,
                    "receipt_digest": receipt_digest,
                    "worker_id": str(receipt.get("worker_id", "")).strip(),
                    "source_system": str(receipt.get("source_system", "")).strip(),
                    "main_checkout_head": input_main_head,
                    "integration_decision": str(
                        receipt.get("integration_decision", ""),
                    ).strip(),
                    "accept_ready_for_batch": accept_ready_for_batch,
                    "changed_files": _dedupe_strings(
                        list(receipt.get("changed_files", [])),
                    ),
                }
            )
        return normalized

    @staticmethod
    def _integration_batch_changed_file_owners(
        ordered_receipts: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        owners: list[Dict[str, Any]] = []
        for receipt in ordered_receipts:
            for changed_file in receipt.get("changed_files", []):
                owners.append(
                    {
                        "file_path": changed_file,
                        "receipt_ref": receipt.get("receipt_ref", ""),
                        "receipt_digest": receipt.get("receipt_digest", ""),
                        "worker_id": receipt.get("worker_id", ""),
                        "source_system": receipt.get("source_system", ""),
                    }
                )
        return sorted(
            owners,
            key=lambda owner: (
                str(owner.get("file_path", "")),
                str(owner.get("receipt_digest", "")),
                str(owner.get("receipt_ref", "")),
            ),
        )

    @staticmethod
    def _integration_batch_changed_file_conflicts(
        changed_file_owners: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        owners_by_file: Dict[str, list[Mapping[str, Any]]] = {}
        for owner in changed_file_owners:
            owners_by_file.setdefault(str(owner.get("file_path", "")), []).append(owner)
        conflicts: list[Dict[str, Any]] = []
        for file_path, owners in sorted(owners_by_file.items()):
            if len(owners) <= 1:
                continue
            conflicts.append(
                {
                    "file_path": file_path,
                    "receipt_refs": [
                        str(owner.get("receipt_ref", "")) for owner in owners
                    ],
                    "receipt_digests": [
                        str(owner.get("receipt_digest", "")) for owner in owners
                    ],
                    "worker_ids": [str(owner.get("worker_id", "")) for owner in owners],
                }
            )
        return conflicts

    @staticmethod
    def _integration_batch_receipt_set_digest(
        *,
        input_receipt_refs: Sequence[str],
        input_receipt_digests: Sequence[str],
    ) -> str:
        receipt_pairs = sorted(
            [
                {"receipt_ref": ref, "receipt_digest": digest}
                for ref, digest in zip(input_receipt_refs, input_receipt_digests)
            ],
            key=lambda item: (item["receipt_digest"], item["receipt_ref"]),
        )
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE,
                    "receipt_pairs": receipt_pairs,
                }
            )
        )

    @staticmethod
    def _integration_batch_ordered_receipt_digest(
        *,
        ordered_receipt_refs: Sequence[str],
        ordered_receipt_digests: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_INTEGRATION_BATCH_ORDERING_PROFILE,
                    "ordered_receipt_refs": list(ordered_receipt_refs),
                    "ordered_receipt_digests": list(ordered_receipt_digests),
                }
            )
        )

    @staticmethod
    def _integration_batch_changed_file_owner_manifest_digest(
        *,
        changed_file_owners: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE
                    ),
                    "changed_file_owners": list(changed_file_owners),
                }
            )
        )

    @staticmethod
    def _integration_batch_quarantined_receipt_digest(
        *,
        quarantined_receipt_refs: Sequence[str],
        quarantined_receipt_digests: Sequence[str],
    ) -> str:
        receipt_pairs = sorted(
            [
                {"receipt_ref": ref, "receipt_digest": digest}
                for ref, digest in zip(
                    quarantined_receipt_refs,
                    quarantined_receipt_digests,
                )
            ],
            key=lambda item: (item["receipt_digest"], item["receipt_ref"]),
        )
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE
                    ),
                    "quarantined_receipt_pairs": receipt_pairs,
                }
            )
        )

    @staticmethod
    def _integration_batch_conflict_digest(
        *,
        changed_file_conflicts: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_BATCH_CONFLICT_PROFILE
                    ),
                    "changed_file_conflicts": list(changed_file_conflicts),
                }
            )
        )

    def _integration_execution_apply_steps(
        self,
        *,
        ordered_receipt_refs: Sequence[str],
        ordered_receipt_digests: Sequence[str],
        changed_file_owners: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        files_by_receipt: Dict[str, list[str]] = {}
        for owner in changed_file_owners:
            receipt_ref = str(owner.get("receipt_ref", "")).strip()
            file_path = str(owner.get("file_path", "")).strip()
            if receipt_ref and file_path:
                files_by_receipt.setdefault(receipt_ref, []).append(file_path)

        steps: list[Dict[str, Any]] = []
        for index, (receipt_ref, receipt_digest) in enumerate(
            zip(ordered_receipt_refs, ordered_receipt_digests),
            start=1,
        ):
            changed_files = sorted(_dedupe_strings(files_by_receipt.get(receipt_ref, [])))
            changed_file_manifest_digest = self._changed_file_manifest_digest(
                changed_files,
            )
            patch_artifact_ref = self._integration_execution_patch_artifact_ref(
                receipt_ref,
            )
            patch_artifact_path = self._integration_execution_patch_artifact_path(
                receipt_ref,
            )
            step = {
                "step_index": index,
                "receipt_ref": receipt_ref,
                "receipt_digest": receipt_digest,
                "changed_files": changed_files,
                "changed_file_count": len(changed_files),
                "changed_file_manifest_digest": changed_file_manifest_digest,
                "patch_artifact_profile": (
                    PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
                ),
                "patch_artifact_source": (
                    PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
                ),
                "patch_artifact_ref": patch_artifact_ref,
                "patch_artifact_path": patch_artifact_path,
                "patch_artifact_command_target": patch_artifact_path,
                "patch_artifact_digest": (
                    self._integration_execution_patch_artifact_digest(
                        receipt_ref=receipt_ref,
                        receipt_digest=receipt_digest,
                        changed_file_manifest_digest=changed_file_manifest_digest,
                        patch_artifact_ref=patch_artifact_ref,
                        patch_artifact_path=patch_artifact_path,
                        patch_artifact_source=(
                            PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
                        ),
                        patch_artifact_profile=(
                            PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
                        ),
                    )
                ),
                "raw_patch_payload_stored": False,
            }
            step["apply_step_digest"] = self._integration_execution_apply_step_digest(
                step,
            )
            steps.append(step)
        return steps

    @staticmethod
    def _integration_execution_apply_step_digest(
        step: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE
                    ),
                    "step_index": step.get("step_index", 0),
                    "receipt_ref": step.get("receipt_ref", ""),
                    "receipt_digest": step.get("receipt_digest", ""),
                    "changed_files": list(step.get("changed_files", [])),
                    "changed_file_manifest_digest": step.get(
                        "changed_file_manifest_digest",
                        "",
                    ),
                    "patch_artifact_profile": step.get("patch_artifact_profile", ""),
                    "patch_artifact_source": step.get("patch_artifact_source", ""),
                    "patch_artifact_ref": step.get("patch_artifact_ref", ""),
                    "patch_artifact_path": step.get("patch_artifact_path", ""),
                    "patch_artifact_command_target": step.get(
                        "patch_artifact_command_target",
                        "",
                    ),
                    "patch_artifact_digest": step.get("patch_artifact_digest", ""),
                }
            )
        )

    @staticmethod
    def _integration_execution_patch_artifact_ref(receipt_ref: str) -> str:
        digest = sha256_text(receipt_ref)
        return f"patch://parallel-codex/{digest[:12]}"

    @staticmethod
    def _integration_execution_patch_artifact_path(receipt_ref: str) -> str:
        digest = sha256_text(receipt_ref)
        return f"artifacts/parallel-codex/{digest[:12]}.patch"

    @staticmethod
    def _integration_execution_patch_artifact_digest(
        *,
        receipt_ref: str,
        receipt_digest: str,
        changed_file_manifest_digest: str,
        patch_artifact_ref: str,
        patch_artifact_path: str,
        patch_artifact_source: str,
        patch_artifact_profile: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
                    ),
                    "receipt_ref": receipt_ref,
                    "receipt_digest": receipt_digest,
                    "changed_file_manifest_digest": changed_file_manifest_digest,
                    "patch_artifact_ref": patch_artifact_ref,
                    "patch_artifact_path": patch_artifact_path,
                    "patch_artifact_source": patch_artifact_source,
                    "patch_artifact_profile": patch_artifact_profile,
                    "raw_patch_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _integration_execution_apply_plan_digest(
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_APPLY_PLAN_PROFILE
                    ),
                    "apply_steps": [
                        {
                            "step_index": step.get("step_index", 0),
                            "receipt_ref": step.get("receipt_ref", ""),
                            "receipt_digest": step.get("receipt_digest", ""),
                            "changed_file_manifest_digest": step.get(
                                "changed_file_manifest_digest",
                                "",
                            ),
                            "patch_artifact_profile": step.get(
                                "patch_artifact_profile",
                                "",
                            ),
                            "patch_artifact_source": step.get(
                                "patch_artifact_source",
                                "",
                            ),
                            "patch_artifact_ref": step.get("patch_artifact_ref", ""),
                            "patch_artifact_path": step.get(
                                "patch_artifact_path",
                                "",
                            ),
                            "patch_artifact_command_target": step.get(
                                "patch_artifact_command_target",
                                "",
                            ),
                            "patch_artifact_digest": step.get(
                                "patch_artifact_digest",
                                "",
                            ),
                            "apply_step_digest": step.get("apply_step_digest", ""),
                        }
                        for step in apply_steps
                    ],
                }
            )
        )

    @staticmethod
    def _integration_execution_patch_artifact_manifest_digest(
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
                    ),
                    "patch_artifacts": [
                        {
                            "step_index": step.get("step_index", 0),
                            "receipt_ref": step.get("receipt_ref", ""),
                            "receipt_digest": step.get("receipt_digest", ""),
                            "patch_artifact_profile": step.get(
                                "patch_artifact_profile",
                                "",
                            ),
                            "patch_artifact_source": step.get(
                                "patch_artifact_source",
                                "",
                            ),
                            "patch_artifact_ref": step.get("patch_artifact_ref", ""),
                            "patch_artifact_path": step.get(
                                "patch_artifact_path",
                                "",
                            ),
                            "patch_artifact_digest": step.get(
                                "patch_artifact_digest",
                                "",
                            ),
                            "raw_patch_payload_stored": False,
                        }
                        for step in apply_steps
                    ],
                }
            )
        )

    @staticmethod
    def _integration_execution_repo_local_patch_artifact_count(
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> int:
        return sum(
            1
            for step in apply_steps
            if step.get("patch_artifact_source")
            == PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
        )

    @staticmethod
    def _integration_execution_repo_local_patch_artifacts_bound(
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> bool:
        if not apply_steps:
            return False
        for step in apply_steps:
            path = str(step.get("patch_artifact_path", ""))
            if (
                step.get("patch_artifact_profile")
                != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
                or step.get("patch_artifact_source")
                != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
                or not path.startswith("artifacts/parallel-codex/")
                or not path.endswith(".patch")
                or step.get("patch_artifact_command_target") != path
                or step.get("raw_patch_payload_stored") is not False
                or not _is_sha256(step.get("patch_artifact_digest"))
            ):
                return False
        return True

    @staticmethod
    def _patch_artifact_cleanup_artifact_paths(
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> list[str]:
        return sorted(
            _dedupe_strings(
                [
                    str(step.get("patch_artifact_path", "")).strip()
                    for step in apply_steps
                    if step.get("patch_artifact_source")
                    == PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_SOURCE
                ]
            )
        )

    @staticmethod
    def _patch_artifact_cleanup_digest(
        *,
        patch_artifact_cleanup_ref: str,
        patch_artifact_cleanup_status: str,
        patch_artifact_cleanup_artifact_paths: Sequence[str],
        patch_artifact_cleanup_artifact_count: int,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        checkout_mutation_event_digest: str,
        checkout_mutation_post_apply_head: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE
                    ),
                    "patch_artifact_cleanup_ref": patch_artifact_cleanup_ref,
                    "patch_artifact_cleanup_status": patch_artifact_cleanup_status,
                    "patch_artifact_cleanup_artifact_paths": list(
                        patch_artifact_cleanup_artifact_paths,
                    ),
                    "patch_artifact_cleanup_artifact_count": (
                        patch_artifact_cleanup_artifact_count
                    ),
                    "patch_artifact_manifest_digest": patch_artifact_manifest_digest,
                    "pre_apply_dry_run_manifest_digest": (
                        pre_apply_dry_run_manifest_digest
                    ),
                    "checkout_mutation_event_digest": checkout_mutation_event_digest,
                    "checkout_mutation_post_apply_head": (
                        checkout_mutation_post_apply_head
                    ),
                    "raw_patch_artifact_cleanup_payload_stored": False,
                }
            )
        )

    def _normalize_patch_artifact_cleanup_receipt(
        self,
        *,
        patch_artifact_cleanup_receipt: Mapping[str, Any] | None,
        apply_steps: Sequence[Mapping[str, Any]],
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        checkout_mutation_event_digest: str,
        checkout_mutation_post_apply_head: str,
    ) -> Dict[str, Any]:
        source = dict(patch_artifact_cleanup_receipt or {})
        expected_artifact_paths = self._patch_artifact_cleanup_artifact_paths(
            apply_steps=apply_steps,
        )
        artifact_paths = sorted(
            _dedupe_strings(
                [
                    str(path).strip()
                    for path in source.get(
                        "patch_artifact_cleanup_artifact_paths",
                        expected_artifact_paths,
                    )
                ]
            )
        )
        artifact_count = _coerce_int(
            source.get("patch_artifact_cleanup_artifact_count"),
            len(artifact_paths),
        )
        status = str(
            source.get("patch_artifact_cleanup_status", "removed"),
        ).strip()
        cleanup_ref = str(source.get("patch_artifact_cleanup_ref", "")).strip()
        if not cleanup_ref:
            cleanup_ref = (
                "cleanup://parallel-codex/"
                f"{sha256_text(patch_artifact_manifest_digest + checkout_mutation_event_digest)[:12]}"
            )
        expected_digest = self._patch_artifact_cleanup_digest(
            patch_artifact_cleanup_ref=cleanup_ref,
            patch_artifact_cleanup_status=status,
            patch_artifact_cleanup_artifact_paths=artifact_paths,
            patch_artifact_cleanup_artifact_count=artifact_count,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            checkout_mutation_event_digest=checkout_mutation_event_digest,
            checkout_mutation_post_apply_head=checkout_mutation_post_apply_head,
        )
        cleanup_digest = str(
            source.get("patch_artifact_cleanup_digest", ""),
        ).strip()
        if not _is_sha256(cleanup_digest):
            cleanup_digest = expected_digest
        artifact_paths_bound = artifact_paths == expected_artifact_paths
        artifact_count_bound = artifact_count == len(expected_artifact_paths)
        manifest_digest_bound = _is_sha256(patch_artifact_manifest_digest)
        pre_apply_digest_bound = _is_sha256(pre_apply_dry_run_manifest_digest)
        checkout_mutation_event_bound = _is_sha256(checkout_mutation_event_digest)
        post_apply_head_bound = _is_commit(checkout_mutation_post_apply_head)
        cleanup_verified = (
            status == "removed"
            and bool(expected_artifact_paths)
            and cleanup_digest == expected_digest
            and artifact_paths_bound
            and artifact_count_bound
            and manifest_digest_bound
            and pre_apply_digest_bound
            and checkout_mutation_event_bound
            and post_apply_head_bound
            and source.get("raw_patch_artifact_cleanup_payload_stored", False)
            is False
        )
        return {
            "patch_artifact_cleanup_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE
            ),
            "patch_artifact_cleanup_status": status,
            "patch_artifact_cleanup_ref": cleanup_ref,
            "patch_artifact_cleanup_digest": cleanup_digest,
            "patch_artifact_cleanup_artifact_paths": artifact_paths,
            "patch_artifact_cleanup_artifact_count": artifact_count,
            "patch_artifact_cleanup_artifact_paths_bound": artifact_paths_bound,
            "patch_artifact_cleanup_artifact_count_bound": artifact_count_bound,
            "patch_artifact_cleanup_manifest_digest_bound": manifest_digest_bound,
            "patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound": (
                pre_apply_digest_bound
            ),
            "patch_artifact_cleanup_checkout_mutation_event_digest_bound": (
                checkout_mutation_event_bound
            ),
            "patch_artifact_cleanup_post_apply_head_bound": post_apply_head_bound,
            "patch_artifact_cleanup_verified": cleanup_verified,
            "raw_patch_artifact_cleanup_payload_stored": False,
        }

    def _normalize_pre_apply_dry_run_results(
        self,
        pre_apply_dry_run_results: Sequence[Mapping[str, Any]] | None,
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> list[Dict[str, Any]]:
        source_results = (
            list(pre_apply_dry_run_results)
            if pre_apply_dry_run_results is not None
            else [
                {
                    "step_index": step.get("step_index", index),
                    "receipt_ref": step.get("receipt_ref", ""),
                    "receipt_digest": step.get("receipt_digest", ""),
                    "patch_artifact_profile": step.get("patch_artifact_profile", ""),
                    "patch_artifact_source": step.get("patch_artifact_source", ""),
                    "patch_artifact_ref": step.get("patch_artifact_ref", ""),
                    "patch_artifact_path": step.get("patch_artifact_path", ""),
                    "patch_artifact_digest": step.get("patch_artifact_digest", ""),
                    "patch_artifact_command_target": step.get(
                        "patch_artifact_command_target",
                        "",
                    ),
                    "command": (
                        "git apply --check "
                        f"{step.get('patch_artifact_command_target', '')}"
                    ),
                    "status": "pass",
                    "exit_code": 0,
                    "stdout_excerpt": "pre-apply dry run passed",
                    "stderr_excerpt": "",
                }
                for index, step in enumerate(apply_steps, start=1)
            ]
        )
        step_by_index = {
            int(step.get("step_index", index)): step
            for index, step in enumerate(apply_steps, start=1)
        }
        normalized: list[Dict[str, Any]] = []
        for index, result in enumerate(source_results, start=1):
            step_index = _coerce_int(result.get("step_index"), index)
            step = step_by_index.get(step_index, {})
            stdout_digest = str(result.get("stdout_digest", "")).strip()
            stderr_digest = str(result.get("stderr_digest", "")).strip()
            patch_artifact_ref = str(
                result.get("patch_artifact_ref", step.get("patch_artifact_ref", "")),
            ).strip()
            patch_artifact_path = str(
                result.get(
                    "patch_artifact_path",
                    step.get("patch_artifact_path", ""),
                ),
            ).strip()
            patch_artifact_profile = str(
                result.get(
                    "patch_artifact_profile",
                    step.get("patch_artifact_profile", ""),
                ),
            ).strip()
            patch_artifact_source = str(
                result.get(
                    "patch_artifact_source",
                    step.get("patch_artifact_source", ""),
                ),
            ).strip()
            patch_artifact_command_target = str(
                result.get(
                    "patch_artifact_command_target",
                    step.get("patch_artifact_command_target", ""),
                ),
            ).strip()
            patch_artifact_digest = str(
                result.get(
                    "patch_artifact_digest",
                    step.get("patch_artifact_digest", ""),
                ),
            ).strip()
            if not _is_sha256(stdout_digest):
                stdout_digest = sha256_text(str(result.get("stdout_excerpt", "")))
            if not _is_sha256(stderr_digest):
                stderr_digest = sha256_text(str(result.get("stderr_excerpt", "")))
            if not _is_sha256(patch_artifact_digest):
                patch_artifact_digest = str(step.get("patch_artifact_digest", ""))
            command = str(result.get("command", "")).strip()
            if not command:
                command = f"git apply --check {patch_artifact_command_target}"
            normalized_result = {
                "step_index": step_index,
                "receipt_ref": str(
                    result.get("receipt_ref", step.get("receipt_ref", "")),
                ).strip(),
                "receipt_digest": str(
                    result.get("receipt_digest", step.get("receipt_digest", "")),
                ).strip(),
                "command_profile": (
                    PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE
                ),
                "patch_artifact_profile": patch_artifact_profile,
                "patch_artifact_source": patch_artifact_source,
                "patch_artifact_ref": patch_artifact_ref,
                "patch_artifact_path": patch_artifact_path,
                "patch_artifact_command_target": patch_artifact_command_target,
                "patch_artifact_digest": patch_artifact_digest,
                "patch_artifact_digest_bound": (
                    patch_artifact_profile == step.get("patch_artifact_profile", "")
                    and patch_artifact_source == step.get("patch_artifact_source", "")
                    and patch_artifact_ref == step.get("patch_artifact_ref", "")
                    and patch_artifact_path == step.get("patch_artifact_path", "")
                    and patch_artifact_command_target
                    == step.get("patch_artifact_command_target", "")
                    and patch_artifact_digest == step.get("patch_artifact_digest", "")
                ),
                "command": command,
                "status": str(result.get("status", "")).strip(),
                "exit_code": _coerce_int(result.get("exit_code"), 0),
                "stdout_digest": stdout_digest,
                "stderr_digest": stderr_digest,
                "raw_patch_payload_stored": False,
                "raw_stdout_stored": False,
                "raw_stderr_stored": False,
            }
            command_receipt_digest = str(
                result.get("command_receipt_digest", ""),
            ).strip()
            if not _is_sha256(command_receipt_digest):
                command_receipt_digest = (
                    self._pre_apply_dry_run_command_receipt_digest(
                        normalized_result,
                    )
                )
            normalized_result["command_receipt_digest"] = command_receipt_digest
            normalized.append(normalized_result)
        return normalized

    @staticmethod
    def _pre_apply_dry_run_command_receipt_digest(
        result: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE
                    ),
                    "step_index": result.get("step_index", 0),
                    "receipt_ref": result.get("receipt_ref", ""),
                    "receipt_digest": result.get("receipt_digest", ""),
                    "patch_artifact_profile": result.get(
                        "patch_artifact_profile",
                        "",
                    ),
                    "patch_artifact_source": result.get(
                        "patch_artifact_source",
                        "",
                    ),
                    "patch_artifact_ref": result.get("patch_artifact_ref", ""),
                    "patch_artifact_path": result.get("patch_artifact_path", ""),
                    "patch_artifact_command_target": result.get(
                        "patch_artifact_command_target",
                        "",
                    ),
                    "patch_artifact_digest": result.get("patch_artifact_digest", ""),
                    "command": result.get("command", ""),
                    "status": result.get("status", ""),
                    "exit_code": result.get("exit_code", 0),
                    "stdout_digest": result.get("stdout_digest", ""),
                    "stderr_digest": result.get("stderr_digest", ""),
                    "raw_patch_payload_stored": False,
                    "raw_stdout_stored": False,
                    "raw_stderr_stored": False,
                }
            )
        )

    @staticmethod
    def _pre_apply_dry_run_manifest_digest(
        pre_apply_dry_run_results: Sequence[Mapping[str, Any]],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE,
                    "pre_apply_dry_run_results": [
                        {
                            "step_index": result.get("step_index", 0),
                            "receipt_ref": result.get("receipt_ref", ""),
                            "receipt_digest": result.get("receipt_digest", ""),
                            "command_profile": result.get("command_profile", ""),
                            "patch_artifact_profile": result.get(
                                "patch_artifact_profile",
                                "",
                            ),
                            "patch_artifact_source": result.get(
                                "patch_artifact_source",
                                "",
                            ),
                            "patch_artifact_ref": result.get(
                                "patch_artifact_ref",
                                "",
                            ),
                            "patch_artifact_path": result.get(
                                "patch_artifact_path",
                                "",
                            ),
                            "patch_artifact_command_target": result.get(
                                "patch_artifact_command_target",
                                "",
                            ),
                            "patch_artifact_digest": result.get(
                                "patch_artifact_digest",
                                "",
                            ),
                            "patch_artifact_digest_bound": result.get(
                                "patch_artifact_digest_bound",
                                False,
                            ),
                            "command": result.get("command", ""),
                            "status": result.get("status", ""),
                            "exit_code": result.get("exit_code", 0),
                            "stdout_digest": result.get("stdout_digest", ""),
                            "stderr_digest": result.get("stderr_digest", ""),
                            "command_receipt_digest": result.get(
                                "command_receipt_digest",
                                "",
                            ),
                        }
                        for result in pre_apply_dry_run_results
                    ],
                }
            )
        )

    def _post_apply_verification_context_digest(
        self,
        *,
        source_batch_receipt_digest: str,
        current_checkout_head: str,
        apply_plan_digest: str,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        post_apply_verification_manifest_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE
                    ),
                    "source_batch_receipt_digest": source_batch_receipt_digest,
                    "current_checkout_head": current_checkout_head,
                    "apply_plan_digest": apply_plan_digest,
                    "patch_artifact_manifest_digest": (
                        patch_artifact_manifest_digest
                    ),
                    "pre_apply_dry_run_manifest_digest": (
                        pre_apply_dry_run_manifest_digest
                    ),
                    "post_apply_verification_manifest_digest": (
                        post_apply_verification_manifest_digest
                    ),
                    "required_verifications": list(
                        self._policy.required_verifications,
                    ),
                    "raw_verification_payload_stored": False,
                }
            )
        )

    def _normalize_checkout_mutation_attestation(
        self,
        *,
        checkout_mutation_attestation: Mapping[str, Any] | None,
        source_batch_receipt_digest: str,
        current_checkout_head: str,
        apply_plan_digest: str,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        post_apply_verification_context_digest: str,
        changed_file_owner_manifest_digest: str,
    ) -> Dict[str, Any]:
        source = dict(checkout_mutation_attestation or {})
        attestation_source = str(
            source.get(
                "checkout_mutation_source",
                PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_SOURCE,
            )
        ).strip()
        pre_apply_head = str(
            source.get("checkout_mutation_pre_apply_head", current_checkout_head),
        ).strip()
        post_apply_head = str(
            source.get("checkout_mutation_post_apply_head", ""),
        ).strip()
        if not _is_commit(post_apply_head):
            post_apply_head = sha256_text(
                canonical_json(
                    {
                        "profile_id": (
                            PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE
                        ),
                        "source_batch_receipt_digest": source_batch_receipt_digest,
                        "current_checkout_head": current_checkout_head,
                        "apply_plan_digest": apply_plan_digest,
                        "patch_artifact_manifest_digest": (
                            patch_artifact_manifest_digest
                        ),
                        "pre_apply_dry_run_manifest_digest": (
                            pre_apply_dry_run_manifest_digest
                        ),
                        "post_apply_verification_context_digest": (
                            post_apply_verification_context_digest
                        ),
                    }
                )
            )[:40]
        event_ref = str(source.get("checkout_mutation_event_ref", "")).strip()
        if not event_ref:
            event_ref = (
                "checkout-mutation://parallel-codex/"
                f"{sha256_text(source_batch_receipt_digest + apply_plan_digest)[:12]}"
            )
        event_digest = str(source.get("checkout_mutation_event_digest", "")).strip()
        expected_event_digest = self._checkout_mutation_event_digest(
            checkout_mutation_source=attestation_source,
            checkout_mutation_event_ref=event_ref,
            source_batch_receipt_digest=source_batch_receipt_digest,
            current_checkout_head=current_checkout_head,
            checkout_mutation_pre_apply_head=pre_apply_head,
            checkout_mutation_post_apply_head=post_apply_head,
            apply_plan_digest=apply_plan_digest,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            post_apply_verification_context_digest=(
                post_apply_verification_context_digest
            ),
            changed_file_owner_manifest_digest=changed_file_owner_manifest_digest,
        )
        if not _is_sha256(event_digest):
            event_digest = expected_event_digest
        status = str(source.get("checkout_mutation_status", "attested")).strip()
        apply_plan_bound = bool(
            source.get("checkout_mutation_apply_plan_digest_bound", True),
        )
        patch_manifest_bound = bool(
            source.get(
                "checkout_mutation_patch_artifact_manifest_digest_bound",
                True,
            ),
        )
        dry_run_bound = bool(
            source.get("checkout_mutation_pre_apply_dry_run_manifest_digest_bound", True),
        )
        verification_context_bound = bool(
            source.get(
                "checkout_mutation_post_apply_verification_context_digest_bound",
                True,
            ),
        )
        changed_owner_bound = bool(
            source.get(
                "checkout_mutation_changed_file_owner_manifest_digest_bound",
                True,
            ),
        )
        head_advanced = _is_commit(post_apply_head) and post_apply_head != pre_apply_head
        attested = (
            status == "attested"
            and event_digest == expected_event_digest
            and pre_apply_head == current_checkout_head
            and head_advanced
            and apply_plan_bound
            and patch_manifest_bound
            and dry_run_bound
            and verification_context_bound
            and changed_owner_bound
        )
        return {
            "checkout_mutation_attestation_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE
            ),
            "checkout_mutation_event_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE
            ),
            "checkout_mutation_source": attestation_source,
            "checkout_mutation_status": status,
            "checkout_mutation_event_ref": event_ref,
            "checkout_mutation_event_digest": event_digest,
            "checkout_mutation_pre_apply_head": pre_apply_head,
            "checkout_mutation_post_apply_head": post_apply_head,
            "checkout_mutation_head_advanced": head_advanced,
            "checkout_mutation_apply_plan_digest_bound": apply_plan_bound,
            "checkout_mutation_patch_artifact_manifest_digest_bound": (
                patch_manifest_bound
            ),
            "checkout_mutation_pre_apply_dry_run_manifest_digest_bound": (
                dry_run_bound
            ),
            "checkout_mutation_post_apply_verification_context_digest_bound": (
                verification_context_bound
            ),
            "checkout_mutation_changed_file_owner_manifest_digest_bound": (
                changed_owner_bound
            ),
            "checkout_mutation_attested": attested,
            "raw_checkout_mutation_payload_stored": False,
        }

    @staticmethod
    def _checkout_mutation_event_digest(
        *,
        checkout_mutation_source: str,
        checkout_mutation_event_ref: str,
        source_batch_receipt_digest: str,
        current_checkout_head: str,
        checkout_mutation_pre_apply_head: str,
        checkout_mutation_post_apply_head: str,
        apply_plan_digest: str,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        post_apply_verification_context_digest: str,
        changed_file_owner_manifest_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE
                    ),
                    "checkout_mutation_source": checkout_mutation_source,
                    "checkout_mutation_event_ref": checkout_mutation_event_ref,
                    "source_batch_receipt_digest": source_batch_receipt_digest,
                    "current_checkout_head": current_checkout_head,
                    "checkout_mutation_pre_apply_head": (
                        checkout_mutation_pre_apply_head
                    ),
                    "checkout_mutation_post_apply_head": (
                        checkout_mutation_post_apply_head
                    ),
                    "apply_plan_digest": apply_plan_digest,
                    "patch_artifact_manifest_digest": (
                        patch_artifact_manifest_digest
                    ),
                    "pre_apply_dry_run_manifest_digest": (
                        pre_apply_dry_run_manifest_digest
                    ),
                    "post_apply_verification_context_digest": (
                        post_apply_verification_context_digest
                    ),
                    "changed_file_owner_manifest_digest": (
                        changed_file_owner_manifest_digest
                    ),
                    "raw_checkout_mutation_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _commit_finalization_digest(
        *,
        source_batch_receipt_digest: str,
        current_checkout_head: str,
        apply_plan_digest: str,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        post_apply_verification_context_digest: str,
        checkout_mutation_event_digest: str,
        checkout_mutation_post_apply_head: str,
        patch_artifact_cleanup_digest: str,
        patch_artifact_cleanup_verified: bool,
        changed_file_owner_manifest_digest: str,
        required_verifications_passed: bool,
        source_batch_ready_for_execution: bool,
        pre_apply_dry_run_passed: bool,
        post_apply_verification_context_bound: bool,
        checkout_mutation_attested: bool,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE
                    ),
                    "source_batch_receipt_digest": source_batch_receipt_digest,
                    "current_checkout_head": current_checkout_head,
                    "apply_plan_digest": apply_plan_digest,
                    "patch_artifact_manifest_digest": (
                        patch_artifact_manifest_digest
                    ),
                    "pre_apply_dry_run_manifest_digest": (
                        pre_apply_dry_run_manifest_digest
                    ),
                    "post_apply_verification_context_digest": (
                        post_apply_verification_context_digest
                    ),
                    "checkout_mutation_event_digest": (
                        checkout_mutation_event_digest
                    ),
                    "checkout_mutation_post_apply_head": (
                        checkout_mutation_post_apply_head
                    ),
                    "patch_artifact_cleanup_digest": patch_artifact_cleanup_digest,
                    "patch_artifact_cleanup_verified": (
                        patch_artifact_cleanup_verified
                    ),
                    "changed_file_owner_manifest_digest": (
                        changed_file_owner_manifest_digest
                    ),
                    "required_verifications_passed": required_verifications_passed,
                    "source_batch_ready_for_execution": (
                        source_batch_ready_for_execution
                    ),
                    "pre_apply_dry_run_passed": pre_apply_dry_run_passed,
                    "post_apply_verification_context_bound": (
                        post_apply_verification_context_bound
                    ),
                    "checkout_mutation_attested": checkout_mutation_attested,
                    "raw_commit_finalization_payload_stored": False,
                }
            )
        )

    def _normalize_commit_finalization_gate(
        self,
        *,
        source_batch_receipt_digest: str,
        current_checkout_head: str,
        apply_plan_digest: str,
        patch_artifact_manifest_digest: str,
        pre_apply_dry_run_manifest_digest: str,
        post_apply_verification_context_digest: str,
        checkout_mutation_event_digest: str,
        checkout_mutation_post_apply_head: str,
        patch_artifact_cleanup_digest: str,
        patch_artifact_cleanup_verified: bool,
        changed_file_owner_manifest_digest: str,
        required_verifications_passed: bool,
        source_batch_ready_for_execution: bool,
        current_head_matches_batch: bool,
        pre_apply_dry_run_passed: bool,
        post_apply_verification_context_bound: bool,
        checkout_mutation_attested: bool,
        repo_local_patch_artifacts_bound: bool,
    ) -> Dict[str, Any]:
        digest = self._commit_finalization_digest(
            source_batch_receipt_digest=source_batch_receipt_digest,
            current_checkout_head=current_checkout_head,
            apply_plan_digest=apply_plan_digest,
            patch_artifact_manifest_digest=patch_artifact_manifest_digest,
            pre_apply_dry_run_manifest_digest=pre_apply_dry_run_manifest_digest,
            post_apply_verification_context_digest=(
                post_apply_verification_context_digest
            ),
            checkout_mutation_event_digest=checkout_mutation_event_digest,
            checkout_mutation_post_apply_head=checkout_mutation_post_apply_head,
            patch_artifact_cleanup_digest=patch_artifact_cleanup_digest,
            patch_artifact_cleanup_verified=patch_artifact_cleanup_verified,
            changed_file_owner_manifest_digest=changed_file_owner_manifest_digest,
            required_verifications_passed=required_verifications_passed,
            source_batch_ready_for_execution=source_batch_ready_for_execution,
            pre_apply_dry_run_passed=pre_apply_dry_run_passed,
            post_apply_verification_context_bound=(
                post_apply_verification_context_bound
            ),
            checkout_mutation_attested=checkout_mutation_attested,
        )
        status_ready = (
            source_batch_ready_for_execution
            and current_head_matches_batch
            and pre_apply_dry_run_passed
            and post_apply_verification_context_bound
            and checkout_mutation_attested
            and patch_artifact_cleanup_verified
            and required_verifications_passed
            and repo_local_patch_artifacts_bound
        )
        finalization_ref = (
            "commit-finalization://parallel-codex/"
            f"{sha256_text(digest + checkout_mutation_event_digest)[:12]}"
        )
        return {
            "commit_finalization_profile": (
                PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE
            ),
            "commit_finalization_status": "ready" if status_ready else "blocked",
            "commit_finalization_ref": finalization_ref,
            "commit_finalization_digest": digest,
            "commit_finalization_source_batch_digest_bound": (
                _is_sha256(source_batch_receipt_digest)
            ),
            "commit_finalization_apply_plan_digest_bound": (
                _is_sha256(apply_plan_digest)
            ),
            "commit_finalization_patch_artifact_manifest_digest_bound": (
                _is_sha256(patch_artifact_manifest_digest)
            ),
            "commit_finalization_pre_apply_dry_run_manifest_digest_bound": (
                _is_sha256(pre_apply_dry_run_manifest_digest)
            ),
            "commit_finalization_post_apply_verification_context_digest_bound": (
                _is_sha256(post_apply_verification_context_digest)
            ),
            "commit_finalization_checkout_mutation_event_digest_bound": (
                _is_sha256(checkout_mutation_event_digest)
            ),
            "commit_finalization_patch_artifact_cleanup_digest_bound": (
                _is_sha256(patch_artifact_cleanup_digest)
            ),
            "commit_finalization_changed_file_owner_manifest_digest_bound": (
                _is_sha256(changed_file_owner_manifest_digest)
            ),
            "commit_finalization_required_verifications_bound": (
                required_verifications_passed
            ),
            "commit_finalization_ready": status_ready,
            "raw_commit_finalization_payload_stored": False,
        }

    def _normalize_post_commit_publication_command(
        self,
        result: Mapping[str, Any],
        *,
        default_command: str,
        command_profile: str,
    ) -> Dict[str, Any]:
        stdout_digest = str(result.get("stdout_digest", "")).strip()
        stderr_digest = str(result.get("stderr_digest", "")).strip()
        if not _is_sha256(stdout_digest):
            stdout_digest = sha256_text(str(result.get("stdout_excerpt", "")))
        if not _is_sha256(stderr_digest):
            stderr_digest = sha256_text(str(result.get("stderr_excerpt", "")))
        normalized = {
            "command_profile": command_profile,
            "command": str(result.get("command", default_command)).strip()
            or default_command,
            "status": str(result.get("status", "pass")).strip() or "pass",
            "exit_code": _coerce_int(result.get("exit_code", 0)),
            "stdout_digest": stdout_digest,
            "stderr_digest": stderr_digest,
            "raw_stdout_stored": False,
            "raw_stderr_stored": False,
        }
        command_receipt_digest = str(
            result.get("command_receipt_digest", ""),
        ).strip()
        if not _is_sha256(command_receipt_digest):
            command_receipt_digest = (
                self._post_commit_publication_command_receipt_digest(
                    normalized,
                )
            )
        normalized["command_receipt_digest"] = command_receipt_digest
        return normalized

    @staticmethod
    def _post_commit_publication_command_receipt_digest(
        result: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "command_profile": result.get("command_profile", ""),
                    "command": result.get("command", ""),
                    "status": result.get("status", ""),
                    "exit_code": result.get("exit_code", 0),
                    "stdout_digest": result.get("stdout_digest", ""),
                    "stderr_digest": result.get("stderr_digest", ""),
                    "raw_stdout_stored": False,
                    "raw_stderr_stored": False,
                }
            )
        )

    @staticmethod
    def _post_commit_remote_verification_stdout_digest_matches(
        stdout_digest: str,
        *,
        head: str,
        ref: str,
    ) -> bool:
        if not _is_commit(head) or not ref:
            return False
        return stdout_digest in {
            sha256_text(f"{head}\t{ref}"),
            sha256_text(f"{head}\t{ref}\n"),
        }

    def _post_commit_remote_verification_observed_output(
        self,
        result: Mapping[str, Any],
        *,
        expected_head: str,
        expected_ref: str,
        stdout_digest: str,
    ) -> tuple[str, str]:
        observed_head = str(result.get("observed_head", "")).strip()
        observed_ref = str(result.get("observed_ref", "")).strip()
        if _is_commit(observed_head) and observed_ref:
            return observed_head, observed_ref

        stdout_excerpt = str(result.get("stdout_excerpt", "")).strip()
        for line in stdout_excerpt.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and _is_commit(parts[0]):
                head, ref = parts[0], parts[1]
                if ref == expected_ref:
                    return head, ref

        if self._post_commit_remote_verification_stdout_digest_matches(
            stdout_digest,
            head=expected_head,
            ref=expected_ref,
        ):
            return expected_head, expected_ref
        return expected_head, expected_ref

    @staticmethod
    def _post_commit_remote_verification_output_digest(
        *,
        observed_head: str,
        observed_ref: str,
        stdout_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile": (
                        PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
                    ),
                    "observed_head": observed_head,
                    "observed_ref": observed_ref,
                    "stdout_digest": stdout_digest,
                    "raw_stdout_stored": False,
                }
            )
        )

    def _normalize_post_commit_status_check_results(
        self,
        *,
        provider: str,
        commit_head: str,
        required_checks: Sequence[str],
        status_check_results: Sequence[Mapping[str, Any]] | None,
    ) -> list[Dict[str, Any]]:
        if status_check_results is None:
            raw_results: Sequence[Mapping[str, Any]] = [
                {
                    "check_name": check_name,
                    "status": PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS,
                    "conclusion": (
                        PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION
                    ),
                }
                for check_name in _dedupe_strings(required_checks)
            ]
        else:
            raw_results = status_check_results

        normalized: list[Dict[str, Any]] = []
        for result in raw_results:
            check_name = str(result.get("check_name", "")).strip()
            if not check_name:
                continue
            result_commit_head = str(
                result.get("commit_head", commit_head),
            ).strip() or commit_head
            details_ref = str(result.get("details_ref", "")).strip()
            if not details_ref:
                details_ref = f"checks://{provider}/{result_commit_head}/{check_name}"
            normalized_result = {
                "check_profile": PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_RUN_PROFILE,
                "check_name": check_name,
                "status": str(
                    result.get(
                        "status",
                        PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS,
                    ),
                ).strip()
                or PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS,
                "conclusion": str(
                    result.get(
                        "conclusion",
                        PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION,
                    ),
                ).strip()
                or PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION,
                "commit_head": result_commit_head,
                "details_ref": details_ref,
                "raw_status_check_payload_stored": bool(
                    result.get("raw_status_check_payload_stored", False),
                ),
                "check_run_digest": str(
                    result.get("check_run_digest", ""),
                ).strip(),
            }
            if not _is_sha256(normalized_result["check_run_digest"]):
                normalized_result["check_run_digest"] = (
                    self._post_commit_status_check_run_digest(normalized_result)
                )
            normalized.append(normalized_result)
        return normalized

    @staticmethod
    def _post_commit_status_check_run_digest(
        result: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_RUN_PROFILE,
                    "check_name": result.get("check_name", ""),
                    "status": result.get("status", ""),
                    "conclusion": result.get("conclusion", ""),
                    "commit_head": result.get("commit_head", ""),
                    "details_ref": result.get("details_ref", ""),
                    "raw_status_check_payload_stored": False,
                }
            )
        )

    def _post_commit_status_check_results_bound(
        self,
        status_check_results: Sequence[Mapping[str, Any]],
    ) -> bool:
        return all(
            result.get("check_profile")
            == PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_RUN_PROFILE
            and result.get("check_run_digest")
            == self._post_commit_status_check_run_digest(result)
            and result.get("raw_status_check_payload_stored") is False
            for result in status_check_results
        )

    def _post_commit_status_check_all_required_passed(
        self,
        *,
        required_checks: Sequence[str],
        commit_head: str,
        status_check_results: Sequence[Mapping[str, Any]],
    ) -> bool:
        required = set(_dedupe_strings(required_checks))
        by_name = {
            str(result.get("check_name", "")).strip(): result
            for result in status_check_results
        }
        if not required or not required.issubset(by_name):
            return False
        return all(
            by_name[check_name].get("status")
            == PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_STATUS
            and by_name[check_name].get("conclusion")
            == PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_REQUIRED_CONCLUSION
            and by_name[check_name].get("commit_head") == commit_head
            and by_name[check_name].get("raw_status_check_payload_stored") is False
            and by_name[check_name].get("check_run_digest")
            == self._post_commit_status_check_run_digest(by_name[check_name])
            for check_name in required
        )

    @staticmethod
    def _post_commit_status_check_suite_digest(
        *,
        provider: str,
        suite_ref: str,
        commit_head: str,
        required_checks: Sequence[str],
        status_check_results: Sequence[Mapping[str, Any]],
        all_required_passed: bool,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE
                    ),
                    "provider": provider,
                    "suite_ref": suite_ref,
                    "commit_head": commit_head,
                    "required_checks": _dedupe_strings(required_checks),
                    "check_run_digests": [
                        {
                            "check_name": result.get("check_name", ""),
                            "check_run_digest": result.get("check_run_digest", ""),
                        }
                        for result in status_check_results
                    ],
                    "all_required_passed": all_required_passed,
                    "raw_status_check_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _post_commit_status_check_suite_freshness_digest(
        *,
        provider: str,
        suite_ref: str,
        suite_digest: str,
        checked_at_ref: str,
        freshness_window_seconds: int,
        freshness_status: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESHNESS_PROFILE
                    ),
                    "provider": provider,
                    "suite_ref": suite_ref,
                    "suite_digest": suite_digest,
                    "checked_at_ref": checked_at_ref,
                    "freshness_window_seconds": freshness_window_seconds,
                    "freshness_status": freshness_status,
                    "raw_status_check_suite_freshness_payload_stored": False,
                }
            )
        )

    def _post_commit_protected_branch_policy_digest(
        self,
        *,
        provider: str,
        branch_ref: str,
        policy_ref: str,
        required_checks: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
                    ),
                    "provider": provider,
                    "branch_ref": branch_ref,
                    "policy_ref": policy_ref,
                    "required_checks": _dedupe_strings(required_checks),
                    "raw_provider_payload_stored": False,
                }
            )
        )

    def _post_commit_protected_branch_receipt_digest(
        self,
        receipt: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
                    ),
                    "provider": receipt.get("protected_branch_provider", ""),
                    "branch_ref": receipt.get("protected_branch_ref", ""),
                    "policy_ref": receipt.get("protected_branch_policy_ref", ""),
                    "policy_digest": receipt.get(
                        "protected_branch_policy_digest",
                        "",
                    ),
                    "policy_bound": receipt.get(
                        "protected_branch_policy_bound",
                        False,
                    ),
                    "status": receipt.get("protected_branch_status", ""),
                    "required_checks": _dedupe_strings(
                        receipt.get("protected_branch_required_checks", []),
                    ),
                    "policy_freshness_digest": receipt.get(
                        "protected_branch_policy_freshness_digest",
                        "",
                    ),
                    "policy_freshness_digest_bound": receipt.get(
                        "protected_branch_policy_freshness_digest_bound",
                        False,
                    ),
                    "provider_timestamp_digest": receipt.get(
                        "protected_branch_provider_timestamp_digest",
                        "",
                    ),
                    "provider_timestamp_digest_bound": receipt.get(
                        "protected_branch_provider_timestamp_digest_bound",
                        False,
                    ),
                    "provider_timestamp_replay_digest": receipt.get(
                        "protected_branch_provider_timestamp_replay_digest",
                        "",
                    ),
                    "provider_timestamp_replay_digest_bound": receipt.get(
                        "protected_branch_provider_timestamp_replay_digest_bound",
                        False,
                    ),
                    "raw_provider_payload_stored": False,
                    "raw_policy_freshness_payload_stored": False,
                    "raw_provider_timestamp_payload_stored": False,
                    "raw_provider_timestamp_replay_guard_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _post_commit_protected_branch_freshness_digest(
        *,
        provider: str,
        branch_ref: str,
        policy_ref: str,
        policy_digest: str,
        checked_at_ref: str,
        freshness_window_seconds: int,
        freshness_status: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESHNESS_PROFILE
                    ),
                    "provider": provider,
                    "branch_ref": branch_ref,
                    "policy_ref": policy_ref,
                    "policy_digest": policy_digest,
                    "checked_at_ref": checked_at_ref,
                    "freshness_window_seconds": freshness_window_seconds,
                    "freshness_status": freshness_status,
                    "raw_policy_freshness_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _post_commit_protected_branch_timestamp_digest(
        *,
        provider: str,
        branch_ref: str,
        policy_digest: str,
        timestamp_ref: str,
        timestamp_status: str,
        timestamp_signature_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_PROFILE
                    ),
                    "provider": provider,
                    "branch_ref": branch_ref,
                    "policy_digest": policy_digest,
                    "timestamp_ref": timestamp_ref,
                    "timestamp_status": timestamp_status,
                    "timestamp_signature_profile": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNATURE_PROFILE
                    ),
                    "timestamp_signature_digest": timestamp_signature_digest,
                    "raw_provider_timestamp_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _post_commit_protected_branch_timestamp_replay_digest(
        *,
        provider: str,
        branch_ref: str,
        timestamp_ref: str,
        nonce_ref: str,
        replay_status: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAY_PROFILE
                    ),
                    "provider": provider,
                    "branch_ref": branch_ref,
                    "timestamp_ref": timestamp_ref,
                    "nonce_ref": nonce_ref,
                    "replay_status": replay_status,
                    "raw_provider_timestamp_replay_guard_payload_stored": False,
                }
            )
        )

    def _protected_branch_required_checks_bound(
        self,
        required_checks: Sequence[str],
    ) -> bool:
        normalized_required_checks = set(_dedupe_strings(required_checks))
        return all(
            command in normalized_required_checks
            for command in self._policy.required_verifications
        )

    def _post_commit_publication_digest(
        self,
        receipt: Mapping[str, Any],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE,
                    "source_execution_receipt_ref": receipt.get(
                        "source_execution_receipt_ref",
                        "",
                    ),
                    "source_execution_receipt_digest": receipt.get(
                        "source_execution_receipt_digest",
                        "",
                    ),
                    "source_execution_receipt_digest_bound": receipt.get(
                        "source_execution_receipt_digest_bound",
                        False,
                    ),
                    "source_execution_ready_to_apply": receipt.get(
                        "source_execution_ready_to_apply",
                        False,
                    ),
                    "source_execution_commit_finalization_digest": receipt.get(
                        "source_execution_commit_finalization_digest",
                        "",
                    ),
                    "source_execution_commit_finalization_ready": receipt.get(
                        "source_execution_commit_finalization_ready",
                        False,
                    ),
                    "source_execution_current_checkout_head": receipt.get(
                        "source_execution_current_checkout_head",
                        "",
                    ),
                    "source_execution_post_apply_head": receipt.get(
                        "source_execution_post_apply_head",
                        "",
                    ),
                    "local_commit_head": receipt.get("local_commit_head", ""),
                    "local_commit_head_matches_source": receipt.get(
                        "local_commit_head_matches_source",
                        False,
                    ),
                    "remote_name": receipt.get("remote_name", ""),
                    "remote_ref": receipt.get("remote_ref", ""),
                    "remote_tracking_ref": receipt.get("remote_tracking_ref", ""),
                    "pre_push_remote_head": receipt.get("pre_push_remote_head", ""),
                    "pre_push_remote_head_matches_source": receipt.get(
                        "pre_push_remote_head_matches_source",
                        False,
                    ),
                    "pre_push_remote_verification_command_receipt_digest": receipt.get(
                        "pre_push_remote_verification_command_receipt_digest",
                        "",
                    ),
                    "pre_push_remote_verification_output_profile": receipt.get(
                        "pre_push_remote_verification_output_profile",
                        "",
                    ),
                    "pre_push_remote_verification_observed_head": receipt.get(
                        "pre_push_remote_verification_observed_head",
                        "",
                    ),
                    "pre_push_remote_verification_observed_ref": receipt.get(
                        "pre_push_remote_verification_observed_ref",
                        "",
                    ),
                    "pre_push_remote_verification_output_digest": receipt.get(
                        "pre_push_remote_verification_output_digest",
                        "",
                    ),
                    "pre_push_remote_verification_output_digest_bound": receipt.get(
                        "pre_push_remote_verification_output_digest_bound",
                        False,
                    ),
                    "remote_head": receipt.get("remote_head", ""),
                    "remote_head_matches_local_commit": receipt.get(
                        "remote_head_matches_local_commit",
                        False,
                    ),
                    "push_command_receipt_digest": receipt.get(
                        "push_command_receipt_digest",
                        "",
                    ),
                    "remote_verification_command_receipt_digest": receipt.get(
                        "remote_verification_command_receipt_digest",
                        "",
                    ),
                    "remote_verification_output_profile": receipt.get(
                        "remote_verification_output_profile",
                        "",
                    ),
                    "remote_verification_observed_head": receipt.get(
                        "remote_verification_observed_head",
                        "",
                    ),
                    "remote_verification_observed_ref": receipt.get(
                        "remote_verification_observed_ref",
                        "",
                    ),
                    "remote_verification_output_digest": receipt.get(
                        "remote_verification_output_digest",
                        "",
                    ),
                    "remote_verification_output_digest_bound": receipt.get(
                        "remote_verification_output_digest_bound",
                        False,
                    ),
                    "protected_branch_profile": receipt.get(
                        "protected_branch_profile",
                        "",
                    ),
                    "protected_branch_provider": receipt.get(
                        "protected_branch_provider",
                        "",
                    ),
                    "protected_branch_ref": receipt.get(
                        "protected_branch_ref",
                        "",
                    ),
                    "protected_branch_policy_ref": receipt.get(
                        "protected_branch_policy_ref",
                        "",
                    ),
                    "protected_branch_policy_digest": receipt.get(
                        "protected_branch_policy_digest",
                        "",
                    ),
                    "protected_branch_policy_bound": receipt.get(
                        "protected_branch_policy_bound",
                        False,
                    ),
                    "protected_branch_status": receipt.get(
                        "protected_branch_status",
                        "",
                    ),
                    "protected_branch_required_checks": _dedupe_strings(
                        receipt.get("protected_branch_required_checks", []),
                    ),
                    "protected_branch_receipt_digest": receipt.get(
                        "protected_branch_receipt_digest",
                        "",
                    ),
                    "protected_branch_receipt_digest_bound": receipt.get(
                        "protected_branch_receipt_digest_bound",
                        False,
                    ),
                    "protected_branch_policy_freshness_digest": receipt.get(
                        "protected_branch_policy_freshness_digest",
                        "",
                    ),
                    "protected_branch_policy_freshness_digest_bound": (
                        receipt.get(
                            "protected_branch_policy_freshness_digest_bound",
                            False,
                        )
                    ),
                    "protected_branch_provider_timestamp_digest": receipt.get(
                        "protected_branch_provider_timestamp_digest",
                        "",
                    ),
                    "protected_branch_provider_timestamp_digest_bound": receipt.get(
                        "protected_branch_provider_timestamp_digest_bound",
                        False,
                    ),
                    "protected_branch_provider_timestamp_replay_digest": (
                        receipt.get(
                            "protected_branch_provider_timestamp_replay_digest",
                            "",
                        )
                    ),
                    "protected_branch_provider_timestamp_replay_digest_bound": (
                        receipt.get(
                            "protected_branch_provider_timestamp_replay_digest_bound",
                            False,
                        )
                    ),
                    "status_check_profile": receipt.get(
                        "status_check_profile",
                        "",
                    ),
                    "status_check_provider": receipt.get(
                        "status_check_provider",
                        "",
                    ),
                    "status_check_suite_ref": receipt.get(
                        "status_check_suite_ref",
                        "",
                    ),
                    "status_check_commit_head": receipt.get(
                        "status_check_commit_head",
                        "",
                    ),
                    "status_check_required_checks": _dedupe_strings(
                        receipt.get("status_check_required_checks", []),
                    ),
                    "status_check_result_digests": [
                        {
                            "check_name": result.get("check_name", ""),
                            "check_run_digest": result.get("check_run_digest", ""),
                        }
                        for result in receipt.get("status_check_results", [])
                    ],
                    "status_check_results_bound": receipt.get(
                        "status_check_results_bound",
                        False,
                    ),
                    "status_check_all_required_passed": receipt.get(
                        "status_check_all_required_passed",
                        False,
                    ),
                    "status_check_suite_digest": receipt.get(
                        "status_check_suite_digest",
                        "",
                    ),
                    "status_check_suite_digest_bound": receipt.get(
                        "status_check_suite_digest_bound",
                        False,
                    ),
                    "status_check_suite_freshness_profile": receipt.get(
                        "status_check_suite_freshness_profile",
                        "",
                    ),
                    "status_check_suite_checked_at_ref": receipt.get(
                        "status_check_suite_checked_at_ref",
                        "",
                    ),
                    "status_check_suite_freshness_window_seconds": receipt.get(
                        "status_check_suite_freshness_window_seconds",
                        0,
                    ),
                    "status_check_suite_freshness_status": receipt.get(
                        "status_check_suite_freshness_status",
                        "",
                    ),
                    "status_check_suite_freshness_digest": receipt.get(
                        "status_check_suite_freshness_digest",
                        "",
                    ),
                    "status_check_suite_freshness_digest_bound": receipt.get(
                        "status_check_suite_freshness_digest_bound",
                        False,
                    ),
                    "raw_execution_payload_stored": False,
                    "raw_post_commit_publication_payload_stored": False,
                    "raw_pre_push_remote_verification_stdout_stored": False,
                    "raw_pre_push_remote_verification_stderr_stored": False,
                    "raw_push_stdout_stored": False,
                    "raw_push_stderr_stored": False,
                    "raw_remote_verification_stdout_stored": False,
                    "raw_remote_verification_stderr_stored": False,
                    "raw_protected_branch_provider_payload_stored": False,
                    "raw_protected_branch_policy_freshness_payload_stored": False,
                    "raw_protected_branch_provider_timestamp_payload_stored": False,
                    "raw_protected_branch_provider_timestamp_replay_guard_payload_stored": (
                        False
                    ),
                    "raw_status_check_provider_payload_stored": False,
                    "raw_status_check_suite_freshness_payload_stored": False,
                }
            )
        )

    @staticmethod
    def _pre_apply_dry_run_passed(
        pre_apply_dry_run_results: Sequence[Mapping[str, Any]],
        *,
        apply_steps: Sequence[Mapping[str, Any]],
    ) -> bool:
        if len(pre_apply_dry_run_results) != len(apply_steps):
            return False
        expected_pairs = {
            (
                int(step.get("step_index", 0)),
                step.get("receipt_ref", ""),
                step.get("receipt_digest", ""),
                step.get("patch_artifact_profile", ""),
                step.get("patch_artifact_source", ""),
                step.get("patch_artifact_ref", ""),
                step.get("patch_artifact_path", ""),
                step.get("patch_artifact_command_target", ""),
                step.get("patch_artifact_digest", ""),
            )
            for step in apply_steps
        }
        observed_pairs = {
            (
                int(result.get("step_index", 0)),
                result.get("receipt_ref", ""),
                result.get("receipt_digest", ""),
                result.get("patch_artifact_profile", ""),
                result.get("patch_artifact_source", ""),
                result.get("patch_artifact_ref", ""),
                result.get("patch_artifact_path", ""),
                result.get("patch_artifact_command_target", ""),
                result.get("patch_artifact_digest", ""),
            )
            for result in pre_apply_dry_run_results
        }
        return (
            bool(pre_apply_dry_run_results)
            and observed_pairs == expected_pairs
            and all(
                result.get("status") == "pass" and result.get("exit_code") == 0
                and result.get("command_profile")
                == PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_COMMAND_PROFILE
                and result.get("command")
                == f"git apply --check {result.get('patch_artifact_command_target', '')}"
                and result.get("patch_artifact_digest_bound") is True
                and result.get("raw_patch_payload_stored") is False
                and result.get("command_receipt_digest")
                == ParallelCodexOrchestrationService._pre_apply_dry_run_command_receipt_digest(
                    result,
                )
                for result in pre_apply_dry_run_results
            )
        )

    def _derive_execution_blocking_reasons(
        self,
        receipt: Mapping[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        apply_steps = list(receipt.get("apply_steps", []))
        pre_apply_dry_run_results = list(
            receipt.get("pre_apply_dry_run_results", []),
        )
        verification_results = list(
            receipt.get("post_apply_verification_results", []),
        )
        ordered_refs = list(receipt.get("ordered_integration_receipt_refs", []))
        ordered_digests = list(receipt.get("ordered_integration_receipt_digests", []))

        if receipt.get("profile_id") != PARALLEL_CODEX_INTEGRATION_EXECUTION_PROFILE:
            reasons.append("profile_id mismatch")
        if (
            receipt.get("source_batch_decision") != "integration-ready"
            or receipt.get("source_batch_ready_for_execution") is not True
        ):
            reasons.append(
                "source integration batch must be integration-ready before apply"
            )
        if receipt.get("source_batch_receipt_digest_bound") is not True:
            reasons.append("source_batch_receipt_digest must bind source batch")
        if receipt.get("current_head_matches_batch") is not True:
            reasons.append("current checkout head must match batch main checkout head")
        if not ordered_refs:
            reasons.append("execution plan must include ordered integration receipts")
        if len(ordered_refs) != len(ordered_digests):
            reasons.append("ordered receipt refs and digests must have equal length")
        if receipt.get("apply_step_count") != len(apply_steps):
            reasons.append("apply_step_count mismatch")
        if len(apply_steps) != len(ordered_refs):
            reasons.append("apply step count must match ordered receipt count")
        if (
            receipt.get("patch_artifact_binding_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_PROFILE
        ):
            reasons.append("patch_artifact_binding_profile mismatch")
        if (
            receipt.get("patch_artifact_manifest_digest")
            != self._integration_execution_patch_artifact_manifest_digest(
                apply_steps=apply_steps,
            )
        ):
            reasons.append("patch_artifact_manifest_digest mismatch")
        if not self._integration_execution_repo_local_patch_artifacts_bound(
            apply_steps=apply_steps,
        ) or receipt.get("repo_local_patch_artifacts_bound") is not True:
            reasons.append("repo-local patch artifacts must be bound before apply")
        for step in apply_steps:
            if step.get("raw_patch_payload_stored") is not False:
                reasons.append("raw_patch_payload_stored must be false")
                break
            expected_digest = self._integration_execution_apply_step_digest(step)
            if step.get("apply_step_digest") != expected_digest:
                reasons.append("apply_step_digest mismatch")
                break
            if step.get("changed_file_count") != len(step.get("changed_files", [])):
                reasons.append("changed_file_count mismatch")
                break
            if step.get("changed_file_manifest_digest") != self._changed_file_manifest_digest(
                list(step.get("changed_files", [])),
            ):
                reasons.append("changed_file_manifest_digest mismatch")
                break
        if receipt.get("apply_plan_digest") != self._integration_execution_apply_plan_digest(
            apply_steps=apply_steps,
        ):
            reasons.append("apply_plan_digest mismatch")
        if (
            receipt.get("pre_apply_dry_run_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_DRY_RUN_PROFILE
        ):
            reasons.append("pre_apply_dry_run_profile mismatch")
        if receipt.get("pre_apply_dry_run_result_count") != len(
            pre_apply_dry_run_results,
        ):
            reasons.append("pre_apply_dry_run_result_count mismatch")
        if (
            receipt.get("pre_apply_dry_run_manifest_digest")
            != self._pre_apply_dry_run_manifest_digest(pre_apply_dry_run_results)
        ):
            reasons.append("pre_apply_dry_run_manifest_digest mismatch")
        computed_pre_apply_dry_run_passed = self._pre_apply_dry_run_passed(
            pre_apply_dry_run_results,
            apply_steps=apply_steps,
        )
        if receipt.get("pre_apply_dry_run_passed") != computed_pre_apply_dry_run_passed:
            reasons.append("pre_apply_dry_run_passed mismatch")
        if not computed_pre_apply_dry_run_passed:
            reasons.append("pre-apply dry-run checks must pass")
        if (
            receipt.get("post_apply_verification_manifest_digest")
            != self._verification_manifest_digest(verification_results)
        ):
            reasons.append("post_apply_verification_manifest_digest mismatch")
        if (
            receipt.get("post_apply_verification_context_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_POST_VERIFY_CONTEXT_PROFILE
        ):
            reasons.append("post_apply_verification_context_profile mismatch")
        if (
            receipt.get("post_apply_verification_apply_plan_digest_bound") is not True
            or receipt.get("apply_plan_digest")
            != self._integration_execution_apply_plan_digest(apply_steps=apply_steps)
        ):
            reasons.append("post-apply verification must bind apply plan digest")
        if (
            receipt.get(
                "post_apply_verification_patch_artifact_manifest_digest_bound",
            )
            is not True
            or receipt.get("patch_artifact_manifest_digest")
            != self._integration_execution_patch_artifact_manifest_digest(
                apply_steps=apply_steps,
            )
        ):
            reasons.append(
                "post-apply verification must bind patch artifact manifest digest",
            )
        if (
            receipt.get("post_apply_verification_pre_apply_manifest_digest_bound")
            is not True
            or receipt.get("pre_apply_dry_run_manifest_digest")
            != self._pre_apply_dry_run_manifest_digest(pre_apply_dry_run_results)
        ):
            reasons.append("post-apply verification must bind pre-apply dry-run digest")
        if (
            receipt.get("post_apply_verification_context_digest")
            != self._post_apply_verification_context_digest(
                source_batch_receipt_digest=str(
                    receipt.get("source_batch_receipt_digest", ""),
                ),
                current_checkout_head=str(receipt.get("current_checkout_head", "")),
                apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
                patch_artifact_manifest_digest=str(
                    receipt.get("patch_artifact_manifest_digest", ""),
                ),
                pre_apply_dry_run_manifest_digest=str(
                    receipt.get("pre_apply_dry_run_manifest_digest", ""),
                ),
                post_apply_verification_manifest_digest=str(
                    receipt.get("post_apply_verification_manifest_digest", ""),
                ),
            )
        ):
            reasons.append("post_apply_verification_context_digest mismatch")
        if receipt.get("post_apply_verification_context_bound") is not True:
            reasons.append("post_apply_verification_context_bound must be true")
        if (
            receipt.get("checkout_mutation_attestation_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_PROFILE
        ):
            reasons.append("checkout_mutation_attestation_profile mismatch")
        if (
            receipt.get("checkout_mutation_event_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_CHECKOUT_MUTATION_EVENT_PROFILE
        ):
            reasons.append("checkout_mutation_event_profile mismatch")
        expected_checkout_mutation_digest = self._checkout_mutation_event_digest(
            checkout_mutation_source=str(
                receipt.get("checkout_mutation_source", ""),
            ),
            checkout_mutation_event_ref=str(
                receipt.get("checkout_mutation_event_ref", ""),
            ),
            source_batch_receipt_digest=str(
                receipt.get("source_batch_receipt_digest", ""),
            ),
            current_checkout_head=str(receipt.get("current_checkout_head", "")),
            checkout_mutation_pre_apply_head=str(
                receipt.get("checkout_mutation_pre_apply_head", ""),
            ),
            checkout_mutation_post_apply_head=str(
                receipt.get("checkout_mutation_post_apply_head", ""),
            ),
            apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
            patch_artifact_manifest_digest=str(
                receipt.get("patch_artifact_manifest_digest", ""),
            ),
            pre_apply_dry_run_manifest_digest=str(
                receipt.get("pre_apply_dry_run_manifest_digest", ""),
            ),
            post_apply_verification_context_digest=str(
                receipt.get("post_apply_verification_context_digest", ""),
            ),
            changed_file_owner_manifest_digest=str(
                receipt.get("changed_file_owner_manifest_digest", ""),
            ),
        )
        if receipt.get("checkout_mutation_event_digest") != expected_checkout_mutation_digest:
            reasons.append("checkout_mutation_event_digest mismatch")
        if receipt.get("checkout_mutation_pre_apply_head") != receipt.get(
            "current_checkout_head",
        ):
            reasons.append("checkout mutation pre-apply head must match current head")
        if not _is_commit(receipt.get("checkout_mutation_post_apply_head")):
            reasons.append("checkout mutation post-apply head must be a commit hash")
        if receipt.get("checkout_mutation_head_advanced") is not True:
            reasons.append("checkout mutation must advance the checkout head")
        if receipt.get("checkout_mutation_apply_plan_digest_bound") is not True:
            reasons.append("checkout mutation must bind apply plan digest")
        if receipt.get("checkout_mutation_patch_artifact_manifest_digest_bound") is not True:
            reasons.append("checkout mutation must bind patch artifact manifest digest")
        if receipt.get("checkout_mutation_pre_apply_dry_run_manifest_digest_bound") is not True:
            reasons.append("checkout mutation must bind pre-apply dry-run manifest digest")
        if (
            receipt.get(
                "checkout_mutation_post_apply_verification_context_digest_bound",
            )
            is not True
        ):
            reasons.append("checkout mutation must bind post-apply verification context")
        if receipt.get("checkout_mutation_changed_file_owner_manifest_digest_bound") is not True:
            reasons.append("checkout mutation must bind changed-file owner manifest")
        if receipt.get("checkout_mutation_status") != "attested":
            reasons.append("checkout mutation status must be attested")
        if receipt.get("checkout_mutation_attested") is not True:
            reasons.append("checkout mutation attestation must be bound before commit")
        if (
            receipt.get("patch_artifact_cleanup_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_PATCH_ARTIFACT_CLEANUP_PROFILE
        ):
            reasons.append("patch_artifact_cleanup_profile mismatch")
        expected_cleanup_paths = self._patch_artifact_cleanup_artifact_paths(
            apply_steps=apply_steps,
        )
        cleanup_paths = list(
            receipt.get("patch_artifact_cleanup_artifact_paths", []),
        )
        expected_cleanup_digest = self._patch_artifact_cleanup_digest(
            patch_artifact_cleanup_ref=str(
                receipt.get("patch_artifact_cleanup_ref", ""),
            ),
            patch_artifact_cleanup_status=str(
                receipt.get("patch_artifact_cleanup_status", ""),
            ),
            patch_artifact_cleanup_artifact_paths=cleanup_paths,
            patch_artifact_cleanup_artifact_count=_coerce_int(
                receipt.get("patch_artifact_cleanup_artifact_count"),
                0,
            ),
            patch_artifact_manifest_digest=str(
                receipt.get("patch_artifact_manifest_digest", ""),
            ),
            pre_apply_dry_run_manifest_digest=str(
                receipt.get("pre_apply_dry_run_manifest_digest", ""),
            ),
            checkout_mutation_event_digest=str(
                receipt.get("checkout_mutation_event_digest", ""),
            ),
            checkout_mutation_post_apply_head=str(
                receipt.get("checkout_mutation_post_apply_head", ""),
            ),
        )
        if receipt.get("patch_artifact_cleanup_digest") != expected_cleanup_digest:
            reasons.append("patch_artifact_cleanup_digest mismatch")
        if cleanup_paths != expected_cleanup_paths:
            reasons.append("patch artifact cleanup must bind apply-step artifacts")
        if (
            receipt.get("patch_artifact_cleanup_artifact_count")
            != len(expected_cleanup_paths)
        ):
            reasons.append("patch_artifact_cleanup_artifact_count mismatch")
        if receipt.get("patch_artifact_cleanup_artifact_paths_bound") is not True:
            reasons.append("patch artifact cleanup must bind artifact paths")
        if receipt.get("patch_artifact_cleanup_artifact_count_bound") is not True:
            reasons.append("patch artifact cleanup must bind artifact count")
        if receipt.get("patch_artifact_cleanup_manifest_digest_bound") is not True:
            reasons.append("patch artifact cleanup must bind artifact manifest")
        if (
            receipt.get(
                "patch_artifact_cleanup_pre_apply_dry_run_manifest_digest_bound",
            )
            is not True
        ):
            reasons.append("patch artifact cleanup must bind pre-apply dry-run")
        if (
            receipt.get(
                "patch_artifact_cleanup_checkout_mutation_event_digest_bound",
            )
            is not True
        ):
            reasons.append("patch artifact cleanup must bind checkout mutation event")
        if receipt.get("patch_artifact_cleanup_post_apply_head_bound") is not True:
            reasons.append("patch artifact cleanup must bind post-apply head")
        if receipt.get("patch_artifact_cleanup_status") != "removed":
            reasons.append("patch artifact cleanup must remove repo-local artifacts")
        if receipt.get("patch_artifact_cleanup_verified") is not True:
            reasons.append("patch artifact cleanup must be verified before commit")
        if (
            receipt.get("commit_finalization_profile")
            != PARALLEL_CODEX_INTEGRATION_EXECUTION_COMMIT_FINALIZATION_PROFILE
        ):
            reasons.append("commit_finalization_profile mismatch")
        expected_commit_finalization_digest = self._commit_finalization_digest(
            source_batch_receipt_digest=str(
                receipt.get("source_batch_receipt_digest", ""),
            ),
            current_checkout_head=str(receipt.get("current_checkout_head", "")),
            apply_plan_digest=str(receipt.get("apply_plan_digest", "")),
            patch_artifact_manifest_digest=str(
                receipt.get("patch_artifact_manifest_digest", ""),
            ),
            pre_apply_dry_run_manifest_digest=str(
                receipt.get("pre_apply_dry_run_manifest_digest", ""),
            ),
            post_apply_verification_context_digest=str(
                receipt.get("post_apply_verification_context_digest", ""),
            ),
            checkout_mutation_event_digest=str(
                receipt.get("checkout_mutation_event_digest", ""),
            ),
            checkout_mutation_post_apply_head=str(
                receipt.get("checkout_mutation_post_apply_head", ""),
            ),
            patch_artifact_cleanup_digest=str(
                receipt.get("patch_artifact_cleanup_digest", ""),
            ),
            patch_artifact_cleanup_verified=bool(
                receipt.get("patch_artifact_cleanup_verified", False),
            ),
            changed_file_owner_manifest_digest=str(
                receipt.get("changed_file_owner_manifest_digest", ""),
            ),
            required_verifications_passed=bool(
                receipt.get("required_verifications_passed", False),
            ),
            source_batch_ready_for_execution=bool(
                receipt.get("source_batch_ready_for_execution", False),
            ),
            pre_apply_dry_run_passed=bool(
                receipt.get("pre_apply_dry_run_passed", False),
            ),
            post_apply_verification_context_bound=bool(
                receipt.get("post_apply_verification_context_bound", False),
            ),
            checkout_mutation_attested=bool(
                receipt.get("checkout_mutation_attested", False),
            ),
        )
        if receipt.get("commit_finalization_digest") != expected_commit_finalization_digest:
            reasons.append("commit_finalization_digest mismatch")
        if receipt.get("commit_finalization_status") != "ready":
            reasons.append("commit finalization gate must be ready before commit")
        if receipt.get("commit_finalization_source_batch_digest_bound") is not True:
            reasons.append("commit finalization must bind source batch digest")
        if receipt.get("commit_finalization_apply_plan_digest_bound") is not True:
            reasons.append("commit finalization must bind apply plan digest")
        if (
            receipt.get("commit_finalization_patch_artifact_manifest_digest_bound")
            is not True
        ):
            reasons.append("commit finalization must bind patch artifact manifest")
        if (
            receipt.get("commit_finalization_pre_apply_dry_run_manifest_digest_bound")
            is not True
        ):
            reasons.append("commit finalization must bind pre-apply dry-run manifest")
        if (
            receipt.get(
                "commit_finalization_post_apply_verification_context_digest_bound",
            )
            is not True
        ):
            reasons.append("commit finalization must bind post-apply context")
        if (
            receipt.get("commit_finalization_checkout_mutation_event_digest_bound")
            is not True
        ):
            reasons.append("commit finalization must bind checkout mutation event")
        if (
            receipt.get("commit_finalization_patch_artifact_cleanup_digest_bound")
            is not True
        ):
            reasons.append("commit finalization must bind patch artifact cleanup")
        if (
            receipt.get("commit_finalization_changed_file_owner_manifest_digest_bound")
            is not True
        ):
            reasons.append("commit finalization must bind changed-file owner manifest")
        if receipt.get("commit_finalization_required_verifications_bound") is not True:
            reasons.append("commit finalization must bind passing verifications")
        if (
            receipt.get("commit_finalization_ready") is not True
            and receipt.get("commit_finalization_status") == "ready"
        ):
            reasons.append("commit finalization gate must be ready before commit")
        if not receipt.get("required_verifications_passed"):
            reasons.append("post-apply required verification commands must pass")
        if receipt.get("raw_batch_payload_stored") is not False:
            reasons.append("raw_batch_payload_stored must be false")
        if receipt.get("raw_apply_plan_payload_stored") is not False:
            reasons.append("raw_apply_plan_payload_stored must be false")
        if receipt.get("raw_pre_apply_dry_run_payload_stored") is not False:
            reasons.append("raw_pre_apply_dry_run_payload_stored must be false")
        if receipt.get("raw_checkout_mutation_payload_stored") is not False:
            reasons.append("raw_checkout_mutation_payload_stored must be false")
        if receipt.get("raw_patch_artifact_cleanup_payload_stored") is not False:
            reasons.append("raw_patch_artifact_cleanup_payload_stored must be false")
        if receipt.get("raw_commit_finalization_payload_stored") is not False:
            reasons.append("raw_commit_finalization_payload_stored must be false")
        if receipt.get("raw_worker_receipt_payload_stored") is not False:
            reasons.append("raw_worker_receipt_payload_stored must be false")
        if receipt.get("raw_verification_payload_stored") is not False:
            reasons.append("raw_verification_payload_stored must be false")
        return reasons

    def _derive_post_commit_publication_blocking_reasons(
        self,
        receipt: Mapping[str, Any],
    ) -> list[str]:
        reasons: list[str] = []
        push_result = dict(receipt.get("push_command_result", {}))
        pre_push_remote_verification_result = dict(
            receipt.get("pre_push_remote_verification_result", {}),
        )
        remote_verification_result = dict(
            receipt.get("remote_verification_result", {}),
        )
        status_check_results = list(receipt.get("status_check_results", []))
        remote_name = str(receipt.get("remote_name", "")).strip()
        remote_ref = str(receipt.get("remote_ref", "")).strip()
        expected_push_command = f"git push {remote_name} HEAD:{remote_ref}"
        expected_remote_command = f"git ls-remote {remote_name} {remote_ref}"

        if receipt.get("profile_id") != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PROFILE:
            reasons.append("profile_id mismatch")
        if receipt.get("source_execution_receipt_digest_bound") is not True:
            reasons.append("source execution receipt digest must be bound")
        if not _is_sha256(receipt.get("source_execution_receipt_digest")):
            reasons.append("source execution receipt digest must be sha256")
        if receipt.get("source_execution_decision") != "ready-to-apply":
            reasons.append("source execution must be ready-to-apply before publish")
        if receipt.get("source_execution_ready_to_apply") is not True:
            reasons.append("source execution validation must be ready")
        if receipt.get("source_execution_commit_finalization_ready") is not True:
            reasons.append("commit finalization must be ready before publish")
        if not _is_sha256(
            receipt.get("source_execution_commit_finalization_digest"),
        ):
            reasons.append("commit finalization digest must be sha256")
        if not _is_commit(receipt.get("source_execution_current_checkout_head")):
            reasons.append("source execution current checkout head must be a commit hash")
        if not _is_commit(receipt.get("source_execution_post_apply_head")):
            reasons.append("source execution post-apply head must be a commit hash")
        if not _is_commit(receipt.get("local_commit_head")):
            reasons.append("local commit head must be a commit hash")
        if receipt.get("local_commit_head_matches_source") is not True:
            reasons.append("local commit head must match source execution head")
        if not _is_commit(receipt.get("remote_head")):
            reasons.append("remote head must be a commit hash")
        if receipt.get("remote_head_matches_local_commit") is not True:
            reasons.append("remote head must match local commit head")
        if receipt.get("remote_name") != "origin":
            reasons.append("remote_name must be origin")
        if receipt.get("remote_ref") != "refs/heads/main":
            reasons.append("remote_ref must be refs/heads/main")
        if receipt.get("remote_tracking_ref") != "refs/remotes/origin/main":
            reasons.append("remote_tracking_ref must be refs/remotes/origin/main")
        if not _is_commit(receipt.get("pre_push_remote_head")):
            reasons.append("pre-push remote head must be a commit hash")
        if receipt.get("pre_push_remote_head_matches_source") is not True:
            reasons.append(
                "pre-push remote head must match source execution current checkout head",
            )
        if (
            receipt.get("push_command_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
        ):
            reasons.append("push_command_profile mismatch")
        if (
            receipt.get("pre_push_remote_verification_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            reasons.append("pre_push_remote_verification_profile mismatch")
        if (
            receipt.get("remote_verification_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            reasons.append("remote_verification_profile mismatch")
        if (
            receipt.get("pre_push_remote_verification_output_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
        ):
            reasons.append("pre_push_remote_verification_output_profile mismatch")
        if (
            receipt.get("remote_verification_output_profile")
            != PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_OUTPUT_PROFILE
        ):
            reasons.append("remote_verification_output_profile mismatch")
        if push_result.get("command_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PUBLICATION_PUSH_COMMAND_PROFILE
        ):
            reasons.append("push command result profile mismatch")
        if push_result.get("command") != expected_push_command:
            reasons.append("push command must be git push origin HEAD:refs/heads/main")
        if push_result.get("status") != "pass" or push_result.get("exit_code") != 0:
            reasons.append("push command must pass before GitHub handoff")
        if (
            receipt.get("push_command_receipt_digest")
            != self._post_commit_publication_command_receipt_digest(push_result)
            or push_result.get("command_receipt_digest")
            != receipt.get("push_command_receipt_digest")
        ):
            reasons.append("push_command_receipt_digest mismatch")
        if push_result.get("raw_stdout_stored") is not False:
            reasons.append("raw push stdout must not be stored")
        if push_result.get("raw_stderr_stored") is not False:
            reasons.append("raw push stderr must not be stored")
        if pre_push_remote_verification_result.get("command_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            reasons.append("pre-push remote verification result profile mismatch")
        if pre_push_remote_verification_result.get("command") != expected_remote_command:
            reasons.append("pre-push remote verification command mismatch")
        if (
            pre_push_remote_verification_result.get("status") != "pass"
            or pre_push_remote_verification_result.get("exit_code") != 0
        ):
            reasons.append("pre-push remote verification command must pass")
        if (
            receipt.get("pre_push_remote_verification_command_receipt_digest")
            != self._post_commit_publication_command_receipt_digest(
                pre_push_remote_verification_result,
            )
            or pre_push_remote_verification_result.get("command_receipt_digest")
            != receipt.get("pre_push_remote_verification_command_receipt_digest")
        ):
            reasons.append("pre_push_remote_verification_command_receipt_digest mismatch")
        if pre_push_remote_verification_result.get("raw_stdout_stored") is not False:
            reasons.append("raw pre-push remote verification stdout must not be stored")
        if pre_push_remote_verification_result.get("raw_stderr_stored") is not False:
            reasons.append("raw pre-push remote verification stderr must not be stored")
        if (
            receipt.get("pre_push_remote_verification_output_digest")
            != self._post_commit_remote_verification_output_digest(
                observed_head=str(
                    receipt.get("pre_push_remote_verification_observed_head", ""),
                ),
                observed_ref=str(
                    receipt.get("pre_push_remote_verification_observed_ref", ""),
                ),
                stdout_digest=str(
                    pre_push_remote_verification_result.get("stdout_digest", ""),
                ),
            )
            or receipt.get("pre_push_remote_verification_output_digest_bound")
            is not True
            or receipt.get("pre_push_remote_verification_observed_head")
            != receipt.get("pre_push_remote_head")
            or receipt.get("pre_push_remote_verification_observed_ref")
            != receipt.get("remote_ref")
            or not self._post_commit_remote_verification_stdout_digest_matches(
                str(pre_push_remote_verification_result.get("stdout_digest", "")),
                head=str(
                    receipt.get("pre_push_remote_verification_observed_head", ""),
                ),
                ref=str(
                    receipt.get("pre_push_remote_verification_observed_ref", ""),
                ),
            )
        ):
            reasons.append(
                "pre-push remote verification output must bind source head and ref",
            )
        if remote_verification_result.get("command_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PUBLICATION_REMOTE_VERIFY_PROFILE
        ):
            reasons.append("remote verification result profile mismatch")
        if remote_verification_result.get("command") != expected_remote_command:
            reasons.append("remote verification command mismatch")
        if (
            remote_verification_result.get("status") != "pass"
            or remote_verification_result.get("exit_code") != 0
        ):
            reasons.append("remote verification command must pass")
        if (
            receipt.get("remote_verification_command_receipt_digest")
            != self._post_commit_publication_command_receipt_digest(
                remote_verification_result,
            )
            or remote_verification_result.get("command_receipt_digest")
            != receipt.get("remote_verification_command_receipt_digest")
        ):
            reasons.append("remote_verification_command_receipt_digest mismatch")
        if remote_verification_result.get("raw_stdout_stored") is not False:
            reasons.append("raw remote verification stdout must not be stored")
        if remote_verification_result.get("raw_stderr_stored") is not False:
            reasons.append("raw remote verification stderr must not be stored")
        if (
            receipt.get("remote_verification_output_digest")
            != self._post_commit_remote_verification_output_digest(
                observed_head=str(
                    receipt.get("remote_verification_observed_head", ""),
                ),
                observed_ref=str(
                    receipt.get("remote_verification_observed_ref", ""),
                ),
                stdout_digest=str(
                    remote_verification_result.get("stdout_digest", ""),
                ),
            )
            or receipt.get("remote_verification_output_digest_bound") is not True
            or receipt.get("remote_verification_observed_head")
            != receipt.get("remote_head")
            or receipt.get("remote_verification_observed_ref")
            != receipt.get("remote_ref")
            or not self._post_commit_remote_verification_stdout_digest_matches(
                str(remote_verification_result.get("stdout_digest", "")),
                head=str(receipt.get("remote_verification_observed_head", "")),
                ref=str(receipt.get("remote_verification_observed_ref", "")),
            )
        ):
            reasons.append("remote verification output must bind remote head and ref")
        if (
            receipt.get("protected_branch_profile")
            != PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_PROFILE
        ):
            reasons.append("protected_branch_profile mismatch")
        if receipt.get("protected_branch_provider") != (
            PARALLEL_CODEX_DEFAULT_PROTECTED_BRANCH_PROVIDER
        ):
            reasons.append("protected_branch_provider must be github")
        if receipt.get("protected_branch_ref") != "refs/heads/main":
            reasons.append("protected_branch_ref must be refs/heads/main")
        if (
            receipt.get("protected_branch_policy_digest")
            != self._post_commit_protected_branch_policy_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_ref=str(receipt.get("protected_branch_policy_ref", "")),
                required_checks=receipt.get("protected_branch_required_checks", []),
            )
            or receipt.get("protected_branch_policy_bound") is not True
        ):
            reasons.append("protected_branch_policy_digest mismatch")
        if (
            receipt.get("protected_branch_status")
            != PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_REQUIRED_STATUS
        ):
            reasons.append("protected branch must be protected before GitHub handoff")
        if not self._protected_branch_required_checks_bound(
            receipt.get("protected_branch_required_checks", []),
        ):
            reasons.append("protected branch must require reference verification checks")
        if (
            receipt.get("protected_branch_required_check_count")
            != len(_dedupe_strings(receipt.get("protected_branch_required_checks", [])))
        ):
            reasons.append("protected_branch_required_check_count mismatch")
        expected_freshness_digest = (
            self._post_commit_protected_branch_freshness_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_ref=str(receipt.get("protected_branch_policy_ref", "")),
                policy_digest=str(receipt.get("protected_branch_policy_digest", "")),
                checked_at_ref=str(
                    receipt.get("protected_branch_policy_checked_at_ref", ""),
                ),
                freshness_window_seconds=_coerce_int(
                    receipt.get("protected_branch_policy_freshness_window_seconds"),
                    0,
                ),
                freshness_status=str(
                    receipt.get("protected_branch_policy_freshness_status", ""),
                ),
            )
        )
        if receipt.get("protected_branch_policy_freshness_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESHNESS_PROFILE
        ):
            reasons.append("protected_branch_policy_freshness_profile mismatch")
        if receipt.get("protected_branch_policy_freshness_digest") != (
            expected_freshness_digest
        ):
            reasons.append("protected_branch_policy_freshness_digest mismatch")
        if receipt.get("protected_branch_policy_freshness_digest_bound") is not True:
            reasons.append("protected branch policy freshness digest must be bound")
        if receipt.get("protected_branch_policy_freshness_status") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_FRESH_STATUS
        ):
            reasons.append("protected branch provider policy freshness must be fresh")
        if not (
            0
            < _coerce_int(
                receipt.get("protected_branch_policy_freshness_window_seconds"),
                0,
            )
            <= PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
        ):
            reasons.append("protected branch provider policy freshness window expired")
        expected_timestamp_digest = (
            self._post_commit_protected_branch_timestamp_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                policy_digest=str(receipt.get("protected_branch_policy_digest", "")),
                timestamp_ref=str(
                    receipt.get("protected_branch_provider_timestamp_ref", ""),
                ),
                timestamp_status=str(
                    receipt.get("protected_branch_provider_timestamp_status", ""),
                ),
                timestamp_signature_digest=str(
                    receipt.get(
                        "protected_branch_provider_timestamp_signature_digest",
                        "",
                    ),
                ),
            )
        )
        if receipt.get("protected_branch_provider_timestamp_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_PROFILE
        ):
            reasons.append("protected_branch_provider_timestamp_profile mismatch")
        if receipt.get("protected_branch_provider_timestamp_digest") != (
            expected_timestamp_digest
        ):
            reasons.append("protected_branch_provider_timestamp_digest mismatch")
        if receipt.get("protected_branch_provider_timestamp_digest_bound") is not True:
            reasons.append("protected branch provider timestamp digest must be bound")
        if receipt.get("protected_branch_provider_timestamp_status") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_SIGNED_STATUS
        ):
            reasons.append("protected branch provider timestamp must be signed-current")
        if not _is_sha256(
            receipt.get("protected_branch_provider_timestamp_signature_digest"),
        ):
            reasons.append("protected branch provider timestamp signature must bind")
        expected_replay_digest = (
            self._post_commit_protected_branch_timestamp_replay_digest(
                provider=str(receipt.get("protected_branch_provider", "")),
                branch_ref=str(receipt.get("protected_branch_ref", "")),
                timestamp_ref=str(
                    receipt.get("protected_branch_provider_timestamp_ref", ""),
                ),
                nonce_ref=str(
                    receipt.get("protected_branch_provider_timestamp_nonce_ref", ""),
                ),
                replay_status=str(
                    receipt.get(
                        "protected_branch_provider_timestamp_replay_status",
                        "",
                    ),
                ),
            )
        )
        if receipt.get("protected_branch_provider_timestamp_replay_profile") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_REPLAY_PROFILE
        ):
            reasons.append(
                "protected_branch_provider_timestamp_replay_profile mismatch",
            )
        if receipt.get("protected_branch_provider_timestamp_replay_digest") != (
            expected_replay_digest
        ):
            reasons.append(
                "protected_branch_provider_timestamp_replay_digest mismatch",
            )
        if (
            receipt.get(
                "protected_branch_provider_timestamp_replay_digest_bound",
            )
            is not True
        ):
            reasons.append(
                "protected branch provider timestamp replay digest must be bound",
            )
        if receipt.get("protected_branch_provider_timestamp_replay_status") != (
            PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_TIMESTAMP_UNIQUE_STATUS
        ):
            reasons.append("protected branch provider timestamp replay must be unique")
        if (
            receipt.get("protected_branch_receipt_digest")
            != self._post_commit_protected_branch_receipt_digest(receipt)
            or receipt.get("protected_branch_receipt_digest_bound") is not True
        ):
            reasons.append("protected_branch_receipt_digest mismatch")
        if (
            receipt.get("status_check_profile")
            != PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_SUITE_PROFILE
        ):
            reasons.append("status_check_profile mismatch")
        if receipt.get("status_check_provider") != (
            PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_PROVIDER
        ):
            reasons.append("status check provider must be github")
        if receipt.get("status_check_commit_head") != receipt.get("remote_head"):
            reasons.append("status check commit head must match remote head")
        if receipt.get("status_check_required_checks") != (
            receipt.get("protected_branch_required_checks")
        ):
            reasons.append("status check required checks must mirror branch policy")
        if receipt.get("status_check_result_count") != len(status_check_results):
            reasons.append("status_check_result_count mismatch")
        if not self._post_commit_status_check_results_bound(status_check_results):
            reasons.append("status check result digests must be bound")
        if receipt.get("status_check_results_bound") is not True:
            reasons.append("status_check_results_bound must be true")
        expected_status_check_suite_digest = (
            self._post_commit_status_check_suite_digest(
                provider=str(receipt.get("status_check_provider", "")),
                suite_ref=str(receipt.get("status_check_suite_ref", "")),
                commit_head=str(receipt.get("status_check_commit_head", "")),
                required_checks=receipt.get("status_check_required_checks", []),
                status_check_results=status_check_results,
                all_required_passed=bool(
                    receipt.get("status_check_all_required_passed", False),
                ),
            )
        )
        if (
            receipt.get("status_check_suite_digest")
            != expected_status_check_suite_digest
            or receipt.get("status_check_suite_digest_bound") is not True
        ):
            reasons.append("status_check_suite_digest mismatch")
        expected_status_check_suite_freshness_digest = (
            self._post_commit_status_check_suite_freshness_digest(
                provider=str(receipt.get("status_check_provider", "")),
                suite_ref=str(receipt.get("status_check_suite_ref", "")),
                suite_digest=str(receipt.get("status_check_suite_digest", "")),
                checked_at_ref=str(
                    receipt.get("status_check_suite_checked_at_ref", ""),
                ),
                freshness_window_seconds=_coerce_int(
                    receipt.get("status_check_suite_freshness_window_seconds"),
                    0,
                ),
                freshness_status=str(
                    receipt.get("status_check_suite_freshness_status", ""),
                ),
            )
        )
        if receipt.get("status_check_suite_freshness_profile") != (
            PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESHNESS_PROFILE
        ):
            reasons.append("status_check_suite_freshness_profile mismatch")
        if (
            receipt.get("status_check_suite_freshness_digest")
            != expected_status_check_suite_freshness_digest
            or receipt.get("status_check_suite_freshness_digest_bound") is not True
        ):
            reasons.append("status_check_suite_freshness_digest mismatch")
        if receipt.get("status_check_suite_freshness_status") != (
            PARALLEL_CODEX_POST_COMMIT_STATUS_CHECK_FRESH_STATUS
        ):
            reasons.append("status check suite freshness must be fresh")
        if not (
            0
            < _coerce_int(
                receipt.get("status_check_suite_freshness_window_seconds"),
                0,
            )
            <= PARALLEL_CODEX_POST_COMMIT_PROTECTED_BRANCH_MAX_FRESHNESS_WINDOW_SECONDS
        ):
            reasons.append("status check suite freshness window expired")
        if not self._post_commit_status_check_all_required_passed(
            required_checks=receipt.get("status_check_required_checks", []),
            commit_head=str(receipt.get("status_check_commit_head", "")),
            status_check_results=status_check_results,
        ):
            reasons.append("all required status checks must pass before handoff")
        if receipt.get("status_check_all_required_passed") is not True:
            reasons.append("status_check_all_required_passed must be true")
        if receipt.get("raw_status_check_provider_payload_stored") is not False:
            reasons.append("raw_status_check_provider_payload_stored must be false")
        if receipt.get("raw_status_check_suite_freshness_payload_stored") is not False:
            reasons.append(
                "raw_status_check_suite_freshness_payload_stored must be false",
            )
        if receipt.get("raw_protected_branch_provider_payload_stored") is not False:
            reasons.append("raw_protected_branch_provider_payload_stored must be false")
        if (
            receipt.get("raw_protected_branch_policy_freshness_payload_stored")
            is not False
        ):
            reasons.append(
                "raw_protected_branch_policy_freshness_payload_stored must be false",
            )
        if (
            receipt.get("raw_protected_branch_provider_timestamp_payload_stored")
            is not False
        ):
            reasons.append(
                "raw_protected_branch_provider_timestamp_payload_stored must be false",
            )
        if (
            receipt.get(
                "raw_protected_branch_provider_timestamp_replay_guard_payload_stored",
            )
            is not False
        ):
            reasons.append(
                "raw_protected_branch_provider_timestamp_replay_guard_payload_stored must be false",
            )
        if receipt.get("publication_digest") != self._post_commit_publication_digest(
            receipt,
        ):
            reasons.append("publication_digest mismatch")
        if receipt.get("raw_execution_payload_stored") is not False:
            reasons.append("raw_execution_payload_stored must be false")
        if receipt.get("raw_post_commit_publication_payload_stored") is not False:
            reasons.append("raw_post_commit_publication_payload_stored must be false")
        if (
            receipt.get("raw_pre_push_remote_verification_stdout_stored")
            is not False
        ):
            reasons.append(
                "raw_pre_push_remote_verification_stdout_stored must be false",
            )
        if (
            receipt.get("raw_pre_push_remote_verification_stderr_stored")
            is not False
        ):
            reasons.append(
                "raw_pre_push_remote_verification_stderr_stored must be false",
            )
        if receipt.get("raw_push_stdout_stored") is not False:
            reasons.append("raw_push_stdout_stored must be false")
        if receipt.get("raw_push_stderr_stored") is not False:
            reasons.append("raw_push_stderr_stored must be false")
        if receipt.get("raw_remote_verification_stdout_stored") is not False:
            reasons.append("raw_remote_verification_stdout_stored must be false")
        if receipt.get("raw_remote_verification_stderr_stored") is not False:
            reasons.append("raw_remote_verification_stderr_stored must be false")
        return reasons

    def _derive_batch_blocking_reasons(self, receipt: Mapping[str, Any]) -> list[str]:
        reasons: list[str] = []
        if receipt.get("profile_id") != PARALLEL_CODEX_INTEGRATION_BATCH_PROFILE:
            reasons.append("profile_id mismatch")
        if not receipt.get("input_receipt_refs"):
            reasons.append("integration batch must include at least one worker receipt")
        if not receipt.get("accept_ready_receipt_refs"):
            reasons.append("integration batch must include at least one accept-ready receipt")
        if receipt.get("conflict_count", 0) > 0:
            reasons.append("changed file conflicts must be resolved before integration")
        if receipt.get("batch_main_head_status") != "consistent":
            reasons.append("all integrated receipts must target the same main checkout head")
        if not receipt.get("required_verifications_passed"):
            reasons.append("batch required verification commands must pass")
        if receipt.get("blocked_receipts_quarantined") is not True:
            reasons.append("blocked receipts must be quarantined from integration order")
        if (
            receipt.get("quarantine_profile")
            != PARALLEL_CODEX_INTEGRATION_BATCH_QUARANTINE_PROFILE
        ):
            reasons.append("quarantine_profile mismatch")
        if len(receipt.get("quarantined_receipt_refs", [])) != len(
            receipt.get("quarantined_receipt_digests", []),
        ):
            reasons.append(
                "quarantined receipt refs and digests must have equal length",
            )
        if receipt.get(
            "quarantined_receipt_set_digest",
        ) != self._integration_batch_quarantined_receipt_digest(
            quarantined_receipt_refs=list(
                receipt.get("quarantined_receipt_refs", []),
            ),
            quarantined_receipt_digests=list(
                receipt.get("quarantined_receipt_digests", []),
            ),
        ):
            reasons.append("quarantined_receipt_set_digest mismatch")
        if receipt.get("raw_worker_receipt_payload_stored") is not False:
            reasons.append("raw_worker_receipt_payload_stored must be false")
        if receipt.get("raw_conflict_payload_stored") is not False:
            reasons.append("raw_conflict_payload_stored must be false")
        if receipt.get("raw_verification_payload_stored") is not False:
            reasons.append("raw_verification_payload_stored must be false")
        return reasons

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
        workspace_marker_only_changed_files = list(
            receipt.get("workspace_marker_only_changed_files", []),
        )
        workspace_marker_diff_summaries = list(
            receipt.get("workspace_marker_diff_summaries", []),
        )
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
                remote_source_revocation_timestamp_nonce_ref=str(
                    receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
                ),
                remote_source_revocation_timestamp_previous_nonce_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_previous_nonce_digest",
                        "",
                    ),
                ),
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_signature_digest mismatch"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_replay_guard_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_replay_guard_profile mismatch"
                )
            if not receipt.get("remote_source_revocation_timestamp_nonce_ref"):
                reasons.append(
                    "remote source revocation timestamp nonce ref must not be empty"
                )
            if not _is_sha256(
                receipt.get(
                    "remote_source_revocation_timestamp_previous_nonce_digest"
                )
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_previous_nonce_digest must be sha256"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_replay_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS
            ):
                reasons.append(
                    "remote source revocation timestamp replay status must be unique"
                )
            if (
                receipt.get("remote_source_content_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE
            ):
                reasons.append("remote_source_content_profile mismatch")
            if not receipt.get("remote_source_content_ref"):
                reasons.append("remote source content ref must not be empty")
            if (
                receipt.get("remote_source_content_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS
            ):
                reasons.append("remote source content status must be bound")
            if not _is_commit(receipt.get("remote_source_head_commit")):
                reasons.append("remote_source_head_commit must be a 40 character hex commit")
            if not _is_sha256(receipt.get("remote_source_tree_digest")):
                reasons.append("remote_source_tree_digest must be sha256")
            if not _is_sha256(receipt.get("remote_source_diff_digest")):
                reasons.append("remote_source_diff_digest must be sha256")
            if not _is_sha256(receipt.get("remote_source_content_digest")):
                reasons.append("remote_source_content_digest must be sha256")
            elif receipt.get(
                "remote_source_content_digest"
            ) != self._remote_source_content_digest(
                remote_source_content_ref=str(
                    receipt.get("remote_source_content_ref", ""),
                ),
                remote_source_content_status=str(
                    receipt.get("remote_source_content_status", ""),
                ),
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                remote_source_head_commit=str(
                    receipt.get("remote_source_head_commit", ""),
                ),
                remote_source_tree_digest=str(
                    receipt.get("remote_source_tree_digest", ""),
                ),
                remote_source_diff_digest=str(
                    receipt.get("remote_source_diff_digest", ""),
                ),
            ):
                reasons.append("remote_source_content_digest mismatch")
            if receipt.get("remote_source_content_bound") is not True:
                reasons.append("remote_source_content_bound must be true")
            if (
                receipt.get("remote_source_ancestry_profile")
                != PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
            ):
                reasons.append("remote_source_ancestry_profile mismatch")
            if not _is_commit(receipt.get("remote_source_base_commit")):
                reasons.append("remote_source_base_commit must be a 40 character hex commit")
            if not _is_commit(receipt.get("remote_source_merge_base_commit")):
                reasons.append(
                    "remote_source_merge_base_commit must be a 40 character hex commit"
                )
            if receipt.get("remote_source_base_commit") != receipt.get(
                "worker_base_commit"
            ):
                reasons.append("remote_source_base_commit must match worker_base_commit")
            if receipt.get("remote_source_merge_base_commit") != receipt.get(
                "worker_base_commit"
            ):
                reasons.append(
                    "remote_source_merge_base_commit must match worker_base_commit"
                )
            if (
                receipt.get("remote_source_ancestry_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS
            ):
                reasons.append("remote source ancestry status must be ancestor-bound")
            if not _is_sha256(receipt.get("remote_source_ancestry_digest")):
                reasons.append("remote_source_ancestry_digest must be sha256")
            elif receipt.get(
                "remote_source_ancestry_digest"
            ) != self._remote_source_ancestry_digest(
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                worker_base_commit=str(receipt.get("worker_base_commit", "")),
                remote_source_head_commit=str(
                    receipt.get("remote_source_head_commit", ""),
                ),
                remote_source_base_commit=str(
                    receipt.get("remote_source_base_commit", ""),
                ),
                remote_source_merge_base_commit=str(
                    receipt.get("remote_source_merge_base_commit", ""),
                ),
                remote_source_ancestry_status=str(
                    receipt.get("remote_source_ancestry_status", ""),
                ),
                remote_source_content_digest=str(
                    receipt.get("remote_source_content_digest", ""),
                ),
            ):
                reasons.append("remote_source_ancestry_digest mismatch")
            if receipt.get("remote_source_ancestry_bound") is not True:
                reasons.append("remote_source_ancestry_bound must be true")
            if not _is_sha256(
                receipt.get("remote_source_revocation_timestamp_replay_guard_digest")
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_replay_guard_digest must be sha256"
                )
            elif receipt.get(
                "remote_source_revocation_timestamp_replay_guard_digest"
            ) != self._remote_source_revocation_timestamp_replay_guard_digest(
                remote_branch_ref=str(receipt.get("remote_branch_ref", "")),
                remote_pr_ref=str(receipt.get("remote_pr_ref", "")),
                remote_source_revocation_timestamp_nonce_ref=str(
                    receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
                ),
                remote_source_revocation_timestamp_previous_nonce_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_previous_nonce_digest",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_signature_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_signature_digest",
                        "",
                    ),
                ),
                remote_source_revocation_timestamp_replay_status=str(
                    receipt.get("remote_source_revocation_timestamp_replay_status", ""),
                ),
            ):
                reasons.append(
                    "remote_source_revocation_timestamp_replay_guard_digest mismatch"
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
                remote_source_revocation_timestamp_replay_guard_digest=str(
                    receipt.get(
                        "remote_source_revocation_timestamp_replay_guard_digest",
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
                receipt.get("remote_source_revocation_timestamp_nonce_ref"),
                receipt.get(
                    "remote_source_revocation_timestamp_previous_nonce_digest"
                ),
                receipt.get("remote_source_revocation_timestamp_replay_guard_digest"),
                receipt.get("remote_source_content_ref"),
                receipt.get("remote_source_head_commit"),
                receipt.get("remote_source_tree_digest"),
                receipt.get("remote_source_diff_digest"),
                receipt.get("remote_source_content_digest"),
                receipt.get("remote_source_base_commit"),
                receipt.get("remote_source_merge_base_commit"),
                receipt.get("remote_source_ancestry_digest"),
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
            if (
                receipt.get("remote_source_revocation_timestamp_replay_guard_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote revocation timestamp replay guard not-applicable"
                )
            if (
                receipt.get("remote_source_revocation_timestamp_replay_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote revocation timestamp replay status not-applicable"
                )
            if (
                receipt.get("remote_source_content_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote source content not-applicable"
                )
            if (
                receipt.get("remote_source_ancestry_profile")
                != PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
            ):
                reasons.append(
                    "non-remote result must mark remote source ancestry not-applicable"
                )
            if (
                receipt.get("remote_source_ancestry_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote source ancestry status not-applicable"
                )
            if (
                receipt.get("remote_source_content_status")
                != PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
            ):
                reasons.append(
                    "non-remote result must mark remote source content status not-applicable"
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
            remote_source_revocation_timestamp_replay_guard_profile=str(
                receipt.get(
                    "remote_source_revocation_timestamp_replay_guard_profile",
                    "",
                ),
            ),
            remote_source_revocation_timestamp_nonce_ref=str(
                receipt.get("remote_source_revocation_timestamp_nonce_ref", ""),
            ),
            remote_source_revocation_timestamp_previous_nonce_digest=str(
                receipt.get(
                    "remote_source_revocation_timestamp_previous_nonce_digest",
                    "",
                ),
            ),
            remote_source_revocation_timestamp_replay_status=str(
                receipt.get("remote_source_revocation_timestamp_replay_status", ""),
            ),
            remote_source_revocation_timestamp_replay_guard_digest=str(
                receipt.get(
                    "remote_source_revocation_timestamp_replay_guard_digest",
                    "",
                ),
            ),
            remote_source_content_profile=str(
                receipt.get("remote_source_content_profile", ""),
            ),
            remote_source_content_ref=str(
                receipt.get("remote_source_content_ref", ""),
            ),
            remote_source_content_status=str(
                receipt.get("remote_source_content_status", ""),
            ),
            remote_source_head_commit=str(
                receipt.get("remote_source_head_commit", ""),
            ),
            remote_source_tree_digest=str(
                receipt.get("remote_source_tree_digest", ""),
            ),
            remote_source_diff_digest=str(
                receipt.get("remote_source_diff_digest", ""),
            ),
            remote_source_content_digest=str(
                receipt.get("remote_source_content_digest", ""),
            ),
            remote_source_ancestry_profile=str(
                receipt.get("remote_source_ancestry_profile", ""),
            ),
            remote_source_base_commit=str(
                receipt.get("remote_source_base_commit", ""),
            ),
            remote_source_merge_base_commit=str(
                receipt.get("remote_source_merge_base_commit", ""),
            ),
            remote_source_ancestry_status=str(
                receipt.get("remote_source_ancestry_status", ""),
            ),
            remote_source_ancestry_digest=str(
                receipt.get("remote_source_ancestry_digest", ""),
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
        if (
            receipt.get(
                "raw_remote_revocation_timestamp_replay_guard_payload_stored"
            )
            is not False
        ):
            reasons.append(
                "raw_remote_revocation_timestamp_replay_guard_payload_stored must be false"
            )
        if receipt.get("raw_remote_source_content_payload_stored") is not False:
            reasons.append("raw_remote_source_content_payload_stored must be false")
        if receipt.get("raw_remote_source_ancestry_payload_stored") is not False:
            reasons.append("raw_remote_source_ancestry_payload_stored must be false")
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
        if (
            receipt.get("workspace_marker_hygiene_profile")
            != PARALLEL_CODEX_WORKSPACE_MARKER_HYGIENE_PROFILE
        ):
            reasons.append("workspace_marker_hygiene_profile mismatch")
        if (
            receipt.get("workspace_marker_classifier_profile")
            != PARALLEL_CODEX_WORKSPACE_MARKER_CLASSIFIER_PROFILE
        ):
            reasons.append("workspace_marker_classifier_profile mismatch")
        if receipt.get("workspace_marker_diff_summary_count") != len(
            workspace_marker_diff_summaries,
        ):
            reasons.append("workspace_marker_diff_summary_count mismatch")
        if receipt.get("workspace_marker_only_change_count") != len(
            workspace_marker_only_changed_files,
        ):
            reasons.append("workspace_marker_only_change_count mismatch")
        reasons.extend(
            self._workspace_marker_diff_summary_reasons(
                workspace_marker_diff_summaries=workspace_marker_diff_summaries,
                changed_files=changed_files,
            )
        )
        marker_file_set = set(workspace_marker_only_changed_files)
        changed_file_set = set(changed_files)
        if not marker_file_set.issubset(changed_file_set):
            reasons.append("workspace marker-only files must be subset of changed_files")
        classifier_marker_files = self._workspace_marker_classifier_marker_files(
            workspace_marker_diff_summaries,
        )
        if not set(classifier_marker_files).issubset(marker_file_set):
            reasons.append(
                "workspace marker classifier files must be reflected in workspace_marker_only_changed_files"
            )
        expected_workspace_marker_classifier_digest = (
            self._workspace_marker_classifier_digest(
                workspace_marker_diff_summaries=workspace_marker_diff_summaries,
                workspace_marker_only_changed_files=(
                    workspace_marker_only_changed_files
                ),
            )
        )
        if (
            receipt.get("workspace_marker_classifier_digest")
            != expected_workspace_marker_classifier_digest
        ):
            reasons.append("workspace_marker_classifier_digest mismatch")
        expected_workspace_marker_hygiene_status = (
            self._workspace_marker_hygiene_status(
                changed_files=changed_files,
                workspace_marker_only_changed_files=(
                    workspace_marker_only_changed_files
                ),
            )
        )
        if (
            expected_workspace_marker_hygiene_status
            == PARALLEL_CODEX_WORKSPACE_MARKER_BLOCKED_STATUS
        ):
            reasons.append(
                "workspace marker-only changes cannot be the only integration payload"
            )
        if (
            receipt.get("workspace_marker_hygiene_status")
            != expected_workspace_marker_hygiene_status
        ):
            reasons.append("workspace_marker_hygiene_status mismatch")
        if receipt.get(
            "workspace_marker_hygiene_digest",
        ) != self._workspace_marker_hygiene_digest(
            changed_files=changed_files,
            workspace_marker_only_changed_files=workspace_marker_only_changed_files,
            workspace_marker_hygiene_status=expected_workspace_marker_hygiene_status,
            workspace_marker_classifier_digest=(
                expected_workspace_marker_classifier_digest
            ),
        ):
            reasons.append("workspace_marker_hygiene_digest mismatch")
        if receipt.get("raw_workspace_marker_payload_stored") is not False:
            reasons.append("raw_workspace_marker_payload_stored must be false")
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
    def classify_workspace_marker_diff_summaries(
        *,
        changed_files: Sequence[str],
        workspace_diff_by_file: Mapping[str, str],
        workspace_patch_segments_by_file: Mapping[
            str,
            Sequence[Mapping[str, Any]],
        ]
        | None = None,
    ) -> list[Dict[str, Any]]:
        """Classify marker-only diffs without persisting raw diff or segment payloads."""

        summaries: list[Dict[str, Any]] = []
        normalized_files = _dedupe_strings(changed_files)
        patch_segments_by_file = workspace_patch_segments_by_file or {}
        for file_path in normalized_files:
            patch_segments = list(patch_segments_by_file.get(file_path, []))
            if patch_segments:
                summaries.append(
                    ParallelCodexOrchestrationService._classify_workspace_patch_segments(
                        file_path=file_path,
                        patch_segments=patch_segments,
                    )
                )
                continue
            diff_text = str(workspace_diff_by_file.get(file_path, ""))
            if not diff_text:
                continue
            added_line_count = 0
            removed_line_count = 0
            marker_added_line_count = 0
            non_marker_added_line_count = 0
            for line in diff_text.splitlines():
                if line.startswith("+++") or line.startswith("---"):
                    continue
                if line.startswith("+"):
                    added_line_count += 1
                    if "workspace-enacted:" in line[1:].strip():
                        marker_added_line_count += 1
                    else:
                        non_marker_added_line_count += 1
                elif line.startswith("-"):
                    removed_line_count += 1
            if added_line_count == 0 and removed_line_count == 0:
                continue
            classifier_status = (
                "marker-only"
                if (
                    added_line_count > 0
                    and removed_line_count == 0
                    and marker_added_line_count == added_line_count
                    and non_marker_added_line_count == 0
                )
                else "substantive"
            )
            summaries.append(
                {
                    "file_path": file_path,
                    "classifier_evidence_profile": (
                        PARALLEL_CODEX_WORKSPACE_MARKER_DIFF_LINE_EVIDENCE_PROFILE
                    ),
                    "diff_digest": sha256_text(diff_text),
                    "segment_manifest_digest": "",
                    "segment_count": 0,
                    "marker_segment_count": 0,
                    "substantive_segment_count": 0,
                    "added_line_count": added_line_count,
                    "removed_line_count": removed_line_count,
                    "marker_added_line_count": marker_added_line_count,
                    "non_marker_added_line_count": non_marker_added_line_count,
                    "classifier_status": classifier_status,
                    "raw_diff_payload_stored": False,
                    "raw_segment_payload_stored": False,
                }
            )
        return sorted(summaries, key=lambda summary: summary["file_path"])

    @staticmethod
    def _classify_workspace_patch_segments(
        *,
        file_path: str,
        patch_segments: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        normalized_segments: list[Dict[str, Any]] = []
        added_line_count = 0
        removed_line_count = 0
        marker_added_line_count = 0
        non_marker_added_line_count = 0
        marker_segment_count = 0
        substantive_segment_count = 0

        for index, segment in enumerate(patch_segments, start=1):
            operation = str(segment.get("operation", "")).strip().lower()
            if operation not in {"add", "remove", "modify", "context"}:
                operation = "modify"
            line_count = _coerce_int(segment.get("line_count"), 1)
            if line_count < 0:
                line_count = 0
            marker_segment = bool(segment.get("contains_workspace_marker", False))
            content_digest = str(segment.get("content_digest", "")).strip()
            if not _is_sha256(content_digest):
                content_digest = sha256_text(
                    canonical_json(
                        {
                            "file_path": file_path,
                            "segment_index": index,
                            "operation": operation,
                            "line_count": line_count,
                            "contains_workspace_marker": marker_segment,
                        }
                    )
                )

            if operation == "add":
                added_line_count += line_count
                if marker_segment:
                    marker_added_line_count += line_count
                    marker_segment_count += 1
                else:
                    non_marker_added_line_count += line_count
                    substantive_segment_count += 1
            elif operation in {"remove", "modify"}:
                if operation == "remove":
                    removed_line_count += line_count
                else:
                    added_line_count += line_count
                    removed_line_count += line_count
                substantive_segment_count += 1

            normalized_segments.append(
                {
                    "segment_index": index,
                    "operation": operation,
                    "line_count": line_count,
                    "contains_workspace_marker": marker_segment,
                    "content_digest": content_digest,
                }
            )

        classifier_status = (
            "marker-only"
            if (
                added_line_count > 0
                and removed_line_count == 0
                and marker_added_line_count == added_line_count
                and non_marker_added_line_count == 0
                and marker_segment_count > 0
                and substantive_segment_count == 0
            )
            else "substantive"
        )
        segment_manifest_digest = sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE
                    ),
                    "file_path": file_path,
                    "segments": normalized_segments,
                }
            )
        )
        return {
            "file_path": file_path,
            "classifier_evidence_profile": (
                PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE
            ),
            "diff_digest": segment_manifest_digest,
            "segment_manifest_digest": segment_manifest_digest,
            "segment_count": len(normalized_segments),
            "marker_segment_count": marker_segment_count,
            "substantive_segment_count": substantive_segment_count,
            "added_line_count": added_line_count,
            "removed_line_count": removed_line_count,
            "marker_added_line_count": marker_added_line_count,
            "non_marker_added_line_count": non_marker_added_line_count,
            "classifier_status": classifier_status,
            "raw_diff_payload_stored": False,
            "raw_segment_payload_stored": False,
        }

    @staticmethod
    def _workspace_marker_classifier_marker_files(
        workspace_marker_diff_summaries: Sequence[Mapping[str, Any]],
    ) -> list[str]:
        return _dedupe_strings(
            [
                str(summary.get("file_path", "")).strip()
                for summary in workspace_marker_diff_summaries
                if summary.get("classifier_status") == "marker-only"
            ]
        )

    @staticmethod
    def _workspace_marker_classifier_digest(
        *,
        workspace_marker_diff_summaries: Sequence[Mapping[str, Any]],
        workspace_marker_only_changed_files: Sequence[str],
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_WORKSPACE_MARKER_CLASSIFIER_PROFILE
                    ),
                    "workspace_marker_diff_summaries": [
                        dict(summary) for summary in workspace_marker_diff_summaries
                    ],
                    "workspace_marker_only_changed_files": list(
                        workspace_marker_only_changed_files,
                    ),
                }
            )
        )

    @staticmethod
    def _workspace_marker_diff_summary_reasons(
        *,
        workspace_marker_diff_summaries: Sequence[Mapping[str, Any]],
        changed_files: Sequence[str],
    ) -> list[str]:
        reasons: list[str] = []
        changed_file_set = set(changed_files)
        seen_paths: set[str] = set()
        for summary in workspace_marker_diff_summaries:
            file_path = str(summary.get("file_path", "")).strip()
            if not file_path:
                reasons.append("workspace marker diff summary file_path must not be empty")
                continue
            if file_path in seen_paths:
                reasons.append("workspace marker diff summary file_path must be unique")
            seen_paths.add(file_path)
            if file_path not in changed_file_set:
                reasons.append(
                    "workspace marker diff summary file_path must be in changed_files"
                )
            if not _is_sha256(summary.get("diff_digest")):
                reasons.append("workspace marker diff summary digest must be sha256")
            classifier_evidence_profile = summary.get("classifier_evidence_profile")
            if classifier_evidence_profile not in {
                PARALLEL_CODEX_WORKSPACE_MARKER_DIFF_LINE_EVIDENCE_PROFILE,
                PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE,
            }:
                reasons.append(
                    "workspace marker diff summary classifier_evidence_profile mismatch"
                )
            segment_count = _coerce_int(summary.get("segment_count"), -1)
            marker_segment_count = _coerce_int(
                summary.get("marker_segment_count"),
                -1,
            )
            substantive_segment_count = _coerce_int(
                summary.get("substantive_segment_count"),
                -1,
            )
            added_line_count = _coerce_int(summary.get("added_line_count"), -1)
            removed_line_count = _coerce_int(summary.get("removed_line_count"), -1)
            marker_added_line_count = _coerce_int(
                summary.get("marker_added_line_count"),
                -1,
            )
            non_marker_added_line_count = _coerce_int(
                summary.get("non_marker_added_line_count"),
                -1,
            )
            if min(
                added_line_count,
                removed_line_count,
                marker_added_line_count,
                non_marker_added_line_count,
                segment_count,
                marker_segment_count,
                substantive_segment_count,
            ) < 0:
                reasons.append("workspace marker diff summary counts must be non-negative")
            if marker_segment_count + substantive_segment_count > segment_count:
                reasons.append(
                    "workspace marker diff summary segment counts must not exceed segment_count"
                )
            segment_manifest_digest = str(
                summary.get("segment_manifest_digest", ""),
            ).strip()
            if (
                classifier_evidence_profile
                == PARALLEL_CODEX_WORKSPACE_MARKER_PATCH_SEGMENT_EVIDENCE_PROFILE
                and not _is_sha256(segment_manifest_digest)
            ):
                reasons.append(
                    "workspace marker segment manifest digest must be sha256"
                )
            if (
                classifier_evidence_profile
                == PARALLEL_CODEX_WORKSPACE_MARKER_DIFF_LINE_EVIDENCE_PROFILE
                and segment_manifest_digest
            ):
                reasons.append(
                    "workspace marker diff-line summary must not carry segment_manifest_digest"
                )
            if marker_added_line_count + non_marker_added_line_count != added_line_count:
                reasons.append(
                    "workspace marker diff summary added counts must sum to added_line_count"
                )
            classifier_status = summary.get("classifier_status")
            if classifier_status not in {"marker-only", "substantive"}:
                reasons.append("workspace marker diff summary classifier_status mismatch")
            if classifier_status == "marker-only" and not (
                added_line_count > 0
                and removed_line_count == 0
                and marker_added_line_count == added_line_count
                and non_marker_added_line_count == 0
            ):
                reasons.append(
                    "marker-only diff summary must contain only added workspace markers"
                )
            if summary.get("raw_diff_payload_stored") is not False:
                reasons.append(
                    "workspace marker diff summary raw_diff_payload_stored must be false"
                )
            if summary.get("raw_segment_payload_stored") is not False:
                reasons.append(
                    "workspace marker diff summary raw_segment_payload_stored must be false"
                )
        return reasons

    @staticmethod
    def _workspace_marker_hygiene_status(
        *,
        changed_files: Sequence[str],
        workspace_marker_only_changed_files: Sequence[str],
    ) -> str:
        marker_files = set(workspace_marker_only_changed_files)
        if not marker_files:
            return PARALLEL_CODEX_WORKSPACE_MARKER_CLEAN_STATUS
        evidence_bearing_files = [
            path for path in changed_files if path not in marker_files
        ]
        if evidence_bearing_files:
            return PARALLEL_CODEX_WORKSPACE_MARKER_REVIEWED_STATUS
        return PARALLEL_CODEX_WORKSPACE_MARKER_BLOCKED_STATUS

    @staticmethod
    def _workspace_marker_hygiene_digest(
        *,
        changed_files: Sequence[str],
        workspace_marker_only_changed_files: Sequence[str],
        workspace_marker_hygiene_status: str,
        workspace_marker_classifier_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_WORKSPACE_MARKER_HYGIENE_PROFILE,
                    "changed_files": list(changed_files),
                    "workspace_marker_only_changed_files": list(
                        workspace_marker_only_changed_files,
                    ),
                    "workspace_marker_hygiene_status": (
                        workspace_marker_hygiene_status
                    ),
                    "workspace_marker_classifier_digest": (
                        workspace_marker_classifier_digest
                    ),
                }
            )
        )

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
                    "remote_source_revocation_timestamp_replay_guard_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
                    ),
                    "remote_source_revocation_timestamp_replay_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS
                    ),
                    "remote_source_content_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE
                    ),
                    "remote_source_content_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS
                    ),
                    "remote_source_ancestry_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
                    ),
                    "remote_source_ancestry_required_status": (
                        PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS
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
                    "remote_source_revocation_timestamp_replay_guard_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
                    ),
                    "remote_source_content_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE
                    ),
                    "remote_source_ancestry_profile": (
                        PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
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
        remote_source_revocation_timestamp_nonce_ref: str,
        remote_source_revocation_timestamp_previous_nonce_digest: str,
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
                    "timestamp_nonce_ref": (
                        remote_source_revocation_timestamp_nonce_ref
                    ),
                    "previous_nonce_digest": (
                        remote_source_revocation_timestamp_previous_nonce_digest
                    ),
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_timestamp_previous_nonce_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_source_revocation_timestamp_nonce_ref: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
                    ),
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "timestamp_nonce_ref": (
                        remote_source_revocation_timestamp_nonce_ref
                    ),
                    "chain_position": "previous",
                }
            )
        )

    @staticmethod
    def _remote_source_revocation_timestamp_replay_guard_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_source_revocation_timestamp_nonce_ref: str,
        remote_source_revocation_timestamp_previous_nonce_digest: str,
        remote_source_revocation_timestamp_signature_digest: str,
        remote_source_revocation_timestamp_replay_status: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": (
                        PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
                    ),
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "timestamp_nonce_ref": (
                        remote_source_revocation_timestamp_nonce_ref
                    ),
                    "previous_nonce_digest": (
                        remote_source_revocation_timestamp_previous_nonce_digest
                    ),
                    "timestamp_signature_digest": (
                        remote_source_revocation_timestamp_signature_digest
                    ),
                    "replay_status": (
                        remote_source_revocation_timestamp_replay_status
                    ),
                }
            )
        )

    @staticmethod
    def _remote_source_head_commit(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "content_identity": "head-commit",
                }
            )
        )[:40]

    @staticmethod
    def _remote_source_tree_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_source_head_commit: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "remote_source_head_commit": remote_source_head_commit,
                    "content_identity": "tree",
                }
            )
        )

    @staticmethod
    def _remote_source_diff_digest(
        *,
        changed_files: Sequence[str],
        patch_digest: str,
        workspace_marker_hygiene_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
                    "changed_files": list(changed_files),
                    "patch_digest": patch_digest,
                    "workspace_marker_hygiene_digest": workspace_marker_hygiene_digest,
                }
            )
        )

    @staticmethod
    def _remote_source_content_digest(
        *,
        remote_source_content_ref: str,
        remote_source_content_status: str,
        remote_branch_ref: str,
        remote_pr_ref: str,
        remote_source_head_commit: str,
        remote_source_tree_digest: str,
        remote_source_diff_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
                    "remote_source_content_ref": remote_source_content_ref,
                    "remote_source_content_status": remote_source_content_status,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "remote_source_head_commit": remote_source_head_commit,
                    "remote_source_tree_digest": remote_source_tree_digest,
                    "remote_source_diff_digest": remote_source_diff_digest,
                }
            )
        )

    @staticmethod
    def _remote_source_ancestry_digest(
        *,
        remote_branch_ref: str,
        remote_pr_ref: str,
        worker_base_commit: str,
        remote_source_head_commit: str,
        remote_source_base_commit: str,
        remote_source_merge_base_commit: str,
        remote_source_ancestry_status: str,
        remote_source_content_digest: str,
    ) -> str:
        return sha256_text(
            canonical_json(
                {
                    "profile_id": PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE,
                    "remote_branch_ref": remote_branch_ref,
                    "remote_pr_ref": remote_pr_ref,
                    "worker_base_commit": worker_base_commit,
                    "remote_source_head_commit": remote_source_head_commit,
                    "remote_source_base_commit": remote_source_base_commit,
                    "remote_source_merge_base_commit": remote_source_merge_base_commit,
                    "remote_source_ancestry_status": remote_source_ancestry_status,
                    "remote_source_content_digest": remote_source_content_digest,
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
        remote_source_revocation_timestamp_replay_guard_digest: str,
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
                    "timestamp_replay_guard_digest": (
                        remote_source_revocation_timestamp_replay_guard_digest
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
        remote_source_revocation_timestamp_replay_guard_profile: str,
        remote_source_revocation_timestamp_nonce_ref: str,
        remote_source_revocation_timestamp_previous_nonce_digest: str,
        remote_source_revocation_timestamp_replay_status: str,
        remote_source_revocation_timestamp_replay_guard_digest: str,
        remote_source_content_profile: str = (
            PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
        ),
        remote_source_content_ref: str = "",
        remote_source_content_status: str = (
            PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
        ),
        remote_source_head_commit: str = "",
        remote_source_tree_digest: str = "",
        remote_source_diff_digest: str = "",
        remote_source_content_digest: str = "",
        remote_source_ancestry_profile: str = (
            PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
        ),
        remote_source_base_commit: str = "",
        remote_source_merge_base_commit: str = "",
        remote_source_ancestry_status: str = (
            PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
        ),
        remote_source_ancestry_digest: str = "",
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
                    "remote_source_revocation_timestamp_replay_guard_profile": (
                        remote_source_revocation_timestamp_replay_guard_profile
                    ),
                    "remote_source_revocation_timestamp_nonce_ref": (
                        remote_source_revocation_timestamp_nonce_ref
                    ),
                    "remote_source_revocation_timestamp_previous_nonce_digest": (
                        remote_source_revocation_timestamp_previous_nonce_digest
                    ),
                    "remote_source_revocation_timestamp_replay_status": (
                        remote_source_revocation_timestamp_replay_status
                    ),
                    "remote_source_revocation_timestamp_replay_guard_digest": (
                        remote_source_revocation_timestamp_replay_guard_digest
                    ),
                    "remote_source_content_profile": remote_source_content_profile,
                    "remote_source_content_ref": remote_source_content_ref,
                    "remote_source_content_status": remote_source_content_status,
                    "remote_source_head_commit": remote_source_head_commit,
                    "remote_source_tree_digest": remote_source_tree_digest,
                    "remote_source_diff_digest": remote_source_diff_digest,
                    "remote_source_content_digest": remote_source_content_digest,
                    "remote_source_ancestry_profile": remote_source_ancestry_profile,
                    "remote_source_base_commit": remote_source_base_commit,
                    "remote_source_merge_base_commit": remote_source_merge_base_commit,
                    "remote_source_ancestry_status": remote_source_ancestry_status,
                    "remote_source_ancestry_digest": remote_source_ancestry_digest,
                }
            )
        )

    def _normalize_remote_metadata(
        self,
        *,
        source_system: str,
        changed_files: Sequence[str],
        patch_digest: str,
        workspace_marker_hygiene_digest: str,
        worker_base_commit: str,
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
        remote_source_revocation_timestamp_nonce_ref: str,
        remote_source_revocation_timestamp_previous_nonce_digest: str,
        remote_source_revocation_timestamp_replay_status: str,
        remote_source_revocation_timestamp_replay_guard_digest: str,
        remote_source_content_ref: str,
        remote_source_content_status: str,
        remote_source_head_commit: str,
        remote_source_tree_digest: str,
        remote_source_diff_digest: str,
        remote_source_content_digest: str,
        remote_source_base_commit: str,
        remote_source_merge_base_commit: str,
        remote_source_ancestry_status: str,
        remote_source_ancestry_digest: str,
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
                "remote_source_revocation_timestamp_replay_guard_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_revocation_timestamp_nonce_ref": "",
                "remote_source_revocation_timestamp_previous_nonce_digest": "",
                "remote_source_revocation_timestamp_replay_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_revocation_timestamp_replay_guard_digest": "",
                "remote_source_content_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_content_ref": "",
                "remote_source_content_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_head_commit": "",
                "remote_source_tree_digest": "",
                "remote_source_diff_digest": "",
                "remote_source_content_digest": "",
                "remote_source_content_bound": True,
                "remote_source_ancestry_profile": (
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                "remote_source_base_commit": "",
                "remote_source_merge_base_commit": "",
                "remote_source_ancestry_status": (
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                "remote_source_ancestry_digest": "",
                "remote_source_ancestry_bound": True,
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
                remote_source_revocation_timestamp_replay_guard_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_revocation_timestamp_nonce_ref="",
                remote_source_revocation_timestamp_previous_nonce_digest="",
                remote_source_revocation_timestamp_replay_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_revocation_timestamp_replay_guard_digest="",
                remote_source_content_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_content_ref="",
                remote_source_content_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_head_commit="",
                remote_source_tree_digest="",
                remote_source_diff_digest="",
                remote_source_content_digest="",
                remote_source_ancestry_profile=(
                    PARALLEL_CODEX_REMOTE_METADATA_NOT_APPLICABLE_PROFILE
                ),
                remote_source_base_commit="",
                remote_source_merge_base_commit="",
                remote_source_ancestry_status=(
                    PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_NOT_APPLICABLE_STATUS
                ),
                remote_source_ancestry_digest="",
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
        normalized_timestamp_nonce_ref = (
            remote_source_revocation_timestamp_nonce_ref.strip()
            or (
                f"{PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_REVOCATION_TIMESTAMP_NONCE_REF}"
                f"/{remote_source_key}"
            )
        )
        normalized_previous_nonce_digest = (
            remote_source_revocation_timestamp_previous_nonce_digest.strip()
        )
        if not _is_sha256(normalized_previous_nonce_digest):
            normalized_previous_nonce_digest = (
                self._remote_source_revocation_timestamp_previous_nonce_digest(
                    remote_branch_ref=remote_branch_ref.strip(),
                    remote_pr_ref=remote_pr_ref.strip(),
                    remote_source_revocation_timestamp_nonce_ref=(
                        normalized_timestamp_nonce_ref
                    ),
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
                    remote_source_revocation_timestamp_nonce_ref=(
                        normalized_timestamp_nonce_ref
                    ),
                    remote_source_revocation_timestamp_previous_nonce_digest=(
                        normalized_previous_nonce_digest
                    ),
                )
            )
        normalized_replay_status = (
            remote_source_revocation_timestamp_replay_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_UNIQUE_STATUS
        )
        normalized_replay_guard_digest = (
            remote_source_revocation_timestamp_replay_guard_digest.strip()
        )
        if not _is_sha256(normalized_replay_guard_digest):
            normalized_replay_guard_digest = (
                self._remote_source_revocation_timestamp_replay_guard_digest(
                    remote_branch_ref=remote_branch_ref.strip(),
                    remote_pr_ref=remote_pr_ref.strip(),
                    remote_source_revocation_timestamp_nonce_ref=(
                        normalized_timestamp_nonce_ref
                    ),
                    remote_source_revocation_timestamp_previous_nonce_digest=(
                        normalized_previous_nonce_digest
                    ),
                    remote_source_revocation_timestamp_signature_digest=(
                        normalized_timestamp_signature_digest
                    ),
                    remote_source_revocation_timestamp_replay_status=(
                        normalized_replay_status
                    ),
                )
            )
        normalized_content_ref = (
            remote_source_content_ref.strip()
            or f"{PARALLEL_CODEX_DEFAULT_REMOTE_SOURCE_CONTENT_REF}/{remote_source_key}"
        )
        normalized_content_status = (
            remote_source_content_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_BOUND_STATUS
        )
        normalized_head_commit = remote_source_head_commit.strip()
        if not _is_commit(normalized_head_commit):
            normalized_head_commit = self._remote_source_head_commit(
                remote_branch_ref=remote_branch_ref.strip(),
                remote_pr_ref=remote_pr_ref.strip(),
            )
        normalized_tree_digest = remote_source_tree_digest.strip()
        if not _is_sha256(normalized_tree_digest):
            normalized_tree_digest = self._remote_source_tree_digest(
                remote_branch_ref=remote_branch_ref.strip(),
                remote_pr_ref=remote_pr_ref.strip(),
                remote_source_head_commit=normalized_head_commit,
            )
        normalized_diff_digest = remote_source_diff_digest.strip()
        if not _is_sha256(normalized_diff_digest):
            normalized_diff_digest = self._remote_source_diff_digest(
                changed_files=changed_files,
                patch_digest=patch_digest,
                workspace_marker_hygiene_digest=workspace_marker_hygiene_digest,
            )
        expected_content_digest = self._remote_source_content_digest(
            remote_source_content_ref=normalized_content_ref,
            remote_source_content_status=normalized_content_status,
            remote_branch_ref=remote_branch_ref.strip(),
            remote_pr_ref=remote_pr_ref.strip(),
            remote_source_head_commit=normalized_head_commit,
            remote_source_tree_digest=normalized_tree_digest,
            remote_source_diff_digest=normalized_diff_digest,
        )
        normalized_content_digest = remote_source_content_digest.strip()
        if not _is_sha256(normalized_content_digest):
            normalized_content_digest = expected_content_digest
        normalized_base_commit = remote_source_base_commit.strip()
        if not _is_commit(normalized_base_commit):
            normalized_base_commit = worker_base_commit.strip()
        normalized_merge_base_commit = remote_source_merge_base_commit.strip()
        if not _is_commit(normalized_merge_base_commit):
            normalized_merge_base_commit = normalized_base_commit
        normalized_ancestry_status = (
            remote_source_ancestry_status.strip()
            or PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_BOUND_STATUS
        )
        expected_ancestry_digest = self._remote_source_ancestry_digest(
            remote_branch_ref=remote_branch_ref.strip(),
            remote_pr_ref=remote_pr_ref.strip(),
            worker_base_commit=worker_base_commit.strip(),
            remote_source_head_commit=normalized_head_commit,
            remote_source_base_commit=normalized_base_commit,
            remote_source_merge_base_commit=normalized_merge_base_commit,
            remote_source_ancestry_status=normalized_ancestry_status,
            remote_source_content_digest=normalized_content_digest,
        )
        normalized_ancestry_digest = remote_source_ancestry_digest.strip()
        if not _is_sha256(normalized_ancestry_digest):
            normalized_ancestry_digest = expected_ancestry_digest
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
                    remote_source_revocation_timestamp_replay_guard_digest=(
                        normalized_replay_guard_digest
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
            remote_source_revocation_timestamp_replay_guard_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
            ),
            remote_source_revocation_timestamp_nonce_ref=(
                normalized_timestamp_nonce_ref
            ),
            remote_source_revocation_timestamp_previous_nonce_digest=(
                normalized_previous_nonce_digest
            ),
            remote_source_revocation_timestamp_replay_status=normalized_replay_status,
            remote_source_revocation_timestamp_replay_guard_digest=(
                normalized_replay_guard_digest
            ),
            remote_source_content_profile=PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
            remote_source_content_ref=normalized_content_ref,
            remote_source_content_status=normalized_content_status,
            remote_source_head_commit=normalized_head_commit,
            remote_source_tree_digest=normalized_tree_digest,
            remote_source_diff_digest=normalized_diff_digest,
            remote_source_content_digest=normalized_content_digest,
            remote_source_ancestry_profile=(
                PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
            ),
            remote_source_base_commit=normalized_base_commit,
            remote_source_merge_base_commit=normalized_merge_base_commit,
            remote_source_ancestry_status=normalized_ancestry_status,
            remote_source_ancestry_digest=normalized_ancestry_digest,
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
            "remote_source_revocation_timestamp_replay_guard_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_REVOCATION_TIMESTAMP_REPLAY_GUARD_PROFILE
            ),
            "remote_source_revocation_timestamp_nonce_ref": (
                normalized_timestamp_nonce_ref
            ),
            "remote_source_revocation_timestamp_previous_nonce_digest": (
                normalized_previous_nonce_digest
            ),
            "remote_source_revocation_timestamp_replay_status": (
                normalized_replay_status
            ),
            "remote_source_revocation_timestamp_replay_guard_digest": (
                normalized_replay_guard_digest
            ),
            "remote_source_content_profile": PARALLEL_CODEX_REMOTE_SOURCE_CONTENT_PROFILE,
            "remote_source_content_ref": normalized_content_ref,
            "remote_source_content_status": normalized_content_status,
            "remote_source_head_commit": normalized_head_commit,
            "remote_source_tree_digest": normalized_tree_digest,
            "remote_source_diff_digest": normalized_diff_digest,
            "remote_source_content_digest": normalized_content_digest,
            "remote_source_content_bound": (
                normalized_content_digest == expected_content_digest
            ),
            "remote_source_ancestry_profile": (
                PARALLEL_CODEX_REMOTE_SOURCE_ANCESTRY_PROFILE
            ),
            "remote_source_base_commit": normalized_base_commit,
            "remote_source_merge_base_commit": normalized_merge_base_commit,
            "remote_source_ancestry_status": normalized_ancestry_status,
            "remote_source_ancestry_digest": normalized_ancestry_digest,
            "remote_source_ancestry_bound": (
                normalized_ancestry_digest == expected_ancestry_digest
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
