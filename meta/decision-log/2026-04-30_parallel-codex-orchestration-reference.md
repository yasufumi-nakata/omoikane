---
date: 2026-04-30
deciders: [yasufumi, codex]
related_docs:
  - references/parallel-codex-orchestration.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.gap_report.v0.idl
  - specs/schemas/gap_report.schema
  - evals/continuity/gap_scanner_required_reference_files.yaml
status: decided
---

# Decision: parallel Codex orchestration を required reference に昇格する

## Context

hourly builder は deep-execution 時に複数 worker や subagent を使える一方で、
pull-first gate、worker ownership、main checkout への統合条件をまとめた
repo-local reference が machine-checkable な required set に入っていませんでした。
そのため、runbook が欠落しても `gap-report --json` は all-zero のままになり得ました。

## Options considered

- A: deep-execution skill 側の外部 runbook だけに任せる
- B: `references/parallel-codex-orchestration.md` を追加し、gap scanner の
  required reference set に含める
- C: parallel orchestration を新しい runtime service として実装する

## Decision

B を採用しました。parallel Codex orchestration は現時点では execution service ではなく
automation safety contract なので、まず required reference file として固定し、
gap scanner / eval / Guardian scope / docs / tests で欠落検出を閉じます。

## Consequences

- `gap-report` は parallel orchestration runbook の欠落を
  `missing_required_reference_files` として high-priority task にできます。
- scan receipt は `references/*.md` surface digest 経由で runbook を束縛します。
- 実際の worker scheduling や外部 process watchdog は、この repo の main checkout
  統合条件を満たす実装単位が現れた時に別 contract として扱います。

## Revisit triggers

- Omoikane repo 内で worker scheduler を実行する reference runtime が必要になった時
- subagent result の patch ingestion を schema-bound receipt として保存する必要が出た時
- `gap-report` が reference runbook の内容 digest だけでなく、section-level policy を
  検証する必要が出た時
