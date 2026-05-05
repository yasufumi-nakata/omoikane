---
decision_id: neuro-integration-application-connector-bundle-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_application_connector_bundle.schema
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

Add `neuro-application-connector-bundle-v1` as a digest-only receipt binding
external application connector refs to a Neuro Integration Workbench replacement
plan.

# Rationale

The replacement plan proves each source type is covered by measurement,
analysis, data-curation, operator-copilot, and agent-automation application
digests. It does not yet prove how those replacement apps would be reached by a
non-ML operator or an LLM-native coding agent. The objective requires replacing
many measurement and analysis tools, so connector refs, credential refs, data
contracts, and LLM tool refs need a first-class receipt before live connectors
are introduced.

# Implementation

The connector bundle stores connector refs, endpoint refs, credential refs,
permission refs, data contract refs, LLM tool refs, source-type coverage, and
lane coverage. The reference demo binds five connectors: measurement ingest,
analysis runner, curation ledger, operator console, and agent runner. Validation
now checks connector bundle digest binding, source-type connector coverage,
connector raw-payload redaction, and operator-safe LLM tooling.

# Safety Boundary

The bundle is not live credential handling and does not store raw connector,
credential, endpoint, source, or analysis payloads. It does not validate the
scientific adequacy of a modality or raise the
`feature-alignment-and-analysis-plan-only` claim ceiling.

# Verification

Unit and integration tests assert connector bundle binding, schema validity,
connector count, redaction flags, and continued no diagnosis / consciousness /
identity replacement claims.

# Revisit Triggers

- A live connector needs credential rotation, billing, network, or latency
  evidence.
- External apps expose modality-specific validation reports beyond generic data
  contracts.
- The workbench adds a UI workflow for selecting, revoking, or replacing
  connector manifests.
