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

- 100-1000 年スケールの保管メディア → [docs/05-research-frontiers/long-term-storage.md](../05-research-frontiers/long-term-storage.md)
- 量子情報の冗長保管（no-cloning に抵触）
- repo 外 key ceremony / HSM / trustee network / signer roster authority への実接続
