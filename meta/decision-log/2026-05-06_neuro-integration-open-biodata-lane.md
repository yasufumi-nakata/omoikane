---
decision_id: neuro-integration-open-biodata-lane-2026-05-06
status: accepted
date: 2026-05-06
area: interface/neuro-integration-workbench
touchpoints:
  - src/omoikane/reference_os.py
  - specs/schemas/neuro_integration_source_bundle.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/02-subsystems/interface/README.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - meta/glossary.md
  - tests/unit/test_neuro_integration_workbench.py
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/reference_os.py
  - specs/schemas/neuro_integration_source_bundle.schema
  - specs/catalog.yaml
  - specs/schemas/README.md
  - evals/interface/neuro_integration_workbench.yaml
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/02-subsystems/interface/README.md
  - docs/05-research-frontiers/biosignal-transmitter.md
---

# Decision

Expand the Neuro Integration Workbench reference demo from four source types to
eight source types by adding biosensor, behavioral task, omics, and clinical
metadata summaries to the same digest-only pipeline as questionnaire, EEG, fMRI
BOLD, and brain organoid summaries.

# Rationale

The objective asks for a multi-application system that can replace biological
measurement and analysis apps beyond the initial questionnaire-plus-EEG seed.
The runtime already had open source-type mechanics, but the demo and eval still
proved only the seed plus two expansion modalities. The open biodata lane makes
the broader path concrete: each added source must pass app replacement coverage,
connector coverage, collection protocol/run, measurement quality gate,
cross-modal pair analysis, and interpretation synthesis.

# Implementation

All five replacement lanes now advertise support for eight current NIW source
types in the reference demo. The source bundle includes bounded feature-summary
manifests for biosensor, behavioral task, omics, and clinical metadata. The
expected downstream counts move from four collection/quality items and six
analysis pairs to eight collection/quality items and twenty-eight source pairs.

# Safety Boundary

Open biodata coverage is source-type coverage, not modality-specific scientific
validity. The added sources remain feature-summary digests only; raw biosensor,
behavioral, omics, clinical, analysis, quality, interpretation, and agent-task
payloads are not stored. Clinical diagnosis, semantic thought content,
consciousness reproduction, identity replacement, and upload readiness remain
false.

# Verification

Unit, runtime, CLI, eval, and public schema tests assert eight-source coverage,
twenty-eight pair coverage, digest binding, raw payload redaction, no semantic
thought content generation, and unchanged claim ceilings.

# Revisit Triggers

- A modality needs a specialized axis derivation instead of the generic feature
  summary proxy.
- Longitudinal, cohort, or regulatory evidence is introduced for source-specific
  validity.
- A future source type requires a distinct consent, quality, or collection
  authority boundary.
