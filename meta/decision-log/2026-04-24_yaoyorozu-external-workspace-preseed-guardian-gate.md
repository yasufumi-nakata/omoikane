---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_workspace_guardian_preseed_gate.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.preseed-guardian-gate
---

# Decision: Yaoyorozu external workspace seed 前に integrity Guardian gate を first-class 化する

## Context

`agentic.yaoyorozu.v0` は same-host candidate workspace discovery から
external execution root 作成、source target-path snapshot seed、worker stub 実行、
dispatch receipt への seed commit 記録までを machine-checkable にしていました。

一方、seed / execution-root creation の直前に
integrity Guardian がその action を許可した事実は
receipt 内で独立した artifact として検証できませんでした。
このままでは candidate workspace 側の root 作成が bounded でも、
seed 前 gate の有無を reviewer が schema / eval / test だけで確認できません。

## Options considered

- A: existing worker dispatch validation の `same_host_scope_only` に含め、gate artifact は増やさない
- B: `yaoyorozu_worker_dispatch_plan` の dispatch unit に preseed gate を持たせ、receipt result に同じ gate digest / status を carry する
- C: HumanOversightChannel の full reviewer-network event まで preseed に要求する

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_workspace_guardian_preseed_gate.schema` を追加し、
  `same-host-external-workspace-preseed-guardian-gate-v1` を
  `workspace-seed` / `execution-root-create` より前の integrity attestation として固定する
- `prepare_worker_dispatch` は external dispatch unit ごとに
  `guardian_preseed_gate` と `workspace_target_digest` を持たせる
- `execute_worker_dispatch` は external unit の gate が pass しない限り
  seed workspace を作らず fail-closed にする
- `yaoyorozu_worker_dispatch_receipt` は gate status / digest / summary count を返し、
  validator は tampered external gate を reject する
- `yaoyorozu_external_workspace_execution.yaml` は
  preseed gate profile と pass count を eval expectation に含める

## Revisit triggers

- same-host local workspace ではなく cross-host worker runtime へ dispatch する場合
- preseed gate を HumanOversightChannel の reviewer-network event へ昇格したくなった場合
- candidate workspace に full repo snapshot や dependency install step を持ち込みたくなった場合
