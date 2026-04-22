---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/schemas/staged_rollout_session.schema
  - specs/schemas/builder_live_enactment_session.schema
  - specs/schemas/builder_rollback_session.schema
  - specs/schemas/guardian_oversight_event.schema
  - tests/integration/test_builder_schema_contracts.py
status: decided
---

# Decision: builder 系 demo の public schema を runtime 実出力へ再同期する

## Context

2026-04-22 時点の builder 系 runtime は、
`builder-demo` / `builder-live-demo` / `rollback-demo` の JSON surface 自体は
整っていましたが、public schema がその current output shape に追随できていませんでした。

確認した drift は 3 件です。

- `builder_rollback_session.schema` が `max_reverted_patch_count=4` を要求し、
  runtime policy (`RollbackEnginePolicy`) と demo 出力の `5` を拒否する
- `builder_live_enactment_session.schema` が
  `guardian_oversight_event` を古い narrow shape で内包し、
  canonical `guardian_oversight_event.schema` に含まれる
  `schema_version` / `event_id` / `recorded_at` / richer reviewer binding を reject する
- `staged_rollout_session.schema` が `executed_stage` を
  `allOf + additionalProperties: false` で閉じており、
  runtime が返す `status` / `guardian_gate` / `rollback_ref` を Draft 2020-12 上で拒否する

この状態では `gap-report --json` が clean でも、
builder 系 contract の machine-checkable closure は壊れたままでした。

## Options considered

- A: runtime を public schema の古い shape へ縮退させる
- B: public schema を canonical runtime output に再同期し、schema validation test を常設する
- C: schema validation 自体を行わず、happy-path smoke test のみ維持する

## Decision

Option B を採択します。

- `builder_rollback_session.schema` は
  rollback policy の canonical value と同じ `max_reverted_patch_count=5` に揃えます
- `builder_live_enactment_session.schema` は
  narrow な inline object を廃止し、
  canonical `guardian_oversight_event.schema` を直接参照します
- `staged_rollout_session.schema` は
  `executed_stage` を flat object として再定義し、
  current runtime output を Draft 2020-12 でそのまま受理できる形へ直します
- integration test は
  `builder-demo` / `builder-live-demo` / `rollback-demo` の実 payload を
  public schema に対して直接 validate します

## Consequences

- builder 系 demo の public schema が reviewer-facing JSON と再び一致します
- runtime の richer oversight binding や rollback policy を
  schema 側が fail-open / fail-closed どちらにも歪めず表現できます
- 今後の builder surface 拡張でも、
  happy-path assertion だけでは見逃す schema drift を regression test で止められます

## Revisit triggers

- builder public schema validation を CLI smoke だけでなく eval runner へ昇格したくなった時
- `guardian_oversight_event` の canonical shape をさらに広げる時
- staged rollout session に stage-level external witness を追加したくなった時
