---
date: 2026-05-06
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
status: decided
---

# Decision: Add NIW source onboarding catalog

## Context

NIW already binds the current questionnaire, EEG, fMRI, organoid, biosensor,
behavioral, omics, and clinical metadata source summaries. The larger design
goal needs a way to prepare arbitrary future biodata sources without pretending
that uncollected or unvalidated modalities are already measured or analyzed.

## Options considered

- Add future source types directly to the active source bundle.
- Keep future modalities only in prose documentation.
- Add a digest-only source onboarding catalog before concrete source bundles.

## Decision

Add a `neuro-source-onboarding-catalog-v1` receipt. It catalogs current and
future source types, aliases, source families, collection method IDs, analysis
recipe hints, replacement lanes, non-ML operator summaries, and coding-agent
tasks. Each source type also has a UI-facing operator status card with a safe
next action and disabled claim list so CLI JSON consumers can render review
panels without reading raw payloads. It stores no raw catalog/source/analysis
payloads and keeps diagnosis,
semantic thought content, consciousness reproduction, identity replacement, and
upload readiness claims false.

## Consequences

NIW can now route MEG, ECoG, fNIRS, diffusion MRI, neural spiking, eye tracking,
speech, gait, microbiome, metabolomics, proteomics, digital phenotyping, sleep
staging, and organoid submodalities through the same onboarding vocabulary
without adding fake measurement data. Each source still needs source-specific
research, consent, feature summaries, quality gates, and validation before it
can become a bound source bundle entry.

## Revisit triggers

- A future source type requires a different replacement lane than the current
  measurement / analysis / curation / operator / agent split.
- A source-specific validation protocol becomes mature enough to promote the
  catalog hint into a concrete source-bundle reference implementation.
- The claim ceiling or ethical boundary changes for neural tissue, invasive
  neural data, clinical data, or identity-related interpretation.
