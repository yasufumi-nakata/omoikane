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

# Decision: Yaoyorozu Guardian の attestation scope を registry contract に固定する

## Context

Yaoyorozu registry は researcher の evidence scope と builder の build surface scope を
role-specific contract として保持するようになっていた。
一方で Guardian role は capability list と自然文の invoke 条件だけに依存しており、
Ethics / Identity / Integrity Guardian がどの docs / specs / evals / agents / meta
surface を監査し、どの attestation policy に従うのかを registry snapshot から
機械的に監査しにくかった。

## Options considered

- A: Guardian は existing capability list だけで運用する
- B: Guardian role だけ `oversight_scope_refs` と `attestation_policy_ref` を必須化する
- C: Councilor を含む全 role-specific source schema を同時に分割する

## Decision

B を採用する。
`agent_source_definition.schema` は role が `guardian` の時だけ
`oversight_scope_refs` と `attestation_policy_ref` を required にする。
Yaoyorozu runtime は registry materialization 前に同じ条件を検証し、
`agent_registry_entry` は Guardian entry に限って oversight scope refs と
attestation policy ref を保持する。

これらは repo-local path / policy ref だけを保存し、raw audit payload、
raw verifier response、raw registry payload、raw packet body は registry に入れない。

## Consequences

- `agents/guardians/*.yaml` は対象 oversight surface と attestation policy boundary を明示する。
- `yaoyorozu-demo --json` の registry snapshot は Guardian entry の監査 scope を返す。
- schema contract tests と agentic eval は、Guardian source definition の欠落を fail-closed で検出する。
- Council は Guardian を選ぶ時に、capability label だけでなく scope / policy ref も監査できる。

## Revisit triggers

- Councilor role にも role-specific deliberation scope を導入する時
- Guardian attestation policy を capability class ごとの sub-policy に分割する時
