---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - specs/schemas/imc_merge_thought_ethics_receipt.schema
  - evals/interface/imc_merge_thought_ethics_gate.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - imc.merge-thought.ethics-gate.digest-only-receipt
---

# Decision: IMC merge_thought に ethics gate receipt を追加する

## Context

IMC の `merge_thought` session は experimental mode として存在していたが、
identity confusion risk、collective boundary、Guardian / Federation Council gate を
reference runtime の first-class receipt として封印していなかった。
そのため、文書上は危険境界を示していても、CLI / schema / eval / tests が同じ不変条件を
検証できない状態だった。

## Decision

`federation-council-merge-thought-ethics-gate-v1` receipt を追加し、
`merge_thought` message を Council witness、Guardian liaison、Ethics Committee role、
continuity event ref、10 second 以下の bounded merge window に束縛する。

receipt は raw thought payload や raw message payload を保存せず、session digest、
message digest、risk boundary digest、collective binding digest、disclosure binding digest、
council / guardian gate digest だけを保持する。`imc-demo --json` は通常の consent /
disconnect / memory glimpse と同じ ledger に
`imc.merge_thought.ethics_gate.sealed` を追加し、public schema で検証可能な
validation flags を返す。

## Consequences

- `merge_thought` の実験的利用は digest-only ethics receipt を通らない限り
  reference demo 上で approved にならない
- public schema / IDL / eval / Integration tests は raw thought payload と raw message payload が
  保存されていないことを検証する
- IntegrityGuardian は `merge_thought_ethics_gate` capability を持ち、
  Federation Council / Guardian / Ethics Committee の 3 role gate を監査対象にする

## Revisit triggers

- `merge_thought` を multi-party live transport や distributed transport へ接続する時
- bounded merge window の上限を policy registry で可変化する時
- Council witness を外部 verifier quorum や auditable human oversight channel へ拡張する時
