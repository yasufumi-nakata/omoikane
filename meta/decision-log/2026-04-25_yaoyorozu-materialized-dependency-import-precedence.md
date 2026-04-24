---
date: 2026-04-25
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.materialized-dependency-import-precedence
---

# Decision: Yaoyorozu worker は materialized dependency snapshot を先に import する

## Context

`same-host-external-workspace-dependency-materialization-v1` は worker 起動前に
minimal runtime dependency snapshot を external execution root へ copy していました。
ただし worker subprocess の `PYTHONPATH` は source checkout の `src` が先で、
materialized dependency が実際に import precedence を持ったことを
receipt / schema / eval だけで確認できませんでした。

## Options considered

- A: dependency manifest を保持し、import order は subprocess 実装 detail として扱う
- B: external workspace に full repo snapshot を持ち込み、source checkout を `PYTHONPATH` から外す
- C: materialized dependency `src` を source checkout `src` より前に置き、receipt に import path order と validation flag を残す

## Decision

**C** を採択。

`materialized-dependency-pythonpath-first-v1` を fixed profile とし、
external worker result は次を返す。

- `dependency_import_root`
- `dependency_import_path_order=[materialized_src, source_src]`
- `dependency_import_precedence_status=materialized-first`
- `dependency_import_precedence_bound=true`

repo-local worker は `source-inline` として source `src` のみを path order に残す。
`omoikane.__init__` と `omoikane.agentic.__init__` は lazy export にし、
minimal materialized package で `omoikane.agentic.local_worker_stub` を
source checkout より先に import しても不要な service module を eager import しない。

## Consequences

- external worker receipt は dependency manifest の存在だけでなく、
  worker subprocess が materialized dependency snapshot を source checkout より先に
  import したことを machine-checkable に示す
- public schema / IDL / eval / docs / Integrity Guardian capability は
  materialized-first import precedence を同じ profile id で共有する
- full repo snapshot は引き続き不要で、external workspace は target-path snapshot +
  minimal dependency snapshot の境界を維持する

## Revisit triggers

- cross-host worker runtime へ移行して source checkout fallback を外す時
- dependency snapshot を lockfile / package wheel artifact へ昇格する時
- worker stub 以外の helper package を materialized dependency set に追加する時
