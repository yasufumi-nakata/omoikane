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
  - yaoyorozu.workspace.sealed-materialized-import
---

# Decision: Yaoyorozu external worker import は materialized snapshot のみを許可する

## Context

`materialized-dependency-module-origin-v1` は worker report の import 元を
materialized dependency snapshot 配下へ束縛しました。
ただし external worker の `PYTHONPATH` には source checkout `src` が fallback として残り、
reviewer が「起動時に source checkout を参照しなかった」ことを
path order だけでは強く確認できませんでした。

## Options considered

- A: materialized-first path order を維持し、source checkout fallback は運用 detail として許容する
- B: source checkout fallback を残したまま、module origin digest だけで十分とみなす
- C: external worker の `PYTHONPATH` を materialized dependency `src` のみにし、receipt / schema / eval へ `materialized-only` を固定する

## Decision

**C** を採択。

`materialized-dependency-sealed-import-v1` を fixed profile とし、
external worker result は次を満たす。

- `dependency_import_path_order=[<execution_root>/.yaoyorozu-dependencies/src]`
- `dependency_import_precedence_status=materialized-only`
- `worker_module_origin.search_path_head` に source checkout `src` を含めない
- `worker_module_origin.module_file` と digest は materialized dependency manifest の
  `src/omoikane/agentic/local_worker_stub.py` entry と一致する

repo-local worker は引き続き `source-inline` として source checkout `src` のみを使う。

## Consequences

- external workspace worker の起動経路は、target-path snapshot と minimal dependency snapshot の
  境界を越えて source checkout の runtime code へ fallback しない
- public schema / IDL / eval / docs / IntegrityGuardian capability は
  sealed materialized-only import isolation を同じ closure point として共有する
- future cross-host worker runtime へ移す時も、source checkout fallback を外した
  import contract をそのまま remote attestation へ束縛できる

## Revisit triggers

- dependency snapshot を lockfile / wheel artifact へ昇格する時
- external worker が `local_worker_stub` 以外の helper module を materialized dependency set へ追加する時
- cross-host worker runtime で sealed dependency root を remote attestation と束縛する時
