---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/council_convocation_session.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_council_convocation.yaml
  - evals/agentic/yaoyorozu_memory_edit_profile.yaml
  - evals/agentic/yaoyorozu_fork_request_profile.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-profile-aware-workspace-review-policy.md#yaoyorozu.profile.dispatch-coverage
next_gap_ids:
  - yaoyorozu.profile.remote-dispatch-policy
---

# Decision: Yaoyorozu actual builder dispatch coverage を proposal-profile-aware required setへ縮退する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
workspace discovery の `review_budget` と required coverage を
proposal profile ごとに分岐できていました。

一方で actual builder handoff / worker dispatch は
`self-modify-patch-v1` / `memory-edit-v1` / `fork-request-v1`
の全 profile で
runtime / schema / eval / docs の 4 coverage を常に起動しており、
cross-workspace review policy と runtime execution policy が
ずれていました。

この状態では `memory-edit-v1` で schema worker、
`fork-request-v1` で eval worker が
public contract 上 optional なのに runtime では mandatory のままで、
profile-aware catalog の意味が dispatch surface で薄れていました。

## Options considered

- A: actual builder dispatch は 4 coverage 固定のまま維持し、profile 差分は workspace discovery と Council panel だけに留める
- B: actual builder dispatch も proposal profile の required coverage に合わせ、optional coverage は dispatch しない
- C: fixed profile catalog を崩し、dispatch coverage を trust / legal / ethics severity から毎回動的決定する

## Decision

**B** を採択。

## Consequences

- `self-modify-patch-v1` は引き続き `runtime/schema/eval/docs` の 4 coverage を dispatch する
- `memory-edit-v1` は `runtime/eval/docs` の 3 coverage だけを actual builder handoff / worker dispatch / TaskGraph binding に載せ、`schema` は optional review coverage に留める
- `fork-request-v1` は `runtime/schema/docs` の 3 coverage だけを actual builder handoff / worker dispatch / TaskGraph binding に載せ、`eval` は optional review coverage に留める
- `council_convocation_session` と `yaoyorozu_worker_dispatch_plan` / `receipt` は
  required/optional builder coverage を first-class field として保持し、
  profile policy mismatch を validation で fail-closed にする
- `TaskGraph` は fixed `max_parallelism=3` を維持したまま、
  `memory-edit-v1` と `fork-request-v1` を
  required coverage 1 surface = 1 root node の 3 root strategy へ単純化する
- follow-up closure として optional coverage の requested dispatch path を追加し、
  repo-local runtime では `memory-edit-v1` の `schema` と
  `fork-request-v1` の `eval` を deterministic な on-demand dispatch へ昇格できるようにする
- 次段の frontier は remote worker runtime / brokered sandbox へ
  同じ policy を持ち込むかに縮小する

## Revisit triggers

- `memory-edit-v1` でも schema migration や schema validation を
  mandatory runtime step に戻したくなった時
- `fork-request-v1` で eval evidence を legal / ethics gate の必須条件へ上げたくなった時
- same-host repo-local subprocess を超えて remote scheduler / brokered sandbox でも
  同じ profile-aware dispatch policy を再利用したくなった時
