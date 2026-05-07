---
date: 2026-05-02
status: decided
closes_next_gaps:
  - gap-report-decision-log-index-inventory
deciders: [yasufumi, codex-builder]
related_docs:
  - meta/decision-log/README.md
  - meta/decision-log/YYYY-MM-DD_*.md
---

# Decision: gap-report は decision-log README index drift も監査する

## Context

`meta/decision-log/README.md` は既存ログ index として機能しているが、
実ファイルとの差分は `gap-report` の all-zero gate に入っていなかった。
そのため新規 decision log が追加されても README index が古いまま通過できた。

## Decision

`gap-report` は `meta/decision-log/README.md` と
`meta/decision-log/YYYY-MM-DD_*.md` の実ファイル集合を照合し、
未掲載 log と stale link を `decision_log_index_inventory_hits` として返す。
count は scan receipt の all-zero 判定にも含める。

## Consequences

- decision-log index drift は high-priority task として completion gate を止める
- append-only decision chain を README から辿れる状態を automation が検証できる
- scan receipt は raw decision log payload ではなく既存 scan surface digest に束縛される

## Revisit triggers

- decision-log index を README ではなく generated manifest へ移す時
- decision log を日付 prefix 以外の structured identifier に移行する時
