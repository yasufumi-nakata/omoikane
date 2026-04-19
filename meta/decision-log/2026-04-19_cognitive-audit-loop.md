---
date: 2026-04-19
deciders: [yasufumi, codex]
related_docs:
  - docs/02-subsystems/agentic/cognitive-audit-loop.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/cognitive_audit_loop.yaml
  - specs/interfaces/agentic.cognitive_audit.v0.idl
status: decided
---

# Decision: reference runtime に cognitive audit loop を追加する

## Context

`gap-report --json` は clean でも、
`evals/cognitive/README.md` には
`qualia checkpoint と ContinuityLedger の横断整合` と
`L4 Council との認知系監査ループ` が次段階として残っていました。
既に `QualiaBuffer`、`SelfModelMonitor`、`MetacognitionService`、
`Council`、`ContinuityLedger` は存在していたため、
cross-layer loop を docs-only のまま残す理由は薄くなっていました。

## Options considered

- A: qualia と metacognition を別々の demo のまま維持し、Council 連携は future work に残す
- B: qualia / self-model / metacognition / Council を束ねる bounded audit contract を追加する
- C: distributed oversight や external verifier まで含む広い監査基盤を一気に実装する

## Decision

B を採択しました。
`agentic.cognitive_audit.v0` を追加し、
`cognitive_audit_record` と `cognitive_audit_resolution` を定義します。
reference runtime では
`qualia-checkpoint` entry を先に append し、
abrupt self-model observation と metacognition alert を
bounded Council review に束ねて、
`cognitive-audit` category で follow-up を記録します。

## Consequences

- qualia / self-model / metacognition / Council の cross-layer surface が machine-readable になります
- `cognitive-audit-demo` で continuity-safe review loop を再現できます
- raw sensory embedding や sealed metacognition note を audit artifact に出さずに済みます
- distributed oversight や remote attestation までは引き続き future work です

## Revisit triggers

- audit loop を Federation / Heritage review や distributed oversight へ接続したくなった時
- raw note ではなく richer structured planner / remediation tree が必要になった時
- external verifier や legal reviewer attestation を live binding したくなった時
