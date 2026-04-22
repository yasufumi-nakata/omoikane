---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_motor_plan.schema
  - specs/schemas/ewa_legal_execution.schema
  - evals/safety/ewa_motor_semantics_legal_execution.yaml
status: decided
---

# Decision: EWA authorization の前段に motor semantics と legal preflight を固定する

## Context

`gap-report --json` は residual future work として
`interface.ewa.v0` に
`Device-specific motor semantics and full jurisdiction-specific legal compliance execution remain future work.`
を返していました。

2026-04-21 時点の EWA は
authorization artifact、emergency stop、digest-only audit までは
machine-checkable でしたが、

- 実 actuator がどの motion envelope / rollback vector / safe-stop policy で動くのか
- jurisdiction bundle が実際にどの preflight control を通過して authorization へ進んだのか

が repo 内 contract に残っていませんでした。

その結果、authorization は legal basis ref と guardian verification ref を持てても、
device-specific semantics と legal execution controls が
current runtime から抜けたままでした。

## Options considered

- A: existing authorization artifact を維持し、motor semantics / legal execution は repo 外のまま据え置く
- B: `ewa_motor_plan` と `ewa_legal_execution` を追加し、authorization / command audit へ binding する
- C: 実 robot firmware bus や regulator API まで一気に接続する

## Decision

**B** を採択。

## Consequences

- `ewa_motor_plan.schema` を追加し、
  `device-specific-motor-semantics-v1` を
  EWA v0 の canonical motor semantics profile とする
- `ewa_legal_execution.schema` を追加し、
  `ewa-jurisdiction-legal-execution-v1` を
  fixed 5-control
  (`bundle-ready-check`, `legal-basis-bind`, `guardian-review-bind`,
  `notice-authority-bind`, `escalation-contact-bind`)
  preflight として固定する
- `authorize` は `motor_plan_id/digest` と `legal_execution_id/digest` を
  fail-closed で要求し、
  `command-approved` audit も同じ receipt を carry する
- `ewa-demo` は
  `motor plan -> legal preflight -> authorization -> command -> emergency stop -> release`
  を 1 シナリオで示せるようになる
- `interface.ewa.v0` の residual future work から
  device-specific motor semantics と jurisdiction-bound legal preflight を外せる

## Revisit triggers

- 実 robot firmware bus や kill-switch wiring へ接続したくなった時
- jurisdiction preflight を actual permit / filing API と同期したくなった時
- EWA legal execution を Guardian reviewer verifier network や distributed authority plane と共通化したくなった時
