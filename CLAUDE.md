# CLAUDE.md ── AI 向け作業指針

このリポジトリは **設計コーパス + reference runtime** である。
Claude / Codex / 任意の LLM エージェントがこのファイルを読んだ時、以下の規約に従うこと。

## 1. 最優先原則

1. **書くのは設計、生むのはコード。コードは別所で AI が生む。**
   ここでは docs/specs/evals に加え、`src/` と `tests/` に限って reference implementation を更新してよい。
   ただし reference runtime は「安全な最小実装」に留め、本番実装や意識主張を持ち込まない。
2. **思兼神メタファーを保つ。** 用語選択・モジュール命名は神話メタファーと整合させる（[meta/glossary.md](meta/glossary.md) 参照）。
3. **未来からの逆算で書く。** 「今できる」ではなく「マインドアップロードが成立する条件」を起点に設計する。
4. **未解決領域は隠さない。** 解けない部分は `docs/05-research-frontiers/` に明示する。曖昧に埋めない。

## 2. 役割分担

- **人間 yasufumi**: 研究課題を解く。意図を述べる。設計を承認する。
- **AI（Council 役）**: 設計の整合性を保つ。新しい諮問を分解し、サブエージェントに発注する。
- **AI（Builder 役 / Codex 等）**: このリポジトリ内の `src/`, `tests/`, `specs/`, `evals/` を実装・同期する。
- **AI（Researcher 役）**: 未解決領域に対して文献調査・実験提案を行う。
- **AI（Guardian 役）**: 倫理・安全規約違反を検出する。

各役割の詳細は [docs/04-ai-governance/](docs/04-ai-governance/) を参照。

## 3. 編集時のチェックリスト

設計ドキュメントを変更するときは：

- [ ] [meta/decision-log/](meta/decision-log/) に決定の根拠を残したか
- [ ] [docs/05-research-frontiers/](docs/05-research-frontiers/) に新しい未解決問題が生まれていないか
- [ ] [meta/glossary.md](meta/glossary.md) に新語が追加されていないか
- [ ] 神話メタファーと矛盾していないか
- [ ] 「人間が後で研究する箇所」と「reference runtime で今すぐ検証できる箇所」が明示されているか

## 4. 禁止事項

- 仕様や倫理境界を読まずにコードだけ先行させること
- 「いずれ解決される」で済ませること（必ず研究課題として登録する）
- 倫理問題（同一性・複製・死・差別）を回避すること
- 既存ファイルを Read せずに上書きすること

## 5. Subagent 召喚規約（Codex 含む）

Codex 等の外部エージェントを呼ぶときは：

1. 召喚先に `agents/` 配下の役割定義を必ず添付する
2. 結果は `meta/decision-log/` に記録する
3. Builder 役の書き込み先は `src/`, `tests/`, `specs/`, `evals/` に限定し、docs と整合を保つ

詳細は [docs/04-ai-governance/codex-as-builder.md](docs/04-ai-governance/codex-as-builder.md)。
