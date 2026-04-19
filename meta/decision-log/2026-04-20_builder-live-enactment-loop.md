---
date: 2026-04-20
deciders: [yasufumi, claude-council, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: builder live workspace enactment を reference runtime 化する

## Context

2026-04-20 時点の L5 self-construction は
`builder-demo` と `rollback-demo` により
descriptor / staged rollout / rollback contract までは machine-checkable でしたが、
README future-work に残っていた
`live workspace mutation hook` と `real eval runner` は未接続でした。

その結果、`SandboxApplyService` は `mirage://...` ref を返すだけで
実 temp workspace を materialize せず、
`DifferentialEvaluatorService` も actual command 実行ではなく
synthetic outcome 判定に留まっていました。

## Options considered

- A: builder-demo / rollback-demo のみ維持し、live enactment は future work のまま残す
- B: temp workspace materialization と actual eval command execution を bounded receipt として追加する
- C: そのまま live repo mutation や real patch reverse-apply まで入れる

## Decision

- B を採択しました
- `LiveEnactmentService` と
  `selfctor.enactment.v0` / `builder_live_enactment_session.schema` /
  `builder_live_enactment_execution.yaml` / `builder-live-demo` を追加します
- live enactment は temp workspace に限定し、
  `PatchGeneratorService` が選んだ target file のみを materialize して
  eval YAML の command を実際に実行します
- temp workspace は run 終了時に必ず cleanup し、
  immutable boundary は引き続き write scope の外へ固定します

## Consequences

- L5 builder pipeline に `spec -> temp workspace mutation -> actual command receipt`
  という一段深い execution loop が加わり、
  hidden future-work gap を repo 内で閉じられます
- hourly builder は synthetic smoke だけでなく、
  real command 実行の receipt を次回以降の rollback / telemetry 拡張へ再利用できます
- ただし real patch reverse-apply、live traffic telemetry gate、
  external verifier network 連携は引き続き future work です

## Revisit triggers

- rollback 側で actual reverse-apply journal を導入したくなった時
- staged rollout を live telemetry gate と結合したくなった時
- reviewer / verifier network を actual transport に接続したくなった時
