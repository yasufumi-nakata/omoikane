---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/self-construction/README.md
  - docs/04-ai-governance/codex-as-builder.md
  - docs/04-ai-governance/self-modification.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/selfctor.design_reader.v0.idl
  - specs/interfaces/selfctor.patch_generator.v0.idl
  - specs/schemas/design_delta_manifest.schema
  - specs/schemas/build_request.yaml
  - evals/continuity/design_reader_handoff.yaml
  - evals/continuity/council_output_build_request_pipeline.yaml
status: decided
---

# Decision: DesignReader planning cue と builder multi-file patch plan を fail-closed に束縛する

## Context

2026-04-22 時点で `DesignReaderService` は
git-bound `design_delta_scan_receipt` と `design_delta_manifest` を返せましたが、
changed ref の内部でどの section が変わったか、
その変化を runtime / tests / evals / docs / meta のどこへ反映すべきかは
machine-checkable に束縛されていませんでした。

そのため `PatchGeneratorService` は
build request を受けても実質的には固定少数ファイルへ寄せた patch plan を返しやすく、
manifest が blocked / invalid でも downstream handoff を fail-closed に止める境界が弱いままでした。

## Options considered

- A: `design_delta_manifest` は source digest 中心のまま維持し、multi-file patch planning は builder の暗黙知に任せる
- B: `DesignReader` が section-level delta から `planning_cues` を出し、`PatchGenerator` がそれを approved output path に解決する multi-file patch plan を返す
- C: DesignReader を直接 patch generator に統合し、manifest/build_request の段を縮退させる

## Decision

- B を採択しました
- `DesignReaderService.scan_repo_delta` は `changed_section_count` と `section_changes` を必須化し、
  changed section digest を downstream planning に引き渡します
- `DesignReaderService.read_design_delta` は
  `runtime-source` / `test-coverage` / `docs-sync` / `meta-decision-log`
  の `planning_cues` を emit し、
  `prepare_build_request` は validation 成功時のみ fail-closed で
  `eval-sync` cue を付与した `build_request` を emit します
- `PatchGeneratorService` は `planning_cues` を approved output path に解決し、
  runtime / tests / evals / docs / meta/decision-log にまたがる
  multi-file patch descriptor 群を返します
- `builder-live-demo` と `rollback-demo` も
  同じ 5-file scope を materialize / reverse-apply できる前提へ揃えます

## Consequences

- L5 builder pipeline は
  「digest 付き handoff」から
  「section-level delta と planning cue を持つ fail-closed handoff」へ昇格しました
- `council_output_build_request_pipeline`、`builder_staged_rollout_execution`、
  `builder_live_enactment_execution`、`builder_rollback_execution`
  の eval expectation は multi-file patch plan を前提に監視されます
- residual future work は generic な patch planning 不足ではなく、
  cue priority の最適化や richer semantic diff、reviewer/verifier への cue attestation に縮小されます

## Revisit triggers

- `planning_cues` を docs/spec section label だけでなく semantic issue cluster まで拡張したくなった時
- multi-file patch plan を 5 file 上限より広い staged batch に分割したくなった時
- `DesignReader` の cue 自体を Council / Guardian verifier network へ attest したくなった時
