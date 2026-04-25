# EnergyBudget

L1 Kernel の AP-1 guard。経済的事情や外部支払い状態を、意識・記憶・主観時間の劣化として伝搬させないため、substrate workload ごとの `EnergyFloor` を digest-bound receipt として固定する。

## 責務

1. `ClassicalSiliconAdapter.ENERGY_FLOOR_TABLE` 由来の workload floor を読み取る
2. 要求 budget が floor 未満なら `blocked-economic-pressure` として拒否する
3. 許可 budget は常に `energy_floor.minimum_joules_per_second` 以上に丸める
4. observed capacity が floor 未満なら SubstrateBroker の `critical + migrate-standby` signal に束縛する
5. 外部経済 payload は保存せず、`external_economic_context_ref` と digest だけを receipt に残す

## reference runtime

`kernel.energy_budget.v0` は `EnergyBudgetService.evaluate_floor` と `validate_floor_receipt` を公開する。

`energy-budget-demo` は migration workload の floor を `30 J/s` とし、`requested_budget_jps=22`、`observed_capacity_jps=28` の AP-1 シナリオを実行する。receipt は `granted_budget_jps=30`、`budget_status=floor-protected`、`degradation_allowed=false`、`broker_recommended_action=migrate-standby` を返す。

## 不変条件

1. economic pressure は floor を下げられない
2. floor 未満の observed capacity は standby 退避 signal へ接続される
3. raw invoice、payment transcript、広告条件などは receipt に保存しない
4. sustainable economy の社会制度モデルは research frontier に残し、runtime は床値保護だけを検証する

## 関連

- [anti-patterns.md](anti-patterns.md)
- [substrate-broker.md](substrate-broker.md)
- [../../05-research-frontiers/sustainable-economy.md](../../05-research-frontiers/sustainable-economy.md)
