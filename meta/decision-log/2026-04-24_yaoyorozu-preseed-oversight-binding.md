---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/guardian_oversight_event.schema
  - specs/schemas/yaoyorozu_workspace_guardian_preseed_gate.schema
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_external_workspace_execution.yaml
status: decided
closes_next_gaps:
  - yaoyorozu.workspace.preseed-human-oversight-binding
---

# Decision: Yaoyorozu preseed gate を HumanOversightChannel event に束縛する

## Context

`same-host-external-workspace-preseed-guardian-gate-v1` は
external execution root 作成と source target-path snapshot seed の前に
integrity Guardian gate を要求していました。

ただし gate は単体 artifact であり、HumanOversightChannel の reviewer-network attestation、
reviewer quorum、legal execution digest を同じ gate/receipt で確認する contract には
なっていませんでした。

## Options considered

- A: preseed gate の `gate_status=pass` だけを維持する
- B: preseed gate に `guardian_oversight_event` ref/digest/status と reviewer quorum を束縛し、dispatch receipt へ carry する
- C: external workspace seed 前に full Guardian oversight demo を毎回実行する

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_workspace_guardian_preseed_gate` は
  `human-oversight-channel-preseed-attestation-v1` profile を持つ
  `guardian_oversight_event` を外部 workspace gate に必須化する
- dispatch plan / receipt は
  oversight event count、satisfied count、reviewer-network attested status、
  reviewer quorum を machine-checkable に返す
- validator は tampered oversight event status や verifier-network binding を
  fail-closed にする
- eval / docs / agent capability は
  preseed gate が単なる local bool ではなく reviewer-network attested artifact であることに同期する

## Revisit triggers

- same-host external workspace から cross-host worker runtime へ拡張する時
- preseed gate を rotating reviewer roster や jurisdiction diversity quorum に広げる時
- source target-path snapshot seed だけでなく dependency materialization も gate 対象に含める時
