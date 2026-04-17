---
date: 2026-04-18
deciders: [yasufumi, codex-council]
related_docs:
  - README.md
  - CLAUDE.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/06-roadmap/milestones.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: reference runtime を同一 repo に置く

## Context

初期方針では OmoikaneOS を設計専用 repo とし、実装は別 repo に分離していた。
しかし今回の指示では、この repo 自体をマインドアップロード OS の実装基盤として前進させ、
1時間ごとの継続改修 automation まで含めて運用することが求められた。

## Options considered

- A: 既存方針を維持し、設計だけを厚くする
- B: 本格実装 repo を別途新設し、この repo は従来どおり設計専用に保つ
- C: この repo に docs/specs/evals と整合した reference runtime を追加する

## Decision

**C** を採択。

## Consequences

- `src/` と `tests/` を reference implementation の正本として扱う
- Builder/Codex は同一 repo の `src/`, `tests/`, `specs/`, `evals/` を更新対象とする
- ただし reference runtime は安全な代理表現に留め、意識成立や人格成立を主張しない
- 本番級の実装や危険な自己改修は、引き続き Guardian と Council の強い制約下に置く

## Revisit triggers

- reference runtime が docs/specs と乖離した時
- 本番実装用に別 repo を切り出す合理性が高まった時
- 倫理境界や不可侵領域の定義が研究進展で更新された時
