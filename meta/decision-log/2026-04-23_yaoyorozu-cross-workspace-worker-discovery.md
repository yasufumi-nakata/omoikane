---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_workspace_discovery.schema
  - evals/agentic/yaoyorozu_workspace_discovery.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-local-worker-dispatch.md#yaoyorozu.local-worker.repo-local-only
next_gap_ids:
  - yaoyorozu.workspace.external-execution
---

# Decision: Yaoyorozu cross-workspace worker discovery を bounded same-host catalog に昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local registry sync、bounded Council convocation、
repo-local worker dispatch receipt、same-session `ConsensusBus` binding、
three-root `TaskGraph` execution bundle までは machine-checkable でした。

一方 compatibility note には
`Cross-workspace worker discovery remains outside this repo.`
が残っており、repo 外 checkout に builder surface が存在する場合でも、
どの local workspace が runtime / schema / eval / docs の coverage を持つかを
public artifact として監査できませんでした。

## Options considered

- A: cross-workspace discovery は引き続き docs-only に留め、repo-local dispatch のみを維持する
- B: same-host local workspace に限定した bounded discovery catalog を追加し、builder coverage を machine-readable に固定する
- C: discovery を飛ばして external runtime dispatch まで一気に実装する

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `discover_workspace_workers` を持ち、
  `yaoyorozu_workspace_discovery` を public contract にする
- reference runtime は
  source workspace と 2 つの candidate workspace を `review_budget=3` で走査し、
  same-host local catalog、builder role presence、
  runtime / schema / eval / docs coverage summary、
  non-source workspace 群だけでの aggregate coverage を 1 artifact に束縛する
- `yaoyorozu-demo` は
  workspace discovery -> repo-local registry sync -> convocation -> dispatch ->
  `ConsensusBus` -> `TaskGraph` の順で L4 orchestration chain を reviewer-facing に可視化する
- residual gap は generic な cross-workspace discovery 不在ではなく、
  external worker runtime dispatch、remote sandbox cluster、cross-host execution witness のような
  repo 外 orchestration へ縮小する

## Revisit triggers

- same-host local catalog を超えて remote worker runtime / remote scheduler へ dispatch したくなった時
- workspace discovery を trust snapshot exchange や Guardian oversight digest と
  同じ execution bundle に統合したくなった時
- proposal profile ごとに required coverage area や review budget を変えたくなった時
