---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/memory-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.memory_replication.v0.idl
  - specs/schemas/memory_replication_session.schema
  - evals/continuity/memory_replication_quorum.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - memory-replication-endpoint-certificate-rollover-chain-3-generations
---

# Decision: MemoryReplication endpoint certificate rollover chain を 3 世代に固定する

## Context

`long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` は
registry endpoint の current certificate と previous certificate retirement digest を
registry response quorum、CT-style readback、SCT policy authority へ束縛していた。
ただし previous certificate は各 jurisdiction につき 1 本だけだったため、rollover
が 2 回続いた場合に reviewer-facing な chain depth を runtime / schema / eval の
同一 contract として確認できなかった。

## Decision

MemoryReplication の endpoint certificate lifecycle は
`certificate_lifecycle_generation_count = 3` を固定 contract とする。
各 registry jurisdiction は current certificate に加えて `previous` と
`previous-2` の 2 本を持ち、flattened receipt では JP-13 / SG-01 合計で
`previous_certificate_refs`、`previous_certificate_fingerprints`、
`previous_retirement_digest_set` を 4 件ずつ返す。

certificate chain digest は current fingerprint と 2 世代分の previous
fingerprint set を束縛し、CT readback digest は同じ jurisdiction の
previous retirement digest set をまとめて参照する。raw certificate payload、
raw certificate lifecycle payload、raw CT log payload、raw SCT policy authority
payload は保存しない。

## Consequences

- `memory-replication-demo --json` の validation summary は
  `long_term_media_renewal_registry_endpoint_certificate_chain_generation_count = 3`
  を返す。
- `memory_replication_session.schema` は previous certificate / retirement digest
  set を 4 件に固定し、policy profile の chain generation count と一致させる。
- continuity eval と IntegrityGuardian は endpoint certificate lifecycle を
  3-generation rollover chain として検証する。

## Revisit triggers

- 実 registry endpoint / CT log / SCT authority の live response を参照する時
- 4 世代以上の certificate rollover depth を policy として必要にする時
