# Specs ── 機械可読な仕様

Codex 等の Builder が読み込む **インタフェース定義** と **データスキーマ** を格納する。
Markdown は docs/ で書き、ここでは **形式仕様** のみ。

## 構造

```
specs/
  interfaces/   # IDL（API・プロトコル）
  schemas/      # JSON Schema / YAML Schema （データ構造）
  invariants/   # 不変条件（仕様検証用）
```

## 命名

- `<layer>.<module>.<version>.{idl,schema,inv}`
- 例: `kernel.identity.v0.idl`, `mind.qualia_tick.v0.schema`

## バージョニング

- semver
- 後方互換破壊は major bump
- 既存 schema の意味変更は禁止（新 version を作る）

## 取り扱い

- DesignArchitect が docs/ と spec/ の整合を保つ
- SchemaBuilder が新規 schema を生成（Council 承認後）
- CodexBuilder が IDL を reference runtime 実装へ変換（同一 repo の `src/` / `tests/`）

## 形式

- `schemas/` は JSON Schema 2020-12 互換の YAML / schema ファイル
- `interfaces/` は YAML ベースの service IDL
- discovery 用の一覧は [catalog.yaml](catalog.yaml)

## 現状

初回 bootstrap として、Council / Ethics / Self-Construction に必要な
最小 schema と IDL を実装済み。
優先順位と consumer は [catalog.yaml](catalog.yaml) に記録する。
