---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/trust-management.md
  - docs/02-subsystems/agentic/council-composition.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/trust_score_update_guard.yaml
  - specs/interfaces/agentic.trust.v0.idl
  - specs/schemas/trust_event.schema
  - specs/schemas/trust_snapshot.schema
status: decided
---

# Decision: Trust score の reference update policy を固定する

## Context

`meta/open-questions.md` に残っていた `Trust score 更新アルゴリズムの定式化` は、
docs では trigger と threshold が書かれている一方で、
reference runtime では CouncilMember に固定値を入れているだけでした。
この状態では、YaoyorozuRegistry がどの evidence で trust を上下させるのか、
人間 pin が自動更新より上位なのか、
guardian role がどの条件で成立するのかが検証できません。

## Options considered

- A: trust を概念説明のまま残し、runtime は静的スコアだけにする
- B: global score だけ更新し、per-domain score と human pin は未実装のままにする
- C: deterministic な delta table と threshold gate を固定し、
  schema / IDL / runtime / CLI / eval / docs を同期させる

## Decision

**C** を採択。

## Consequences

- reference runtime は `TrustService(policy_id=reference-v0)` を持つ
- update 式は `raw_delta = base_delta * severity_multiplier * evidence_confidence` に固定する
- `global_score` と `per_domain[domain]` の双方を同じ delta で更新する
- `pinned_by_human = true` の間は event を記録するが `applied_delta = 0` に固定する
- `guardian_role` は `global_score >= 0.99` に加えて human pin を必須とする
- `self_modify_role` は `global_score >= 0.95` と `per_domain.self_modify >= 0.95` の両方を要求する
- `trust-demo` で positive delta, apply gate, cold start, pin freeze を可視化する

## Revisit triggers

- trust を global / domain の単純加算ではなく、長期 decay や Bayesian update へ置き換える必要が出た時
- substrate 跨ぎや multi-Council federation で trust portability を定式化する時
- adversarial collusion や self-trust tampering を検出する別 subsystem が追加された時
