---
decision_id: observation-measurement-analysis-catalog-2026-05-05
status: accepted
date: 2026-05-05
area: interface/observation-integration-workbench
touchpoints:
  - src/omoikane/interface/observation_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.observation_integration_workbench.v0.idl
  - specs/schemas/observation_measurement_analysis_catalog.schema
  - specs/schemas/observation_analysis_plan.schema
  - specs/catalog.yaml
  - evals/interface/observation_integration_workbench.yaml
  - docs/02-subsystems/interface/observation-integration-workbench.md
  - docs/05-research-frontiers/observation-integration.md
  - tests/unit/test_observation_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/observation_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.observation_integration_workbench.v0.idl
  - specs/schemas/observation_measurement_analysis_catalog.schema
  - specs/schemas/observation_analysis_plan.schema
  - specs/catalog.yaml
  - evals/interface/observation_integration_workbench.yaml
  - docs/02-subsystems/interface/observation-integration-workbench.md
---

# Decision

Extend Observation Integration Workbench with an open-world measurement and
analysis method catalog. The catalog records method families and method ids for
historical and declared measurement practices plus analysis practices, then
binds the catalog digest into the observation analysis plan.

# Rationale

The request is broader than source family routing. To support prior
measurements and their analysis methods, OIW needs a method vocabulary that is
separate from raw datasets and separate from Neuro Integration replacement
lanes. A dedicated method catalog lets Builder and Researcher agents plan with
method refs while Guardian can still enforce rights, uncertainty, and claim
ceilings.

# Implementation

The runtime now emits `universal-observation-method-catalog-v1` with
measurement families such as self-report, biosignal recording, imaging,
sequencing, sensors, registries, experiments, and simulations. It also emits
analysis families such as descriptive statistics, signal processing,
spatiotemporal analysis, statistical inference, machine learning, graph
analysis, omics, image analysis, simulation checks, qualitative analysis, and
privacy / rights audit. Each planned analysis lane carries measurement-method
and analysis-method refs, and ContinuityLedger records the catalog digest.

# Safety Boundary

The catalog is open-world and does not claim complete method coverage. It does
not store raw methods, raw algorithms, raw code, raw source records, or raw
analysis payloads. The claim ceiling remains
`cross-domain-feature-integration-plan-only`; truth unification, causal truth,
clinical diagnosis, consciousness reproduction, and identity replacement remain
false.

# Verification

Unit tests cover method catalog shape, digest binding, and tamper rejection.
Integration tests validate the new public schema, CLI output, reference runtime
validation flags, and ledger category count for the method catalog.

# Revisit Triggers

- A domain registry can provide machine-checkable method provenance and
  uncertainty profiles.
- Observation method aliases need to be reconciled with a domain-specific
  ontology.
- A later decision proposes a narrower method adapter while retaining the same
  claim ceiling.
