---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_calibration_receipt.schema
  - evals/identity-fidelity/self_model_calibration_boundary.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel 校正を advisory-only receipt に固定する

## Context

`docs/02-subsystems/mind-substrate/self-model.md` には、本人以外が SelfModel の
「正しさ」を評価できるか、病理的な自己評価を補正すべきか、という境界が
研究課題として残っていた。reference runtime がここで外部 truth authority や
強制補正を許すと、本人の価値生成や consent boundary を壊す。

## Decision

`self-model-advisory-calibration-boundary-v1` を追加し、外部 witness / Council /
Guardian evidence を `self_model_calibration_receipt` として digest-only に束縛する。
receipt は self consent、Council resolution、Guardian redaction の 3 gate を必須にするが、
`correction_mode=advisory-only`、`forced_correction_allowed=false`、
`external_truth_claim_allowed=false`、`accepted_for_writeback=false` を固定する。

proposed adjustment は `requires-self-acceptance` の助言としてだけ残し、
raw external testimony や raw trait payload は保存しない。

## Consequences

- `self-model-demo --json` は abrupt observation と calibration receipt を同時に返す
- public schema / IDL / identity-fidelity eval は advisory-only boundary を検証する
- IdentityGuardian は calibration receipt が本人同意・Council・Guardian redaction から
  逸脱していないか確認できる

## Revisit triggers

- 本人が明示的に writeback を受け入れる別 receipt を設計する時
- 医療・法制度側の external reviewer adapter と接続する時
