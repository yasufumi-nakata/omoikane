---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/07-reference-implementation/README.md
status: decided
---

# Decision: DesignReader に git-bound delta scan receipt を追加する

## Context

2026-04-20 時点で `DesignReaderService` は
`docs/` / `specs/` の source digest と `design_delta_manifest` を生成できましたが、
実際にどの checkout / HEAD / working tree 差分を根拠に
handoff を組み立てたかは machine-checkable ではありませんでした。

そのため、`build_request` の前段で
「どの docs/spec が HEAD から変わっているか」を runtime が確認したい時でも、
reference runtime 側には digest 列しか残らず、
actual doc diff detector の residual gap が残っていました。

## Options considered

- A: source digest だけを維持し、git-bound delta detection は future work のまま残す
- B: `design_delta_scan_receipt` を追加し、HEAD-bound changed refs と command receipts を出す
- C: DesignReader を cross-repo sync orchestrator まで一気に拡張する

## Decision

- B を採択しました
- `DesignReaderService.scan_repo_delta` を追加し、
  `git rev-parse HEAD` と `git status --short` に束縛された
  `design_delta_scan_receipt` を返します
- receipt は per-ref の
  `baseline/current digest`、`change_status`、`working_tree_state`、
  changed ref counts を持ちます
- `design-reader-demo` は temp git fixture を生成し、
  modified design ref 1 件 + modified spec ref 1 件を
  `delta-detected` receipt として可視化したうえで、
  その receipt を `design_delta_manifest` に束縛します

## Consequences

- DesignReader は「source digest 生成器」だけでなく、
  actual checkout delta detector としても reference runtime 化されます
- `evals/continuity/design_reader_git_delta_scan.yaml` により、
  HEAD-bound changed ref accounting が regression 監視対象に入ります
- residual future work は broad な doc diff 一般論ではなく、
  cross-repo sync orchestration や reviewer/verifier への delta receipt binding に縮小されます

## Revisit triggers

- DesignReader を current checkout だけでなく multi-repo handoff orchestrator に拡張したくなった時
- changed ref ごとの semantic section diff や richer patch planning cue を束縛したくなった時
- delta receipt を Council / Guardian verifier network へ直接 attest したくなった時
