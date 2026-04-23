---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_task_graph_binding.schema
  - evals/agentic/yaoyorozu_task_graph_binding.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-consensus-dispatch-binding.md#yaoyorozu.consensus.to-taskgraph
next_gap_ids:
  - yaoyorozu.taskgraph.profile-aware-bundles
---

# Decision: Yaoyorozu worker dispatch を three-root TaskGraph execution bundle に束縛する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local registry sync、
bounded Council convocation、
repo-local worker dispatch receipt、
same-session `ConsensusBus` binding までは machine-checkable でした。

一方で最新の revisit trigger には、
worker dispatch receipt を `TaskGraph` node / `ConsensusBus` claim /
guardian gate digest と同一 execution bundle に統合したい、
という残差が残っていました。

この状態では selected builder 群が
same-session `ConsensusBus` までは閉じていても、
L4 `TaskGraph` の complexity policy 上で
どう review / synthesis へ渡されるかを
repo 内の public contract として確認できませんでした。

## Options considered

- A: current の `yaoyorozu_consensus_dispatch_binding` までで止め、TaskGraph 側は別 demo として分離したままにする
- B: `TaskGraph` complexity ceiling は維持したまま、4 worker coverage を 3 root bundle に畳んで same-session binding artifact を追加する
- C: `TaskGraph` の `max_parallelism` を 4 へ引き上げ、worker coverage と 1:1 に揃える

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `bind_task_graph_dispatch` を持ち、
  `yaoyorozu_task_graph_binding` を public contract にする
- reference runtime は
  `runtime` / `schema` / `evidence-sync(eval+docs)` の 3 root bundle を生成し、
  fixed `max_parallelism=3` / `max_nodes=5` を崩さずに
  worker dispatch receipt を `TaskGraph` review / synthesis へ接続する
- 各 root bundle は dispatch unit、ConsensusBus report claim、
  guardian gate digest、resolve digest を同じ session で保持し、
  `yaoyorozu-demo` 1 run で reviewer-facing に監査できる
- residual gap は generic な Yaoyorozu/TaskGraph 分離ではなく、
  profile ごとの bundle strategy や external worker runtime / remote scheduler 連携へ縮小する

## Revisit triggers

- `self-modify-patch-v1` 以外の proposal profile でも bundle grouping を変えたくなった時
- `TaskGraph` complexity policy 自体を 3 root bundle 以外へ見直したくなった時
- repo-local subprocess を超えて external worker runtime や remote sandbox cluster へ
  same-session dispatch したくなった時
