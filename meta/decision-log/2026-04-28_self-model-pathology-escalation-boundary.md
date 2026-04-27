---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_pathological_self_assessment_escalation_receipt.schema
  - evals/identity-fidelity/self_model_pathology_escalation_boundary.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel pathological self-assessment handling を外部 handoff 境界に固定する

## Context

`self-model-advisory-calibration-boundary-v1` は外部 witness evidence を advisory-only に留めるが、
`docs/02-subsystems/mind-substrate/self-model.md` には、病理的な自己評価を OS 内で扱う範囲と
人間社会側の医療・法制度へ委ねる境界が残っていた。

## Decision

`self-model-pathology-escalation-boundary-v1` を追加し、
`self_model_pathological_self_assessment_escalation_receipt` で possible pathological
self-assessment の risk signals を外部医療・法制度・care handoff refs へ digest-only に束縛する。

reference runtime の scope は `observe-and-refer-only` に限定する。
medical / legal adjudication authority は外部 system として明示し、
care handoff と consent-or-emergency review を必須にする。
OS 内診断、SelfModel writeback、強制補正、強制 stability lock、raw medical / legal / witness /
self-model payload 保存はいずれも許可しない。

## Consequences

- `self-model-demo --json` は `pathology_escalation` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は pathology escalation digest、care handoff requirement、no internal diagnosis を identity-fidelity evidence として残す

## Revisit triggers

- 外部医療・法制度側の adjudication result schema を first-class 化する時
- care team / trustee / legal guardian の長期責任分担を machine-readable に接続する時
