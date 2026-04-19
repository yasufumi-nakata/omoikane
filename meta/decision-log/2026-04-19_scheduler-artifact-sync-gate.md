# 2026-04-19 AscensionScheduler Artifact Sync Gate

## Decision

- `AscensionScheduler` の `ScheduleHandle` に `artifact_sync` snapshot を追加し、
  core governance artifact bundle
  (`self_consent` / `ethics` / `council` / `legal` / `artifact_bundle`)
  の external proof 状態を `current / stale / revoked` で保持する。
- Method A の `active-handoff`、Method B の `authority-handoff`、
  Method C の `scan-commit` を protected handoff stage とし、
  `current` bundle なしでは stage を開かない。
- `stale` snapshot は scheduler を pause して refresh-required とし、
  `revoked` snapshot は fail-closed で schedule を停止する。

## Rationale

- `docs/07-reference-implementation/README.md` の future work に残っていた
  artifact freshness / revocation / external sync gap を、
  docs-only の TODO ではなく runtime / CLI / schema / eval まで materialize する必要があった。
- artifact ref と digest の束縛だけでは、
  実際に handoff 前に freshness を再確認したか、revocation を止められるかが
  machine-checkable ではなかった。
- protected handoff stage の直前に current bundle を必須化すれば、
  Method A/B/C の安全境界を壊さずに external proof drift を明示的に扱える。

## Consequences

- `scheduler-demo` は order / timeout / substrate signal に加え、
  current sync gate、stale pause、revoked fail-closed を一度に可視化する。
- `kernel.scheduler.v0.idl`・`schedule_handle.schema`・
  `governance_artifact_sync.schema`・`evals/continuity/scheduler_artifact_sync.yaml`
  が追加され、`artifact_sync` が handle validation に含まれる。
- 残課題は verifier 自体の真正性、root-of-trust rotation、
  実在外部システムとの証跡同期であり、reference runtime では snapshot binding までを責務とする。
