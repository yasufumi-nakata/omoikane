---
decision_id: neuro-integration-biodata-fusion-binding-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_source_bundle.schema
  - specs/schemas/neuro_integration_analysis_receipt.schema
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

Bind BioData Transmitter's `biodata-survey-eeg-window-fusion-v1` receipt into
Neuro Integration Workbench as a compact digest-only upstream binding.

# Rationale

The workbench already treated questionnaire and EEG as the seed pair, but it
recomputed the seed alignment from local feature summaries only. The broader
multi-application objective needs the application surface to consume the
BioData Transmitter receipt that binds survey score digest, EEG feature digest,
fused window digest, and non-ML operator accessibility.

# Implementation

`bind_source_bundle` now accepts upstream receipts and stores only receipt
digests, fused window digest, selected source digests, fusion confidence, and
redaction / claim-ceiling flags. `build_survey_eeg_fusion` carries this compact
binding into the analysis receipt. The demo creates and validates a BioData
Survey EEG Fusion receipt before opening the NIW workspace.

# Safety Boundary

The BioData receipt keeps its own `survey-eeg-correlation-input-only` ceiling.
NIW does not promote that receipt to diagnosis, consciousness reproduction, or
identity replacement. Raw survey answers, raw EEG samples, raw latent payloads,
and raw fusion payloads remain outside the workbench artifacts.

# Verification

Unit tests cover upstream binding in the NIW validation bundle. Integration
tests validate the upstream BioData receipt schema, NIW source bundle schema,
NIW analysis schema, and new validation flags for upstream digest binding and
payload redaction.

# Revisit Triggers

- BioData emits a newer survey+EEG fusion profile.
- NIW adds an external app connector that needs a richer receipt projection.
- A future validated multimodal model requires more than receipt digest and
  fused window digest for provenance reconciliation.
