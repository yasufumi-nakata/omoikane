---
date: 2026-05-09
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - docs/07-reference-implementation/README.md
  - evals/continuity/gap_scanner_ignored_generated_artifact_hygiene.yaml
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: ignored generated artifacts を gap-report gate に入れる

## Context

2026-05-09 の ignored platform metadata gate は `.DS_Store` / `Thumbs.db`
を `.gitignore` 越しに検出できるようにした。一方で、この checkout には
`build/`、`dist/`、`*.egg-info` の ignored packaging output が残っており、
`git status --short` と `gap-report --json` の all-zero からは見えなかった。

## Options considered

- A: ignored artifact 全体を gate に入れる
- B: build / dist / egg-info / patch / coverage output だけを ignored generated artifact として gate に入れる
- C: cleanup 手順だけを運用で追加し、runtime scanner は据え置く

## Decision

B を採用する。`git:ignored-generated-artifacts` を digest-bound scan surface として追加し、
ignored build / dist / egg-info / patch / coverage output を
`ignored_generated_artifact_hits` として all-zero gate の外へ出す。
unittest 実行後に自然発生する `__pycache__/` と `.pytest_cache/` はこの ignored-only gate
から除外し、raw artifact payload は読まず path manifest digest だけを保持する。

## Consequences

- release / package output が `.gitignore` に隠れても automation hygiene で検出できる。
- normal unittest 後の bytecode / test cache は no-op watch を妨げない。
- existing ignored build / dist / egg-info output は cleanup されてから all-zero gate を通す。

## Revisit Triggers

- ignored cache output も all-zero gate に入れる必要が出た時
- packaging output cleanup を command receipt として gap-report に束縛する時
- release artifact directory を fixture として allowlist する必要が出た時
