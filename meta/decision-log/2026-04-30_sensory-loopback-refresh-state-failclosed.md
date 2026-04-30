---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_calibration_refresh_state_guard.schema
  - evals/interface/sensory_loopback_calibration_refresh_state_guard.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-refresh-state-failclosed
---

# Decision: shared loopback の refresh state recheck は fail-closed guard として扱う

## Context

shared Sensory Loopback arbitration は participant ごとの BioData confidence gate、
feature-window drift gate、fresh calibration refresh receipt、hardware timing latency gate、
weighted latency quorum を binding に束縛していた。これにより session 開始時の
freshness は保証できるが、session 中に refresh が expired、revoked、stale へ変わった時に
delivery block と shared session hold へ伝播する machine-checkable surface は分かれていなかった。

## Decision

`participant-calibration-refresh-state-fail-closed-v1` を public schema、IDL、runtime、
eval、CLI demo、IntegrityGuardian policy に追加する。guard は既存の
`participant-biodata-gate-arbitration-v1` binding の refresh ref / digest /
source digest set / window flag を participant order のまま再利用し、current status を
`fresh / expired / revoked / stale` として recheck する。

`expired`、`revoked`、`stale` が 1 件でもあれば `refresh_fail_closed=true`、
`delivery_blocked=true`、`shared_session_hold_required=true`、
`safe_baseline_required=true`、`guard_status=blocked` にする。`revoked` は
revocation registry ref を必須にし、非 revoked status は revocation ref を持たない。

## Consequences

- `sensory-loopback-demo --json` の weighted shared path は peer の expired refresh と
  observer の revoked refresh を fail-closed guard に通し、guard validation と public
  schema contract manifest へ露出する。
- guard は refresh state digest set、guard digest、revocation ref だけを保持し、
  raw refresh payload と raw revocation payload を保存しない。
- existing BioData arbitration binding は fresh receipt の入口保証として残り、
  mid-session state recheck は別 schema として監査できる。
