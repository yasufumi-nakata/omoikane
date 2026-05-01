---
decision_id: parallel-codex-command-bound-dry-run-2026-05-01
status: accepted
date: 2026-05-01
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-integration-command-bound-git-apply-dry-run
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
  - tests/integration/test_reference_runtime.py
  - tests/integration/test_cli.py
---

# Decision

Parallel Codex integration execution dry-runs are now command-bound to the
patch artifact they rehearse.

# Rationale

The execution receipt already carried pre-apply dry-run status and manifest
digests, but a dry-run result could be marked pass without proving that the
actual command checked the patch artifact associated with the ordered apply
step. That left a hidden gap between the ordered apply plan and the mutation
gate immediately before commit.

# Consequences

- Each apply step now has a `patch_artifact_ref` and `patch_artifact_digest`.
- Each pre-apply dry-run result must carry
  `command_profile=command-bound-git-apply-check-v1`,
  `git apply --check patch://...`, `patch_artifact_digest_bound=true`, and a
  `command_receipt_digest`.
- A failed dry-run remains schema-bound and blocked. A pass result whose
  command is not bound to the patch artifact is rejected by validation and
  cannot become `ready-to-apply`.
- Raw patch payloads, dry-run stdout, and dry-run stderr remain redacted.

# Revisit Triggers

- Replace digest-only patch artifact refs with actual repo-local patch files or
  provider-native merge artifacts when Parallel Codex starts materializing
  patch payloads for a standardized apply queue.
