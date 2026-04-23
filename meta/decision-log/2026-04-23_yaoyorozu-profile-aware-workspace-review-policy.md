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
  - specs/schemas/council_convocation_session.schema
  - evals/agentic/yaoyorozu_workspace_discovery.yaml
  - evals/agentic/yaoyorozu_memory_edit_profile.yaml
  - evals/agentic/yaoyorozu_fork_request_profile.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-profile-aware-task-graph-bundles.md#yaoyorozu.profile.workspace-policy
next_gap_ids:
  - yaoyorozu.profile.dispatch-coverage
---

# Decision: Yaoyorozu workspace review を proposal-profile-aware policy へ昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
Council panel、local worker dispatch、ConsensusBus binding、
proposal-profile-aware TaskGraph bundle strategy までは
machine-checkable でした。

一方で workspace discovery 側は
`review_budget=3` と `runtime/schema/eval/docs` の full coverage を
全 proposal profile 共通の固定値として扱っており、
`memory-edit-v1` や `fork-request-v1` の review emphasis が
cross-workspace candidate selection には反映されていませんでした。

この状態では profile-aware なのが Council panel と TaskGraph bundle だけになり、
review budget / required cross-workspace coverage が
public contract として一段手前の discovery / convocation artifact へ
落ちていませんでした。

## Options considered

- A: current fixed `review_budget=3` / full four-surface coverage を維持し、profile 差分は panel と TaskGraph に留める
- B: proposal profile ごとに workspace review budget と required cross-workspace coverage を固定し、`workspace_discovery` と `convocation` に束縛する
- C: proposal profile ごとの workspace policy を導入せず、次段の `inter-mind-negotiation-v1` 追加まで保留する

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_workspace_discovery` は
  `proposal_profile` と `profile_policy` を first-class field として持つ
- reference runtime は
  `self-modify-patch-v1` を `review_budget=3` / `runtime+schema+eval+docs` required、
  `memory-edit-v1` を `review_budget=2` / `runtime+eval+docs` required + `schema` optional、
  `fork-request-v1` を `review_budget=3` / `runtime+schema+docs` required + `eval` optional
  に固定する
- accepted candidate workspace は fixed review budget 内で deterministic に選ばれ、
  `memory-edit-v1` では single candidate でも required coverage を満たせる
- `council_convocation_session` は `workspace_discovery_binding` を持ち、
  selected profile の review budget / required coverage / accepted workspace set を
  same-session Council artifact に束縛する
- `yaoyorozu-demo`、schema contract、CLI integration、profile eval が
  proposal profile ごとの workspace policy 差分を継続検証する
- residual gap は generic な profile unawareness ではなく、
  `review_budget` の further dynamic tuning や
  `inter-mind-negotiation-v1` のような次段 profile catalog 拡張へ縮小する

## Revisit triggers

- proposal profile ごとに optional coverage area ではなく
  actual builder dispatch coverage 自体を減らしたくなった時
- same-host local workspace を超えて
  remote scheduler / brokered sandbox にも同じ profile-aware review policy を持ち込みたくなった時
- `review_budget` を fixed integer ではなく
  trust / legal / ethics severity から導出する bounded policy へ上げたくなった時
