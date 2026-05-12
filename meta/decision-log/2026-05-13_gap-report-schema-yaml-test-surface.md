---
date: 2026-05-13
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/self_construction/gaps.py
  - specs/schemas/gap_report.schema
  - specs/interfaces/selfctor.gap_report.v0.idl
  - docs/07-reference-implementation/README.md
  - tests/integration/test_schema_examples.py
  - tests/integration/test_gap_report_schema_contracts.py
  - tests/unit/test_gap_scanner.py
status: decided
---

# Decision: YAML schema examples と tests surface を gap receipt に含める

## Context

`gap-report --json` は all-zero だったが、schema inventory と catalog coverage は
`specs/schemas/*.yaml` を扱う一方で、schema example validation は
`specs/schemas/*.schema` だけを検証していた。また scan receipt の digest-bound
surface は runtime と specs には強いが、`tests/**/*.py` 自体を含んでいなかった。
このため、YAML schema examples や test contract の変更が automation gate の
source surface evidence から外れる可能性があった。

## Options considered

- A: `.schema` のみを public example validation の対象として維持する
- B: `.schema` と `.yaml` の両方を同じ validation path に通し、`tests/**/*.py` も
  scan receipt surface に含める
- C: YAML schema examples は separate fixture へ移してから後続 run で扱う

## Decision

B を採用する。`GapScanner` は `specs/schemas/*.schema` と
`specs/schemas/*.yaml` の `example` / `examples` を同じ repo-local `$ref`
resolution と JSON Schema validation に通す。scan receipt は `tests/**/*.py` を
source surface digest に含め、test contract drift を automation gate の evidence
から外さない。

## Consequences

- YAML schema examples の stale contract は `schema_example_validation_hits` として
  all-zero completion を止める。
- scan receipt の surface manifest は runtime/spec/eval/docs/meta だけでなく
  test contract の変更にも digest-bound evidence を持つ。
- raw schema example payload と raw test payload は gap report に保存しない。
- BioData Transmitter、主観同一性、意識再現、thought content、完全人格再現の
  claim ceiling は変更しない。

## Revisit Triggers

- schema examples を dedicated fixture directory へ移す時
- test suite を repo 外 package へ分離する時
