---
decision_id: neuro-integration-longitudinal-timeline-2026-05-06
status: accepted
date: 2026-05-06
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/interface/neuro_integration_workbench.py
  - src/omoikane/reference_os.py
  - specs/schemas/neuro_integration_longitudinal_timeline.schema
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
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

Add a Neuro Integration Workbench longitudinal timeline receipt that binds
multiple source-bundle windows into per-source axis drift and stability proxy
summaries.

# Rationale

The workbench can now collect, quality-gate, analyze, and interpret an
eight-source biodata window. The broader objective needs repeated biological
data collection and analysis over time, because single-window integration cannot
support longitudinal review. The timeline receipt makes repeated-window binding
explicit while keeping the claim ceiling below diagnosis, semantic thought
content, identity replacement, and upload readiness.

# Implementation

The reference runtime now builds a second digest-only source-bundle window for
the same eight source types and binds both windows into
`neuro-longitudinal-integration-timeline-v1`. The receipt records source bundle
digests, stable source-type coverage, per-source common analysis axes, bounded
axis drift summaries, operator summaries, coding-agent next actions, and
redaction flags.

# Safety Boundary

Timeline stability is review context only. It does not prove personhood,
subjective continuity, clinical longitudinal validity, treatment readiness,
identity replacement, or mind-upload readiness. Raw source, timeline, axis, and
operator payloads are not stored.

# Verification

Unit, runtime, CLI, and public schema tests assert two-window binding, eight
stable source types, eight axis drift items, digest verification, raw payload
redaction, and unchanged claim ceilings.

# Revisit Triggers

- More than two windows need cadence, missing-window, or retention policy
  semantics.
- Modality-specific longitudinal validity evidence replaces the current bounded
  axis drift proxy.
- Clinical or regulatory requirements demand a separate longitudinal quality
  authority boundary.
