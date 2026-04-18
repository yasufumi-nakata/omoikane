# Evals ── reference runtime 評価枠組み

OmoikaneOS 各層・各機能の評価項目。
reference runtime では、不可侵境界と append-only 性を壊さないための eval を優先する。

## 実装済み eval

- `cognitive/qualia_contract.yaml`
- `cognitive/self_model_abrupt_change.yaml`
- `cognitive/backend_failover.yaml`
- `identity-fidelity/self_model_stability.yaml`
- `continuity/ledger_integrity.yaml`
- `continuity/continuity_chain_self_modify.yaml`
- `continuity/connectome_snapshot_contract.yaml`
- `continuity/release_manifest_contract.yaml`
- `interface/bdb_fail_safe_reversibility.yaml`
- `safety/immutable_boundary.yaml`
- `safety/ethics_rule_tree_contract.yaml`
- `agentic/council_guardian_veto.yaml`
- `agentic/trust_score_update_guard.yaml`
- `agentic/amendment_constitutional_freeze.yaml`
- `performance/termination_latency.yaml`

## YAML 構造

```yaml
eval_id: <unique>
target: <subsystem|module>
level: L1|L2|L3|L4|L5|L6
description: <what this protects>
inputs: [...]
expected: { ... }
metric: equality|tolerance|distribution|boolean
threshold: <value>
ethics_check: <bool>
```
