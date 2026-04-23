---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_event.schema
  - evals/agentic/trust_score_update_guard.yaml
status: decided
---

# Decision: Trust update を provenance-bound anti-tamper guard 付きで fail-closed にする

## Context

2026-04-23 時点で `agentic.trust.v0` と `TrustService` は
delta table、threshold gate、human pin freeze までは machine-checkable でしたが、
`triggered_by` は free-form string のままで、
docs には
「Agent 自身による自己 trust 改ざん攻撃」
「集合的な trust 操作（複数 Agent が結託）」
が未解決として残っていました。

この状態では positive trust event の provenance が weak で、
self-issued boost や reciprocal positive boost を
public contract として fail-closed に確認できませんでした。

## Options considered

- A: current delta table と human pin freeze だけを維持し、anti-tamper は docs 上の research frontier に残す
- B: provenance guard を `trust_event` に追加し、Council / Guardian / Human origin と self / reciprocal positive block を deterministic に固定する
- C: trust update を外部 attestation service 前提に置き換え、repo 内 runtime では provenance を扱わない

## Decision

**B** を採択。

## Consequences

- `trust_event` は `triggered_by_agent_id`、`provenance_status`、
  `provenance_policy_id=reference-trust-provenance-v1` を保持する
- `TrustService.record_event()` は positive event について、
  self-issued boost、origin mismatch、registered agent 同士の reciprocal positive boost を
  fail-closed にしつつ append-only history へ残す
- `trust-demo` は accepted Council / Guardian / Human origin に加えて、
  blocked self-issued positive、blocked reciprocal positive、
  pinned negative freeze を同じ scenario で返す
- `evals/agentic/trust_score_update_guard.yaml`、unit test、runtime/CLI integration test、
  schema contract test が同じ provenance policy を継続検証する
- unresolved gap は generic な trust tampering 全般ではなく、
  cross-substrate trust transfer や external attestation federation のような次段へ縮小する

## Revisit triggers

- trust provenance を repo-local history ではなく
  external attestation ledger や witness quorum へ拡張したくなった時
- cross-substrate trust transfer を import/export receipt 付きで materialize したくなった時
- reciprocal detection を domain history から time-bounded campaign graph へ拡張したくなった時
