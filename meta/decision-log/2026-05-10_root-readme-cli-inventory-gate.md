---
date: 2026-05-10
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - evals/continuity/gap_report_scan_receipt.yaml
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: root README CLI inventory を gap-report gate に入れる

## Context

`gap-report --json` は all-zero だったが、root `README.md` の「すぐ動かせるもの」は
`src/omoikane/cli.py` の parser 定義より古く、reference implementation README にだけ
新しい runnable commands が列挙されていた。これは runtime claim の不足ではなく、
automation が見る truth source の command inventory drift である。

## Options considered

- A: root README の command list だけを手動同期する
- B: root README の runnable CLI command inventory を `gap-report` の existing `inventory_drift_hits` に含める
- C: root README は抜粋として扱い、reference implementation README のみを正本にする

## Decision

B を採用する。`src/omoikane/cli.py` の `add_parser` command names を AST で読み、
root `README.md` の top-level runnable command bullets に各 command が少なくとも 1 回
現れることを `inventory_drift_hits` で検査する。同じ gate で stale command name と
full unittest command の欠落も検出する。

## Consequences

- root README の runnable command list が古くなると all-zero gate の外へ出る。
- optional argument 付きの example は同じ command name として扱い、重複 variant は許容する。
- BioData Transmitter の claim ceiling や research frontier status は変更しない。

## Revisit Triggers

- CLI command inventory を parser AST ではなく argparse 実行結果へ束縛する必要が出た時
- root README の command list を意図的な抜粋へ戻す判断が明示された時
