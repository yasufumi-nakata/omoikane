---
decision_id: neuro-integration-open-biodata-recipes-2026-05-06
status: accepted
date: 2026-05-06
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - specs/schemas/neuro_integration_collection_run.schema
  - specs/schemas/neuro_integration_measurement_quality_gate.schema
  - specs/schemas/neuro_integration_cross_modal_analysis_plan.schema
  - specs/schemas/neuro_integration_cross_modal_analysis_run.schema
  - specs/schemas/neuro_integration_interpretation_synthesis.schema
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/02-subsystems/interface/README.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - tests/unit/test_neuro_integration_workbench.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/neuro_integration_workbench.py
  - specs/schemas/neuro_integration_collection_run.schema
  - specs/schemas/neuro_integration_measurement_quality_gate.schema
  - specs/schemas/neuro_integration_cross_modal_analysis_plan.schema
  - specs/schemas/neuro_integration_cross_modal_analysis_run.schema
  - specs/schemas/neuro_integration_interpretation_synthesis.schema
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/catalog.yaml
---

# Decision

Promote the open biodata lane from generic source-type coverage to bounded
modality-specific context recipes for biosensor, behavioral task, omics, and
clinical metadata summaries.

# Rationale

The prior open biodata lane proved that the new source types flow through app
replacement, connector, collection, quality, analysis, and interpretation
receipts. It still let several of those sources use the generic feature-summary
fallback in analysis. The objective asks for a multi-application system that can
replace biological measurement and analysis apps, so the reference runtime needs
named analysis semantics for those common biodata classes before falling back to
generic handling.

# Implementation

The workbench now derives modality-specific analysis axes for biosensor,
behavioral task, omics, and clinical metadata feature summaries. Cross-modal
pair planning adds bounded recipes for biosignal autonomic context, behavioral
performance context, omics physiology context, omics plus clinical context, and
clinical metadata modulation. Collection, quality, result, and interpretation
statuses now expose these open biodata contexts in plain-language operator and
coding-agent handoffs.

# Safety Boundary

The new recipes are context screens only. They do not make clinical diagnoses,
causal claims, semantic thought-content claims, consciousness reproduction
claims, identity replacement claims, treatment recommendations, or upload
readiness claims. Raw source, collection, quality, analysis, interpretation, and
agent-task payloads remain outside the reference runtime.

# Verification

Unit and integration tests assert the new open biodata axes, recipe ids, result
statuses, and interpretation statuses while preserving eight-source coverage,
twenty-eight pair coverage, digest binding, raw payload redaction, and the
`feature-alignment-and-analysis-plan-only` claim ceiling.

# Revisit Triggers

- A source-specific scientific validity study replaces the current bounded proxy
  axes.
- A future source type needs a consent, sampling, or quality boundary that cannot
  share the open biodata context recipe pattern.
- Clinical utility, cohort validity, or regulatory readiness evidence becomes
  strong enough to move from research frontier to a stricter runtime contract.
