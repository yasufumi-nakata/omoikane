---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_dependency_materialization_manifest.schema
  - specs/schemas/yaoyorozu_workspace_guardian_preseed_gate.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.dependency-materialization-gate
---

# Decision: Yaoyorozu preseed gate に dependency materialization を含める

## Context

`same-host-external-workspace-preseed-guardian-gate-v1` は
external execution root 作成と source target-path snapshot seed を
HumanOversightChannel-bound integrity gate に束縛していました。

ただし worker 起動に必要な最小 runtime dependency snapshot は
gate 対象や dispatch receipt の first-class artifact には含まれていませんでした。
このままでは external workspace が seed commit を持っていても、
worker 実行直前の dependency materialization が
reviewer-facing に machine-checkable ではありません。

## Options considered

- A: source checkout の `PYTHONPATH` だけを使い、dependency snapshot は作らない
- B: preseed gate の `required_before` に dependency materialization を追加し、最小 runtime dependency snapshot manifest を receipt 化する
- C: external workspace に full repo snapshot と dependency install step を持ち込む

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_workspace_guardian_preseed_gate` は
  `workspace-seed` / `execution-root-create` / `dependency-materialization`
  の 3 action より前に pass する
- `yaoyorozu_dependency_materialization_manifest` は
  `pyproject.toml`、`common.py`、`local_worker_stub.py` などの
  minimal runtime dependency snapshot を digest-bound に残す
- dispatch plan / receipt は dependency materialization profile、
  strategy、required count、manifest digest、materialized count を返す
- validator は manifest digest、file digest、source path order、external count の
  tampering を fail-closed にする
- full repo snapshot や dependency install は行わず、
  same-host external workspace の target-path snapshot boundary を維持する

## Revisit triggers

- cross-host worker runtime へ dispatch する時
- materialized dependency snapshot だけで worker を実行する必要が出た時
- dependency install / lockfile verification を gate 対象に含める時
