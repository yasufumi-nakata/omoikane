---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.rollback.v0.idl
  - specs/schemas/builder_rollback_session.schema
status: decided
---

# Decision: builder rollback に current-worktree direct mutation receipt を追加する

## Context

2026-04-21 時点で `RollbackEngineService` は、
temp rollback workspace での actual reverse-apply command、
repo-bound verification、
detached git worktree 上の checkout-bound mutation receipt、
repo-root external observer receipt までは machine-checkable でした。

一方で、**actual current checkout そのもの** を mutate したうえで
baseline status/diff へ戻した証跡は contract の外に残っていました。
`specs/schemas/README.md` でも
`current-worktree direct rollback mutation` が residual gap として残っており、
rollback surface の次段として最も具体的でした。

## Options considered

- A: detached worktree / observer receipt だけを維持し、current checkout direct mutation は future work に残す
- B: actual current checkout の対象 path を bounded に mutate し、baseline snapshot から restore する direct receipt を追加する
- C: current checkout 全体への広域 rollback apply や external verifier network まで同時に拡張する

## Decision

Option B を採択します。

`RollbackEngineService` は既存の detached worktree rollback を保ったまま、
`current-worktree-direct-restore-v1` receipt を追加します。
receipt は次を必須にします。

- current checkout の対象 path ごとの baseline snapshot
- baseline / mutated / restored の `git status` / `git diff` digest
- actual current checkout 上で実行した restore command receipt
- restore 後に baseline digest へ戻ったこと
- snapshot cleanup 完了

telemetry gate は detached worktree receipt と external observer receipt に加え、
この current-worktree direct receipt も approval 条件に含めます。

## Consequences

- rollback contract は temp workspace / detached worktree だけでなく、
  actual current checkout の bounded mutation まで machine-checkable になります
- `builder_rollback_session.schema` と `selfctor.rollback.v0` は
  direct current-worktree restore を first-class field / guarantee として持ちます
- `specs/schemas/README.md` の residual gap は
  `cross-host authority routing + OS-native packet capture` へ縮小されます
- current checkout mutation は path-scoped snapshot/restore に限定し、
  baseline dirty state 自体は preserve する方針になります

## Revisit triggers

- rollback を path-scoped ではなく current checkout 全体へ apply したくなった時
- rollback telemetry を reviewer / verifier network へ送達したくなった時
- rollback receipt に staged / index / submodule 状態まで束縛したくなった時
