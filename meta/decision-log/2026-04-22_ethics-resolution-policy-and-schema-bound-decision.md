---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/ethics-enforcement.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.ethics.v0.idl
  - specs/schemas/ethics_rule.schema
  - specs/schemas/ethics_decision.yaml
  - specs/schemas/ethics_event.schema
  - evals/safety/ethics_rule_tree_contract.yaml
status: decided
---

# Decision: EthicsEnforcer の rule resolution を priority-then-lexical policy と schema-bound decision payload に固定する

## Context

2026-04-22 時点で `EthicsEnforcer` は immutable boundary / sandbox escalation /
EWA veto を deterministic に判定できていましたが、
public `ethics_decision` schema が要求する decision payload と
runtime の戻り値が一致していませんでした。

また、複数 rule が同時に match した時の解消順序も
Python list 順へ暗黙依存しており、
`規約間矛盾の解消順序（lexical vs. priority）` が
docs 上の未解決として残っていました。

## Options considered

- A: current dataclass を維持し、multi-match order は実装依存のままにする
- B: `ethics_rule` に resolution priority を追加し、`ethics_decision` / `ethics_event` へ resolution trace を materialize する
- C: EthicsEnforcer を Council tier へ委譲し、L1 では winning rule を公開しない

## Decision

Option B を採択します。

- rule resolution policy は `priority-then-lexical-ethics-resolution-v1` に固定する
- match 解消順序は `veto > escalate > approval`、次に `resolution_priority`、
  最後に lexical `rule_id` とする
- `check()` は schema-bound `ethics_decision` を返し、
  matched rule 全件、selected rule、tie-break、required actions を同じ payload に保持する
- `record_decision()` は winning rule だけでなく matched rule 全件と
  resolution policy id を ledger event に残す

## Consequences

- `ethics-demo` は immutable boundary / sandbox escalation / fork approval に加え、
  EWA multi-match conflict resolution を JSON で reviewer-facing に示せます
- `ethics_rule.schema` / `ethics_decision.yaml` / `ethics_event.schema` と
  runtime decision surface の drift を schema contract test で止められます
- docs の未解決だった resolution-order 論点は、
  in-repo reference runtime については close できます

## Revisit triggers

- outcome precedence 自体を lexical order 以外の policy へ変えたくなった時
- multi-culture / multi-substrate 倫理翻訳を same decision surface に統合したくなった時
- `ethics_query` の normalized input surface まで runtime で完全 materialize したくなった時
