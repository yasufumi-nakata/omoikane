---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/self_model_abrupt_change.yaml
  - evals/identity-fidelity/self_model_stability.yaml
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_observation.schema
status: decided
---

# Decision: SelfModel abrupt-change threshold を 0.35 に固定する

## Context

`SelfModelMonitor` 自体は repo にありましたが、
docs/02-subsystems/mind-substrate/README.md では
「SelfModel の急変検知の閾値」が未解決のまま残っていました。
この状態では `evals/cognitive/self_model_abrupt_change.yaml` と
`evals/identity-fidelity/self_model_stability.yaml` があっても、
どの divergence profile を reference runtime の真実源とするかが
CLI / docs / specs で同期されません。

## Options considered

- A: threshold は未解決のままにし、unit test の暗黙値だけで運用する
- B: adjacent snapshot 比較に限定して `threshold=0.35` を明示し、demo / IDL / schema を追加する
- C: relationships や identity_core まで含む richer self-model schema を一度に実装する

## Decision

**B** を採択。

## Consequences

- reference runtime は `bounded-self-model-monitor-v1` を採用する
- divergence は `values` / `goals` / `traits` の equal-weight average で計算する
- adjacent snapshot の divergence が `0.35` 以上なら `abrupt_change=true` とする
- `self-model-demo` は stable drift と abrupt takeover 候補を 1 本で smoke し、
  `mind.self_model.observed` ledger event を返す

## Revisit triggers

- `identity_core` / `relationships` / disclosure template を schema-bound に昇格したくなった時
- windowed 監視や time-decay を導入したくなった時
- human-confirmed identity drift と pathological takeover を別 policy に分けたくなった時
