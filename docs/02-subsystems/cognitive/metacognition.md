# Metacognition

L3 Cognitive Services の自己監視面。reference runtime では
**bounded self-monitor report + continuity-safe failover** だけを固定し、
内省や主観的自己意識の成立そのものは主張しない。

## 役割

- `SelfModelMonitor` の divergence / abrupt change と `QualiaBuffer` の状態を受けて 1 つの bounded report を構成する
- primary backend 障害時に fallback backend へ **一度だけ** failover する
- abrupt change や non-nominal guard を `guardian-review` / `sandbox-stabilization` へ deterministic に昇格する
- public report は values / goals を最大 3 件に制限し、private note も 4 件に抑える
- ledger には `metacognition_shift` の要約のみ残し、全文 report や raw trait vector は書かない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-self-monitor-loop-v1` |
| primary | `reflective_loop_v1` |
| fallback | `continuity_mirror_v1` |
| max_public_values | `3` |
| max_private_notes | `4` |
| divergence_alert_threshold | `0.35` |
| failover_mode | `single-switch` |

## API

```yaml
metacognition.generate_report:
  input:
    tick_id: <int>
    summary: <text>
    identity_id: <string>
    self_values: [continuity-first, consent-preserving]
    self_goals: [bounded-reflection, stable-handoff]
    self_traits:
      curiosity: 0.67
      caution: 0.79
    qualia_summary: 起動後の自己監視を静穏に維持している
    attention_target: self-monitor
    self_awareness: 0.76
    lucidity: 0.94
    affect_guard: nominal | observe | sandbox-notify
    continuity_pressure: <0.0..1.0>
    abrupt_change: <bool>
    divergence: <0.0..1.0>
    memory_cues:
      - cue_id: continuity-anchor
        focus: continuity-first
        weight: 0.24
  output: metacognition_report
```

`metacognition_report` は `reflection_summary`, `salient_values`, `active_goals`,
`trait_summary`, `qualia_bridge`, `reflection_mode`, `escalation_target`,
`risk_posture`, `coherence_score`, `continuity_guard` を持つ。
ledger に残す `metacognition_shift` は `report_ref`, `selected_backend`,
`reflection_mode`, `escalation_target`, `affect_guard`, `abrupt_change`,
`divergence`, `guard_aligned` に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `abrupt_change=true` または `affect_guard!=nominal` の時は `escalation_target=none` を返さない
3. public reflection は values / goals を最大 3 件までに制限する
4. `observe` では `guardian-review`、`sandbox-notify` では `sandbox-hold` へ整列する
5. SelfModel の raw 履歴や詳細 trait vector は ledger に残さず、digest-safe な要約だけを記録する

## reference runtime の扱い

- `cognitive.metacognition.v0.idl` を追加し、`generate_report / validate_report / validate_shift` を定義
- `metacognition_report.schema` / `metacognition_shift.schema` を追加
- `metacognition-demo --json` で baseline の `self-reflect` と、
  failover 後の `guardian-review` への昇格を一度に可視化
- `evals/cognitive/metacognition_failover.yaml` で degraded failover と identity anchor 保持を固定

## 関連

- [README.md](README.md)
- [imagination.md](imagination.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
