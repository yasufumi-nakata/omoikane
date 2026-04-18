# Versioning ── OS バージョン管理規約

OmoikaneOS は「機械可読契約」「実装」「規約レイヤー」が混在するため、
バージョン体系も **複数を組み合わせる** ことを fix する。

## 体系一覧

| 対象 | 形式 | 例 | 背景 |
|---|---|---|---|
| **IDL / schema** | semver `MAJOR.MINOR.PATCH` | `agentic.council.v0` (`v0.x.y`) | 機械検証可能・破壊的変更を区別したい |
| **Reference runtime** | semver | `0.3.1` | 通常 OSS 慣習に合わせる |
| **規約レイヤー（T-Core/T-Kernel）** | calver `YYYY.MM` + 改正履歴 | `2026.04` | 人間社会フローと連動。semver は不適 |
| **Continuity / Identity record** | monotonic integer | `cursor: 142` | append-only、比較可能性が必要 |
| **Catalog snapshot** | calver + sha | `2026.04+sha=abcd1234` | reproducibility |

## semver 適用ルール（IDL / schema / runtime）

- **MAJOR**: 既存 consumer の振る舞いを壊す変更
  - 例: `bdb.transduce_cycle` の latency_budget を縮める、operation 削除、required field 追加
- **MINOR**: 後方互換な追加
  - 例: optional field 追加、新 operation 追加
- **PATCH**: 振る舞いに影響しない修正
  - 例: docstring、example の typo、validation メッセージ改善

namespace 自体に `v0` を含めるのは「**破壊的版を別 namespace で並走** させる」
ためで、semver と独立。`v0 → v1` は MAJOR でも namespace 変更が必要なほど大きいときだけ。

## calver 適用ルール（規約レイヤー）

- 規約改正は基本「年月単位」で発効
- 同月内の複数改正は `2026.04+rev2` のように revision 番号
- 規約は [amendment-protocol.md](../04-ai-governance/amendment-protocol.md) を経て発効
- semver と違い、人間 reviewer が「同月内の整合性」を担保する

## 互換性宣言

各 IDL / schema は frontmatter / footer に `compatibility.stability` を持つ:

| 値 | 意味 |
|---|---|
| `bootstrap` | reference runtime の最小契約。MAJOR 変更を予期して使う |
| `stable` | 後方互換を約束。MAJOR は事前告知必須 |
| `frozen` | 変更禁止。代替は別 namespace で導入 |

reference runtime はすべて `bootstrap`。`stable` への昇格基準は別途設計。

## reference runtime の扱い

- `release_manifest.schema` に「runtime semver」「IDL semver 表」「規約 calver」を集約
- `governance.versioning.v0` IDL は **持たない**（version は静的 manifest で十分）
- `PYTHONPATH=src python3 -m omoikane.cli version-demo --json` で manifest を生成・検証する
- decision-log に `2026-04-18_versioning-policy.md`

## 思兼神メタファー

神話では神々の世代（高天原 → 葦原中国）が calver 的に区切られ、神々個別の役割（IDL）は
個別に進化する。版管理は **神話の時間構造** に倣う。

## 関連

- [milestones.md](milestones.md)
- [dependency-graph.md](dependency-graph.md)
- [../04-ai-governance/amendment-protocol.md](../04-ai-governance/amendment-protocol.md)
