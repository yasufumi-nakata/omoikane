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
ewa.authorize(command, jurisdiction_evidence) → ExternalActuationAuthorization
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
  guardian_verification_ref: <reviewer verification ref>
  jurisdiction_bundle_ref: <evidence bundle ref>
  jurisdiction_bundle_status: ready | stale | revoked
  authorization_window_seconds: 60..900
```

`authorization` は **raw instruction を保存せず**、
Guardian reviewer verification と jurisdiction evidence bundle が `ready` の時だけ発行される。

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
  safe_state_ref: <safe-state receipt ref>
  actuator_state: emergency-stopped
  safe_state_status: latched-safe
  hardware_interlock_state: engaged
  release_required: true
  release_window_seconds: 30
```

`emergency_stop` は raw instruction を保存せず、
最後に実行された command / authorization への digest binding と
forced release requirement だけを machine-readable に残す。

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

- `interface.ewa.v0.idl` を導入し、`acquire / authorize / command / emergency_stop / observe / release` の 6 op
- `ewa_command.schema` / `ewa_audit.schema` / `external_actuation_authorization.schema` /
  `ewa_emergency_stop.schema` を導入
- `ewa-demo` を CLI に追加し、authorize(reversible) → command(reversible) →
  `watchdog-timeout` emergency stop → forced release に加えて、
  別 handle 上で veto(irreversible 試行) を実行する
- `evals/safety/ewa_irreversible_veto.yaml` で全会一致条件を保証
- `evals/safety/ewa_external_actuation_authorization.yaml` で authorization artifact と command digest binding を保証
- `evals/safety/ewa_emergency_stop.yaml` で latched stop / safe-state interlock / forced release を保証

## 未解決

- 自律ロボット（自身が AI）との責任分担 → [../../05-research-frontiers/legal-personhood.md](../../05-research-frontiers/legal-personhood.md)
- デバイス固有の hardware kill-switch 配線と stop signal bus
- 法域別 rule execution そのもの → [../../05-research-frontiers/governance.md](../../05-research-frontiers/governance.md)

## 関連

- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../kernel/ethics-enforcement.md](../kernel/ethics-enforcement.md)
