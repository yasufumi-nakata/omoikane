---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/agent_source_definition.schema
  - specs/schemas/agent_registry_entry.schema
  - evals/agentic/yaoyorozu_agent_source_definition_contract.yaml
status: decided
---

# Decision: Yaoyorozu researcher の evidence scope を registry contract に固定する

## Context

Yaoyorozu registry は raw `agents/**/*.yaml` を schema-bound に検証してから
materialize していたが、`researcher` role は Council と同じ generic schema refs だけを
持っていた。
そのため、研究補助 agent がどの research/domain surface を扱い、どの evidence policy
に従うのかを reviewer-facing registry entry から機械的に確認しにくかった。

## Options considered

- A: Researcher を既存の Council input/output schema のまま運用する
- B: Researcher role だけ `research_domain_refs` と `evidence_policy_ref` を必須化する
- C: Councilor / builder / guardian も含めて role-specific source schema を一気に分割する

## Decision

B を採用する。
`agent_source_definition.schema` は role が `researcher` の時だけ
`research_domain_refs` と `evidence_policy_ref` を required にする。
Yaoyorozu runtime は同じ条件を registry materialization 前に検証し、
`agent_registry_entry` は researcher entry に限って domain refs と evidence policy ref を保持する。

これらは docs / research / agents 配下の repo-local ref だけを保存し、
raw research payload や外部文献本文は registry に入れない。

## Consequences

- `agents/researchers/*.yaml` は research domain と evidence policy boundary を明示する。
- `yaoyorozu-demo --json` の registry snapshot は researcher entry の evidence scope を返す。
- schema contract tests と agentic eval は、researcher source definition の欠落を fail-closed で検出する。
- Council は researcher を選ぶ時に、role 名だけでなく domain/evidence policy ref も監査できる。

## Revisit triggers

- Councilor / builder / guardian にも role-specific source schema を導入する時
- Researcher 専用の input/output schema を Council schema から分離する時
