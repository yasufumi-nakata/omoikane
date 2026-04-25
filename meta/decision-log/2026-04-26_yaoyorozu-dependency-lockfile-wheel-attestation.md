---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_dependency_materialization_manifest.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.dependency-lockfile-wheel-attestation
---

# Decision: Yaoyorozu dependency snapshot を lockfile / wheel attestation へ昇格する

## Context

`same-host-external-workspace-dependency-materialization-v1` は
external execution root へ最小 runtime dependency snapshot をコピーし、
`materialized-dependency-sealed-import-v1` と
`materialized-dependency-module-origin-v1` により source checkout fallback 無しの
worker import origin まで検証していました。

ただし reviewer が確認できる snapshot evidence は file digest list が中心で、
dependency set 全体の lockfile と sealed artifact digest が
first-class に束縛されていませんでした。

## Options considered

- A: 既存 file digest list のまま運用し、lockfile は省く
- B: manifest 内に digest-only lockfile と deterministic sealed wheel artifact digest を追加する
- C: 外部 package installer を実行して real dependency install receipt を保存する

## Decision

**B** を採択。

`yaoyorozu_dependency_materialization_manifest` は
`materialized-dependency-lockfile-v1` の lockfile digest と
`materialized-dependency-wheel-attestation-v1` の sealed wheel artifact digest /
attestation digest を持つ。

## Consequences

- external worker の dependency materialization は file digest list、lockfile digest、
  sealed wheel artifact digest、attestation digest の 4 点で同じ dispatch unit に束縛される
- worker launch は引き続き materialized `src` のみを `PYTHONPATH` に入れ、
  source checkout fallback を使わない
- public schema / IDL / eval / docs / IntegrityGuardian capability は
  lockfile と sealed artifact attestation を同じ closure point として共有する
- 外部 installer は呼ばず、standard library の deterministic zip artifact だけを使う

## Revisit triggers

- cross-host worker runtime で remote artifact store へ seal する時
- full dependency installer を sandbox 内で実行する必要が出た時
- wheel metadata を package installer compatible な form へ拡張する時
