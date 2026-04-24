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
  `distributed-transport-demo` が participant attestation / transport authenticity /
  key rotation overlap / federated roots / bounded route target discovery / replay guard を可視化し、
  `cognitive-audit-demo` が qualia / self-model / metacognition を bounded Council review に束ね、
  `cognitive-audit-governance-demo` が Federation / Heritage returned result を
  digest-only signature binding 付きで reviewer-network oversight に結合する

### YaoyorozuRegistry
- 利用可能 Agent の登録簿
- 各 Agent の role, capability, trust score を管理
- 役割定義は [agents/](../../../agents/) 配下
  - reference runtime では `agentic.trust.v0` と `trust-demo` / `trust-transfer-demo` が deterministic な更新規則に加え、
  self-issued positive event と reciprocal positive boost を provenance guard で fail-closed にし、
  guardian / human quorum 付きの cross-substrate trust export/import receipt に
  live remote verifier federation、fixed re-attestation cadence、
  append-only destination lifecycle (`imported -> renewed -> revoked -> recovered`) に加えて
  full-clone / redacted の public export profile 分岐と
  `trust_redacted_snapshot` projection と
  `trust_redacted_verifier_federation` summary、
  `trust_redacted_destination_lifecycle` summary まで内包して machine-checkable にし、
  `agentic.yaoyorozu.v0` と `yaoyorozu-demo` が source workspace に加えて bounded same-host local candidate workspace を proposal profile ごとの review budget で走査し、
  `self-modify-patch-v1` では `runtime/schema/eval/docs`、`memory-edit-v1` では `runtime/eval/docs` required + `schema` optional、
  `fork-request-v1` では `runtime/schema/docs` required + `eval` optional、
  `inter-mind-negotiation-v1` では `runtime/schema/eval/docs` required という cross-workspace coverage policy を
  `yaoyorozu_workspace_discovery` として machine-readable に固定したうえで、
  repo-local `agents/` から trust-bound registry snapshot と
  `self-modify-patch-v1` / `memory-edit-v1` / `fork-request-v1` / `inter-mind-negotiation-v1` の
  Council convocation / builder handoff plan を materialize し、
  convocation 側でも `workspace_discovery_binding` により accepted workspace set と profile policy を再束縛し、
  `self-modify-patch-v1` では `runtime/schema/eval/docs`、
  `memory-edit-v1` では `runtime/eval/docs`、
  `fork-request-v1` では `runtime/schema/docs`、
  `inter-mind-negotiation-v1` では `runtime/schema/eval/docs`
  だけを actual builder handoff coverage として固定したうえで、
  selected builder handoff を dispatch/unit binding と workspace target 観測、
  さらに git-bound target path delta receipt と deterministic priority-ranked patch candidate receipt を持つ
  same-host subprocess worker dispatch receipt まで実行する。
  workspace discovery が bound される場合は、required coverage area を profile-covered non-source candidate workspace に割り当て、
  requested optional coverage は candidate が無い場合に source fallback として明示し、
  `same-host-external-workspace` の execution root へ source target-path snapshot を seed してから worker を起動し、
  HumanOversightChannel reviewer-network attestation に束縛された preseed gate と
  dependency materialization manifest / materialized-first import precedence /
  materialized dependency module-origin binding /
  seed commit / candidate-bound success count / source fallback count を receipt に残しつつ、
  同じ convocation session 上の `ConsensusBus` transcript と blocked direct handoff を
  `yaoyorozu_consensus_dispatch_binding` として束縛する。
  さらに fixed `max_parallelism=3` を守るため、
  `self-modify`=`runtime` / `schema` / `evidence-sync(eval+docs)`,
  `memory-edit`=`runtime` / `eval` / `docs`,
  `fork-request`=`runtime` / `schema` / `docs`,
  `inter-mind-negotiation`=`runtime` / `contract-sync(schema+docs)` / `eval`
  の 3 root bundle に畳み込んだ `TaskGraph` execution bundle を
  `yaoyorozu_task_graph_binding` として残し、
  さらに同じ bundle を `L5.PatchGenerator` 向け `build_request` と
  patch-generator-ready scope validation へ接続した
  `yaoyorozu_build_request_binding` まで materialize する。
  そのうえで同じ `build_request` handoff から
  `build_artifact` / `sandbox_apply_receipt` / live enactment /
  rollback witness を same-request digest family に束縛した
  `yaoyorozu_execution_chain_binding` まで返し、
  L4 orchestration から reviewer-facing builder execution chain までを
  1 つの artifact family として監査できるようにする

### TaskGraph
- タスクの依存関係グラフ（DAG）
- 各ノードはサブタスク、エッジは依存
- Council が分解、Yaoyorozu が実行
- reference runtime v0 では `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3`
  に固定し、過大な DAG は build 前に reject する。
  `yaoyorozu-demo` はこの ceiling を破らないため、proposal profile ごとの
  required worker coverage だけを 3 root node grouping へ畳み込んでから
  review / synthesis へ流す

### ConsensusBus
- Agent 間の合意形成メッセージバス
- 直接通信ではなく必ずバス経由（監査可能性のため）
- reference runtime では `consensus-bus-demo` が dispatch / report / guardian gate /
  resolve と direct handoff block を可視化する

### AmenoUzumePool
- 実行担当 Agent プール（Codex 等の Builder）
- サンドボックス実行が原則
- 結果は Council を経由して本体に反映

## メッセージプロトコル

```yaml
CouncilMessage:
  message_id: <uuid>
  session_id: <thread>
  sender_role: <agent role>
  recipient: <council|agent://...|broadcast>
  delivery_scope: <council|agent|broadcast>
  intent: dispatch|report|vote|escalate|gate|resolve
  phase: brief|opening|rebuttal|amendment|decision|gate|resolve
  transport_profile: consensus-bus-only
  payload:
    task_ref: <TaskGraph node>
    content: <body>
  related_claim_ids: [<TaskGraph node>]
  ethics_check_id: <EthicsLedger entry>
  signature_ref: <bus signature ref>
  message_digest: <sha256>
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
- [distributed-transport-attestation.md](distributed-transport-attestation.md) ── Federation / Heritage remote handoff の attestation と transport authenticity
- [cognitive-audit-loop.md](cognitive-audit-loop.md) ── 認知系 cross-layer audit と Council follow-up
- [consensus-bus.md](consensus-bus.md) ── audited dispatch / report / gate / resolve bus
- [task-decomposition.md](task-decomposition.md) ── タスク分解アルゴリズム
- [yaoyorozu-roster.md](yaoyorozu-roster.md) ── 標準 Agent ロスタ
- [trust-management.md](trust-management.md) ── Agent 信頼スコア
