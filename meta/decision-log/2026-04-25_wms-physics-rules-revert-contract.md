---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_physics_rules_change_receipt.schema
  - evals/interface/wms_physics_rules_revert.yaml
status: decided
---

# Decision: WMS physics_rules change を reversible receipt へ昇格する

## Context

`docs/02-subsystems/interface/wms-spec.md` は、physics_rules 変更に
満場一致と revert API を要求していました。
一方で reference runtime と `interface.wms.v0` は
`snapshot / propose_diff / switch_mode / observe_violation` に留まり、
shared reality の physics_rules 改変が本当に rollback 可能かを
machine-checkable に検証できませんでした。

## Options considered

- A: docs の不変条件を維持し、physics_rules 変更は future work のままにする
- B: physics_rules_ref を直接変更するだけで、rollback token と Guardian attestation は後回しにする
- C: unanimous approval、Guardian attestation、rollback token、first-class revert receipt を同じ WMS contract に固定する

## Decision

**C** を採択。

## Consequences

- `wms_physics_rules_change_receipt.schema` を追加し、
  `apply` と `revert` の両 receipt を digest-bound に固定する
- `WorldModelSync.propose_physics_rules_change()` と
  `revert_physics_rules_change()` は、全 participant approval、
  Guardian attestation、rollback token、baseline rules restoration を要求する
- `wms-demo --json` は physics_rules change と revert を返し、
  `evals/interface/wms_physics_rules_revert.yaml` と schema contract test で
  public payload を継続検証する

## Remaining scope

- actual physics engine や perceptual adaptation は research frontier に残す
- time_rate の distributed synchronization は引き続き twin-integration 側の研究課題に分離する

## Revisit triggers

- physics_rules change を real multi-user engine の transaction log と統合したくなった時
- participant approval を live IMC / distributed Council transport へ接続したくなった時
