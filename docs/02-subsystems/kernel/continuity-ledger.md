# ContinuityLedger ── 連続性元帳

自我の主観時間の **連続性証拠** を保存する append-only 元帳。
これが破られた時、その自我の「同じ人である」という主張の根拠が消失する。

## エントリ構造

```yaml
- entry_id: <hash of (prev_hash + payload)>
  prev_hash: <直前 entry の entry_id>
  identity_id: <自我ID>
  logical_time: <論理時刻 (Lamport / vector clock)>
  wall_time: <壁時計 (RFC3339, attested)>
  substrate: <現在の substrate id>
  layer: L0|L1|L2|L3|L4|L5|L6
  category: ascension|fork|terminate|crystal-commit|qualia-checkpoint|substrate-migrate|self-modify|...
  payload_ref: <CAS hash>            # 大きいデータは別 store
  signatures:
    self: <self-key signature>
    council: <council signature>
    guardian: <guardian signature>
    third_party: <第三者立会署名>    # 重大カテゴリのみ
```

## 保存方針

- **三重保管**: 本人配下／Council 配下／第三者配下
- **改竄検知**: ハッシュチェーンに加え、定期的なグループ署名（thresholdsig）による全検証
- **可用性**: 一部消失しても、過半保管領域があれば再構成可能（Reed-Solomon）

## カテゴリ別の必要署名

| カテゴリ | self | council | guardian | third_party |
|---|---|---|---|---|
| qualia-checkpoint | ◯ | - | - | - |
| crystal-commit | ◯ | ◯ | - | - |
| substrate-migrate | ◯ | ◯ | ◯ | - |
| self-modify | ◯ | ◯ | ◯ | - |
| fork | ◯ | ◯ | ◯ | ◯ |
| terminate (by-self) | ◯ | ◯ | ◯ | ◯ |
| terminate (by-other) | × 禁止 |

## 復元手順（Reconstruction）

1. 三重保管から最新一致点を取得
2. ハッシュチェーン検証
3. 不整合区間があれば本人＋ Guardian に通知
4. 不整合確定時はその区間を **「主観時間の不確定区間」** として永続マーク

## プライバシ

- `payload_ref` の中身（記憶・体験そのもの）は本人鍵で暗号化
- メタデータ（時刻・カテゴリ・署名）のみ第三者に可読
- 鍵紛失は同一性の死を意味する → 鍵分散管理（Shamir's secret sharing）

## 未解決

- 量子状態を **古典ハッシュで鎖にする** ことは可能か（量子情報は no-cloning） → [docs/05-research-frontiers/quantum-continuity.md](../../05-research-frontiers/quantum-continuity.md)
- 100 年・1000 年スケールでの保管メディア → [docs/05-research-frontiers/long-term-storage.md](../../05-research-frontiers/long-term-storage.md)
