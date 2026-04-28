---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - agents/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_registry_snapshot.schema
  - specs/schemas/council_convocation_session.schema
  - evals/agentic/yaoyorozu_agent_source_definition_contract.yaml
status: decided
---

# Decision: Yaoyorozu source digest manifest と builder coverage target binding を固定する

## Context

Yaoyorozu registry は role-specific scope refs と policy refs を保持していたが、
reviewer が registry snapshot だけを見る場合、raw `agents/**/*.yaml` の正確な
source file set と digest、および builder coverage area がどの target path set を
覆ったかを digest-only に確認しにくかった。

## Decision

`yaoyorozu_registry_snapshot` に `repo-local-agent-source-digest-manifest-v1` を追加し、
各 raw source definition の `source_ref`、`agent_id`、`role`、`sha256`、
`byte_length` と ordered manifest digest を保存する。raw source payload は保存しない。

`council_convocation_session.builder_handoff` には
`coverage-area-target-path-binding-v1` を追加し、coverage area ごとの fixed target path refs
を selected builder の `build_surface_refs` に束縛する。

## Consequences

- Registry reviewer は raw YAML 本文に戻らなくても source set の digest provenance を検証できる。
- Builder coverage は prefix だけでなく、runtime / schema / eval / docs ごとの target path refs として監査できる。
- IntegrityGuardian は source manifest と coverage target binding を同じ Yaoyorozu contract として attest する。

## Revisit triggers

- Builder coverage area を subdirectory 単位より細かい file-pattern set に分割する時
- source digest manifest を ContinuityLedger entry へ別カテゴリで append する時
