---
status: decided
related:
  - 2026-04-23_gap-report-eval-inventory-drift.md
  - 2026-04-27_catalog-coverage-gap-report.md
---

# Decision: gap-report は非抽象 runtime stub も検出する

## Context

`gap-report --json` は open question、missing file、inventory drift、catalog coverage、
truth-source future work、latest decision-log follow-up を all-zero にできていました。
一方で `src/` の concrete execution path に `raise NotImplementedError` が残った場合、
schema / eval / docs が揃っていても runnable reference runtime の未実装面を見落とす余地がありました。

## Decision

`GapScanner` は `src/omoikane/**/*.py` を AST で読み、
非抽象 path の `raise NotImplementedError` を
`implementation_stub_hits` と `implementation-stub` prioritized task として返す。
`*Backend._*` の abstract hook は concrete backend subclass が担う extension point として除外する。

同時に scheduler の unreachable stale `NotImplementedError` guard は
reference profile の実行可能性エラーへ置き換え、current repo は
`implementation_stub_count=0` を維持する。

## Consequences

- `gap-report --json` は scanner-detected gap が all-zero でも、非抽象 runtime stub が残れば high-priority task を出す。
- `evals/continuity/gap_scanner_implementation_stub_detection.yaml` と unit / integration tests が abstract hook 除外と concrete stub 検出を固定する。
- IntegrityGuardian は release inventory だけでなく implementation stub scan も監査対象に含める。
