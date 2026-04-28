---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_source_manifest_ledger_binding.schema
  - evals/agentic/yaoyorozu_source_manifest_ledger_binding.yaml
status: decided
---

# Decision: Yaoyorozu source manifest を ContinuityLedger に dedicated binding する

## Context

Yaoyorozu registry snapshot は raw `agents/**/*.yaml` source set の digest manifest を
保持していたが、registry snapshot 自体を見るだけでは、その source manifest が
append-only ledger 上で self と Guardian の署名 role に束縛された証跡まで確認できなかった。

## Decision

`yaoyorozu_source_manifest_ledger_binding` を追加し、
`repo-local-agent-source-digest-manifest-v1` の ordered source definition digest set を
dedicated `yaoyorozu-agent-source-manifest` ContinuityLedger entry に append する。
ledger entry は `self` と `guardian` の署名 role を必須とし、binding receipt は
entry ref、entry hash、payload ref、source manifest digest、registry digest を返す。

raw source definition payload、raw registry payload、raw continuity event payload は
binding receipt に保存しない。

## Consequences

- IntegrityGuardian は registry source manifest の改ざん検査を ledger ref / payload ref から監査できる。
- `yaoyorozu-demo --json` は registry snapshot だけでなく、source manifest ledger binding を reviewer-facing artifact として返す。
- schema / eval / tests は source manifest digest、ledger entry、self+guardian signature roles、raw payload 非保存を同じ contract として検証する。

## Revisit triggers

- source manifest binding を public verification bundle の別 projection として公開する時
- agent source manifest を workspace discovery や cross-workspace dispatch manifest と統合する時
