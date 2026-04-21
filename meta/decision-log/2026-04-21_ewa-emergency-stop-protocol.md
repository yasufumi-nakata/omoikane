---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/02-subsystems/interface/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_emergency_stop.schema
  - evals/safety/ewa_emergency_stop.yaml
status: decided
---

# Decision: EWA に latched emergency stop protocol を追加する

## Context

`external_actuation_authorization` artifact により
non-read-only command の digest-bound authorization は固定できましたが、
docs にはなお **「物理世界での緊急停止プロトコル」** が未解決として残っていました。

既存 `release` は work completion や timeout 後の handle close を表現できても、
実 actuator を **即時 safe state へ遷移させた事実** と、
その停止がどの command / authorization に束縛されていたかを
machine-readable に残せていませんでした。

## Options considered

- A: `release(reason=emergency-stop)` のみで済ませ、latched stop receipt は future work に残す
- B: `ewa_emergency_stop` receipt と `emergency_stop` op を追加し、safe-state interlock と forced release を repo 内で固定する
- C: device-specific motor kill-switch wiring や regulator API まで一気に実装する

## Decision

**B** を採択。

## Consequences

- `interface.ewa.v0` に `emergency_stop / validate_emergency_stop` を追加し、
  `guardian-latched-emergency-stop-v1` を canonical policy とする
- `ewa_emergency_stop.schema` は
  `command_id` / `bound_command_digest` / `authorization_id` /
  `bound_authorization_digest` / `safe_state_ref` /
  `hardware_interlock_state=engaged` / `release_required=true`
  を必須化する
- `ewa-demo` は authorized reversible actuation の後に
  `watchdog-timeout` 起因の latched stop を返し、その後 forced release まで実行する
- residual future work は generic な emergency stop 不在ではなく、
  device-specific kill-switch wiring と法域別 hardware execution へ縮小される

## Revisit triggers

- 実デバイス固有の kill-switch wiring や watchdog bus へ接続したくなった時
- emergency stop を Guardian 手動停止だけでなく multi-controller arbitration に広げたくなった時
- latched stop receipt を distributed transport / verifier network と共通化したくなった時
