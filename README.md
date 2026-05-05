# OmoikaneOS

> **思兼神（オモイカネ）** ── 高御産巣日神の子。天照大御神の諮問に応じて深く謀り、八百万神を統べて計画を実行した知慮の神。
> 出典: [古事記学センター 神名データベース 思兼神](https://kojiki.kokugakuin.ac.jp/shinmei/omoikanenokami/)

OmoikaneOS は、いずれ到来する **マインドアップロード（Mind Uploading）** のための基盤 OS の設計プロジェクトである。
現在の中心像は、脳波・心電・脈波・皮膚電気活動・呼吸に限らない
**あらゆる宣言済みの生体データ** から
その人に束縛された **体内状態の中間表現** を作り、そこから別モダリティの
生体データ、感情 proxy、思考圧 proxy を生成する **BioData Transmitter** を核に置く。
つまり `生体データ → internal body-state latent → 生体データ` を OmoikaneOS の
実装可能な入口とし、主観同一性や thought content の飛躍は
`mind-upload.com` の conflict sink に分離する。
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
references/          ── automation / builder 実行用の repo-local runbook
specs/                ── 機械可読な仕様（Codex 入力用）
agents/               ── 各サブエージェントの役割定義
src/                  ── Reference runtime（安全な最小実装）
tests/                ── Reference runtime の検証
meta/                 ── 用語集・決定履歴
```

最初に読むべきは [docs/00-philosophy/manifesto.md](docs/00-philosophy/manifesto.md) と [docs/01-architecture/overview.md](docs/01-architecture/overview.md)。
何から研究を始めるべきかは [docs/05-research-frontiers/README.md](docs/05-research-frontiers/README.md) にある。
Researcher の evidence seed や調査補助メモは [agents/researchers/](agents/researchers/) に置き、
人間用の自由記述ノート surface は持たない。
`docs/` 配下の Markdown は GitHub Wiki にも mirror する。
正本はこの repository の `docs/` で、wiki は閲覧用の索引として扱い、
更新時は `scripts/sync_docs_to_wiki.py --output-dir /path/to/omoikane.wiki` で再生成する。

## 現在の立ち位置

- これは **夢物語の設計図** であり、同時にその設計を壊さず試す **参考実装の実験場** である。
- 今日の技術で実装できない部分は多いが、L1/L4/L5 の統率や append-only ledger のような骨格は今から prototype 化できる。
- L6 では BDB（Biological-Digital Bridge）の bounded viability を proxy 実装し、ms 級 latency budget・fail-safe fallback・可逆な置換比率調整までは reference runtime で検証できる。
- L6 では BioData Transmitter も reference runtime 化し、人間から取られる神経・心血管・呼吸・皮膚・筋・眼・体温・運動・音声・生化学系などの宣言済み生体信号を catalog / family map に束縛し、体内状態 latent を経由して別モダリティの生体データ proxy を生成し、未知 target は汎用 biosignal proxy として digest-bound に扱い、複数日の latent digest から個人内 calibration profile と identity / loopback confidence gate を作る境界を検証できる。
- L6 では Observation Integration Workbench も reference runtime 化し、人類が取得・計測してきた観測 source と、過去に行われた測定方法・解析方法を taxonomy / method catalog / source bundle / integration graph / analysis plan / operator guide に束縛し、raw payload を保持せずに統合解析計画を作る境界を検証できる。
- automation は [Daily Automation Direction](references/daily-automation-direction.md) に従い、repo 内 gap または追跡可能な研究進展がある時だけ更新する。進展が無い日は no-op とし、意識再現や同一性達成を装う差分を作らない。
- このリポジトリは「設計が成熟するほど、必要な研究が明確になり、reference runtime も厚くなる」ことを目指す。

## すぐ動かせるもの

- `PYTHONPATH=src python3 -m unittest discover -s tests -t .`
- `PYTHONPATH=src python3 -m omoikane.cli demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli biodata-transmitter-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli neuro-integration-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli human-body-analysis-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli observation-integration-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli collective-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli memory-edit-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli memory-replication-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli semantic-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli procedural-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli cognitive-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-governance-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli patch-generator-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli diff-eval-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli sandbox-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli council-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli consensus-bus-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli trust-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1 --json`
- `PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile fork-request-v1 --json`
- `PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile inter-mind-negotiation-v1 --json`
- `PYTHONPATH=src python3 -m omoikane.cli builder-live-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli rollback-demo --json`
- `PYTHONPATH=src python3 -m omoikane.cli gap-report --json`

### 動かした時に何が見えるか

ここで「動かせる」と言っているものは、本番のマインドアップロード基盤ではなく、docs/specs/evals に書いた境界を reference runtime で確認するための小さな実行単位です。
`--json` 付きの demo は標準出力へ JSON を返します。
主に `policy_id`、`profile`、`status`、`validation.ok`、`receipt`、`ledger`、`digest`、`blocked` / `approved` のような値を見て、設計上の gate が期待どおり通るか、または止まるかを確認できます。

| コマンド群 | 実行するとあるもの | 実行してもないもの |
| --- | --- | --- |
| `PYTHONPATH=src python3 -m unittest discover -s tests -t .` | reference runtime、CLI、schema、eval 連携の回帰テスト結果 | 実環境の起動、外部サービス接続、研究上の正しさの証明 |
| `demo` | identity 作成、substrate allocation、ContinuityLedger、Council 承認、EthicsEnforcer veto の最小シナリオ | 意識・人格・同一性成立の主張 |
| `substrate-demo` / `connectome-demo` | substrate allocation / attestation / migration と、L2 connectome snapshot の validation summary | 実ハードウェア移行、実神経データの取り込み |
| `bdb-demo` / `biodata-transmitter-demo` / `neuro-integration-demo` / `human-body-analysis-demo` / `observation-integration-demo` / `collective-demo` | L6 interface の proxy contract、biosignal roundtrip、アンケート+EEG の digest-only fusion receipt、アンケート+EEG seed から fMRI / 脳オルガノイド expansion lane までの multi-application workbench、human body analysis package、人類の観測・計測 source と測定・解析 method catalog を raw payload なしで束縛する cross-domain analysis plan、collective identity の bounded merge / recovery receipt | 生体データの実測、身体状態の医学的診断、semantic thought content の復元、完全知識や真理統一の証明、意識再現、集合人格成立の証明 |
| `memory-edit-demo` / `memory-replication-demo` / `semantic-demo` / `procedural-demo` / `cognitive-demo` | MemoryCrystal、reversible memory edit、semantic / procedural projection、L3 reasoning failover の安全な代理シナリオ | 記憶の実改変、技能の実世界実行、汎用推論エンジン |
| `cognitive-audit-governance-demo` / `council-demo` / `task-graph-demo` / `consensus-bus-demo` / `trust-demo` / `trust-transfer-demo` | Council、TaskGraph、ConsensusBus、TrustService、audit governance の policy / receipt / timeout / quorum 結果 | 人間監督の代替、法的承認、外部組織の実署名 |
| `patch-generator-demo` / `diff-eval-demo` / `sandbox-demo` / `yaoyorozu-demo` / `builder-live-demo` / `rollback-demo` | Builder 系の patch plan、diff evaluation、sandbox freeze、worker dispatch、temp workspace 実行、rollback receipt | 現 checkout への無断永続変更、本番 worker 実行、秘密情報を含む長いログ保存 |
| `gap-report --json` | open question、missing file、inventory drift、stub、生成物混入などの count と all-zero gate | 問題の自動解決、研究判断の代替 |

大きな JSON が出る場合は、先頭の summary field と末尾の `validation` / `all_zero` を見れば十分です。

## GitHub Release / Package

GitHub 上の配布 surface は [GitHub Release and Package Runbook](references/github-release-package.md) に固定する。

- `main` へ push すると `.github/workflows/package.yml` が wheel / sdist を workflow artifact として build し、GHCR に `main` / `sha-<short-sha>` image を publish する。
- `v*.*.*` tag を push すると `.github/workflows/release.yml` が full test、release manifest、gap-report、wheel install smoke を通してから GitHub Release asset と GHCR release image を publish する。
- Python wheel / sdist は GitHub Releases の添付 asset、GitHub Packages は `ghcr.io/yasufumi-nakata/omoikane` の container package として扱う。
`all_zero: true` は repo-local な監査項目が 0 件という意味であり、研究課題が解けたという意味ではありません。

## ライセンス

未定。マインドアップロード基盤の知的財産帰属は、人類規模の議論を要する。
