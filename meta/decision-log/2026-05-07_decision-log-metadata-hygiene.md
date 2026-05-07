---
date: 2026-05-07
deciders: [yasufumi, codex-builder]
related_docs:
  - meta/decision-log/README.md
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - evals/continuity/gap_scanner_decision_log_metadata.yaml
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: decision log metadata を gap-report gate に入れる

## Context

`meta/decision-log/README.md` は dated decision log の frontmatter 形式を規定していたが、
`gap-report --json` は README index への掲載有無だけを検査し、
各 decision log の `date`、`deciders`、`related_docs`、`status` 欠落を all-zero gate の外へ
出していなかった。

## Decision

`decision-log-frontmatter-conformance-v1` を gap-report に追加し、
dated decision log が canonical metadata を持たない場合は
`decision_log_metadata_violation_hits` と high-priority
`decision-log-metadata` task を返す。既存の historical log には、本文を変えずに
frontmatter だけを backfill する。

## Consequences

- automation は decision log index が揃っていても metadata 欠落を見落とさない。
- `accepted` は既存 log に合わせて、`decided` / `superseded` と同じ canonical status として
  README に明記する。
- raw decision log payload は scan receipt に保存せず、scan surface digest と violation summary だけを保持する。

## Revisit Triggers

- decision log を YAML 以外の metadata format へ移行する
- decision log README を filesystem から生成する
- `related_docs` を artifact manifest schema へ昇格する
