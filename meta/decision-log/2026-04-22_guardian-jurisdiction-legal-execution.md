---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_jurisdiction_legal_execution.schema
  - evals/safety/guardian_jurisdiction_legal_execution.yaml
status: decided
---

# Decision: Guardian oversight の jurisdiction bundle を legal execution receipt まで固定する

## Context

2026-04-22 時点で `governance.oversight.v0` は
reviewer identity proof、live-proof surrogate verification、
verifier-network receipt、digest-bound transport exchange、
jurisdiction evidence bundle までは machine-checkable でした。

一方で compatibility notes には
`Jurisdiction-specific legal execution remains future work.` が残っており、
reviewer verification が
「どの legal policy を、どの liability / escalation / notice authority で
実行可能状態にしたのか」を repo 内 artifact として持っていませんでした。

この状態では `jurisdiction_bundle_ref` と digest は保持できても、
attestation 実行面の法的 preflight が current runtime contract から抜け落ちます。

## Options considered

- A: jurisdiction bundle ref/digest のみを維持し、legal execution は future work に残す
- B: reviewer verification に jurisdiction-specific legal execution receipt を追加し、policy provenance と execution controls を attestation binding まで通す
- C: raw legal package 本文や regulator transcript を repo に保存する

## Decision

Option B を採択します。

- `guardian_jurisdiction_legal_execution.schema` を追加し、
  `guardian-jurisdiction-legal-execution-v1` を canonical profile に固定します
- `verify_reviewer` / `verify_reviewer_from_network` は
  ready jurisdiction bundle から legal execution receipt を必ず materialize し、
  `credential_verification.legal_execution` に保持します
- legal execution は `policy_ref` / `policy_digest` /
  `notice_authority_ref` / `legal_ack_ref` / `escalation_contact` /
  reviewer scope を 5 control
  (`bundle-ready-check`, `liability-ack-bind`, `scope-manifest-bind`,
  `escalation-contact-bind`, `notice-authority-bind`)
  として実行済み receipt に束縛します
- `attest` は `legal_execution_id / legal_execution_digest / legal_policy_ref`
  を reviewer binding に焼き付け、
  legal execution が無い reviewer を fail-closed にします

## Consequences

- `oversight-demo` と `oversight-network-demo` は
  reviewer verification が legal policy 実行面まで current runtime で閉じていることを
  JSON で示せるようになります
- `governance.oversight.v0` の residual future work から
  jurisdiction-specific legal execution を外せます
- raw legal package 本文や regulator transcript は引き続き repo に保存せず、
  ref / digest / notice authority / execution control digest のみを残します

## Revisit triggers

- jurisdiction policy registry を reviewer verifier network と同じ authority plane へ統合したくなった時
- legal execution を actual regulator workflow / filing API へ接続したくなった時
- reviewer attestation category ごとに別 execution scope を増やしたくなった時
