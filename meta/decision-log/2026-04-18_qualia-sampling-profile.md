---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/README.md
  - docs/02-subsystems/mind-substrate/qualia-buffer.md
  - docs/07-reference-implementation/README.md
  - evals/cognitive/qualia_contract.yaml
  - specs/interfaces/mind.qualia.v0.idl
  - specs/schemas/qualia_tick.schema
status: decided
---

# Decision: QualiaTick の reference sampling profile を固定する

## Context

`meta/open-questions.md` に残っていた
`QualiaTick の高次元埋め込みの次元数と時間粒度` は、
L2 docs では surrogate representation が詳しく書かれている一方で、
reference runtime / schema / CLI / eval は summary と 3 軸の affective 値しか持たず、
どの粒度で qualia surrogate を扱うのかが未定でした。

## Options considered

- A: 研究課題として残し、reference runtime では単純な summary のみを維持する
- B: modality を増やすが、embedding 次元数と sampling window は未定のままにする
- C: reference runtime 専用の固定 profile を決め、schema/IDL/runtime/eval を同期させる

## Decision

**C** を採択。

## Consequences

- reference runtime は `visual / auditory / somatic / interoceptive` の 4 modality を持つ
- 各 modality embedding は 32 次元、1 tick は 250ms の観測窓を代表する
- `QualiaTick` には `modality_salience`, `sensory_embeddings`, `attention_target`,
  `self_awareness`, `lucidity` を含める
- embedding は外部モデル依存ではなく、summary と salience から決定的に作る surrogate vector とする
- canonical qualia encoding 自体は未解決のまま維持し、より高忠実度の profile は将来見直す

## Revisit triggers

- 実測ベースの知覚 encoder を導入し、32 次元では表現不足だと分かった時
- 250ms 窓が粗すぎる、または ledger/privacy コストが高すぎると評価された時
- modality の追加（例: olfactory, vestibular）が必要になった時
