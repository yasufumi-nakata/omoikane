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

# Decision: Yaoyorozu builder の build surface scope を registry contract に固定する

## Context

Researcher role は `research_domain_refs` と `evidence_policy_ref` を
Yaoyorozu registry entry へ保持するようになったが、builder role は
coverage label と generic schema refs だけで materialize されていた。
そのため、hand off 前に builder が repo-local のどの surface を触れるか、
どの execution policy に従うかを registry snapshot から機械的に監査しにくかった。

## Options considered

- A: builder は既存の capability list だけで運用する
- B: builder role だけ `build_surface_refs` と `execution_policy_ref` を必須化する
- C: councilor / guardian も含めて全 role-specific source schema を一気に分割する

## Decision

B を採用する。
`agent_source_definition.schema` は role が `builder` の時だけ
`build_surface_refs` と `execution_policy_ref` を required にする。
Yaoyorozu runtime は registry materialization 前に同じ条件を検証し、
`agent_registry_entry` は builder entry に限って build surface refs と
execution policy ref を保持する。

これらは repo-local path / policy ref だけを保存し、raw patch payload や
execution transcript は registry に入れない。

## Consequences

- `agents/builders/*.yaml` は対象 surface と execution policy boundary を明示する。
- `yaoyorozu-demo --json` の registry snapshot は builder entry の build scope を返す。
- schema contract tests と agentic eval は、builder source definition の欠落を fail-closed で検出する。
- Council は builder を選ぶ時に、coverage label だけでなく surface / policy ref も監査できる。

## Revisit triggers

- Councilor / guardian にも role-specific source schema を導入する時
- Builder の execution policy を action class ごとの sub-policy に分割する時
