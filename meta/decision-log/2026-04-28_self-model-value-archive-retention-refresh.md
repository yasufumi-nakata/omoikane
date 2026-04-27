---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_archive_retention_refresh_receipt.schema
  - evals/identity-fidelity/self_model_value_archive_retention_refresh.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel value archive retention proof を refresh / revocation / expiry window に束縛する

## Context

`self-model-value-archive-retention-proof-v1` は retired value archive snapshot を
external trustee proof、long-term storage proof、retention policy、retrieval test refs へ
digest-only に束縛した。
ただし proof refresh / revocation / expiry window は次の review trigger として残っており、
初回 proof が無期限に受理されるか、失効・失効確認・更新期限が reviewer-facing artifact
に出ない状態だった。

## Decision

`self-model-value-archive-retention-refresh-window-v1` を追加し、
`self_model_value_archive_retention_refresh_receipt` で source proof receipt digest、
source retention commit digest、archive snapshot set digest、retention policy set digest、
更新後の trustee / storage / retrieval test proof digest set、revocation registry digest set、
90 日 freshness window、refresh deadline、continuity audit ref、Council resolution、
Guardian archive ref を `refresh_commit_digest` に束縛する。

この receipt は `source_proof_status=current-not-revoked`、
`refresh_status=refreshed-before-expiry`、`expiry_fail_closed=true` を固定し、
revoked / expired source proof を受理しない。archive deletion、external veto、
raw refresh / revocation / archive / storage payload 保存も許さない。

## Consequences

- `self-model-demo --json` は `value_archive_retention_refresh` branch と validation summary を返す。
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する。
- ledger event は refresh receipt digest、refresh commit binding、revocation check binding、
  expiry fail-closed を identity-fidelity evidence として残す。

## Revisit triggers

- 実在 trustee registry や storage verifier の live response を refresh receipt に接続する時
- retention proof refresh cadence を identity ごと、jurisdiction ごとに変える時
