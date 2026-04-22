# Verification Checklist

completion 宣言前に通す確認項目です。

## 必須コマンド

- `PYTHONPATH=src python3 -m unittest discover -s tests -t .`
- `PYTHONPATH=src python3 -m omoikane.cli gap-report --json`

## 追加確認

- 変更 surface に対応する CLI demo があれば `--json` で 1 回確認する
- diff を見直し、docs / schema / tests / decision log の naming drift が無いか確認する
- new field を追加した場合は integration test で shape を押さえる

## Git Hygiene

- unrelated change を巻き戻さない
- meaningful change のみ commit する
- commit message は gap の closure が分かる語にする
- push 後に local branch が `origin` と同期していることを確認する
