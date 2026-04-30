---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
status: decided
closes_next_gaps:
  - sensory-loopback-calibration-refresh-propagation
---

# Decision: shared loopback arbitration は calibration refresh を participant ごとに伝播する

## Context

BioData Transmitter は `biodata-calibration-refresh-window-v1` により、current drift gate、
self consent、Guardian review、freshness window を calibration confidence gate に
直接束縛できるようになった。Sensory Loopback の shared arbitration は participant ごとの
confidence gate、feature-window drift gate、hardware timing latency gate を検証していたが、
fresh calibration refresh receipt が group arbitration の入口で participant set と同じ粒度で
伝播されていることまでは contract 化していなかった。

## Decision

`participant-biodata-gate-arbitration-v1` は各 participant の confidence gate について、
`calibration_refresh_bound=true`、`calibration_refresh_status=fresh`、
`calibration_refresh_window_bound=true`、refresh ref / digest / source digest set が
揃うことを必須にする。shared binding は
`participant_calibration_refresh_digest_set`、`all_calibration_refresh_receipts_fresh`、
`all_calibration_refresh_windows_bound`、top-level `calibration_refresh_status=fresh` を返し、
runtime validation、public schema、IDL、eval、CLI demo、IntegrityGuardian policy で同じ条件を
確認する。

## Consequences

- `sensory-loopback-demo --json` の shared path は participant ごとの calibration refresh
  receipt を group arbitration binding に伝播し、validation に fresh / digest-set bound の
  flag を露出する。
- storage policy は `participant-gate+drift+refresh-digest-only` とし、raw BioData、
  calibration、drift、refresh、gate payload は保存しない。
- weighted latency quorum は refresh freshness を満たした participant set の上でのみ
  評価されるため、hardware timing acceptance と calibration reuse freshness が分離して
  監査できる。

## Revisit triggers

- calibration refresh freshness を live scheduler cadence や external verifier SLA に接続する時
- participant ごとの refresh source に multi-jurisdiction Guardian quorum を追加する時
- refresh expiry / revocation を shared sensory session の途中で fail-closed に伝播する時
