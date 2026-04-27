---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_acceptance_receipt.schema
  - evals/identity-fidelity/self_model_value_acceptance_writeback.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel の future self acceptance writeback を receipt 化する

## Context

直前の `self-model-self-authored-value-generation-v1` は、新しい価値候補を
self-authored proposal として保持し、future self acceptance 前の writeback を拒む
境界を固定した。一方で、後日の本人受容が起きた場合にどの candidate をどの
digest / review / writeback ref へ束縛するかは first-class artifact ではなかった。

## Decision

`self-model-future-self-acceptance-writeback-v1` を追加し、
`self_model_value_acceptance_receipt` で value-generation receipt digest、
source candidate digest set、accepted value refs、continuity recheck refs、
future self acceptance ref、Council resolution、Guardian boundary、writeback ref、
post-acceptance snapshot ref を束ねる。

受容対象は元の self-authored candidate set の subset に限定し、
`acceptance_mode=future-self-accepted-bounded-writeback`、
`integration_status=accepted-for-bounded-writeback`、
`boundary_only_review=true`、`accepted_for_writeback=true` を固定する。
Council / Guardian は境界監査だけを担い、external veto、forced stability lock、
raw value / continuity payload storage は許可しない。

## Consequences

- `self-model-demo --json` は `value_acceptance` branch を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian が同じ boundary を検証する
- proposed value と accepted writeback の間に digest-bound handoff ができる

## Revisit Triggers

- accepted value の長期撤回・再評価 receipt を設計する時
- 医療・法制度側 reviewer adapter が boundary-only review へ接続される時
