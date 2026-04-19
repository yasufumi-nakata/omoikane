---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/imagination.md
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/imagination_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の imagination failover と handoff gate を入れる

## Context

`docs/07-reference-implementation/README.md` と `specs/interfaces/README.md` は
L3 imagination を未昇格 surface として残していたが、
`interface.imc.v0` には既に `co_imagination` が mode として存在していた。
このままでは L6 側が scene 共有を想定しているのに、
L3 側に bounded scene を compose する machine-readable contract が無く、
failover 時にどこまで private fallback へ縮退すべきかも固定されない。

## Options considered

- A: Imagination は docs-only のまま残し、`co_imagination` は IMC の mode 名だけに留める
- B: Imagination と merge-thought / collective imagination をまとめて一気に実装する
- C: Imagination に限って deterministic failover と IMC/WMS handoff gate を先に固定する

## Decision

**C** を採択。

## Consequences

- `cognitive.imagination.v0` を追加し、`compose_scene / validate_scene / validate_shift` を定義する
- `bounded-counterfactual-handoff-v1` として
  `counterfactual_scene_v1 -> continuity_scene_guard_v1` の single-switch failover を固定する
- `nominal + council_witnessed` の時だけ `co_imagination` / `shared_reality` handoff を許可し、
  `observe` / `sandbox-notify` guard 時は `private-sandbox` / `private_reality` へ縮退する
- `imagination-demo` で baseline handoff と failover fallback を
  `IMC` / `WMS` の実インスタンスと一緒に smoke できる

## Revisit triggers

- `merge_thought` や collective imagination を L3/L6 横断で扱いたくなった時
- scene を procedural enactment や language planner へ直接渡したくなった時
- 複数 imagination backend の同時実行や confidence arbitration が必要になり、
  single-switch では監査が足りなくなった時
