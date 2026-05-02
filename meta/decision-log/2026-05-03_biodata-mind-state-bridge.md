---
decision_id: biodata-mind-state-bridge-2026-05-03
status: accepted
date: 2026-05-03
area: interface/biodata-transmitter
touchpoints:
  - src/omoikane/interface/biodata_transmitter.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_mind_state_bridge.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/interface/biodata_transmitter_roundtrip.yaml
  - evals/interface/README.md
  - docs/01-architecture/data-flow.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - tests/unit/test_biodata_transmitter.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_reference_runtime.py
---

# Decision

BioData Transmitter now has a current-stage downstream bridge:
`biodata-mind-state-bridge-v1`. It binds one body-state latent, one generated
biosignal bundle, one calibration confidence gate, and optionally the current
feature-window series profile into a digest-only handoff receipt for L2/L3
mind-state consumers.

# Rationale

The current runtime can integrate many human biosignal feature summaries into a
person-bound body-state latent and generate bounded biosignal / affect /
thought-pressure proxies. The next system goal is broader: integrate biological
signals toward a person's conscious state. The implementable bridge between
those stages is not a consciousness model; it is a strictly bounded handoff that
lets QualiaBuffer, SelfModel, perception, affect, attention, and identity
confidence components consume the BioData state under an explicit claim ceiling.

# Implementation

The bridge receipt binds:

- `body_state_latent_digest`
- `generated_bundle_digest`
- `calibration_confidence_gate_digest`
- optional `feature_window_series_profile_digest`
- Qualia surrogate axis digests
- SelfModel advisory digest
- L2/L3 handoff digest set

Its `claim_ceiling` is fixed to `body-state-surrogate-input-only`. The runtime
keeps `semantic_thought_content_generated`, `subjective_equivalence_claimed`,
`consciousness_reproduction_claimed`, and `identity_replacement_claimed` false.
It also keeps raw BioData, latent, generated, gate, qualia, and self-model
payload storage false.

# Verification

The unit tests validate bridge digest binding and tamper rejection. Integration
tests validate the demo against `biodata_mind_state_bridge.schema`, confirm the
L2/L3 handoff bindings, and assert that the no-consciousness and no-identity
claim ceiling remains active.

# Revisit Triggers

- A validated qualia representation becomes available.
- Semantic thought recovery from biosignal-only inputs becomes experimentally
  grounded.
- Identity continuity protocols can accept physiological state as more than a
  confidence input.
- Mind-upload research issues close enough evidence to raise the claim ceiling.
