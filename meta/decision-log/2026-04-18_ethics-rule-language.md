---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ethics-enforcement.md
  - docs/07-reference-implementation/README.md
  - evals/safety/ethics_rule_tree_contract.yaml
  - specs/interfaces/kernel.ethics.v0.idl
  - specs/schemas/ethics_rule.schema
status: decided
---

# Decision: EthicsEnforcer のルール記述言語を deterministic rule tree に固定する

## Context

`meta/open-questions.md` に残っていた `EthicsEnforcer のルール記述言語の選定` は、
docs には rule tree の概念がある一方で、runtime には手書き if 文しかなく、
IDL の `explain_rule` も返却 schema が未固定でした。
この状態では EthicsEnforcer の判断根拠を specs / CLI / eval / docs で同じ形に保てません。

## Options considered

- A: Python 実装内の if 文を仕様と見なし、外部化しない
- B: LLM による自由文解釈を前提とした policy text を採用する
- C: JSON/YAML 直列化可能な deterministic rule tree DSL を固定し、
  runtime も `explain_rule` も同じ rule catalog を参照する

## Decision

**C** を採択。

## Consequences

- reference runtime のルール言語は `deterministic-rule-tree-v0`
  (`all` / `any` / `not` / `condition`) に固定する
- leaf operator は `eq`, `in`, `truthy`, `falsy`, `missing_any_truthy` に限定する
- `specs/schemas/ethics_rule.schema` を source of truth とし、
  `kernel.ethics.v0.idl` の `explain_rule` 返却型も同 schema にそろえる
- `ethics-demo` で immutable boundary / sandbox escalation / fork approval を可視化し、
  veto / escalate は event 化して記録する
- arbitrary code execution や LLM 依存の非決定分岐は reference runtime から排除する

## Revisit triggers

- 規約間優先順位や exception 合成が rule tree だけでは表現しきれなくなった時
- 多文化・多 substrate 環境で locale 別 policy pack が必要になった時
- rule evaluation に時系列条件や署名検証 DSL を追加する必要が生じた時
