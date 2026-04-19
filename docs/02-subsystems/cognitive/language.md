# Language

L3 Cognitive Services の thought-to-text bridge 面。reference runtime では
**bounded outward brief + disclosure-floor redaction** だけを固定し、
自由生成や豊かな内的独白の実装は主張しません。

## 役割

- bounded な internal thought metadata を outward brief へ 1 回だけ射影する
- primary backend 障害時に fallback backend へ **一度だけ** failover する
- `observe` / `sandbox-notify` guard では disclosure floor を tightening し、
  `guardian` または `self` へ送達先を縮退する
- outward render には public points を最大 3 件までしか出さず、
  sealed terms も最大 4 件に制限する
- ledger には `language_shift` の要約だけを残し、raw `internal_thought` は残さない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-thought-text-bridge-v1` |
| primary | `semantic_frame_v1` |
| fallback | `continuity_phrase_v1` |
| max_public_points | `3` |
| max_redacted_terms | `4` |
| failover_mode | `single-switch` |

## API

```yaml
language.render_text:
  input:
    tick_id: <int>
    summary: <text>
    internal_thought: <text>
    audience: self | council | guardian | peer
    intent_label: <string>
    attention_focus: <string>
    affect_guard: nominal | observe | sandbox-notify
    continuity_pressure: <0.0..1.0>
    public_points: [continuity-first, bounded rollout]
    sealed_terms: [identity drift note, private distress trace]
    memory_cues:
      - cue_id: guardian-review
        phrase: guardian review
        weight: 0.22
  output: language_render
```

`language_render` は `thought_digest`, `discourse_mode`, `delivery_target`,
`rendered_text`, `disclosure_floor`, `continuity_guard` を持つ。
ledger に残す `language_shift` は `render_ref`, `selected_backend`,
`delivery_target`, `discourse_mode`, `affect_guard`, `redaction_applied`,
`guard_aligned` に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `observe` では `guardian-brief` + `guardian`、`sandbox-notify` では `sandbox-brief` + `self`
3. non-nominal guard では `private_channel_locked=true` かつ redaction を必須化する
4. outward render は public points を最大 3 件、redacted terms を最大 4 件に制限する
5. raw `internal_thought` は runtime 内で hash 化し、ledger や shift summary へ直接は残さない

## reference runtime の扱い

- `cognitive.language.v0.idl` を追加し、`render_text / validate_render / validate_shift` を定義
- `language_render.schema` / `language_shift.schema` を追加
- `language-demo --json` で baseline の `public-brief` と、
  failover 後の `guardian-brief` への縮退を一度に可視化
- `evals/cognitive/language_failover.yaml` で degraded failover と disclosure-floor redaction を固定

## 関連

- [README.md](README.md)
- [metacognition.md](metacognition.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
