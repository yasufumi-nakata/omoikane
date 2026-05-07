---
decision_id: observation-integration-analysis-run-2026-05-05
status: accepted
date: 2026-05-05
area: interface/observation-integration-workbench
touchpoints:
  - src/omoikane/interface/observation_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.observation_integration_workbench.v0.idl
  - specs/schemas/observation_analysis_run.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/observation_integration_workbench.yaml
  - docs/02-subsystems/interface/observation-integration-workbench.md
  - docs/02-subsystems/interface/README.md
  - docs/05-research-frontiers/observation-integration.md
  - docs/07-reference-implementation/README.md
  - meta/glossary.md
  - tests/unit/test_observation_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/observation_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.observation_integration_workbench.v0.idl
  - specs/schemas/observation_analysis_run.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/observation_integration_workbench.yaml
  - docs/02-subsystems/interface/observation-integration-workbench.md
---

# Decision

Add `universal-observation-analysis-run-v1` as a digest-only run receipt for
bounded lane-level summaries in the Observation Integration Workbench.

# Rationale

The workbench already binds taxonomy, source bundle, graph, analysis plan, and
operator guide, but a plan alone does not prove that a non-specialist operator
or coding agent has bounded outputs to review. The biological and neuroscience
integration objective needs the universal observation surface to move from
planning to receipt-producing execution without crossing into diagnosis,
causal truth, complete knowledge, consciousness reproduction, or identity
replacement claims.

# Implementation

The run receipt binds the source bundle, integration graph, analysis plan, and
operator guide digests. It emits one bounded result summary for each ingest,
normalize, align, model, audit, and publish-digest lane, plus result digests,
a result digest set, review readiness, and payload redaction flags.

# Safety Boundary

The run is not a medical result, not a causal proof, not a truth-unification
artifact, and not evidence of upload readiness. It stores no raw source,
analysis, model, instruction, or result payloads.

# Verification

Unit and integration tests assert public schema validity, run digest binding,
lane result count, result digest tamper rejection, raw result payload redaction,
operator/coding-agent readiness, and continued no totality / truth /
consciousness / identity claims.

# Revisit Triggers

- A live OIW runner begins emitting domain-specific execution receipts.
- A biological source family needs a stronger lane result schema.
- Causal, diagnostic, or upload-readiness claims require separate evidence
  receipts and Guardian review.
