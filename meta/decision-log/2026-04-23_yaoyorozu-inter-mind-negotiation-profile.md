---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/council-composition.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/council_convocation_session.schema
  - specs/schemas/yaoyorozu_workspace_discovery.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - specs/schemas/yaoyorozu_task_graph_binding.schema
  - evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml
status: decided
---

# Decision: Yaoyorozu proposal catalog に `inter-mind-negotiation-v1` を追加する

## Context

2026-04-23 時点の `agentic.yaoyorozu.v0` は
`self-modify-patch-v1` / `memory-edit-v1` / `fork-request-v1` までを
proposal-profile-aware に materialize できていました。
一方で recent decision log の residual gap は、
bounded catalog を次段の `inter-mind-negotiation-v1` へ拡張できる状態まで
縮小していました。

このままでは disclosure / merge / collective contract の review を
fork-request と同じ generic governance lane へ押し込み続けることになり、
legal / ethics / schema-sync / docs-sync を同時に要求する
inter-mind 固有の execution policy を repo 内で machine-checkable に監査できません。

## Options considered

- A: 既存 3 profile を維持し、inter-mind negotiation は future work に残す
- B: `inter-mind-negotiation-v1` を bounded catalog に追加し、workspace review / convocation / dispatch / TaskGraph を full four-surface contract として固定する
- C: repo-local profile 追加を飛ばして remote worker runtime / brokered sandbox 前提の negotiation lane へ進む

## Decision

**B** を採択。

## Consequences

- `inter-mind-negotiation-v1` は `review_budget=3` /
  `runtime+schema+eval+docs` required / optional なしの profile として固定する
- Council panel は `LegalScholar` / `DesignAuditor` /
  `ConservatismAdvocate` / `EthicsCommittee` を用いる
- actual builder dispatch は 4 coverage 全件を materialize し、
  `TaskGraph` では `runtime` / `contract-sync(schema+docs)` / `eval`
  の 3 root bundle strategy に畳み込む
- `yaoyorozu-demo --proposal-profile inter-mind-negotiation-v1 --json`、
  schema contract test、CLI/runtime integration test、
  `evals/agentic/yaoyorozu_inter_mind_negotiation_profile.yaml` が
 同じ policy を継続検証する
- residual gap は generic な profile catalog 不足ではなく、
  `fork-request-v2` や `inter-mind-negotiation-v2`、
  remote scheduler / brokered sandbox への profile carryover へ縮小する

## Revisit triggers

- inter-mind negotiation でも optional coverage を on-demand dispatch したくなった時
- collective / IMC negotiation が four-surface review を超える fourth/fifth bundle を要求した時
- repo-local subprocess を超えて remote worker runtime へ同じ profile policy を移植したくなった時
