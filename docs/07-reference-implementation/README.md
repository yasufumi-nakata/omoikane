# Reference Implementation

OmoikaneOS の `src/` 配下には、意識や人格成立を主張しない **reference runtime** を置く。
目的は次の 3 つである。

1. docs/ と specs/ の整合をコードで検証する
2. evals/ の受け皿を用意する
3. 将来の本格実装に渡す前に、安全境界と不可侵領域を固定する

## 境界

- `src/omoikane/` は L0/L1/L2/L4/L5 と、L3 reasoning/affect/attention/volition/imagination/language/metacognition failover、L6 BDB の bounded viability contract を扱う
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
PYTHONPATH=src python3 -m omoikane.cli council-demo --json
PYTHONPATH=src python3 -m omoikane.cli multi-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-council-demo --json
PYTHONPATH=src python3 -m omoikane.cli distributed-transport-demo --json
PYTHONPATH=src python3 -m omoikane.cli cognitive-audit-demo --json
PYTHONPATH=src python3 -m omoikane.cli task-graph-demo --json
PYTHONPATH=src python3 -m omoikane.cli consensus-bus-demo --json
PYTHONPATH=src python3 -m omoikane.cli trust-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-demo --json
PYTHONPATH=src python3 -m omoikane.cli oversight-network-demo --json
PYTHONPATH=src python3 -m omoikane.cli ethics-demo --json
PYTHONPATH=src python3 -m omoikane.cli termination-demo --json
PYTHONPATH=src python3 -m omoikane.cli substrate-demo --json
PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json
PYTHONPATH=src python3 -m omoikane.cli imc-demo --json
PYTHONPATH=src python3 -m omoikane.cli collective-demo --json
PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json
PYTHONPATH=src python3 -m omoikane.cli wms-demo --json
PYTHONPATH=src python3 -m omoikane.cli connectome-demo --json
PYTHONPATH=src python3 -m omoikane.cli episodic-demo --json
PYTHONPATH=src python3 -m omoikane.cli memory-demo --json
PYTHONPATH=src python3 -m omoikane.cli semantic-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-writeback-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-skill-demo --json
PYTHONPATH=src python3 -m omoikane.cli procedural-enactment-demo --json
PYTHONPATH=src python3 -m omoikane.cli qualia-demo --json
PYTHONPATH=src python3 -m omoikane.cli self-model-demo --json
PYTHONPATH=src python3 -m omoikane.cli design-reader-demo --json
PYTHONPATH=src python3 -m omoikane.cli reasoning-demo --json
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

`scheduler-demo` は L1 AscensionScheduler の reference contract
(`kernel.scheduler.v0`) を JSON で可視化し、
Method A の 4 stage blueprint、順序違反の reject、
`identity-confirmation` timeout 超過時の `bdb-bridge` への自動 rollback、
Method B の degraded / critical substrate signal に対する pause / rollback、
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
live-proof surrogate snapshot が `veto` attestation に immutable binding として焼き付くこと、
scope 外 reviewer が `pin-renewal` を attest できず fail-closed になること、
その後 reviewer 不足で `pin-renewal` が `breached` になった時に
`integrity-guardian` の human pin と guardian eligibility が外れることを確認する。

`oversight-network-demo` は L4 Guardian reviewer verifier-network transport を JSON で可視化し、
fixed endpoint registry から解決された `verifier_endpoint` /
`authority_chain_ref` / `trust_root_ref` / `trust_root_digest` を持つ
`guardian_verifier_network_receipt` が reviewer verification に束縛され、
その receipt id と root binding が `veto` attestation の immutable reviewer binding に
焼き付くことを確認する。

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
`docs/` / `specs/` source digest、`must_sync_docs`、
`design_delta_manifest`、`build_request` handoff を 1 シナリオで確認する。

`builder-demo` は L5 self-construction builder pipeline の reference contract
(`selfctor.patch_generator.v0` / `selfctor.diff_eval.v0` / `selfctor.rollout.v0`) を
JSON で可視化し、Council の `emit_build_request` handoff が
`design_delta_manifest` / `build_request` / `build_artifact` / `sandbox_apply_receipt` /
`staged_rollout_session` schema に束縛されたまま immutable boundary を検証し、
Mirage Self への sandbox apply、`council_output_build_request_pipeline` と
`builder_staged_rollout_execution` eval 選定、`promote` / `hold` / `rollback`
の rollout 分類、Stage 0/1/2/3 (`dark-launch` / `canary-5pct` / `broad-50pct` /
`full-100pct`) の固定順序実行まで
ledger-safe な `self-modify` chain で進むことを確認する。

`builder-live-demo` は L5 live enactment の reference contract
(`selfctor.enactment.v0`) を JSON で可視化し、
`PatchGeneratorService` が生成した patch descriptor を
temp workspace にだけ materialize しつつ、
`builder_live_enactment_execution` eval の command を実際に実行し、
`workspace-enacted` marker を持つ mutated file と
cleanup 済み receipt を 1 シナリオで確認する。

`rollback-demo` は L5 builder rollback の reference contract
(`selfctor.rollback.v0`) を JSON で可視化し、
rollback 判定済み staged rollout が `builder_rollback_session` を通じて
`pre-apply` Mirage Self snapshot を復元し、
`dark-launch` / `canary-5pct` の revoke 範囲、
live enactment receipt に束縛された reverse-apply journal と telemetry gate、
append-only continuity ref 2 本、
self / council / guardian の 3 者通知を
1 シナリオで確認する。

`memory-demo` は L2 MemoryCrystal の暫定 compaction policy
(`append-only-segment-rollup-v1`) を JSON で可視化し、
source event を保持したまま最大 3 件ずつ segment 化する manifest と
`crystal-commit` ledger event を確認する。
入力 source event は `EpisodicStream` の handoff window から取り込み、
`compaction_candidate_ids` をそのまま payload に残す。

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
reversible command に Guardian observe を要求しつつ、
blocked token を含む irreversible command を
fail-closed で veto し、digest-only audit と forced release を確認する。

`wms-demo` は L6 World Model Sync の reference contract
(`interface.wms.v0`) を JSON で可視化し、
minor diff を `consensus-round` で reconcile しつつ、
major diff で `private_reality` 退避を提示し、
unauthorized diff を `guardian-veto` / `isolate-session` へ落とすことを確認する。

`version-demo` は hybrid versioning policy を JSON で可視化し、
runtime semver、IDL/schema の `bootstrap` stability、governance calver、
`specs/catalog.yaml` の sha256 snapshot を 1 つの manifest に集約して確認する。

`naming-demo` は naming policy を JSON で可視化し、
project branding の英字表記を `Omoikane` に固定し、
サンドボックス自我の formal name を `Mirage Self` に固定しつつ、
runtime 実装上は `SandboxSentinel` alias を内部 detail としてのみ許容することを確認する。

## 今後広げる面

- non-loopback distributed PKI authority plane と external key server 群への接続
- automation による未実装ギャップの継続充填
