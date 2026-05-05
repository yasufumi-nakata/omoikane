---
decision_id: neuro-integration-semantic-thought-ceiling-2026-05-06
status: accepted
date: 2026-05-06
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_collection_protocol.schema
  - specs/schemas/neuro_integration_collection_run.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/07-reference-implementation/README.md
  - agents/guardians/integrity-guardian.yaml
  - agents/guardians/integrity-guardian.policy.md
  - tests/unit/test_neuro_integration_workbench.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
---

# Decision

Bind `semantic_thought_content_generated=false` directly into Neuro
Integration Workbench collection protocol and collection run receipts.

# Rationale

The upstream BioData Survey EEG Fusion receipt already rejects semantic thought
content generation, but the Neuro collection receipts only machine-checked raw
payload redaction, diagnosis, consciousness reproduction, and identity
replacement. Collection evidence should carry the same claim ceiling at the
protocol, step, run, and result levels.

# Implementation

The reference runtime now emits the semantic thought content flag on collection
protocols, steps, runs, and results. Validation checks it in the core bundle,
collection protocol, collection run, schemas, eval expectations, Guardian
policy, ReferenceOS ledger payloads, and public tests.

# Safety Boundary

The collection receipts remain bounded feature-alignment artifacts. They do
not reconstruct thought content, diagnose a body or mind, reproduce
consciousness, or replace identity.

# Verification

Unit and integration coverage asserts the new false flags, public schema
validity, validation keys, ledger propagation, CLI output, and tamper failure
for run-level and result-level semantic thought content claims.
