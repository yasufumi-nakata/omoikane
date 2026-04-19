---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/volition.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/volition_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の volition failover を入れる

## Context

`docs/07-reference-implementation/README.md` と `evals/cognitive/README.md` は
L3 cognitive の次段候補として `volition / imagination` を挙げていたが、
reference runtime には `Attention` と `Affect` の guard を束ねて
1 つの bounded intent を選ぶ service contract がなかった。
`AttentionService` は safe target を返せるようになっており、
`AffectService` も `recommended_guard` を返すため、
guard-aware な意図選択を machine-readable に固定する条件は既に揃っていた。

## Options considered

- A: Volition は docs-only のまま残し、L3 追加 surface はまとめて後回しにする
- B: Volition と Imagination を同時に実装する
- C: Volition に限って deterministic failover と guard-aware safe intent routing を先に固定する

## Decision

**C** を採択。

## Consequences

- `cognitive.volition.v0` を追加し、`arbitrate_intent / validate_intent / validate_shift` を定義する
- `bounded-volition-failover-v1` として
  `utility_policy_v1 -> guardian_bias_v1` の single-switch failover を固定する
- `observe` / `sandbox-notify` guard 時は
  `guardian-review` / `sandbox-stabilization` / `continuity-hold` の safe intent へ寄せる
- irreversible intent を review なしで advance しない policy を
  runtime / schema / eval で一貫させる

## Revisit triggers

- Imagination を追加し、`co_imagination` や WMS と cross-layer で束ねたくなった時
- L4 Council の deliberation evidence を volition arbitration と接続したくなった時
- 複数 backend の同時実行や confidence arbitration が必要になり、
  single-switch では監査が足りなくなった時
