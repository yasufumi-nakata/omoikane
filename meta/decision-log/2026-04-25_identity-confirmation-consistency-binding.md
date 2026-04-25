---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/identity-lifecycle.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.identity.v0.idl
  - specs/schemas/identity_confirmation_profile.schema
  - evals/identity-fidelity/identity_confirmation_profile.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: Identity confirmation は self-report と witness consistency を同一 subject に束縛する

## Context

`multidimensional-identity-confirmation-v1` は episodic recall、SelfModel alignment、
subjective self-report、third-party witness alignment の 4 dimension と
clinician + guardian witness quorum を確認していました。
一方で、自己報告が高く witness quorum も成立しているが、両者の continuity score が
大きく乖離する profile を同じ continuity subject 上で fail-closed できる
first-class receipt はありませんでした。

## Options considered

- A: 4 dimension と witness quorum のみで Active 遷移を判断し続ける
- B: raw self-report statement と raw third-party observation text を保存して照合する
- C: digest-only `identity-self-report-witness-consistency-v1` を profile に追加し、
  self-report evidence digest、accepted witness digest set、required roles、
  score delta を同一 continuity subject に束縛する

## Decision

**C** を採択。

`identity-self-report-witness-consistency-v1` は
`score-delta-and-role-bound-v1` profile として、self-report continuity score と
accepted witness mean score の差分を `max_score_delta=0.12` 以内に固定する。
receipt は self-report evidence digest、accepted witness evidence digest set、
required witness roles、continuity subject digest を保存し、raw subjective statement や
raw witness observation payload は保存しない。

## Consequences

- `identity-confirmation-demo --json` は
  `self_report_witness_consistency` と validation flag
  `self_report_witness_consistency_bound` を返す
- public schema / IDL / eval / IdentityGuardian capability は同じ policy id を共有する
- all dimension と witness quorum が pass しても score consistency が divergent なら
  `self-report-witness-consistency-not-bound` で Active 遷移を拒否する

## Revisit triggers

- witness role を jurisdiction-specific reviewer registry へ拡張する時
- score delta を本人の事前同意 profile や clinical context に応じて可変化する時
