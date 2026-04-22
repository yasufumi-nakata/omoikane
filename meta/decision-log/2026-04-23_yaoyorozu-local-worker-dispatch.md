---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_dispatch_plan.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_local_worker_dispatch.yaml
status: decided
---

# Decision: Yaoyorozu builder handoff を repo-local worker dispatch receipt まで昇格する

## Context

2026-04-22 時点で `agentic.yaoyorozu.v0` は
repo-local registry sync と Council convocation までは
machine-checkable でしたが、
compatibility note には
`live agent process orchestration remain outside this repo`
が残っていました。

この状態では `builder_handoff` が
runtime / schema / eval / docs を覆うと示されても、
その handoff が actual local worker process として
どう materialize されるかを repo 内で検証できませんでした。

## Options considered

- A: registry / convocation のみを維持し、worker dispatch は repo 外の future work に残す
- B: builder handoff を queue descriptor だけへ延長し、actual process execution は持ち込まない
- C: repo-local に限定した bounded subprocess worker dispatch plan / receipt を追加する

## Decision

**C** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は
  `prepare_worker_dispatch` / `execute_worker_dispatch` を持ち、
  `yaoyorozu_worker_dispatch_plan` /
  `yaoyorozu_worker_dispatch_receipt` を public contract にする
- reference runtime は
  `runtime / schema / eval / docs` の各 coverage area を
  1 worker ずつの repo-local subprocess launch へ固定し、
  zero-exit `ready` report を receipt に束縛する
- `yaoyorozu-demo` は
  trust-bound registry snapshot、
  bounded convocation、
  actual local worker dispatch receipt を
  1 run で監査できる
- residual gap は generic な live process orchestration 不在ではなく、
  cross-workspace worker discovery や external runtime dispatch のような
  repo 外 coordination へ縮小する

## Revisit triggers

- repo-local subprocess を超えて
  remote worker runtime / sandbox cluster / external scheduler へ dispatch したくなった時
- builder handoff を `self-modify-patch-v1` 以外の proposal profile へ広げたくなった時
- worker receipt を ConsensusBus / TaskGraph / Guardian oversight と
  同一 execution digest で統合したくなった時
