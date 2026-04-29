---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/agent_source_definition.schema
  - specs/schemas/agent_registry_entry.schema
  - specs/schemas/research_evidence_request.schema
  - specs/schemas/research_evidence_report.schema
  - evals/agentic/yaoyorozu_agent_source_definition_contract.yaml
status: decided
closes_next_gaps:
  - researcher-evidence-schema-contract
---

# Decision: Yaoyorozu researcher evidence schema を Council schema から分離する

## Context

`researcher` role は `research_domain_refs` と `evidence_policy_ref` を registry entry に
保持していたが、input / output schema は Council session や jurisdiction-specific schema を
再利用できる状態だった。
これでは researcher が advisory-only evidence report を返すのか、Council decision payload を
扱うのかを registry materialization 前に機械的に区別しにくい。

## Decision

`research_evidence_request.schema` と `research_evidence_report.schema` を追加し、
researcher source definition の `input_schema_ref` / `output_schema_ref` をこの 2 つに固定する。
Yaoyorozu runtime は researcher が Council input/output schema を指した場合に fail-closed する。
registry entry も同じ schema refs を保持し、`yaoyorozu-demo --json` の validation は
`researcher_evidence_schema_contract_bound=true` を返す。

report schema は source refs、evidence digest、claim ceiling、advisory-only implication、
raw research payload 非保存、decision authority 不保持を required にする。

## Consequences

- Researcher は Council decision maker ではなく、advisory evidence provider として分離される。
- `agents/researchers/*.yaml` はすべて research evidence request/report schema を参照する。
- schema / IDL / eval / tests は researcher evidence scope と evidence schema を同じ contract として検証する。

## Revisit triggers

- researcher evidence report を live external literature verifier transport へ接続する時
- domain-specific researcher report schema を法律 / neuroscience / experiment design ごとに分ける時
