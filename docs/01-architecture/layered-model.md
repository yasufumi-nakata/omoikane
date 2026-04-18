# Layered Model ── 各層の責務と境界

## L0: Substrate

**責務**: 物理基板を抽象化し、上位層に統一インタフェースを提供する。
**含むもの**: 量子プロセッサ、神経模倣チップ、光コンピュータ、生体ニューロン、未来の未知 substrate。
**API（v0）**: `allocate(identity_id, units, purpose)`, `attest(allocation_id, integrity)`, `transfer(allocation_id, state, destination_substrate, continuity_mode)`, `release(allocation_id, reason)`, `energy_floor(identity_id, workload_class)`
**不変条件**: substrate 障害時にも上位層に **「自我の死」を通知しない**（L1 がフェイルオーバする）。

## L1: Kernel ── Omoikane 中枢

**責務**: 自我の **連続性・唯一性・終了権** を保証する。スケジューラ。
**主モジュール**:
- `IdentityRegistry` ── 自我 ID の発行・回収・複製承認
- `ContinuityLedger` ── 連続性ログの append-only 記録
- `AscensionScheduler` ── アップロード・退避・復元の時間管理
- `EthicsEnforcer` ── [docs/00-philosophy/ethics.md](../00-philosophy/ethics.md) の規約を強制
- `SubstrateBroker` ── L0 の選択・冗長化・移行

**不変条件**:
- 同一 Identity の能動コピーは原則 1 つ
- 終了権の発動は他のどの命令より優先

## L2: Mind Substrate

**責務**: 心の構成要素をデータとして保持する。
**主データ構造**:
- `Connectome` ── 神経回路グラフ（[docs/03-protocols/connectome-format.md](../03-protocols/connectome-format.md)）
- `QualiaBuffer` ── 主観状態の連続バッファ（解釈は L3 が行う）
- `SelfModel` ── 自己についての信念ネットワーク
- `MemoryCrystal` ── 長期記憶の不変表現
- `EpisodicStream` ── エピソード記憶の時系列ストリーム

**不変条件**: `MemoryCrystal` への破壊的書き込み禁止。常に append-only。

## L3: Cognitive Services

**責務**: L2 のデータを「思考」「感覚」「意志」として処理する。
**サービス群**:
- `Perception` ── 感覚入力 → 知覚表象
- `Reasoning` ── 推論エンジン（記号 / 連続 / 量子推論を選択可能）
- `Affect` ── 情動・気分の生成と維持
- `Volition` ── 意志・意図の生成
- `Attention` ── 注意の配分
- `Imagination` ── 反実仮想・シミュレーション
- `Language` ── 内的言語と外的言語の橋渡し

各サービスは **複数の実装** を持ち得る（古典 / LLM / 量子 / 生体）。本人が選択できる。
reference runtime では `Reasoning` に対してのみ backend supervisor を置き、
health check に基づく `primary -> fallback` の単純切替を行う。

## L4: Agentic Orchestration ── 八百万

**責務**: タスクを分解し、サブエージェントに割り当て、結果を統合する。
**主要要素**:
- `Council` ── 評議体（合議プロトコル → [docs/04-ai-governance/council-protocol.md](../04-ai-governance/council-protocol.md)）
- `YaoyorozuRegistry` ── 利用可能 Agent の登録簿
- `TaskGraph` ── タスク依存グラフ
- `ConsensusBus` ── Agent 間合意のメッセージバス
- `AmenoUzumePool` ── 実行担当 Agent（Codex 等の Builder）

## L5: Self-Construction

**責務**: OS 自身が自身の設計図を読み、改修パッチを生成する。
**特徴**:
- 改修は必ず **サンドボックス自我** に対して先に適用し、本人本体には適用しない（A/B 検証）。
- 改修ログは Council を経由してのみ本体反映。
- 改修中の状態は L1 の連続性ログに記録される。

## L6: Interface

**責務**: 外界・他自我・生体側との接続。
**境界**:
- **Biological-Digital Bridge** ── BCI、神経インタフェース、生体センサ
- **Inter-Mind Channel** ── 他のアップロード自我との通信プロトコル
- **World Model Sync** ── 外界状態の同期（共有現実 / 個別現実の選択）
- **Sensory Loopback** ── 感覚出力のフィードバック

reference runtime では L6 全体を実装せず、まず BDB のみを
`latency budget / fail-safe fallback / continuity evidence / reversibility`
の 4 点に限定した v0 contract として固定する。

## 層間呼び出し規則

- 上位 → 下位: 直接 API 呼び出し可
- 下位 → 上位: イベント／割り込みのみ（直接呼び出し禁止）
- 同層内: メッセージバス経由（直接参照禁止）
- L4 → L5: Council の合議承認を要する
- 全層 → L1: 終了権・倫理違反通知は最優先パス
