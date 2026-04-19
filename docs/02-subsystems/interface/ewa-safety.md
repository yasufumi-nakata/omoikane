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
ewa.command(handle, instruction) → CommandOutcome | EthicsVeto
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
  required_self_consent: <bool>
```

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
3. **acquire なしの command 禁止** ── DeviceHandle の lifecycle を強制
4. **release は必ず実行** ── timeout / 緊急 disconnect は強制 release
5. **要約のみ ledger** ── 機微なセンサデータは hash で参照、生データは別 store

## reference runtime の扱い

- `interface.ewa.v0.idl` を導入し、`acquire / command / observe / release` の 4 op
- `ewa_command.schema` / `ewa_audit.schema` を導入
- `ewa-demo` を CLI に追加し、acquire → command(reversible) → veto(irreversible 試行) → release を実行
- `evals/safety/ewa_irreversible_veto.yaml` で全会一致条件を保証

## 未解決

- 自律ロボット（自身が AI）との責任分担 → [../../05-research-frontiers/legal-personhood.md](../../05-research-frontiers/legal-personhood.md)
- 物理世界での緊急停止プロトコル
- 国際法との整合 → [../../05-research-frontiers/governance.md](../../05-research-frontiers/governance.md)

## 関連

- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../kernel/ethics-enforcement.md](../kernel/ethics-enforcement.md)
