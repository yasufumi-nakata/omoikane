# Inter-Mind Channel (IMC) Protocol

詳細は [docs/03-protocols/inter-mind-comm.md](../../03-protocols/inter-mind-comm.md) を参照。
本ドキュメントは L6 サブシステム視点での補足。

## L6 内のコンポーネント

- `HandshakeBroker` ── identity-handshake の実行
- `DisclosureGate` ── 開示テンプレートの強制
- `KeyManager` ── 鍵交換と分散保管
- `SessionRouter` ── 通信モードに応じた接続
- `AuditLogger` ── ContinuityLedger への要約記録

## 通信モード別の経路

```
text/voice            → SessionRouter → encrypted stream
presence              → SessionRouter → WMS で共有空間
affect_share          → SessionRouter + L3 Affect 接続
memory_glimpse        → SessionRouter + L2 MemoryCrystal 一時参照
co_imagination        → SessionRouter + L3 Imagination + WMS
merge_thought         → SessionRouter + L3 全接続 (Council 立会必須)
```

## 緊急停止

任意モードで本人の意思により即時切断可能。切断後の整合性復元は L4 Council が試みる。
