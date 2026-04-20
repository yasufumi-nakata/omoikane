# 2026-04-20 SubstrateBroker Reference Runtime

## Context

- `docs/02-subsystems/kernel/substrate-broker.md` には deterministic selection、
  neutrality rotation、`broker-demo`、`kernel.broker.v0.idl`、
  `evals/safety/substrate_neutrality_rotation.yaml` が書かれていた一方、
  repo 内には runtime / CLI / tests / machine-readable contract が存在していなかった。
- `gap-report --json` は all-zero でも、この broker surface は docs-only の latent gap だった。

## Decision

- `SubstrateBrokerService` を L1 kernel surface として追加し、
  `select_substrate -> lease -> attest -> migrate -> release -> handle_energy_floor_signal`
  を bounded reference contract に固定する。
- broker は既存 `substrate_*` schema を再利用し、
  standby は **1 active lease + 1 standby candidate** として保持する。
  AP-3 を避けるため、reference runtime では second active lease は作らない。
- deterministic selection は
  `capability / health_score >= 0.6 / attestation_valid / energy_floor`
  を満たす候補だけを残し、
  `-priority_for_method / -health_score / substrate_kind_neutrality_index`
  の順で tie-break する。
- `neutrality_window=2` とし、直近 2 回の selection history に含まれた kind 数を
  `substrate_kind_neutrality_index` として rotation を促す。
- `handle_energy_floor_signal` は energy floor violation 時に
  `critical + migrate-standby` と scheduler-compatible payload を返す。

## Alternatives considered

- A: broker docs を維持し、runtime は `substrate-demo` だけに留める
  - docs と runtime の差分が残り、latent gap が継続するため不採用
- B: standby も second active lease として即時 allocate する
  - `same identity の 2 active leases は禁止` と衝突し、reference runtime では過剰
- C: scheduler signal bridge まで外して selection/migrate だけに絞る
  - EnergyFloor violation の failover 意味論が docs とずれるため不採用

## Consequences

- `broker-demo` 1 本で neutrality rotation、healthy-attestation gate、
  standby-bound migration、release completion を smoke できる。
- docs-only だった `SubstrateBroker` が runtime / CLI / tests / IDL / eval まで揃い、
  scheduler の substrate signal 境界も machine-checkable になった。
- residual future work は live dual allocation、continuous cross-substrate attestation streaming、
  richer substrate-specific adapters へ縮小される。
