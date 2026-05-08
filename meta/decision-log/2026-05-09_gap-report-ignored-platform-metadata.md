---
date: 2026-05-09
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - docs/07-reference-implementation/README.md
  - evals/continuity/gap_report_scan_receipt.yaml
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: ignored platform metadata を gap-report gate に入れる

## Context

`gap-report` は tracked / untracked generated artifact を検出していたが、
`.gitignore` や global excludes により hidden になった `.DS_Store` / `Thumbs.db`
は `git ls-files --others --exclude-standard` から見えず、all-zero の裏に残り得た。
2026-05-08 の nested platform metadata gate は tracked / untracked path を
basename-aware にしたが、ignored path の scan surface はまだ別に必要だった。

## Options considered

- A: ignored artifact 全体を generated artifact gate に統合する
- B: platform metadata だけを ignored 専用 gate として分離する
- C: cleanup 手順だけを運用で追加し、runtime scanner は据え置く

## Decision

B を採用する。`git:ignored-platform-metadata` を digest-bound scan surface として追加し、
ignored `.DS_Store` / `Thumbs.db` を `ignored_platform_metadata_hits` として
all-zero gate の外へ出す。raw platform metadata payload は読まず、
path manifest digest だけを receipt に束縛する。

## Consequences

- macOS / Windows の platform metadata が `.gitignore` に隠れても automation hygiene で検出できる。
- Python bytecode や test cache はこの専用 gate では対象外にし、unittest 実行後の自然発生物を巻き込まない。
- `.gitignore` は `Thumbs.db` / `**/Thumbs.db` も明示する。

## Revisit Triggers

- ignored build / dist output も gap-report gate に含める必要が出た時
- generated artifact policy を cleanup command receipt 付きに拡張する時
- platform metadata allowlist を fixture directory 単位で導入する時
