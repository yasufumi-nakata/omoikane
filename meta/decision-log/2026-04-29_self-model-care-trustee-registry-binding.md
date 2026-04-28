---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_care_trustee_registry_binding_receipt.schema
  - evals/identity-fidelity/self_model_care_trustee_registry_binding.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel care trustee registry binding を外部証跡に固定する

## Context

`self-model-care-trustee-responsibility-handoff-v1` は、長期 trustee、care team、
legal guardian の責任分担を外部制度 refs と境界 refs へ digest-only に束縛した。
ただし、handoff refs が現在有効な外部 registry entry、verifier key ref、
not-revoked revocation ref に接続されていることは、repo-local の machine-checkable
contract にはなっていなかった。

## Decision

`self-model-care-trustee-registry-binding-v1` を追加し、
`self_model_care_trustee_registry_binding_receipt` で source care trustee handoff
receipt、source role refs、registry entry digest set、registry snapshot digest、
verifier key refs、revocation refs、Council resolution、Guardian boundary、
continuity review ref を digest-only に束縛する。

reference runtime は、すべての trustee / care team / legal guardian refs が
`current` かつ `not-revoked` の registry entry に覆われる場合だけ
`binding_status=bound` とする。raw registry / revocation / trustee / care / legal
payload は保存しない。OS trustee role、OS medical authority、OS legal guardianship、
SelfModel writeback、forced correction はいずれも許可しない。

## Consequences

- `self-model-demo --json` は `care_trustee_registry_binding` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は registry binding digest、external registry bound、no raw registry payload を identity-fidelity evidence として残す

## Revisit triggers

- 外部 registry の real verifier transport と freshness SLA を導入する時
- trustee / care team / legal guardian registry の jurisdiction-specific schema を分岐する時
- revocation verifier quorum を care trustee registry binding に直接接続する時
