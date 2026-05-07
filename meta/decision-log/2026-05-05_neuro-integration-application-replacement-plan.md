---
decision_id: neuro-integration-application-replacement-plan-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_application_replacement_plan.schema
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
  - specs/schemas/neuro_integration_application_replacement_plan.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
---

# Decision

Add `neuro-application-replacement-plan-v1` as a digest-only receipt for
checking whether the current Neuro Integration Workbench source bundle is
covered by all required application replacement lanes.

# Rationale

The workbench already registered measurement, analysis, data-curation,
operator-copilot, and agent-automation applications. It did not yet prove that
every source type in the current bundle could flow through every lane. The
objective requires replacing many measurement and analysis applications, so
lane presence alone is not enough.

# Implementation

The replacement plan binds app digests, source bundle digest, workspace digest,
operator guide digest, lane coverage, source-type coverage, and non-ML /
coding-agent handoffs. The reference demo now requires questionnaire, EEG,
fMRI BOLD, and brain organoid sources to be covered by all five lanes before
`application_replacement_plan_bound` can pass.

# Safety Boundary

The plan is a routing and provenance artifact. It does not validate the
scientific adequacy of each modality, does not store raw app or source payloads,
and does not raise the `feature-alignment-and-analysis-plan-only` claim ceiling.

# Verification

Unit and integration tests assert replacement plan digest binding, source-type
lane coverage, schema validity, raw payload redaction, and no diagnosis /
consciousness / identity replacement claims.

# Revisit Triggers

- A new source family requires a modality-specific analysis adequacy gate.
- External app connectors introduce credential, billing, or live-data routing
  artifacts that need separate receipts.
- The project adds a UI workflow for selecting or replacing applications.
