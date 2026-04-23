---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/02-subsystems/kernel/README.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/interfaces/kernel.identity.v0.idl
  - specs/schemas/council_convocation_session.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - evals/agentic/yaoyorozu_fork_request_profile.yaml
status: decided
closes_next_gaps:
  - 2026-04-23_yaoyorozu-memory-edit-profile.md#yaoyorozu.catalog.additional-profiles
next_gap_ids:
  - yaoyorozu.catalog.inter-mind-negotiation
---

# Decision: Yaoyorozu proposal profile catalog を `fork-request-v1` まで昇格する

## Context

2026-04-23 時点の `agentic.yaoyorozu.v0` は
`self-modify-patch-v1` と `memory-edit-v1` までは machine-checkable でしたが、
最新の decision log では residual gap が
fork request や inter-mind negotiation のような別 proposal profile へ縮小していました。

一方で repo には `kernel.identity.v0` の fork triple-approval contract、
fork approval を強制する ethics rule、
`IdentityGuardian` / `LegalScholar` / `EthicsCommittee` を含む roster が既に存在します。
この状態では reviewer-facing に
「fork request をどの bounded panel / builder handoff で扱うか」を
repo 内で確認できませんでした。

## Options considered

- A: Yaoyorozu は 2 profile のまま維持し、fork request は docs 説明に留める
- B: bounded profile catalog を 3 本目まで広げ、`fork-request-v1` を convocation / dispatch / CLI demo で machine-checkable にする
- C: open-ended profile system を一気に作り、role catalog / bundle strategy / builder coverage を完全に一般化する

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `fork-request-v1` を public input として受け付ける
- `fork-request-v1` は `IdentityProtector` / `LegalScholar` /
  `ConservatismAdvocate` / `EthicsCommittee` を panel に固定しつつ、
  builder handoff coverage は runtime / schema / eval / docs の 4 本を維持する
- `yaoyorozu-demo --proposal-profile fork-request-v1 --json` で
  identity fork の triple-approval review 向け convocation / dispatch chain を直接確認できる
- residual gap は generic な fork request 不在ではなく、
  `inter-mind-negotiation-v1` のような別 profile catalog や
  profile ごとの bundle strategy 分岐へ縮小する

## Revisit triggers

- `inter-mind-negotiation-v1` や `fork-request-v2` を同じ bounded catalog に追加したくなった時
- proposal profile ごとに TaskGraph bundle grouping や required coverage area を分岐させたくなった時
- repo-local subprocess を超えて remote worker runtime / remote sandbox cluster へ audited dispatch したくなった時
