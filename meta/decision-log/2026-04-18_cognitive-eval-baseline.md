---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/cognitive/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
  - evals/README.md
  - evals/cognitive/README.md
status: decided
---

# Decision: cognitive eval は qualia/self-model gateway から開始する

## Context

`evals/cognitive/` は空のままで、`specs/catalog.yaml` でも次優先として残っていた。
一方、reference runtime に存在する cognitive 近傍の実装は `QualiaBuffer` と
`SelfModelMonitor` であり、docs 上の Builder プロトコルも実在しない
`reasoning_basic.yaml` を例示していた。

## Options considered

- A: L3 Reasoning backend が実装されるまで cognitive eval を空のまま維持する
- B: 仮の reasoning eval を docs だけから起こし、runtime 不在のまま先行定義する
- C: 現在の runtime が提供する qualia/self-model gateway を cognitive baseline として先に固定する

## Decision

**C** を採択。

## Consequences

- `evals/cognitive/qualia_contract.yaml` と
  `evals/cognitive/self_model_abrupt_change.yaml` を baseline とする
- `gap-report` は空の eval surface を検出し、同様の空洞を今後も見逃さない
- Builder 向けの build request 例は、存在する docs/specs/evals にのみ依存させる

## Revisit triggers

- L3 Reasoning / Affect / Attention backend が reference runtime に入った時
- cognitive eval が gateway だけでは不十分で、cross-component scenario が必要になった時
- qualia/self-model の schema が大きく更新された時
