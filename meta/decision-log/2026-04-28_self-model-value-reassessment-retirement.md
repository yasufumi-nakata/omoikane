---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_reassessment_receipt.schema
  - evals/identity-fidelity/self_model_value_reassessment_retirement.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel accepted value の再評価・退役を receipt 化する

## Context

`self-model-future-self-acceptance-writeback-v1` は self-authored value candidate を
後日の本人受容により active SelfModel writeback へ進める境界を固定した。
一方で、その後の生活史で本人が同じ value を再評価し、active writeback から外したい場合の
machine-readable contract は未接続だった。

## Decision

`self-model-future-self-reevaluation-retirement-v1` を追加し、accepted value の退役を
`self_model_value_reassessment_receipt` として固定する。

receipt は source value-acceptance receipt digest、source accepted value digest set、
retired value refs、continuity recheck refs、future self reevaluation ref、
Council resolution、Guardian boundary、retirement writeback ref、
post-reassessment snapshot ref、archival snapshot ref を束ねる。

retired value refs は元の accepted value set の subset に限定する。
退役は active writeback からの retirement であり、value history の削除ではない。
`historical_value_archived=true`、`active_writeback_retired=true`、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`raw_value_payload_stored=false` を public schema / runtime validation / eval で固定する。

## Consequences

- `self-model-demo --json` は `value_reassessment` branch を返す
- `mind.self_model.v0` は build / validate value reassessment operation を持つ
- IdentityGuardian は accepted value retirement の archive retention と external veto 禁止を確認できる
- identity-fidelity eval は value deletion ではなく archive-retained retirement を保護する

## Revisit triggers

- active value set の複数世代履歴を first-class timeline として公開する時
- archive retention を long-term storage proof や external trustee proof に束縛する時
