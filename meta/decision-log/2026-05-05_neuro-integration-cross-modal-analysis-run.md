---
decision_id: neuro-integration-cross-modal-analysis-run-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_cross_modal_analysis_run.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/02-subsystems/interface/README.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - meta/glossary.md
  - tests/unit/test_neuro_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
---

# Decision

Add `neuro-cross-modal-analysis-run-v1` as a digest-only receipt for bounded
per-pair result summaries derived from the Neuro Integration Workbench
cross-modal analysis plan.

# Rationale

The workbench can plan every source-type pair, but a plan alone does not show
that an operator or coding agent can review bounded outputs. The objective calls
for questionnaire plus EEG analysis and broader neuroscience integration, so the
runtime needs a safe result surface that remains below diagnosis, subjective
equivalence, consciousness reproduction, and identity replacement claims.

# Implementation

The run receipt binds the source bundle, connector bundle, cross-modal analysis
plan, every pair digest, bounded compatibility and uncertainty summaries,
operator summaries, coding-agent next actions, and result digest set. It marks
the survey plus EEG seed result explicitly and keeps all result payloads
digest-only.

# Safety Boundary

The run is not a medical-grade analysis result and not proof of mind uploading
readiness. It stores no raw source, analysis, connector, or result payloads and
does not claim clinical diagnosis, semantic thought content, consciousness
reproduction, or identity replacement.

# Verification

Unit and integration tests assert result digest binding, public schema validity,
pair/result count equality, payload redaction, operator/coding-agent readiness,
and continued no diagnosis / consciousness / identity replacement claims.

# Revisit Triggers

- A live analysis runner starts returning execution receipts rather than
  bounded summaries.
- A source family needs a domain-specific result schema or adequacy threshold.
- Clinical, cohort-scale, or causal inference claims require separate validated
  evidence receipts.
