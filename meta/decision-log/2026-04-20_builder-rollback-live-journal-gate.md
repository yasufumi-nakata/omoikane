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

# Decision: builder rollback を live enactment journal / telemetry gate に束縛する

## Context

2026-04-20 時点で `rollback-demo` は
pre-apply snapshot 復元と stakeholder notify までは machine-checkable でしたが、
README future work に残っていた
`actual reverse-apply journal` と `live telemetry gate` は未接続でした。

そのため、`builder-live-demo` が実際に temp workspace で command を完走していても、
rollback 側では「どの materialized file をどう戻すか」と
「cleanup 済み receipt を根拠に rollback を許可したか」が
明示的に残りませんでした。

## Options considered

- A: rollback は snapshot 復元と notify のみで維持し、live receipt 連携は future work に残す
- B: rollback が live enactment receipt を受け取り、reverse-apply journal と telemetry gate を必須にする
- C: real filesystem reverse-apply までこの run で入れる

## Decision

- B を採択しました
- `selfctor.rollback.v0` / `builder_rollback_session.schema` を拡張し、
  `live_enactment_session_id`、`reverse_apply_journal`、`telemetry_gate` を追加します
- `rollback-demo` は `builder_live_enactment_execution.yaml` を先に通し、
  materialized file ごとの reverse action と cleanup / command receipt を束ねた
  telemetry gate が `rollback-approved` の時だけ `rolled-back` になります

## Consequences

- builder rollback は snapshot-only ではなく、
  temp workspace enactment の実行痕跡まで machine-checkable に結び付きます
- README future work から `builder rollback の actual reverse-apply journal と live telemetry gate 連携`
  を外せます
- ただし real repo への reverse-apply や external reviewer network 連携は
  引き続き future work です

## Revisit triggers

- rollback journal を actual patch reverse-apply command まで昇格したくなった時
- telemetry gate を live traffic / external observer へ接続したくなった時
- rollback notification を remote verifier network へ束縛したくなった時
