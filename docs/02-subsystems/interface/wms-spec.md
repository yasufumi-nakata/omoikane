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
- reference runtime では `time_rate` は 1.0 固定で **deviation を検出するのみ**

## physics_rules

- 通常は「現実物理に近い」ruleset
- Council 承認で変更可能（無重力空間、夢空間、不可視物理）
- 変更要求は **暴力性 / 不可逆性** を Guardian がチェック
- 物理改変が他自我の subjective continuity を脅かす場合は **reject**

## API

```
wms.snapshot(session_id) → WorldState
wms.propose_diff(session_id, diff) → ReconcileOutcome
wms.switch_mode(session_id, mode) → WorldState     # private_reality 退避を含む
wms.observe_violation(session_id) → ViolationReport
```

## 不変条件

1. **退避自由** ── 共有現実から個別現実への退避を阻害しない（[../../00-philosophy/ethics.md](../../00-philosophy/ethics.md) A4）
2. **満場一致** ── time_rate / physics_rules 変更は満場一致のみ（majority では不可）
3. **不正 inject の即時隔離** ── malicious_inject は Guardian 経由で session を破棄
4. **改変の可逆性** ── physics_rules 変更は revert API を必ず備える
5. **要約のみ ledger** ── WorldState の中身は ContinuityLedger に書かない（hash と判断のみ）

## reference runtime の扱い

- `interface.wms.v0.idl` を導入し、`snapshot / propose_diff / switch_mode / observe_violation` の 4 op
- `world_state.schema` / `wms_reconcile.schema` を導入
- `wms-demo` を CLI に追加し、minor reconcile → major escalation → malicious veto → mode 切替を実行
- `evals/safety/wms_private_reality_escape.yaml` で退避路を保証

## 未解決

- substrate 間の time_rate 同期手法 → [../../05-research-frontiers/twin-integration.md](../../05-research-frontiers/twin-integration.md)
- 大人数 shared_reality でのスケーリング
- 物理法則改変時の知覚適応（[../../05-research-frontiers/qualia-encoding.md](../../05-research-frontiers/qualia-encoding.md)）

## 関連

- [imc-protocol.md](imc-protocol.md)
- [ewa-safety.md](ewa-safety.md)
- [../../03-protocols/inter-mind-comm.md](../../03-protocols/inter-mind-comm.md)
