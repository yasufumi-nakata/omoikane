---
decision_id: observation-integration-workbench-2026-05-05
status: accepted
date: 2026-05-05
area: interface/observation-integration-workbench
touchpoints:
  - src/omoikane/interface/observation_integration_workbench.py
  - src/omoikane/reference_os.py
  - src/omoikane/cli.py
  - specs/interfaces/interface.observation_integration_workbench.v0.idl
  - specs/schemas/observation_source_catalog.schema
  - specs/schemas/observation_source_bundle.schema
  - specs/schemas/observation_integration_graph.schema
  - specs/schemas/observation_analysis_plan.schema
  - specs/schemas/observation_operator_guide.schema
  - specs/catalog.yaml
  - evals/interface/observation_integration_workbench.yaml
  - docs/02-subsystems/interface/observation-integration-workbench.md
  - docs/05-research-frontiers/observation-integration.md
  - tests/unit/test_observation_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
---

# Decision

Add `interface.observation_integration_workbench.v0` as a new L6 reference
runtime surface for human-acquired observations and measurements. The workbench
binds broad source families into taxonomy, source bundle, integration graph,
analysis plan, and operator guide artifacts.

# Rationale

The request asks for analysis and integration of what humanity has acquired or
measured so far. In this repository that cannot mean bulk ingestion of raw
datasets or a claim of total knowledge. It should mean a schema-bound surface
that can accept declared observation manifests across domains, preserve
provenance and rights boundaries, and hand a safe analysis plan to Builder,
Researcher, and Guardian roles.

# Implementation

The reference runtime now emits an open-world observation taxonomy, a
multi-domain source bundle, a cross-domain integration graph, an analysis plan,
and beginner/coding-agent operator guide receipts. The demo binds EEG, fMRI
BOLD, climate record, satellite imagery, telescope image, and survey sources
across six measurement families, then records the artifacts in ContinuityLedger.

# Safety Boundary

The claim ceiling is fixed to `cross-domain-feature-integration-plan-only`.
The workbench does not store raw observation, personal, external dataset,
analysis, model, or instruction payloads. Complete human knowledge, truth
unification, consciousness reproduction, and identity replacement remain false.

# Verification

Unit tests cover taxonomy shape, source manifest validation, rights boundary
binding, and tamper rejection. Integration tests validate the demo output
against public schemas and pin the validation flags for alignment axes,
analysis lanes, operator handoff, raw payload redaction, and claim ceiling
preservation.

# Revisit Triggers

- A domain-specific registry can provide machine-checkable rights and consent
  mappings across many observation families.
- Cross-domain unit and uncertainty propagation becomes strong enough to
  support a narrower analysis adapter.
- A future decision proposes raising the claim ceiling beyond analysis planning.
