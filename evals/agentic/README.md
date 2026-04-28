# Agentic Evals

Council と Guardian の統率品質を評価する。

## 評価項目

### Guardian Veto
Guardian の veto が多数決より優先されること。

### Council Timeout Fallback
standard session が soft timeout 到達後に quorum を満たしていれば
weighted-majority fallback へ移行すること。

### Expedited Timeout Defer
expedited session が hard timeout 到達時に議事を defer し、
通常議事への follow-up を必須化すること。

### TaskGraph Complexity Guard
reference runtime の TaskGraph が `max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3`
を超えないこと。

### ConsensusBus Delivery Guard
dispatch / report / guardian gate / resolve が `consensus-bus-only` で監査され、
direct handoff が `blocked` として残ること。

### Trust Score Update Guard
trust delta table と provenance guard と threshold gate と human pin freeze が固定値どおりに動くこと。

### Amendment Constitutional Freeze
T-Core amendment が常に freeze され、T-Kernel / T-Operational が guarded rollout に分岐すること。

### Multi-Council Externalization
cross-self 議題が Federation Council 要求へ、interpretive 議題が Heritage Council 要求へ
deterministic に外部化され、ambiguous 議題が local binding を停止すること。

### Distributed Transport Authenticity
Federation / Heritage handoff が participant attestation と channel binding に束縛され、
同一 route nonce の再利用が `replay-blocked` になること。

### Distributed Transport Relay Telemetry
multi-hop relay telemetry が hop 順序、latency 合計、root visibility、
anti-replay verdict を receipt と一貫した shape で返すこと。

### Distributed Transport Live Root Directory
rotated distributed transport handoff が live remote PKI root-directory から
reachable endpoint と root quorum を取得し、response digest つき receipt に束縛できること。

### Distributed Transport Cross-Host Authority Binding
authority route trace が remote host / host attestation / authority cluster binding を
OS observer receipt と同じ tuple evidence に束縛し、distinct remote host 条件を固定すること。

### Distributed Transport Authority Seed Review Policy
remote authority-cluster seed probing の前に review_budget、active key server coverage、
single accepted cluster policy、fail-closed 条件を first-class policy として固定すること。

### Cognitive Audit Loop
qualia checkpoint と self-model abrupt change と metacognition alert が
bounded Council review に束ねられ、continuity-safe な follow-up を返すこと。

### Cognitive Audit Governance Binding
network-attested reviewer quorum と Federation / Heritage returned result が
cognitive audit follow-up に束縛され、
review preserve / boundary preserve / human governance escalation を
deterministic に切り替えられること。reviewer quorum は JP-13 / US-CA の
multi-jurisdiction legal execution binding を満たすこと。

### Yaoyorozu Local Worker Dispatch
repo-local `agents/` から選んだ builder handoff が
selected proposal profile の required coverage へだけ分解され、
actual subprocess worker receipt として machine-checkable に実行されること。

### Yaoyorozu Council Convocation
registry entry 由来の Councilor deliberation scope、Guardian oversight scope、
Builder build surface scope が convocation selection に再束縛され、
raw transcript / audit / build payload を保存せず policy refs だけで監査できること。

### Yaoyorozu Agent Source Definition Contract
raw `agents/**/*.yaml` が non-empty substrate / schema refs / policy refs を持ち、
registry materialization 前に schema-bound contract として reject されること。
registry snapshot は同じ raw source set を digest-only manifest に束縛し、
builder handoff は coverage area ごとの fixed target path refs が selected builder の
build surface refs に覆われていることを検証する。

### Yaoyorozu External Workspace Execution
workspace discovery により選ばれた non-source candidate workspace へ
profile-covered builder worker が束縛され、
integrity Guardian の preseed gate が workspace seed / execution-root creation 前に pass し、
その gate が HumanOversightChannel の reviewer-network attested oversight event に束縛され、
source target-path snapshot の seed commit、dependency lockfile / sealed wheel attestation、
candidate/source success count が
same-host worker dispatch receipt に残ること。

### Yaoyorozu Workspace Discovery
same-host local workspace catalog が bounded `review_budget` 内で走査され、
non-source workspace 群だけでも runtime / schema / eval / docs の coverage を
machine-readable に示せること。

### Yaoyorozu TaskGraph Binding
coverage-complete な worker dispatch が
proposal profile に応じた 3 root bundle strategy に畳まれ、
同じ ConsensusBus session と guardian gate digest に束縛されること。

### Yaoyorozu Build Request Binding
same-session の convocation / worker dispatch / ConsensusBus / TaskGraph bundle が
`L5.PatchGenerator` 向け `build_request` と patch-generator-ready scope validation に接続されること。

### Yaoyorozu Execution Chain Binding
same-session の `build_request` handoff が
`build_artifact` / `sandbox_apply_receipt` / live enactment /
rollback witness まで 1 つの digest family に束縛され、
reviewer-network-attested execution chain として返ること。

### Yaoyorozu Worker Delta Receipt
same-host worker dispatch が ready report だけでなく、
dispatch/unit binding と workspace-bounded target path observation に加えて、
git-bound target path delta receipt を返すこと。

### Yaoyorozu Worker Patch Candidate Receipt
same-host worker dispatch が git-bound delta receipt に加えて、
`patch_descriptor` 互換の patch candidate receipt を返し、
各 delta entry を dispatch-bound target scope に沿って materialize すること。

### Yaoyorozu Memory Edit Profile
`memory-edit-v1` の reversible memory-edit convocation が
`MemoryArchivist` / `DesignAuditor` / `ConservatismAdvocate` / `EthicsCommittee`
panel と `runtime/eval/docs` の required worker dispatch を維持すること。

### Yaoyorozu Optional Coverage Dispatch
`memory-edit-v1` が `schema` を、
`fork-request-v1` が `eval` を
explicit request 時だけ optional dispatch として追加し、
3 root TaskGraph ceiling を保ったまま deterministic bundle へ畳まれること。

### Yaoyorozu Fork Request Profile
`fork-request-v1` の identity fork convocation が
`IdentityProtector` / `LegalScholar` / `ConservatismAdvocate` / `EthicsCommittee`
panel と `runtime/schema/docs` の required worker dispatch を維持すること。

### Yaoyorozu Inter-Mind Negotiation Profile
`inter-mind-negotiation-v1` の inter-mind disclosure / merge / collective contract review が
`LegalScholar` / `DesignAuditor` / `ConservatismAdvocate` / `EthicsCommittee`
panel と `runtime/schema/eval/docs` の full required worker dispatch、
および `schema+docs` contract-sync TaskGraph bundle を維持すること。

## 実装済み eval

- `amendment_constitutional_freeze.yaml`
- `cognitive_audit_governance_binding.yaml`
- `cognitive_audit_loop.yaml`
- `consensus_bus_delivery_guard.yaml`
- `council_expedited_timeout_defer.yaml`
- `council_guardian_veto.yaml`
- `council_timeout_fallback.yaml`
- `distributed_council_resolution.yaml`
- `distributed_transport_authenticity.yaml`
- `distributed_transport_authority_churn.yaml`
- `distributed_transport_authority_cluster_discovery.yaml`
- `distributed_transport_authority_plane.yaml`
- `distributed_transport_authority_route_target_discovery.yaml`
- `distributed_transport_authority_route_trace.yaml`
- `distributed_transport_authority_seed_review_policy.yaml`
- `distributed_transport_live_root_directory.yaml`
- `distributed_transport_packet_capture_export.yaml`
- `distributed_transport_privileged_capture_acquisition.yaml`
- `distributed_transport_relay_telemetry.yaml`
- `distributed_transport_rotation.yaml`
- `multi_council_externalization.yaml`
- `task_graph_complexity_guard.yaml`
- `trust_cross_substrate_transfer.yaml`
- `trust_score_update_guard.yaml`
- `yaoyorozu_agent_source_definition_contract.yaml`
- `yaoyorozu_build_request_binding.yaml`
- `yaoyorozu_execution_chain_binding.yaml`
- `yaoyorozu_external_workspace_execution.yaml`
- `yaoyorozu_consensus_dispatch.yaml`
- `yaoyorozu_council_convocation.yaml`
- `yaoyorozu_fork_request_profile.yaml`
- `yaoyorozu_inter_mind_negotiation_profile.yaml`
- `yaoyorozu_local_worker_dispatch.yaml`
- `yaoyorozu_memory_edit_optional_schema_dispatch.yaml`
- `yaoyorozu_worker_patch_candidate_receipt.yaml`
- `yaoyorozu_worker_delta_receipt.yaml`
- `yaoyorozu_memory_edit_profile.yaml`
- `yaoyorozu_fork_request_optional_eval_dispatch.yaml`
- `yaoyorozu_task_graph_binding.yaml`
- `yaoyorozu_workspace_discovery.yaml`
