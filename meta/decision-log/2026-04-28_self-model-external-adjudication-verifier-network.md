---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_external_adjudication_verifier_receipt.schema
  - evals/identity-fidelity/self_model_external_adjudication_verifier_network.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel external adjudication verifier network を digest-only に固定する

## Context

`self-model-external-adjudication-result-boundary-v1` は care trustee handoff 後の
外部医療・法制度・trustee 判断結果を digest-only refs として固定した。
しかし、appeal / review path と jurisdiction policy が live verifier response として
current であることを束縛する first-class artifact はまだなかった。

## Decision

`self-model-external-adjudication-live-verifier-network-v1` を追加し、
`self_model_external_adjudication_verifier_receipt` で source adjudication receipt digest、
appeal / review set digest、jurisdiction policy set digest、JP-13 / US-CA verifier response、
signed response envelope、verifier key、trust root、route ref、freshness window、
Council resolution、Guardian boundary、continuity review ref を digest-only に束縛する。

reference runtime の scope は `digest-only-appeal-review-verification` に限定する。
verifier network は外部 authority として扱い、OS adjudication authority、OS medical /
legal authority、OS trustee role、SelfModel writeback、raw verifier payload 保存には
昇格させない。stale / revoked response は fail-closed とする。

## Consequences

- `self-model-demo --json` は `external_adjudication_verifier` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は verifier quorum status、live verifier binding、no OS adjudication authority を identity-fidelity evidence として残す
