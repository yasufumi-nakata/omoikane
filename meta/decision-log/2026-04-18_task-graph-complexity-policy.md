---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/task-decomposition.md
  - docs/02-subsystems/agentic/README.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/task_graph_complexity_guard.yaml
  - specs/interfaces/agentic.task_graph.v0.idl
  - specs/schemas/task_graph_policy.schema
status: decided
---

# Decision: TaskGraph の reference complexity policy を固定する

## Context

`meta/open-questions.md` に残っていた `TaskGraph の複雑度上限` は、
L4 の docs と IDL には TaskGraph の存在が書かれている一方で、
runtime・CLI・eval のどこにも graph-level cap がありませんでした。
このままでは Council が過大な DAG を作っても
reference runtime では止められず、安全境界の検証対象になりません。

## Options considered

- A: 複雑度上限は研究課題のまま残し、runtime には何も入れない
- B: node 単位制約だけを `task_node.schema` に足し、graph-level cap は持たない
- C: reference runtime 用の graph-level policy を固定し、
  `build_graph / dispatch_graph / synthesize_results` をその範囲で実装する

## Decision

**C** を採択。

## Consequences

- reference runtime は `TaskGraphComplexityPolicy(policy_id=reference-v0)` を持つ
- 上限は `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5`
  に固定する
- executable node は最大 3 つまでとし、その後に `council-review` と
  `result-synthesis` を 1 段ずつ置く
- 上限超過の要求は build 前に reject し、より大きい DAG は二段階に分割する前提にする
- CLI/eval/test から同じ policy を可視化し、L4 の reference surface を検証可能にする

## Revisit triggers

- YaoyorozuRegistry が実装され、実 agent の並列能力を観測可能になった時
- multi-Council federation や human approval queue を導入し、
  depth 3 を超える DAG が必要になった時
- dispatch telemetry が蓄積され、`max_parallelism=3` が保守的すぎる、
  または危険すぎると判定された時
