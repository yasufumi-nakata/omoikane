---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_stop_signal_path.schema
  - specs/schemas/external_actuation_authorization.schema
  - specs/schemas/ewa_emergency_stop.schema
  - evals/safety/ewa_stop_signal_path_guard.yaml
  - evals/safety/ewa_emergency_stop.yaml
status: decided
---

# Decision: EWA の hardware kill-switch wiring を armed stop-signal path として固定する

## Context

2026-04-22 時点で EWA は
device-specific motor semantics、jurisdiction-bound legal preflight、
authorization artifact、latched emergency stop までは machine-checkable でした。

一方で `docs/02-subsystems/interface/ewa-safety.md` の未解決には
`実デバイス固有の hardware kill-switch 配線と stop signal bus`
が残っており、
authorization 前に「どの wiring / signal path / relay が
safe-stop を担うか」を repo 内 artifact に束縛できていませんでした。

この状態では `ewa_emergency_stop` が `hardware_interlock_state=engaged`
を返しても、
どの armed path が実際に latch したのかを current runtime contract で
追跡できません。

## Options considered

- A: 現状の emergency stop receipt を維持し、kill-switch wiring は docs の未解決として残す
- B: authorization 前に armed stop-signal path receipt を materialize し、authorization / command audit / emergency stop を同じ digest に束縛する
- C: 実 PLC / firmware adapter と raw bus transcript まで同時に repo へ保存する

## Decision

Option B を採択します。

- `ewa_stop_signal_path.schema` を追加し、
  `guardian-latched-stop-signal-bus-v1` /
  `bounded-hardware-kill-switch-bus-v1` を canonical profile に固定します
- `prepare_stop_signal_path` は
  `guardian-manual-stop` / `watchdog-timeout` / `sensor-drift` /
  `emergency-disconnect`
  の 4 trigger を armed binding として materialize し、
  `kill_switch_wiring_ref` / `stop_signal_bus_ref` /
  `interlock_controller_ref` を digest-bound に保持します
- `authorize` は matching `motor_plan` / `stop_signal_path` /
  `legal_execution` receipt が揃わない限り fail-closed に進めません
- `command-approved` audit と `ewa_emergency_stop` は
  `stop_signal_path_id` / digest と
  activated binding/channel/path/interlock を carry します

## Consequences

- `ewa-demo` は
  `motor plan -> stop-signal path arming -> legal preflight -> authorization ->
  reversible command -> watchdog emergency stop -> forced release`
  を 1 シナリオで JSON へ可視化できます
- `ewa_emergency_stop` の `hardware_interlock_state=engaged` が
  abstract flag ではなく、
  armed path 上の activated binding と結び付いた receipt になります
- docs の未解決から broad な `hardware kill-switch wiring / stop signal bus`
  を外し、残課題は実 PLC / firmware adapter や regulator API 接続へ縮小できます

## Revisit triggers

- actual PLC / firmware adapter から stop-signal bus state を live 取得したくなった時
- hardware interlock を site-specific redundancy topology や fieldbus へ拡張したくなった時
- EWA emergency stop を distributed authority plane や external verifier network と共通 observability plane に束縛したくなった時
