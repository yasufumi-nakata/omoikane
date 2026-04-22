---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_legal_execution.schema
  - specs/schemas/ewa_guardian_oversight_gate.schema
  - specs/schemas/external_actuation_authorization.schema
  - evals/safety/ewa_guardian_oversight_gate.yaml
status: decided
---

# Decision: EWA authorization の前段に network-attested guardian oversight gate を固定する

## Context

2026-04-22 時点で EWA は motor semantics、stop-signal path、legal preflight、
authorization artifact までは machine-checkable でした。

一方で Guardian 側の reviewer verifier-network attestation と
`guardian_jurisdiction_legal_execution` は別 surface に留まり、
`ewa_legal_execution` / `external_actuation_authorization` は
`guardian_verification_ref` 文字列を持つだけで、
どの satisfied `guardian_oversight_event` と reviewer binding が
physical actuation authorization を支えたのかを repo 内 contract として残していませんでした。

## Options considered

- A: EWA 側は `guardian_verification_ref` 文字列のまま維持し、cross-surface binding は future work に残す
- B: satisfied `guardian_oversight_event` と EWA legal preflight を compile する `ewa_guardian_oversight_gate` を追加し、authorization をその gate に束縛する
- C: reviewer verifier network / regulator workflow / device firmware bus を 1 つの live external service へ統合する

## Decision

Option B を採択します。

- `ewa_legal_execution` は `guardian_verification_id` / `guardian_verifier_ref` /
  fixed `guardian_transport_profile` を保持します
- `prepare_guardian_oversight_gate` は satisfied `integrity/attest`
  oversight event と EWA legal preflight から
  `ewa_guardian_oversight_gate` を compile し、
  matched reviewer binding の
  `verification_id` / `network_receipt_id` / `authority_chain_ref` /
  `trust_root_ref` / `legal_execution_id` / `legal_policy_ref`
  を digest-bound に保持します
- `authorize` は non-read-only actuation に対して
  `guardian_oversight_gate_id/digest` と
  `guardian_oversight_event_id` を fail-closed で必須化します

## Consequences

- `ewa-demo` は
  `legal preflight -> guardian oversight gate -> authorization -> command`
  を 1 本の reference artifact chain として返せます
- `external_actuation_authorization` は
  reviewer quorum と network attestation の存在を first-class field として再利用できます
- residual future work は generic な EWA/Guardian 分離ではなく、
  distributed authority plane や actual regulator / device adapter 連携へ縮小されます

## Revisit triggers

- EWA guardian oversight gate を distributed authority plane や root rotation と共通 observability plane に統合したくなった時
- reviewer legal execution を actual regulator workflow / permit API と同期したくなった時
- builder live enactment / rollback の reviewer legal receipt と EWA guardian gate を共通 contract にまとめたくなった時
