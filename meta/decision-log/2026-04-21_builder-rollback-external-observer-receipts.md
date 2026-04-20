---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.rollback.v0.idl
  - specs/schemas/builder_rollback_session.schema
  - evals/continuity/builder_rollback_execution.yaml
status: decided
---

# Decision: builder rollback に repo-root external observer receipt を追加する

## Context

2026-04-21 時点で `rollback-demo` は、temp rollback workspace 上の actual reverse-apply command、
repo-bound verification、detached git worktree 上の checkout-bound mutation receipt までは
machine-checkable でした。

一方で、rollback が repo root から見て本当に baseline へ戻ったかを、
mutation 実行主体とは別の観測面で確かめる receipt はありませんでした。
そのため、detached worktree 内の status/diff が一致していても、
repo-root から見た worktree membership や stash visibility まで approval 条件へ束縛できていませんでした。

## Options considered

- A: detached worktree receipt だけを維持し、repo-root external observer は future work に残す
- B: current checkout そのものを直接 mutate し、live repo で observer receipt を取る
- C: detached worktree rollback は維持しつつ、repo-root `git worktree list --porcelain` / `git stash list` を external observer receipt として追加する

## Decision

Option C を採択します。

`RollbackEngineService` は既存の detached worktree rollback を保ったまま、
repo root から取得する external observer receipt を追加します。
observer は `repo-root-git-observer-v1` profile とし、baseline / mutated / restored の
`git worktree list --porcelain` と baseline / restored の `git stash list` を記録します。

approval 条件には次を含めます。

- detached worktree の rollback mutation が baseline へ戻ること
- external observer が detached worktree mutation を検出すること
- external observer の restored worktree view が baseline と一致すること
- external observer の stash view が baseline と一致すること

## Consequences

- `builder_rollback_session` は repo-root 観測面を持つようになり、
  rollback approval が repo 内から見てより reviewer-facing になります
- future work は broad な external observer 一般論ではなく、
  current-worktree direct rollback mutation や reviewer/verifier network 連携へ縮小されます
- raw git output は digest/excerpt に留め、bounded receipt で machine-checkable を維持します

## Revisit triggers

- rollback を detached worktree ではなく current checkout 自体へ apply したくなった時
- external observer を `git worktree` / `git stash` 以外の repo telemetry へ広げたくなった時
- rollback telemetry を reviewer / verifier network へ送達したくなった時
