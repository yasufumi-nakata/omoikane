---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ascension-scheduler.md
  - specs/interfaces/kernel.scheduler.v0.idl
  - specs/schemas/scheduler_execution_receipt.schema
  - evals/continuity/scheduler_execution_receipt.yaml
  - tests/integration/test_scheduler_schema_contracts.py
status: decided
---

# Decision: scheduler_execution_receipt の public schema は非該当 gate を JSON null で表す

## Context

2026-04-22 時点で `AscensionScheduler.compile_execution_receipt()` は
Method A / C や non-live scenario で
`broker_handoff_status=None`、
`verifier_connectivity_status=None` を返していました。

runtime の `validate_execution_receipt()` と unit test はこの contract を前提にしていましたが、
public `scheduler_execution_receipt.schema` は enum に文字列 `"null"` を列挙しており、
実際の JSON `null` を reject していました。

この状態では `scheduler-demo` の reviewer-facing receipt が
internal validation では通る一方、public schema validation では fail し、
machine-checkable closure が破れていました。

## Decision

public schema を runtime contract に再同期し、
`broker_handoff_status` / `verifier_connectivity_status` の非該当値は
文字列 sentinel ではなく JSON `null` として扱います。

併せて次を追加します。

- IDL / subsystem doc / eval expectation で nullable contract を明示する
- `scheduler-demo` の Method A / A-live / A-cancel / B / C execution receipt と
  Method B handoff receipt を public schema に直接当てる integration test を追加する

## Consequences

- Method A / C / cancel scenario の execution receipt も
  public schema に対してそのまま validate できます
- live verifier や Method B handoff が存在しない scenario を
  sentinel string なしで fail-closed に表現できます
- 今後の scheduler surface 拡張でも
  reviewer-facing schema drift を integration test で止められます

## Revisit triggers

- execution receipt に別の nullable gate status を追加する時
- public schema を JSON Schema 以外の typed contract へ二重出力する時
- scheduler execution receipt を external attestation artifact と結合したくなった時
