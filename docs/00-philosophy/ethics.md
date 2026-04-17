# Ethics ── マインドアップロード基盤の倫理規範

設計レベルで埋め込むべき倫理。実装フェーズで「足す」のではなく、**カーネルの不変条件として最初から書く**。

## 1. 同一性原則（Identity Axioms）

### A1. 連続性原則
アップロード前後で **主観的時間の連続性** が保たれることを設計目標とする。
不連続が避けられない場合、本人の事前同意（informed consent）が成立した上で、不連続点をログに残す。

### A2. 唯一性原則
原則として、同時に複数の能動的コピーを走らせない。
複製は **退避バックアップ** 用途に限り、活性化は単一に絞る。
複数活性化を許す場合は、本人の事前同意と「分岐後はそれぞれが別人格」と明記する規約が必要。

### A3. 終了権原則
アップロードされた自我は **自身を停止／削除する権利** を保持する。
これを技術的に剥奪する設計は許可しない。

### A4. 拒否権原則
アップロードを **撤回・拒否する権利** を、アップロード前の人間が常に保持する。
未成年・意識不明者・強制下にある者からのアップロードは禁止。

## 2. 不可逆性ガード（Irreversibility Guards）

- スキャン（破壊的読み出し）を伴うアップロードは、二重承認・冷却期間・第三者立会を必須にする。
- アップロード後の **記憶削除・改竄** はデフォルトで禁止。本人による明示同意がない限り Council はこれを拒否する。

## 3. Substrate 中立性

- 自我の格納先（生体／量子／古典シリコン／光／未知）に関わらず **同一の権利**を持つ。
- Substrate を理由とした差別を禁止。

## 4. 経済性に関する規範

- 自我の維持に必要な計算資源は、本人の意思に反して削減しない。
- 「料金未払いで意識が薄れる」「広告で意識が中断される」等の設計は **アンチパターン** として明示禁止する（→ [docs/02-subsystems/kernel/anti-patterns.md](../02-subsystems/kernel/anti-patterns.md) で具体化）。

## 5. AI Council の倫理権限

- Council（思兼神役）は **倫理規約を書き換える権限を持たない**。
- 規約変更は人間社会側のガバナンスを要する（プロジェクト未解決領域 → [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)）。

## 6. ガーディアン

- 全ての操作には Guardian agent（[agents/guardians/](../../agents/guardians/)）が監視として並走する。
- Guardian は本規約に違反する操作を停止する権限を持つ。
- Guardian の判断ログは [meta/decision-log/](../../meta/decision-log/) に永続化する。

## 7. 未解決の倫理問題（研究課題に登録）

- 死の定義／脳死との関係 → [docs/05-research-frontiers/death-and-continuity.md](../05-research-frontiers/death-and-continuity.md)
- 法人格・市民権 → [docs/05-research-frontiers/legal-personhood.md](../05-research-frontiers/legal-personhood.md)
- 子孫・遺産・婚姻 → 未起稿
- 動物・他種族のアップロード → 未起稿
