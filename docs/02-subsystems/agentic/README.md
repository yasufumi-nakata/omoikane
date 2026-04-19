# L4 Agentic Orchestration ── 八百万 (Yaoyorozu)

タスクを分解し、無数のサブエージェントに割り当て、結果を統合する層。
思兼神メタファーの本丸。**Council** が八百万神の評議体として機能する。

## 主要コンポーネント

### Council
- 評議体。重要決定をすべて経由する。
- 構成員は固定ではなく、案件ごとに召集される（→ [docs/04-ai-governance/council-protocol.md](../../04-ai-governance/council-protocol.md)）
- 議事は EthicsLedger に永続化
- reference runtime では `multi-council-demo` が Local / Federation / Heritage への deterministic routing を可視化し、
  `distributed-council-demo` が Federation binding / Heritage veto / human escalation を可視化し、
  `cognitive-audit-demo` が qualia / self-model / metacognition を bounded Council review に束ねる

### YaoyorozuRegistry
- 利用可能 Agent の登録簿
- 各 Agent の role, capability, trust score を管理
- 役割定義は [agents/](../../../agents/) 配下
- reference runtime では `agentic.trust.v0` と `trust-demo` が deterministic な更新規則を持つ

### TaskGraph
- タスクの依存関係グラフ（DAG）
- 各ノードはサブタスク、エッジは依存
- Council が分解、Yaoyorozu が実行
- reference runtime v0 では `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3`
  に固定し、過大な DAG は build 前に reject する

### ConsensusBus
- Agent 間の合意形成メッセージバス
- 直接通信ではなく必ずバス経由（監査可能性のため）

### AmenoUzumePool
- 実行担当 Agent プール（Codex 等の Builder）
- サンドボックス実行が原則
- 結果は Council を経由して本体に反映

## メッセージプロトコル

```yaml
CouncilMessage:
  message_id: <uuid>
  conversation_id: <thread>
  from: <agent_id>
  to: <council|agent_id|broadcast>
  intent: propose|vote|report|escalate|veto
  payload:
    task_ref: <TaskGraph node>
    content: <body>
  signatures: [...]
  ethics_check_id: <EthicsLedger entry>
```

## タスクライフサイクル

```
1. ユーザ意図受信 (L6 経由)
2. Council に上申
3. Council が TaskGraph に分解
4. 各タスクを Yaoyorozu に発注
5. 並列／逐次実行
6. 結果を Council が統合・検証
7. Guardian 承認
8. 本体（L1-L3）に反映
9. ContinuityLedger 記録
```

## 不変条件

1. **直接合意禁止** ── Agent 間は ConsensusBus 経由のみ
2. **Builder は本体未接触** ── AmenoUzumePool は常にサンドボックス
3. **倫理 veto の優先** ── EthicsEnforcer が Council 決議より上位
4. **ログ完備** ── 全議事は EthicsLedger
5. **召集権** ── Council は本人意思または Guardian 判断でいつでも召集される

## サブドキュメント

- [council-composition.md](council-composition.md) ── Council 構成と動的メンバ選定
- [distributed-council-resolution.md](distributed-council-resolution.md) ── Federation / Heritage returned result の解決規則
- [cognitive-audit-loop.md](cognitive-audit-loop.md) ── 認知系 cross-layer audit と Council follow-up
- [task-decomposition.md](task-decomposition.md) ── タスク分解アルゴリズム
- [yaoyorozu-roster.md](yaoyorozu-roster.md) ── 標準 Agent ロスタ
- [trust-management.md](trust-management.md) ── Agent 信頼スコア
