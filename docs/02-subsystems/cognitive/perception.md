# Perception

L3 Cognitive Services の知覚面。reference runtime では
**bounded scene encoding + qualia-bound failover** だけを固定し、
豊かな主観的知覚そのものは主張しない。

## 役割

- `sensory stream` を 1 つの bounded `scene summary` に圧縮する
- scene を `qualia://tick/<id>` に束縛し、L2 `QualiaBuffer` への handoff を固定する
- primary backend 障害時に fallback backend へ **一度だけ** failover
- `affect_guard` が上がった時は `guardian-review-scene` / `continuity-hold` /
  `sandbox-stabilization` の safe scene へ縮退する
- ledger には `perception_shift` の要約のみを残し、raw sensory payload は書かない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-perception-failover-v1` |
| primary | `salience_encoder_v1` |
| fallback | `continuity_projection_v1` |
| safe scenes | `guardian-review-scene`, `continuity-hold`, `sandbox-stabilization` |
| qualia_handoff_required | `true` |
| body_coherence_floor | `0.6` |
| failover_mode | `single-switch` |

## API

```yaml
perception.encode_scene:
  input:
    tick_id: <int>
    summary: <text>
    sensory_stream_ref: sensory://...
    world_state_ref: world://...
    body_anchor_ref: body-anchor://...
    modality_salience:
      visual: <0.0..1.0>
      auditory: <0.0..1.0>
      somatic: <0.0..1.0>
      interoceptive: <0.0..1.0>
    drift_score: <0.0..1.0>
    affect_guard: nominal | observe | sandbox-notify
    detected_entities:
      - guardian-console
      - anomaly-cluster
    memory_cues:
      - cue_id: guardian-review-scene
        target: guardian-review-scene
        weight: 0.27
  output: perception_frame
```

`perception_frame` は `scene_label`, `scene_summary`, `dominant_modality`,
`salience_map`, `qualia_binding_ref`, `body_coherence_score`, `perception_gate`,
`continuity_guard` を含む。
ledger に残す `perception_shift` は `frame_ref`, `scene_label`,
`dominant_modality`, `qualia_binding_ref`, `body_coherence_preserved`
に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `qualia_binding_ref` は必ず `qualia://tick/<id>` に束縛する
3. `affect_guard` が `observe` / `sandbox-notify` の時は safe scene へ縮退する
4. `perception_shift` は raw sensory embedding や payload body を含まない
5. `body_coherence_score < 0.6` を continuity-preserved と主張しない

## reference runtime の扱い

- `cognitive.perception.v0.idl` を追加し、`encode_scene / validate_frame / validate_shift` を定義
- `perception_frame.schema` / `perception_shift.schema` を追加
- `perception-demo --json` で nominal baseline と failover scene を一度に可視化
- `evals/cognitive/perception_failover.yaml` で degraded failover と safe scene alignment を固定

## 関連

- [README.md](README.md)
- [attention.md](attention.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
