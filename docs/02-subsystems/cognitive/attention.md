# Attention

L3 Cognitive Services の注意配分面。reference runtime では
**bounded focus routing + affect-aware failover** だけを固定し、
主体的な注意経験そのものは主張しない。

## 役割

- `QualiaBuffer` の `attention_target` と `modality_salience` から 1 つの focus target を選ぶ
- `AffectService.recommended_guard` を受け取り、guard が上がった時は安全 target へ寄せる
- primary backend 障害時に fallback backend へ **一度だけ** failover
- ledger には `attention_shift` の要約のみを残し、raw sensory embedding は書かない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `hybrid-attention-failover-v1` |
| primary | `salience_router_v1` |
| fallback | `continuity_anchor_v1` |
| safe targets | `guardian-review`, `continuity-ledger`, `sandbox-stabilization` |
| failover_mode | `single-switch` |
| respect_affect_guard | `true` |
| default_dwell_ms | `600` |
| degraded_dwell_ms | `450` |

## API

```yaml
attention.route_focus:
  input:
    tick_id: <int>
    summary: <text>
    attention_target: <ref>
    modality_salience:
      visual: <0.0..1.0>
      auditory: <0.0..1.0>
      somatic: <0.0..1.0>
      interoceptive: <0.0..1.0>
    self_awareness: <0.0..1.0>
    lucidity: <0.0..1.0>
    affect_guard: nominal | observe | sandbox-notify
    memory_cues:
      - cue_id: guardian-review
        target: guardian-review
        weight: 0.27
  output: attention_focus
```

`attention_focus` は `focus_target`, `candidate_scores`, `dwell_ms`,
`degraded`, `continuity_guard` を含む。
ledger に残す `attention_shift` は `focus_ref`, `selected_backend`,
`focus_target`, `affect_guard`, `preserved_target` に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `affect_guard` が `observe` または `sandbox-notify` の時は safe target へ移る
3. `attention_shift` は raw sensory embedding を含まない
4. fallback が選ばれても `continuity_guard.attempted_backends` を必ず残す

## reference runtime の扱い

- `cognitive.attention.v0.idl` を追加し、`route_focus / validate_focus / validate_shift` を定義
- `attention_focus.schema` / `attention_shift.schema` を追加
- `attention-demo --json` で nominal baseline と failover focus を一度に可視化
- `evals/cognitive/attention_failover.yaml` で degraded failover と guard alignment を固定

## 関連

- [README.md](README.md)
- [affect.md](affect.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
