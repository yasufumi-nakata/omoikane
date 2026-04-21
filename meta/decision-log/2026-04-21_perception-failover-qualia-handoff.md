# 2026-04-21 Perception Failover Qualia Handoff

deciders: [yasufumi, codex-builder]
context:
  - docs/02-subsystems/cognitive/README.md
  - docs/07-reference-implementation/README.md
  - specs/catalog.yaml
  - evals/cognitive/README.md

# Decision: L3 Perception を qualia-bound failover surface として reference runtime 化する

## なぜ必要か

2026-04-21 時点で `docs/02-subsystems/cognitive/README.md` は
`Perception` を L3 Cognitive Services の先頭に置いていましたが、
runtime / schema / IDL / eval / CLI / tests には対応 surface が存在しませんでした。

このままでは `Perception -> Attention -> QualiaBuffer` の前段が
docs 上だけの暗黙前提になり、
`gap-report --json` が clean でも L3 cognitive contract に
1 つだけ空白が残る状態でした。

## 選択肢

- A: `Perception` は docs-only のまま残し、既存 `QualiaBuffer` を gateway として扱い続ける
- B: `PerceptionService` を追加し、bounded scene summary と qualia handoff を repo 内 contract として固定する
- C: 実画像/音声 encoder や heavy external model まで含む perception stack を一気に持ち込む

## 決定

- B を採用します。
- `salience_encoder_v1 -> continuity_projection_v1` の single-switch failover を持つ
  `bounded-perception-failover-v1` を reference profile に固定します。
- output は `perception_frame` / `perception_shift` に限定し、
  `qualia://tick/<id>` への handoff と safe scene set
  (`guardian-review-scene`, `continuity-hold`, `sandbox-stabilization`) を必須にします。
- raw sensory payload や embedding は ledger-safe shift に持ち込まず、
  repo 内では scene summary と body coherence の bounded contract までを扱います。

## 影響

- `perception-demo --json` が baseline / failover の両方を smoke できるようになります。
- `cognitive.perception.v0`、schema、eval、docs、tests が同じ contract を共有します。
- `docs/07-reference-implementation/README.md` と `specs/catalog.yaml` に
  `Perception` を first-class L3 surface として載せられます。

## 残すもの

- actual CV / vision-language / neuromorphic encoder の導入
- richer cross-modal scene graphs や long-horizon perception memory
