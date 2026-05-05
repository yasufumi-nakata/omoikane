---
decision_id: neuro-integration-interpretation-synthesis-2026-05-06
status: accepted
date: 2026-05-06
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_interpretation_synthesis.schema
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

Add `neuro-operator-interpretation-synthesis-v1` as a digest-only receipt that
binds measurement quality gate items and cross-modal analysis results into
plain-language synthesis cards and coding-agent tasks.

# Rationale

The workbench already collects, gates, plans, and executes bounded analysis, but
the objective also requires LLM-native use by people who are not machine-learning
specialists. A separate interpretation synthesis receipt makes the operator
handoff explicit without turning bounded compatibility summaries into diagnosis,
causal inference, mind-state proof, or upload readiness.

# Implementation

The receipt emits one synthesis card per cross-modal analysis result. Each card
binds the result digest, the relevant source types, quality item digests,
plain-language summary, operator next action, coding-agent task, interpretation
confidence proxy, evidence refs, and digest. Validation checks the synthesis
digest, card digest set, result coverage, source/quality/run bindings, payload
redaction, and unchanged claim ceiling.

# Safety Boundary

Interpretation synthesis is not a medical report, causal neuroscience result,
semantic thought-content decoder, subjective-equivalence claim, or upload
readiness proof. It stores no raw source, quality, analysis, interpretation, or
agent-task payloads and keeps clinical diagnosis, consciousness reproduction,
identity replacement, and upload-readiness claims false.

# Verification

Unit and integration tests assert synthesis digest binding, public schema
validity, card count, operator and coding-agent readiness, payload redaction,
ledger category append, CLI output, tamper detection, and continued claim
ceiling enforcement.

# Revisit Triggers

- Operators need role-specific explanation packs or localization beyond the
  current plain-language card.
- Real analysis apps provide uncertainty provenance or visualization receipts.
- Upload readiness, subjective equivalence, or thought-content claims need
  separate frontier evidence and Guardian review before any design elevation.
