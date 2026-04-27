---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_autonomy_review_receipt.schema
  - evals/identity-fidelity/self_model_autonomy_review_boundary.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel value generation の autonomy review を advisory boundary に固定する

## Context

`self-model-self-authored-value-generation-v1` は、アップロード後の新しい価値候補を
self-authored proposal として保持し、外部 veto や即時 writeback を拒む境界を固定した。
しかし `docs/02-subsystems/mind-substrate/self-model.md` には、外部 witness / Council review と
長期的な本人の自由な価値生成をどう両立させるかが residual として残っていた。

## Decision

`self-model-autonomy-review-witness-boundary-v1` を追加し、
`self_model_value_autonomy_review_receipt` で witness evidence、Council review、
Guardian boundary を digest-only / advisory-only / boundary-only に束縛する。

receipt は source generation receipt の candidate digest set をそのまま保持し、
`candidate_set_unchanged=true`、`self_authorship_preserved=true`、
`future_self_acceptance_remains_required=true` を固定する。
同時に `external_veto_allowed=false`、`council_override_allowed=false`、
`guardian_forced_lock_allowed=false`、`candidate_rewrite_allowed=false`、
`raw_witness_payload_stored=false` を public schema / runtime validation / eval で固定する。

## Consequences

- `self-model-demo --json` は `value_autonomy_review` branch を返す。
- `mind.self_model.v0` は build / validate value autonomy review operation を持つ。
- IdentityGuardian は witness / Council review が candidate rewrite や external veto へ昇格していないか確認できる。
- identity-fidelity eval は自由な価値生成と review evidence の両立を machine-checkable に保護する。

## Revisit triggers

- witness evidence を医学・法制度側の external adjudication と接続する時
- Council review が advisory を超えて legal hold を要求する社会制度 contract を持つ時
