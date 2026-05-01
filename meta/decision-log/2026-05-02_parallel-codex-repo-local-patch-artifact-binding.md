---
decision_id: parallel-codex-repo-local-patch-artifact-binding-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-integration-repo-local-patch-artifact-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_integration_execution_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_integration_execution.yaml
  - evals/continuity/README.md
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_parallel_orchestration.py
  - tests/integration/test_parallel_orchestration_schema_contracts.py
---

# Decision

Parallel Codex integration execution now binds dry-run checks to repo-local
patch artifact paths before main-checkout apply.

# Rationale

The prior execution receipt used digest-only `patch://parallel-codex/...` refs
as the command target. That proved a patch artifact digest was carried, but it
did not model the repo-local patch file that a real pre-apply `git apply --check`
command would rehearse.

# Consequences

- Apply steps include `repo-local-patch-artifact-binding-v1`,
  `repo-local-patch-file`, and `artifacts/parallel-codex/*.patch`.
- Execution receipts carry `patch_artifact_manifest_digest`,
  `repo_local_patch_artifact_count`, and
  `repo_local_patch_artifacts_bound`.
- Dry-run commands now bind `git apply --check artifacts/parallel-codex/*.patch`
  to the same patch artifact digest used by the apply step.
- Raw patch payloads, dry-run stdout, and dry-run stderr remain redacted.

# Revisit Triggers

- Replace synthetic repo-local patch paths with actual materialized patch files
  when Parallel Codex receives provider-native patch payloads.
