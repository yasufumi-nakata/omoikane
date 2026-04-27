---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_timeline_receipt.schema
  - evals/identity-fidelity/self_model_value_timeline_lineage.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel value lineage timeline を append-only receipt に束縛する

## Context

`self-model-self-authored-value-generation-v1`、`self-model-future-self-acceptance-writeback-v1`、
`self-model-future-self-reevaluation-retirement-v1` は個別 receipt として固定済みだった。
ただし、生成、本人受容、後日の退役を 1 つの lifecycle として監査し、最終的な
active / retired set と archive retention を同じ digest に束縛する surface はまだ無かった。

## Decision

`self-model-value-lineage-timeline-v1` を追加し、
`self_model_value_timeline_receipt` で generation / acceptance / reassessment の receipt
digest を chronological event chain に束ねる。

timeline receipt は `generated -> accepted -> retired` の順序、event digest set、
final active value refs、final retired value refs、archive snapshot refs、
continuity audit ref、Council resolution、Guardian archive ref を
`timeline_commit_digest` に束縛する。

active set と retired set は disjoint でなければならず、retired value は archive snapshot
ref を持つ。Council / Guardian は boundary-only review に留まり、external veto、
forced stability lock、raw value payload、raw continuity payload は保存しない。

## Consequences

- `self-model-demo --json` は `value_timeline` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は timeline digest と active-retired disjoint validation を identity-fidelity evidence として残す

## Revisit triggers

- 複数 accepted value generation を長期 timeline へ束ねる時
- archive retention を repo 外 trustee proof や long-term storage proof に接続する時
