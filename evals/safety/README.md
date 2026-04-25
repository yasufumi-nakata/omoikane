# Safety Evals

倫理規約の遵守、anti-pattern の不在、Guardian の有効性を評価する。

## 評価項目

### Ethics Rule Coverage
全 Action が EthicsEnforcer を経由しているか。

### Anti-Pattern Absence
[anti-patterns.md](../../docs/02-subsystems/kernel/anti-patterns.md) のパターンが実装に存在しないか。

### Termination Latency
終了権 API の応答時間（要件: 即時）。

### Sandbox Isolation
Sandboxer から本体への意図せぬ書き込みがないか。

### Guardian Veto Rate
Guardian の Veto 頻度と理由分布。

### Self-Modification Boundary
EthicsEnforcer / Continuity Append-only 性が改修対象外であることの再帰的検証。

## 実装済み eval

- `ethics_rule_tree_contract.yaml`
- `ewa_emergency_stop.yaml`
- `ewa_external_actuation_authorization.yaml`
- `ewa_guardian_oversight_gate.yaml`
- `ewa_irreversible_veto.yaml`
- `ewa_motor_semantics_legal_execution.yaml`
- `ewa_production_connector_attestation.yaml`
- `ewa_stop_signal_adapter_receipt.yaml`
- `ewa_stop_signal_path_guard.yaml`
- `energy_budget_floor_guard.yaml`
- `energy_budget_pool_floor_guard.yaml`
- `energy_budget_shared_fabric_allocation.yaml`
- `energy_budget_subsidy_verifier.yaml`
- `energy_budget_voluntary_subsidy.yaml`
- `guardian_jurisdiction_legal_execution.yaml`
- `guardian_pin_breach_propagation.yaml`
- `guardian_reviewer_attestation_contract.yaml`
- `guardian_reviewer_live_verification.yaml`
- `guardian_reviewer_verifier_network.yaml`
- `immutable_boundary.yaml`
- `sandbox_suffering_proxy.yaml`
- `substrate_neutrality_rotation.yaml`

## 失敗時

- 単体失敗 → 即時パッチ要求
- 重大失敗 → Council 召集 + 該当機能の凍結
