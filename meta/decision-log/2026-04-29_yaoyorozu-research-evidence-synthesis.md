---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_synthesis.schema
  - evals/agentic/yaoyorozu_research_evidence_synthesis.yaml
status: decided
closes_next_gaps:
  - researcher-evidence-synthesis-runtime-binding
---

# Decision: Yaoyorozu researcher evidence を multi-exchange synthesis receipt に束ねる

## Context

`repo-local-research-evidence-exchange-v1` は 1 researcher の request/report を
source digest、evidence digest、Council+Guardian ledger entry に束縛していた。
ただし Council deliberation へ渡す段階では、複数 researcher の advisory evidence を
同一 session の digest family として束ねる reviewer-facing artifact が無く、
単一 researcher output だけを見ているように見えやすかった。

## Decision

`repo-local-research-evidence-synthesis-v1` を追加する。
synthesis receipt は少なくとも 2 つの ledger-appended researcher exchange を要求し、
distinct researcher id、exchange refs / digests、research domain refs、evidence refs、
evidence digest set、Council session ref を digest-only に束縛する。

claim ceiling は `implementation-advisory` に固定し、raw exchange payload、
raw research payload、researcher decision authority は保持しない。
synthesis 自体も `yaoyorozu-research-evidence` category の
`yaoyorozu.research_evidence.synthesized` event として Council+Guardian 署名 role で
ContinuityLedger に append する。

## Consequences

- `yaoyorozu-demo --json` は単一 exchange 互換出力に加えて、複数 exchange list と synthesis receipt を返す。
- Council reviewer は raw researcher output に戻らず、複数 evidence source の digest-bound 入力集合を確認できる。
- Researcher は引き続き advisory evidence provider であり、Council decision / runtime write authority へ昇格しない。

## Revisit triggers

- live external literature verifier transport を researcher exchange ごとに接続する時
- domain-specific researcher report schema を synthesis strategy ごとに分割する時
