# World Model Sync (WMS) Spec

L6 Interface のサブシステム。**外界モデル**（共有現実 / 個別現実）の同期。

## モード

- `shared_reality` ── 複数自我が同じ世界モデルを共有
- `private_reality` ── 自分専用の世界モデル
- `mixed` ── 一部共有、一部個別（領域単位で切替）

## WorldState スキーマ

```yaml
world_state:
  state_id: <hash>
  participants: [<identity_id>...]
  spatial_layout: <opaque hash, scenegraph>
  objects: [...]
  physics_rules_ref: <ruleset id>
  time_rate: <multiplier>          # 主観時間の流れ方
  authority: <consensus | local | broker>
  recorded_at: <iso8601>
```

reference runtime では `objects` と `spatial_layout` は不透明 hash として扱い、
**整合性検査と退避判定のみ** を行う。

## 不整合 4 段階の退避戦略（deterministic）

| 区分 | 条件 | アクション |
|---|---|---|
| `none` | hash 一致 | nop |
| `minor_diff` | hash 不一致だが影響範囲 < 5% | `consensus_round` で reconcile |
| `major_diff` | 影響範囲 5% 以上 | Council 通知 + private_reality 切替を本人に提示 |
| `malicious_inject` | 認証されない参加者からの差分 | Guardian veto + audit |

**reference runtime は影響範囲を schema 上で `affected_object_ratio` (0..1) として受理し、
0.05 を境界に minor / major を切る**。

## time_rate

- 異なる substrate では主観時間の進み方が異なりうる
- shared_reality 参加者は session 開始時に `time_rate` を **満場一致** で合意
- 合意できない場合は private_reality へ退避（shared_reality に **強制ロックイン禁止**）
- reference runtime では `time_rate` は 1.0 固定で、requested deviation を
  `fixed-time-rate-private-escape-v1` の digest-bound evidence として残し、
  WorldState を変更せず private_reality 退避を提示する
- requested deviation の evidence は `subjective-time-attestation-transport-v1`
  receipt を participant 全員分要求し、IMC handshake、message digest、
  time_rate attestation subject digest、forward secrecy を束縛してから
  `participant-subjective-time-attestation-set-v1` digest にまとめる

## physics_rules

- 通常は「現実物理に近い」ruleset
- Council 承認で変更可能（無重力空間、夢空間、不可視物理）
- 変更要求は **暴力性 / 不可逆性** を Guardian がチェック
- 物理改変が他自我の subjective continuity を脅かす場合は **reject**
- reference runtime では満場一致 approval を静的な participant id だけで扱わず、
  `imc-participant-approval-transport-v1` receipt で IMC handshake、
  message digest、approval subject digest、forward secrecy を束縛する
- 大人数 shared_reality の collection は `bounded-wms-approval-collection-v1`
  receipt で participant order、receipt digest set、bounded batch digest を固定し、
  complete collection だけを apply へ渡す
- distributed Council transport への fan-out は
  `distributed-council-approval-fanout-v1` receipt で complete collection digest、
  Federation envelope digest、authenticated receipt digest、participant ごとの
  approval result digest を ordered set として束縛する
- partial outage は `bounded-distributed-approval-fanout-retry-v1` で
  `max_retry_attempts=2` / `retry_window_ms=1500` に制限し、
  retry の recovery result digest と transport receipt digest が
  最終 fan-out result に一致した時だけ `fanout_status=complete` に戻す
- reference runtime の external engine adapter 境界は
  `digest-bound-wms-engine-transaction-log-v1` receipt で固定する。
  time_rate escape evidence、approval collection、distributed fan-out、
  physics_rules apply、revert の各 source artifact digest を ordered committed
  transaction entry に束縛する。さらに adapter signer key ref と
  `signed-wms-engine-adapter-log-v1` signature digest が transaction digest set、
  source artifact digest set、state-transition digest、current WMS state digest を
  署名対象として束縛し、raw engine payload / raw world-state body /
  raw adapter signature material は保存しない
- same adapter の route 境界は
  `distributed-transport-bound-wms-engine-adapter-route-v1` receipt で固定する。
  completed engine transaction log digest、ordered transaction entry digest set、
  authenticated non-loopback authority-route trace digest、cross-host remote host ref、
  OS observer tuple / host-binding digest を同じ digest-only receipt に束縛し、
  raw engine payload / raw route payload / packet body は保存しない
- real remote authority に近い partial outage recovery は
  `bounded-remote-authority-adaptive-retry-budget-v1` receipt で固定する。
  `signed-jurisdiction-rate-limit-retry-budget-v1` により
  remote jurisdiction、jurisdiction-specific rate limit ref、signer key ref、
  rate-limit digest、authority signature digest を route-health observation と
  schedule entry の両方へ複写する。さらに
  `registry-bound-authority-retry-slo-v1` により jurisdiction policy registry
  digest と authority SLO snapshot digest を束縛し、schedule は
  `registry-slo-derived-retry-schedule-v1` として fixed backoff、jurisdiction
  limit、registry/SLO 由来 limit の全てを満たす場合だけ `retry` になる。
  さらに `base_retry_after_ms=250` /
  `exponential_multiplier=2` / `total_retry_budget_ms=1500` の schedule entry、
  engine transaction log の `approval_fanout_bound` entry を同じ fan-out digest に束縛し、
  raw remote authority transcript は保存しない

## API

```
wms.snapshot(session_id) → WorldState
wms.propose_diff(session_id, diff, time_rate_attestation_receipts) → ReconcileOutcome
wms.collect_approval_transport_receipts(session_id, receipts) → ApprovalCollectionReceipt
wms.collect_distributed_approval_fanout(session_id, collection, transport_results, retry_attempts) → DistributedApprovalFanoutReceipt
wms.bind_engine_transaction_log(session_id, entries, engine_adapter_key_ref) → EngineTransactionLogReceipt
wms.bind_engine_route_trace(session_id, engine_log, authority_route_trace) → EngineRouteBindingReceipt
wms.bind_remote_authority_retry_budget(session_id, fanout, engine_log, route_health) → RemoteAuthorityRetryBudgetReceipt
wms.switch_mode(session_id, mode) → WorldState     # private_reality 退避を含む
wms.propose_physics_rules_change(session_id, change) → PhysicsRulesChangeReceipt
wms.revert_physics_rules_change(session_id, change_id) → PhysicsRulesChangeReceipt
wms.observe_violation(session_id) → ViolationReport
```

## 不変条件

1. **退避自由** ── 共有現実から個別現実への退避を阻害しない（[../../00-philosophy/ethics.md](../../00-philosophy/ethics.md) A4）
2. **満場一致** ── time_rate / physics_rules 変更は満場一致のみ（majority では不可）
3. **不正 inject の即時隔離** ── malicious_inject は Guardian 経由で session を破棄
4. **改変の可逆性** ── physics_rules 変更は revert API を必ず備え、rollback token と Guardian attestation を receipt に残す
5. **要約のみ ledger** ── WorldState の中身は ContinuityLedger に書かない（hash と判断のみ）

## reference runtime の扱い

- `interface.wms.v0.idl` は `snapshot / propose_diff / switch_mode / observe_violation` に加え、
  `propose_physics_rules_change / revert_physics_rules_change` を固定する
- `world_state.schema` / `wms_reconcile.schema` /
  `wms_approval_collection_receipt.schema` /
  `wms_distributed_approval_fanout_receipt.schema` /
  `wms_engine_transaction_log.schema` /
  `wms_engine_route_binding_receipt.schema` /
  `wms_engine_capture_binding_receipt.schema` /
  `wms_remote_authority_retry_budget_receipt.schema` /
  `wms_time_rate_attestation_receipt.schema` /
  `wms_physics_rules_change_receipt.schema` /
  `wms_participant_approval_transport_receipt.schema` を導入
- `wms-demo` を CLI に追加し、minor reconcile → major escalation →
  participant subjective-time attested time_rate deviation の fixed-time-rate private escape →
  3 participant の IMC transport-bound approval collection →
  partial outage retry を含む distributed Council transport fan-out →
  unanimous physics_rules change → rollback-token revert → engine transaction log →
  engine route binding → engine packet capture binding →
  signed jurisdiction-aware remote authority retry budget → malicious veto → mode 切替を実行
- `evals/interface/wms_private_reality_escape.yaml` と
  `evals/interface/wms_time_rate_deviation_escape.yaml` /
  `evals/interface/wms_time_rate_attestation_transport.yaml` /
  `evals/interface/wms_physics_rules_revert.yaml` /
  `evals/interface/wms_participant_approval_transport.yaml` /
  `evals/interface/wms_approval_collection_scaling.yaml` /
  `evals/interface/wms_distributed_approval_fanout.yaml` /
  `evals/interface/wms_distributed_approval_fanout_retry.yaml` で退避路、
  time_rate deviation escape、participant subjective-time attestation の live transport binding、
  physics_rules 可逆性、participant approval の live transport binding、
  ordered batch collection、distributed Council transport fan-out、
  partial outage retry recovery を保証
- `evals/interface/wms_engine_transaction_log.yaml` で external WMS engine adapter
  transaction log が ordered committed entry、source artifact digest set、
  state transition digest、adapter signature digest、payload redaction flag を持つことを保証
- `evals/interface/wms_engine_route_binding.yaml` で completed engine transaction log が
  authenticated cross-host distributed transport authority-route trace、OS observer digest、
  route binding ref set と raw payload 無しで束縛されることを保証
- `evals/interface/wms_engine_capture_binding.yaml` で completed engine route binding が
  verified packet-capture export、delegated privileged capture acquisition、route ref set、
  readback / artifact digest、broker lease / filter digest と raw packet body 無しで
  束縛されることを保証
- `evals/interface/wms_remote_authority_retry_budget.yaml` で recovered fan-out retry が
  signed jurisdiction-specific rate limit digest、authority signature digest、
  jurisdiction policy registry digest、authority SLO snapshot digest、
  route-health observation、registry/SLO-derived fixed exponential backoff schedule、engine transaction log
  digest に束縛され、raw remote authority transcript を保存しないことを保証

## 未解決

- substrate 間の time_rate 同期手法 → [../../05-research-frontiers/twin-integration.md](../../05-research-frontiers/twin-integration.md)
- 物理法則改変時の知覚適応（[../../05-research-frontiers/qualia-encoding.md](../../05-research-frontiers/qualia-encoding.md)）

## 関連

- [imc-protocol.md](imc-protocol.md)
- [ewa-safety.md](ewa-safety.md)
- [../../03-protocols/inter-mind-comm.md](../../03-protocols/inter-mind-comm.md)
