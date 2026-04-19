---
date: 2026-04-20
deciders: [yasufumi, claude-council, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: builder staged rollout の rollback execution を reference runtime 化する

## Context

2026-04-20 時点の L5 self-construction は
`builder-demo` により `build_request -> sandbox apply -> staged rollout`
までは machine-checkable でしたが、
`RollbackEngine` は docs 上の主要モジュールである一方、
runtime / schema / IDL / CLI / eval / tests に surface がありませんでした。

この状態では `完全可逆` と書いていても、
regression 検出後に何を復元し、どこまで revoke し、
誰へ通知するかが deterministic になっていませんでした。

## Options considered

- A: rollback は `rollback_ref` だけ残し、実行面は future work に据え置く
- B: `RollbackEngineService` と `builder_rollback_session` を追加し、pre-apply snapshot restore を reference runtime で固定する
- C: 実 filesystem mutation と live eval runner を巻き込む full rollback enactment まで入れる

## Decision

- B を採択しました
- `selfctor.rollback.v0` / `builder_rollback_session.schema` / `rollback-demo` を追加します
- rollback は `eval-regression` / `guardian-veto` / `manual-review` trigger を受け、
  pre-apply Mirage Self snapshot の復元、append-only continuity evidence 2 本、
  self / council / guardian 3 者通知を必須にします
- staged rollout の rollback path は `dark-launch` 完了後に
  `canary-5pct` で rollback し、残り stage は blocked に固定します

## Consequences

- L5 `RollbackEngine` が docs/specs/runtime/CLI/eval/tests まで materialize され、
  self-construction の `完全可逆` が reference runtime でも machine-checkable になります
- hourly builder は `rollback-ready` 参照だけでなく、
  rollback 実行そのものを次回以降の surface として再利用できます
- ただし live workspace mutation と実際の patch reverse-apply は依然 future work です

## Revisit triggers

- sandbox 上で real patch reverse-apply を再現したくなった時
- rollback notification を external reviewer network へ接続したくなった時
- staged rollout revoke を telemetry gate と結合したくなった時
