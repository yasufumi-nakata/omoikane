---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/reasoning.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/backend_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reasoning failover を dedicated service contract へ昇格する

## Context

reference runtime には `ReasoningService` が既に存在し、
`evals/cognitive/backend_failover.yaml` でも failover 自体は検証されていた。
一方で他の L3 cognitive surfaces と違い、reasoning だけは
`specs/interfaces/README.md` 上で internal-only 扱いのまま残っており、
schema-bound な trace / shift や dedicated CLI surface も不足していた。

## Options considered

- A: reasoning は internal helper のまま維持し、docs だけで補足する
- B: `cognitive-demo` を残したまま、IDL/schema を追加せず現状維持する
- C: reasoning を他の L3 surfaces と同じ水準まで昇格し、trace / shift / CLI / docs を揃える

## Decision

**C** を採択。

## Consequences

- `cognitive.reasoning.v0` を追加し、`reason / validate_trace / validate_shift` を定義する
- `reasoning_trace.schema` / `reasoning_shift.schema` を追加し、
  raw trace と ledger-safe summary を分離する
- canonical command は `reasoning-demo` とし、`cognitive-demo` は互換 alias として残す
- `evals/cognitive/backend_failover.yaml` は reasoning 専用 eval として扱い続ける

## Revisit triggers

- reasoning backend が 3 系統以上になり single-switch では監査が足りなくなった時
- Council による multi-backend adjudication を reasoning runtime に直接接続したくなった時
- richer planner / theorem / probabilistic reasoning surfaces を別 service として切り出す時
