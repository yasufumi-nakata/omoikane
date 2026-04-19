# 2026-04-20 Builder Pipeline Reference Loop

## Context

`docs/07-reference-implementation/README.md` の future work に
`specs/ から runtime への自動生成ループ` が残っていました。
一方で repo には `build_request.yaml` / `build_artifact.yaml` と
`selfctor.patch_generator.v0.idl` / `selfctor.diff_eval.v0.idl` が既にあり、
Council-approved build handoff を受ける L5 surface だけが
reference runtime へ materialize されていませんでした。

さらに `build_request` / `council_output` schema が
`evals/continuity/council_output_build_request_pipeline.yaml` を参照しているのに
実ファイルが存在せず、gap scanner では見えない hidden gap になっていました。

## Decision

- L5 self-construction に `PatchGeneratorService` と `DifferentialEvaluatorService` を追加する
- `builder-demo --json` で `build_request -> patch descriptor -> differential eval -> rollout classify`
  の bounded loop を reference runtime として可視化する
- build pipeline は descriptor-only のままにし、actual sandbox apply / staged rollout execution は future work に残す
- `council_output_build_request_pipeline` eval を追加し、
  Council handoff と immutable boundary guard を machine-checkable にする

## Consequences

- specs に存在していた builder contract が runtime / CLI / eval / docs / tests まで到達した
- `build_request` handoff が `self-modify` ledger chain に結び付いたため、
  L5 改修フローを reference runtime 上で end-to-end に smoke できる
- future work は「specs から runtime」一般論ではなく、
  actual patch apply / staged rollout execution という次段の残件に絞られた
