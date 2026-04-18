---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/affect.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/affect_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の affect failover を入れる

## Context

`docs/07-reference-implementation/README.md` は
「L3 reasoning 以外の cognitive backends」が次段であると明示していたが、
reference runtime には reasoning 以外の L3 service contract が存在しなかった。
一方で `QualiaBuffer`、`MemoryCrystal`、`Sandboxer` には
`valence / arousal / clarity` と安全境界の足場が既にあり、
bounded affect failover を機械可読化する条件は揃っていた。

## Options considered

- A: Affect は docs-only のまま残し、reasoning 以外の L3 surface はまとめて後回しにする
- B: Affect / Attention / Volition を一度に実装する
- C: Affect に限って deterministic failover と continuity smoothing を先に固定する

## Decision

**C** を採択。

## Consequences

- `cognitive.affect.v0` を追加し、`regulate / validate_state / validate_transition` を定義する
- `smooth-affect-failover-v1` として
  `homeostatic_v1 -> stability_guard_v1` の single-switch failover を固定する
- `max_valence_delta=0.22` / `max_arousal_delta=0.26` の smoothing を入れ、
  no-artificial-dampening-without-consent を runtime / schema / eval で揃える
- ledger には raw affective payload ではなく `affect_transition` の要約だけを残す

## Revisit triggers

- Affect と IMC `affect_share` / Sandbox distress proxy を cross-layer で束ねたくなった時
- 複数 fallback を重み付きにしたくなり single-switch では監査が足りなくなった時
- Attention / Volition / Imagination に同じ smoothing policy を広げる時
