---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - references/operating-playbook.md
  - docs/07-reference-implementation/README.md
  - src/omoikane/self_construction/gaps.py
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: gap-report は最新 decision log の residual gap も surfacing する

## Context

2026-04-23 時点で `gap-report --json` は truth-source inventory / future-work / open question
を正しく検出できていましたが、recent decision log に残った
`residual gap` / `unresolved gap` の bullet は拾えていませんでした。
そのため truth-source が clean になると、
hourly builder は repo 内に次の durable gap が残っていても
manual log scan なしには候補を見失いやすい状態でした。

## Options considered

- A: gap-report は curated truth-source だけを見て、decision log 残差は人手探索に委ねる
- B: 最新 decision log 日付の `residual gap` / `unresolved gap` を `decision_log_residual_hits` として surfacing する
- C: 全 decision log を自然言語で解析し、長期 backlog 全体を自動優先度付けする

## Decision

**B** を採択。

## Consequences

- `gap-report` は hard blocker と truth-source residual に加えて、
  最新 decision log 日付の residual bullet を `decision_log_residual_hits` /
  `decision_log_residual_count` として返す
- prioritized task には `decision-log-residual` kind を追加し、
  truth-source clean 後の hourly builder が次の durable gap を拾いやすくする
- scan 範囲は最新日付かつ `status != superseded` の log に限定し、
  古い closure 済み residual line の noise を抑える
- residual gap は open question や missing file の代替ではなく、
  次段候補の hint として扱う

## Revisit triggers

- decision log 側に structured `residual_gap` field や explicit backlog metadata を追加した時
- 最新日付だけでは stale backlog を取りこぼすと分かり、
  rolling window や supersession chain を導入したくなった時
- decision-log residual と truth-source residual を同一 priority model へ統合したくなった時
