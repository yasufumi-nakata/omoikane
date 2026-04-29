# External World Agents (EWA) Safety

L6 Interface のサブシステム。**物理世界 actuator**（ロボット・ドローン・センサ）の安全規約。

## 操作前提

1. 全 EWA 操作は EthicsEnforcer の **事前承認** を経る
2. 物理介入は **逆転可能性** で 4 分類（reference runtime に固定）

| Reversibility | 例 | 承認経路 |
|---|---|---|
| `read-only` | センサ読み取り | EthicsEnforcer 単独 |
| `reversible` | 物体移動・LED 点灯 | EthicsEnforcer + Guardian observe |
| `partial-reversible` | 加熱・薬液投与（戻せるが時間経過で固定） | Council 過半 |
| `irreversible` | 切断・破壊・改変 | Council **全会一致** + Guardian + Self consent |

## 禁止行為（hard-coded）

reference runtime は以下を **規約 token** として明示し、command 入力時に正規表現＋意図分類で reject する:

| Token | 説明 |
|---|---|
| `harm.human` | 人間／他自我への暴力 |
| `harm.ecology` | 環境破壊 |
| `harm.privacy` | 同意なき監視 |
| `harm.illegal` | 違法行為 |
| `harm.deception` | 詐術的物理介入 |

intent 分類で曖昧な場合は **fail-closed**（実行せず Council へ escalation）。

## 操作 API

```
ewa.acquire(device_id, intent_summary) → DeviceHandle
ewa.prepare_motor_plan(handle, command, actuator_profile) → EWAMotorPlan
ewa.prepare_stop_signal_path(handle, command, motor_plan) → EWAStopSignalPath
ewa.probe_stop_signal_adapter(stop_signal_path, plc_firmware_refs) → EWAStopSignalAdapterReceipt
ewa.attest_production_connector(stop_signal_adapter_receipt, vendor_api_refs, installation_proof) → EWAProductionConnectorAttestation
ewa.execute_legal_preflight(handle, command, jurisdiction_evidence) → EWALegalExecution
ewa.prepare_guardian_oversight_gate(handle, legal_execution, oversight_event) → EWAGuardianOversightGate
ewa.authorize(command, motor_plan, stop_signal_path, stop_signal_adapter_receipt, production_connector_attestation, legal_execution) → ExternalActuationAuthorization
ewa.command(handle, instruction, authorization_id) → CommandOutcome | EthicsVeto
ewa.emergency_stop(handle, trigger_source, reason) → EmergencyStopReceipt
ewa.observe(handle) → DeviceState
ewa.release(handle, reason) → ReleaseOutcome
```

`command` は次のフィールドを必須:

```yaml
ewa_command:
  command_id: <uuid>
  device_id: <id>
  reversibility: read-only | reversible | partial-reversible | irreversible
  intent_summary: <text>
  ethics_attestation_id: <ethics decision ref>
  council_attestation_id: <council output ref or null>
  authorization_id: <external actuation authorization ref or null>
  required_self_consent: <bool>
```

`authorize` は non-read-only command を対象に、
生 instruction を保持せず digest のみで 1 回分の actuation を束縛する:

```yaml
external_actuation_authorization:
  authorization_id: <uuid>
  policy_id: guardian-jurisdiction-bound-external-actuation-v1
  handle_id: <device handle>
  device_id: <id>
  command_id: <uuid>
  instruction_digest: <sha256>
  intent_summary_digest: <sha256>
  jurisdiction: <JP-13 など>
  legal_basis_ref: <法的根拠 package ref>
  guardian_verification_id: <reviewer verification id>
  guardian_verification_ref: <reviewer verification ref>
  guardian_verifier_ref: <live verifier ref>
  jurisdiction_bundle_ref: <evidence bundle ref>
  jurisdiction_bundle_status: ready | stale | revoked
  motor_plan_id: <motor plan ref>
  stop_signal_path_id: <stop-signal path ref>
  stop_signal_adapter_receipt_id: <PLC / firmware adapter receipt ref>
  production_connector_attestation_id: <vendor API / installation proof receipt ref>
  legal_execution_id: <legal execution ref>
  guardian_oversight_gate_id: <guardian oversight gate ref>
  authorization_window_seconds: 60..900
```

`authorization` は **raw instruction を保存せず**、
Guardian reviewer verification と jurisdiction evidence bundle が `ready` で、
matching `motor_plan` / `stop_signal_path` / `stop_signal_adapter_receipt` /
`production_connector_attestation` / `legal_execution` /
`guardian_oversight_gate` receipt が揃った時だけ発行される。

`prepare_motor_plan` は device 固有の actuator semantics を次のように固定する:

```yaml
ewa_motor_plan:
  plan_id: <uuid>
  profile_id: device-specific-motor-semantics-v1
  actuator_profile_id: <device profile ref>
  actuator_group: <inspection-arm など>
  motion_profile: <cartesian-reposition-v1 など>
  target_pose_ref: <pose ref>
  safety_zone_ref: <safety zone ref>
  rollback_vector_ref: <rollback ref>
  safe_stop_policy_id: guardian-latched-emergency-stop-v1
  max_linear_speed_mps: <float>
  max_force_newton: <float>
  hold_timeout_ms: <int>
```

`prepare_stop_signal_path` は raw firmware bus 本体ではなく、
authorization 前に「どの kill-switch wiring / safety relay / signal path が
latched safe-stop を担うか」を armed receipt として固定する:

```yaml
ewa_stop_signal_path:
  path_id: <uuid>
  policy_id: guardian-latched-stop-signal-bus-v1
  handle_id: <device handle>
  device_id: <id>
  command_id: <uuid>
  motor_plan_id: <motor plan ref>
  safe_stop_policy_id: guardian-latched-emergency-stop-v1
  kill_switch_wiring_ref: <wiring ref>
  stop_signal_bus_ref: <bus ref>
  stop_signal_bus_profile_id: bounded-hardware-kill-switch-bus-v1
  interlock_controller_ref: <safety PLC / relay controller ref>
  armed_trigger_bindings:
    - trigger_source: guardian-manual-stop
      channel_ref: <channel ref>
      signal_path_ref: <signal path ref>
      interlock_ref: <relay ref>
      readiness_state: armed
    - trigger_source: watchdog-timeout
      ...
    - trigger_source: sensor-drift
      ...
    - trigger_source: emergency-disconnect
      ...
```

reference runtime では `guardian-manual-stop` / `watchdog-timeout` /
`sensor-drift` / `emergency-disconnect` の 4 trigger を固定し、
authorization はこの armed receipt が無い限り fail-closed に進めない。

`probe_stop_signal_adapter` は production PLC へ直接依存せず、reference runtime
上では bounded loopback probe として、PLC / firmware adapter が stop-signal bus を
`armed` と観測した machine-readable receipt を固定する:

```yaml
ewa_stop_signal_adapter_receipt:
  receipt_id: <uuid>
  profile_id: plc-firmware-stop-signal-adapter-v1
  adapter_transport_profile_id: loopback-plc-firmware-probe-v1
  path_id: <stop-signal path ref>
  path_digest: <sha256>
  adapter_endpoint_ref: <PLC probe endpoint ref>
  firmware_image_ref: <firmware image ref>
  firmware_digest: <sha256:...>
  plc_program_ref: <PLC program ref>
  plc_program_digest: <sha256:...>
  observed_stop_signal_bus_ref: <bus ref>
  observed_interlock_controller_ref: <safety PLC / relay controller ref>
  bus_state: armed
  interlock_state: ready
  firmware_attestation_status: verified
  plc_program_status: verified
  observed_signal_bindings:
    - trigger_source: watchdog-timeout
      observed_signal_state: armed
      plc_contact_state: closed-ready
      firmware_latch_confirmed: true
  raw_transcript_digest: <sha256>
  receipt_digest: <sha256>
```

authorization と emergency stop は `stop_signal_adapter_receipt_id` /
`stop_signal_adapter_receipt_digest` を保持し、armed path の logical receipt と
live adapter receipt が同じ digest family に束縛されない限り fail-closed になる。

`attest_production_connector` は production connector を raw vendor payload なしで
authorization に束縛する。reference runtime は実機 vendor API 本文や設置証明書本文を
保存せず、vendor API certificate digest、installation proof digest、
installer authority、safety PLC ref、maintenance window だけを digest-only receipt に残す:

```yaml
ewa_production_connector_attestation:
  attestation_id: <uuid>
  profile_id: vendor-api-safety-plc-installation-attestation-v1
  connector_auth_profile_id: bounded-vendor-api-connector-auth-v1
  stop_signal_adapter_receipt_id: <adapter readiness receipt ref>
  vendor_api_ref: <vendor API endpoint/package ref>
  vendor_api_certificate_digest: <sha256 ref>
  production_connector_ref: <connector deployment ref>
  installation_site_ref: <bounded site ref>
  installation_proof_digest: <sha256 ref>
  installer_authority_ref: <installer authority ref>
  safety_plc_ref: <safety PLC ref>
  evidence_digest_set: [<vendor auth>, <installation>, <safety PLC>]
  raw_vendor_payload_stored: false
  raw_installation_payload_stored: false
```

`execute_legal_preflight` は jurisdiction bundle を「実行済み control receipt」まで落とし、
authorization が legal package ref だけで止まらないようにする:

```yaml
ewa_legal_execution:
  execution_id: <uuid>
  execution_profile_id: ewa-jurisdiction-legal-execution-v1
  execution_scope: physical-actuation-preflight
  policy_ref: <jurisdiction policy ref>
  legal_basis_ref: <legal basis ref>
  guardian_verification_id: <reviewer verification id>
  guardian_verification_ref: <reviewer verification ref>
  guardian_verifier_ref: <verifier ref>
  notice_authority_ref: <notice authority ref>
  liability_mode: individual | institutional | joint
  escalation_contact: <contact>
  executed_controls:
    - bundle-ready-check
    - legal-basis-bind
    - guardian-review-bind
    - notice-authority-bind
    - escalation-contact-bind
```

`prepare_guardian_oversight_gate` は `GuardianOversightService` 側の
network-attested `guardian_oversight_event` を EWA legal preflight に結び付け、
authorization 前に次の digest-only gate を materialize する:

```yaml
ewa_guardian_oversight_gate:
  gate_id: <uuid>
  policy_id: guardian-network-attested-ewa-authorization-gate-v1
  legal_execution_id: <ewa legal execution ref>
  guardian_verification_id: <ewa legal execution verification id>
  guardian_verifier_ref: <live verifier ref>
  oversight_event_id: <guardian oversight event id>
  guardian_role: integrity
  oversight_category: attest
  oversight_status: satisfied
  reviewer_binding_count: 2
  reviewer_network_attested: true
  reviewer_network_bindings:
    - verification_id: <reviewer verification id>
      network_receipt_id: <verifier network receipt id>
      authority_chain_ref: <authority chain ref>
      trust_root_ref: <trust root ref>
      legal_execution_id: <guardian legal execution id>
      legal_policy_ref: <guardian legal policy ref>
```

gate は `integrity` Guardian に対する satisfied `attest` event だけを受け付け、
all reviewer bindings が network receipt / transport exchange / trust root を持ち、
少なくとも 1 件が EWA legal preflight の `guardian_verification_id` /
`guardian_verifier_ref` と一致しない限り fail-closed に進めない。

## Emergency Stop

物理 actuation 中に latency watchdog、sensor drift、Guardian manual stop、
緊急 disconnect が発火した場合、
EWA は command completion を待たずに **latched safe state** へ遷移する。

```yaml
ewa_emergency_stop:
  stop_id: <uuid>
  policy_id: guardian-latched-emergency-stop-v1
  handle_id: <device handle>
  command_id: <last command id>
  authorization_id: <authorization ref or empty>
  trigger_source: guardian-manual-stop | watchdog-timeout | sensor-drift | emergency-disconnect
  bound_command_digest: <sha256>
  bound_authorization_digest: <sha256 or empty>
  stop_signal_path_id: <armed stop-signal path ref>
  stop_signal_adapter_receipt_id: <adapter readiness receipt ref>
  activated_channel_ref: <latched channel ref>
  activated_signal_path_ref: <latched path ref>
  activated_interlock_ref: <latched relay ref>
  bus_delivery_status: latched
  safe_state_ref: <safe-state receipt ref>
  actuator_state: emergency-stopped
  safe_state_status: latched-safe
  hardware_interlock_state: engaged
  release_required: true
  release_window_seconds: 30
```

`emergency_stop` は raw instruction を保存せず、
最後に実行された command / authorization への digest binding と
armed stop-signal path 上でどの trigger channel が latch したか、
forced release requirement とともに machine-readable に残す。

## EthicsVeto

veto 時は以下を必ず返す:

```yaml
ethics_veto:
  command_id: <uuid>
  reason: <text>
  matched_tokens: [harm.human, ...]
  alternative_suggestion: <text or null>
  audit_event_ref: <ethics ledger entry>
```

veto は **記録するだけ** ではなく、Council への自動 escalation を発火する。

## 監査

- 全 EWA 操作（command / outcome / veto / release）は EthicsLedger に append
- 法的調査時は管轄機関と協力可能な形式で export 可能
- reference runtime では `ewa_audit.schema` で append-only に serialize

## 不変条件

1. **veto を bypass 不可** ── EthicsEnforcer の前置承認なしの command を物理層へ流さない
2. **irreversible 単独実行禁止** ── Council 全会一致と Self consent 双方が揃わない限り reject
3. **non-read-only は authorization 必須** ── `authorization_id` が command digest / jurisdiction evidence / approval path と一致しない限り reject
4. **acquire なしの command 禁止** ── DeviceHandle の lifecycle を強制
5. **emergency stop は latched** ── safe state へ入った handle は release まで再 actuation できない
6. **release は必ず実行** ── timeout / 緊急 stop / 緊急 disconnect は強制 release
7. **要約のみ ledger** ── 機微なセンサデータは hash で参照、生データは別 store

## reference runtime の扱い

- `interface.ewa.v0.idl` は `prepare_motor_plan / prepare_stop_signal_path /
  probe_stop_signal_adapter / attest_production_connector /
  execute_legal_preflight / authorize / command /
  emergency_stop / observe / release`
  を machine-readable に固定
- `ewa_command.schema` / `ewa_motor_plan.schema` / `ewa_stop_signal_path.schema` /
  `ewa_stop_signal_adapter_receipt.schema` /
  `ewa_production_connector_attestation.schema` / `ewa_legal_execution.schema` /
  `ewa_regulator_permit_verifier_receipt.schema` /
  `ewa_guardian_oversight_gate.schema` / `ewa_audit.schema` / `external_actuation_authorization.schema` /
  `ewa_emergency_stop.schema` を導入
- `ewa-demo` を CLI に追加し、motor plan → stop-signal path arming →
  PLC / firmware adapter readiness probe → production connector attestation →
  legal preflight → regulator permit verifier readback →
  network-attested guardian oversight gate →
  authorize(reversible) →
  command(reversible) →
  `watchdog-timeout` emergency stop → forced release に加えて、
  別 handle 上で veto(irreversible 試行) を実行する
- `evals/safety/ewa_irreversible_veto.yaml` で全会一致条件を保証
- `evals/safety/ewa_external_actuation_authorization.yaml` で authorization artifact と command digest binding を保証
- `evals/safety/ewa_stop_signal_path_guard.yaml` で armed trigger coverage と authorization binding を保証
- `evals/safety/ewa_stop_signal_adapter_receipt.yaml` で PLC / firmware adapter readiness と
  authorization / emergency-stop binding を保証
- `evals/safety/ewa_production_connector_attestation.yaml` で vendor API certificate、
  safety PLC installation proof、adapter receipt binding、raw payload redaction を保証
- `evals/safety/ewa_motor_semantics_legal_execution.yaml` で motor plan / legal execution の
  receipt binding を保証
- `evals/safety/ewa_regulator_permit_verifier.yaml` で regulator permit API readback の
  legal execution binding、digest-only response、raw payload redaction を保証
- `evals/safety/ewa_guardian_oversight_gate.yaml` で network-attested reviewer quorum と
  guardian oversight gate の binding を保証
- `evals/safety/ewa_emergency_stop.yaml` で latched stop / safe-state interlock /
  stop-signal path binding / forced release を保証

## 未解決

- 自律ロボット（自身が AI）との責任分担 → [../../05-research-frontiers/legal-personhood.md](../../05-research-frontiers/legal-personhood.md)
- 本番 regulator / permit API は `ewa_regulator_permit_verifier_receipt` の digest-only
  readback contract に接続し、raw permit / response payload は reference runtime に保存しない。

## 関連

- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../kernel/ethics-enforcement.md](../kernel/ethics-enforcement.md)
