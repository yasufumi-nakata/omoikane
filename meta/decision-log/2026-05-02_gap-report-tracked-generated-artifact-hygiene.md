---
date: 2026-05-02
status: decided
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
---

# Decision: gap-report は tracked generated artifact も surfacing する

## Context

前段で `git ls-files --others --exclude-standard` 由来の未追跡生成物は
`untracked_generated_artifact_hits` として all-zero gate の外へ出せるようにした。
一方で、`build/`、`artifacts/`、`*.pyc`、`*.egg-info` などが誤って
Git index に入った場合は、未追跡 scan surface では検出できない。

## Decision

`git ls-files` 由来の追跡対象 path manifest を
`git:tracked-generated-artifacts` として digest-bound scan surface に追加し、
生成物 pattern に一致する path を `tracked_generated_artifact_hits` として報告する。
raw artifact payload は読まず、path manifest digest と artifact class だけを残す。

## Consequences

- tracked generated artifact は high-priority task として all-zero gate を止める
- clean repo では count / hits は 0 / [] のままで、scan receipt は追加 surface digest を持つ
- 未追跡生成物 detection とは別 count に分離し、既存の untracked contract を保持する
