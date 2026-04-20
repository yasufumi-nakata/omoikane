---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: builder rollback を actual reverse-apply command まで昇格する

## Context

2026-04-20 時点で `rollback-demo` は
pre-apply snapshot 復元、reverse-apply journal、telemetry gate までは
machine-checkable でしたが、
journal 自体は metadata 中心で、
rollback 側が temp workspace 上で実際に reverse command を走らせた証跡は
残っていませんでした。

そのため `builder-live-demo` が actual eval command を実行していても、
rollback は「戻すべき file 一覧」を記録するだけで、
restore/delete が成功したかを同じ contract で閉じ切れていませんでした。

## Options considered

- A: rollback は journal metadata と live telemetry gate のみ維持し、actual reverse command は future work に残す
- B: rollback が temp rollback workspace を持ち、file ごとの actual reverse-apply command receipt を journal に束ねる
- C: temp workspace を飛ばして live repo 自体へ reverse-apply する

## Decision

- B を採択しました
- `builder_rollback_session.schema` と `selfctor.rollback.v0` を拡張し、
  journal entry ごとに `command` / `exit_code` / `status` / `stdout_excerpt` /
  `stderr_excerpt` / `result_state` を必須化します
- telemetry gate は live enactment cleanup だけでなく、
  reverse workspace cleanup、reverse command pass 数、verified result 数も
  approval 条件に含めます
- `rollback-demo` は temp rollback workspace で copied file の restore、
  created file の delete を実行し、verification 済み receipt を返します

## Consequences

- L5 rollback は snapshot-only の再現ではなく、
  actual reverse-apply execution まで含む contract になりました
- `builder-live-demo` の actual command receipt と
  `rollback-demo` の actual reverse command receipt が同じ bounded pipeline に揃います
- residual future work は live repo への reverse-apply や
  external observer / verifier network への rollback telemetry 連携へ縮小されます

## Revisit triggers

- rollback を temp workspace ではなく live repo へ apply したくなった時
- external reviewer / verifier network へ rollback telemetry を束縛したくなった時
- patch descriptor 単位ではなく diff hunk 単位の reverse-apply へ細分化したくなった時
