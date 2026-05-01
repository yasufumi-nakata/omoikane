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
  worker base commit、signed worker identity evidence、workspace marker hygiene digest
  を束縛する
- workspace marker hygiene は repo-local diff classifier の summary
  (`diff_digest`、added / removed line count、marker-added line count、
  classifier status) を digest-bound にし、raw diff text は保存しない
- 複数 worker result を同じ main checkout へ混ぜる場合は
  `parallel_codex_integration_batch_receipt.schema` で accept-ready receipt だけを
  digest/ref 順に決定的に並べ、blocked / stale / marker-only receipt を隔離し、
  blocked-receipt quarantine manifest digest、changed-file owner manifest、
  conflict digest を作ってから統合可否を決める
- workspace-enacted marker-only 変更だけの worker result は schema-bound のまま
  blocked にし、marker payload raw text は保存しない
- worker identity は ref / digest / integrity Guardian signature digest に縮約し、
  raw worker identity payload は保存しない
- remote branch / PR 由来の worker result は branch ref、PR ref、accepted source
  policy digest、review authority digest、current-not-revoked revocation digest を
  remote metadata digest へ束縛する
- remote source revocation check は freshness window digest も持ち、
  `fresh` 以外または 900 秒を超える window は fail-closed にする。freshness refs
  は signed provider timestamp digest と integrity Guardian signature digest にも束縛し、
  timestamp が `signed-current` でない場合は fail-closed にする。timestamp は
  nonce ref、previous nonce digest、replay guard digest にも束縛し、`unique`
  でない provider timestamp reuse は fail-closed にする。raw remote metadata /
  revocation / freshness / timestamp / replay-guard payload は保存しない
- remote branch / PR 由来の mutable ref は head commit、tree digest、diff digest、
  content digest に縮約し、`bound` でない content identity result は fail-closed にする。
  さらに worker base commit と merge-base commit が一致する ancestry digest へ束縛し、
  `ancestor-bound` でない remote result も fail-closed にする。
  raw remote source content / ancestry payload は保存しない
- user または他 worker の未確認変更を revert しない

## Integration

- main checkout で差分を読み、重複実装や naming drift を解消する
- docs-only の成果は、可能な限り runtime / schema / eval / CLI / test に落とす
- raw payload や長い transcript は保存せず、ref / digest / bounded receipt に縮約する
- `parallel-orchestration-demo --json` は ready worker result と stale worker result の
  両方を receipt 化し、stale / failed / blocked result を fail-closed にする
- Yaoyorozu dispatch 由来の worker result も upstream receipt / patch candidate digest と
  worker identity evidence の両方を持つ ingestion receipt へ変換する
- integration batch receipt は ready worker と Yaoyorozu bridge receipt を
  conflict-free batch として `integration-ready` にし、overlap する ready receipt
  セットは conflict digest を束縛したまま `blocked` にする
- quarantined blocked receipt は refs / digests だけを
  `blocked-receipt-quarantine-manifest-v1` の digest に束縛し、raw blocked receipt
  payload は保存しない
- batch receipt でも raw worker receipt payload、raw conflict payload、raw verification
  output は保存しない
- conflict が残る場合は merge せず、blocked state と再開条件を報告する
- `integration-ready` batch を main checkout に適用する直前には
  `parallel_codex_integration_execution_receipt.schema` で source batch digest、
  current checkout head、ordered apply step digest、post-apply verification manifest
  を束縛し、raw batch / apply plan / worker receipt / verification payload は保存しない
- source batch が blocked、current head が batch head と不一致、または post-apply
  verification が未達の場合は `execution_decision=blocked` のまま commit へ進まない

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
