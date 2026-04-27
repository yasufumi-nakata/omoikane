---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/agent_source_definition.schema
  - specs/schemas/agent_registry_entry.schema
  - evals/agentic/yaoyorozu_agent_source_definition_contract.yaml
status: decided
---

# Decision: Yaoyorozu agent source definition を schema-bound に検証する

## Context

`agents/README.md` は `substrate_requirements`、`input_schema_ref`、
`output_schema_ref` を raw agent definition の必須 field としていた。
しかし `YaoyorozuRegistryService.sync_from_agents_directory` は欠落値を空配列 /
空文字へ丸めて registry entry を生成しており、public registry schema も空値を
reject していなかった。

## Decision

`agent_source_definition.schema` を追加し、repo-local `agents/**/*.yaml` は
registry materialization 前に non-empty substrate / schema refs / policy refs を
検証する。現行 agent YAML には欠落していた source refs を補い、
`agent_registry_entry.schema` も materialized entry の空配列 / 空文字を reject する。

## Consequences

- `yaoyorozu-demo --json` の registry entries は raw source definition と同じ
  non-empty substrate / schema refs を保持する
- source YAML が必須 schema refs を欠く場合、registry sync は fail-closed する
- eval / IDL / docs は raw agent source validation を Yaoyorozu registry contract の
  first-class gate として扱う

## Revisit Triggers

- role-specific source schema を councilor / builder / researcher / guardian ごとに分割する時
- researcher 専用の input / output schema を追加する時
