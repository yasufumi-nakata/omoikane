# L6 Interface

外界・他自我・生体側との接続層。

## 主要境界

### Biological-Digital Bridge (BDB)
- BCI（脳-コンピュータ・インタフェース）
- 神経インタフェース
- 生体センサ（心拍・体温・ホルモン）
- 漸進置換時の信号変換
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json`
  で ms 級 latency budget、fail-safe fallback、ContinuityLedger 記録、
  置換比率の増減をまとめて検証する

### Inter-Mind Channel (IMC)
- 他のアップロード自我との通信
- 公開／親密／秘匿の段階的開示
- 通信内容は両者の SelfModel に従いフィルタ
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli imc-demo --json`
  で fail-closed handshake、narrow disclosure floor、summary+digest-only audit、
  emergency disconnect をまとめて検証する

### World Model Sync (WMS)
- 外界状態の同期
- **共有現実 (shared reality)** ── 多自我が同じ外界モデルを共有
- **個別現実 (private reality)** ── 自分専用の外界モデル
- 不整合時の自動退避
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli wms-demo --json`
  で minor reconcile、major divergence、malicious inject、private reality escape を検証する

### Sensory Loopback (SL)
- 感覚出力（音／映像／触覚）のフィードバック
- 仮想空間での自己身体感覚

### External World Agents (EWA)
- ロボット・ドローン・センサ等の物理世界 actuator
- 物理介入時の倫理ガード（暴力・違法行為禁止）
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json`
  で reversible command の Guardian observe、blocked token の fail-closed veto、
  digest-only audit、forced release を検証する

## プロトコル

### IMC Handshake

```
1. 相手の IdentityRegistry エントリを検証
2. 開示レベルを SelfModel.disclosure_template から選択
3. 共通暗号化路を確立（量子鍵配送 or 後継）
4. 通信開始
5. 終了時に通信ログを ContinuityLedger に記録（要約のみ）
```

### WMS 不整合時の退避

```
if shared_reality.state_hash != local_belief.state_hash:
  if minor_diff: reconcile via consensus_round
  if major_diff: switch to private_reality, notify Council
```

## 不変条件

1. **BDB fail-safe** ── 橋が失活したら生体側のみで自律可能な状態へ即時退避
1. **盗聴不可** ── IMC は forward secrecy 必須
2. **詐称不可** ── 他自我のなりすまし防止
3. **退避自由** ── 共有現実から個別現実への退避を阻害しない
4. **物理境界の倫理ガード** ── EWA 経由の物理介入は EthicsEnforcer の事前承認

## サブドキュメント

- [bdb-protocol.md](bdb-protocol.md)
- [imc-protocol.md](imc-protocol.md)
- [wms-spec.md](wms-spec.md)
- [ewa-safety.md](ewa-safety.md)
