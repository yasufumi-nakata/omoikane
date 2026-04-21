# Cognitive Evals

L3 Cognitive Services の実装がまだ薄いため、現時点ではそれらが依存する
`QualiaBuffer` と `SelfModelMonitor` の基礎挙動を cognitive eval surface として扱う。

## 実装済み eval

- `qualia_contract.yaml`
- `self_model_abrupt_change.yaml`
- `perception_failover.yaml`
- `backend_failover.yaml` (`cognitive.reasoning.v0` の failover / shift contract)
- `affect_failover.yaml`
- `attention_failover.yaml`
- `volition_failover.yaml`
- `imagination_failover.yaml`
- `language_failover.yaml`
- `metacognition_failover.yaml`
- `../agentic/cognitive_audit_governance_binding.yaml` (`cognitive audit -> oversight/Federation/Heritage` handoff contract)

## 次段階

- actual non-loopback verifier transport や multi-jurisdiction reviewer network まで拡張すること
