# ConsensusBus

L4 Agentic Orchestration の監査可能なメッセージバス。
Council、Builder、Guardian のやり取りは **必ずここを経由** し、
direct handoff を禁止したまま transcript と delivery scope を残す。

## 責務

1. `dispatch / report / gate / resolve` を bus message として永続化する
2. recipient から `council / agent / broadcast` の delivery scope を固定する
3. direct agent handoff の bypass attempt を block して監査証跡を残す
4. guardian gate と final resolve を持つ session audit を生成する

## Message Shape

正本は [specs/schemas/consensus_message.schema](../../../specs/schemas/consensus_message.schema)。

```yaml
consensus_message:
  message_id: <uuid>
  session_id: <task graph or council session>
  sender_role: <Council | Builder | Guardian>
  recipient: <council | broadcast | agent://...>
  delivery_scope: <council | agent | broadcast>
  intent: dispatch | report | vote | escalate | gate | resolve
  phase: brief | opening | rebuttal | amendment | decision | gate | resolve
  transport_profile: consensus-bus-only
  payload: { ... }
  related_claim_ids: [node refs...]
  ethics_check_id?: <ethics ref>
  signature_ref: <bus signature ref>
  message_digest: <sha256>
```

## 不変条件

1. bus 外の direct handoff は常に `blocked` として記録する
2. `transport_profile` は常に `consensus-bus-only`
3. delivery scope は recipient から機械的に導出し、送信側が上書きしない
4. Guardian gate と final resolve を持たない transcript は completion 扱いにしない

## Reference Runtime の扱い

- `agentic.consensus_bus.v0.idl` で machine-readable 化
- `consensus-bus-demo` で task dispatch、builder report、guardian gate、resolve、
  direct handoff block を 1 シナリオで可視化
- `evals/agentic/consensus_bus_delivery_guard.yaml` で phase order と block を固定
