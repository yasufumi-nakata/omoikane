---
decision_id: neuro-integration-collection-run-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_collection_run.schema
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
  - specs/schemas/neuro_integration_collection_run.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
---

# Decision

Add `neuro-collection-run-v1` as a digest-only receipt for bounded per-source
collection result summaries produced from a Neuro Integration Workbench
collection protocol.

# Rationale

The collection protocol fixes the acquisition boundary, but it does not show
that each source can produce a reviewable collection summary before analysis.
The objective requires collection, analysis, and broader biological data
integration, so collection execution needs its own safe receipt between
connector binding and cross-modal analysis planning.

# Implementation

The collection run binds the source bundle, connector bundle, collection
protocol digest, every collection step digest, bounded quality/risk summaries,
operator summaries, coding-agent next actions, result digest set, and review
readiness. The summary is derived only from digest-bound feature counts,
construct coverage, consent binding, and measurement connector binding.

# Safety Boundary

The run is not live device acquisition, calibration, artifact rejection,
clinical-grade QC, IRB/legal approval, or session burden safety evidence. It
stores no raw source, collection, connector, result, analysis, plan, or
credential payloads and does not claim clinical diagnosis, semantic thought
content, consciousness reproduction, subjective equivalence, or identity
replacement.

# Verification

Unit and integration tests assert collection run digest binding, public schema
validity, result count, payload redaction, ledger category append, CLI output,
tamper detection, and continued no diagnosis / consciousness / identity
replacement claims.

# Revisit Triggers

- Live acquisition sessions need modality-specific calibration and artifact
  receipts.
- A real measurement app returns structured QC evidence beyond bounded summary
  proxies.
- Human-subject burden, consent expiry, or jurisdictional review needs a
  stronger collection authority receipt.
