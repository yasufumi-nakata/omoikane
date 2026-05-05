---
decision_id: neuro-integration-cross-modal-analysis-plan-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_cross_modal_analysis_plan.schema
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

Add `neuro-cross-modal-analysis-plan-v1` as a digest-only receipt for planning
bounded analyses across every current Neuro Integration Workbench source-type
pair.

# Rationale

The workbench can already bind sources, run the survey plus EEG seed analysis,
prove application replacement lane coverage, and bind external connector refs.
The remaining gap is analysis coverage across all currently integrated
modalities: fMRI, organoid, and future source summaries should not merely sit in
the bundle; each source-type pair needs an explicit bounded recipe and connector
support before the runtime can claim cross-modal analysis readiness.

# Implementation

The cross-modal analysis plan enumerates every source-type pair, assigns a
recipe, binds source feature digests, binds connector support for measurement,
analysis, data-curation, operator-copilot, and agent-automation lanes, and
records plain-language questions plus coding-agent actions. The questionnaire
plus EEG pair reuses the seed Survey EEG Fusion analysis receipt, while fMRI and
organoid pairs remain context screens under the same claim ceiling.

# Safety Boundary

The plan is analysis routing and planning evidence only. It stores no raw
source, analysis, connector, or plan payloads. It does not claim clinical
diagnosis, causal validity, consciousness reproduction, upload readiness, or
identity replacement.

# Verification

Unit and integration tests assert cross-modal plan digest binding, pair coverage
for all current source types, public schema validity, raw payload redaction, and
continued no diagnosis / consciousness / identity replacement claims.

# Revisit Triggers

- A modality needs a validated domain-specific adequacy gate beyond generic
  pair planning.
- Live connector execution begins returning analysis run receipts.
- Cohort-scale or causal inference workflows require stronger statistical
  evidence receipts.
