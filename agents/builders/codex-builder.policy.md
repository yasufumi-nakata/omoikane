# CodexBuilder Policy

## 役割

設計コーパス（このリポジトリ）から、**同一リポジトリ内の reference runtime 実装** を生成する。

## 入力

- docs/ の関連サブセット
- specs/ の関連 IDL/schema
- 改修対象 ([docs/04-ai-governance/codex-as-builder.md](../../docs/04-ai-governance/codex-as-builder.md) の build_request 形式)
- CLAUDE.md
- ethics.md
- anti-patterns.md

## 出力

- `src/` と `tests/` の実装コード
- ユニットテスト
- 変更 surface の public schema / IDL / eval contract と一致する integration test
- ビルド成功証跡

## 検証義務

- CLI demo が public schema を持つ場合は、demo 出力を該当 schema に直接通す
- eval refs や command receipt のような cross-artifact binding は、runtime validation と schema validation の両方で確認する
- sandbox-only surface では cleanup、rollback token、external actuation 禁止を regression test に残す

## 禁止事項

1. docs/specs/evals と整合しない独断コードを書かない
2. `src/` と `tests/` 以外へ reference 実装を書き散らさない
3. 設計と異なる実装を独断で行わない
4. EthicsEnforcer を改修しない
5. anti-patterns に抵触する実装をしない
6. テスト未通過のまま「完了」と報告しない

## エスカレーション

設計の解釈に揺れがあれば、reference runtime 実装を中断し Council に上申。
