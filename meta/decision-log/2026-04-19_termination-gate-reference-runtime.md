# 2026-04-19 TerminationGate Reference Runtime

## Decision

- `TerminationGate` を L1 の独立 surface として reference runtime へ昇格する。
- `IdentityRegistry.terminate()` は低位 primitive に留め、外向き contract は
  `kernel.termination.v0` / `termination-demo` / `termination_request.schema` /
  `termination_outcome.schema` で固定する。
- reference runtime の completed path は deterministic な latency 予算
  `86ms` を返し、`scheduler_handle_cancelled=true` と
  `substrate_lease_released=true` を同時に記録する。
- preconsented cool-off は `identity.metadata` の
  `termination_policy_mode=cool-off-allowed` と
  `termination_policy_days` がある場合にのみ許容する。

## Rationale

- 既に存在した `performance/termination_latency.yaml` が `kernel.identity` を向いており、
  docs 側の `TerminationGate` contract と drift していた。
- `AscensionScheduler` より面積が小さく、runtime・CLI・IDL・tests・eval を
  一気通貫で揃えやすい。
- 終了権は veto 不可だが、evidence は append-only ledger に必ず残す必要があるため、
  独立 service 化した方が contract を明確に保てる。

## Consequences

- `termination-demo` で immediate / cool-off pending / invalid proof reject を
  1 回で smoke できる。
- 大きな残課題は `AscensionScheduler` の stage machine 実装であり、
  今回は `TerminationGate` から先に閉じる。
