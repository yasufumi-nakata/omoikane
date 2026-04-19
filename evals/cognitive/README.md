# Cognitive Evals

L3 Cognitive Services の実装がまだ薄いため、現時点ではそれらが依存する
`QualiaBuffer` と `SelfModelMonitor` の基礎挙動を cognitive eval surface として扱う。

## 実装済み eval

- `qualia_contract.yaml`
- `self_model_abrupt_change.yaml`
- `backend_failover.yaml`
- `affect_failover.yaml`
- `attention_failover.yaml`
- `volition_failover.yaml`

## 次段階

- imagination への failover 拡張
- qualia checkpoint と ContinuityLedger の横断整合
- L4 Council との認知系監査ループ
