# Omoikane Operating Playbook

hourly builder や broad automation が repo 内 gap を埋める時の最小 runbook です。
thin prompt でも、次の順序は崩しません。

## 1. Preflight

- `git status --short --branch` を確認する
- `git pull --ff-only` を実行する
- pull が失敗したら更新作業へ進まず、exact blocker と再開条件だけを報告する

## 2. 初期トリアージ

- `meta/open-questions.md`
- `docs/07-reference-implementation/README.md`
- `specs/catalog.yaml`
- `PYTHONPATH=src python3 -m omoikane.cli gap-report --json`

`gap-report` が all-zero でも停止しません。
truth-source と現行 runtime を読み、repo 内で machine-checkable に閉じられる残差を拾います。
最新 decision log 日付の `residual gap` / `unresolved gap` が `gap-report` に出ている場合は、
それも next durable gap 候補として同列に扱います。

## 3. ギャップ選定ルール

- docs-only の整文より、reference runtime / schema / eval / CLI / tests の具体化を優先する
- `future work` / `未実装` が current truth-source に残るなら最優先で閉じる
- truth-source が clean でも、automation 自体を阻害する欠落は優先して埋める
- repo 外依存が強い open-world 実装より、repo 内で deterministic に検証できる contract を優先する

## 4. 実装範囲

- 必要なら `src/`, `tests/`, `docs/`, `specs/`, `evals/`, `agents/`, `meta/decision-log/` を同時に更新する
- decision log は「なぜこの option を採ったか」「残差がどこへ縮小したか」を短く残す
- raw payload や外部 transcript を保存せず、ref / digest / bounded receipt へ縮約する方針を維持する

## 5. 検証

- `PYTHONPATH=src python3 -m unittest discover -s tests -t .`
- `PYTHONPATH=src python3 -m omoikane.cli gap-report --json`
- 追加した surface に CLI があるなら demo を 1 回実行して shape を確認する

## 6. 完了条件

- 実装・docs・tests が同じ contract を共有している
- `gap-report` が新しい residual gap を残していない
- meaningful change なら commit して `origin` へ push する
