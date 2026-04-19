---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/attention.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/attention_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の attention failover を入れる

## Context

`docs/07-reference-implementation/README.md` は
L3 cognitive backends の次段候補として `attention / volition / imagination`
を挙げていたが、reference runtime には
`QualiaBuffer.attention_target` を受ける dedicated な L3 service contract がなかった。
一方で `QualiaBuffer` には `modality_salience` と `attention_target` があり、
`AffectService` も `recommended_guard` を返すため、
bounded attention routing を機械可読化する条件は既に揃っていた。

## Options considered

- A: Attention は docs-only のまま残し、L3 追加 surface はまとめて後回しにする
- B: Attention / Volition / Imagination を一度に実装する
- C: Attention に限って deterministic failover と affect-aware safe target を先に固定する

## Decision

**C** を採択。

## Consequences

- `cognitive.attention.v0` を追加し、`route_focus / validate_focus / validate_shift` を定義する
- `hybrid-attention-failover-v1` として
  `salience_router_v1 -> continuity_anchor_v1` の single-switch failover を固定する
- `observe` / `sandbox-notify` guard 時は
  `guardian-review` / `sandbox-stabilization` など safe target へ寄せる
- ledger には raw sensory payload ではなく `attention_shift` の要約だけを残す

## Revisit triggers

- Attention と Sandboxer / WMS / IMC `co_imagination` を cross-layer で束ねたくなった時
- Volition や Imagination を追加し、L3 cognitive policy を service 横断で揃えたくなった時
- 複数 fallback を同時調停したくなり single-switch では監査が足りなくなった時
