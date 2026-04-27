---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_external_adjudication_result_receipt.schema
  - evals/identity-fidelity/self_model_external_adjudication_boundary.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel external adjudication result を digest-only 境界に固定する

## Context

`self-model-care-trustee-responsibility-handoff-v1` は pathology escalation 後の
長期 trustee、care team、legal guardian の責任分担を外部制度 refs へ束縛した。
しかし、外部医療・法制度・trustee 側が返す判断結果の **repo-local な受け皿** は
まだ first-class artifact になっていなかった。

## Decision

`self-model-external-adjudication-result-boundary-v1` を追加し、
`self_model_external_adjudication_result_receipt` で source care trustee handoff receipt、
medical / legal / trustee adjudication result refs、jurisdiction policy refs、
appeal / review refs、continuity review ref を digest-only に束縛する。

reference runtime の scope は `digest-only-result-routing` に限定する。
medical result authority、legal result authority、trustee result authority は外部人間社会側の
制度に置き、OS adjudication authority、OS medical authority、OS legal authority、
OS trustee role、SelfModel writeback、forced correction、raw result / policy / SelfModel
payload 保存はいずれも許可しない。

## Consequences

- `self-model-demo --json` は `external_adjudication` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は external adjudication digest、jurisdiction policy binding、no OS adjudication authority を identity-fidelity evidence として残す

## Revisit triggers

- 実世界の医療・法制度・trustee registry を first-class external connector へ接続する時
- appeal / review result の live verifier network を外部 authority として取り込む時
