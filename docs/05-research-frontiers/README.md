# Research Frontiers ── 人間 yasufumi が研究すべき未解決領域

このディレクトリは **AI が解けない／設計判断できない領域** を集約する。
人間 yasufumi（あるいは同等の研究者）が学術・実験的に解いて、ここに結果を書き込む。

## 優先度（暫定）

| Tier | 重要度 | 例 |
|---|---|---|
| **T0** | OS が成立するために絶対必要 | Qualia 表現、漸進置換、スキャン精度 |
| **T1** | OS の信頼性に必要 | 連続性測定、量子連続性、長期保管 |
| **T2** | 社会実装に必要 | 法的人格、governance、経済 |
| **T3** | 拡張機能 | inter-mind merge, 集合知 |

## 一覧

### T0 ── 必須

- [qualia-encoding.md](qualia-encoding.md) ── 主観経験を表現できるか
- [gradual-replacement.md](gradual-replacement.md) ── 漸進置換の最小単位と可逆性
  （BDB v0 の bounded viability smoke は reference runtime に追加済み）
- [scan-fidelity.md](scan-fidelity.md) ── スキャン精度の必要十分性
- [consciousness-substrate.md](consciousness-substrate.md) ── 意識を生む基板条件

### T1 ── 信頼性

- [qualia-measurement.md](qualia-measurement.md) ── 主観時間連続性の物理測定
- [quantum-continuity.md](quantum-continuity.md) ── 量子状態の連続性証明
- [long-term-storage.md](long-term-storage.md) ── 100-1000 年保管メディア
- [twin-integration.md](twin-integration.md) ── 並走時の二重身統合
- [substrate-zoology.md](substrate-zoology.md) ── 各 substrate の妥当性
- [death-and-continuity.md](death-and-continuity.md) ── 死の定義と連続性

### T2 ── 社会実装

- [legal-personhood.md](legal-personhood.md) ── アップロード自我の法的人格
- [governance.md](governance.md) ── OS 外の意思決定機構
- [sustainable-economy.md](sustainable-economy.md) ── 持続的計算資源モデル
- [consent-validity.md](consent-validity.md) ── 強制下同意の検出

### T3 ── 拡張

- [inter-mind-merge.md](inter-mind-merge.md) ── 自我間の思考融合
- [collective-personhood.md](collective-personhood.md) ── Collective の人格
- [memory-edit-ethics.md](memory-edit-ethics.md) ── 記憶編集の倫理境界

## 研究ノートの書き方

各ファイルは以下の構造を持つ：

```markdown
# <題目>

## 問題定義
（厳密に何が解けていないかを述べる）

## 既知の進捗
（学界での到達点）

## ブロッキング要因
（なぜ解けないか）

## 暫定運用方針
（解けるまで OmoikaneOS はどう振る舞うか）

## 解決時のシステムへの影響
（解けたら設計のどこが変わるか）

## 関連文献／実験
```

## ステータス

各ファイルの先頭に：

```yaml
status: open|in-progress|partial-solution|solved
last_revisit: <YYYY-MM-DD>
researcher: <name>
```
