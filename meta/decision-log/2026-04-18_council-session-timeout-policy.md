---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/council-protocol.md
  - docs/02-subsystems/agentic/council-composition.md
  - docs/01-architecture/failure-modes.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/council_timeout_fallback.yaml
  - evals/agentic/council_expedited_timeout_defer.yaml
  - specs/interfaces/agentic.council.v0.idl
  - specs/schemas/council_session_policy.schema
status: decided
---

# Decision: Council session の時間 budget と timeout 戦略を固定する

## Context

`meta/open-questions.md` に残っていた `Council session の最大時間と timeout 戦略`
は、L4 の runtime・schema・eval のどこにも具体値がなく、議事が長引いた時の
fallback が曖昧でした。`docs/04-ai-governance/council-protocol.md` には
緊急議事が `<1s` とだけあり、standard session の上限や
soft timeout 時の扱いが固定されていませんでした。

## Options considered

- A: timeout 戦略は研究課題のまま残し、runtime 側には何も入れない
- B: standard / expedited を同じ budget で扱い、単純に elapsed だけで打ち切る
- C: mode ごとに固定 budget を与え、soft timeout は weighted-majority fallback、
  hard timeout は standard で human escalation、expedited で defer に分ける

## Decision

**C** を採択。

## Consequences

- reference runtime の Council に session policy と timeout verdict を追加する
- standard session は `45s soft / 90s hard / max 4 rounds / quorum 3` に固定する
- expedited session は `250ms soft / 1s hard / max 1 round / quorum 2` に固定する
- soft timeout は quorum が揃っていれば `timeout-fallback` として weighted-majority に移る
- hard timeout は standard で `timeout-escalation`、expedited で `deferred` とし、
  follow-up action を必須化する

## Revisit triggers

- Council transcript を外部永続化し、round ごとの wall-clock が取得できるようになった時
- multi-Council federation を導入し、単一 budget では文化圏差を表現できなくなった時
- human governance の上申先が具体実装され、escalation payload を詳細化する時
