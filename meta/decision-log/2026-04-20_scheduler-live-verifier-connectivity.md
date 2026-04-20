---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - docs/07-reference-implementation/README.md
  - evals/continuity/scheduler_live_verifier_connectivity.yaml
  - specs/interfaces/kernel.scheduler.v0.idl
  - specs/schemas/governance_verifier_roster.schema
  - specs/schemas/governance_verifier_connectivity_receipt.schema
status: decided
---

# Decision: AscensionScheduler external verifier live connectivity を bounded receipt として固定する

## Context

`docs/07-reference-implementation/README.md` の future work には
`AscensionScheduler external verifier の真正性証明と live 接続`
が残っていました。
既存 runtime は `sync_governance_artifacts` によって
`verifier_roster` snapshot を受け取って pause / cutover / fail-closed までは評価できましたが、
その roster をどの live endpoint から取得し、
どの程度の latency / digest / HTTP status で観測したのかを
repo 内で machine-checkable に残す surface はありませんでした。

そのため `scheduler-demo` は verifier rotation の state machine は示せても、
external verifier live connectivity 自体は still surrogate input に留まっていました。

## Options considered

- A: verifier roster は今後も外から注入する前提にして、live connectivity は future work に残す
- B: live connectivity を導入するが、raw transcript や full response body まで repo に保存する
- C: bounded live HTTP JSON fetch で roster を取得し、endpoint / digest / latency / status だけを
  `connectivity_receipt` として roster に束縛する

## Decision

**C** を採択。

## Consequences

- `kernel.scheduler.v0` に `probe_live_verifier_roster` を追加し、
  live endpoint から取得した roster を `sync_governance_artifacts` の前段で正規化できるようにする
- `governance_verifier_connectivity_receipt.schema` を追加し、
  `verifier_endpoint` / `response_digest` / `observed_latency_ms` / `http_status` /
  `request_timeout_ms` / `rotation_state` / `accepted_root_count`
  を bounded receipt として保持する
- `governance_verifier_roster.schema` は optional な `connectivity_receipt` を持ち、
  `scheduler-demo` では loopback live verifier endpoint を立てて
  protected handoff 前の live fetch を確認する
- raw external transcript や full network trace は repo に残さず、
  digest と summary fields のみを continuity-safe に保持する

## Revisit triggers

- distributed transport actual network と scheduler verifier connectivity を統合したい時
- HTTPS mutual-auth や richer PKI metadata を receipt に追加したい時
- raw transcript や signed response body まで監査対象に上げる必要が出た時
