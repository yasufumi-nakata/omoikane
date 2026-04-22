---
date: 2026-04-23
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/07-reference-implementation/README.md
  - specs/interfaces/README.md
  - specs/schemas/README.md
  - src/omoikane/self_construction/gaps.py
status: decided
---

# Decision: gap-report は spec inventory の truth-source drift も fail-closed で拾う

## Context

2026-04-23 時点の `gap-report --json` は all-zero でしたが、
`specs/interfaces/README.md` と `specs/schemas/README.md` の inventory には
実装済み IDL / schema の記載漏れが残っていました。

この状態では hourly builder が truth-source を見ても
どの surface が current inventory に未反映なのか分からず、
all-zero report が「実際に drift が無い」ことを意味しませんでした。

## Options considered

- A: README inventory drift は手動 review の責務として残し、scanner は現状維持する
- B: `gap-report` が spec README inventory と実在 file を突き合わせ、
  drift を high-priority task として返す
- C: README inventory をやめ、catalog だけを truth source に寄せる

## Decision

Option B を採択します。

- `gap-report` は `specs/interfaces/README.md` と `specs/schemas/README.md` について、
  README inventory に無い実在 IDL / schema / YAML を `inventory_drift_hits` として返します
- drift は `prioritized_tasks` の high priority に載せ、
  automation が all-zero を信用できる条件を引き上げます
- あわせて両 README inventory を current tree に同期し、
  current checkout では `inventory_drift_count=0` を維持します

## Consequences

- spec inventory の記載漏れが `gap-report` だけで見えるようになり、
  hourly builder の次候補選定が fail-closed になります
- `specs/interfaces/README.md` / `specs/schemas/README.md` は
  reference runtime の現行 surface 一覧として再び使える状態になります
- future work / next-stage 検出とは別に、
  「実装済み surface が truth-source から落ちている」系の blind spot を塞げます

## Revisit triggers

- README inventory を hand-maintained list ではなく generated manifest に置き換えたくなった時
- docs/02-subsystems 側の inventory drift まで同じ scanner で監視したくなった時
- `inventory_drift_hits` を file 名だけでなく subsystem/category 単位へ構造化したくなった時
