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

# Decision: gap-report は latest decision log の gap chain を append-only metadata で triage する

## Context

2026-04-23 時点で `gap-report --json` は latest decision log の
`residual gap` / `unresolved gap` を surfacing できていましたが、
同日内の later decision log が earlier residual を実質的に閉じた場合でも、
earlier 側の bullet をそのまま数えていました。

この状態では Yaoyorozu のように同一日付で gap を連続的に分解・実装する surface で、
hourly builder が current frontier より false positive な historical residual を
先に拾いやすくなっていました。

## Options considered

- A: latest 日付の residual bullet を現状のまま flat に数え続ける
- B: `next_gap_ids` / `closes_next_gaps` を decision log frontmatter に追加し、
  append-only な closure chain を gap-report 側で差し引く
- C: decision log を後から `status: superseded` へ書き換えて whole-log 単位で隠す

## Decision

**B** を採択。

## Consequences

- `gap-report` は latest decision log の `next_gap_ids` / `closes_next_gaps` を読み、
  later log が閉じた earlier gap bullet を `decision_log_residual_hits` から除外する
- `next-stage frontier` bullet は `decision_log_frontier_hits` として別枠で surfacing し、
  hourly builder が closed residual と current frontier を区別しやすくする
- decision log 自体は append-only のまま残しつつ、
  whole-log `superseded` より細かい粒度で gap closure を追跡できる

## Revisit triggers

- decision log gap chain を frontmatter list ではなく
  structured backlog artifact へ昇格したくなった時
- `next-stage frontier` を priority / actionability metadata 付きで
  truth-source residual と統合したくなった時
