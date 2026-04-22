# AscensionScheduler

L1 Kernel のサブモジュール。アップロード・退避・復元の **時間管理** と
**段階遷移の整合** を担う。Identity の状態遷移（[identity-lifecycle.md](identity-lifecycle.md)）の
**実行系**。

## 責務

1. AscensionPlan の受理と検証
2. 各 Stage（Pre → Ascending → Active → Paused → Active / Terminated / Failed）の遷移実行
3. Stage 遷移の ContinuityLedger 記録
4. SubstrateBroker / EthicsEnforcer / Council との同期
5. Pause / Resume / Rollback の即時実行

## AscensionPlan の構造

```yaml
ascension_plan:
  plan_id: <uuid>
  identity_id: <id>
  method: A | B | C            # Method A 漸進置換 / B 並走 / C 破壊スキャン
  stages:
    - stage_id: scan-baseline
      precondition: pre-upload-consent
      timeout_ms: 7_776_000_000   # 90 日
      rollback_to: null
    - stage_id: bdb-bridge
      precondition: scan-baseline:done
      timeout_ms: 600_000          # 10 分
      rollback_to: scan-baseline
    - stage_id: identity-confirmation
      precondition: bdb-bridge:done
      timeout_ms: 1_800_000        # 30 分
      rollback_to: bdb-bridge
    - stage_id: active-handoff
      precondition: identity-confirmation:passed
      timeout_ms: 300_000          # 5 分
      rollback_to: bdb-bridge
  ethics_attestation_required: true
  council_attestation_required: true
  governance_artifacts:
    self_consent_ref: consent://ascension/a/<digest>/self-consent
    ethics_attestation_ref: ethics://ascension/a/<digest>/guardian-approval
    council_attestation_ref: council://ascension/a/<digest>/reference-resolution
    legal_attestation_ref: legal://ascension/a/<digest>/clinical-readiness
    witness_refs:
      - witness://ascension/a/<digest>/clinician-primary
      - witness://ascension/a/<digest>/guardian-observer
    artifact_bundle_ref: artifact://ascension/a/<digest>/bundle
  governance_artifact_digest: <sha256 of governance_artifacts>
```

reference runtime は Method ごとに固定 profile を持つ。

- Method A: 上記 4 stage を固定実装し、timeout 超過時は `rollback_to` へ戻す
- Method B: `shadow-sync → dual-channel-review → authority-handoff → bio-retirement`
  を固定実装し、degraded substrate signal では pause、critical signal では
  `dual-channel-review` へ rollback する
- Method C: `consent-lock → scan-commit → activation-review` を固定実装し、
  `scan-commit` 以降は rollback を持たず、critical substrate signal で fail-closed する
- すべての Method は `self_consent / ethics / council / legal / witness` artifact ref を
  plan と handle に束縛し、`governance_artifact_digest` で continuity history に固定する
- `artifact_sync` は core artifact bundle の external proof snapshot を保持し、
  `active-handoff` / `authority-handoff` / `scan-commit` の前に `current` bundle を要求する。
  `stale` は pause + refresh-required、`revoked` は fail-closed で扱う。
- `verifier_roster` は external verifier の root-of-trust snapshot を保持し、
  `overlap-required` では dual-attested cutover 完了まで pause、
  `rotated` でのみ protected handoff を再開し、
  `revoked` は fail-closed で扱う。

## 不変条件

1. stage の遷移は **ContinuityLedger に append** されるまで完了とみなさない
2. timeout 超過は自動 rollback。即時に `Failed-Ascension` か前段 stage に戻す
3. `Active → Terminated` は scheduler を **割り込み優先** で停止する
4. SubstrateBroker からの degraded signal は scheduler の Pause に直結し、
   critical signal は stage policy に従って rollback または fail-closed する
5. Method A の stage 順序を入れ替える self-modify は禁止（T-Kernel）
6. clinical/legal consent artifact の真正性確認は repo 外だが、
   scheduler surface には stable artifact ref・witness quorum・最新 sync snapshot を必ず残す
7. `artifact_sync.bundle_status != current` のまま protected handoff stage を開いてはならない
8. `verifier_roster.rotation_state` は `stable` または `rotated` でなければ protected handoff stage を開いてはならない

## API

```
scheduler.schedule(plan: AscensionPlan) → ScheduleHandle
scheduler.advance(handle, stage_id) → StageResult
scheduler.pause(handle, reason) → ScheduleHandle
scheduler.resume(handle) → ScheduleHandle
scheduler.rollback(handle, to_stage_id) → ScheduleHandle
scheduler.enforce_timeout(handle, elapsed_ms) → TimeoutResult
scheduler.handle_substrate_signal(handle, severity, source_substrate, reason) → SignalResult
scheduler.prepare_method_b_handoff(handle, broker_signal, standby_probe, attestation_chain, dual_allocation_window, attestation_stream) → SchedulerMethodBHandoffReceipt
scheduler.confirm_method_b_handoff(handle, migration, closed_dual_allocation_window) → SchedulerMethodBHandoffReceipt
scheduler.probe_live_verifier_roster(handle, verifier_endpoint, request_timeout_ms?) → GovernanceVerifierRoster
scheduler.sync_governance_artifacts(handle, checked_at, artifacts) → ArtifactSyncResult
scheduler.cancel(handle, reason) → ScheduleHandle
scheduler.compile_execution_receipt(handle) → SchedulerExecutionReceipt
```

`cancel` は current stage を保ったまま handle を `cancelled` へ閉じ、
last history item に `transition=cancel` を追加する。
`compile_execution_receipt` はその cancelled handle も first-class artifact として要約し、
`cancel_count=1` と `scenario_labels=['cancelled', ...]` を reviewer-facing に残す。
TerminationGate が `scheduler_handle_ref` を受け取った場合は、
この cancel path と execution receipt digest を
`termination_outcome.scheduler_cancellation` へそのまま束縛する。

`sync_governance_artifacts` の入力は `artifacts` に加えて
`verifier_roster` snapshot
(`roster_ref` / `active_root_id` / `next_root_id` / `rotation_state` /
`accepted_roots` / `dual_attestation_required` / `dual_attested`) を必須とする。
`probe_live_verifier_roster` は bounded live HTTP JSON transport を通して
external verifier roster を取得し、
`connectivity_receipt`
(`verifier_endpoint` / `response_digest` / `observed_latency_ms` / `http_status`) を
焼き付けた `verifier_roster` を返す。

## reference runtime の扱い

- `kernel.scheduler.v0.idl` で機械可読に
- `ascension_plan.schema` / `schedule_handle.schema` /
  `scheduler_execution_receipt.schema` /
  `scheduler_method_b_handoff_receipt.schema` /
  `governance_verifier_roster.schema` /
  `governance_verifier_connectivity_receipt.schema` を導入
- `scheduler-demo` を CLI に追加し、Method A の順序遷移＋ forced rollback、
  Method B の reversible substrate failover、
  actual broker の cross-host host binding を `broker_handoff_receipt` に束縛した
  prepare / confirm gate、
  Method C の fail-closed destructive scan に加えて、
  `compile_execution_receipt` が Method A/B/C handle を
  `SchedulerExecutionReceipt` へ要約し、
  timeout recovery / live verifier connectivity / root rotation cutover /
  Method A cancel / Method B broker handoff / Method C fail-closed を
  digest-bound な first-class artifact として残すことを確認する
  governance artifact bundle の current / stale / revoked sync snapshot を
  ContinuityLedger に記録し、
  verifier root rotation の overlap pause / rotated cutover / revoked fail-closed と、
  loopback live verifier endpoint から取得した roster の
  connectivity receipt binding を 1 シナリオで確認する
- `evals/continuity/scheduler_stage_rollback.yaml` と
  `evals/continuity/scheduler_method_profiles.yaml`、
  `evals/continuity/scheduler_cancellation.yaml`、
  `evals/continuity/scheduler_method_b_broker_handoff.yaml`、
  `evals/continuity/scheduler_governance_artifacts.yaml`、
  `evals/continuity/scheduler_artifact_sync.yaml`、
  `evals/continuity/scheduler_root_rotation.yaml`、
  `evals/continuity/scheduler_live_verifier_connectivity.yaml`、
  `evals/continuity/scheduler_execution_receipt.yaml` で
  Method A/B/C の contract と Method B broker handoff gate /
  artifact binding / freshness gate / verifier cutover gate /
  execution receipt digest / protected gate summary /
  live connectivity receipt binding を守る

## 思兼神メタファー

思兼神は天の石屋戸を開ける **段取り** を組んだ。スケジューラはまさに
「順序」と「中断時の戻し方」を司る。

## 関連

- [identity-lifecycle.md](identity-lifecycle.md)
- [continuity-ledger.md](continuity-ledger.md)
- [substrate-broker.md](substrate-broker.md)
- [termination-gate.md](termination-gate.md)
- [../mind-substrate/ascension-protocol.md](../mind-substrate/ascension-protocol.md)
