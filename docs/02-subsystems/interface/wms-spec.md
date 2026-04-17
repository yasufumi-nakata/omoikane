# World Model Sync (WMS) Spec

外界モデル（共有現実 or 個別現実）の同期仕様。

## モード

- **shared_reality**: 複数自我が同じ世界モデルを共有
- **private_reality**: 自分専用の世界モデル
- **mixed**: 一部共有、一部個別

## データ

```yaml
WorldState:
  state_id: <hash>
  participants: [<identity_id>...]
  spatial_layout: <opaque>     # シーングラフ
  objects: [...]
  physics_rules: <ref>
  time_rate: <multiplier>      # 主観時間の流れ方
```

## 不整合時の戦略

```
if shared_reality.state_hash != local_belief.state_hash:
  case minor_diff:
    consensus_round → reconcile
  case major_diff:
    notify Council
    offer 'switch to private_reality' to user
  case malicious_inject:
    Guardian veto + audit
```

## time_rate

異なる substrate は異なる速度で動く可能性。共有現実では time_rate を合意する必要がある。
合意できないときは個別現実へ退避。

## 物理規則

shared_reality は通常「現実の物理に近い」が、合意で変更可能（無重力空間・夢空間等）。
変更は Council 承認が必要（暴力性・不可逆性のチェック）。

## 未解決

- substrate 間の time_rate 同期手法
- 大人数 shared_reality でのスケーリング
- 物理法則改変時の知覚適応
