---
date: 2026-04-30
deciders: [codex, ethics-guardian]
related_docs:
  - docs/00-philosophy/ethics.md
  - docs/02-subsystems/kernel/ethics-enforcement.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.ethics.v0.idl
  - specs/schemas/ethics_query.yaml
  - evals/safety/ethics_rule_tree_contract.yaml
status: decided
---

# Decision: 本人同意の真正性 guard を EthicsEnforcer の deterministic rule tree に昇格する

## Context

`gap-report --json` は all-zero でしたが、`docs/02-subsystems/kernel/ethics-enforcement.md`
には「本人同意」の真正性検証、特に強制下での同意検出が runtime contract として
まだ固定されていませんでした。本人同意を単なる string flag として扱うと、
不連続・memory edit・fork などの consent-bound action が強制や誘導を含む consent を
正当な入力として受け入れる余地が残ります。

## Options considered

- A: 引き続き人間社会 governance の研究課題としてのみ残す
- B: Consent workflow 専用 service を新設する
- C: 既存 EthicsEnforcer の rule tree に coercion veto と authenticity escalation を追加する

## Decision

C を採用しました。`A9-consent-coercion-veto` は
`requires_consent=true` かつ `coercion_suspected=true` の action を fail-closed veto します。
`A10-consent-authenticity-attestation` は coercion が未検出でも
`self_signed` / `independent_witness_signed` / `duress_screen_passed` のいずれかが欠ける場合に
Council / EthicsGuardian review へ escalate します。

## Consequences

- Consent-bound action は self signature、独立 witness、duress screen の 3 点を
  machine-checkable evidence として持つ必要があります。
- Coercion / duress の疑いは Council の便宜判断より強く、即時 veto されます。
- `ethics-demo` は immutable boundary、sandbox escalation、fork approval、consent authenticity、
  EWA conflict resolution を同じ schema-bound decision/event surface で示します。
- raw consent payload は保持せず、decision / ethics event / ledger category に digest-ready な
  refs と rule ids だけを残します。

## Revisit triggers

- Consent authenticity を外部 verifier network や jurisdiction-specific consent registry に
  接続する必要が出た時
- duress screen の証跡形式を `ethics_query` とは独立した public schema に昇格する時
- 多文化・多 substrate 環境で consent validity の翻訳 policy を runtime contract にする時
