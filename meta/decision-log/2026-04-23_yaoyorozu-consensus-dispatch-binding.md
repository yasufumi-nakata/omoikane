---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/interfaces/agentic.consensus_bus.v0.idl
  - specs/schemas/yaoyorozu_consensus_dispatch_binding.schema
  - evals/agentic/yaoyorozu_consensus_dispatch.yaml
status: decided
---

# Decision: Yaoyorozu builder handoff を same-session ConsensusBus binding まで昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local registry sync、bounded Council convocation、
repo-local worker dispatch receipt までは machine-checkable でした。
一方で decision log の revisit trigger には、
この convocation / builder handoff を
`ConsensusBus` dispatch と same-session digest で直結したい、
という残差が残っていました。

この状態では selected builder 群が local subprocess として実行された後、
その handoff が
`ConsensusBus` の audited delivery、guardian gate、
blocked direct handoff と同じ session 上で閉じていることを
repo 内の public contract として確認できませんでした。

## Options considered

- A: current の worker dispatch receipt を維持し、ConsensusBus binding は docs-only のまま据え置く
- B: convocation / dispatch plan / dispatch receipt を同じ session_id の `ConsensusBus` transcript と束縛する public binding artifact を追加する
- C: TaskGraph construction まで同時に結合し、Yaoyorozu dispatch 全体を graph-first orchestration へ置き換える

## Decision

**B** を採択。

## Consequences

- `agentic.yaoyorozu.v0` は `bind_consensus_dispatch` を持ち、
  `yaoyorozu_consensus_dispatch_binding` を public contract にする
- `yaoyorozu-demo` は
  convocation と同じ `session_id` 上で
  brief、4 worker report、guardian gate、final resolve、
  blocked direct builder handoff を生成し、
  dispatch claim chain を audit summary に束縛する
- `evals/agentic/yaoyorozu_consensus_dispatch.yaml` により、
  same-session binding、direct handoff block、
  guardian-gated resolution を継続検証できる
- residual gap は generic な Yaoyorozu/ConsensusBus 分離ではなく、
  TaskGraph construction との same-session 統合や
  cross-workspace external worker dispatch のような次段へ縮小する

## Revisit triggers

- Yaoyorozu convocation を `self-modify-patch-v1` 以外の proposal profile へ広げ、
  profile ごとの bus transcript 差分を public contract にしたくなった時
- worker dispatch receipt を TaskGraph node / ConsensusBus claim / Guardian oversight digest と
  同一 execution bundle に統合したくなった時
- repo-local subprocess を超えて external worker runtime や remote sandbox cluster へ
  audited dispatch したくなった時
