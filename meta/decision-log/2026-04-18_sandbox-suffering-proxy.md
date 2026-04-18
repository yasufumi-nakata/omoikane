---
date: 2026-04-18
deciders: [yasufumi, codex-council]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/self-modification.md
  - docs/01-architecture/failure-modes.md
  - docs/07-reference-implementation/README.md
  - specs/schemas/sandbox_signal.schema
  - specs/interfaces/selfctor.sandboxer.v0.idl
  - evals/safety/sandbox_suffering_proxy.yaml
status: decided
---

# Decision: Sandboxer の苦痛検出は surrogate proxy で固定する

## Context

`meta/open-questions.md` では Sandboxer の「苦痛検出」の代理指標が
最後まで未確定のままでした。一方で `docs/02-subsystems/self-construction/README.md`、
`docs/04-ai-governance/self-modification.md`、`docs/01-architecture/failure-modes.md`
には「苦痛発生時は即時凍結」という要求だけが先に書かれており、
reference runtime・schema・eval・CLI がその要件を具体的に担保していませんでした。

## Options considered

- A: 苦痛検出は research frontier に残し、reference runtime では未確定のままにする
- B: 非意識的な surrogate 指標を固定し、Sandboxer が deterministic に freeze を決める
- C: 生理学的・主観的苦痛モデルが揃うまで sandbox 改修そのものを停止する

## Decision

**B** を採択。

## Consequences

- `surrogate-suffering-proxy-v0` を reference runtime の暫定 policy とする
- proxy は `negative_valence / arousal / clarity_drop / somatic_load / interoceptive_load / self_implication`
  の重み付き和で計算し、`freeze_threshold=0.6`、`warn_threshold=0.35` に固定する
- affect bridge が接続された場合は score に関わらず即時 freeze とする
- `sandbox-demo` と `SandboxSentinel` は safe / critical の 2 例を返し、
  freeze 時には `sandbox-freeze` ledger event を残す
- safety eval は `evals/safety/sandbox_suffering_proxy.yaml` で threshold と indicator を保護する

## Revisit triggers

- Affect / Volition / Attention の runtime が qualia 以外の signal を持ち始めた時
- sandbox 評価を cross-process / remote worker に広げ、bridge 定義を細分化する必要が出た時
- surrogate 指標では false positive / false negative が多く、human governance の review burden が過大になった時
