# Reference Implementation

OmoikaneOS の `src/` 配下には、意識や人格成立を主張しない **reference runtime** を置く。
目的は次の 3 つである。

1. docs/ と specs/ の整合をコードで検証する
2. evals/ の受け皿を用意する
3. 将来の本格実装に渡す前に、安全境界と不可侵領域を固定する

## 境界

- `src/omoikane/` は L0/L1/L2/L4/L5 と、L3 perception/reasoning/affect/attention/volition/imagination/language/metacognition failover、L6 BDB の bounded viability contract を扱う
- EthicsEnforcer と ContinuityLedger の不可侵性は reference runtime でも守る
- Qualia / SelfModel は代理表現に留め、「意識の実装」とは主張しない
- 外部サービス依存は避け、標準ライブラリで再現可能にする

## 主要コマンド

```bash
PYTHONPATH=src python3 -m omoikane.cli demo --json
PYTHONPATH=src python3 -m omoikane.cli amendment-demo --json
PYTHONPATH=src python3 -m omoikane.cli version-demo --json
PYTHONPATH=src python3 -m omoikane.cli naming-demo --json
PYTHONPATH=src python3 -m omoikane.cli continuity-demo --json
PYTHONPATH=src python3 -m omoikane.cli identity-demo --json
PYTHONPATH=src python3 -m omoikane.cli council-demo --json
PYTHONPATH=src python3 -m omoikane.cli multi-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-transport-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-governance-demo --json
PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json
PYTHONPATH=src python3 -m omoikane.cli consensus-bus-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-network-demo --json
PYTHONPATH=src python3 -m omoikane.cli ethics-demo --json
PYTHONPATH=src python3 -m omoikane.cli termination-demo --json
PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json
PYTHONPATH=src python3 -m omoikane.cli broker-demo --json
PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json
PYTHONPATH=src python3 -m omoikane.cli imc-demo --json
PYTHONPATH=src python3 -m omoikane.cli collective-demo --json
PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json
PYTHONPATH=src python3 -m omoikane.cli wms-demo --json
PYTHONPATH=src python3 -m omoikane.cli sensory-loopback-demo --json
PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json
PYTHONPATH=src python3 -m omoikane.cli episodic-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-edit-demo --json
PYTHONPATH=src python3 -m omoikane.cli semantic-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-writeback-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-skill-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-enactment-demo --json
PYTHONPATH=src python3 -m omoikane.cli perception-demo --json
PYTHONPATH=src python3 -m omoikane.cli qualia-demo --json
PYTHONPATH=src python3 -m omoikane.cli self-model-demo --json
PYTHONPATH=src python3 -m omoikane.cli design-reader-demo --json
PYTHONPATH=src python3 -m omoikane.cli reasoning-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-demo --json
PYTHONPATH=src python3 -m omoikane.cli affect-demo --json
PYTHONPATH=src python3 -m omoikane.cli attention-demo --json
PYTHONPATH=src python3 -m omoikane.cli volition-demo --json
PYTHONPATH=src python3 -m omoikane.cli imagination-demo --json
PYTHONPATH=src python3 -m omoikane.cli language-demo --json
PYTHONPATH=src python3 -m omoikane.cli metacognition-demo --json
PYTHONPATH=src python3 -m omoikane.cli sandbox-demo --json
PYTHONPATH=src python3 -m omoikane.cli builder-demo --json
PYTHONPATH=src python3 -m omoikane.cli builder-live-demo --json
PYTHONPATH=src python3 -m omoikane.cli rollback-demo --json
PYTHONPATH=src python3 -m omoikane.cli scheduler-demo --json
PYTHONPATH=src python3 -m omoikane.cli gap-report --json
python3 -m unittest discover -s tests -t .
```

`continuity-demo` は L1 ContinuityLedger の暫定 profile
(`sha256` chain / `hmac-sha256` signatures / category ごとの required roles)
を JSON で可視化する。

`gap-report` は open question / missing file / empty eval / placeholder に加えて、
current truth-source (`README.md` / `docs/07-reference-implementation/README.md` /
`specs/interfaces/**/*.idl` / `specs/schemas/README.md`) に残る
residual `future work` も JSON で列挙する。

`identity-demo` は L1 IdentityRegistry の reference contract
(`kernel.identity.v0`) を JSON で可視化し、
Council resolution 付き pause、self proof のみ許可する resume、
self-initiated pause では `council_resolution_ref` を持たないこと、
最新 pause/resume cycle を `pause_state` と `identity-lifecycle` ledger event に残すことを確認する。

`broker-demo` は L1 SubstrateBroker の reference contract
(`kernel.broker.v0`) を JSON で可視化し、
Method B candidate selection が
`health_score >= 0.6` / `attestation_valid` / `energy_floor` を満たす substrate だけを残し、
直近 2 回の `substrate_kind_neutrality_index` で tie-break すること、
default の 1 active lease + 1 standby candidate に加えて
`shadow-sync` で bounded dual allocation window を開き、
lease → standby probe → attest → attestation-chain bridge → open_dual_allocation_window → seal_attestation_stream → migrate → close_dual_allocation_window → release
を実行すること、
さらに energy floor violation が `critical + migrate-standby` の
scheduler-compatible signal を返し、
standby probe が health / attestation / energy headroom を満たして
`ready_for_migrate` を返すこと、
attestation chain が fixed 3-beat window で
`expected_state_digest` / `expected_destination_substrate` /
`expected_destination_host_ref` / `substrate_cluster_ref` を migrate 前に束縛すること、
attestation stream が shadow-active dual allocation window 上で
fixed 5-beat keepalive を sealed し、
handoff-ready digest と destination substrate/host binding を `hot-handoff` migrate 前に固定すること、
dual allocation window が pre-bound standby 上の second active allocation、
`45s / 250ms / drift<=0.08` の overlap receipt、
distinct-host pair、
shared `substrate_cluster_ref`、
`hot-handoff` destination binding、cleanup release を返すこと、
selected standby がそのまま migration destination に束縛されることを
1 シナリオで確認する。

`scheduler-demo` は L1 AscensionScheduler の reference contract
(`kernel.scheduler.v0`) を JSON で可視化し、
Method A の 4 stage blueprint、順序違反の reject、
`identity-confirmation` timeout 超過時の `bdb-bridge` への自動 rollback、
Method B の degraded / critical substrate signal に対する pause / rollback、
actual broker の standby probe / attestation chain / dual allocation window /
attestation stream を `broker_handoff_receipt` として束縛し、
`authority-handoff` の前に prepared、
`bio-retirement` の前に hot-handoff migration + cleanup release 付き confirmed を要求すること、
Method C の `scan-commit` fail-closed に加えて、
`self_consent` / `ethics` / `council` / `legal` / `witness` artifact bundle と
`governance_artifact_digest` が plan と handle に束縛されること、
さらに `artifact_sync` が `current / stale / revoked` external proof snapshot を持ち、
protected handoff 前に `current` bundle を要求すること、
`verifier_roster` が `overlap-required` で pause、
`rotated` で cutover 後に再開、
`revoked` で fail-closed になることに加え、
loopback live verifier endpoint から取得した roster に
`connectivity_receipt` (`verifier_endpoint` / `response_digest` /
`observed_latency_ms` / `http_status`) が束縛されることを
1 シナリオで確認する。
さらに `compile_execution_receipt` が Method A/B/C の
`schedule_handle` history を `scheduler_execution_receipt` へ要約し、
timeout recovery、live verifier connectivity、verifier rotation cutover、
Method B broker handoff、Method C fail-closed を
digest-bound な first-class artifact として残すことを確認する。

`amendment-demo` は L4 governance amendment policy を JSON で可視化し、
`T-Core` が常に `frozen` に留まること、
`T-Kernel` が `Council unanimous + self consent + guardian attest + human reviewers >= 2`
でのみ `dark-launch` に進めること、
`T-Operational` が `Council majority + guardian attest` で `5pct` rollout に進めることを確認する。

`council-demo` は L4 Council の session budget を可視化し、
standard 議事では 45s soft / 90s hard timeout、
expedited 議事では 250ms soft / 1s hard timeout を持ち、
soft timeout 時は weighted-majority fallback、
hard timeout 時は defer または human governance escalation に分岐する。

`multi-council-demo` は L4 multi-council trigger の reference routing を JSON で可視化し、
単一 identity 議題が Local Council に留まり、
複数 identity をまたぐ議題が Federation Council 要求へ、
`ethics_axiom` / `identity_axiom` / `governance` を引用する議題が
Heritage Council 要求へ外部化されること、
両条件が衝突する曖昧案件は local binding decision を停止することを確認する。

`distributed-council-demo` は L4 distributed council resolution の reference contract
(`distributed_council_resolution`) を JSON で可視化し、
`cross-self` advisory Local decision が Federation returned result で
`binding-approved` へ昇格すること、
`interpretive` proposal が Heritage `ethics-committee` veto で
`binding-rejected` になること、
Federation と Heritage の returned result が衝突した場合は
`escalate-human-governance` へ落ちることを確認する。

`distributed-transport-demo` は L4 distributed transport authenticity の reference contract
(`agentic.distributed_transport.v0`) を JSON で可視化し、
Federation handoff が `self-liaison x2 + guardian x1` の participant attestation と
`channel_binding_ref` に束縛されること、
rotated Federation handoff が `accepted_key_epochs=[1,2]` と
`trust_root_quorum=2` を持つ federated root overlap を要求すること、
loopback live root-directory endpoint から取得した
`distributed_transport_root_directory` が `trusted_root_refs` と
`connectivity_receipt` を返し、その quorum が rotated receipt verification に束縛されること、
さらに bounded external key-server fleet から取得した
`distributed_transport_authority_plane` が `directory_digest` と
per-server connectivity receipt を返し、
draining member と replacement member の overlap を
`root_coverage` / `churn_profile=overlap-safe-authority-handoff-v1` で固定しつつ、
その `trusted_root_refs` が
rotated receipt verification に最終的に束縛されること、
さらに `authority_churn` が overlap snapshot から stable snapshot への
draining exit を `bounded-key-server-churn-window-v1` で証明すること、
さらに live remote authority-cluster seed から得た
`distributed_transport_authority_cluster_discovery` が
`candidate_targets` / `candidate_clusters` / `review_budget` /
`accepted_route_catalog_ref` を first-class artifact として残し、
active authority-plane member 全件と host attestation complete を満たした
1 cluster だけを accepted catalog として downstream へ渡すこと、
さらに reviewed `route_catalog` から生成した
`distributed_transport_authority_route_target_discovery` が
stable authority plane の active member 全件を
`bounded-authority-route-target-discovery-v1` で覆い、
`server_endpoint` / `server_name` / `remote_host_ref` /
`remote_host_attestation_ref` / `authority_cluster_ref` を
trace 前の discovery receipt として固定すること、
さらに stable authority plane に対する actual non-loopback mTLS route trace が
`peer_certificate_fingerprint` / `client_certificate_fingerprint` /
`tls_version` / `cipher_suite` / `local_ip` / `remote_ip` / `response_digest`
を socket trace として返し、同時に `netstat` / `lsof` ベースの
`os_observer_receipt` が同じ TCP tuple と connection state を束縛し、
authority plane の per-server digest と一致したときだけ `authenticated` になること、
さらに route trace 自体が `route_target_discovery_ref` /
`route_target_discovery_digest` /
`route_target_discovery_profile=bounded-authority-route-target-discovery-v1`
に束縛されること、
さらに各 traced route が `remote_host_ref` /
`remote_host_attestation_ref` / `authority_cluster_ref` を保持し、
`os_observer_receipt.host_binding_digest` がその host binding と tuple を同時に固定しつつ、
stable authority plane の全 member が distinct remote host として束縛された時だけ
`cross_host_verified=true` になること、
さらに authenticated route trace が
`trace-bound-pcap-export-v1` により PCAP artifact へ export され、
in-process readback と `tcpdump` readback が
tuple ごとの request/response byte count を再確認すること、
さらに delegated broker 発行の
`bounded-live-interface-capture-acquisition-v1` receipt が
resolved interface / exact capture filter / route binding set / `tcpdump`
command preview / lease ref / broker attestation ref を束縛すること、
Heritage handoff が fixed reviewer roles を満たした receipt だけを
`authenticated` にすること、
同一 `route_nonce` と `hop_nonce_chain` の再利用が `replay-blocked` になること、
さらに bounded relay telemetry が hop latency / jurisdiction / root visibility を
receipt verdict と同じ形で返すことを確認する。

`cognitive-audit-demo` は L2/L3/L4 cognitive audit loop の reference contract
(`agentic.cognitive_audit.v0`) を JSON で可視化し、
`qualia-checkpoint` entry、abrupt self-model observation、
guardian-review metacognition report を 1 つの bounded Council review に束ね、
`cognitive.audit.resolved` follow-up が raw sensory embedding や sealed note を
含まず `open-guardian-review` へ落ちることを確認する。

`cognitive-audit-governance-demo` は cognitive audit governance binding の
reference contract (`agentic.cognitive_audit_governance.v0`) を JSON で可視化し、
network-attested reviewer quorum を持つ `guardian-oversight` event と、
Federation の `binding-approved` returned result、
Heritage の `binding-rejected` returned result を
同一 cognitive audit follow-up に束ねつつ、
`federation-attested-review` / `heritage-veto-boundary` /
`distributed-conflict-human-escalation` の 3 gate を
raw cognitive payload を露出せずに切り替えることを確認する。

`task-graph-demo` は L4 TaskGraph の暫定 complexity policy
(`max_nodes=5 / max_edges=4 / max_depth=3 / max_parallelism=3 / max_result_refs=5`)
を JSON で可視化し、初期 dispatch と synthesis がその範囲に収まることを示す。

`consensus-bus-demo` は L4 ConsensusBus の reference contract
(`agentic.consensus_bus.v0`) を JSON で可視化し、
Council dispatch brief、Builder report、Guardian gate、final resolve を
`consensus-bus-only` transport で監査可能に束ねつつ、
direct handoff attempt が `blocked` として別途記録されることを確認する。

`trust-demo` は L4 YaoyorozuRegistry の trust update policy
(`council_quality_positive=+0.04`, `guardian_audit_pass=+0.06`,
`human_feedback_good=+0.05`, `guardian_veto=-0.12`,
`regression_detected=-0.08`, `human_feedback_bad=-0.10`,
`ethics_violation=-0.25`) と human pin freeze を JSON で可視化し、
Council 召集・weighted vote・runtime 反映・guardian role の gate を確認する。

`oversight-demo` は L4 Guardian human oversight channel を JSON で可視化し、
registered reviewer の `proof_ref` / `legal_ack_ref` / liability scope に加えて、
`verifier_ref` / `challenge_digest` / jurisdiction evidence bundle digest を持つ
live-proof surrogate snapshot と
`policy_ref` / `notice_authority_ref` / `legal_execution_id` を持つ
jurisdiction-specific legal execution receipt が
`veto` attestation に immutable binding として焼き付くこと、
scope 外 reviewer が `pin-renewal` を attest できず fail-closed になること、
その後 reviewer 不足で `pin-renewal` が `breached` になった時に
`integrity-guardian` の human pin と guardian eligibility が外れることを確認する。

`oversight-network-demo` は L4 Guardian reviewer verifier-network transport を JSON で可視化し、
fixed endpoint registry から解決された `verifier_endpoint` /
`authority_chain_ref` / `trust_root_ref` / `trust_root_digest` /
digest-bound `transport_exchange` を持つ
`guardian_verifier_network_receipt` が reviewer verification に束縛され、
さらに `guardian_jurisdiction_legal_execution` が
`network_receipt_id` / `authority_chain_ref` / `trust_root_ref` を carry しつつ、
その execution id・digest・policy ref が
`veto` attestation の immutable reviewer binding に焼き付くことを確認する。

`ethics-demo` は L1 EthicsEnforcer の rule language profile
(`deterministic-rule-tree-v0`) と immutable boundary / sandbox escalation /
fork approval の 3 例を JSON で可視化し、
`explain_rule` が schema-bound な rule tree を返すことを確認する。

`termination-demo` は L1 TerminationGate の reference contract
(`kernel.termination.v0`) を JSON で可視化し、
正しい self proof による即時終了、事前同意済み cool-off pending、
invalid self proof の reject を 1 シナリオで確認する。

`qualia-demo` は L2 QualiaBuffer の surrogate profile
(`visual/auditory/somatic/interoceptive` の 4 modality、
各 32 次元、250ms sampling window) を JSON で可視化し、
checkpoint ledger event まで含めて確認する。

`self-model-demo` は L2 SelfModelMonitor の reference contract
(`mind.self_model.v0`) を JSON で可視化し、
`bounded-self-model-monitor-v1` の `threshold=0.35`、
values / goals / traits の equal-weight divergence、
stable drift と abrupt takeover 候補の両観測、
`mind.self_model.observed` ledger event を確認する。

`sandbox-demo` は L5 Sandboxer の surrogate suffering proxy
(`surrogate-suffering-proxy-v0`) を JSON で可視化し、
negative valence / arousal / clarity drop / somatic/interoceptive load /
self implication を重み付きで集計して
`freeze_threshold=0.6` 以上、または affect bridge 接続時に
Guardian が sandbox を即時凍結することを確認する。

`design-reader-demo` は L5 DesignReader の reference contract
(`selfctor.design_reader.v0`) を JSON で可視化し、
temp git checkout に対する `design_delta_scan_receipt`、
section-level `changed_section_count` / `section_changes`、
`docs/` / `specs/` source digest、`must_sync_docs`、
`planning_cues` を持つ `design_delta_manifest`、
fail-closed `build_request` handoff を 1 シナリオで確認する。

`builder-demo` は L5 self-construction builder pipeline の reference contract
(`selfctor.patch_generator.v0` / `selfctor.diff_eval.v0` / `selfctor.rollout.v0`) を
JSON で可視化し、Council の `emit_build_request` handoff が
`design_delta_manifest` / `build_request` / `build_artifact` / `sandbox_apply_receipt` /
`staged_rollout_session` schema に束縛されたまま immutable boundary を検証し、
planning cue と target subsystem に整列した multi-file patch descriptor を生成し、
Mirage Self への sandbox apply、parsed baseline / sandbox observation と
temp workspace の actual command run を束縛した `diff_eval_execution_receipt` と comparison digest を持つ
`council_output_build_request_pipeline` および
`builder_staged_rollout_execution` eval report、`promote` / `hold` / `rollback`
の rollout 分類、Stage 0/1/2/3 (`dark-launch` / `canary-5pct` / `broad-50pct` /
`full-100pct`) の固定順序実行まで
ledger-safe な `self-modify` chain で進むことを確認する。

`builder-live-demo` は L5 live enactment の reference contract
(`selfctor.enactment.v0`) を JSON で可視化し、
`PatchGeneratorService` が生成した patch descriptor を
temp workspace にだけ materialize しつつ、
runtime/tests/evals/docs/meta/decision-log の approved scope 以外には広げず、
`builder_live_enactment_execution` eval の command を実際に実行し、
`workspace-enacted` marker を持つ mutated file と
cleanup 済み receipt を 1 シナリオで確認する。

`rollback-demo` は L5 builder rollback の reference contract
(`selfctor.rollback.v0`) を JSON で可視化し、
rollback 判定済み staged rollout が `builder_rollback_session` を通じて
`pre-apply` Mirage Self snapshot を復元し、
`dark-launch` / `canary-5pct` の revoke 範囲、
live enactment receipt に束縛された reverse-apply journal、
temp rollback workspace 上の actual reverse-apply command receipt、
current checkout baseline に束縛された repo verification receipt、
detached git worktree 上の checkout-bound mutation receipt、
actual current checkout 自体を baseline へ戻す direct worktree receipt、
repo-root の `git worktree list --porcelain` / `git stash list` による external observer receipt、
rollback plan を payload に持つ integrity reviewer 2 名の verifier-network attestation event、
cleanup 済み telemetry gate、
append-only continuity ref 2 本、
self / council / guardian の 3 者通知を
1 シナリオで確認する。

`memory-demo` は L2 MemoryCrystal の暫定 compaction policy
(`append-only-segment-rollup-v1`) を JSON で可視化し、
source event を保持したまま最大 3 件ずつ segment 化する manifest と
`crystal-commit` ledger event を確認する。
入力 source event は `EpisodicStream` の handoff window から取り込み、
`compaction_candidate_ids` をそのまま payload に残す。

`memory-edit-demo` は L2 Memory Editing API の reference contract
(`mind.memory_edit.v0`) を JSON で可視化し、
`SemanticMemory` 由来の concept を source として
`consented-recall-affect-buffer-v1` の recall overlay を開きつつ、
`delete-memory` / `insert-false-memory` / `overwrite-source-segment` が
禁止されたままであること、
`freeze_record` が source manifest / source concept digest に束縛されること、
`memory-edit` ledger event が policy id と freeze ref を残すことを確認する。

`episodic-demo` は L2 EpisodicStream の canonical shape
(`canonical-episodic-stream-v1`) を JSON で可視化し、
append-only snapshot、最新 5 event の handoff window、
`MemoryCrystal` への manifest 生成プレビュー、
`episodic-window` ledger event を確認する。

`semantic-demo` は L2 semantic projection の reference contract
(`mind.semantic.v0`) を JSON で可視化し、
`MemoryCrystal` segment を `semantic-segment-rollup-v1` で
read-only concept view に投影しつつ、
`procedural-memory` が deferred surface として残ること、
`semantic-projection` ledger event が source manifest digest と concept label を記録することを確認する。

`procedural-demo` は L2 procedural preview の reference contract
(`mind.procedural.v0`) を JSON で可視化し、
`MemoryCrystal` segment と `Connectome` snapshot を
`connectome-coupled-procedural-preview-v1` で突き合わせ、
bounded な `weight-delta-preview` recommendation と
`procedural-preview` ledger event が source manifest / connectome digest と
target path を記録することを確認する。

`procedural-writeback-demo` は L2 procedural writeback gate の reference contract
(`mind.procedural_writeback.v0`) を JSON で可視化し、
validated preview を `human-approved-procedural-writeback-v1` で copied
`Connectome` snapshot へ適用しつつ、
2 名の human reviewer quorum、continuity diff metadata、
rollback token、`procedural-writeback` ledger event を確認する。

`procedural-skill-demo` は L2 procedural skill execution の reference contract
(`mind.skill_execution.v0`) を JSON で可視化し、
validated writeback を `guardian-witnessed-procedural-skill-execution-v1` で
sandbox-only rehearsal へ昇格しつつ、
guardian witness、executed skill label、rollback token carryover、
no external actuation、`procedural-execution` ledger event を確認する。

`procedural-enactment-demo` は L2 procedural skill enactment の reference contract
(`mind.skill_enactment.v0`) を JSON で可視化し、
validated `skill-execution` receipt を `guardian-witnessed-procedural-skill-enactment-v1`
で temp workspace に materialize しつつ、
actual command receipt、cleanup、rollback token carryover、
sandbox-only delivery、`procedural-enactment` ledger event を確認する。

`perception-demo` は L3 perception failover の reference contract
(`cognitive.perception.v0`) を JSON で可視化し、
`salience_encoder_v1` baseline から `continuity_projection_v1` fallback への
single-switch failover、`qualia://tick/<id>` handoff、
`body_coherence_floor=0.6` の continuity guard、
`observe` guard 下での `guardian-review-scene` への縮退、
`cognitive.perception.failover` ledger event を確認する。

`reasoning-demo` は L3 reasoning failover の reference contract
(`cognitive.reasoning.v0`) を JSON で可視化し、
`symbolic_v1` baseline から `narrative_v1` fallback への
single-switch failover、bounded belief budget、`reasoning_trace` と
ledger-safe な `reasoning_shift` の分離、
`cognitive.reasoning.failover` ledger event を確認する。
`cognitive-demo` は互換性のための alias として残す。

`affect-demo` は L3 affect failover の reference contract
(`cognitive.affect.v0`) を JSON で可視化し、
`homeostatic_v1` baseline から `stability_guard_v1` fallback への
single-switch failover、`max_valence_delta=0.22` /
`max_arousal_delta=0.26` の continuity smoothing、
本人同意なしの artificial dampening 不可、
`cognitive.affect.failover` ledger event を確認する。

`attention-demo` は L3 attention failover の reference contract
(`cognitive.attention.v0`) を JSON で可視化し、
`salience_router_v1` baseline から `continuity_anchor_v1` fallback への
single-switch failover、`AffectService.recommended_guard` を受けた
safe target routing、`guardian-review` への degrade shift、
`cognitive.attention.failover` ledger event を確認する。

`volition-demo` は L3 volition failover の reference contract
(`cognitive.volition.v0`) を JSON で可視化し、
`utility_policy_v1` baseline から `guardian_bias_v1` fallback への
single-switch failover、`Attention` の focus と
`AffectService.recommended_guard` を受けた safe intent routing、
irreversible intent を review なしで advance しない policy、
`cognitive.volition.failover` ledger event を確認する。

`imagination-demo` は L3 imagination failover の reference contract
(`cognitive.imagination.v0`) を JSON で可視化し、
`counterfactual_scene_v1` baseline から `continuity_scene_guard_v1` fallback への
single-switch failover、council-witnessed `co_imagination` / `shared_reality`
handoff、guard 上昇時の `private-sandbox` / `private_reality` への縮退、
`cognitive.imagination.failover` ledger event を確認する。

`language-demo` は L3 language bridge の reference contract
(`cognitive.language.v0`) を JSON で可視化し、
`semantic_frame_v1` baseline から `continuity_phrase_v1` fallback への
single-switch failover、`observe` / `sandbox-notify` guard 時の
disclosure-floor redaction、`guardian` / `self` への送達先縮退、
`cognitive.language.failover` ledger event を確認する。

`metacognition-demo` は L3 metacognition failover の reference contract
(`cognitive.metacognition.v0`) を JSON で可視化し、
`reflective_loop_v1` baseline から `continuity_mirror_v1` fallback への
single-switch failover、`SelfModelMonitor` の abrupt change と
`QualiaBuffer` の lucidity/awareness を束ねた bounded self-monitor report、
`observe` guard 時の `guardian-review` 昇格、
`cognitive.metacognition.failover` ledger event を確認する。

`bdb-demo` は L6 Biological-Digital Bridge の reference contract
(`interface.bdb.v0`) を JSON で可視化し、
`latency_budget_ms=5.0`、`failover_budget_ms=1.0`、
coarse neuromodulator proxy、置換比率の増減、`bio-autonomous-fallback`
をまとめて確認する。

`imc-demo` は L6 Inter-Mind Channel の reference contract
(`interface.imc.v0`) を JSON で可視化し、
peer attestation、forward secrecy、narrow disclosure floor、
sealed field redaction、summary+digest-only audit、
unilateral emergency disconnect をまとめて確認する。

`collective-demo` は L6 Collective Identity の reference contract
(`interface.collective.v0`) を JSON で可視化し、
distinct collective ID、`merge_thought` 10 秒 cap、Federation attested merge、
WMS major divergence 後の `private_reality` escape、
全 member の post-disconnect identity confirmation、
collective dissolution を 1 シナリオで確認する。

`ewa-demo` は L6 External World Agents の reference contract
(`interface.ewa.v0`) を JSON で可視化し、
device-specific `ewa_motor_plan` が
`actuator_profile_id` / `motion_profile` / `target_pose_ref` /
`rollback_vector_ref` / `safe_stop_policy_id` を固定し、
jurisdiction-bound `ewa_legal_execution` が
`policy_ref` / `legal_basis_ref` / `notice_authority_ref` / `liability_mode` /
fixed 5-control preflight を固定したうえで、
`external_actuation_authorization` artifact が
`instruction_digest` / `intent_summary_digest` / `motor_plan_id` /
`legal_execution_id` / `guardian_verification_ref` /
`jurisdiction_bundle_status=ready` を固定したうえで、
reversible command に Guardian observe を要求しつつ、
`watchdog-timeout` emergency stop が
`command_id` / `bound_command_digest` / `bound_authorization_digest` /
`hardware_interlock_state=engaged` / `release_required=true` を返し、
その後 forced release が実行されること、
さらに別 handle 上で blocked token を含む irreversible command を
fail-closed で veto し、digest-only audit を維持することを確認する。

`wms-demo` は L6 World Model Sync の reference contract
(`interface.wms.v0`) を JSON で可視化し、
minor diff を `consensus-round` で reconcile しつつ、
major diff で `private_reality` 退避を提示し、
unauthorized diff を `guardian-veto` / `isolate-session` へ落とすことを確認する。

`sensory-loopback-demo` は L6 Sensory Loopback の reference contract
(`interface.sensory_loopback.v0`) を JSON で可視化し、
`world_state_ref` と `body_anchor_ref` に束縛された visual/audio/haptic bundle が
`avatar_body_map_ref` / `proprioceptive_calibration_ref` /
`body_map_alignment_ref` にも束縛され、
weighted `body_map_alignment` から導出される
`latency_budget_ms=90.0` と `body_coherence_score<=0.20` の範囲では
`delivered` になり、
high-drift bundle が `guardian-hold` と `safe baseline` に落ちた後、
`stabilize` で active session へ復帰すること、
さらに `qualia_binding_ref` が surrogate tick ref に束縛され、
coherent / held / stabilized の 3 scene が
`multi-scene-artifact-family-v1` で 1 つの digest-only artifact family に束縛されつつ、
audit が artifact digest と summary ref だけを保持することを確認する。

`version-demo` は hybrid versioning policy を JSON で可視化し、
runtime semver、IDL/schema の `bootstrap` stability、governance calver、
`specs/catalog.yaml` の sha256 snapshot を 1 つの manifest に集約して確認する。

`naming-demo` は naming policy を JSON で可視化し、
project branding の英字表記を `Omoikane` に固定し、
サンドボックス自我の formal name を `Mirage Self` に固定しつつ、
runtime 実装上は `SandboxSentinel` alias を内部 detail としてのみ許容することを確認する。

## 今後広げる面

- automation による未実装ギャップの継続充填
