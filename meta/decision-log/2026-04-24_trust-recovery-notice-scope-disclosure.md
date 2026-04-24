---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_recovery_review.schema
  - specs/schemas/trust_redacted_destination_recovery_summary.schema
  - specs/schemas/trust_transfer_receipt.schema
  - evals/agentic/trust_cross_substrate_transfer.yaml
status: decided
closes_next_gaps:
  - 2026-04-24_trust-recovery-rationale-redaction-summary.md#notice-authority-execution-scope-floor
---

# Decision: Trust recovery review は notice authority と legal execution scope を redacted disclosure floor に含める

## Context

`trust-transfer-demo` は recovered branch の rationale と legal proof summary まで
redacted export に残せていましたが、jurisdiction-specific notice authority と
実際に許可・禁止された recovery execution scope は full `trust_recovery_review`
側の暗黙条件に留まっていました。

このままでは redacted reviewer が multi-root recovery quorum と legal proof digest を確認できても、
復帰時にどの notice authority へ束縛され、どの recovery action だけが許されたかを
machine-checkable に監査できません。

## Options considered

- A: existing legal proof digest の内部情報として扱い、public summary は増やさない
- B: notice authority refs だけを redacted summary に露出し、execution scope は future work に残す
- C: full review に notice authority refs と bounded execution scope manifest を追加し、redacted summary では scope digest と action count だけを公開する

## Decision

**C** を採択。

## Consequences

- `trust_recovery_review.schema` は `notice_authority_refs` と
  `bounded-trust-recovery-legal-execution-scope-v1` manifest を要求する
- redacted `trust_redacted_destination_recovery_summary` は
  `notice_authority_refs` と `execution_scope_summary` を公開し、
  full scope manifest と legal acknowledgement refs は sealed / redacted に保つ
- `TrustService.validate_transfer_receipt()` は
  `recovery_notice_scope_bound` を返し、
  notice authority / execution scope digest が recovered verifier federation の jurisdiction set と
 一致しなければ fail-closed にする
- CLI / schema / eval / tests / docs は同じ disclosure floor に同期した

## Revisit triggers

- notice authority を static refs ではなく live jurisdiction registry から解決したくなった時
- recovery scope に expiry / renewal / emergency override を追加したくなった時
- redacted summary で action count ではなく action class labels まで公開したくなった時
