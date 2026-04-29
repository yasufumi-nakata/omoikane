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
  - researcher-evidence-verifier-readback
---

# Decision: Yaoyorozu researcher evidence に verifier readback receipt を束縛する

## Context

`repo-local-research-evidence-exchange-v1` は selected researcher の request/report、
repo-local evidence digest、Council+Guardian ledger entry を束縛していた。
ただし reviewer-facing artifact としては、evidence ref を独立に readback した verifier
receipt が無く、exchange の内部 validation と evidence digest が同じ artifact に畳まれていた。

## Decision

`repo-local-research-evidence-verifier-v1` を追加する。
verifier receipt は exchange ref、researcher id、evidence refs、expected / observed
digest set、digest set digest、verified evidence count を保持し、raw evidence payload、
network payload、decision authority をいずれも保持しない。

exchange receipt は verifier ref / digest / receipt を first-class field として持ち、
synthesis receipt は source exchanges 由来の verifier refs / digests / digest-set digest を
同じ advisory Council input に束縛する。

## Consequences

- `yaoyorozu-demo --json` は researcher exchange と synthesis の両方で verifier binding を返す。
- public schema / IDL / eval / tests は expected / observed repo-local digest readback と raw payload 非保存を同じ contract として検証する。
- IntegrityGuardian は researcher evidence が Council decision authority へ昇格していないことに加え、evidence readback 自体も監査できる。

## Revisit triggers

- repo-local readback を live external literature verifier transport へ接続する時
- domain-specific researcher evidence verifier policy を法律 / neuroscience / experiment design ごとに分岐する時
