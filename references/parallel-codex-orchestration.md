# Parallel Codex Orchestration

hourly builder や broad automation が複数 Codex worker / subagent / 外部
`codex exec` を使う時の repo-local runbook です。

## Purpose

- main checkout の pull-first gate を単一の authority として保つ
- worker ごとの write scope を分け、同じ file set を同時に編集しない
- subagent の成果を main checkout に取り込む前に、schema / eval / docs / tests の
  contract drift を確認する
- failed worker や stale worker の成果を、検証なしで main に混ぜない

## Gate Order

1. main checkout で `git status --short --branch` を確認する
2. main checkout で `git pull --ff-only` を実行する
3. pull が失敗した場合は worker を起動せず、exact blocker と再開条件だけを報告する
4. pull が通過した後だけ、並列探索や bounded worker 実装を開始する

## Worker Boundaries

- 各 worker には ownership を明示する
- implementation worker は互いに disjoint な file set を持つ
- explorer worker は編集しない
- worker result は patch / changed file list / verification result の形で受け取る
- worker result は main checkout へ混ぜる前に `parallel_codex_worker_result_receipt.schema`
  で patch digest、changed file manifest digest、verification manifest digest、
  worker base commit を束縛する
- user または他 worker の未確認変更を revert しない

## Integration

- main checkout で差分を読み、重複実装や naming drift を解消する
- docs-only の成果は、可能な限り runtime / schema / eval / CLI / test に落とす
- raw payload や長い transcript は保存せず、ref / digest / bounded receipt に縮約する
- `parallel-orchestration-demo --json` は ready worker result と stale worker result の
  両方を receipt 化し、stale / failed / blocked result を fail-closed にする
- conflict が残る場合は merge せず、blocked state と再開条件を報告する

## Verification

最低限、main checkout で次を実行する。

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -t .
PYTHONPATH=src python3 -m omoikane.cli gap-report --json
```

追加した surface に CLI demo がある場合は、該当 demo の `--json` smoke も実行する。

## Handoff

- commit は main checkout からだけ作成する
- commit message は閉じた gap が分かる名前にする
- push 後に `git status --short --branch` で `origin/main` との同期を確認する
- recurring automation の場合は automation memory に run note を残す
