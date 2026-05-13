---
date: 2026-05-14
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - evals/continuity/gap_report_scan_receipt.yaml
  - docs/07-reference-implementation/README.md
  - specs/catalog.yaml
  - tests/unit/test_gap_scanner.py
  - tests/integration/test_gap_report_schema_contracts.py
status: decided
---

# Decision: gap-report は stale inventory と catalog consumer を all-zero gate で検出する

## Context

`gap-report --json` は all-zero だったが、repo-local inspection で
`specs/catalog.yaml` の `consumers` に実在しない path が残っていても
report が通過する blind spot があった。同じ class として、eval README は
実ファイルの未掲載だけを検出し、README 側だけに残った stale entry を
検出していなかった。また runnable CLI inventory は root README のみを対象とし、
reference implementation README と `argparse` parser / `main()` dispatch の
対応までは gate に入れていなかった。

## Options considered

- A: catalog の stale consumer 2 件だけを手で修正する
- B: stale consumer、stale eval inventory、reference README CLI inventory、
  parser / dispatch 対応を同じ gap-report gate に入れる
- C: CLI parser / dispatch 対応は別 automation の手動 review に委ねる

## Decision

B を採用する。`GapScanner` は catalog consumer が repo-local path に見える場合に
実在確認し、欠落を `catalog_consumer_reference_hits` として報告する。
eval README inventory は missing と stale の両方向を検出する。
CLI inventory は root README と reference implementation README の両方を読み、
`argparse` subparser と `main()` dispatch handler の両方を持つ command set と照合する。

## Consequences

- stale catalog consumer と stale eval README entry は all-zero completion を止める。
- parser だけ、handler だけ、README だけの CLI command は `inventory_drift_hits` として
  automation-hygiene run の対象になる。
- scan receipt counts は `catalog_consumer_reference_count` を含み、
  public schema と integration test で report count と一致する。
- BioData Transmitter は `body-state-surrogate-input-only` の claim ceiling を維持し、
  主観同一性、意識再現、thought content、完全人格再現の達成主張は追加しない。

## Revisit Triggers

- specs/catalog.yaml の consumer 表現を structured object に移行する時
- CLI dispatch を `if args.command == ...` 以外の table-driven handler に移行する時
