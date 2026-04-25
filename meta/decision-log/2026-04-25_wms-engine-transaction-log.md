---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_engine_transaction_log.schema
  - evals/interface/wms_engine_transaction_log.yaml
status: decided
closes_next_gaps:
  - 2026-04-25_wms-approval-collection-scaling.md#gap-1
  - 2026-04-25_wms-distributed-approval-fanout.md#gap-1
  - 2026-04-25_wms-time-rate-attestation-transport.md#gap-1
---

# Decision: WMS source artifacts を external engine transaction log receipt へ束縛する

## Context

WMS の time_rate deviation、approval collection、distributed fan-out、physics_rules
apply / revert は reference receipt として閉じていました。
一方で external / multi-user engine adapter がそれらをどの committed transaction
として materialize したかは、source artifact digest と ordered state transition の
同一 receipt で確認できませんでした。

## Options considered

- A: engine adapter 統合は real engine 実装が来るまで docs のみで保留する
- B: raw engine transaction payload を WMS demo に保存する
- C: source artifact digest、ordered committed entry、state transition digest、
  redaction flag を `wms_engine_transaction_log` receipt に縮約する

## Decision

**C** を採択。

`digest-bound-wms-engine-transaction-log-v1` は次の 5 operation を必須化する。

- `time_rate_escape_evidence`
- `approval_collection_bound`
- `approval_fanout_bound`
- `physics_rules_apply`
- `physics_rules_revert`

各 entry は `wms-engine-transaction-entry-digest-v1` で source artifact digest、
engine state before/after digest、participant set、committed status を束縛し、
`payload_redacted=true` / `raw_payload_stored=false` を必須にする。

## Consequences

- `wms-demo --json` は `engine_transaction_log` scenario と
  `engine_transaction_log_bound` validation を返す
- public schema / IDL / eval / Integrity Guardian capability は同じ policy id を共有する
- `gap-report --json` は `Remaining scope` / `Deferred scope` の operational adapter follow-up を surfacing でき、今回閉じた WMS adapter gap は `closes_next_gaps` で除外される

## Revisit triggers

- real WMS engine adapter が transaction body の external signed hash を返す時
- cross-host engine adapter を distributed transport route trace と直接束縛する時
