---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - specs/schemas/yaoyorozu_worker_workspace_delta_receipt.schema
  - evals/agentic/yaoyorozu_worker_delta_receipt.yaml
status: decided
---

# Decision: Yaoyorozu worker report を git-bound target-path delta receipt まで昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local worker dispatch を持ち、
`target_path_observations` と `coverage_evidence` により
worker が intended workspace scope を見たことまでは
machine-checkable でした。

一方で worker report は
対象 path 配下にどの change candidate が存在するかを
git-bound artifact として保持しておらず、
`ready` report が返っても
「どの変更候補を見て builder handoff を受けたのか」を
public contract 上で監査できませんでした。

## Options considered

- A: path existence / sample observation のみを維持し、git-bound delta evidence は持ち込まない
- B: changed path count だけを summary field として足し、receipt artifact 自体は作らない
- C: dispatch/unit binding を維持したまま、target path scope に閉じた git-bound delta receipt を worker report に追加する

## Decision

**C** を採択。

## Consequences

- `local_worker_stub` は
  `yaoyorozu_worker_workspace_delta_receipt` を生成し、
  `git rev-parse HEAD` と `git status --short --untracked-files=all -- <target_paths...>` に
  束縛された changed path evidence を report へ含める
- `yaoyorozu_worker_dispatch_receipt` は
  `delta_receipt_ok` / `all_delta_receipts_bound` /
  `delta_scan_profile` / `delta_bound_count` を持ち、
  ready gate が target path observation と delta receipt の両方を要求する
- docs / eval / catalog / tests は
  Yaoyorozu worker が workspace boundary だけでなく
  git-bound target path delta evidence まで返す contract へ同期する
- residual gap は generic な「worker が何を見たか不明」ではなく、
  actual patch candidate ranking や remote sandbox execution witness のような
  次段の orchestration へ縮小する

## Revisit triggers

- worker delta receipt を changed path list から
  actual patch descriptor / diff hunk evidence まで昇格したくなった時
- repo-local git scan を超えて remote workspace / brokered sandbox でも
  同じ delta receipt family を維持したくなった時
- worker delta receipt を DesignReader / Builder apply / rollback receipt と
  同一 execution digest に統合したくなった時
