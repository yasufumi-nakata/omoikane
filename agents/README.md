# Agents ── 役割定義

OmoikaneOS で召喚しうる Agent の役割定義（YAML）を格納する。
この repo では docs だけでなく `src/`, `tests/`, `specs/`, `evals/` を更新する Builder もここで定義する。

## 構造

```
agents/
  councilors/   # 評議系（Council 構成員）
  builders/     # 実装系（同一 repo の reference runtime で動作）
  researchers/  # 研究補助系
  guardians/    # 監視系
```

## 役割定義のフォーマット

各 `agents/**/*.yaml` は
[`specs/schemas/agent_source_definition.schema`](../specs/schemas/agent_source_definition.schema)
に従い、Yaoyorozu registry materialization 前に必須 field と repo-local ref が検証される。
registry snapshot には raw YAML 本文ではなく、各 source definition の digest manifest だけを保持する。
同じ source manifest は ContinuityLedger entry と public verification bundle に束縛され、
raw source / registry / continuity event / signature payload を公開しない。
Builder の `build_surface_refs` は convocation 時に coverage area ごとの fixed target path refs を覆う必要がある。
Researcher の `input_schema_ref` / `output_schema_ref` は
`specs/schemas/research_evidence_request.schema` /
`specs/schemas/research_evidence_report.schema` に固定し、Council input/output へ混ぜない。

```yaml
name: <unique>
role: councilor|builder|researcher|guardian
version: <semver>
capabilities: [<capability_id>]
trust_floor: <0.0-1.0>
substrate_requirements: [<id> | 'any']
input_schema_ref: <specs/...>  # researcher は specs/schemas/research_evidence_request.schema 固定
output_schema_ref: <specs/...>  # researcher は specs/schemas/research_evidence_report.schema 固定
deliberation_scope_refs: [<docs/...> | <specs/...> | <evals/...> | <agents/...> | <meta/...>]  # councilor のみ必須
deliberation_policy_ref: <agents/... | docs/... | specs/... | evals/... | meta/...>  # councilor のみ必須
build_surface_refs: [<src/...> | <tests/...> | <specs/...> | <evals/...> | <docs/...>]  # builder のみ必須
execution_policy_ref: <agents/... | docs/... | specs/... | evals/... | meta/...>  # builder のみ必須
research_domain_refs: [<docs/...> | <research/...>]  # researcher のみ必須
evidence_policy_ref: <agents/... | docs/... | research/...>  # researcher のみ必須
oversight_scope_refs: [<docs/...> | <specs/...> | <evals/...> | <agents/...> | <meta/...>]  # guardian のみ必須
attestation_policy_ref: <agents/... | docs/... | specs/... | evals/... | meta/...>  # guardian のみ必須
ethics_constraints: [<rule_id>]
prompt_or_policy_ref: <agents/.../policy.md>
when_to_invoke: |
  自然文での召喚条件
when_not_to_invoke: |
  自然文での非召喚条件
```

## 召喚規約

詳細は [docs/04-ai-governance/subagent-roster.md](../docs/04-ai-governance/subagent-roster.md) と
[docs/04-ai-governance/codex-as-builder.md](../docs/04-ai-governance/codex-as-builder.md)。

## 命名

- 神話メタファーを優先（meta/glossary.md 参照）
- 機能名は英語、神話名は和ローマ字も併記
