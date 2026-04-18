# OmoikaneOS

> **思兼神（オモイカネ）** ── 高御産巣日神の子。天照大御神の諮問に応じて深く謀り、八百万神を統べて計画を実行した知慮の神。
> 出典: [古事記学センター 神名データベース 思兼神](https://kojiki.kokugakuin.ac.jp/shinmei/omoikanenokami/)

OmoikaneOS は、いずれ到来する **マインドアップロード（Mind Uploading）** のための基盤 OS の設計プロジェクトである。
本リポジトリは、未来の AI 群が読み解いて自律的に構築できる **設計言語（design corpus）** と、
その設計を崩さず検証するための **reference implementation** を同居させた workspace である。

---

## このリポジトリは何か

- **設計・spec・評価・reference runtime** を同じ repo で扱う。
- `src/` 配下の実装は「意識を主張しない安全な reference runtime」であり、本番実装ではない。
- 人間（yasufumi）は **意図** と **未解決の研究課題** だけを供給する。
- AI が AI を呼び、AI が AI を統率する世界 ── 思兼神が八百万神を統べた構図 ── を最初から前提にする。

## なぜ「Omoikane」か

マインドアップロードに必要なのは演算力ではなく、**「諮問に対して計画を立て、無数のサブエージェントに役割を割り振り、首尾よく実行を取り計らう知慮」** である。
記紀において思兼神が果たした役割そのものが、この OS のカーネルに要求される機能と一致する。

| 神話の構図 | OmoikaneOS での対応 |
|---|---|
| 天照（諮問者） | 人間ユーザ／アップロード対象の自我 |
| 思兼神（思慮の神） | OS カーネルの統率層（Council） |
| 八百万神（実行神群） | サブエージェント／Codex ビルダー群 |
| 祭祀の取り計らい | タスク分解・合議・実行 |

## このリポジトリの読み方

```
docs/00-philosophy/   ── なぜ作るか。倫理・自我の連続性
docs/01-architecture/ ── レイヤード設計の全体図
docs/02-subsystems/   ── 各層の詳細設計
docs/03-protocols/    ── データ形式と通信規約
docs/04-ai-governance/── AI が AI を統率する規約
docs/05-research-frontiers/ ── 人間 yasufumi が研究する未解決領域
docs/06-roadmap/      ── 依存関係と里程標
specs/                ── 機械可読な仕様（Codex 入力用）
agents/               ── 各サブエージェントの役割定義
src/                  ── Reference runtime（安全な最小実装）
tests/                ── Reference runtime の検証
research/             ── 人間が書く研究ノート（自由記述）
meta/                 ── 用語集・決定履歴
```

最初に読むべきは [docs/00-philosophy/manifesto.md](docs/00-philosophy/manifesto.md) と [docs/01-architecture/overview.md](docs/01-architecture/overview.md)。
何から研究を始めるべきかは [docs/05-research-frontiers/README.md](docs/05-research-frontiers/README.md) にある。

## 現在の立ち位置

- これは **夢物語の設計図** であり、同時にその設計を壊さず試す **参考実装の実験場** である。
- 今日の技術で実装できない部分は多いが、L1/L4/L5 の統率や append-only ledger のような骨格は今から prototype 化できる。
- L6 では BDB（Biological-Digital Bridge）の bounded viability を proxy 実装し、ms 級 latency budget・fail-safe fallback・可逆な置換比率調整までは reference runtime で検証できる。
- このリポジトリは「設計が成熟するほど、必要な研究が明確になり、reference runtime も厚くなる」ことを目指す。

## すぐ動かせるもの

- `python3 -m unittest discover -s tests -t .`
- `PYTHONPATH=src python3 -m omoikane.cli demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli cognitive-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli sandbox-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli council-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli trust-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli gap-report --json`

## ライセンス

未定。マインドアップロード基盤の知的財産帰属は、人類規模の議論を要する。
