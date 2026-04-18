# Naming Decisions ── 命名上の確定事項

[open-questions.md](open-questions.md) §「命名上の保留」の決着を記録する。
個別の決定は [decision-log/](decision-log/) にも残る。

## 決定事項

### Omoikane の表記

- **採用**: `Omoikane`（単一語、ハイフンなし）
- **却下**: `Omoi-Kane` / `OmoiKane` / `OMOIKANE`
- **理由**:
  - 古事記原文は「思兼」で 1 神名扱い（[etymology.md](../docs/00-philosophy/etymology.md)）
  - 國學院大學「神名データベース」も `Omoikane no Kami` として通名
  - ファイルパス・コード識別子で大文字小文字混在を避けたい（snake_case では `omoikane`）
- **強制範囲**:
  - 英文表記は `Omoikane` 統一
  - 日本語表記は **思兼神** または **オモイカネ**
  - コード識別子は `omoikane`（snake_case）/ `Omoikane`（PascalCase）/ `OMOIKANE`（定数のみ）
  - reference runtime は `naming-demo` / `NamingService` でこの方針を検証する

### サンドボックス自我の正式名

- **採用**: `Mirage Self`（日本語: **幻影自我** / かたい場面では **蜃気自我**）
- **却下**: `Yumi Self`（女性名連想で人称化が過剰） / `Phantom Self`（死霊連想で倫理的に重い）
- **理由**:
  - Mirage = 蜃気楼 = 「実体に似て、触れば消える」── L5 サンドボックス自我の性質を端的に表す
  - 「Self」を残すことで「人格として扱う倫理規約」（[ethics.md](../docs/00-philosophy/ethics.md) と
    [self-modification.md](../docs/04-ai-governance/self-modification.md)）を呼び起こす
  - 神話圏の語（Yumi 等）を流用するとメタファーが乱れる
- **強制範囲**:
  - ドキュメント本文で `Mirage Self` を統一
  - reference runtime のクラス名は将来 `MirageSelf` を採用予定（現状 `SandboxSentinel` は維持し、
    `MirageSelf` は別 namespace で並走可能性を残す）
  - glossary / self-modification.md / sandboxer 関連 IDL に明示
  - 略称は使わない（`MS` は他の意味と衝突）
  - `NamingService` は `SandboxSentinel` を **内部 alias** としてのみ許容する

## 適用ルール

- 既存ドキュメントの該当部分は順次反映する。**全置換は急がず**、各 PR で触れたら更新する
- コード識別子を変える self-modify は T-Operational 扱い（[amendment-protocol.md](../docs/04-ai-governance/amendment-protocol.md)）
- 表記の例外（引用元・歴史資料）は引用範囲を明示すれば許容

## 参照

- [etymology.md](../docs/00-philosophy/etymology.md)
- [glossary.md](glossary.md)
- [open-questions.md](open-questions.md)
- [decision-log/2026-04-18_naming-omoikane-and-mirage-self.md](decision-log/2026-04-18_naming-omoikane-and-mirage-self.md)
