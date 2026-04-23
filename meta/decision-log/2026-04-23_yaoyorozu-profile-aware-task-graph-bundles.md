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
  - evals/agentic/yaoyorozu_memory_edit_profile.yaml
  - evals/agentic/yaoyorozu_fork_request_profile.yaml
status: decided
---

# Decision: Yaoyorozu TaskGraph binding を proposal profile ごとの three-root bundle strategy へ昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
same-host workspace discovery、
proposal profile catalog、
repo-local worker dispatch、
same-session `ConsensusBus` binding、
three-root `TaskGraph` execution bundle までは machine-checkable でした。

一方で `TaskGraph` 側の grouping は
`runtime` / `schema` / `evidence-sync(eval+docs)` に固定されており、
`memory-edit-v1` と `fork-request-v1` を追加しても
profile ごとの review emphasis が public contract に反映されませんでした。

この状態では profile catalog が増えても、
`TaskGraph` bundle が毎回同じ shape のままになり、
proposal profile ごとの bounded execution policy を
repo 内で reviewer-facing に監査できません。

## Options considered

- A: 全 proposal profile で同一 three-root bundle を維持し、profile 差分は Council panel だけに留める
- B: `max_parallelism=3` を維持したまま、proposal profile ごとに fixed three-root bundle strategy を切り替える
- C: worker coverage と 1:1 に合わせるため `TaskGraph` の `max_parallelism` を引き上げる

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_task_graph_binding` は
  `proposal_profile` と `bundle_strategy` を first-class field として持つ
- reference runtime は
  `self-modify-patch-v1` を
  `runtime` / `schema` / `evidence-sync(eval+docs)`、
  `memory-edit-v1` を
  `runtime+eval` / `schema` / `docs`、
  `fork-request-v1` を
  `runtime` / `schema+docs` / `eval`
  の fixed three-root strategy へ束縛する
- `yaoyorozu-demo` は profile ごとに異なる TaskGraph bundle strategy を返しつつ、
  すべて `max_parallelism=3` / `root_count=3` を維持する
- `evals/agentic/yaoyorozu_task_graph_binding.yaml`、
  `yaoyorozu_memory_edit_profile.yaml`、
  `yaoyorozu_fork_request_profile.yaml`、
  unit / integration / schema contract test が
  strategy selection と grouping drift を継続検証する
- residual gap は generic な profile unawareness ではなく、
  profile ごとの `review_budget` / required coverage branching や
  `inter-mind-negotiation-v1` のような次段の catalog 拡張へ縮小する

## Revisit triggers

- proposal profile ごとに `review_budget` や required coverage area 自体を変えたくなった時
- `inter-mind-negotiation-v1` や `fork-request-v2` を追加し、
  fourth strategy を bounded catalog に増やしたくなった時
- repo-local subprocess を超えて external worker runtime / remote scheduler へ
  same-session dispatch したくなった時
