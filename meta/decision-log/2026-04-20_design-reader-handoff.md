---
date: 2026-04-20
deciders: [yasufumi, claude-council, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: DesignReader を builder pipeline の入口 handoff として reference runtime 化する

## Context

2026-04-20 時点の L5 self-construction は
`PatchGenerator` 以降の surface は runtime 化されていた一方、
docs の主要モジュールに明記されていた `DesignReader` は
`src/omoikane/self_construction/` に実体がありませんでした。

そのため、builder pipeline は `build_request` を前提にしているにもかかわらず、
どの docs/specs を根拠にその handoff が組み立てられたか、
どの docs を同期対象として固定したか、
source digest を何に束縛したかが machine-checkable ではありませんでした。

## Options considered

- A: `DesignReader` を docs-only のまま維持し、builder pipeline は既存 `build_request` 直入力を続ける
- B: `DesignReaderService` / `design_delta_manifest` / `design-reader-demo` を追加し、`docs/specs -> build_request` handoff を reference runtime 化する
- C: DesignReader を full diff engine として実装し、実際の doc mutation 検出まで同時に入れる

## Decision

- B を採択しました
- `selfctor.design_reader.v0` / `design_delta_manifest.schema` / `design_reader_handoff.yaml` / `design-reader-demo` を追加します
- `build_request` は `design_delta_ref` / `design_delta_digest` / `must_sync_docs` を必須にし、
  PatchGenerator は DesignReader handoff が無い request を reject します
- `builder-demo` / `builder-live-demo` / `rollback-demo` はすべて
  DesignReader handoff から build_request を起こす形へ更新します

## Consequences

- L5 self-construction の docs-only だった入口が
  runtime / CLI / schema / IDL / eval / tests / docs / agent config まで閉じます
- builder pipeline は「何を根拠に emit された request か」を
  `design_delta_manifest` と digest で追跡できます
- ただし実 doc diff 監視や cross-repo sync orchestration は
  依然 future work です

## Revisit triggers

- DesignReader を actual doc diff detector として昇格したくなった時
- must_sync_docs を README や agents/ まで自動拡張したくなった時
- design delta manifest を reviewer / verifier network へ束縛したくなった時
