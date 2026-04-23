---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_execution_chain_binding.schema
  - evals/agentic/yaoyorozu_execution_chain_binding.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-build-request-binding.md#yaoyorozu.build-request.execution-chain
---

# Decision: Yaoyorozu build_request handoff を reviewer-facing execution chain へ延長する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
same-session `build_request` handoff までは
`yaoyorozu_build_request_binding` として machine-checkable でした。

一方で builder 側の `build_artifact` / `sandbox_apply_receipt` /
live enactment / rollback は別 surface に分かれており、
`yaoyorozu-demo` だけでは
L4 Council / worker / TaskGraph bundle が
どの reviewer-facing builder execution chain に昇格したかを
同一 digest family で監査できませんでした。

## Options considered

- A: `yaoyorozu_build_request_binding` を維持し、downstream builder chain は引き続き別 demo に分離する
- B: same-session `build_request` handoff を起点に `build_artifact` / `sandbox_apply_receipt` / live enactment / rollback witness までを 1 artifact に束縛する
- C: repo-local chain を飛ばして remote sandbox / brokered builder runtime 側の execution witness から先に着手する

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `bind_execution_chain` を持ち、
  `yaoyorozu_execution_chain_binding` を public contract に追加する
- `yaoyorozu-demo` は same-session `build_request_binding` を起点に、
  `build_artifact` / `sandbox_apply_receipt` / `builder_live_enactment_session` /
  `staged_rollout_session` / `builder_rollback_session` を
  1 つの digest family に束縛して返す
- reviewer-facing summary は `required_eval_refs` と
  reviewer-network-attested rollback witness を持ち、
  `build_request` 由来の patch candidate hint が downstream chain に残る
- remaining scope は generic な `build_request` downstream 不在ではなく、
  remote sandbox / brokered builder runtime へ
  同じ execution-chain policy を carry over する段へ縮小する

## Revisit triggers

- repo-local rollback witness だけでなく
  actual patch application witness / `sandbox_apply_receipt` live mutation proof を
  同じ digest family に昇格したくなった時
- remote sandbox / brokered builder runtime でも
  same-session `yaoyorozu_execution_chain_binding` を再利用したくなった時
- reviewer-facing execution chain に
  external Guardian witness や remote worker attestation を混在させたくなった時
