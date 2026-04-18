---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/README.md
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - evals/safety/ewa_irreversible_veto.yaml
status: decided
---

# Decision: EWA の physical safety gate を reference runtime に固定する

## Context

`gap-report --json` は clean でしたが、reference runtime README には
「残る L6 interface protocol（EWA）の adapter」が残っていました。
特に EWA は docs に reversibility ごとの承認経路、blocked token、forced release が
明示されている一方で、runtime / CLI / eval / tests / machine-readable schema がなく、
物理 actuation の fail-closed 境界がコードで検証されていませんでした。

## Options considered

- A: EWA は docs-only のまま維持し、物理 actuation は future work へ残す
- B: acquire / command / observe / release に限定した bounded safety gate を追加し、
  reversibility ごとの approval path と blocked token veto を固定する
- C: device driver 実装、法域別 compliance、緊急停止 hardware protocol まで v0 に含める

## Decision

**B** を採択。

## Consequences

- `interface.ewa.v0`、`ewa_command.schema`、`ewa_audit.schema` を追加し、
  digest-only audit と handle lifecycle を機械可読化する
- `ewa-demo` を追加し、reversible command の実行、irreversible blocked command の veto、
  observe、forced release をまとめて確認する
- EthicsEnforcer に blocked token veto と ambiguous intent escalation を追加し、
  physical-world command を fail-closed に固定する
- device-specific motor semantics、jurisdiction-specific legal compliance、
  hardware emergency stop protocol は future work に残す

## Revisit triggers

- 実機 actuator ごとに torque / blast radius / human proximity を model 化したくなった時
- Guardian observe を mere flag ではなく attested reviewer channel に昇格したくなった時
- 国や法域ごとに別の blocked token / duty-of-care profile が必要になった時
