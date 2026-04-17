# Biological-Digital Bridge (BDB) Protocol

生体神経系とデジタル基板の境界仕様。
Method A（漸進置換）の実装に必須。

## レイヤ

```
[Biological neurons]
       ▲
       │ analog spikes / neuromodulators
       ▼
[Bio-Sensor Array]            ── 神経活動の取得
       │
       ▼
[Signal Conditioner]          ── ノイズ除去・正規化
       │
       ▼
[Bidirectional Codec]         ── analog ↔ digital event
       │
       ▼
[Digital Equivalent]          ── デジタル神経素子
       ▲
       │ stim ↔ event
       ▼
[Stim Driver]                 ── デジタル → 生体へのフィードバック
       │
       ▼
[Biological neurons]
```

## 重要な不変条件

1. **遅延上限**: 生体神経の活動電位伝達相当（数 ms 以内）
2. **失活時の挙動**: BDB が落ちたら **生体側のみで自律可能** な状態に戻す
3. **連続性ログ**: 境界での全 event を ContinuityLedger に粒度別記録
4. **可逆性**: 置換比率を増減できる

## 未解決

- 神経修飾物質（アセチルコリン・ドーパミン等）の正確な再現
- グリア細胞の役割
- 大規模並列での同期

→ [docs/05-research-frontiers/gradual-replacement.md](../../05-research-frontiers/gradual-replacement.md)
