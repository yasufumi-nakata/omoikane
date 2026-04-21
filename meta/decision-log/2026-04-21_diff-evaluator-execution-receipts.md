---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: DifferentialEvaluator に actual command execution receipt を束縛する

## Context

2026-04-21 時点の L5 self-construction では `builder-demo` / `rollback-demo` が
parsed baseline / sandbox observation と comparison digest を返していましたが、
`DifferentialEvaluator` 自身は actual eval command 実行の証跡を持っていませんでした。

一方で `builder-live-demo` には temp workspace materialization と actual command execution の
reference surface があり、hidden gap は
「実行系 surface が別 demo にあるだけで、diff eval report には焼き付いていない」点へ縮小していました。

## Options considered

- A: parsed observation のみを維持し、actual command execution は `builder-live-demo` 専任のままにする
- B: `DifferentialEvaluator` report に temp workspace command evidence を `diff_eval_execution_receipt` として束縛する
- C: eval YAML 全体を recursive CLI smoke から全面置換し、`DifferentialEvaluator` 自身が every eval command runner になる

## Decision

- B を採択しました
- `diff_eval_execution_receipt.schema` を追加し、
  `selfctor.diff_eval.v0` が optional execution receipt binding を持つようにします
- `builder-demo` は dedicated execution-binding eval を temp workspace で実行し、
  その command receipt と cleanup status を diff eval report に焼き付けます
- `rollback-demo` も同じ execution-binding eval を live enactment session に同居させ、
  regression path の diff eval report から actual command evidence を辿れるようにします

## Consequences

- diff eval report は parsed observation だけでなく、
  actual temp-workspace command execution と cleanup 完了まで machine-checkable に説明できます
- `builder-live-demo` は依然として full enactment surface の truth source ですが、
  `builder-demo` / `rollback-demo` も execution evidence を report に束縛するため
  hidden gap が 1 段前進します
- builder pipeline continuity eval は
  `selected_eval_count` や `self_modify` ledger count だけでなく、
  execution-bound evidence の有無も見るように更新します

## Revisit triggers

- recursive CLI smoke 依存の continuity eval を全面的に workspace-safe command へ置き換えたくなった時
- `DifferentialEvaluator` 自身が temp workspace の materialization と cleanup まで内包したくなった時
- docs/spec delta や patch target ranking を actual execution plan と直接結合したくなった時
