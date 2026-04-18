---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - meta/naming-decisions.md
  - meta/open-questions.md
  - docs/00-philosophy/etymology.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
  - evals/identity-fidelity/naming_policy_contract.yaml
  - specs/interfaces/governance.naming.v0.idl
  - specs/schemas/naming_policy.schema
status: decided
---

# Decision: project romanization を `Omoikane`、sandbox fork 名を `Mirage Self` に固定する

## Context

`meta/open-questions.md` に naming 2 件が残っていた一方で、
docs 本文・glossary・runtime の class alias では表記がまだ機械的に検証されていませんでした。
この状態では `Omoi-Kane` のような派生表記や、
サンドボックス自我の呼称揺れがレビューごとに再発し、
reference runtime と design corpus の接続点が曖昧なままでした。

## Options considered

- A: naming は docs の注意事項に留め、runtime では扱わない
- B: project name と sandbox name を単に markdown で fixed し、machine-readable contract は作らない
- C: `NamingService` / `governance.naming.v0` / schema / eval を追加し、
  canonical term・rejected form・internal alias を機械可読に固定する

## Decision

**C** を採択。

## Consequences

- project-facing 英字表記は `Omoikane` に固定し、`Omoi-Kane` 系は rewrite-required とする
- サンドボックス自我の formal name は `Mirage Self` に固定し、
  `Yumi Self` / `Phantom Self` は rejected form とする
- `SandboxSentinel` は runtime 実装の legacy alias としてのみ残し、
  user-facing docs では promotion しない
- `naming-demo` と `naming_policy_contract` eval が docs / spec / runtime / test の接点になる
- gap report 上の naming open question は close する

## Revisit triggers

- `SandboxSentinel` を本当に `MirageSelf` class へ rename したい時
- 国際向け documentation で追加の transliteration policy が必要になった時
- 複数 sandbox fork family を導入し、Mirage Self の下位 taxonomy が必要になった時
