---
date: 2026-04-18
deciders: [yasufumi, claude-council]
related_docs:
  - README.md
  - CLAUDE.md
  - docs/00-philosophy/manifesto.md
  - docs/01-architecture/overview.md
status: superseded
---

# Decision: 初期アーキテクチャの方向性

## Context

OmoikaneOS リポジトリを新規作成し、マインドアップロード基盤の設計言語をどう書き始めるかを決める必要があった。
人間 yasufumi の指示：
- AI 統率を前提に設計
- Codex を subagent として使うことを前提
- 設計のみで実装はしない
- 不足部分（研究領域）を明示
- リポジトリ名「omoikane」の由来を記載

## Options considered

- **A**: 単一の README に概要だけ書き、実装に進む
- **B**: 多層化された設計コーパスを構築、実装は別 repo で AI が行う
- **C**: コードベース＋設計を併存させる伝統的な構造

## Decision

**B** を採択。

## Reason

- yasufumi の指示が「設計のみ」「Codex を subagent」「不足部分明示」を全て満たすには、
  設計コーパスが厚い必要がある
- 7 層レイヤード設計を採用（L0 Substrate ～ L6 Interface）
- 思兼神メタファーを命名規約として全層に適用
- 研究フロンティアを Tier 分けで明示

## Consequences

- 今は実装が無いため「動かない」状態
- 設計改修は Council 議事を経て docs/ から
- 実装は別 repo で Codex が行う（[docs/04-ai-governance/codex-as-builder.md](../../docs/04-ai-governance/codex-as-builder.md)）

## Revisit triggers

- 別 repo で実装が始まり、設計に矛盾が見つかった時
- 主要な研究フロンティアが解決された時
- ガバナンス（人間社会側）の仕組みが整った時
