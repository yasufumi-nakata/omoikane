---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/01-architecture/failure-modes.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/backend_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の reasoning failover を入れる

## Context

`docs/07-reference-implementation/README.md` では L3 cognitive backends の複数実装が
今後の拡張面として残っており、`specs/catalog.yaml` でも
`evals/cognitive/backend_failover.yaml` が次優先に残っていた。
一方で runtime 側には L3 backend がまだ存在せず、failover 方針を
eval でも code でも検証できない状態だった。

## Options considered

- A: L3 backend 実装が揃うまで failover を docs/evals の保留項目として残す
- B: reasoning / affect / attention をまとめて一気に実装する
- C: `Reasoning` に限って deterministic な failover を先に入れ、ledger 記録まで固定する

## Decision

**C** を採択。

## Consequences

- reference runtime に `ReasoningService` と 2 backend の最小 failover を追加する
- `backend_failover.yaml` を cognitive eval の実装済み面へ昇格する
- failover は health-based single switch のみとし、複数 backend 同時調停や
  Affect/Attention への拡張は将来課題として残す
- failover の結果は `cognitive.reasoning.failover` として ContinuityLedger に記録する

## Revisit triggers

- reasoning backend が 3 系統以上になり、単純 fallback では監査が足りなくなった時
- Affect / Attention / Volition に同等の failover を導入する時
- cognitive service の外部 IDL を昇格させる時
