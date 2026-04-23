---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_recovery_review.schema
  - specs/schemas/trust_redacted_destination_lifecycle.schema
  - specs/schemas/trust_redacted_destination_recovery_summary.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-multi-root-recovery-quorum.md#agentic.trust.recovery-rationale-redaction-summary
---

# Decision: Trust redacted export では recovered branch の rationale / legal proof を destination recovery summary に縮約する

## Context

2026-04-24 時点で `trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1`
は snapshot、verifier federation、destination lifecycle まで summary 化されていましたが、
recovered branch が「なぜ fail-closed から current に戻れたのか」を示す
reviewer-facing root cause と legal proof floor は残っていませんでした。

このままでは redacted export が
multi-root / cross-jurisdiction recovery quorum の成立までは public に示せても、
recovery rationale と jurisdiction policy/bundle binding が
full lifecycle の raw rationale に埋もれたままになり、
reviewer-facing disclosure floor を machine-checkable に固定できません。

## Options considered

- A: recovered entry の raw rationale だけを redacted lifecycle に露出し、summary surface は増やさない
- B: trust transfer receipt 直下へ flat な recovery summary field を追加し、destination lifecycle とは分離する
- C: full recovered entry に `trust_recovery_review` を追加し、redacted export では `trust_redacted_destination_recovery_summary` を `trust_redacted_destination_lifecycle` に束縛する

## Decision

**C** を採択。

## Consequences

- full-clone profile の recovered entry は `trust_recovery_review` を持ち、
  `review_scope=destination-trust-recovery-review`、
  fixed `reason_codes`、
  jurisdiction policy refs / bundle refs、
  reviewer binding digest、
  sealed `legal_ack_refs`、
  raw rationale を 1 object に束ねる
- redacted profile の `trust_redacted_destination_lifecycle` は
  active recovered entry に束縛された
  `trust_redacted_destination_recovery_summary` を公開し、
  rationale digest、summary text、legal proof digest、
  policy refs / bundle refs / liability mode を public floor として返す
- validator は `recovery_review_bound` を追加し、
  full / redacted のどちらでも recovered branch が
  fixed recovery review surface に束縛されていることを継続検証する
- schema / IDL / docs / eval / CLI / unit test / integration test は
  recovered-branch review summary contract に同期した

## Revisit triggers

- recovery summary に jurisdiction-specific notice authority や execution scope まで露出したくなった時
- recovery review を fixed 3 jurisdiction から rotating legal roster へ広げたくなった時
- recovery rationale summary を destination lifecycle ではなく standalone reviewer export family に切り出したくなった時
