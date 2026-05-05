# Glossary ── 用語集

## 神話メタファー

| 用語 | 意味 | 由来 |
|---|---|---|
| **Omoikane** / 思兼神 | OS の中枢統率機能 | 古事記の知恵神 |
| **Amaterasu Endpoint** | ユーザ自我の側 | 天照大御神 |
| **Yaoyorozu** | 八百万、サブエージェント群 | 八百万神 |
| **Council** | 評議体、思兼神の議事機能 | 天の石屋戸の議論 |
| **AmenoUzumePool** | 実行担当 Builder 群 | 天宇受売命（実行神） |
| **Tachikarao** | 力業を担う実行系 | 手力男命 |

## OS 内部用語

| 用語 | 意味 |
|---|---|
| **IdentityRegistry** | 自我 ID の管理機構 |
| **ContinuityLedger** | 連続性証拠の append-only 元帳 |
| **EthicsLedger** | 倫理事象の記録 |
| **EthicsEnforcer** | 倫理規約の機械的強制 |
| **AscensionScheduler** | アップロード時間管理 |
| **SubstrateBroker** | 物理基板選定機構 |
| **TerminationGate** | 終了権の即時実行口 |
| **QualiaBuffer** | 主観状態の連続バッファ |
| **MemoryCrystal** | 不変長期記憶 |
| **EpisodicStream** | エピソード記憶ストリーム |
| **SelfModel** | 自己認識のネットワーク |
| **Connectome** | 神経回路グラフ |
| **TaskGraph** | タスク依存 DAG |
| **ConsensusBus** | Agent 間メッセージバス |
| **Sandboxer** | サンドボックス自我生成 |
| **Mirage Self** / 幻影自我 | user-facing なサンドボックス自我の正式名 |
| **NamingService** | Omoikane / Mirage Self 表記を固定する naming policy validator |

## アップロード関連

| 用語 | 意味 |
|---|---|
| **Method A / Gradual Replacement** | 漸進置換 |
| **Method B / Parallel Run** | 並走移行 |
| **Method C / Destructive Scan** | 破壊スキャン |
| **Identity Confirmation Test** | 自己同一性確認テスト |
| **Failed-Ascension** | アップロード失敗状態 |
| **Fork** | 自我の複製分岐 |
| **Pause / Active / Terminated** | 自我の状態 |

## 通信関連

| 用語 | 意味 |
|---|---|
| **BDT** | BioData Transmitter |
| **Survey EEG Fusion** | アンケート score summary digest と EEG feature-window digest を同じ analysis window に束縛する BDT receipt |
| **BioData Fusion Binding** | Survey EEG Fusion receipt の digest / fused window digest を NIW source bundle と analysis receipt に再束縛する compact binding |
| **Application Replacement Plan** | NIW の source type ごとの measurement / analysis / curation / operator / agent lane coverage を app digest で束縛する receipt |
| **Application Connector Bundle** | NIW の replacement plan に external connector ref、credential ref、data contract ref、LLM tool ref を digest-only で束縛する receipt |
| **Collection Protocol** | NIW の各 biological source summary を consent ref、measurement connector ref、collection window ref に digest-only で束縛する receipt |
| **Observation Integration Workbench** | 人類が取得・計測してきた source を taxonomy / source bundle / graph / analysis plan / operator guide に raw payload なしで束縛する L6 workbench |
| **Observation Method Catalog** | 過去に行われた測定方法と解析方法を method family / method id / digest に縮約し、完全網羅や raw algorithm 保存を避ける OIW catalog |
| **Observation Analysis Run** | OIW の ingest / normalize / align / model / audit / publish-digest lane result summary と review readiness を束縛する digest-only receipt |
| **Cross-Modal Analysis Plan** | NIW の source type 全ペアに bounded analysis recipe と connector support を割り当てる digest-only receipt |
| **Cross-Modal Analysis Run** | Cross-Modal Analysis Plan の全 pair に bounded result summary と review readiness を束縛する digest-only receipt |
| **BDB** | Biological-Digital Bridge |
| **IMC** | Inter-Mind Channel |
| **WMS** | World Model Sync |
| **EWA** | External World Agents |
| **merge_thought** | 思考融合モード |
| **Collective** | 継続的高密度通信集合体 |

## 役割（Subagent）

詳細は [docs/04-ai-governance/subagent-roster.md](../docs/04-ai-governance/subagent-roster.md)。

- Council 系: DesignArchitect, EthicsCommittee, ConservatismAdvocate, ChangeAdvocate, MemoryArchivist
- Researcher 系: ConsciousnessTheorist, NeuroscienceScout, ...
- Builder 系: CodexBuilder, SchemaBuilder, EvalBuilder, DocSyncBuilder
- Guardian 系: EthicsGuardian, IntegrityGuardian, IdentityGuardian
