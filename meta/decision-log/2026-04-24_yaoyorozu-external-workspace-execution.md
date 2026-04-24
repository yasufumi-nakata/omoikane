---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/council_convocation_session.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.external-execution
---

# Decision: Yaoyorozu worker dispatch を same-host external workspace execution へ昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
same-host workspace discovery、proposal-profile-aware review policy、
repo-local worker dispatch、ConsensusBus / TaskGraph / build_request / execution-chain binding まで
machine-checkable でした。

一方、workspace discovery で non-source candidate workspace を見つけても、
actual worker execution は source checkout 内の repo-local subprocess に留まっていました。
この状態では candidate workspace の coverage は review catalog には現れても、
worker dispatch receipt が candidate workspace 上の execution root、
seeded source snapshot、candidate/source success count を証明できませんでした。

## Options considered

- A: discovery は review-only のまま維持し、worker execution は source checkout 固定にする
- B: same-host candidate workspace の下に execution root を作り、source target-path snapshot を seed して local worker stub を起動する
- C: remote scheduler / cross-host sandbox cluster まで一気に広げる

## Decision

**B** を採択。

## Consequences

- `council_convocation_session` は `workspace_execution_binding` を持ち、
  dispatch coverage area ごとに selected workspace ref、root、role、scope、
  transport profile、sandbox seed strategy を digest-bound にする
- profile required coverage は non-source candidate workspace 必須とし、
  requested optional coverage は candidate workspace が無い場合に source fallback を明示する
- `yaoyorozu_worker_dispatch_plan` は
  `execution_workspace_ref` / `execution_workspace_root` /
  `selected_workspace_root` / `selected_workspace_role` /
  `execution_host_ref` / `execution_transport_profile` /
  `sandbox_seed_strategy` を unit ごとに持つ
- `execute_worker_dispatch` は
  external candidate worker では source target-path snapshot を
  `.yaoyorozu-external-execution/<dispatch>/<coverage>` へ copy し、
  cache artifact を除外した seed commit を作ってから worker stub を実行する
- `yaoyorozu_worker_dispatch_receipt` は
  `workspace_seed_status`、`workspace_seed_head_commit`、
  candidate/source success count、same-host scope validation を返す
- `yaoyorozu_external_workspace_execution.yaml` が
  candidate-bound execution、source fallback absence、seed receipt、same-host scope を
  eval surface として固定する

## Revisit triggers

- same-host local workspace ではなく cross-host worker runtime へ dispatch する場合
- candidate workspace に full repo snapshot や dependency install step を持ち込みたくなった場合
- Guardian oversight を workspace seed / external execution root creation の前段 gate に上げる場合
