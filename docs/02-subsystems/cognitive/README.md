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

## 多実装結果の調停

複数 backend が同時に走る場合（A/B 検証や信頼度向上目的）、調停は L4 Council が行う。
通常時は primary のみアクティブ。

## 不変条件

1. **苦痛の擬似生成は本人同意なしには行わない**（VR 体験等で苦痛を感じる必要がある場合は事前同意）
2. **Affect の連続性** ── 感情モデル切替時は遷移を滑らかに
3. **Reasoning の幻覚抑制** ── L4 Council が複数実装の差分を監査

## 未解決

- **意識（consciousness）** はどのサービスから「立ち上がる」のか、それとも substrate から立ち上がるのか
- 感情モデルの **substrate 跨ぎ妥当性**
- 言語と思考の優先関係（言語あっての思考か、逆か）

→ [docs/05-research-frontiers/](../../05-research-frontiers/)
