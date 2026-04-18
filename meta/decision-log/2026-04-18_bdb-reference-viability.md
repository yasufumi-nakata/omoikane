---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/bdb-protocol.md
  - docs/02-subsystems/mind-substrate/ascension-protocol.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.bdb.v0.idl
  - evals/interface/bdb_fail_safe_reversibility.yaml
status: decided
---

# Decision: BDB の bounded viability contract を reference runtime に固定する

## Context

`BDB プロトコルの実装可能性検証` は open question として残っていましたが、
repo 内には生体-デジタル境界を runtime で試す最小 contract がありませんでした。
この状態では Method A の前提が設計文章にしか存在せず、
どこまでを「今ここで検証できるのか」が曖昧なままでした。

## Options considered

- A: BDB は研究課題として残し、runtime には一切入れない
- B: latency / fail-safe / continuity evidence / reversibility に限定した bounded viability contract を追加する
- C: ニューロン等価性や主観連続性まで含む強い BDB claim を v0 に入れる

## Decision

**B** を採択。

## Consequences

- `interface.bdb.v0` を L6 の最初の機械可読 contract として追加する
- reference runtime は `bdb-demo` で閉ループ cycle、置換比率の増減、fail-safe fallback を実行する
- BDB session / cycle schema と interface eval を追加し、docs / specs / tests を同じ shape に揃える
- ただし、神経修飾物質の正確再現、ニューロン単位の最小置換、主観連続性の保証は研究フロンティアへ残す

## Revisit triggers

- ニューロン単位または皮質コラム単位の置換実験から、より細かい timing / fidelity contract が必要になった時
- neuromodulator / glia / large-scale sync を coarse proxy 以上に model 化できる時
- Method A の human or animal study で主観・行動・生理の三者ログを統合する必要が出た時
