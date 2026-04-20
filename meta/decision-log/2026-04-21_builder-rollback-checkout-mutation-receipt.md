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

# Decision: builder rollback に checkout-bound mutation receipt を追加する

## Context

2026-04-21 時点で `rollback-demo` は
temp rollback workspace 上の actual reverse-apply command、
repo-bound verification、telemetry gate までは machine-checkable でしたが、
**git metadata を持つ checkout 形状そのもの** が rollback 前後でどう変化したかは
contract の外に残っていました。

そのため、current checkout が dirty でも成立する rollback か、
`git status` / `git diff` の観点で baseline に戻ったかを
同じ receipt から追えませんでした。

## Options considered

- A: temp rollback workspace と repo-bound verification のみを維持し、checkout mutation は future work に残す
- B: current worktree を直接 mutate し、rollback 後の `git status` / `git diff` を approval 条件に含める
- C: detached git worktree を一時生成し、current checkout の対象 path を overlay したうえで mutation -> reverse-apply -> baseline digest 復元を receipt 化する

## Decision

- C を採択しました
- `RollbackEngineService` は temp rollback workspace に加えて、
  `detached-git-worktree-overlay-v1` で checkout-bound mutation を再現します
- `builder_rollback_session.schema` に `checkout_mutation_receipt` を追加し、
  `git status` / `git diff` の baseline / mutated / restored digest、
  path ごとの reverse command receipt、cleanup status を必須化します
- telemetry gate は reverse journal と repo-bound verification に加えて、
  checkout 状態が baseline へ戻ったことも `rollback-approved` の条件に含めます

## Consequences

- rollback は temp workspace だけでなく、
  git metadata を持つ checkout 形状でも baseline 復元まで machine-checkable になります
- current checkout が clean でなくても、
  overlay した baseline digest を restore target にできるため dirty 状態の drift を吸収できます
- `specs/schemas/README.md` の residual gap は
  broad な `in-place checkout rollback mutation` から
  より狭い `current-worktree direct rollback mutation / external observer receipts` に縮小されます
- ただし actual current worktree 自体への direct rollback apply と
  external observer / verifier network receipt は引き続き future work です

## Revisit triggers

- rollback を detached worktree ではなく current worktree 自体へ apply したくなった時
- `git status` / `git diff` に加えて `git worktree` / `git stash` / external observer metadata も approval 条件に束ねたくなった時
- rollback telemetry を reviewer / verifier network へ外部送達したくなった時
