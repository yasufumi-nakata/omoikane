---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_participant_approval_transport_receipt.schema
  - specs/schemas/wms_physics_rules_change_receipt.schema
  - evals/interface/wms_participant_approval_transport.yaml
status: decided
closes_next_gaps:
  - wms.physics-rules.participant-approval-transport
---

# Decision: WMS participant approval を IMC transport receipt に束縛する

## Context

`wms_physics_rules_change_receipt` は reversible physics_rules change を
unanimous approval / Guardian attestation / rollback token に束縛していました。
ただし approval は `participant_approvals` の static id list であり、
実際に participant が live channel 上で同じ proposal subject を承認したことまでは
machine-checkable ではありませんでした。

## Options considered

- A: static `participant_approvals` を維持し、transport binding は future work のままにする
- B: approval message の raw payload を WMS receipt に保存する
- C: IMC handshake / message digest / approval subject digest を
  `wms_participant_approval_transport_receipt` として保存し、
  raw conversation body は保存しない

## Decision

**C** を採択。

`imc-participant-approval-transport-v1` を fixed profile とし、
physics_rules apply は次を満たす時だけ `applied` になる。

- WMS session participant 全員の `participant_approvals`
- 同じ `approval_subject_digest` に束縛された participant ごとの IMC receipt
- `peer_attested=true`
- `forward_secrecy=true`
- approval payload の `redacted_fields=[]`
- Guardian attestation と rollback token

## Consequences

- static participant list だけでは physics_rules change は `rejected` になる
- `wms-demo --json` は approval subject、IMC messages、transport receipts、
  physics change / revert receipts を同じ digest family として返す
- public schema / IDL / eval / Integrity Guardian capability は
  participant approval の live transport binding を同じ profile id で共有する

## Remaining scope

- distributed Council transport 経由の approval fan-out は research frontier に残す
- 大人数 shared_reality の approval collection scaling は別 surface として扱う

## Revisit triggers

- WMS approval を Federation / Heritage Council の returned result と直接束縛する時
- IMC approval message を remote attested transport に切り替える時
