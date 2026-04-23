---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/yaoyorozu_worker_patch_candidate_receipt.schema
  - specs/schemas/yaoyorozu_worker_dispatch_receipt.schema
  - evals/agentic/yaoyorozu_worker_patch_candidate_receipt.yaml
status: decided
---

# Decision: Yaoyorozu patch candidate receipt に deterministic priority ranking を追加する

## Context

2026-04-23 時点で `agentic.yaoyorozu.v0` は
target path observation、git-bound delta receipt、
`patch_descriptor` 互換 patch candidate receipt までは
machine-checkable でした。

一方で patch candidate 群は
builder apply review に渡す順序や重点が public contract に現れておらず、
同じ delta evidence から出た候補のどれを先に review すべきかを
repo 内の deterministic surface として監査できませんでした。

## Options considered

- A: current の candidate receipt を維持し、review priority は人手判断に委ねる
- B: candidate receipt に deterministic priority score / rank / top-priority summary を追加し、dispatch receipt の ready evidence へも反映する
- C: ranking を飛ばして直接 `build_artifact` / apply witness まで接続する

## Decision

**B** を採択。

## Consequences

- `yaoyorozu_worker_patch_candidate_receipt` は
  `target-delta-priority-ranking-v1` を canonical priority profile として持ち、
  candidate ごとの `priority_rank` / `priority_score` / `priority_tier` /
  `priority_reason` を返す
- receipt 自体も `highest_priority_tier` / `highest_priority_score` /
  `ranked_candidate_ids` を持ち、builder apply review に渡す top-priority summary を返す
- `yaoyorozu_worker_dispatch_receipt` の worker `coverage_evidence` と
  `execution_summary` は同じ priority profile と top-priority summary を束縛し、
  no-candidate path でも `none / 0` を deterministic に返す
- unit / integration / schema contract は同じ ranking contract を継続検証する

## Revisit triggers

- patch candidate を `build_artifact` / `sandbox_apply_receipt` /
  `builder_rollback_session` と同一 execution digest で束縛したくなった時
- deterministic priority を diff hunk summary や apply risk witness まで拡張したくなった時
- repo-local subprocess を超えて remote sandbox / external runtime にも
  同じ priority profile を持ち込みたくなった時
