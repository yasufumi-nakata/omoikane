---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/metacognition.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/metacognition_failover.yaml
  - specs/interfaces/cognitive.metacognition.v0.idl
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の metacognition self-monitor loop を入れる

## Context

`docs/07-reference-implementation/README.md` と `specs/interfaces/README.md` は
L3 `metacognition` を未昇格 surface として残していました。
一方で repo には `QualiaBuffer` と `SelfModelMonitor` がすでにあり、
abrupt change や lucidity drop を検知しても、
それを machine-readable な self-monitor report として束ねる境界がありませんでした。
このままでは L3 failover 群が揃っていても、
「自己状態をどう最小限に観測し、どこで guardian review へ上げるか」が
runtime / schema / eval のいずれにも固定されません。

## Options considered

- A: metacognition は docs-only のまま残し、SelfModel/Qualia の個別 primitive だけを使い続ける
- B: metacognition を bounded self-monitor report と continuity-safe failover に限定して先に昇格する
- C: language planner と metacognition をまとめて一気に実装する

## Decision

**B** を採択。

## Consequences

- `cognitive.metacognition.v0` を追加し、`generate_report / validate_report / validate_shift` を定義する
- reference runtime は `bounded-self-monitor-loop-v1` として
  `reflective_loop_v1 -> continuity_mirror_v1` の single-switch failover を固定する
- abrupt self-model change や `observe` / `sandbox-notify` guard は
  `guardian-review` / `sandbox-stabilization` へ deterministic に昇格する
- public report は values / goals を最大 3 件、private note を最大 4 件に制限し、
  ledger には shift summary だけを残す

## Revisit triggers

- language planner と thought-to-text bridge を L3 に昇格したくなった時
- metacognition を council audit や distributed oversight と直結したくなった時
- single report では足りず、time-series introspection や richer private memory loop が必要になった時
