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
  - yaoyorozu.workspace.materialized-dependency-module-origin
---

# Decision: Yaoyorozu worker は materialized dependency module origin を証明する

## Context

`materialized-dependency-pythonpath-first-v1` は external worker の
`PYTHONPATH` order を receipt に残していました。
ただし path order だけでは、実際に起動した
`omoikane.agentic.local_worker_stub` が materialized dependency snapshot 由来で
import されたことまでは worker 自身の出力から検証できませんでした。

## Options considered

- A: path order のみを維持し、module origin は subprocess 実装 detail として扱う
- B: parent process が expected path を推定して receipt に補う
- C: worker report 自身が `worker_module_origin` を emit し、parent が materialized root / digest / search path order と照合する

## Decision

**C** を採択。

`materialized-dependency-module-origin-v1` を fixed profile とし、
worker report は次を返す。

- `module_name=omoikane.agentic.local_worker_stub`
- `module_file`
- `module_digest`
- `search_path_head`
- `origin_digest`

external dispatch receipt はこの report を
`dependency_module_origin_*` field へ束縛し、
module file が materialized dependency `src` 配下にあり、
source checkout fallback より先に search path 上で解決されることを検証する。

## Consequences

- materialized dependency snapshot は存在・path order だけでなく、
  worker process の実 import origin まで reviewer-facing に machine-checkable になる
- public schema / IDL / eval / IntegrityGuardian capability は
  `materialized-dependency-module-origin-v1` を同じ closure point として共有する
- full repo snapshot は引き続き不要で、external workspace は target-path snapshot +
  minimal dependency snapshot の境界を維持する

## Revisit triggers

- dependency snapshot を lockfile / wheel artifact へ昇格する時
- source checkout fallback を外して materialized dependency だけで worker を起動する時
- cross-host worker runtime で module provenance を remote attestation と束縛する時
