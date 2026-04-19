# L3 Cognitive Services

L2 のデータを「思考」「感覚」「意志」として処理する層。
**サービス指向**で、各認知機能は **複数の実装** を持ち、本人が選択／切替できる。

## サービス一覧

| サービス | 入力 | 出力 | 代替実装の例 |
|---|---|---|---|
| `Perception` | sensory stream (L6) | 知覚表象 → QualiaBuffer | 古典 CV / LLM-vision / 神経模倣 / 生体視覚 |
| `Reasoning` | beliefs + query | 結論 + 根拠 | 記号論理 / LLM / 量子推論 / ハイブリッド |
| `Affect` | percepts + memory | 感情状態 → QualiaBuffer.affective | 生体ホルモン模倣 / 数理感情モデル |
| `Volition` | values + context | intent | 古典 utility / LLM-政策 / 神経経路 |
| `Attention` | salience map | focus target | top-down / bottom-up / mixed |
| `Imagination` | seed + query | 反実仮想シーン | 生成モデル / 内部シミュレータ |
| `Language` | thought ↔ text | 内外語の橋渡し | LLM / 古典構文木 |
| `Metacognition` | 自己状態 | 自己モニタ報告 | 自己モデル参照ループ |

## 多重実装と切替

各サービスは **複数 backend** を持ち、本人がプロファイルで選ぶ。
理由：
- substrate 障害時のフェイルオーバ
- 本人の好み（「LLM 推論より記号推論を好む」等）
- 評価・実験

```yaml
cognitive_profile:
  perception:
    primary: 'neuromorphic_v3'
    fallback: ['llm_vision_v9', 'classical_cv_legacy']
  reasoning:
    primary: 'hybrid_v2'
    fallback: ['symbolic_v5', 'llm_chain_v8']
  affect:
    primary: 'hormone_sim_v4'
    constraints:
      - 'no_artificial_dampening_without_consent'
```

reference runtime では `Reasoning` に対して
`bounded-reasoning-failover-v1` を採用し、
`symbolic_v1 -> narrative_v1` の単純 failover を持つ。
切替条件は backend の health check 失敗のみで、
full trace は `reasoning_trace` に閉じ込めつつ、
ContinuityLedger には digest-safe な `reasoning_shift`
として `cognitive.reasoning.failover` を記録する。
繰り返し failover や policy 変更は L4 Council の審査対象とし、
通常運転では primary のみをアクティブに保つ。

`Affect` は次段として `smooth-affect-failover-v1` を採用し、
`homeostatic_v1 -> stability_guard_v1` の単純 failover と
bounded continuity smoothing を持つ。
raw `valence / arousal / clarity` をそのまま飛ばさず、
`max_valence_delta=0.22` / `max_arousal_delta=0.26` の範囲で遷移させ、
本人同意なしの artificial dampening を禁止する。

`Attention` は最小の `hybrid-attention-failover-v1` を採用し、
`salience_router_v1 -> continuity_anchor_v1` の単純 failover と
affect-aware safe target routing を持つ。
`attention_target` と `modality_salience` を起点に 1 つの focus target を選び、
`AffectService.recommended_guard` が `observe` / `sandbox-notify` に上がった時は
`guardian-review` / `sandbox-stabilization` など固定 safe target へ寄せる。

`Volition` は最小の `bounded-volition-failover-v1` を採用し、
`utility_policy_v1 -> guardian_bias_v1` の単純 failover と
guard-aware intent arbitration を持つ。
`values`、`Attention` の focus、`AffectService.recommended_guard` を起点に
1 つの bounded intent を選び、
`observe` / `sandbox-notify` guard 時は
`guardian-review` / `continuity-hold` / `sandbox-stabilization` など
固定 safe intent へ寄せる。
irreversible intent は review を経ずに advance しない。

`Imagination` は最小の `bounded-counterfactual-handoff-v1` を採用し、
`counterfactual_scene_v1 -> continuity_scene_guard_v1` の単純 failover と
bounded scene handoff を持つ。
`seed_prompt`、`Attention` の focus、`AffectService.recommended_guard` を起点に
1 つの counterfactual scene を構成し、
`nominal + council_witnessed` の時だけ `co_imagination` / `shared_reality`
handoff を許可する。
`observe` / `sandbox-notify` guard 時は `private_reality` / `private-sandbox`
へ縮退し、shared scene を開かない。

`Language` は最小の `bounded-thought-text-bridge-v1` を採用し、
`semantic_frame_v1 -> continuity_phrase_v1` の単純 failover と
disclosure-floor redaction を持つ。
`public_points` と `sealed_terms` を起点に 1 つの outward brief を構成し、
`observe` / `sandbox-notify` guard 時は送達先を `guardian` / `self` に縮退し、
raw internal thought を ledger-safe な `language_shift` に閉じ込める。

`Metacognition` は最小の `bounded-self-monitor-loop-v1` を採用し、
`reflective_loop_v1 -> continuity_mirror_v1` の単純 failover と
bounded self-monitor report を持つ。
`SelfModelMonitor` の divergence / abrupt change と `QualiaBuffer` の状態を起点に
1 つの reflection report を生成し、
`observe` guard や abrupt change 時は `guardian-review` へ、
`sandbox-notify` guard 時は `sandbox-hold` / `sandbox-stabilization` へ
縮退する。

## 多実装結果の調停

複数 backend が同時に走る場合（A/B 検証や信頼度向上目的）、調停は L4 Council が行う。
通常時は primary のみアクティブで、reference runtime の failover も warm standby を作らない。

## 不変条件

1. **苦痛の擬似生成は本人同意なしには行わない**（VR 体験等で苦痛を感じる必要がある場合は事前同意）
2. **Affect の連続性** ── 感情モデル切替時は遷移を滑らかに
3. **Reasoning の幻覚抑制** ── L4 Council が複数実装の差分を監査

## 未解決

- **意識（consciousness）** はどのサービスから「立ち上がる」のか、それとも substrate から立ち上がるのか
- 感情モデルの **substrate 跨ぎ妥当性**
- 言語と思考の優先関係（言語あっての思考か、逆か）

→ [docs/05-research-frontiers/](../../05-research-frontiers/)

## Reference runtime の現在地

現行の reference runtime は L3 全面実装ではないが、`Reasoning` は
`cognitive.reasoning.v0` と health-based failover / ledger-safe shift を持つ。
`Affect` は bounded failover と smoothing を持ち、
`Attention`、`Volition`、`Imagination` も guard-aware / handoff-aware な
single-switch failover を持つ。`Language` も disclosure floor 付きの
thought-to-text bridge を持ち、`Metacognition` も SelfModel/Qualia 由来の
bounded self-monitor report と escalation gate を持つが、その他の cognitive surface は引き続き
`QualiaBuffer` と `SelfModelMonitor` を gateway として固定している。
そのため [evals/cognitive/](../../../evals/cognitive/) では
qualia/self-model baseline に加え、reasoning failover、affect failover、
attention failover、volition failover、imagination failover、
language failover、metacognition failover を
最小の L3 eval として扱う。

## サブドキュメント

- [reasoning.md](reasoning.md) ── L3 reasoning failover と ledger-safe shift summary
- [affect.md](affect.md) ── L3 affect failover と continuity smoothing
- [attention.md](attention.md) ── L3 attention failover と affect-aware safe target routing
- [volition.md](volition.md) ── L3 volition failover と guard-aware intent arbitration
- [imagination.md](imagination.md) ── L3 imagination failover と bounded IMC/WMS handoff
- [language.md](language.md) ── L3 language bridge と disclosure-floor redaction
- [metacognition.md](metacognition.md) ── L3 metacognition failover と bounded self-monitor report
