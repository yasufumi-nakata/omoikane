# 2026-04-19 AscensionScheduler Method B/C Profiles

## Decision

- `AscensionScheduler` の reference runtime を Method A 専用から、
  Method B / C を含む fixed-profile executor へ拡張する。
- Method B は `shadow-sync -> dual-channel-review -> authority-handoff -> bio-retirement`
  を固定 sequence とし、degraded substrate signal は pause、
  critical substrate signal は `dual-channel-review` への rollback として扱う。
- Method C は `consent-lock -> scan-commit -> activation-review`
  を固定 sequence とし、`scan-commit` 開始後は rollback target を持たず、
  critical substrate signal で fail-closed する。
- `kernel.scheduler.v0` と `scheduler-demo` は
  substrate failover hook を first-class surface として公開する。

## Rationale

- `docs/07-reference-implementation/README.md` と
  `2026-04-19_ascension-scheduler-reference-runtime.md` が共通して
  Method B/C execution 面を大きな残課題として残していた。
- Method B/C を docs-only のままにすると、Ascension protocol の
  reversible boundary と fail-closed boundary が machine-readable にならない。
- SubstrateBroker 由来の signal を scheduler 内で pause / rollback / fail に
  正規化すると、Method ごとの可逆性境界を unit test と eval で固定しやすい。

## Consequences

- `scheduler-demo` 1 回で Method A timeout rollback、
  Method B reversible failover、Method C fail-closed を smoke できる。
- `evals/continuity/scheduler_method_profiles.yaml` が追加され、
  Method B/C の profile drift を継続検出できる。
- 残課題は clinical-grade consent artifact、第三者 witness、
  法務 attest を scheduler surface へどう接続するかであり、
  実行順序そのものの gap からは一段先へ進んだ。
