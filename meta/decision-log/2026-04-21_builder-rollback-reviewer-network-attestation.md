---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.rollback.v0.idl
  - specs/schemas/builder_rollback_session.schema
  - evals/continuity/builder_rollback_oversight_network.yaml
status: decided
---

# Decision: builder rollback に reviewer verifier-network attestation を必須化する

## Context

2026-04-21 時点で `RollbackEngineService` は、
temp rollback workspace での actual reverse-apply command、
repo-bound verification、
detached checkout mutation receipt、
current-worktree direct mutation receipt、
repo-root external observer receiptまでは machine-checkable でした。

一方で、rollback 自体を **どの human reviewer が live verifier network で確認して承認したか**
は rollback contract の外に残っていました。
`OversightService` には `verify_reviewer_from_network()` が既にあり、
reviewer verifier-network receipt は別 surface として実装済みだったため、
rollback approval 側へ統合する余地がありました。

## Options considered

- A: rollback は既存 telemetry gate のみで維持し、reviewer network attestation は future work に残す
- B: rollback plan payload を持つ `guardian_oversight_event` を追加し、integrity reviewer 2 名の verifier-network attestation を rollback telemetry gate の approval 条件へ束縛する
- C: rollback telemetry を verifier network の raw transcript まで含めて全面的に transport 化する

## Decision

Option B を採択します。

`RollbackEngineService` は `guardian_oversight_event` を
`builder_rollback_session` の first-class field として保持し、
次を approval 条件に追加します。

- `guardian_role=integrity`
- `category=attest`
- `payload_ref == rollback_plan_ref`
- reviewer quorum `2/2`
- reviewer binding 2 件とも `network_receipt_id / authority_chain_ref / trust_root_ref / trust_root_digest` を持つこと

`telemetry_gate` も reviewer quorum / network receipt count / network-attested verdict を持ち、
rollback-approved の前提に含めます。

## Consequences

- `rollback-demo` は repo 内だけで reviewer verifier-network attestation まで再現し、
  rollback plan と human approval の結びつきを machine-checkable にします
- `selfctor.rollback.v0` / `builder_rollback_session.schema` /
  `builder_rollback_oversight_network.yaml` が同じ contract を共有します
- residual future work は reviewer attestation 一般論ではなく、
  raw verifier transcript や cross-host authority routing のような
  より外部依存の強い領域へ縮小されます

## Revisit triggers

- rollback approval を 2 名より大きい reviewer quorum へ拡張したい時
- reviewer verifier network を root rotation や multi-jurisdiction registry と統合したい時
- rollback telemetry に raw verifier payload / transcript retention を求めたくなった時
