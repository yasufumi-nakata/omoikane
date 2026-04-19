---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - docs/07-reference-implementation/README.md
  - evals/continuity/scheduler_root_rotation.yaml
  - specs/interfaces/kernel.scheduler.v0.idl
  - specs/schemas/governance_verifier_roster.schema
status: decided
---

# Decision: AscensionScheduler の external verifier root rotation を overlap/cutover contract に固定する

## Context

`docs/07-reference-implementation/README.md` の future work には
`AscensionScheduler artifact の root-of-trust rotation` が残っていました。
artifact bundle の freshness / revocation は既に machine-checkable でしたが、
それを検証する external verifier 側の root が切り替わるときに
protected handoff をどう止めるかが runtime に存在しませんでした。

## Options considered

- A: verifier root rotation は docs-only の注意書きに留め、runtime では扱わない
- B: `artifact_sync` に root fingerprint だけ足し、overlap / cutover state は表現しない
- C: `verifier_roster` を独立 snapshot として持ち、
  `overlap-required` / `rotated` / `revoked` を scheduler gate に入れる

## Decision

**C** を採択。

## Consequences

- `ScheduleHandle` は `verifier_roster` を保持し、
  `stable` / `overlap-required` / `rotated` / `revoked` を machine-readable にする
- `sync_governance_artifacts` は artifact freshness と同時に verifier roster も受理し、
  overlap 中は pause、cutover 後のみ accept、revoked は fail-closed にする
- `scheduler-demo` は Method A の rotation overlap / cutover recovery と
  Method C の verifier revocation fail-closed を可視化する
- `evals/continuity/scheduler_root_rotation.yaml` が
  overlap pause、dual-attested cutover、verifier revocation を継続検証する

## Revisit triggers

- external verifier を単一 roster ではなく distributed trust quorum へ拡張したい時
- root fingerprint だけでなく hardware-backed transparency log inclusion まで必須化したい時
- 実在 remote verifier との live transport / authenticity 連携を repo 内で扱う時
