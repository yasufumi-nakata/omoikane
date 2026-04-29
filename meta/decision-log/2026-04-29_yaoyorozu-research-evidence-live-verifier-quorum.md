---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_verifier_receipt.schema
  - evals/agentic/yaoyorozu_research_evidence_verifier.yaml
status: decided
closes_next_gaps:
  - researcher-evidence-live-verifier-transport
---

# Decision: Yaoyorozu researcher evidence verifier を live quorum へ束縛する

## Context

`repo-local-research-evidence-verifier-v1` は researcher report の evidence ref を
repo-local readback で expected / observed digest に束縛していた。
ただし reviewer-facing artifact としては、readback digest が外部 verifier transport、
signed response、freshness window、quorum policy に接続されておらず、
live verifier transport へ進める時の境界がまだ曖昧だった。

## Decision

既存の repo-local digest readback は残し、その digest set を
`digest-only-live-research-evidence-verifier-quorum-v1` の対象 evidence とする。
verifier receipt は literature-index / publisher-record の 2 class、
JP-13 / US-CA の 2 jurisdiction、threshold 2、signed response envelope、
900 秒 freshness window、transport receipt digest set、quorum digest を束縛する。
raw evidence payload、raw verifier response payload、raw signature payload、
network payload、decision authority は保持しない。

multi-researcher synthesis は各 exchange の verifier digest だけでなく
`verifier_transport_quorum_digest` set も束縛し、Council deliberation 前の
advisory input が live verifier quorum を経由したことを machine-checkable にする。

## Consequences

- `yaoyorozu-demo --json` は researcher exchange ごとに live verifier transport quorum receipt を返す。
- schema / IDL / eval / docs / IntegrityGuardian policy は raw-payload redaction と signed/freshness/quorum の両方を検証する。
- Researcher は引き続き evidence provider であり、Council decision や runtime write authority へ昇格しない。

## Revisit triggers

- 実 HTTP / publisher API / DOI resolver への transport 実装を追加する時
- domain-specific verifier class を neuroscience / legal / experiment design ごとに分割する時
- verifier quorum policy を法域や source class ごとに可変 threshold にする時
