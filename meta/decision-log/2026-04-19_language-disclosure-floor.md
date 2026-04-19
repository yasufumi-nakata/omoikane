---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/02-subsystems/cognitive/language.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/language_failover.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: reference runtime に最小の language bridge を入れる

## Context

`docs/07-reference-implementation/README.md` と
`specs/interfaces/README.md` には、L3 `Language` が
次段の durable gap として残っていた。
一方で reference runtime には `Attention`、`Affect`、
`Metacognition` までの bounded state が揃っており、
thought-to-text の outward boundary を deterministic に固定する条件は既に整っていた。

## Options considered

- A: Language は docs-only のまま残し、distributed council など他の surface を先に進める
- B: Language を free-form generation surface として広く実装する
- C: Language に限って disclosure floor 付きの bounded thought-to-text bridge を先に固定する

## Decision

**C** を採択。

## Consequences

- `cognitive.language.v0` を追加し、`render_text / validate_render / validate_shift` を定義する
- `bounded-thought-text-bridge-v1` として
  `semantic_frame_v1 -> continuity_phrase_v1` の single-switch failover を固定する
- `observe` / `sandbox-notify` guard 時は送達先を `guardian` / `self` に縮退し、
  public points 3 件・redacted terms 4 件までの disclosure floor を必須化する
- ledger には raw `internal_thought` を残さず、`language_shift` の要約だけを残す

## Revisit triggers

- Language と IMC / WMS / external agent delivery を cross-layer で束ねたくなった時
- structured planner や syntax tree を持つ richer language backend を比較導入したくなった時
- disclosure floor だけでは法務・医療向け attest が足りず、audience-specific policy が必要になった時
