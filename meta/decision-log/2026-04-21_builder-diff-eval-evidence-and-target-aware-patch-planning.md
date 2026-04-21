---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: builder pipeline を target-aware patch planning と evidence-bound diff eval に寄せる

## Context

2026-04-21 時点の L5 self-construction は `builder-demo` / `builder-live-demo` /
`rollback-demo` により runtime surface 自体は揃っていましたが、
hidden gap が 2 件残っていました。

1. `PatchGeneratorService` は `target_subsystem` や `output_paths` をほぼ見ず、
   常に `builders.py` / `test_builders.py` 向けの固定 descriptor を返していました。
2. `DifferentialEvaluatorService` は `baseline_ref` / `sandbox_ref` の文字列に
   `fail` / `regression` / `rollback-breach` が含まれるかだけで outcome を決めており、
   docs/IDL が約束する「eval suite を実行した結果としての差分評価」からは乖離していました。

`gap-report --json` は all-zero でしたが、これは open question / 欠損ファイル /
placeholder を中心に見る scanner であり、こうした「surface はあるが意味が固定化され過ぎている」
hidden gap は検出しませんでした。

## Options considered

- A: 既存の fixed descriptor / 文字列判定を維持し、runtime surface があることを優先する
- B: `PatchGenerator` を target-aware にし、`DifferentialEvaluator` を parsed evidence binding に上げる
- C: そのまま actual eval command 実行まで `DifferentialEvaluator` に持ち込み、
  `builder-live-demo` と完全統合する

## Decision

- B を採択しました
- `PatchGeneratorService` は `target_subsystem` と `output_paths` から
  primary target file を決め、target-aware な patch summary を返します
- `DifferentialEvaluatorService` は eval ごとの fixed execution profile を持ち、
  baseline / sandbox ref を parsed observation に落として
  `profile_id`、`triggered_rules`、`comparison_digest` を report に束縛します
- `builder-demo` / `rollback-demo` は
  eval report の evidence binding を validation でも確認します

## Consequences

- builder pipeline は「存在する surface」から、
  「どの target をどう触る想定か」「なぜ promote / hold / rollback なのか」を
  machine-checkable に説明できる surface へ進みます
- `evals/continuity/council_output_build_request_pipeline.yaml` と
  `builder_staged_rollout_execution.yaml` の期待値も runtime 実態へ同期されます
- なお `DifferentialEvaluator` 自身が actual eval command を直接実行する段階までは
  まだ進めておらず、その execution loop は引き続き `builder-live-demo` が担います

## Revisit triggers

- `DifferentialEvaluator` 自身に actual eval command runner を持たせたくなった時
- `PatchGenerator` に docs/evals/meta の multi-file planning まで要求したくなった時
- design delta の changed refs を patch target ranking へ直接反映したくなった時
