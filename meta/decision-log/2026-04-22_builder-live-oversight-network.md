---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.enactment.v0.idl
  - specs/schemas/builder_live_enactment_session.schema
  - evals/continuity/builder_live_oversight_network.yaml
status: decided
---

# Decision: live enactment の actual command execution を reviewer verifier-network attestation で gate する

## Context

2026-04-22 時点で `LiveEnactmentService` は
temp workspace materialization、actual eval command execution、cleanup までは
machine-checkable でした。

一方で 2026-04-20 の decision では
`external verifier network 連携` が future work として残っており、
actual command execution 自体が
「どの human reviewer が live verifier network で確認した artifact を実行したか」
を current runtime contract に持っていませんでした。

この状態では `builder-demo` / `builder-live-demo` / `rollback-demo` が
actual command receipt を返しても、
execution 前の human approval が rollback 側ほど machine-checkable ではありませんでした。

## Options considered

- A: live enactment は temp workspace command receipt のみ維持し、reviewer verifier-network attestation は future work に残す
- B: live enactment session に artifact-bound Guardian oversight event と oversight gate を追加し、network-backed reviewer quorum を execution 前提へ昇格する
- C: raw verifier transcript や payload body を repo へ保存して execution transcript まで一体化する

## Decision

Option B を採択します。

- `LiveEnactmentService` は
  `artifact://...` payload に束縛された `guardian_oversight_event` を必須化し、
  integrity Guardian / `attest` / reviewer quorum `2/2` /
  verifier-network receipt binding を fail-closed で確認します
- `builder_live_enactment_session` は
  `guardian_oversight_event` と `oversight_gate` を first-class field として保持し、
  `enactment-approved` は
  network-attested reviewer quorum、actual command receipt、cleanup 完了の全てを満たした時だけ返します
- `builder-demo`、`builder-live-demo`、`rollback-demo` の live enactment path は
  同じ oversight contract を通して actual command execution を行います

## Consequences

- `builder-live-demo` は
  `artifact-bound reviewer network attest -> temp workspace materialization -> actual command execution -> cleanup`
  を 1 つの reference artifact として返せます
- `builder-demo` の `diff_eval_execution_receipt` も
  reviewer-network attested live enactment session を起点にした execution evidence になります
- residual future work は generic な external verifier network 不在ではなく、
  reviewer scope の多段化や raw transcript retention のような
  より外部依存の強い領域へ縮小されます

## Revisit triggers

- live enactment reviewer quorum を 2 名より大きい policy へ広げたくなった時
- verifier network を distributed authority plane や root rotation と統合したくなった時
- raw verifier payload / transcript retention を repo 外 sealed store と連携したくなった時
