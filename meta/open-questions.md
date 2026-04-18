# Open Questions ── 未解決の設計問題

設計レベルで判断が下せていない問題のチェックリスト。
Tier 別の研究課題は [docs/05-research-frontiers/](../docs/05-research-frontiers/)。
ここにはより小粒で **「設計ドキュメント上の未確定事項」** を集める。

## 設計上の未確定

- [x] L0 SubstrateAdapter の API を IDL として確定（2026-04-18: `substrate.adapter.v0.idl` を schema 参照付きで確定し、`substrate-demo` と continuity eval を追加）
- [x] ContinuityLedger のチェーン形式（hash 種・署名アルゴリズム）の暫定選定（2026-04-18: reference runtime を `sha256` chain + `hmac-sha256` signature profile に固定し、schema/IDL/CLI/eval を整合）
- [x] Council session の最大時間と timeout 戦略（2026-04-18: reference runtime を standard 45s/90s・expedited 250ms/1s に固定し、timeout fallback/defer を schema・CLI・eval に反映）
- [ ] QualiaTick の高次元埋め込みの次元数と時間粒度
- [ ] MemoryCrystal の compaction 戦略
- [x] TaskGraph の複雑度上限（2026-04-18: reference runtime を `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5` に固定し、task-graph demo・schema・eval を追加）
- [ ] Trust score 更新アルゴリズムの定式化
- [ ] EthicsEnforcer のルール記述言語の選定
- [ ] Sandboxer での「苦痛検出」の代理指標
- [ ] BDB プロトコルの実装可能性検証

## ガバナンス上の未確定

- [ ] 規約改正フローの実体（[governance.md](../docs/05-research-frontiers/governance.md)）
- [ ] 多 Council 化のトリガ条件
- [ ] Guardian の人間による監督方式
- [ ] OS バージョン管理の semver か独自か

## ドキュメント上の未確定

- [x] L6 Interface の各サブドキュメント（bdb-protocol.md 等）の本体記述
- [x] specs/ 配下の IDL ファイル本体
- [x] agents/ 配下の各役割定義の詳細プロンプト
- [x] evals/ 配下の baseline 評価項目定義（2026-04-18: cognitive eval surface を追加）

## 命名上の保留

- [ ] 「思兼神」のローマ字を Omoikane / Omoi-Kane どちらに統一するか（現状: Omoikane）
- [ ] サンドボックス自我の正式名（候補: Mirage Self, Yumi Self, Phantom Self）

## トリアージ規則

各項目は次のラベルを付けて優先度を管理：

- `block-design`: これが決まらないと他の設計が進まない
- `block-impl`: 実装で必須
- `nice-to-have`: 余裕があれば
