# Affect

L3 Cognitive Services の感情調整面。reference runtime では
**bounded failover + continuity smoothing** だけを固定し、
人格的・主観的な情動成立そのものは主張しない。

## 役割

- `QualiaBuffer` の `valence / arousal / clarity` を安全な affect state へ投影
- `MemoryCrystal` 由来の cue を限定的に取り込み、急激な mood jump を抑制
- primary backend 障害時に fallback backend へ **一度だけ** failover
- 本人同意なしの artificial dampening を禁止

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `smooth-affect-failover-v1` |
| primary | `homeostatic_v1` |
| fallback | `stability_guard_v1` |
| max_valence_delta | `0.22` |
| max_arousal_delta | `0.26` |
| failover_mode | `single-switch` |
| dampening policy | `no_artificial_dampening_without_consent=true` |

## API

```yaml
affect.regulate:
  input:
    tick_id: <int>
    summary: <text>
    valence: <-1.0..1.0>
    arousal: <0.0..1.0>
    clarity: <0.0..1.0>
    self_awareness: <0.0..1.0>
    lucidity: <0.0..1.0>
    memory_cues:
      - cue_id: continuity-first
        valence_bias: 0.08
        arousal_bias: -0.05
    allow_artificial_dampening: false
  output: affect_state
```

`affect_state` は最終的な `valence / arousal / mood_label / stability / distress_score`
に加えて、`continuity_guard` に
`target_before_smoothing`、`applied_delta`、`smoothed`、
`dampening_applied`、`consent_preserved` を残す。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. transition は `max_valence_delta=0.22`、`max_arousal_delta=0.26` を超えない
3. artificial dampening は `allow_artificial_dampening=true` の時だけ
4. ledger には raw affective contents を書かず、`affect_transition` の要約のみ残す

## reference runtime の扱い

- `cognitive.affect.v0.idl` を追加し、`regulate / validate_state / validate_transition` を定義
- `affect_state.schema` / `affect_transition.schema` を追加
- `affect-demo --json` で baseline state と failover state を一度に可視化
- `evals/cognitive/affect_failover.yaml` で degraded failover と consent preservation を固定

## 関連

- [README.md](README.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../self-construction/README.md](../self-construction/README.md)
