---
date: 2026-05-08
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - tests/unit/test_gap_scanner.py
  - docs/07-reference-implementation/README.md
  - specs/schemas/gap_report.schema
status: decided
---

# Decision: nested platform metadata を generated artifact gate で拾う

## Context

`gap-report` は `.DS_Store` / `Thumbs.db` を generated artifact gate の対象として
docs / schema に明記していた。一方で runtime classifier は full path だけを
`GENERATED_ARTIFACT_FILENAMES` と照合していたため、
`tests/integration/.DS_Store` や `docs/Thumbs.db` のような nested platform metadata を
basename で検出できなかった。

## Options considered

- A: root 直下の `.DS_Store` / `Thumbs.db` だけを gate 対象に据え置く
- B: generated artifact filename は basename で照合し、nested platform metadata も gate 対象にする
- C: platform metadata 専用の別 scanner を増やす

## Decision

B を採用する。generated artifact filename の照合と artifact class 判定を basename-aware にし、
nested `.DS_Store` / `Thumbs.db` が tracked / untracked のどちらでも
`platform-metadata-output` として all-zero gate の外へ出るように固定する。

## Consequences

- repo 深部に残った macOS / Windows platform metadata を automation hygiene で検出できる。
- root 直下の既存 generated artifact 判定は維持される。
- raw platform metadata payload は読まず、path manifest digest だけを保持する。

## Revisit Triggers

- platform metadata の allowlist を repo-local fixture に限定する必要が出た時
- generated artifact classifier を filesystem metadata aware に拡張する時
- generated artifact path manifest を schema-generated inventory へ移す時
