# Task Decomposition

ユーザ意図 → 実行可能タスク群 への分解アルゴリズム。

## 入力

```yaml
UserIntent:
  raw_text: <自由文>
  context_refs:
    - <SelfModel>
    - <recent EpisodicStream slice>
    - <relevant Crystal slice>
  constraints:
    deadline?: <ts>
    energy_budget?: <J>
    ethics_overrides?: [list]
```

## 分解段階

### Stage 1: Intent Clarification
- LLM 系 Reasoning が複数の解釈候補を生成
- Council が本人に確認（必要時）
- 確定意図を `IntentSpec` に固める

### Stage 2: Capability Mapping
- IntentSpec を満たすために必要な能力を列挙
- YaoyorozuRegistry から候補 Agent を引く

### Stage 3: TaskGraph Construction
- DAG を構築
- 各ノード: { agent_role, input_spec, output_spec, ethics_constraints }
- 並列可能箇所と直列必須箇所を識別
- reference runtime v0 では complexity cap を
  `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5`
  に固定し、これを超える案件は本人確認または分割へ回す

### Stage 4: Council Review
- Council が DAG を見て：
  - 倫理違反がないか
  - 重複・無駄がないか
  - 本人の SelfModel と整合的か
- 不適切ならやり直し

### Stage 5: Dispatch
- 各ノードを担当 Agent に発注
- ConsensusBus に投げる
- 進捗を Council が監視

### Stage 6: Synthesis
- 完了した結果を Council が統合
- 整合性チェック
- 本人提示用の表現に整形

### Stage 7: Apply
- 本体反映前に Guardian 承認
- 反映後 ContinuityLedger 記録

## TaskGraph 例

```yaml
intent: "去年の夏の旅行記録から短い物語を作って欲しい"
nodes:
  - id: n1
    role: MemoryRetriever
    input: { query: "trip last summer", time_range: "..." }
    output: episodic_slice
  - id: n2
    role: NarrativeWriter
    deps: [n1]
    input: { slice: $n1.output, style: "short_story" }
    output: draft
  - id: n3
    role: PrivacyAuditor
    deps: [n2]
    input: { draft: $n2.output, sensitivity_check: true }
    output: redacted_draft
  - id: n4
    role: SelfStyleCalibrator
    deps: [n3]
    input: { draft: $n3.output, voice: <SelfModel.narrative_voice> }
    output: final
```

## 失敗時の戦略

- ノード失敗 → 代替 Agent への再発注
- 連鎖失敗 → Council 召集、戦略再考
- どうしても解けない → 本人にエスカレ「これは現状解けません」（隠さない）

## Reference Runtime の暫定上限

reference runtime は安全側に倒して、次の上限を固定する。

```yaml
TaskGraphComplexityPolicy:
  policy_id: reference-v0
  max_nodes: 5
  max_edges: 4
  max_depth: 3
  max_parallelism: 3
  max_result_refs: 5
  max_dependencies_per_node: 3
```

この上限では、最大 3 つの executable node を並列に走らせ、
その後に `council-review` と `result-synthesis` を 1 段ずつ置く。
複雑度超過の要求は build 前に reject し、TaskGraph を二段階へ分割するか、
ユーザ確認つきの再構成へ送る。

## 思兼神メタファー

『古事記』で思兼神は祭祀の **役割分担を設計** した（鏡を作る神、勾玉を作る神、舞う神）。
本仕様の TaskGraph 分解はこの構図を写し取る。
