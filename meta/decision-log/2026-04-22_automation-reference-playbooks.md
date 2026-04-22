---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - docs/07-reference-implementation/README.md
  - references/operating-playbook.md
  - references/repo-coverage-checklist.md
  - references/verification-checklist.md
  - src/omoikane/self_construction/gaps.py
status: decided
---

# Decision: automation 前提の repo-local reference playbook を常設し gap-report で監視する

## Context

2026-04-22 時点の hourly builder prompt は
`deep-execution` を前提にしつつ、
repo-local `references/operating-playbook.md` /
`references/repo-coverage-checklist.md` /
`references/verification-checklist.md`
を読む運用を要求していました。

一方この repo には `references/` 自体が無く、
automation は毎回 repo 外 skill 側の一般論から補完するしかありませんでした。
この状態では deep-execution の入口が repo に固定されず、
`gap-report` も automation-blocking な欠落を検出できませんでした。

## Options considered

- A: `references/` は作らず、repo 外 skill prompt を毎回読む運用に留める
- B: repo-local runbook 3 点を常設し、`gap-report` が欠落を high-priority gap として検出する
- C: `references/` を作る代わりに README の一節へ埋め込む

## Decision

Option B を採択します。

- `references/operating-playbook.md` に hourly builder の preflight / triage / closure rule を固定する
- `references/repo-coverage-checklist.md` に gap 選定前の inspection surface を固定する
- `references/verification-checklist.md` に completion 前の検証順序を固定する
- `GapScanner` は上記 3 ファイルを required reference docs として監視し、
  欠落時は `missing-reference-file` を high-priority task として返す

## Consequences

- broad automation は repo 自身の runbook を読んでから gap 選定に入れるようになります
- `gap-report` は truth-source residual だけでなく、
  automation-blocking な reference 欠落も first-class に報告できます
- repo 運用 knowledge が README 一箇所の散文ではなく、
  preflight / coverage / verification に分解された再利用可能な artifact になります

## Revisit triggers

- automation ごとに別 playbook を分岐したくなった時
- `gap-report` に command failure 実績や automation memory health まで統合したくなった時
- repo-local runbook を schema 化して builder request へ直接束縛したくなった時
