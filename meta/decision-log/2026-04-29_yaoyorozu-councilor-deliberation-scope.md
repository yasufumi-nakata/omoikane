---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/agent_source_definition.schema
  - specs/schemas/agent_registry_entry.schema
  - evals/agentic/yaoyorozu_agent_source_definition_contract.yaml
status: decided
---

# Decision: Yaoyorozu Councilor の deliberation scope を registry contract に固定する

## Context

Yaoyorozu registry は Researcher / Builder / Guardian の role-specific scope を
raw source definition と registry entry に保持するようになっていた。
一方で Councilor role は Council input/output schema と capability label だけで
materialize されており、DesignArchitect / ChangeAdvocate /
ConservatismAdvocate / EthicsCommittee / MemoryArchivist がどの docs / specs /
evals / agents / meta surface を評議し、どの deliberation policy に従うのかを
registry snapshot から機械的に監査しにくかった。

## Options considered

- A: Councilor は既存 capability list と Council schema refs だけで運用する
- B: Councilor role だけ `deliberation_scope_refs` と `deliberation_policy_ref` を必須化する
- C: Councilor ごとに別 schema を作り、Council convocation schema も同時分割する

## Decision

B を採用する。
`agent_source_definition.schema` は role が `councilor` の時だけ
`deliberation_scope_refs` と `deliberation_policy_ref` を required にする。
Yaoyorozu runtime は registry materialization 前に同じ条件を検証し、
`agent_registry_entry` は Councilor entry に限って deliberation scope refs と
deliberation policy ref を保持する。

これらは repo-local path / policy ref だけを保存し、raw deliberation transcript、
raw Council argument payload、raw registry payload は registry に入れない。

## Consequences

- `agents/councilors/*.yaml` は対象 deliberation surface と policy boundary を明示する。
- `yaoyorozu-demo --json` の registry snapshot は Councilor entry の評議 scope を返す。
- schema contract tests と agentic eval は、Councilor source definition の欠落を fail-closed で検出する。
- Council は Councilor を選ぶ時に、capability label だけでなく scope / policy ref も監査できる。

## Revisit triggers

- Councilor role ごとに input/output schema を分割する時
- Council deliberation policy を proposal profile ごとの sub-policy に分割する時
