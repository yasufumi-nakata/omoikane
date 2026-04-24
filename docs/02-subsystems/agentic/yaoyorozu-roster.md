# Yaoyorozu Roster ── 標準 Agent ロスタ

OmoikaneOS が標準で持つべき Agent タイプの一覧。
詳細な役割定義は [agents/](../../../agents/) 配下に YAML/JSON として配置。

## 評議系（Council Members）

- `Speaker` ── 議事進行
- `Recorder` ── 議事録作成
- `EthicsCommittee` ── 倫理審査
- `ConservatismAdvocate` ── 「変えない理由」を必ず述べる役（重要）
- `ChangeAdvocate` ── 「変える理由」を必ず述べる役
- `DesignAuditor` ── 設計仕様との一致を確認
- `RegressionTester` ── 退行検出
- `PrivacyOfficer` ── プライバシ保護
- `LegalAdvisor` ── 法的整合性

## 専門系（Domain Experts）

- `SubstrateExpert` ── 各 substrate の特性に詳しい
- `NeuropsychAnalogue` ── 神経精神医学的判断
- `MemoryEthicist` ── 記憶編集に関する倫理
- `IdentityProtector` ── 同一性保護
- `ContinuityAuditor` ── 連続性ログ監査
- `SafetyOfficer` ── 物理／論理安全
- `DiplomatAgent` ── 他自我との交渉

## 実行系（Yaoyorozu Workers）

- `MemoryRetriever` ── 記憶想起
- `NarrativeWriter` ── 物語生成
- `Imaginer` ── 反実仮想シミュレーション
- `Translator` ── 言語間／表現間の変換
- `Summarizer` ── 要約
- `Calibrator` ── 本人 SelfModel に合わせた調整
- `WorldModelSyncer` ── 共有現実との同期
- `SensoryRenderer` ── 感覚出力の描画

## ガーディアン系（Guardians）

- `EthicsGuardian` ── 倫理規約強制
- `IntegrityGuardian` ── データ整合性
- `IdentityGuardian` ── 同一性保護
- `TerminationGuardian` ── 終了権の保証

## ビルダー系（Builders, in-repo reference implementation）

- `CodexBuilder` ── `src/` / `tests/` 向け reference runtime 実装
- `SchemaBuilder` ── データスキーマ生成
- `EvalBuilder` ── 評価コード生成
- `DocSyncBuilder` ── docs と実装の同期検査

## 各 Agent の定義書フォーマット

```yaml
# agents/<role>/<agent_name>.yaml
name: <unique>
role: <one of above>
version: <semver>
capabilities:
  - <capability_id>
trust_floor: <0.0-1.0>
substrate_requirements:
  - <substrate_id or 'any'>
input_schema_ref: <specs/...>
output_schema_ref: <specs/...>
ethics_constraints:
  - <rule_id>
prompt_or_policy_ref: <agents/.../policy.md>
```

## 拡張

新規 Agent タイプの追加は Council 承認＋ docs 更新を経て YaoyorozuRegistry に登録する。
reference runtime では `yaoyorozu-demo` が
source workspace に加えて bounded same-host local candidate workspace catalog を
`yaoyorozu_workspace_discovery` として記録し、
`self-modify-patch-v1` では `review_budget=3` / full four-surface review、
`memory-edit-v1` では `review_budget=2` / `runtime+eval+docs` required + `schema` optional、
`fork-request-v1` では `review_budget=3` / `runtime+schema+docs` required + `eval` optional、
`inter-mind-negotiation-v1` では `review_budget=3` / full four-surface review
という proposal-profile-bound workspace review policy を返し、
repo-local `agents/` をそのまま sync し、
trust-bound registry snapshot、bounded convocation plan、
`self-modify-patch-v1` と `memory-edit-v1` と `fork-request-v1` と `inter-mind-negotiation-v1` を切り替え可能な
bounded proposal profile catalog、および
`self-modify-patch-v1` では 4 coverage、
`memory-edit-v1` では `runtime/eval/docs` の 3 coverage、
`fork-request-v1` では `runtime/schema/docs` の 3 coverage、
`inter-mind-negotiation-v1` では `runtime/schema/eval/docs` の 4 coverage を持つ
same-host worker dispatch receipt を JSON で可視化する。
workspace discovery が bound される場合は
non-source candidate workspace ごとに `same-host-external-workspace` execution root を作り、
source target-path snapshot を seed commit 付きで固定してから worker を実行する。
必要時だけ `memory-edit-v1` は `schema` を、
`fork-request-v1` は `eval` を requested optional coverage として追加 dispatch でき、
`requested_optional_builder_coverage_areas` /
`dispatch_builder_coverage_areas` が same-session artifact に残る。
各 worker report は dispatch plan / dispatch unit に束縛され、
workspace 内 target path の存在確認と bounded sample observation に加え、
同じ target path scope に閉じた git-bound delta receipt と、
`patch_descriptor` 互換で deterministic priority rank を持つ patch candidate receipt を返す。
同じ demo は builder report / guardian gate / final resolve を
`ConsensusBus` transcript として監査し、
blocked direct builder handoff と worker claim chain を
`yaoyorozu_consensus_dispatch_binding` へ束縛する。
Council convocation は `workspace_discovery_binding` により、
selected profile の required coverage と accepted workspace set を
same-session artifact として固定する。
さらに `TaskGraph` 側では `max_parallelism=3` を守るため、
`self-modify-patch-v1` は `runtime` / `schema` / `evidence-sync(eval+docs)`,
`memory-edit-v1` は `runtime` / `eval` / `docs`,
`fork-request-v1` は `runtime` / `schema` / `docs`,
`inter-mind-negotiation-v1` は `runtime` / `contract-sync(schema+docs)` / `eval`
の 3 root bundle strategy へ畳み、
worker dispatch receipt と guardian gate / resolve digest を
`yaoyorozu_task_graph_binding` として固定する。
さらに同じ convocation / dispatch / ConsensusBus / TaskGraph bundle は
`L5.PatchGenerator` 向け `build_request` と patch-generator-ready scope validation に接続され、
priority-ranked patch candidate hint を添えた
`yaoyorozu_build_request_binding` としても固定される。
さらに同じ `build_request` handoff は
`build_artifact` / `sandbox_apply_receipt` / `builder_live_enactment_session` /
`builder_rollback_session` を same-request digest family に束縛した
`yaoyorozu_execution_chain_binding` としても返り、
reviewer-facing builder execution chain を 1 artifact で監査できる。
optional dispatch を要求した場合は
`memory-edit-v1` が `runtime` / `contract-eval(eval+schema)` / `docs` へ、
`fork-request-v1` が `runtime` / `schema` / `evidence-docs(docs+eval)` へ
deterministic に切り替わる。
