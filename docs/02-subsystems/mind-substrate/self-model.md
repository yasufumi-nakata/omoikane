# Self Model

「自分はこういう人間である」という自己認識のネットワーク。
人格・価値観・好み・自伝的物語を含む。

## 構成要素

```yaml
SelfModel:
  identity_core:           # 中核アイデンティティ
    name: <自称＞
    pronouns: <代名詞>
    autobiographical_arc: <自伝的物語のサマリ>
  values:                  # 価値観（重み付き）
    - { value: 'honesty', weight: 0.9, last_revised: <ts> }
    - { value: 'autonomy', weight: 0.8, last_revised: <ts> }
  preferences:             # 好み
    - { domain: 'food', items: [...] }
    - { domain: 'aesthetics', items: [...] }
  relationships:           # 対人関係グラフ
    - { other_id: <id>, kind: 'family|friend|colleague|stranger', strength: 0.7 }
  capabilities:            # 自己評価された能力
    - { skill: 'mathematical_reasoning', self_rating: 0.6 }
  beliefs_about_self:      # 自分についての信念
    - "私は内向的だ"
    - "私は変化を好む"
  trauma_loci:             # 触れにくい領域（参照に注意）
    - { ref: <memory_ref>, sensitivity: 0.9 }
```

## 更新原則

1. **緩慢更新が基本** ── 価値観は時間をかけて変化する。急変は要注意。
2. **Council 監視** ── SelfModel の急変は人格乗っ取り or 病理の徴候。Council が検知する。
3. **本人観察** ── 本人が自分の SelfModel を読める権利を持つ。

reference runtime では `bounded-self-model-monitor-v1` を採用し、
divergence を `values` / `goals` / `traits` の 3 成分平均で計算する。
adjacent snapshot 間の divergence が `0.35` 以上なら `abrupt_change=true` とし、
それ未満は stable drift として扱う。

## 急変検知

```
急変判定:
  - reference runtime は `values` / `goals` / `traits` の equal-weight divergence を使う
  - adjacent snapshot の divergence が `0.35` 以上 → flag
  - stable drift は `0.35` 未満に留め、history は append-only で保持する
```

flag された変化は Council が本人に確認する。**変化の自由は損なわず、外部からの操作のみ拒否する** バランス。

## SelfModel と他層の関係

- L3 Reasoning は SelfModel を「私はこう判断する人間だ」の前提として参照
- L3 Volition は SelfModel.values に基づいて意志を生成
- L4 Council は SelfModel の整合性を監視
- L6 Inter-Mind Channel では、相手に開示する SelfModel の範囲を本人が選択

## プライバシ

- SelfModel 全体は本人鍵で暗号化
- 外部開示は **明示的なビューテンプレート**（"public profile", "close friends only" 等）経由のみ

## 未解決

- 自己モデルの「正しさ」を本人以外が評価できるか
- 病理的な自己評価（過小評価・過大評価）の補正をするべきか／しないべきか
- アップロード後の **新しい価値観の生成** の自由度
