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

## reference runtime で固定した校正境界

`self-model-advisory-calibration-boundary-v1` は、本人以外の witness や
Council が SelfModel の「正しさ」を断定する contract ではない。
外部 evidence は `self_model_calibration_receipt` に digest-only で束ねられ、
本人同意、Council resolution、Guardian redaction が揃った場合でも
`correction_mode=advisory-only` に留まる。

この receipt は病理的な自己評価の可能性を Council review へ渡せるが、
`forced_correction_allowed=false`、`accepted_for_writeback=false`、
`raw_external_testimony_stored=false` を固定し、
proposed adjustment は常に `requires-self-acceptance` として扱う。
つまり reference runtime は補正の根拠を監査可能にするだけで、
本人に代わって価値観や trait を上書きしない。

## reference runtime で固定した価値生成境界

`self-model-self-authored-value-generation-v1` は、アップロード後の新しい価値観を
外部 reviewer が「正しい / 間違っている」と裁定する contract ではない。
reference runtime は新規価値候補を
`self_model_value_generation_receipt` に digest-only で束ねるが、
`generation_mode=self-authored-bounded-experiment`、
`integration_status=proposed-not-written-back`、
`requires_future_self_acceptance=true` を固定する。

Council と Guardian は continuity context と安全境界を確認できるが、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`accepted_for_writeback=false` を維持する。
raw value payload や raw continuity payload は保存せず、将来の本人受容があるまで
SelfModel 本体には書き戻さない。

## reference runtime で固定した本人受容 writeback 境界

`self-model-future-self-acceptance-writeback-v1` は、上記の
self-authored value-generation proposal を、後日の本人受容が明示された場合だけ
bounded writeback へ進める contract である。

`self_model_value_acceptance_receipt` は元の value-generation receipt digest、
candidate digest set、accepted value refs、continuity recheck refs、future self
acceptance ref、Council resolution、Guardian boundary を束ねる。
受容対象は元の self-authored candidate set の subset に限定し、
`acceptance_mode=future-self-accepted-bounded-writeback`、
`integration_status=accepted-for-bounded-writeback`、
`future_self_acceptance_satisfied=true`、
`boundary_only_review=true`、
`accepted_for_writeback=true` を固定する。

Council と Guardian は境界違反を監査するだけで、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`external_truth_claim_allowed=false` を保つ。
writeback は `writeback_commit_digest` によって source generation、
accepted value digest、writeback ref、post-acceptance snapshot ref へ束縛し、
raw value payload や raw continuity payload は保存しない。

## reference runtime で固定した価値再評価・退役境界

`self-model-future-self-reevaluation-retirement-v1` は、過去に本人受容され
active writeback へ入った value を、後日の本人再評価が明示された場合だけ
active SelfModel writeback から退役させる contract である。

`self_model_value_reassessment_receipt` は元の value-acceptance receipt digest、
accepted value digest set、retired value refs、continuity recheck refs、
future self reevaluation ref、Council resolution、Guardian boundary を束ねる。
退役対象は元の accepted value set の subset に限定し、
`reassessment_mode=future-self-reevaluated-bounded-retirement`、
`integration_status=retired-from-active-writeback-archive-retained`、
`future_self_reevaluation_satisfied=true`、
`active_writeback_retired=true`、
`historical_value_archived=true` を固定する。

これは価値履歴の削除ではなく、active writeback からの退役である。
Council と Guardian は境界違反を監査するだけで、
`external_veto_allowed=false`、`forced_stability_lock_allowed=false`、
`external_truth_claim_allowed=false` を保つ。
retirement は `retirement_commit_digest` によって source acceptance、
retired value digest、retirement writeback ref、post-reassessment snapshot ref、
archival snapshot ref へ束縛し、raw value payload や raw continuity payload は保存しない。

## 残る未解決

- 外部 witness / Council review を長期的な本人の自由な価値生成とどう両立させるか
- 病理的な自己評価という判断を OS 内でどこまで扱い、どこから人間社会側の医療・法制度へ委ねるか
