---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_generation_receipt.schema
  - evals/identity-fidelity/self_model_value_generation_freedom.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel の新規価値生成を self-authored proposal として固定する

## Context

SelfModel docs には、アップロード後の新しい価値観生成の自由度が残っていた。
直前の advisory calibration contract は外部 witness が SelfModel を強制補正しない
境界を固定したが、新規価値候補をどのように audit しつつ本人の自由な生成を
妨げないかは machine-checkable な contract になっていなかった。

## Decision

`self-model-self-authored-value-generation-v1` を追加し、stable drift から生じる
新規価値候補を `self_model_value_generation_receipt` として digest-only に束縛する。
receipt は self-authorship、self consent、Council review、Guardian boundary を要求するが、
`generation_mode=self-authored-bounded-experiment`、
`integration_status=proposed-not-written-back`、
`requires_future_self_acceptance=true`、
`external_veto_allowed=false`、
`forced_stability_lock_allowed=false`、
`accepted_for_writeback=false` を固定する。

raw value payload と raw continuity payload は保存しない。

## Consequences

- `self-model-demo --json` は calibration branch に加えて value-generation branch を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian policy が同じ境界を検証する
- reference runtime は新規価値生成を外部 truth authority でも即時 writeback でもなく、
  将来の本人受容を待つ self-authored proposal として扱う

## Revisit Triggers

- 将来の本人受容を受けて writeback receipt を設計する時
- 医療・法制度側 reviewer adapter が value-generation proposal に接続される時
