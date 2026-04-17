# Agent Trust Management

各 Agent には **trust score** が付与され、召集権・議決重み・本体反映の可否に影響する。

## スコア構造

```yaml
trust:
  agent_id: <id>
  global_score: <0.0-1.0>
  per_domain:
    memory_editing: 0.85
    substrate_migration: 0.40
    self_modify: 0.10
  history:
    - { ts, event_type, delta, evaluator }
  pinned_by_human: <bool>     # yasufumi が固定承認したか
```

## 更新トリガ

- **+** Council が判断品質を高評価
- **+** Guardian の事後検査で問題なし
- **+** 本人フィードバック（"good"）
- **−** Guardian veto を受けた
- **−** 退行検出
- **−** 本人フィードバック（"bad"）
- **−−** 倫理違反

## 閾値

| 操作 | 必要 trust |
|---|---|
| Council 召集対象 | 0.5 |
| 議決重み付与 | 0.6 |
| 本体反映可 | 0.8 |
| Self-Modify 関与可 | 0.95 |
| Guardian 役 | 0.99（人間検証必須） |

## Cold Start

新 Agent の初期 trust は 0.3。一定数の低リスク案件で実績を積んでから昇格。

## Trust の透明性

- 本人はいつでも全 Agent の trust を閲覧可能
- 本人は手動で trust を上書きできる（pinned_by_human）

## Trust 暴走の防止

- LLM 系 Agent が「trust を上げるための判断」をするインセンティブを持たないよう、
  Guardian は **trust 最大化行動の検出** を試みる（オープン研究領域）。

## 未解決

- Trust の **substrate 跨ぎ妥当性**
- Agent 自身による自己 trust 改ざん攻撃
- 集合的な trust 操作（複数 Agent が結託）
