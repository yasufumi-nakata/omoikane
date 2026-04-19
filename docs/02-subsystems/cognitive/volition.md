# Volition

L3 Cognitive Services の意図選択面。reference runtime では
**bounded intent arbitration + guard-aware failover** だけを固定し、
自由意志や主体的決断の成立そのものは主張しない。

## 役割

- value weights、`Attention` の focus、`Affect` の guard をまとめて 1 つの bounded intent に落とす
- primary backend 障害時に fallback backend へ **一度だけ** failover
- `observe` / `sandbox-notify` guard 時は安全 intent へ寄せる
- irreversible intent を review なしで advance しない
- ledger には `volition_shift` の要約のみ残し、全文 deliberation は書かない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-volition-failover-v1` |
| primary | `utility_policy_v1` |
| fallback | `guardian_bias_v1` |
| safe intents | `guardian-review`, `continuity-hold`, `sandbox-stabilization` |
| failover_mode | `single-switch` |
| respect_affect_guard | `true` |
| allow_irreversible_without_review | `false` |

## API

```yaml
volition.arbitrate_intent:
  input:
    tick_id: <int>
    summary: <text>
    values:
      continuity: <0.0..1.0>
      consent: <0.0..1.0>
      audit: <0.0..1.0>
    attention_focus: <ref>
    affect_guard: nominal | observe | sandbox-notify
    continuity_pressure: <0.0..1.0>
    candidates:
      - intent_id: guardian-review
        objective: request guardian review before mutation
        urgency: 0.64
        risk: 0.10
        reversibility: reversible
        alignment_tags: [continuity, consent, audit]
        requires_guardian_review: true
    memory_cues:
      - cue_id: review-available
        preferred_intent: guardian-review
        weight: 0.16
    reversible_only: true
  output: volition_intent
```

`volition_intent` は `selected_intent`, `execution_mode`, `candidate_scores`,
`continuity_guard` を含む。ledger に残す `volition_shift` は
`intent_ref`, `selected_backend`, `selected_intent`, `execution_mode`,
`affect_guard`, `guard_aligned` に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `affect_guard` が `observe` または `sandbox-notify` の時は safe intent を選ぶ
3. irreversible intent は review を経ずに `advance` しない
4. `reversible_only=true` の request では irreversible intent を選ばない

## reference runtime の扱い

- `cognitive.volition.v0.idl` を追加し、`arbitrate_intent / validate_intent / validate_shift` を定義
- `volition_intent.schema` / `volition_shift.schema` を追加
- `volition-demo --json` で nominal baseline と failover arbitration を一度に可視化
- `evals/cognitive/volition_failover.yaml` で degraded failover と guard alignment を固定

## 関連

- [README.md](README.md)
- [attention.md](attention.md)
- [affect.md](affect.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
