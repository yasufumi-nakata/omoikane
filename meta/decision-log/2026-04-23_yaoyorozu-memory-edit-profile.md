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
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_workspace_discovery.schema
  - evals/agentic/yaoyorozu_memory_edit_profile.yaml
status: decided
---

# Decision: Yaoyorozu proposal profile catalog を `memory-edit-v1` まで昇格する

## Context

2026-04-23 時点の `agentic.yaoyorozu.v0` は
Council convocation / worker dispatch / ConsensusBus / TaskGraph まで
machine-checkable でしたが、
proposal profile は `self-modify-patch-v1` に固定されていました。

一方で repo には `mind.memory_edit.v0` と `memory-edit-demo`、
関連する schema / eval / docs が既に存在し、
memory-edit 系の案件を Yaoyorozu の convocation catalog へ昇格する下地は揃っていました。
この状態では reviewer-facing に
「Memory Edit Request をどの bounded panel / builder handoff で扱うか」を
repo 内で確認できませんでした。

## Options considered

- A: Yaoyorozu は `self-modify-patch-v1` 固定のまま維持し、memory-edit 案件は docs 説明に留める
- B: bounded profile catalog を 2 本目まで広げ、`memory-edit-v1` を convocation / dispatch / CLI demo で machine-checkable にする
- C: open-ended profile system を一気に作り、role catalog / bundle strategy / builder coverage を完全に一般化する

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `self-modify-patch-v1` に加えて `memory-edit-v1` を public input として受け付ける
- `memory-edit-v1` は `MemoryArchivist` / `DesignAuditor` /
  `ConservatismAdvocate` / `EthicsCommittee` を panel に固定しつつ、
  builder handoff coverage は runtime / schema / eval / docs の 4 本を維持する
- `yaoyorozu-demo --proposal-profile memory-edit-v1 --json` で
  reversible memory-edit 向け convocation / dispatch chain を直接確認できる
- residual gap は generic な single-profile 固定ではなく、
  fork request や inter-mind negotiation など別 proposal profile の catalog 拡張へ縮小する

## Revisit triggers

- `fork-request-v1` や `inter-mind-negotiation-v1` を同じ bounded catalog に追加したくなった時
- proposal profile ごとに TaskGraph bundle grouping や required coverage area を分岐させたくなった時
- repo-local subprocess を超えて remote worker runtime / remote sandbox cluster へ audited dispatch したくなった時
