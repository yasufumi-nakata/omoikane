# Cognitive Evals

L3 Cognitive Services の実装がまだ薄いため、現時点ではそれらが依存する
`QualiaBuffer` と `SelfModelMonitor` の基礎挙動を cognitive eval surface として扱う。

## 実装済み eval

- `qualia_contract.yaml`
- `self_model_abrupt_change.yaml`
- `backend_failover.yaml` (`cognitive.reasoning.v0` の failover / shift contract)
- `affect_failover.yaml`
- `attention_failover.yaml`
- `volition_failover.yaml`
- `imagination_failover.yaml`
- `language_failover.yaml`
- `metacognition_failover.yaml`

## 次段階

- distributed oversight / Federation / Heritage returned result と認知監査ループを直結すること
