---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/amendment-protocol.md
  - docs/05-research-frontiers/governance.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/amendment_constitutional_freeze.yaml
  - specs/interfaces/governance.amendment.v0.idl
  - specs/schemas/amendment_proposal.schema
  - specs/schemas/amendment_decision.schema
status: decided
---

# Decision: 規約改正フローは tier 固定ルールで freeze / guarded rollout へ分岐させる

## Context

`meta/open-questions.md` に残っていた `規約改正フローの実体` は、
docs には概念がある一方で reference runtime・CLI・eval に deterministic な apply 条件がありませんでした。
特に T-Core を「人間レビュー待ちのまま凍結する」のか、
あるいは Council 合意で局所的に通してしまうのかが未固定でした。

## Options considered

- A: 改正フローは研究課題のまま残し、runtime では扱わない
- B: すべての tier を Council + Guardian のみで処理し、人間 review は docs だけに残す
- C: tier ごとに allow/apply 条件を固定し、T-Core は常時 freeze、下位 tier だけ guarded rollout を許可する

## Decision

**C** を採択。

## Consequences

- `governance.amendment.v0` と `amendment-demo` を追加し、proposal -> attest -> apply/freeze を機械可読化する
- `T-Core` は signature が揃っていても `allow_apply=false` / `status=frozen` に固定する
- `T-Kernel` は `Council unanimous + self consent + guardian attest + human reviewers >= 2` を満たした場合のみ `dark-launch` に進める
- `T-Operational` は `Council majority-or-better + guardian attest` を満たした場合のみ `5pct` rollout に進める
- `T-Cosmetic` は DesignArchitect attest のみで即時適用できるが、reference runtime では demo 対象外とする

## Revisit triggers

- 外部 human governance reviewer の実体と証跡フォーマットを repo 内へ取り込みたくなった時
- Guardian oversight channel を実装し、amendment attest と reviewer breach を連結したくなった時
- T-Kernel の rollout stage を `dark-launch` 以外へ変えるだけの運用 evidence が溜まった時
