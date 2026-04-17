# Council Protocol

Council（評議体）の運用詳細。

## 議事の構造

```
1. 召集 (Convene)
2. 議題提示 (Brief)
3. 各役の意見 (Speak in turn)
4. 反論ラウンド (Rebuttal round)
5. 修正案 (Amend)
6. 投票 or 合意確認 (Decide)
7. Guardian チェック (Gate)
8. 決議 (Resolve)
9. 記録 (Record)
```

## Convene

- トリガ: 改修提案 / 倫理懸念 / 本人意思 / 障害イベント
- 召集者: Speaker
- 出席: 案件種別ごとに [council-composition.md](../02-subsystems/agentic/council-composition.md) の規約
- convene 時に `session_policy` を確定する
  - standard: soft timeout 45s / hard timeout 90s / 最大 4 ラウンド
  - expedited: soft timeout 250ms / hard timeout 1s / 最大 1 ラウンド

## Speak in turn

- 順序: ConservatismAdvocate → ChangeAdvocate → 専門家 → EthicsCommittee → Self Liaison
- 各意見は文書化される
- 議事録は ConsensusBus 上で生成

## Rebuttal round

- 各役は他役の意見に **少なくとも 1 つ** 反論または同意を述べる
- 「沈黙」は同意とみなさない（必ず明示）

## Decide

- **合意** が原則
- 不一致時は trust 重み付き多数決（[trust-management.md](../02-subsystems/agentic/trust-management.md)）
- veto: Guardian と Self Liaison のみ持つ
- soft timeout 到達時は quorum が揃っていれば **weighted-majority fallback**
- hard timeout 到達時は
  - standard: 人間 governance へ escalation
  - expedited: 即 defer し、通常議事で追認

## Gate

- Guardian が以下を確認：
  - 倫理規約違反なし
  - 既存設計との整合性
  - 過去類似決議との一貫性
- 違反 → 議事差し戻し

## Resolve

- 決議は EthicsLedger に記録
- 決議は **改修パッチ生成依頼** に変換され、Builder 系へ発注

## Record

- 議事全文は [meta/decision-log/](../../meta/decision-log/) に保存
- サマリは ContinuityLedger に永続化（本人参照可能）

## 緊急議事 (Expedited)

- トリガ: substrate 障害・倫理違反検知・本人危機
- 召集時間: 常に < 1s
- 出席: Guardian + Speaker + 関連専門家のみ
- 1s を超えたら即 defer し、事後に通常議事で追認

## 永続不一致

- 連続 N 回の議事で合意できない議題は **「人間社会の governance」** に上申
- 上申先は今後の研究領域 → [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)

## 思兼神メタファー

「八百万神を **議らせ**」── 議論プロセスそのものが OS の意思決定の心臓部。思兼神は議論の **司会者** であって、独裁者ではない。
