---
decision_id: neuro-integration-collection-protocol-2026-05-05
status: accepted
date: 2026-05-05
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
  - specs/schemas/neuro_integration_collection_protocol.schema
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

Add `neuro-collection-protocol-v1` as a digest-only receipt binding each Neuro
Integration Workbench source summary to consent refs, measurement connector
refs, and collection window refs before cross-modal analysis planning.

# Rationale

The workbench already binds source summaries and application connectors, but
collection/acquisition was only implicit. The objective requires collecting,
analyzing, and integrating biological data across questionnaire, EEG, fMRI,
brain organoids, and later modalities. A first-class collection protocol makes
the acquisition boundary machine-checkable while keeping the reference runtime
minimal and safe.

# Implementation

The collection protocol stores one collection step per source. Each step binds
source refs, participant/consent/license refs, feature digest, collection window
ref, measurement connector refs/digests, plain operator summary, coding-agent
next action, and digest. The demo validates protocol digest binding, all-source
coverage, survey+EEG seed collection coverage, measurement connector coverage,
payload redaction, and the unchanged claim ceiling.

# Safety Boundary

The protocol is not live device acquisition, device calibration, IRB/legal
approval, signal-quality certification, or clinical evidence. It stores no raw
source, collection, connector, credential, analysis, plan, or result payloads
and does not claim diagnosis, semantic thought content, consciousness
reproduction, subjective equivalence, or identity replacement.

# Verification

Unit and integration tests assert collection step count, collection protocol
digest binding, schema validity, redaction flags, ledger category append, CLI
output, and continued no diagnosis / consciousness / identity replacement
claims.

# Revisit Triggers

- Live measurement devices need calibration, artifact, sampling burden, or
  acquisition-session receipts.
- Human-subject consent, IRB, jurisdiction, or provenance review needs a
  stronger collection authority schema.
- Future source types require modality-specific collection-window contracts
  beyond generic feature summaries.
