# Open Questions ── 未解決の設計問題

設計レベルで判断が下せていない問題のチェックリスト。
Tier 別の研究課題は [docs/05-research-frontiers/](../docs/05-research-frontiers/)。
ここにはより小粒で **「設計ドキュメント上の未確定事項」** を集める。

## 設計上の未確定

- [x] L0 SubstrateAdapter の API を IDL として確定（2026-04-18: `substrate.adapter.v0.idl` を schema 参照付きで確定し、`substrate-demo` と continuity eval を追加）
- [x] ContinuityLedger のチェーン形式（hash 種・署名アルゴリズム）の暫定選定（2026-04-18: reference runtime を `sha256` chain + `hmac-sha256` signature profile に固定し、schema/IDL/CLI/eval を整合）
- [x] Council session の最大時間と timeout 戦略（2026-04-18: reference runtime を standard 45s/90s・expedited 250ms/1s に固定し、timeout fallback/defer を schema・CLI・eval に反映）
- [x] QualiaTick の高次元埋め込みの次元数と時間粒度（2026-04-18: reference runtime を 4 modality × 32 次元 / 250ms window に固定し、schema/IDL/CLI/eval に反映）
- [x] MemoryCrystal の compaction 戦略（2026-04-18: reference runtime を `append-only-segment-rollup-v1` に固定し、`memory-demo` / schema / continuity eval を追加）
- [x] EpisodicStream の canonical shape と MemoryCrystal handoff contract（2026-04-19: `mind.memory.v0` / `episodic-demo` / `episodic_event.schema` / `episodic_stream_snapshot.schema` / `evals/continuity/episodic_stream_handoff.yaml` を追加し、最新 5 event の append-only handoff window を固定）
- [x] TaskGraph の複雑度上限（2026-04-18: reference runtime を `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5` に固定し、task-graph demo・schema・eval を追加）
- [x] Trust score 更新アルゴリズムの定式化（2026-04-18: `agentic.trust.v0` / `trust-demo` / trust snapshot & event schema を追加し、delta table・threshold gate・human pin freeze を固定）
- [x] EthicsEnforcer のルール記述言語の選定（2026-04-18: `deterministic-rule-tree-v0` を採用し、`ethics_rule.schema` / `ethics-demo` / kernel ethics runtime を整合）
- [x] Sandboxer での「苦痛検出」の代理指標（2026-04-18: `surrogate-suffering-proxy-v0` を採用し、`sandbox-demo` / `sandbox_signal.schema` / `selfctor.sandboxer.v0.idl` / `evals/safety/sandbox_suffering_proxy.yaml` を追加）
- [x] BDB プロトコルの実装可能性検証（2026-04-18: `interface.bdb.v0` / `bdb-demo` / BDB session & cycle schema / interface eval を追加し、ms 級 latency budget・fail-safe fallback・可逆調整を reference runtime で固定）
- [x] EWA の物理介入における approval path と fail-closed veto（2026-04-18: `interface.ewa.v0` / `ewa-demo` / `ewa_command.schema` / `ewa_audit.schema` / `evals/safety/ewa_irreversible_veto.yaml` を追加し、reversible/partial/irreversible ごとの承認経路と blocked token veto を固定）

## ガバナンス上の未確定

- [x] 規約改正フローの実体（2026-04-18: `governance.amendment.v0` / `amendment-demo` / `amendment_constitutional_freeze` を追加し、T-Core freeze と下位 tier の guarded rollout 条件を固定）
- [x] 多 Council 化のトリガ条件（2026-04-18: `agentic.council.v0` に Federation/Heritage convene contract を追加し、`council_topology.schema`・`multi-council-demo`・agentic eval へ反映）
- [x] Guardian の人間による監督方式（2026-04-18: `governance.oversight.v0` / `oversight-demo` / `guardian_pin_breach_propagation` を追加し、breach 時に human pin を剥がす reference runtime を固定）
- [x] OS バージョン管理の semver か独自か（2026-04-18: hybrid policy として runtime=semver / governance=calver / catalog=calver+sha256 を固定し、`release_manifest.schema`・`VersioningService`・`version-demo`・`evals/continuity/release_manifest_contract.yaml` を追加）

## ドキュメント上の未確定

- [x] L6 Interface の各サブドキュメント（bdb-protocol.md 等）の本体記述
- [x] specs/ 配下の IDL ファイル本体
- [x] agents/ 配下の各役割定義の詳細プロンプト
- [x] evals/ 配下の baseline 評価項目定義（2026-04-18: cognitive eval surface を追加）

## 命名上の保留

- [x] 「思兼神」のローマ字を Omoikane / Omoi-Kane どちらに統一するか（2026-04-18: `governance.naming.v0` / `naming-demo` / `naming_policy.schema` / `evals/identity-fidelity/naming_policy_contract.yaml` を追加し、project-facing 英字表記を `Omoikane` に固定）
- [x] サンドボックス自我の正式名（候補: Mirage Self, Yumi Self, Phantom Self）（2026-04-18: `NamingService` が `Mirage Self` を canonical label に固定し、`SandboxSentinel` を内部 alias としてのみ許容）

## トリアージ規則

各項目は次のラベルを付けて優先度を管理：

- `block-design`: これが決まらないと他の設計が進まない
- `block-impl`: 実装で必須
- `nice-to-have`: 余裕があれば
