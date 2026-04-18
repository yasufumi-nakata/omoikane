# Biological-Digital Bridge (BDB) Protocol

生体神経系とデジタル基板の境界仕様。
Method A（漸進置換）の実装に必須。

reference runtime では `interface.bdb.v0` / `bdb-demo` として
bounded viability だけを固定する。

## Reference Runtime v0

- `latency_budget_ms=5.0`
- `failover_budget_ms=1.0`
- `codec_id=analog-spike-event-v0`
- 神経修飾物質は `acetylcholine / dopamine / serotonin / norepinephrine`
  の coarse proxy channel に限定
- 置換比率は `0.05` 刻みで増減可能
- bridge 失活時は `bio-autonomous-fallback` に遷移し、
  `effective_replacement_ratio=0.0` / `stim_output_enabled=false` を強制
- 各 cycle・ratio change・fallback は ContinuityLedger 互換の event ref を保持

`PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json` は、
1 回の閉ループ cycle、置換比率の増加と減少、fail-safe fallback を
まとめて実行する smoke path である。

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

## v0 Operations

- `open_session(identity_id, replacement_ratio, bio_signal_channels, neuromodulator_channels)`
- `transduce_cycle(session_id, spike_channels, neuromodulators, stimulus_targets)`
- `adjust_replacement_ratio(session_id, new_ratio, rationale)`
- `fail_safe_fallback(session_id, reason)`
- `snapshot(session_id)`

## なお未解決

- 神経修飾物質（アセチルコリン・ドーパミン等）の正確な再現
- グリア細胞の役割
- 大規模並列での同期
- 本当にニューロン単位まで置換できる最小ステップ
- 主観連続性そのものの測定

したがって、reference runtime が解いたのは **境界 contract の実装可能性**
までであり、神経科学的・主観的な完全性ではない。

→ [docs/05-research-frontiers/gradual-replacement.md](../../05-research-frontiers/gradual-replacement.md)
