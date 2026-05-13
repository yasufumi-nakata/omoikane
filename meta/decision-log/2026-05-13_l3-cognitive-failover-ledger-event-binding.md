---
date: 2026-05-13
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/reference_os.py
  - evals/cognitive/backend_failover.yaml
  - evals/cognitive/affect_failover.yaml
  - evals/cognitive/attention_failover.yaml
  - evals/cognitive/perception_failover.yaml
  - evals/cognitive/volition_failover.yaml
  - evals/cognitive/imagination_failover.yaml
  - evals/cognitive/language_failover.yaml
  - evals/cognitive/metacognition_failover.yaml
  - tests/integration/test_cli.py
  - tests/integration/test_reference_runtime.py
status: decided
---

# Decision: L3 cognitive failover の ledger event binding を public validation に出す

## Context

`gap-report --json` は all-zero だったが、L3 cognitive failover eval 群は
`ledger_event` を期待している一方で、public demo の `validation` は
主に selected backend と category count だけを返していた。特に
`backend_failover.yaml` の `shift_safe_summary_only` は runtime 内の shift と
ledger payload には存在するが、public validation field として直接固定されていなかった。

## Options considered

- A: eval YAML は narrative evidence として維持し、public demo output は変えない
- B: 各 L3 failover demo の `validation` に ledger event type、category、Guardian signature、
  payload ref binding を出し、reasoning は `shift_safe_summary_only` も直接返す
- C: eval YAML 側から `ledger_event` を削除し、既存 category count だけを期待値にする

## Decision

B を採用する。各 L3 failover demo は append 済み ContinuityLedger event を
`validation.ledger_event` として返し、`cognitive-failover` category、Guardian signature、
CAS payload ref binding も machine-checkable にする。reasoning demo は
既存の `shift_safe` alias を残しつつ、eval 名と一致する
`shift_safe_summary_only` も返す。

## Consequences

- eval YAML の期待値と public CLI / runtime validation が同じ event type を共有する。
- tests は category count だけでなく、`ledger_snapshot[-1].event_type` と public validation の
  event binding を直接確認する。
- BioData Transmitter、主観同一性、意識再現、thought content、完全人格再現の claim ceiling は変更しない。

## Revisit Triggers

- L3 cognitive eval runner が YAML の `expected` を直接実行検証する時
- ContinuityLedger の signature / payload ref 表現を変更する時
