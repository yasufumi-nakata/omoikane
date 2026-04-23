---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/build_request.yaml
  - specs/schemas/yaoyorozu_build_request_binding.schema
  - evals/agentic/yaoyorozu_build_request_binding.yaml
status: decided
---

# Decision: Yaoyorozu execution bundle を L5 build_request handoff へ束縛する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
same-host workspace discovery、bounded Council convocation、
repo-local worker dispatch、`ConsensusBus` binding、
proposal-profile-aware `TaskGraph` bundle までは
machine-checkable でした。

一方でその execution bundle は
L5 self-construction 側の `build_request` へはまだ接続されておらず、
`yaoyorozu-demo` の reviewer-facing output だけを見ても
「この Council / worker / TaskGraph artifact がどの L5 handoff に昇格するのか」
を repo 内 contract として監査できませんでした。

## Options considered

- A: Yaoyorozu は L4 orchestration だけを維持し、L5 handoff は別 demo に委ねる
- B: convocation / dispatch / ConsensusBus / TaskGraph bundle を同じ session の `build_request` と patch-generator-ready scope validation に束縛する
- C: `build_request` を飛ばして直接 `build_artifact` / `sandbox_apply_receipt` へ接続する

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `bind_build_request_handoff` を持ち、
  `yaoyorozu_build_request_binding` を public contract に追加する
- handoff は `L5.PatchGenerator` 向け `build_request` を生成し、
  `evals/continuity/council_output_build_request_pipeline.yaml` と
  proposal-profile-aware Yaoyorozu eval を `must_pass` に束縛する
- `build_request` は patch-generator-ready な scope validation を通しつつ、
  worker dispatch 由来の priority-ranked patch candidate hint を同じ binding に残す
- `yaoyorozu-demo` / schema contract / runtime integration / CLI integration / docs は
  L4 execution bundle から L5 handoff までを一続きの reference chain として継続検証する
- next-stage frontier は broad な L4/L5 separation ではなく、
  `build_artifact` / `sandbox_apply_receipt` / rollback witness を
  同じ digest family に統合する reviewer-facing execution chain へ縮小する

## Revisit triggers

- `build_request` だけでなく `build_artifact` と `sandbox_apply_receipt` まで
  same-session binding に昇格したくなった時
- selected patch candidate hint を
  actual patch application witness や rollback witness と同一 digest で統合したくなった時
- repo-local subprocess / patch-generator-ready scope を超えて
  remote sandbox や brokered builder runtime にも同じ handoff contract を持ち込みたくなった時
