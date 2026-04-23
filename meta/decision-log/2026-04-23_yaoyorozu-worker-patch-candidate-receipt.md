---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/patch_descriptor.schema
  - specs/schemas/yaoyorozu_worker_patch_candidate_receipt.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_worker_patch_candidate_receipt.yaml
status: decided
---

# Decision: Yaoyorozu local worker report を patch_descriptor-compatible candidate receipt へ昇格する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
repo-local worker dispatch を持ち、
`target_path_observations` と `yaoyorozu_worker_workspace_delta_receipt` により
worker が intended workspace scope と changed path を見たことまでは
machine-checkable でした。

一方で worker report は
「その changed path を builder handoff 上でどう読むか」を
public contract として返しておらず、
`delta-detected` の先にある reviewer-facing patch candidate の形が
repo 内 surface として固定されていませんでした。

## Options considered

- A: delta receipt だけを維持し、patch candidate への読み替えは人手に委ねる
- B: full `build_artifact` を worker report へ埋め込み、PatchGenerator surface をそのまま持ち込む
- C: `patch_descriptor` を再利用した lightweight candidate receipt を追加し、delta receipt と target-path observation に束縛する

## Decision

**C** を採択します。

- worker report は `yaoyorozu_worker_patch_candidate_receipt` を持ち、
  `target-delta-to-patch-candidate-v1` を canonical profile に固定します
- receipt は dispatch/unit binding、delta receipt ref/digest、
  target-path observation digest を保持しつつ、
  each changed path を `patch_descriptor` 互換 object へ materialize します
- ready gate は `path-bound-target-delta-patch-candidate-v3` に引き上げ、
  all target paths ready だけでなく
  all delta entries materialized も要求します

## Consequences

- `yaoyorozu-demo` は worker report が
  target observation / delta receipt / patch candidate receipt を同じ dispatch unit に束縛したことを
  reviewer-facing に示せます
- `patch_descriptor.schema` との shape drift を増やさず、
  future の PatchGenerator / Builder handoff へ接続しやすくなります
- residual gap は generic な「changed path をどう読むか不明」ではなく、
  priority ranking や actual patch application witness のような
  次段の execution orchestration へ縮小します

## Revisit triggers

- worker candidate receipt に priority ranking や diff hunk summary を追加したくなった時
- local worker receipt を PatchGenerator build_artifact や builder apply receipt と
  同一 execution digest で統合したくなった時
- repo-local subprocess を超えて remote sandbox / external runtime にも
  同じ candidate receipt family を維持したくなった時
