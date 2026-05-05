---
date: 2026-05-06
deciders: [yasufumi, codex-builder, packaging-worker]
related_docs:
  - docs/02-subsystems/interface/neuro-integration-workbench.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - specs/interfaces/interface.neuro_integration_workbench.v0.idl
status: decided
---

# Decision: Add NIW human body analysis package

## Context

The workbench already catalogs current and future biodata source types, but the
larger user request needs a single package surface that can account for the full
BioData human biosignal catalog, show an operator-friendly UI artifact, and
publish the reference runtime across common environments. The repository rules
require this to stay a safe reference implementation rather than a production
medical, mind-upload, or identity system.

## Decision

Add `human-body-data-analysis-package-v1` inside Neuro Integration Workbench.
It binds the BioData human biosignal catalog digest, all family-level modality
groups, family analysis capability cards, operator UI tabs/cards/workflow steps,
and release package metadata for wheel, sdist, CLI JSON, schema bundle, OCI
container, Linux, macOS, Windows, Python 3.10/3.11/3.12, and linux/amd64 plus
linux/arm64 containers.

Packaging changes were delegated to a worker subagent under the Codex Builder
role. The worker updated GitHub package/release workflows and package metadata;
the main builder integrated the runtime/spec/schema/docs/test surface.

## Consequences

The runtime can now emit `human-body-analysis-demo --json` as the same bounded
NIW scenario with a dedicated human-body package artifact. This is an analysis
capability and packaging contract only: raw biosignal, analysis, UI, and release
payloads are not stored, and diagnosis, semantic thought content, consciousness
reproduction, identity replacement, and upload-readiness claims remain false.

## Revisit Triggers

- BioData adds or renames a human biosignal family or modality.
- The supported Python version floor or release platform matrix changes.
- A source family matures enough to need a dedicated source-specific schema,
  calibration protocol, or clinical/regulatory research frontier.
