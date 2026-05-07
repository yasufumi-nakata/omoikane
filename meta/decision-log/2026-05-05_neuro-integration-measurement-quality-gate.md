---
decision_id: neuro-integration-measurement-quality-gate-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_measurement_quality_gate.schema
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
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_measurement_quality_gate.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
---

# Decision

Add `neuro-measurement-quality-gate-v1` as a digest-only receipt binding Neuro
Integration Workbench collection run results to calibration, artifact/QC,
consent freshness, operator review, and quality authority refs.

# Rationale

Collection run receipts show bounded source collection summaries, but they do
not yet make calibration, artifact review, or consent freshness explicit. The
objective requires a multi-application biological data system that can replace
measurement and analysis apps safely for non-ML operators and coding agents, so
measurement quality needs a first-class gate before analysis planning.

# Implementation

The gate emits one quality item per source type. Each item binds a collection
result digest, source feature digest, collection window ref, measurement
connector refs, calibration ref, artifact/QC ref, consent freshness ref,
operator review ref, quality authority ref, bounded quality scores, operator
summary, coding-agent next action, and digest. Validation checks gate digest,
item digest set, source coverage, payload redaction, and unchanged claim
ceiling.

# Safety Boundary

The gate is not a live calibration procedure, artifact rejection algorithm,
clinical-grade QC result, legal/IRB approval, or session burden safety proof. It
stores no raw source, quality, calibration, artifact, consent, connector,
analysis, plan, or result payloads and does not claim clinical diagnosis,
semantic thought content, consciousness reproduction, subjective equivalence, or
identity replacement.

# Verification

Unit and integration tests assert measurement quality gate digest binding,
public schema validity, item count, payload redaction, ledger category append,
CLI output, tamper detection, and continued no diagnosis / consciousness /
identity replacement claims.

# Revisit Triggers

- Real measurement apps provide modality-specific calibration or artifact
  rejection receipts.
- Consent freshness needs jurisdictional authority, expiry windows, or
  re-consent verifier receipts.
- Clinical, cohort-scale, or regulatory quality claims require separate
  validated evidence receipts.
