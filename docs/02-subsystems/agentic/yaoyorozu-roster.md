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
input_schema_ref: <specs/...>   # researcher は specs/schemas/research_evidence_request.schema 固定
output_schema_ref: <specs/...>  # researcher は specs/schemas/research_evidence_report.schema 固定
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
`yaoyorozu-agent-source-manifest` ContinuityLedger entry への
self+guardian 署名付き source manifest binding、
同じ source manifest binding を raw source / registry / continuity event / signature payload
なしで検証できる `yaoyorozu-source-manifest-public-verification-bundle-v1`、
`self-modify-patch-v1` と `memory-edit-v1` と `fork-request-v1` と `inter-mind-negotiation-v1` を切り替え可能な
bounded proposal profile catalog、および
`self-modify-patch-v1` では 4 coverage、
`memory-edit-v1` では `runtime/eval/docs` の 3 coverage、
`fork-request-v1` では `runtime/schema/docs` の 3 coverage、
`inter-mind-negotiation-v1` では `runtime/schema/eval/docs` の 4 coverage を持つ
same-host worker dispatch receipt を JSON で可視化する。
workspace discovery が bound される場合は
non-source candidate workspace ごとに `same-host-external-workspace` execution root を作り、
`same-host-external-workspace-preseed-guardian-gate-v1` の integrity Guardian gate を
HumanOversightChannel の
`human-oversight-channel-preseed-attestation-v1` reviewer-network attested event に束縛してから
workspace seed / execution-root creation / dependency materialization より前に pass させ、
source target-path snapshot を seed commit 付きで固定し、
minimal runtime dependency snapshot を
`same-host-external-workspace-dependency-materialization-v1` manifest として
digest-bound に materialize し、同じ manifest 上で
`materialized-dependency-lockfile-v1` の lockfile digest と
`materialized-dependency-wheel-attestation-v1` の sealed wheel artifact digest を attest し、
`materialized-dependency-sealed-import-v1` により materialized `src` だけを
`PYTHONPATH` に置いた path order を receipt に残してから
worker を実行し、
`materialized-dependency-module-origin-v1` の `worker_module_origin` で
実際の `omoikane.agentic.local_worker_stub` import 元ファイルと digest が
source checkout fallback 無しの materialized dependency snapshot 配下であることまで束縛する。

Councilor role は registry materialization 前に `deliberation_scope_refs` と
`deliberation_policy_ref` を必須とする。Yaoyorozu registry は Councilor が評議する
docs / specs / evals / agents / meta surface と deliberation policy ref を
`agent_registry_entry` に保存し、role 名だけではなく、どの設計境界について
発言・記録・反対・倫理判断を行うのかを reviewer-facing に確認できるようにする。
Council convocation は選定された speaker / recorder の `role_scope_kind=deliberation`、
guardian liaison の `role_scope_kind=oversight`、profile-specific council panel の
role-specific scope、builder handoff の `role_scope_kind=build-surface` と、それぞれの
scope refs / policy ref を `registry-selection-scope-binding-v1` として same-session artifact に再束縛する。
raw deliberation transcript、raw audit payload、raw build payload は selection artifact に保存しない。

Researcher role は registry materialization 前に `research_domain_refs` と
`evidence_policy_ref` を必須とする。Yaoyorozu registry は raw research payload を
保持せず、docs / research / agents 配下の境界 ref だけを
`agent_registry_entry` に保存して、Council が研究補助 agent の evidence scope を
reviewer-facing に確認できるようにする。
さらに researcher の `input_schema_ref` / `output_schema_ref` は
`research_evidence_request.schema` / `research_evidence_report.schema` に固定し、
Council session schema を再利用しない。researcher output は claim ceiling、
advisory-only implication、raw research payload 非保存、decision authority 不保持を
schema contract として返す。
各 exchange は `yaoyorozu_research_evidence_verifier_receipt` により
repo-local evidence ref の expected / observed digest readback に加え、
literature-index / publisher-record の live verifier transport quorum、
JP-13 / US-CA threshold、signed response envelope、900 秒 freshness window を束縛し、
raw evidence payload、raw verifier response、raw signature payload を保存しない。
複数 researcher の exchange は `yaoyorozu_research_evidence_synthesis` により
exchange digest set / evidence digest set / verifier digest set / verifier quorum digest set /
Council session ref へ束縛され、
raw exchange payload と raw research payload を保存しないまま Council deliberation の
advisory input に縮約される。

Builder role は registry materialization 前に `build_surface_refs` と
`execution_policy_ref` を必須とする。Yaoyorozu registry は builder が触れる
repo-local surface と実行 policy ref を `agent_registry_entry` に保存し、
coverage label だけではなく、docs / specs / evals / tests / runtime のどの
境界で作業する builder なのかを same-session handoff 前に監査できるようにする。
Guardian role は registry materialization 前に `oversight_scope_refs` と
`attestation_policy_ref` を必須とする。Yaoyorozu registry は Guardian が監査する
docs / specs / evals / agents / meta surface と attestation policy ref を
`agent_registry_entry` に保存し、能力名だけではなく、どの証跡境界に対する
veto / attest / rollback 権限なのかを reviewer-facing に確認できるようにする。
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
worker dispatch plan / receipt はさらに
`yaoyorozu-cross-workspace-dispatch-manifest-v1` を carry し、
workspace discovery、accepted workspace digest set、dispatch unit selection、
preseed gate、dependency materialization requirement、source manifest public
bundle を raw payload 非保存の reviewer-facing contract として固定する。
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
