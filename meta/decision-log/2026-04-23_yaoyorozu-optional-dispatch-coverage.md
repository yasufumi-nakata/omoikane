---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/council_convocation_session.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - specs/schemas/yaoyorozu_task_graph_binding.schema
  - evals/agentic/yaoyorozu_memory_edit_optional_schema_dispatch.yaml
  - evals/agentic/yaoyorozu_fork_request_optional_eval_dispatch.yaml
status: decided
---

# Decision: Yaoyorozu optional builder coverage を requested on-demand dispatch として固定する

## Context

2026-04-23 時点で `memory-edit-v1` と `fork-request-v1` は
required coverage だけを actual builder dispatch / TaskGraph へ載せる
profile-aware runtime まで閉じていました。

しかし optional coverage を必要時だけ起動したい repo-local path は
まだ public contract に出ておらず、
`schema` / `eval` の補助 worker を
same-session dispatch / receipt / TaskGraph bundle として
machine-checkable に要求する方法がありませんでした。

## Options considered

- A: optional coverage は引き続き review-only に留め、dispatch へは載せない
- B: proposal profile ごとの optional coverage を explicit request でだけ追加し、convocation / dispatch / receipt / TaskGraph に first-class で束縛する
- C: optional coverage の起動有無を runtime が毎回自動推定し、public contract では request を持たない

## Decision

**B** を採択。

## Consequences

- `prepare_council_convocation()` は
  `requested_optional_builder_coverage_areas` を受け取り、
  `dispatch_builder_coverage_areas` を same-session artifact として保持する
- `prepare_worker_dispatch()` / `execute_worker_dispatch()` は
  `requested_optional_coverage_areas` と `dispatch_coverage_areas` を保持し、
  selected optional coverage も required coverage と同じ dispatch-bound receipt に束縛する
- `memory-edit-v1` は `--include-optional-coverage schema` で
  `memory-edit-optional-schema-dispatch-three-root-v1` へ、
  `fork-request-v1` は `--include-optional-coverage eval` で
  `fork-request-optional-eval-dispatch-three-root-v1` へ
  deterministic に切り替わる
- `agentic.yaoyorozu.v0` / schema / eval / CLI / tests は
  requested optional coverage を public contract として継続検証する

## Revisit triggers

- optional coverage を 1 surface ずつの explicit request ではなく、
  severity / trust / legal gate に応じた auto-selection へ拡張したくなった時
- same-host repo-local subprocess を超えて remote scheduler / brokered sandbox にも
  requested optional coverage policy を持ち込みたくなった時
