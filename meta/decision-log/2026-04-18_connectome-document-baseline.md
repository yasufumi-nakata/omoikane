---
date: 2026-04-18
deciders: [yasufumi, codex-council]
related_docs:
  - docs/03-protocols/connectome-format.md
  - docs/02-subsystems/mind-substrate/README.md
  - docs/07-reference-implementation/README.md
  - specs/schemas/connectome_document.schema
status: decided
---

# Decision: connectome の canonical document を先に固定する

## Context

`docs/03-protocols/connectome-format.md` には概念設計が存在した一方で、
reference runtime が参照できる machine-readable schema は未作成でした。
この欠落により、L2 connectome を docs/specs/src/tests/evals の横断対象として
前進させにくい状態でした。

## Options considered

- A: connectome は研究段階として据え置き、schema 化を後回しにする
- B: node/edge の最小 canonical document だけ先に固定し、reference runtime で生成・検証可能にする
- C: memory crystal や episodic stream まで含めた L2 全体 schema を一気に定義する

## Decision

**B** を採択。

## Consequences

- `specs/schemas/connectome_document.schema` を L2 connectome の正本 schema とする
- reference runtime は `connectome-demo` で最小 snapshot を生成し、edge/hierarchy 参照整合を自前検証する
- `invariants` は map ではなく object 配列で保持し、diff しやすい canonical shape を優先する
- `delay_ms` は物理遅延そのものではなく、機能単位へ正規化した reference 指標として扱う

## Revisit triggers

- SubstrateAdapter の IDL が確定し、物理表現との変換境界を厳密化する時
- MemoryCrystal / EpisodicStream と横断する複合 snapshot を導入する時
- connectome の量子相関や高密度圧縮表現を schema に反映する必要が出た時
