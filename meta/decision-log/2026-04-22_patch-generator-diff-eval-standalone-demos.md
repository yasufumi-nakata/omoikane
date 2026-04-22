---
date: 2026-04-22
deciders: [yasufumi, codex]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.patch_generator.v0.idl
  - specs/interfaces/selfctor.diff_eval.v0.idl
  - evals/continuity/patch_generator_direct_contract.yaml
  - evals/continuity/diff_evaluator_direct_contract.yaml
status: decided
---

# Decision: PatchGenerator と DifferentialEvaluator を standalone demo として露出する

## Context

`builder-demo` は L5 self-construction の end-to-end loop を 1 本で確認できますが、
`PatchGeneratorService` と `DifferentialEvaluatorService` 自体は
builder pipeline の内部に埋もれており、automation が
「patch descriptor の direct contract を見たい」
「parsed A/B evidence と classify_rollout を単独で検証したい」
という粒度で surface を選べませんでした。

その結果、spec/runtime/eval は存在していても、
サービス単位の reference runtime entrypoint と smoke eval が不足していました。

## Options considered

- A: `builder-demo` のみを維持し、個別 service の確認は unit test と手読みに委ねる
- B: `patch-generator-demo` と `diff-eval-demo` を追加し、ready/blocked と promote/hold/rollback を direct contract として固定する
- C: builder pipeline をさらに細かい micro-service CLI に分割し、既存 composite demo を縮小する

## Decision

B を採択する。

`patch-generator-demo` は design-backed build request から
planning-cue aligned な ready artifact を生成しつつ、
workspace escape・immutable boundary 欠落・planning cue 欠如を含む blocked request を
fail-closed に列挙する direct surface とします。

`diff-eval-demo` は parsed baseline/sandbox observation、
temp-workspace command evidence に束縛された `diff_eval_execution_receipt`、
および `promote` / `hold` / `rollback` の分類を単独で可視化する direct surface とします。

## Consequences

- `builder-demo` を開かなくても、PatchGenerator と DifferentialEvaluator の contract を個別に JSON で監査できます
- automation は「patch descriptor planning を見たい run」と
  「A/B evidence classification を見たい run」を分離して選べます
- self-construction の CLI / docs / eval / tests が 2 surface 分だけ増えます
- composite builder loop は維持されるため、standalone demo と end-to-end demo の双方を併用できます

## Revisit triggers

- PatchGenerator に file grouping / patch dependency DAG のような別 contract が追加された時
- DifferentialEvaluator が single A/B classify を超えて matrix compare や weighted gating を持つ時
- self-construction CLI が過密になり、service grouping や namespace 再編が必要になった時
