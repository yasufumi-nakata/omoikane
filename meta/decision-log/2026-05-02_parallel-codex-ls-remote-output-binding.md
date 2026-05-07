---
decision_id: parallel-codex-ls-remote-output-binding-2026-05-02
status: accepted
date: 2026-05-02
area: self-construction/parallel-orchestration
closes_next_gaps:
  - parallel-codex-ls-remote-output-binding
touchpoints:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
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
deciders: [yasufumi, codex-builder]
related_docs:
  - references/parallel-codex-orchestration.md
  - src/omoikane/self_construction/parallel_orchestration.py
  - src/omoikane/reference_os.py
  - specs/interfaces/selfctor.parallel_orchestration.v0.idl
  - specs/schemas/parallel_codex_post_commit_publication_receipt.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/continuity/parallel_codex_post_commit_publication.yaml
---

# Decision

Parallel Codex post-commit publication now binds the `git ls-remote
origin refs/heads/main` output digest to the observed head/ref before GitHub
handoff can become ready.

# Rationale

The previous receipt proved the remote verification command digest and recorded
the accepted `remote_head`, but it did not separately bind the command stdout
digest to an observed `refs/heads/main` line. A receipt could therefore model a
passing `ls-remote` command while leaving the relationship between command
output and accepted remote head implicit.

# Consequences

- `parallel_codex_post_commit_publication_receipt` records
  `remote_verification_output_profile`,
  `remote_verification_observed_head`, `remote_verification_observed_ref`,
  `remote_verification_output_digest`, and
  `remote_verification_output_digest_bound`.
- `ready_for_github_handoff=true` requires the observed head/ref to match the
  accepted remote head and `refs/heads/main`, and the command stdout digest to
  match that observed line.
- Output mismatch remains schema-bound but blocks publication before GitHub
  handoff.
- Raw `ls-remote` stdout remains redacted; the receipt keeps only the observed
  bounded fields and digest evidence.

# Revisit Triggers

- Replace reference-runtime output binding with live provider merge queue or
  branch protection API receipts when those become available.
