---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - agents/researchers/consciousness-theorist.policy.md
  - docs/04-ai-governance/subagent-roster.md
  - specs/schemas/agent_source_definition.schema
status: decided
---

# Decision: Researcher evidence lives under agents

## Context

The top-level `research/` tree was described as a human free-form notebook area.
This conflicted with the project structure: unresolved human-facing research
questions already have canonical homes under `docs/05-research-frontiers/`, while
agent-authored literature seeds and evidence notes belong to the Researcher role.

## Options considered

- A: Keep `research/` as a human notebook surface.
- B: Remove `research/` and place Researcher evidence seeds under `agents/researchers/`.
- C: Move every research-adjacent artifact into `docs/05-research-frontiers/`.

## Decision

Adopt B. Human free-form research notes are not a repository surface. Canonical
open questions remain in `docs/05-research-frontiers/`; Researcher evidence
seeds and auxiliary investigation notes live under `agents/researchers/evidence/`.
Schemas and runtime validation no longer accept `research/` as a first-class
agent source, build surface, or evidence policy location.

## Consequences

Researcher outputs stay advisory-only and role-scoped. Existing useful seed
material is preserved under `agents/researchers/evidence/`, but human-oriented
notebook README files are removed. Historical decision logs may still mention
`research/` as past context, but new agent definitions must use `docs/` or
`agents/researchers/`.

## Revisit triggers

- Researcher evidence grows large enough to require role-specific subfolders.
- `docs/05-research-frontiers/` starts mixing unresolved questions with raw
  evidence seeds.
- A non-agent, non-doc archival requirement appears and needs a separate schema.
