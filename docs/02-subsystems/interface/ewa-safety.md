# External World Agents (EWA) Safety

物理世界に作用する actuator（ロボット・ドローン・センサ）の安全規約。

## 操作の前提

1. 全 EWA 操作は EthicsEnforcer の事前承認を経る
2. 物理介入は **逆転可能性** で分類：
   - 完全可逆（センサ読み取りのみ）── 承認簡易
   - 部分的可逆（物体移動）── 承認標準
   - 不可逆（破壊・改変）── 承認厳格 + Council 召集

## 禁止行為

- 人間／他自我への暴力
- 違法行為
- 環境破壊
- 監視（同意なき）

## 操作 API

```
ewa.acquire(device_id) → DeviceHandle
ewa.command(handle, instruction) → ResultOrVeto
ewa.release(handle) → ()
```

`command` は EthicsEnforcer により veto されうる。
重大コマンドは Council 経由のみ。

## 監査

全 EWA 操作は EthicsLedger に記録。
法的調査時は管轄機関と協力可能。

## 未解決

- 自律ロボット（自身が AI）との責任分担
- 物理世界での緊急停止プロトコル
- 国際法との整合
