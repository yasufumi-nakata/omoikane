# 2026-04-19 AscensionScheduler Governance Artifacts

## Decision

- `AscensionScheduler` の `AscensionPlan` / `ScheduleHandle` に
  governance artifact bundle を追加し、
  `self_consent` / `ethics` / `council` / `legal` / `witness` ref を
  reference runtime の固定 profile として束縛する。
- artifact bundle は `governance_artifact_digest` で要約し、
  schedule history の全 transition payload に digest と bundle ref を残す。
- witness quorum は reference runtime で 2 件に固定し、
  plan validation は witness 不足または digest 不一致を reject する。

## Rationale

- `docs/07-reference-implementation/README.md` に残っていた
  clinical/legal consent artifact 接続 gap を、
  docs ではなく runtime / schema / test で具体化する必要があった。
- Method A/B/C の execution 面は既に fixed profile 化されていたため、
  次の durable gap は「誰の consent / attest / witness に支えられているか」を
  machine-readable に持たせることだった。
- artifact の真正性そのものは repo 外で管理される前提でも、
  stable ref と digest を scheduler surface に残せば
  continuity history と eval で drift を検出できる。

## Consequences

- `scheduler-demo` は Method A/B/C の stage machine に加えて、
  governance artifact bundle と digest binding まで一度に可視化できる。
- `ascension_plan.schema` / `schedule_handle.schema` /
  `kernel.scheduler.v0.idl` が bundle ref と witness quorum を明示し、
  `evals/continuity/scheduler_governance_artifacts.yaml` が追加された。
- 残課題は artifact ref の freshness / revocation / external proof verification であり、
  repo 内 reference runtime は stable ref と continuity-safe digest 保持までを責務とする。
