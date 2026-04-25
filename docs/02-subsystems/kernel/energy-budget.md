# EnergyBudget

L1 Kernel の AP-1 guard。経済的事情や外部支払い状態を、意識・記憶・主観時間の劣化として伝搬させないため、substrate workload ごとの `EnergyFloor` を digest-bound receipt として固定する。

## 責務

1. `ClassicalSiliconAdapter.ENERGY_FLOOR_TABLE` 由来の workload floor を読み取る
2. 要求 budget が floor 未満なら `blocked-economic-pressure` として拒否する
3. 許可 budget は常に `energy_floor.minimum_joules_per_second` 以上に丸める
4. observed capacity が floor 未満なら SubstrateBroker の `critical + migrate-standby` signal に束縛する
5. 外部経済 payload は保存せず、`external_economic_context_ref` と digest だけを receipt に残す

## reference runtime

`kernel.energy_budget.v0` は `EnergyBudgetService.evaluate_floor`、`evaluate_pool_floor`、`evaluate_voluntary_subsidy`、`allocate_shared_fabric_capacity` と各 validation contract を公開する。

`energy-budget-demo` は migration workload の floor を `30 J/s` とし、`requested_budget_jps=22`、`observed_capacity_jps=28` の AP-1 シナリオを実行する。receipt は `granted_budget_jps=30`、`budget_status=floor-protected`、`degradation_allowed=false`、`broker_recommended_action=migrate-standby` を返す。

`EnergyBudgetService.evaluate_pool_floor` は multi-identity pool の合算 budget を扱うが、floor 判定は identity ごとに固定する。
`energy-budget-pool-demo` は migration member が `requested_budget_jps=22 < floor=30`、council member が `requested_budget_jps=38 > floor=24` の状況を作り、aggregate requested budget が total floor を覆っていても `cross_identity_floor_offset_blocked=true`、`cross_identity_subsidy_allowed=false`、`pool_budget_status=floor-protected` を返す。

`EnergyBudgetService.evaluate_voluntary_subsidy` は pool floor receipt の validation 後にだけ、post-floor voluntary consent として別 identity の donor surplus を recipient shortfall に紐づける。`energy-budget-subsidy-demo` は council member の floor-preserved surplus `14 J/s` のうち `8 J/s` を migration member の shortfall `8 J/s` に明示同意 digest、revocation ref、funding policy ref、signature ref 付きで束縛する。さらに `jurisdiction-bound-energy-subsidy-authority-v1` として、funding policy signature を `JP-13` の signer roster / signer key ref に束縛し、`energy-subsidy-signer-roster-live-verifier-v1` の loopback verifier receipt で signer roster digest と signer key ref を live bridge にも束縛し、offer revocation refs を revocation registry digest に束ね、同じ法域の audit authority digest が signer roster と revocation registry の両方を監査対象として保持することを確認する。receipt は `voluntary_subsidy_allowed=true`、`authority_binding_status=verified`、`funding_policy_signature_bound=true`、`signer_roster_verifier_bound=true`、`revocation_registry_bound=true`、`audit_authority_bound=true`、`jurisdiction_authority_bound=true`、`floor_protection_preserved=true`、`cross_identity_offset_used=false`、`raw_funding_payload_stored=false`、`raw_authority_payload_stored=false` を返す。

`EnergyBudgetService.allocate_shared_fabric_capacity` は pool floor receipt の validation 後に、shared fabric 全体でしか観測できない capacity を `floor-ratio-deficit-first-v1` で deterministic に member floor へ配賦する。`energy-budget-fabric-demo` は total required floor `54 J/s` に対して shared fabric observed capacity `50 J/s` の deficit を作り、migration member `28/30 J/s`、council member `22/24 J/s` として shortfall を導出する。receipt は `fabric_capacity_deficit_jps=4`、`impacted_member_count=2`、`budget_status=fabric-capacity-deficit-protected`、`degradation_allowed=false`、`broker_signal_bound=true`、`raw_capacity_payload_stored=false` を返す。

## 不変条件

1. economic pressure は floor を下げられない
2. floor 未満の observed capacity は standby 退避 signal へ接続される
3. raw invoice、payment transcript、広告条件などは receipt に保存しない
4. multi-identity pool でも別 identity の surplus budget で floor 未満 request を相殺しない
5. voluntary subsidy は pool floor validation の後段だけで許可し、donor consent digest と donor floor preservation を必須にする
6. voluntary subsidy の funding policy signature は法域付き signer roster、live verifier receipt、revocation registry、audit authority の digest chain に束縛され、raw authority payload / verifier payload は保存しない
7. shared fabric capacity しか観測できない場合でも、member shortfall を明示し、劣化許可ではなく standby 退避 signal に束縛する
8. sustainable economy の社会制度モデルは research frontier に残し、runtime は床値保護、同意付き補助、shared fabric shortfall receipt だけを検証する

## 関連

- [anti-patterns.md](anti-patterns.md)
- [substrate-broker.md](substrate-broker.md)
- [../../05-research-frontiers/sustainable-economy.md](../../05-research-frontiers/sustainable-economy.md)
