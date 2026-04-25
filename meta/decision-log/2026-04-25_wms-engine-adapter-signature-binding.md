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
  - 2026-04-25_wms-engine-transaction-log.md#gap-2
---

# Decision: WMS engine transaction log を adapter signature digest に束縛する

## Context

`digest-bound-wms-engine-transaction-log-v1` は WMS source artifact、ordered entry、
state transition、redaction flag を external engine adapter receipt へ束縛していた。
一方で completed log がどの adapter signer key によって承認されたかは
`engine_adapter_ref` だけでは machine-checkable ではなかった。

## Options considered

- A: adapter signer は route trace / capture binding で間接的に検証する
- B: raw adapter signature payload を receipt に保存する
- C: adapter signer key ref と signature digest だけを transaction log receipt に追加する

## Decision

**C** を採択。

`signed-wms-engine-adapter-log-v1` は adapter signer key ref、adapter ref、
engine session ref、transaction log ref、required / covered operation set、
ordered transaction digest set、source artifact digest set、state-transition digest、
current WMS state digest を署名対象にする。

receipt は `engine_adapter_signature_digest`、
`engine_adapter_signature_digest_profile=wms-engine-adapter-signature-digest-v1`、
`engine_adapter_signature_bound=true`、`raw_adapter_signature_stored=false` を返す。

## Consequences

- `wms-demo --json` の `engine_transaction_log` scenario は adapter signer key ref と
  signature digest binding を含む
- public schema / IDL / eval / Integrity Guardian capability は同じ signature profile を共有する
- `validate_engine_transaction_log_receipt()` は source artifact や signature digest の
  改ざんをどちらも `engine_binding_status=complete` から排除する

## Remaining frontier

- jurisdiction policy registry / authority SLO snapshot から retry schedule を導出する
  registry-bound receipt は別 gap として残る
