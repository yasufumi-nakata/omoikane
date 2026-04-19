---
date: 2026-04-20
deciders: [yasufumi, claude-council, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: builder pipeline を sandbox apply / staged rollout まで reference runtime 化する

## Context

2026-04-20 時点の `builder-demo` は
`build_request -> patch descriptor -> differential eval -> rollout classify` までしか
materialize されておらず、docs に書かれていた
「Mirage Self への適用」「Stage 0/1/2/3 rollout」は docs-only でした。

README future work にも
`generated patch descriptor の actual sandbox apply / staged rollout execution`
が残っており、L5 self-construction surface の次段が明確でした。

## Options considered

- A: descriptor-only の builder demo を維持し、sandbox apply / rollout は future work のまま残す
- B: reference runtime として deterministic sandbox apply receipt と staged rollout session を追加する
- C: そのまま実 workspace への patch apply や real eval 実行まで入れる

## Decision

- B を採択しました
- `SandboxApplyService` と `RolloutPlannerService` を追加し、
  `sandbox_apply_receipt.schema` / `staged_rollout_session.schema` /
  `selfctor.rollout.v0.idl` を定義します
- `builder-demo --json` は
  `build_request -> patch descriptor -> sandbox apply -> differential eval -> rollout classify -> staged rollout execute`
  までを 1 回で可視化します
- 新しい continuity eval と tests で、
  rollback-ready receipt と fixed stage order を machine-checkable にします

## Consequences

- L5 builder contract が docs/specs/runtime/tests/evals まで閉じ、
  hidden future-work gap が 1 段前進します
- `Mirage Self` apply と Stage 0/1/2/3 rollout の reference behavior を
  CLI で直接 smoke できます
- ただし real workspace mutation や実 eval runner 連携はまだ future work です

## Revisit triggers

- 実 filesystem patch apply と rollback を sandbox 上で再現したくなった時
- staged rollout の traffic gate を live telemetry に接続したくなった時
- Guardian gate を外部 verifier network と結合したくなった時
