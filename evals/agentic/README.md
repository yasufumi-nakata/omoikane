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
trust delta table と threshold gate と human pin freeze が固定値どおりに動くこと。

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

### Cognitive Audit Loop
qualia checkpoint と self-model abrupt change と metacognition alert が
bounded Council review に束ねられ、continuity-safe な follow-up を返すこと。

### Cognitive Audit Governance Binding
network-attested reviewer quorum と Federation / Heritage returned result が
cognitive audit follow-up に束縛され、
review preserve / boundary preserve / human governance escalation を
deterministic に切り替えられること。

### Yaoyorozu Local Worker Dispatch
repo-local `agents/` から選んだ builder handoff が
runtime / schema / eval / docs の 4 coverage へ分解され、
actual subprocess worker receipt として machine-checkable に実行されること。

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
- `distributed_transport_live_root_directory.yaml`
- `distributed_transport_packet_capture_export.yaml`
- `distributed_transport_privileged_capture_acquisition.yaml`
- `distributed_transport_relay_telemetry.yaml`
- `distributed_transport_rotation.yaml`
- `multi_council_externalization.yaml`
- `task_graph_complexity_guard.yaml`
- `trust_score_update_guard.yaml`
- `yaoyorozu_consensus_dispatch.yaml`
- `yaoyorozu_council_convocation.yaml`
- `yaoyorozu_local_worker_dispatch.yaml`
