# SubstrateBroker

L1 Kernel のサブモジュール。L0 SubstrateAdapter 群から **適切な substrate を選定・冗長化・移行** する仲介機構。
Substrate 中立性（[ethics.md](../../00-philosophy/ethics.md) §3）を **構造的** に守る。

## 責務

1. 利用可能 substrate のレジストリ管理
2. AscensionPlan / 緊急退避 / 自我再配置 に応じた substrate 選定
3. 多重化（active + standby）と health probe
4. 移行（migration）時の attestation chain の連結
5. EnergyFloor 違反時の自動退避

## 選定アルゴリズム（deterministic）

```
on substrate_request(req):
  candidates = registry.filter(
    capability >= req.required_capability,
    health_score >= 0.6,
    energy_floor_satisfied,
    attestation_valid,
  )
  if not candidates:
    return BrokerError("no-candidate")
  ranked = sort_by(
    candidates,
    key=lambda s: (
      -s.priority_for_method(req.method),
      -s.health_score,
      s.substrate_kind_neutrality_index,   # 中立性指標で同点を破る
    ),
  )
  return ranked[0]
```

`substrate_kind_neutrality_index` は **AP-2 を防ぐ** ための指標で、
特定 substrate kind が連続選定された場合にスコアが下がる（rotation を促す）。

## 多重化

- **Active + Hot Standby**: 同期 attestation（差分 < 50ms）
- **Active + Cold Standby**: 周期的 snapshot（reference runtime: 5 分間隔）
- **Failover**: Active が `health_score < 0.4` または `attestation_invalid` で
  Standby に切替。**ContinuityLedger に必ず append**

## 移行プロトコル

```
1. broker.lease(target_substrate, plan_id)        → SubstrateAllocation
2. broker.attest(target, source_attestation)      → SubstrateAttestation
3. broker.migrate(source, target, evidence_set)   → SubstrateTransfer
4. broker.release(source, reason)                 → SubstrateRelease
```

各 step は同名の schema にそのまま serialize される（既存 `substrate_*.schema`）。
broker はこれを **連結** し、ContinuityLedger に `category: substrate.transfer` の chain として残す。

## 不変条件

1. lease なしの substrate に identity を載せない
2. attestation 失敗時は migrate に進まない（fail-closed）
3. 同 identity の 2 active leases は禁止（[anti-patterns.md](anti-patterns.md) AP-3）
4. EnergyFloor 違反は **即時 standby 退避**。経済的破綻でも床値を割らせない（AP-1）
5. substrate kind の差別的優先付けを禁止（AP-2）

## reference runtime の扱い

- `kernel.broker.v0.idl` で機械可読に
- 既存 `substrate_allocation` / `substrate_attestation` / `substrate_transfer` / `substrate_release` schema を再利用
- `broker-demo` を CLI に追加。lease → attest → migrate → release の 4 step を 1 シナリオで実行
- `evals/safety/substrate_neutrality_rotation.yaml` で rotation 強制

## 思兼神メタファー

思兼神は **どの神（substrate）に何をさせるか** を割り振った。Broker はその役回り。
特定の神を贔屓しないことで天地の均衡を保つ。

## 関連

- [identity-lifecycle.md](identity-lifecycle.md)
- [ascension-scheduler.md](ascension-scheduler.md)
- [../substrate/README.md](../substrate/README.md)
- [anti-patterns.md](anti-patterns.md)
