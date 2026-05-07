---
decision_id: neuro-integration-workbench-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - src/omoikane/cli.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_app_registry_receipt.schema
  - specs/schemas/neuro_integration_source_bundle.schema
  - specs/schemas/neuro_integration_workspace.schema
  - specs/schemas/neuro_integration_analysis_receipt.schema
  - specs/schemas/neuro_integration_operator_guide.schema
  - specs/catalog.yaml
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/02-subsystems/interface/README.md
  - docs/07-reference-implementation/README.md
  - tests/unit/test_neuro_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - src/omoikane/cli.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_app_registry_receipt.schema
  - specs/schemas/neuro_integration_source_bundle.schema
  - specs/schemas/neuro_integration_workspace.schema
  - specs/schemas/neuro_integration_analysis_receipt.schema
---

# Decision

Add `interface.neuro_integration_workbench.v0` as a new L6 reference runtime
surface above BioData Transmitter. The workbench starts from questionnaire plus
EEG feature summaries, then attaches fMRI BOLD and brain organoid feature
summaries as expansion lanes inside a single LLM-native workspace.

# Rationale

The requested system is broader than a signal transmitter. It needs to replace
measurement applications, analysis applications, data curation tools, operator
copilots, and coding-agent automation with one multi-application workflow that
non-ML operators can still use. BioData Transmitter remains the body-state
latent bridge; the Workbench is the application-level orchestration surface
that binds source provenance, app lane coverage, and safe analysis receipts.

# Implementation

The reference runtime now emits app registry receipts, source bundles,
workspaces, survey+EEG fusion analysis receipts, and operator guide receipts.
The demo binds five replacement lanes: measurement, analysis, data-curation,
operator-copilot, and agent-automation. It also binds questionnaire and EEG as
the seed pair, fMRI BOLD and brain organoid as expansion context, and plain
language cards plus coding-agent task templates for LLM-native operation.

# Safety Boundary

The claim ceiling is fixed to `feature-alignment-and-analysis-plan-only`.
Questionnaire, EEG, fMRI, and organoid integration does not establish clinical
diagnosis, consciousness reproduction, or identity replacement. Raw
questionnaire, EEG, neuroimaging, organoid, app, instruction, and analysis
payloads remain outside the runtime artifact.

# Verification

Unit tests cover source binding, tamper rejection, and seed source enforcement.
Integration tests validate the demo output against all new public schemas and
pin the validation flags for LLM-native workflow, beginner support, replacement
lane coverage, raw payload redaction, and claim ceiling preservation.

# Revisit Triggers

- A validated modality-specific fMRI or organoid analysis adapter is added.
- The workbench grows an actual UI or external app connector layer.
- Mind-upload research evidence justifies raising the claim ceiling beyond
  feature alignment and analysis planning.
