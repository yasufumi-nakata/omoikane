# Memory Replication Protocol

`MemoryCrystal` の冗長保管・差分転送・整合性検証の規約。

## 配置

```
[Primary]   ── 本人配下の主保管
[Mirror]    ── 別 substrate の同期コピー
[ColdStore] ── 長期保管（読み出し低速、改竄極小）
[Trustee]   ── 第三者保管（暗号化、本人鍵がないと開けない）
```

各 commit は最低 4 箇所に分散保管（PrimaryFailure → Mirror → ColdStore → Trustee）。

## 同期方式

- **Append**: 新 commit は即座に Primary → Mirror。ColdStore/Trustee は遅延 OK。
- **Verify**: 定期的にすべての保管先の Merkle ルートを比較。
- **Reconcile**: 不整合検出時は最新合意点まで rollback、Council へエスカレ。

## 暗号

- 内容は本人鍵で暗号化、メタは平文（保管側に内容が漏れない）
- 鍵は Shamir's secret sharing でさらに分散
- 鍵紛失は **同一性の死** に等しい → 鍵管理は最高優先度

## 差分転送

容量を抑えるため、commit 間 diff のみ転送。
- 内容 diff: encrypted blob
- 構造 diff: 平文 metadata
- reference runtime では compaction 後の `MemoryCrystalManifest` を metadata として運び、
  `source_event_ids` / `source_refs` を残して元イベントへの追跡性を失わない

## バックグラウンド整合性検査

- ランダムなブロックを取り出し、全保管先で hash 照合
- 不一致を検出したら Guardian へ即時通報

## Reference Runtime v0

reference runtime ではこの protocol を
`quad-store-memory-replication-v1` として bounded contract 化し、
`PYTHONPATH=src python3 -m omoikane.cli memory-replication-demo --json`
で次の 1 シナリオを確認する。

- `primary` / `mirror` / `coldstore` / `trustee` の fixed four-target placement
- `encrypted-content-plus-plaintext-metadata` による payload / metadata 分離
- random-block Merkle audit による全 target 比較
- `trustee` mismatch を `primary` / `mirror` / `coldstore` の latest consensus digest に戻して
  `Guardian alert + Council escalation + resync_required=true` へ束縛する bounded reconcile
- 本人が一時的に identity key を失った場合の `threshold-key-succession-guarded-recovery-v1`
  receipt を同じ session に束縛し、3-of-5 Shamir share、2 Guardian attestation、
  successor key digest、rotation ledger ref、JP-13 signer roster policy digest、
  identity-guardian + integrity-guardian signature digest に加え、JP-13 / SG-01 の
  multi-jurisdiction signer roster quorum digest と quorum threshold policy authority
  digest を保存する。ただし raw key / raw shard material / raw jurisdiction policy
  payload / raw quorum threshold policy payload / raw signer roster payload は保存しない
- `long-term-media-renewal-proof-v1` receipt を同じ session に束縛し、
  `coldstore` / `trustee` の long-term copy を renewed media proof、readback digest、
  migration attestation digest、3650 日 refresh interval、1000 年 target horizon へ固定する。
  さらに `long-term-media-renewal-cadence-policy-v1` receipt が identity cadence class、
  JP-13 / SG-01 jurisdiction cadence policy digest、target 別 refresh interval、
  effective refresh / revocation window を同じ proof set に束縛する。
  `long-term-media-renewal-refresh-window-v1` receipt は source proof set を
  current-not-revoked status、90 日 revocation check window、次回 refresh ref、
  stale / revoked proof fail-closed と cadence policy digest に束縛し、
  `long-term-media-renewal-registry-verifier-v1` が JP-13 / SG-01 の registry response
  digest、response signature digest、250ms timeout budget、quorum digest を
  source proof set に束縛する。さらに
  `long-term-media-renewal-registry-endpoint-certificate-lifecycle-v1` が各 registry
  endpoint の certificate fingerprint、chain digest、OCSP / revocation digest、
  renewal event、previous certificate retirement digest を registry response quorum と
  同じ source proof set へ束縛する。さらに
  `long-term-media-renewal-registry-endpoint-certificate-ct-log-readback-v1` /
  `long-term-media-renewal-registry-endpoint-certificate-ct-log-quorum-v1` /
  `long-term-media-renewal-registry-endpoint-certificate-sct-policy-authority-v1`
  により、CT-style readback、2-log quorum、SCT timestamp window、
  SCT policy authority を digest-only に束縛する。
  raw media payload / raw readback payload / raw cadence payload /
  raw revocation payload / raw refresh payload /
  raw registry payload / raw response payload / raw endpoint certificate payload /
  raw certificate freshness payload / raw certificate lifecycle payload /
  raw certificate CT log payload / raw SCT policy authority payload は保存しない

canonical schema:
[specs/schemas/memory_replication_session.schema](../../specs/schemas/memory_replication_session.schema)

IDL:
[specs/interfaces/mind.memory_replication.v0.idl](../../specs/interfaces/mind.memory_replication.v0.idl)

## 攻撃モデル

| 攻撃 | 対策 |
|---|---|
| 単一保管先の改竄 | 多数決で検出 |
| 鍵奪取 | Shamir 閾値以上を奪う必要、現実的に困難 |
| 全保管先同時破壊 | 地理／substrate 分散で確率を下げる |
| Trustee の悪意 | 内容は暗号化済、メタの除去のみ可能 |
| 量子攻撃 | PQC で対抗、定期更新 |

## 未解決

- 実物理媒体での 100-1000 年スケール耐久実証 → [docs/05-research-frontiers/long-term-storage.md](../05-research-frontiers/long-term-storage.md)
- 量子情報の冗長保管（no-cloning に抵触）
- repo 外 key ceremony / HSM / trustee network / signer roster authority / physical storage audit への実接続
