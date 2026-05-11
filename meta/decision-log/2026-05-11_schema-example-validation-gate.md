---
date: 2026-05-11
deciders: [yasufumi, codex-builder]
related_docs:
  - specs/schemas/
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - tests/integration/test_schema_examples.py
status: decided
---

# Decision: schema examples を all-zero gate に含める

## Context

`gap-report --json` は all-zero だったが、`specs/schemas/*.schema` の public
`examples` の一部が、自分自身の JSON Schema に通らない状態だった。
既存の schema contract tests は runtime payload を schema に通していたが、schema file
内部の example payload 全体を横断検証していなかったため、stale example drift を
見逃していた。

## Options considered

- A: 今回失敗した example payload だけを個別修正する
- B: 全 schema example を横断検証する integration test と gap-report gate を追加する
- C: public schema examples は参考扱いに下げ、validation 対象から外す

## Decision

B を採用する。`GapScanner` は `specs/schemas/*.schema` の `example` / `examples` を
repo-local `$ref` 解決後の schema に通し、失敗したものを
`schema_example_validation_hits` として all-zero gate の外へ出す。
同時に integration test で全 schema examples を直接検証する。

## Consequences

- schema example の追加・変更時は、public contract と example payload の drift が
  automation の hard gate で見える。
- raw example payload は gap report に保存せず、path、example label、error summary、
  error count だけを残す。
- stale で複雑な examples は、contract を弱める主張に使わず、valid な public example
  と machine-checkable schema を優先する。
- BioData Transmitter、主観同一性、意識再現、thought content、完全人格再現の
  claim ceiling は変更しない。

## Revisit Triggers

- schema examples を separate fixture directory へ移す時
- external `$ref` resolver や official schema registry を導入する時
