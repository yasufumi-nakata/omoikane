---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - agents/guardians/integrity-guardian.yaml
  - docs/02-subsystems/agentic/README.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_research_evidence_exchange.schema
  - evals/agentic/yaoyorozu_research_evidence_exchange.yaml
status: decided
closes_next_gaps:
  - researcher-evidence-exchange-runtime-binding
---

# Decision: Yaoyorozu researcher evidence exchange を runtime receipt 化する

## Context

前段では `research_evidence_request.schema` と
`research_evidence_report.schema` を追加し、researcher source definition が
Council input/output schema を再利用しないことを固定した。
ただし `yaoyorozu-demo` はまだ実際の researcher request/report exchange を返しておらず、
source digest、evidence digest、ledger entry へ同時に束縛された reviewer-facing receipt が無かった。

## Decision

`YaoyorozuRegistryService` に `repo-local-research-evidence-exchange-v1` を追加し、
選定 researcher の registry entry、source definition digest、request/report digest、
repo-local evidence digest、Council+Guardian 署名付き ContinuityLedger entry ref/hash/payload ref を
単一の `yaoyorozu_research_evidence_exchange` として返す。
request は raw payload retention と decision authority を禁止し、report は
`implementation-advisory` claim ceiling と `advisory-only` implication に限定する。

## Consequences

- Researcher schema は source definition だけでなく runtime exchange として検証される。
- IntegrityGuardian は researcher output が Council decision や runtime write authority を持たないことを ledger evidence 付きで監査できる。
- `yaoyorozu-demo --json` は source manifest public verification bundle と researcher exchange binding の両方を返す。

## Revisit triggers

- researcher evidence report を live external literature verifier transport へ接続する時
- domain-specific researcher report schema を法律 / neuroscience / experiment design ごとに分ける時
- Council deliberation へ複数 researcher exchange を束ねる synthesis receipt を追加する時
