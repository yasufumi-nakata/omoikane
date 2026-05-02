---
date: 2026-05-03
deciders: [yasufumi, codex-builder]
related_docs:
  - references/daily-automation-direction.md
  - references/operating-playbook.md
  - src/omoikane/self_construction/gaps.py
  - evals/continuity/gap_scanner_required_reference_files.yaml
status: decided
---

# Decision: Daily automation direction

## Context

Omoikane automation will keep running on a daily or more frequent cadence.
The project needs a stable direction that advances repo-local contracts when possible while allowing no update on days when research, experiments, institutions, or human decisions have not moved.
The same policy must keep the BioData Transmitter claim at a body-state surrogate boundary rather than implying consciousness reproduction.

## Options considered

- A: Force each run to create a new implementation or document diff.
- B: Stop automation when `gap-report` is all-zero.
- C: Keep automation active, but classify runs as runtime-gap, research-frontier-sync, automation-hygiene, no-op-watch, or blocked-preflight.

## Decision

Adopt option C.
`references/daily-automation-direction.md` becomes the repo-local direction file for recurring automation.
It requires pull-first preflight, truth-source triage, evidence-bounded research updates, and an explicit no-op-watch class for days with no meaningful progress.
`gap-report` now treats this reference file and its core sections as required automation policy.

## Consequences

Automation can safely do nothing when there is no new repo-local gap or external evidence.
Meaningful changes still prefer runtime, schema, eval, CLI, tests, docs, and decision-log alignment.
Research frontier updates require traceable evidence or yasufumi's explicit decision, and claim ceiling changes cannot be made by prose alone.

## Revisit triggers

- daily automation moves from paused/manual operation to a production schedule
- a research frontier reaches accepted evidence strong enough to raise the BioData Transmitter or BDB claim ceiling
- `gap-report` gains a more specific recurring-run audit surface
