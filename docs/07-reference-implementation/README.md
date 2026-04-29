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
PYTHONPATH=src python3 -m omoikane.cli identity-confirmation-demo --json
PYTHONPATH=src python3 -m omoikane.cli council-demo --json
PYTHONPATH=src python3 -m omoikane.cli multi-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-transport-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-governance-demo --json
PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json
PYTHONPATH=src python3 -m omoikane.cli consensus-bus-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-transfer-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-transfer-demo --export-profile bounded-trust-transfer-redacted-export-v1 --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile memory-edit-v1 --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile memory-edit-v1 --include-optional-coverage schema --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile fork-request-v1 --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile fork-request-v1 --include-optional-coverage eval --json
PYTHONPATH=src python3 -m omoikane.cli yaoyorozu-demo --proposal-profile inter-mind-negotiation-v1 --json
PYTHONPATH=src python3 -m omoikane.cli oversight-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-network-demo --json
PYTHONPATH=src python3 -m omoikane.cli ethics-demo --json
PYTHONPATH=src python3 -m omoikane.cli termination-demo --json
PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json
PYTHONPATH=src python3 -m omoikane.cli broker-demo --json
PYTHONPATH=src python3 -m omoikane.cli energy-budget-demo --json
PYTHONPATH=src python3 -m omoikane.cli energy-budget-pool-demo --json
PYTHONPATH=src python3 -m omoikane.cli energy-budget-subsidy-demo --json
PYTHONPATH=src python3 -m omoikane.cli energy-budget-fabric-demo --json
PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json
PYTHONPATH=src python3 -m omoikane.cli imc-demo --json
PYTHONPATH=src python3 -m omoikane.cli collective-demo --json
PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json
PYTHONPATH=src python3 -m omoikane.cli wms-demo --json
PYTHONPATH=src python3 -m omoikane.cli sensory-loopback-demo --json
PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json
PYTHONPATH=src python3 -m omoikane.cli episodic-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-replication-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-edit-demo --json
PYTHONPATH=src python3 -m omoikane.cli semantic-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-writeback-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-skill-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-enactment-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-actuation-demo --json
PYTHONPATH=src python3 -m omoikane.cli perception-demo --json
PYTHONPATH=src python3 -m omoikane.cli qualia-demo --json
PYTHONPATH=src python3 -m omoikane.cli self-model-demo --json
PYTHONPATH=src python3 -m omoikane.cli design-reader-demo --json
PYTHONPATH=src python3 -m omoikane.cli patch-generator-demo --json
PYTHONPATH=src python3 -m omoikane.cli diff-eval-demo --json
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
同じ demo は `continuity-public-verification-key-management-v1` の
digest-only public verification bundle も返し、ledger head、role verifier key roster、
entry ごとの signature digest / verifier key ref、raw key / raw signature 非公開 flag を
`continuity_public_verification_bundle.schema` で検証できる形に固定する。

`gap-report` は open question / missing file / empty eval / placeholder に加えて、
automation が前提にする repo-local `references/*.md` の欠落、
`specs/interfaces/README.md` / `specs/schemas/README.md` / `evals/*/README.md` の inventory drift、
実装済みの `specs/interfaces/*.idl` / `specs/schemas/*` が
`specs/catalog.yaml` entries に未登録の catalog coverage gap、
current truth-source (`README.md` / `docs/07-reference-implementation/README.md` /
`specs/interfaces/**/*.idl` / `specs/schemas/README.md`) に残る
residual `future work` に加え、
`src/omoikane/**/*.py` の非抽象 runtime path に残る
`raise NotImplementedError` も `implementation_stub_hits` として拾う。
`*Backend._*` の抽象 backend hook は concrete backend subclass が実装するため除外する。
最新 decision log 日付に残る `residual gap` / `unresolved gap` の bullet も
`decision_log_residual_hits` として JSON で列挙する。
同じ最新日付の後続 decision log が `closes_next_gaps` で閉じた item は除外され、
`next-stage frontier` bullet は `decision_log_frontier_hits` として別枠で surfacing する。
decision log 側で append-only に gap chain を保つ時は、
frontmatter の `next_gap_ids` と `closes_next_gaps` を使う。
同じ report は `self-construction-gap-report-scan-receipt-v1` の `scan_receipt` を返し、
counts、prioritized task count、scan surface、report digest、
truth-source ごとの digest-only `scan_surface_digests` / `surface_manifest_digest`、
raw report / raw surface payload 非保存を
`gap_report.schema` で machine-checkable に固定する。
さらに scan receipt は `gap-report-scan-continuity-ledger-binding-v1` として
`continuity_event_ref` / `continuity_event_digest` を返し、report digest と
surface manifest digest を continuity ledger 用 evidence に束縛する。
`OmoikaneReferenceOS.generate_gap_report()` は同じ digest-only event payload を
`selfctor-gap-report-scan` category の `ContinuityLedger` entry として実際に append し、
receipt に `continuity_ledger_entry_ref` / `continuity_ledger_entry_hash` /
`continuity_ledger_payload_ref` / `continuity_ledger_signature_roles=[self, guardian]`
を返す。
raw continuity event payload は保存しない。


`identity-demo` は L1 IdentityRegistry の reference contract
(`kernel.identity.v0`) を JSON で可視化し、
Council resolution 付き pause、self proof のみ許可する resume、
self-initiated pause では `council_resolution_ref` を持たないこと、
最新 pause/resume cycle を `pause_state` と `identity-lifecycle` ledger event に残すことを確認する。

`identity-confirmation-demo` は L1 IdentityRegistry の Ascending → Active
identity confirmation contract (`kernel.identity.v0`) を JSON で可視化し、
`multidimensional-identity-confirmation-v1` profile 上で
episodic recall、SelfModel alignment、subjective self-report、
third-party witness alignment の 4 dimension を固定し、
subjective self-report digest と clinician + guardian witness quorum が揃った時だけ
`active_transition_allowed=true` になることに加えて、
`identity-self-report-witness-consistency-v1` が self-report evidence digest、
accepted witness digest set、required roles、score delta `<=0.12` を
同じ continuity subject に束縛すること、さらに
`identity-witness-registry-binding-v1` が accepted witness の current registry entry、
verifier key ref、not-revoked revocation ref を raw registry payload なしで
束縛し、さらに `identity-witness-revocation-live-verifier-quorum-v1` が
accepted revocation refs を JP-13 / US-CA の dual verifier quorum、
freshness window、digest-only response set に束縛し、さらに
`identity-witness-revocation-verifier-roster-policy-v1` が policy-bound required
jurisdiction set と roster digest を quorum に束縛することを確認する。
同じ demo は低い self-report と witness quorum 不足を
`failed-ascension-or-repeat-ascending` へ fail-closed する blocked profile と、
revoked witness を accepted witness から除外して fail-closed する profile、
revocation verifier quorum が incomplete の profile、quorum は complete だが
verifier roster jurisdiction set が不一致の profile も返す。

`self-model-demo` は L2 SelfModelMonitor の abrupt-change / advisory calibration /
self-authored value-generation / future-self acceptance writeback contract
(`mind.self_model.v0`) を JSON で可視化し、stable drift が `0.35` threshold 未満に留まり、
abrupt drift が Council review へ回ることを確認する。
calibration branch は外部 evidence を advisory-only receipt に束ねるが
forced correction や external truth claim を許さない。
care-trustee-handoff branch は pathology escalation 後の長期 trustee、
care team、legal guardian の責任分担を外部制度 refs と boundary refs へ
digest-only に束縛し、OS 自身が trustee、医療 authority、legal guardian へ
昇格しないことを確認する。
care-trustee-registry-binding branch は、その handoff refs が current external
registry entry、verifier key ref、not-revoked revocation ref に束縛されていることを
digest-only に確認する。さらに accepted revocation refs を JP-13 / US-CA の
live revocation verifier quorum、signed response envelope、freshness window に束縛し、
stale / revoked verifier response を fail-closed する。raw registry / revocation /
verifier payload や OS trustee / medical / legal / writeback authority は許さない。
external-adjudication branch は外部医療・法制度・trustee 側の adjudication result、
jurisdiction policy、appeal/review path を digest-only refs として束縛し、
OS 自身が adjudicator、医療 authority、legal authority、trustee、SelfModel writeback
authority へ昇格しないことを確認する。
value-generation branch は新しい価値候補を self-authored proposal として
digest-only に残し、future self acceptance 前の writeback を拒む。
value-autonomy-review branch は、外部 witness と Council review を
digest-only / advisory-only / boundary-only に留め、source candidate set と
self authorship を保ったまま external veto、Council override、Guardian forced lock、
candidate rewrite、raw witness payload 保存を拒む。
value-acceptance branch は、後日の本人受容がある場合だけ
元の candidate digest set の subset を `self_model_value_acceptance_receipt` へ束縛し、
`accepted-for-bounded-writeback` と `writeback_commit_digest` を返す。
value-reassessment branch は、後日の本人再評価がある場合だけ
元の accepted value digest set の subset を
`self_model_value_reassessment_receipt` へ束縛し、
active writeback から退役させつつ `historical_value_archived=true` を返す。
value-timeline branch は generation / acceptance / reassessment の receipt digest を
`self_model_value_timeline_receipt` の append-only event chain に束ね、
最終 active / retired value set と archive snapshot ref を
`timeline_commit_digest` で固定する。
value-archive-retention-proof branch は retired value の archive snapshot ref を
external trustee proof、long-term storage proof、retention policy、retrieval test refs へ
digest-only に束縛し、`retention_commit_digest` で固定する。
value-archive-retention-refresh branch は、その proof を 90 日の freshness window、
revocation registry refs、refresh deadline へ束縛し、revoked / expired source proof を
fail-closed にしつつ `refresh_commit_digest` で固定する。
Council / Guardian review は boundary-only であり、external veto、forced stability lock、
archive deletion、raw value / archive / trustee / storage / revocation payload 保存は
引き続き false に固定される。

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
`hot-handoff` destination binding、shadow-active 中は nullable lifecycle fields、
closed 後は cleanup release を返すこと、
selected standby がそのまま migration destination に束縛されることを
1 シナリオで確認する。

`energy-budget-demo` は L1 EnergyBudget の AP-1 floor protection contract
(`kernel.energy_budget.v0`) を JSON で可視化し、
`migration` workload の `EnergyFloor=30 J/s` に対して
`requested_budget_jps=22` の economic pressure を
`budget_status=floor-protected` / `degradation_allowed=false` として拒否し、
`observed_capacity_jps=28` の below-floor capacity を
SubstrateBroker の `critical + migrate-standby` signal に束縛する。
receipt は raw economic payload を保存せず、外部 context ref と digest だけを残す。
`energy-budget-pool-demo` は multi-identity pool 上で
migration member の below-floor request と council member の surplus request を同時に評価し、
aggregate requested budget が total floor を覆っていても
`cross_identity_floor_offset_blocked=true`、
`cross_identity_subsidy_allowed=false`、
`pool_budget_status=floor-protected` を返す。
pool receipt は ordered child floor receipt digest set を束縛し、raw economic payload を保存しない。
`energy-budget-subsidy-demo` は pool floor receipt の validation 後にだけ
post-floor voluntary consent を評価し、council member の floor-preserved surplus
`14 J/s` のうち `8 J/s` を migration member の shortfall へ同意 digest / revocation ref / funding policy ref /
signature digest 付きで束縛する。receipt は
`voluntary_subsidy_allowed=true`、`floor_protection_preserved=true`、
`cross_identity_offset_used=false`、`raw_funding_payload_stored=false` を返し、
surplus を floor validation 中の cross-identity offset として使わない。
同じ receipt は `jurisdiction-bound-energy-subsidy-authority-v1` により
funding policy signature を `JP-13` の signer roster / signer key ref へ束縛し、
`energy-subsidy-signer-roster-live-verifier-v1` の live HTTP verifier receipt で
signer roster digest / signer key ref / funding policy signature digest /
network response digest / signed response envelope / response signing key ref /
response signature digest も確認し、
さらに `multi-jurisdiction-energy-subsidy-verifier-quorum-v1` が
primary `JP-13` verifier と backup `SG-01` verifier の live receipt を
accepted authority refs / verifier jurisdictions / route refs /
response digest set / response signature digest set に束ね、
`signed-energy-subsidy-verifier-quorum-threshold-policy-v1` が
quorum threshold を jurisdiction policy registry refs / digests、
verifier jurisdiction set、policy body digest、signature digest に束縛し、
offer revocation refs を revocation registry digest に束ね、
audit authority digest が signer roster と revocation registry の両方を同じ法域で監査する。
`authority_binding_status=verified`、`funding_policy_signature_bound=true`、
`signer_roster_verifier_bound=true`、`network_probe_bound=true`、
`signer_roster_verifier_quorum_bound=true`、`quorum_status=complete`、
`threshold_policy_source_bound=true`、`threshold_policy_signature_bound=true`、
`signed_response_envelope_bound=true`、
`signed_response_envelope_quorum_bound=true`、
`revocation_registry_bound=true`、`audit_authority_bound=true`、
`jurisdiction_authority_bound=true`、`raw_verifier_payload_stored=false`、
`raw_response_signature_payload_stored=false`、
`raw_threshold_policy_payload_stored=false`、
`raw_authority_payload_stored=false` が
`energy_budget_subsidy_verifier_receipt.schema` /
`energy_budget_subsidy_verifier_quorum_threshold_policy_receipt.schema` /
`energy_budget_subsidy_verifier_quorum_receipt.schema` /
`energy_budget_voluntary_subsidy_receipt.schema` と CLI smoke で検証される。

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
Method A cancel、Method B broker handoff、Method C fail-closed を
digest-bound な first-class artifact として残すことを確認する。
公開 `scheduler_execution_receipt.schema` との cancel/completed/fail-closed contract は
integration test で継続検証する。

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
`distributed_transport_authority_seed_review_policy` が
seed 全件を review budget 内に収め、active key server coverage と
single accepted cluster policy を digest-bound に固定してから、
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
network-attested reviewer quorum と
`cognitive-audit-multi-jurisdiction-review-v1` の
JP-13 / US-CA 法域 quorum を持つ `guardian-oversight` event と、
actual non-loopback mTLS authority route trace から縮約した
`cognitive-audit-non-loopback-verifier-transport-v1` profile、
Federation の `binding-approved` returned result、
Heritage の `binding-rejected` returned result を
同一 cognitive audit follow-up に束ねつつ、
各 returned result を `distributed-council-verdict-signature-binding-v1` の
digest-only signature binding へ包み、signed payload digest と signature digest を
governance binding digest に含め、さらに verifier network receipt ids /
reviewer binding digest / route binding digest を transport profile digest に含めつつ、
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
`ethics_violation=-0.25`) と provenance guard / human pin freeze を JSON で可視化し、
Council 召集・weighted vote・runtime 反映・guardian role の gate に加えて、
self-issued positive event と reciprocal positive boost が fail-closed になることを確認する。

`trust-transfer-demo` は L4 TrustRegistry の cross-substrate transfer contract
(`bounded-cross-substrate-trust-transfer-v1`) を JSON で可視化し、
`source-guardian` / `destination-guardian` / `human-reviewer` の fixed quorum、
source / destination `trust_snapshot` の digest binding、
history / thresholds / provenance policy / eligibility preserve、
`snapshot-clone-with-history` seed mode に加えて、
`export_profile_id=snapshot-clone-with-history | bounded-trust-transfer-redacted-export-v1`
により full snapshot export と redacted projection export を切り替えられ、
redacted profile では `trust_redacted_snapshot` が
sealed snapshot ref / digest、history commitment digest、thresholds、eligibility、
`pinned_reason` と raw history payload を伏せた `redacted_fields`
だけを public surface として返すこと、
同じ redacted profile では `trust_redacted_verifier_federation` が
`trust_redacted_verifier_receipt_summary` を束ね、
`quorum_policy_id` / `trust_root_quorum` / `jurisdiction_quorum` / `jurisdictions`
を保ちつつ freshness timing / transport digest / sealed receipt digest を公開し、
challenge / payload exchange detail を `redacted_fields` へ退避すること、
さらに `trust_redacted_destination_lifecycle` が
`imported -> renewed -> revoked -> recovered` の bounded recovery branch を
sequence / status / timing / `quorum_policy_id` / federation digest / cadence digest /
`trust_root_quorum` / `jurisdiction_quorum` / covered verifier receipt commitment digest へ縮約し、
entry ref / verifier receipt ids / rationale を `redacted_fields` へ退避すること、
さらに `trust_redacted_destination_recovery_summary` が
recovered branch の `recovery_review` から reason code / rationale digest と
jurisdiction policy refs / bundle refs / liability mode / legal-proof digests を
公開し、raw rationale と `legal_ack_refs` を `redacted_fields` へ退避すること、
baseline では `guardian-reviewer-remote-attestation-v1` の 2 verifier receipt を
human reviewer attestation に束縛しつつ、
recovered branch では `required_verifier_count=3` /
`trust_root_quorum=2` / `jurisdiction_quorum=2` の multi-root / cross-jurisdiction
quorum へ昇格した `remote_verifier_federation` と、
`renew_after=10m` / `grace_window=240s` / verifier freshness window 内 renew を
固定した `re_attestation_cadence`、
さらに full profile では destination 側の `imported -> renewed -> revoked -> recovered`
append-only lifecycle、fail-closed revocation action、`recovery_quorum_bound=true`
に加えて full `trust_recovery_review` と
redacted `recovery_review_bound=true` を 1 receipt で確認する。
同じ recovery review は `notice_authority_refs` と
`bounded-trust-recovery-legal-execution-scope-v1` の execution scope manifest を持ち、
redacted export では `execution_scope_summary` と digest だけを公開して
`recovery_notice_scope_bound=true` を返す。

`yaoyorozu-demo` は L4 YaoyorozuRegistry / council convocation の reference contract
(`agentic.yaoyorozu.v0`) を JSON で可視化し、
source workspace に加えて bounded same-host local candidate workspace を
proposal profile ごとの review policy で走査した `yaoyorozu_workspace_discovery` を返し、
`self-modify-patch-v1` では `review_budget=3` / `runtime+schema+eval+docs`、
`memory-edit-v1` では `review_budget=2` / `runtime+eval+docs` required + `schema` optional、
`fork-request-v1` では `review_budget=3` / `runtime+schema+docs` required + `eval` optional、
`inter-mind-negotiation-v1` では `review_budget=3` / `runtime+schema+eval+docs`
という cross-workspace coverage policy を machine-readable に固定する。
そのうえで、
repo-local `agents/` から materialize した trust-bound registry snapshot、
raw `agents/**/*.yaml` が `agent_source_definition.schema` の必須 field、
non-empty substrate / schema refs、repo-local policy refs を満たしてから registry 化されること、
同じ registry snapshot が `repo-local-agent-source-digest-manifest-v1` として
各 raw source definition の `source_ref`、`agent_id`、`role`、`sha256`、`byte_length` を
`source_definition_digests` に束縛し、ordered digest set 由来の
`source_manifest_digest` を返しながら `raw_source_payload_stored=false` を固定すること、
さらに同じ source manifest を
`yaoyorozu-agent-source-manifest-continuity-ledger-binding-v1` として
dedicated `yaoyorozu-agent-source-manifest` ContinuityLedger entry に append し、
`continuity_ledger_entry_ref` / `continuity_ledger_entry_hash` /
`continuity_ledger_payload_ref` / `continuity_ledger_signature_roles=[self, guardian]`
を返し、さらに `yaoyorozu-source-manifest-public-verification-bundle-v1` として
同じ source manifest digest、ledger entry ref/hash/payload ref、self+guardian の
signature digest と verifier key ref を raw signature payload なしで公開検証 bundle に束縛し、
raw source / registry / continuity event payload 非保存を固定すること、
`councilor` role では `deliberation_scope_refs` と `deliberation_policy_ref` を
raw source definition と materialized registry entry の両方に保持し、
議事 transcript 本体ではなく repo-local deliberation boundary ref だけを渡すこと、
さらに `researcher` role では `research_domain_refs` と `evidence_policy_ref` を
raw source definition と materialized registry entry の両方に保持し、
research payload 本体ではなく repo-local evidence boundary ref だけを渡すこと、
加えて `input_schema_ref=specs/schemas/research_evidence_request.schema` と
`output_schema_ref=specs/schemas/research_evidence_report.schema` に固定し、
Council session schema ではなく advisory-only research evidence request/report として
claim ceiling、source refs、raw research payload 非保存、decision authority 不保持を
machine-readable にすること、
同じ demo が選定 researcher の request/report を
`repo-local-research-evidence-exchange-v1` として実際に生成し、
researcher source digest、request/report digest、repo-local evidence digest、
`repo-local-research-evidence-verifier-v1` の repo-local readback verifier receipt、
Council+Guardian 署名付き ContinuityLedger entry ref/hash/payload ref に束縛し、
raw evidence / raw research / network payload 非保存と decision authority 不保持を
runtime validation で確認すること、
さらに複数 researcher exchange を
`repo-local-research-evidence-synthesis-v1` として束ね、
distinct researcher、exchange digest set、evidence digest set、verifier digest set、
Council session ref、Council+Guardian 署名付き ContinuityLedger entry を
単一の advisory-only synthesis receipt に固定し、
raw exchange / raw research payload 非保存と decision authority 不保持を
Council deliberation 前の reviewer-facing artifact として確認すること、
`builder` role では `build_surface_refs` と `execution_policy_ref` を
raw source definition と materialized registry entry の両方に保持し、
coverage label だけではなく repo-local write/eval/schema/doc surface と
実行 policy boundary を same-session handoff 前に監査できること、
さらに `guardian` role では `oversight_scope_refs` と
`attestation_policy_ref` を raw source definition と materialized registry entry の
両方に保持し、Ethics / Identity / Integrity Guardian が監査する
docs / specs / evals / agents / meta surface と attestation policy boundary を
能力名とは別に reviewer-facing へ露出できること、
convocation selection は registry entry 由来の scope を
`registry-selection-scope-binding-v1` として再束縛し、
speaker / recorder には `role_scope_kind=deliberation`、
guardian liaison には `role_scope_kind=oversight`、
profile-specific council panel には selected agent の role に応じた
`deliberation` / `oversight` / `research-evidence` scope を持たせ、
builder handoff には `role_scope_kind=build-surface` を持たせ、
`raw_role_scope_payload_stored=false` のまま scope refs / policy ref だけを
same-session Council artifact に残すこと、さらに builder handoff ごとに
`coverage-area-target-path-binding-v1` で `coverage_area` と
`coverage_target_path_refs` を束縛し、`runtime=src/omoikane/ + tests/unit/ + tests/integration/`、
`schema=specs/interfaces/ + specs/schemas/`、`eval=evals/`、
`docs=docs/ + meta/decision-log/` の target path set が selected builder の
`build_surface_refs` に覆われること、
`Speaker` / `Recorder` / `GuardianLiaison` / `SelfLiaison` の standing role、
`self-modify-patch-v1` の `DesignAuditor` / `ChangeAdvocate` /
`ConservatismAdvocate` / `EthicsCommittee` panel と、
`memory-edit-v1` の `MemoryArchivist` / `DesignAuditor` /
`ConservatismAdvocate` / `EthicsCommittee` panel、
`fork-request-v1` の `IdentityProtector` / `LegalScholar` /
`ConservatismAdvocate` / `EthicsCommittee` panel、
`inter-mind-negotiation-v1` の `LegalScholar` / `DesignAuditor` /
`ConservatismAdvocate` / `EthicsCommittee` panel を
同じ bounded profile catalog から選べること、
さらに convocation 自体が `workspace_discovery_binding` を持ち、
selected profile の review budget / required coverage / accepted workspace set を
same-session Council artifact に束縛すること、
`self-modify-patch-v1` では `runtime/schema/eval/docs`、
`memory-edit-v1` では `runtime/eval/docs`、
`fork-request-v1` では `runtime/schema/docs`、
`inter-mind-negotiation-v1` では `runtime/schema/eval/docs`
を覆う builder handoff coverage、
さらに `memory-edit-v1` は `--include-optional-coverage schema`、
`fork-request-v1` は `--include-optional-coverage eval` により
optional coverage を requested dispatch として追加できること、
さらにそれを same-host subprocess worker へ展開した
`yaoyorozu_worker_dispatch_plan` / `yaoyorozu_worker_dispatch_receipt` が
同一 convocation session に束縛されること、
さらに `workspace_discovery_binding` が存在する場合は
`workspace_execution_binding` により required coverage area を non-source candidate workspace へ割り当て、
requested optional coverage は candidate が無い場合に source fallback として明示し、
`same-host-external-workspace` の execution root に source target-path snapshot を seed してから
同じ local worker stub を実行し、
`same-host-external-workspace-preseed-guardian-gate-v1` の integrity Guardian gate が
HumanOversightChannel の `human-oversight-channel-preseed-attestation-v1`
reviewer-network attestation に束縛されたうえで
workspace seed / execution-root creation / dependency materialization 前に pass したこと、
`same-host-external-workspace-dependency-materialization-v1` manifest が
minimal runtime dependency snapshot を external execution root へ digest-bound に固定し、
`materialized-dependency-lockfile-v1` の dependency lockfile と
`materialized-dependency-wheel-attestation-v1` の sealed wheel artifact digest /
attestation digest を同じ manifest に束縛したこと、
`materialized-dependency-sealed-import-v1` により materialized `src` だけが
worker の `PYTHONPATH` に入る path order を receipt に残し、
`materialized-dependency-module-origin-v1` により
worker が emit した `worker_module_origin` の `module_file` / digest / search path から
`omoikane.agentic.local_worker_stub` が source checkout fallback 無しの
materialized snapshot 由来であることを固定すること、
`workspace_seed_head_commit`、dependency manifest digest、candidate/source 成功 count を receipt に残すこと、
さらに各 worker report が dispatch plan / dispatch unit と workspace root に結び付いた
target path observation と git-bound target path delta receipt、
および `patch_descriptor` 互換で top-priority summary を持つ patch candidate receipt を返すことを確認する。
CLI は `--proposal-profile memory-edit-v1` により
reversible memory-edit 向け convocation / dispatch chain へ切り替えられる。
同じ CLI は `--proposal-profile fork-request-v1` により
identity fork の triple-approval review 向け convocation / dispatch chain へ切り替えられる。
同じ CLI は `--include-optional-coverage schema` /
`--include-optional-coverage eval` により
profile optional coverage だけを on-demand dispatch へ昇格できる。
同じ CLI は `--proposal-profile inter-mind-negotiation-v1` により
disclosure / merge / collective contract review 向け convocation / dispatch chain へ切り替えられる。
さらに同じ session 上で `ConsensusBus` が builder report / guardian gate /
final resolve を監査し、blocked direct handoff と worker claim chain を
`yaoyorozu_consensus_dispatch_binding` として束縛することを確認する。
さらに fixed `max_parallelism=3` を超えないよう
`self-modify-patch-v1` では
`runtime` / `schema` / `evidence-sync(eval+docs)`、
`memory-edit-v1` では
`runtime` / `eval` / `docs`、
`fork-request-v1` では
`runtime` / `schema` / `docs`、
`inter-mind-negotiation-v1` では
`runtime` / `contract-sync(schema+docs)` / `eval`
の 3 root bundle strategy へ畳み込んだ `TaskGraph` が、
同じ session 上の worker claim / guardian gate / resolve digest を
`yaoyorozu_task_graph_binding` として束縛することを確認する。
さらに同じ session の convocation / dispatch / ConsensusBus / TaskGraph bundle を
`L5.PatchGenerator` 向け `build_request` と patch-generator-ready scope validation に接続し、
priority-ranked patch candidate hint を添えた
`yaoyorozu_build_request_binding` として束縛することを確認する。
さらに同じ `build_request` handoff が
`build_artifact` / `sandbox_apply_receipt` / `builder_live_enactment_session` /
`builder_rollback_session` を含む
`yaoyorozu_execution_chain_binding` へ延長され、
repo-local reviewer-facing builder execution chain を
1 つの digest family として可視化することも確認する。
optional dispatch を要求した場合は
`memory-edit-v1` が `runtime` / `contract-eval(eval+schema)` / `docs` へ、
`fork-request-v1` が `runtime` / `schema` / `evidence-docs(docs+eval)` へ
deterministic に切り替わる。

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
fork approval / EWA multi-match conflict resolution の 4 例を JSON で可視化し、
`check_action` 相当の decision payload が schema-bound な `ethics_decision` と
`priority-then-lexical-ethics-resolution-v1` を返し、
`explain_rule` が schema-bound な rule tree を返すことを確認する。

`termination-demo` は L1 TerminationGate の reference contract
(`kernel.termination.v0`) を JSON で可視化し、
正しい self proof による即時終了が
bound Method A handle の `cancel` と execution receipt digest まで閉じること、
事前同意済み cool-off pending と invalid self proof reject が
同じ scheduler handle を cancel せず retain することを 1 シナリオで確認する。

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
さらに abrupt observation に対する
`self-model-advisory-calibration-boundary-v1` receipt を返し、
外部 witness evidence を digest-only に束ねつつ、
本人同意、Council resolution、Guardian redaction が揃っても
`correction_mode=advisory-only`、`forced_correction_allowed=false`、
`accepted_for_writeback=false`、`raw_external_testimony_stored=false` を
維持することを確認する。
同じ abrupt observation 由来の calibration receipt から
`self-model-pathology-escalation-boundary-v1` receipt も返し、
病理的な自己評価の可能性を OS 内診断や強制補正へ昇格させず、
外部医療・法制度の adjudication と care handoff refs へ digest-only に束縛する。
この branch は `os_scope=observe-and-refer-only`、
`care_handoff_required=true`、
`consent_or_emergency_review_required=true`、
`internal_diagnosis_allowed=false`、
`self_model_writeback_allowed=false`、
`forced_correction_allowed=false`、
`raw_medical_payload_stored=false` を確認する。
さらに `self-model-care-trustee-responsibility-handoff-v1` receipt は、
pathology escalation の external handoff refs を前提に、trustee / care team /
legal guardian / responsibility boundary refs を digest-only に束ねる。
この branch は `os_scope=boundary-and-evidence-routing-only`、
`long_term_review_required=true`、`external_adjudication_required=true`、
`os_trustee_role_allowed=false`、`os_medical_authority_allowed=false`、
`os_legal_guardianship_allowed=false`、`self_model_writeback_allowed=false`、
`forced_correction_allowed=false`、`raw_trustee_payload_stored=false` を確認し、
OS が長期 trustee や医療・法的 authority にならない境界を固定する。
さらに `self-model-care-trustee-registry-binding-v1` receipt は、
care trustee handoff の digest と source refs を前提に、current external registry
entries、verifier key refs、not-revoked revocation refs を digest-only に束ねる。
この branch は `role_binding_status=bound`、`registry_status=current`、
`revocation_status=not-revoked`、`external_registry_bound=true`、
`verifier_key_refs_bound=true`、`revocation_refs_bound=true`、
`revocation_verifier_quorum_status=complete`、`revocation_live_verifier_bound=true` を確認する。
また `raw_registry_payload_stored=false`、`raw_revocation_payload_stored=false`、
`raw_revocation_verifier_payload_stored=false`、
`os_trustee_role_allowed=false`、`os_medical_authority_allowed=false`、
`os_legal_guardianship_allowed=false`、`self_model_writeback_allowed=false` を保ち、
OS が外部 registry の検証証跡を持っても trustee / medical / legal authority へ
昇格しない境界を固定する。
さらに `self-model-external-adjudication-result-boundary-v1` receipt は、
care trustee handoff の digest を前提に、外部 medical / legal / trustee の
adjudication result refs、jurisdiction policy refs、appeal / review refs、
continuity review ref を digest-only に束ねる。
この branch は `os_scope=digest-only-result-routing`、
`external_adjudication_result_bound=true`、`jurisdiction_policy_bound=true`、
`appeal_or_review_path_required=true`、
`os_adjudication_authority_allowed=false`、
`os_medical_authority_allowed=false`、`os_legal_authority_allowed=false`、
`os_trustee_role_allowed=false`、`self_model_writeback_allowed=false`、
`raw_medical_result_payload_stored=false` を確認し、OS が外部判断結果の保管・監査経路を
持っても判断主体へ昇格しない境界を固定する。
さらに `self-model-external-adjudication-live-verifier-network-v1` receipt は、
external adjudication result の appeal / review set と jurisdiction policy set を
JP-13 / US-CA の live verifier response、signed response envelope、freshness window、
trust root / route ref へ digest-only に束ねる。
この branch は `network_scope=digest-only-appeal-review-verification`、
`verifier_quorum_status=complete`、
`appeal_review_live_verifier_bound=true`、
`jurisdiction_policy_live_verifier_bound=true`、
`signed_response_envelope_bound=true`、
`stale_response_accepted=false`、`revoked_response_accepted=false`、
`raw_verifier_payload_stored=false` を確認し、live verifier network が
OS adjudication authority や SelfModel writeback authority に昇格しない境界を固定する。
同じ demo は stable drift から生じた新しい価値候補を
`self-model-self-authored-value-generation-v1` receipt に束縛し、
`generation_mode=self-authored-bounded-experiment`、
`integration_status=proposed-not-written-back`、
`requires_future_self_acceptance=true`、`external_veto_allowed=false`、
`forced_stability_lock_allowed=false`、`accepted_for_writeback=false` を
確認する。raw value / continuity payload は保存しない。
さらに同じ demo は future self acceptance と future self reevaluation を経た
value lifecycle を `self-model-value-lineage-timeline-v1` receipt に束ね、
`generated -> accepted -> retired` の chronological event order、
active / retired set の disjointness、archive retention、
`timeline_commit_digest` を確認する。timeline でも raw value / continuity payload は保存せず、
Council / Guardian は boundary-only review に留まる。
退役後の archive retention は
`self-model-value-archive-retention-proof-v1` receipt により、
archive snapshot refs と external trustee / long-term storage / retention policy /
retrieval test refs を digest-only に束縛し、`retention_commit_digest`、
`trustee_proof_bound=true`、`long_term_storage_proof_bound=true`、
`archive_deletion_allowed=false`、`raw_archive_payload_stored=false` を確認する。
さらに future self acceptance 後の value は
`self-model-future-self-reevaluation-retirement-v1` receipt により、
`reassessment_mode=future-self-reevaluated-bounded-retirement`、
`integration_status=retired-from-active-writeback-archive-retained`、
`historical_value_archived=true`、
`active_writeback_retired=true` を満たす場合だけ active writeback から退役できる。
retirement digest は source acceptance、retired value set、writeback ref、
post-reassessment snapshot、archival snapshot を束縛し、raw payload は保存しない。

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

`patch-generator-demo` は L5 PatchGenerator の reference contract
(`selfctor.patch_generator.v0`) を JSON で可視化し、
design-backed `build_request` から planning cue / target subsystem / output path に整列した
ready multi-file patch descriptor を生成しつつ、
workspace escape、immutable boundary 欠落、planning cue 欠如を含む blocked request が
`blocking_rules` を列挙した fail-closed artifact に落ちることを 1 シナリオで確認する。

`diff-eval-demo` は L5 DifferentialEvaluator の reference contract
(`selfctor.diff_eval.v0`) を JSON で可視化し、
selected eval suite、parsed baseline / sandbox observation、
temp workspace の actual command evidence を束縛した `diff_eval_execution_receipt`、
および `pass -> promote`、`fail -> hold`、`regression -> rollback` の
fail-closed classify を direct surface として 1 シナリオで確認する。

`builder-demo` は L5 self-construction builder pipeline の reference contract
(`selfctor.patch_generator.v0` / `selfctor.diff_eval.v0` / `selfctor.rollout.v0`) を
JSON で可視化し、Council の `emit_build_request` handoff が
`design_delta_manifest` / `build_request` / `build_artifact` / `sandbox_apply_receipt` /
`staged_rollout_session` schema に束縛されたまま immutable boundary を検証し、
planning cue と target subsystem に整列した multi-file patch descriptor を生成し、
Mirage Self への sandbox apply、parsed baseline / sandbox observation と
artifact-bound reviewer network attestation を通過した temp workspace の actual command run を束縛した `diff_eval_execution_receipt` と comparison digest を持つ
`council_output_build_request_pipeline` および
`builder_staged_rollout_execution` eval report、`promote` / `hold` / `rollback`
の rollout 分類、Stage 0/1/2/3 (`dark-launch` / `canary-5pct` / `broad-50pct` /
`full-100pct`) の固定順序実行まで
ledger-safe な `self-modify` chain で進むことを確認する。
公開 `staged_rollout_session.schema` との整合は integration test で継続検証する。

`builder-live-demo` は L5 live enactment の reference contract
(`selfctor.enactment.v0`) を JSON で可視化し、
`PatchGeneratorService` が生成した patch descriptor を
artifact payload に束縛された integrity Guardian の reviewer verifier-network attestation を満たしたうえで
temp workspace にだけ materialize しつつ、
runtime/tests/evals/docs/meta/decision-log の approved scope 以外には広げず、
`builder_live_enactment_execution` eval の command を実際に実行し、
`builder_live_oversight_network` expectation と `workspace-enacted` marker を持つ mutated file、
network-attested oversight gate、cleanup 済み receipt を 1 シナリオで確認する。
公開 `builder_live_enactment_session.schema` は canonical
`guardian_oversight_event.schema` と同じ reviewer binding shape を使う。

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
公開 `builder_rollback_session.schema` とは
`max_reverted_patch_count=5` を含む rollback policy contract まで同期する。

`memory-demo` は L2 MemoryCrystal の暫定 compaction policy
(`append-only-segment-rollup-v1`) を JSON で可視化し、
source event を保持したまま最大 3 件ずつ segment 化する manifest と
`crystal-commit` ledger event を確認する。
入力 source event は `EpisodicStream` の handoff window から取り込み、
`compaction_candidate_ids` をそのまま payload に残す。

`memory-replication-demo` は L2 MemoryCrystal replication の reference contract
(`mind.memory_replication.v0`) を JSON で可視化し、
同一 manifest を `primary` / `mirror` / `coldstore` / `trustee` の
fixed four-target set へ束縛しつつ、
`encrypted-content-plus-plaintext-metadata` diff transfer、
random-block Merkle audit、
`trustee` mismatch を latest consensus digest に戻して council escalation へ渡す
bounded reconciliation、
本人が一時的に key を失った場合の threshold key succession receipt
(`3-of-5` share + `2` Guardian attestation + successor key digest / rotation ledger ref /
JP-13 signer roster policy digest / identity-guardian + integrity-guardian signature digest /
JP-13 + SG-01 multi-jurisdiction signer roster quorum digest /
quorum threshold policy registry digest / authority signature digest /
raw key material, raw jurisdiction policy payload, raw quorum threshold policy payload,
and raw roster payload redaction)、
`long-term-media-renewal-proof-v1` による `coldstore` / `trustee` の
renewed media proof、readback digest、3650 日 refresh interval、1000 年 target horizon、
`long-term-media-renewal-cadence-policy-v1` による identity cadence class、
JP-13 / SG-01 jurisdiction cadence policy digest、target refresh interval、
effective refresh / revocation window、
`long-term-media-renewal-refresh-window-v1` による current-not-revoked source proof、
90 日 revocation check、next refresh ref、stale / revoked source fail-closed、
cadence policy digest binding、
`long-term-media-renewal-registry-verifier-v1` による JP-13 / SG-01 registry response
digest、response signature digest、250ms timeout budget、quorum digest、
`long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` による registry
endpoint certificate fingerprint、3-generation certificate chain digest、OCSP /
revocation digest、renewal event、jurisdiction ごとの 2 本の previous certificate
retirement digest、
`long-term-media-renewal-registry-endpoint-certificate-ct-log-readback-v1` /
`long-term-media-renewal-registry-endpoint-certificate-ct-log-quorum-v1` /
`long-term-media-renewal-registry-endpoint-certificate-sct-policy-authority-v1`
による CT-style readback、2-log quorum、SCT timestamp window、
SCT policy authority の digest-only binding、
raw media / raw readback / raw cadence / raw revocation / raw refresh / raw registry /
raw response / raw endpoint certificate / raw certificate freshness /
raw certificate lifecycle / raw certificate CT log /
raw SCT policy authority payload redaction、
`memory-replication` ledger event を 1 シナリオで確認する。

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
snapshot contract 上では `procedural-memory` が deferred surface として残る一方、
validated `Connectome` snapshot に束縛された
`semantic_procedural_handoff` を生成し、
`semantic-projection` と `semantic-handoff` の両 ledger event が
source manifest digest / concept label / handoff digest を記録することを確認する。

`procedural-demo` は L2 procedural preview の reference contract
(`mind.procedural.v0`) を JSON で可視化し、
semantic projection 由来の `semantic_procedural_handoff` と
`MemoryCrystal` segment / `Connectome` snapshot を
`connectome-coupled-procedural-preview-v1` で突き合わせ、
bounded な `weight-delta-preview` recommendation と
`procedural-preview` ledger event が source manifest / connectome digest /
semantic handoff digest / target path を記録することを確認する。

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
同じ session は `procedural_skill_enactment_session.schema` に直接照合され、
mandatory eval と command receipt の `eval_ref` binding が public schema contract として
検証される。

`procedural-actuation-demo` は L2 procedural skill enactment から
L6 External World Agent authorization へ移る boundary contract
(`mind.procedural_actuation.v0`) を JSON で可視化し、
passed / cleaned-up な `procedural_skill_enactment_session` と
`external_actuation_authorization`、approved EWA command audit、
legal execution、Guardian oversight gate、rollback token を
`procedural_actuation_bridge_session` に digest-bound で束ねる。
bridge receipt は raw instruction text を保持せず、
`procedural-actuation-bridge` ledger event と
`interface-ewa-authorization` ledger event の同時成立を確認する。

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
Council-witnessed `memory_glimpse` receipt、
unilateral emergency disconnect、
timeboxed revoke / re-consent receipt をまとめて確認する。
同じ receipt は `council-witnessed-memory-glimpse-receipt-v1` として
MemoryCrystal manifest / selected segment digest、IMC message payload digest、
Council session / resolution / Guardian attestation ref から作る witness digest を束縛し、
raw memory payload と raw message payload を保存しないことを
`imc_memory_glimpse_receipt.schema` と integration test で検証する。
さらに `timeboxed-memory-glimpse-reconsent-receipt-v1` が
元の memory_glimpse receipt digest、participant withdrawal による revocation event、
`expires_after_seconds<=86400` の consent window、Council re-consent ref、
Guardian attestation ref を束縛し、raw re-consent payload を保存しないことを
`imc_memory_glimpse_reconsent_receipt.schema` と integration test で検証する。
さらに `merge_thought` は `federation-council-merge-thought-ethics-gate-v1`
receipt により、Federation Council、EthicsCommittee、Guardian attestation、
distinct collective target、10 秒 cap、emergency disconnect、private recovery、
post-disconnect identity confirmation requirement を digest-only に束縛し、
raw thought payload と raw message payload を保存しないことを
`imc_merge_thought_ethics_receipt.schema` と integration test で検証する。
同じ risk boundary は `merge-thought-window-policy-authority-v1` として
10 秒 cap を policy registry digest、signer roster digest、2 live HTTP verifier
receipt の quorum digest、250ms request timeout budget、verifier network response
digest set、policy body digest、policy signature digest に束縛し、raw policy / verifier / response-signature
payload を保存しない。

`collective-demo` は L6 Collective Identity の reference contract
(`interface.collective.v0`) を JSON で可視化し、
distinct collective ID、`merge_thought` 10 秒 cap、Federation attested merge、
WMS major divergence 後の `private_reality` escape、
全 member の post-disconnect identity confirmation、
`collective_dissolution_receipt.schema` に合う
schema-bound collective dissolution receipt を 1 シナリオで確認する。
同じ receipt は `schema_version=1.0`、全 member confirmation、
`member_recovery_required=true`、digest-only `audit_event_ref` を保持し、
`collective-dissolution-identity-confirmation-binding-v1` として
各 member の `multidimensional-identity-confirmation-v1` confirmation digest、
witness quorum status、self-report/witness consistency digest を束縛し、
raw identity confirmation profile を保存しない。
`interface-collective-dissolution` ledger event は same binding digest と
confirmation digest set を持つため、単独に検証できる。
さらに `collective_recovery_verifier_transport_binding.schema` に合う
`collective-dissolution-recovery-verifier-transport-v1` artifact を返し、
dissolution receipt digest、member recovery binding digest、member ごとの
verified remote reviewer transport receipt、transport exchange digest set、
raw verifier payload 非保存を同じ ledger category へ束縛する。
同じ demo は `collective_recovery_route_trace_binding.schema` に合う
`collective-recovery-non-loopback-route-trace-binding-v1` artifact も返し、
recovery verifier transport binding digest、authenticated non-loopback
distributed authority-route trace digest、member ごとの route binding ref /
remote host attestation ref / socket response digest を束ねる。
さらに `collective_recovery_capture_export_binding.schema` に合う
`collective-recovery-route-trace-capture-export-v1` artifact が、
同じ route binding ref set を verified pcap export、pcap readback digest、
delegated-broker privileged capture acquisition、member ごとの capture binding digest へ
束縛する。
続けて `collective_external_registry_sync.schema` に合う
`collective-dissolution-external-registry-sync-v1` artifact が、
recovery capture export binding digest を external legal registry digest、
governance registry digest、registry entry digest、submission receipt digest、
ack receipt digest、2 jurisdiction ack quorum digest、
ack route trace binding digest、ack route capture binding digest に束縛する。
ack route capture binding は acknowledgement route trace を verified pcap export、
pcap readback digest、delegated-broker privileged capture acquisition、
ack ごとの capture binding digest へつなぐ。
同じ artifact は `collective-external-registry-ack-live-endpoint-probe-v1` により、
legal / governance registry acknowledgement を live HTTP JSON endpoint response digest、
HTTP status、probe latency、endpoint ref、signed response envelope digest に束縛し、
さらに mTLS client certificate ref / fingerprint / chain digest / client CA ref を
response digest と同じ probe receipt に束縛する。
さらに `collective-external-registry-ack-client-certificate-freshness-revocation-v1`
により、client certificate revocation registry ref、OCSP-style response digest、
not-revoked status、24h freshness window を同じ probe receipt に束縛する。
続けて `collective-external-registry-ack-client-certificate-lifecycle-v1` が
previous certificate ref、retirement digest、renewal event digest を同じ probe に束ね、
`renewed` lifecycle だけを complete として受け入れ、`stale` / `revoked`
相当の lifecycle drift は fail-closed にする。
さらに `collective-external-registry-ack-client-certificate-rollover-chain-v1` が
ancestor -> previous -> current の 3 generation certificate refs、
2 件の retirement digest、2 件の renewal event digest、terminal lifecycle proof digest を
chain proof digest に束縛し、単一 rollover だけで complete にならないようにする。
さらに `collective-external-registry-ack-client-certificate-ct-log-readback-v1` が
CT-style log ref、certificate leaf digest、inclusion proof digest、chain proof digest を
同じ endpoint probe に束縛し、raw CT log payload を保存しない。
加えて `collective-external-registry-ack-client-certificate-ct-log-quorum-v1`
が primary / witness の 2 log readback を quorum set digest に束縛し、
`collective-external-registry-ack-client-certificate-sct-timestamp-policy-v1`
が 300 秒 SCT timestamp window を同じ endpoint probe に固定する。
同じ probe は
`collective-external-registry-ack-client-certificate-sct-policy-authority-v1`
として jurisdiction policy registry digest、signer roster digest、2 signer verifier
quorum digest を SCT timestamp digest に束縛する。
probe set digest、response signature digest set、client certificate proof set digest、
client certificate freshness proof set digest、client certificate lifecycle proof set digest、
client certificate lifecycle chain proof set digest、
client certificate CT log readback set digest、
client certificate CT log quorum digest set digest、
client certificate SCT policy authority digest set digest
を registry digest set に含めてから
complete になる。
raw verifier payload、raw route payload、raw dissolution payload、raw registry payload、
raw ack payload、raw ack-route payload、raw endpoint payload、
raw response signature payload、raw client certificate payload、
raw client certificate freshness payload、raw client certificate lifecycle payload、
raw client certificate lifecycle chain payload、
raw client certificate CT log payload、
raw SCT policy authority payload、
raw packet body は保存しない。

`ewa-demo` は L6 External World Agents の reference contract
(`interface.ewa.v0`) を JSON で可視化し、
device-specific `ewa_motor_plan` が
`actuator_profile_id` / `motion_profile` / `target_pose_ref` /
`rollback_vector_ref` / `safe_stop_policy_id` を固定し、
armed `ewa_stop_signal_path` が
`kill_switch_wiring_ref` / `stop_signal_bus_ref` /
fixed 4 trigger binding (`guardian-manual-stop` / `watchdog-timeout` /
`sensor-drift` / `emergency-disconnect`) を固定したうえで、
`ewa_stop_signal_adapter_receipt` が
`profile_id=plc-firmware-stop-signal-adapter-v1` /
`adapter_transport_profile_id=loopback-plc-firmware-probe-v1` /
firmware / PLC program sha256 refs、observed armed bus state、
fixed 4 trigger の PLC contact readiness、raw transcript digest を
stop-signal path digest に束縛したうえで、
`ewa_production_connector_attestation` が
`profile_id=vendor-api-safety-plc-installation-attestation-v1` /
`connector_auth_profile_id=bounded-vendor-api-connector-auth-v1` /
vendor API certificate digest、installation proof digest、
safety PLC ref、maintenance window ref、raw vendor / installation payload
redaction を同じ adapter receipt digest に束縛したうえで、
jurisdiction-bound `ewa_legal_execution` が
`policy_ref` / `legal_basis_ref` / `guardian_verification_id` /
`guardian_verifier_ref` / `notice_authority_ref` / `liability_mode` /
fixed 5-control preflight を固定したうえで、
network-attested `ewa_guardian_oversight_gate` が
`guardian_role=integrity` / `oversight_category=attest` /
`oversight_event_id` / `reviewer_binding_count` /
matched reviewer `verification_id` / `network_receipt_id` /
`authority_chain_ref` / `trust_root_ref` を固定したうえで、
`external_actuation_authorization` artifact が
`instruction_digest` / `intent_summary_digest` / `motor_plan_id` / `stop_signal_path_id` /
`stop_signal_adapter_receipt_id` /
`production_connector_attestation_id` /
`legal_execution_id` / `guardian_verification_ref` /
`guardian_oversight_gate_id` / `jurisdiction_bundle_status=ready` を固定したうえで、
reversible command に Guardian observe を要求しつつ、
`watchdog-timeout` emergency stop が
`command_id` / `bound_command_digest` / `bound_authorization_digest` /
`stop_signal_adapter_receipt_id` /
`production_connector_attestation_id` /
`activated_channel_ref` / `hardware_interlock_state=engaged` /
`release_required=true` を返し、
その後 forced release が実行されること、
さらに別 handle 上で blocked token を含む irreversible command を
fail-closed で veto し、digest-only audit を維持することを確認する。

`wms-demo` は L6 World Model Sync の reference contract
(`interface.wms.v0`) を JSON で可視化し、
minor diff を `consensus-round` で reconcile しつつ、
major diff で `private_reality` 退避を提示し、
`fixed-time-rate-private-escape-v1` により requested `time_rate` deviation を
baseline 1.0 からの digest-bound delta として残しつつ
WorldState の `time_rate` は変更せず private escape を提示し、
`subjective-time-attestation-transport-v1` により participant ごとの
IMC subjective-time attestation receipt を同じ deviation evidence に束縛し、
`unanimous-reversible-physics-rules-v1` により
shared-reality の `physics_rules_ref` 改変を全 participant approval /
`imc-participant-approval-transport-v1` の IMC approval receipt /
Guardian attestation / rollback token に束縛し、
`revert_physics_rules_change` で baseline rules へ戻す receipt を返しつつ、
unauthorized diff を `guardian-veto` / `isolate-session` へ落とすことを確認する。
同じ demo は `approval_subject_digest`、participant ごとの IMC handshake /
message digest、forward secrecy、redaction-free approval payload を
`wms_participant_approval_transport_receipt.schema` と
`wms_physics_rules_change_receipt.schema` の両方で検証できる形に固定する。
time_rate deviation 側も `time_rate_attestation_subject_digest`、participant ごとの
IMC handshake / message digest / forward secrecy を
`wms_time_rate_attestation_receipt.schema` と `wms_reconcile.schema` の両方で
検証できる形に固定する。
さらに 3 participant の approval receipt を
`bounded-wms-approval-collection-v1` / `participant-ordered-batch-digest-v1`
で ordered digest set と `max_batch_size=2` の bounded batches に集約し、
`wms_approval_collection_receipt.schema` と physics change receipt の
`approval_collection_digest` が同じ collection を指すことを確認する。
同じ collection は `distributed-council-approval-fanout-v1` により
Federation distributed transport envelope / authenticated receipt / participant approval
result digest の ordered set へ fan-out され、
`wms_distributed_approval_fanout_receipt.schema` と physics change receipt の
`approval_fanout_digest` が同じ digest-only fan-out receipt を指すことも確認する。
fan-out 中の partial outage は
`bounded-distributed-approval-fanout-retry-v1` /
`participant-retry-outage-digest-v1` により、observer participant の timeout を
`max_retry_attempts=2` / `retry_window_ms=1500` の範囲で retry し、
recovery result digest と recovery transport receipt digest が最終 fan-out result に
一致した時だけ `partial_outage_status=recovered` として physics change へ渡す。
さらに同じ source artifacts を
`digest-bound-wms-engine-transaction-log-v1` の external engine adapter receipt へ束ね、
time_rate escape evidence、approval collection、distributed fan-out、
physics_rules apply、physics_rules revert の 5 committed transaction entry が
`wms_engine_transaction_log.schema` に従って ordered entry digest set、
source artifact digest set、state transition digest、adapter signer key ref、
`signed-wms-engine-adapter-log-v1` signature digest、redaction flags を共有し、
raw adapter signature material を保存しないことを確認する。
さらに completed engine transaction log を
`distributed-transport-bound-wms-engine-adapter-route-v1` の route binding receipt へ束ね、
authenticated cross-host authority-route trace digest、route binding refs、
remote host refs、OS observer tuple / host-binding digests を
`wms_engine_route_binding_receipt.schema` に従って raw engine payload / raw route
payload 無しで共有することを確認する。
さらに completed engine route binding を
`packet-capture-bound-wms-engine-route-v1` の capture binding receipt へ束ね、
verified packet-capture export、delegated privileged capture acquisition、
route binding ref set、PCAP artifact / readback digest、broker lease / filter digest を
`wms_engine_capture_binding_receipt.schema` に従って raw packet body 無しで
共有することを確認する。
さらに recovered fan-out retry を
`bounded-remote-authority-adaptive-retry-budget-v1` の
signed jurisdiction-specific rate limit digest、authority signature digest、
remote authority route-health observation と
`registry-bound-authority-retry-slo-v1` の jurisdiction policy registry digest、
	authority SLO snapshot digest、`registry-slo-derived-retry-schedule-v1` の
	schedule derivation、`live-authority-slo-snapshot-probe-v1` の live HTTP SLO probe receipt、
	`multi-authority-slo-probe-quorum-v1` の 2 authority / 2 jurisdiction quorum receipt、
	`authority-slo-quorum-non-loopback-transport-binding-v1` の
	non-loopback route trace digest / route binding refs / OS observer digest set、
	`signed-authority-slo-quorum-threshold-policy-v1` の signed threshold policy receipt、
`authority-slo-quorum-threshold-signer-roster-v1` の signer roster digest、
`authority-slo-threshold-signer-roster-live-verifier-quorum-v1` の verifier response set digest、
`authority-slo-quorum-threshold-revocation-registry-v1` の revocation registry digest、
	`authority-retry-budget-slo-quorum-transport-binding-v1` の
	retry-budget 側 route trace digest / route binding refs / OS observer digest set、
`fixed-exponential-backoff-with-health-cap-v1` schedule entry へ束ね、
engine transaction log の `approval_fanout_bound` entry と同じ fan-out digest を共有し、
	raw remote authority transcript と raw threshold policy / signer roster / revocation registry /
	authority verifier payload / route trace payload を保存しないことを確認する。

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
同じ demo は sidecar の shared loopback path も返し、
`participant_identity_ids` / `shared_imc_session_id` / `shared_collective_id` を束縛した
collective-shared session 上で、
owner handoff を伴う `shared-aligned` / `guardian-mediated` arbitration を
別の digest-only artifact family として machine-checkable に残す。
さらに `sensory-loopback-public-schema-contract-v1` の `schema_contracts` manifest が
self-only と shared loopback の session / receipt / artifact family payload を
`sensory_loopback_session.schema` /
`sensory_loopback_receipt.schema` /
`sensory_loopback_artifact_family.schema` へ列挙し、
integration test が demo payload を public schema に直接通す。

`version-demo` は hybrid versioning policy を JSON で可視化し、
runtime semver、IDL/schema の `bootstrap` stability、governance calver、
`specs/catalog.yaml` の sha256 snapshot を 1 つの manifest に集約して確認する。
同じ manifest は `catalog_inventory_receipt` を返し、
`specs-catalog-generated-inventory-v1` profile で catalog entries、priority/kind counts、
実装済み schema/IDL coverage、欠落・重複ゼロの検証結果を digest-bound に固定する。

`naming-demo` は naming policy を JSON で可視化し、
project branding の英字表記を `Omoikane` に固定し、
サンドボックス自我の formal name を `Mirage Self` に固定しつつ、
runtime 実装上は `SandboxSentinel` alias を内部 detail としてのみ許容することを確認する。

## 今後広げる面

- automation による未実装ギャップの継続充填
