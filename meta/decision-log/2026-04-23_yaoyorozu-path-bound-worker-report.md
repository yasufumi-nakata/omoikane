---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_local_worker_dispatch.yaml
status: decided
---

# Decision: Yaoyorozu local worker report を path-bound workspace observation へ昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local subprocess worker dispatch を持っていましたが、
worker report は `ready` と基本 identity field を返すだけで、
dispatch plan / dispatch unit / workspace target との結び付きが弱い状態でした。

このままでは
`yaoyorozu_worker_dispatch_receipt` が zero-exit を示しても、
worker が実際に repo 内の intended target path を見たのか、
あるいは workspace 境界を守っていたのかを machine-checkable に証明できません。

## Options considered

- A: current ready-only report を維持し、workspace target verification は future work に残す
- B: dispatch/unit binding だけを echo し、path observation は持ち込まない
- C: dispatch/unit binding に加えて workspace-bounded target path observation を返す

## Decision

**C** を採択。

## Consequences

- `local_worker_stub` は
  `dispatch_plan_ref` / `dispatch_unit_ref` / `workspace_root` /
  `invocation_digest` を report に含める
- worker report は
  `target_path_observations` と `coverage_evidence` を返し、
  target path の存在確認と workspace boundary を ready gate に含める
- `yaoyorozu_worker_dispatch_receipt` は
  `report_binding_ok` / `target_paths_ready` を result ごとに持ち、
  execution summary / validation でも同じ binding を aggregate する
- residual gap は generic な「local worker は動くが何を見たか不明」ではなく、
  actual code mutation や cross-workspace remote dispatch のような repo 外 coordination へ縮小する

## Revisit triggers

- worker report を target path existence ではなく
  actual patch candidate / diff evidence まで昇格したくなった時
- repo-local subprocess を超えて
  external sandbox / remote runtime / brokered execution へ dispatch したくなった時
- worker report を ConsensusBus / TaskGraph / builder apply receipt と
  同じ execution digest で統合したくなった時
