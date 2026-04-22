# Repo Coverage Checklist

gap 選定前に最低限確認する repo 内サーフェスです。
すべてを毎回全文精読する必要はありませんが、対象 gap に関係する層は必ず跨いで確認します。

## Truth Source

- `README.md`
- `docs/07-reference-implementation/README.md`
- `meta/open-questions.md`
- `specs/catalog.yaml`
- `specs/interfaces/**/*.idl`
- `specs/schemas/README.md`

## Runtime

- `src/omoikane/reference_os.py`
- 対象 surface の service 実装
- `src/omoikane/cli.py`
- `src/omoikane/self_construction/gaps.py`

## Verification

- 対象 surface の `tests/unit/` と `tests/integration/`
- 対応する `evals/` と README
- schema / IDL / docs の field 名と validation 条件

## Decision Hygiene

- 近い日付の `meta/decision-log/` を見て、何が既に close 済みかを確認する
- 「broad future work」ではなく、今この repo で machine-checkable に閉じられる残差を選ぶ
- 既存 decision と衝突しそうなら、runtime を読んでから追記方針を決める
