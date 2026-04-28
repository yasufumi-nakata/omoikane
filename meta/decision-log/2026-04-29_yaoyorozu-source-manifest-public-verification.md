---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_source_manifest_ledger_binding.schema
  - specs/schemas/yaoyorozu_source_manifest_public_verification_bundle.schema
  - evals/agentic/yaoyorozu_source_manifest_public_verification.yaml
status: decided
closes_next_gaps:
  - source-manifest-public-verification-projection
---

# Decision: Yaoyorozu source manifest を public verification bundle に投影する

## Context

`yaoyorozu-agent-source-manifest` の ContinuityLedger binding は、
source manifest digest と ledger entry ref / hash / payload ref を self+guardian 署名 role に
束縛していた。一方で、外部 reviewer が raw `agents/**/*.yaml`、raw registry payload、
raw continuity event payload、raw signature payload なしで同じ証跡を検証するための
dedicated public projection はまだ registry artifact として分離されていなかった。

## Decision

`yaoyorozu-source-manifest-public-verification-bundle-v1` を追加する。
bundle は source definition digest set、source manifest digest、registry digest、
dedicated ledger entry ref / hash / payload ref、continuity event digest、
self+guardian の signature digest、ContinuityLedger verifier key refs を束縛する。

raw source、registry、continuity event、signature payload は bundle に公開しない。
ledger binding receipt は `public_verification_bundle_ref` と
`public_verification_bundle_digest` を保持し、validation で bundle binding と digest binding を
同時に true にする。

## Consequences

- `yaoyorozu-demo --json` は source manifest ledger binding の中に public verification bundle を返す。
- IntegrityGuardian は raw source set に触れず、source digest manifest と ledger signature digest evidence を監査できる。
- schema / IDL / eval / tests は source manifest provenance、ledger evidence、signature digest redaction を同じ contract として検証する。

## Revisit triggers

- Yaoyorozu source manifest の public verification bundle を ContinuityLedger 全体の public verification bundle と統合する時
- external workspace discovery manifest や cross-workspace dispatch manifest も同じ public projection へ含める時
