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

# Decision: builder rollback を repo-bound verification まで固定する

## Context

2026-04-21 時点で `rollback-demo` は
temp rollback workspace 上の actual reverse-apply command と
reverse-apply journal までは machine-checkable でしたが、
その結果が **current checkout の baseline と一致したか** は
journal 外の暗黙前提に留まっていました。

そのため、rollback が「戻した」と主張していても、
repo 起点の source digest や verification command receipt を
同じ contract の中で追跡できませんでした。

## Options considered

- A: temp rollback workspace での restore / delete だけを維持し、repo baseline との照合は future work に残す
- B: rollback journal に repo binding ref / source digest / verification command receipt を追加し、current checkout baseline との一致を approval 条件に含める
- C: temp workspace をやめて live checkout 自体へ直接 reverse-apply する

## Decision

- B を採択しました
- `builder_rollback_session.schema` と `selfctor.rollback.v0` を拡張し、
  journal entry ごとに `repo_binding_ref` / `repo_source_digest` /
  `verification_command` / `verification_status` を必須化します
- telemetry gate は reverse command pass 数だけでなく、
  repo-bound verification pass 数も `rollback-approved` の条件に含めます
- top-level `repo_binding_summary` で current checkout subtree に対する
  bound path 数・verified path 数・binding digest を固定します

## Consequences

- rollback は temp workspace 内の復元だけでなく、
  current checkout baseline への整合まで machine-checkable になります
- `specs/schemas/README.md` の residual gap は
  generic な `live-repo reverse-apply` から
  より狭い `in-place checkout rollback mutation` へ縮小されます
- ただし actual checkout そのものを mutate する rollback や
  git worktree / external observer との統合は引き続き future work です

## Revisit triggers

- rollback を temp workspace ではなく actual checkout へ apply したくなった時
- git status / diff / worktree metadata まで approval 条件に束ねたくなった時
- external reviewer / verifier network へ rollback telemetry を接続したくなった時
