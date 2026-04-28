# ContinuityLedger ── 連続性元帳

自我の主観時間の **連続性証拠** を保存する append-only 元帳。
これが破られた時、その自我の「同じ人である」という主張の根拠が消失する。

## エントリ構造

```yaml
- entry_id: <same as entry_hash in the reference runtime>
  entry_hash: <sha256(canonical_json(signable fields))>
  prev_hash: <直前 entry の entry_id>
  identity_id: <自我ID>
  logical_time: <論理時刻 (Lamport / vector clock)>
  wall_time: <壁時計 (RFC3339, attested)>
  substrate: <現在の substrate id>
  layer: L0|L1|L2|L3|L4|L5|L6
  category: ascension|attestation|fork|terminate|crystal-commit|semantic-projection|memory-edit|energy-budget|procedural-preview|connectome-snapshot|qualia-checkpoint|cognitive-audit|substrate-migrate|substrate-release|self-modify|selfctor-gap-report-scan|ethics-veto|ethics-escalate|cognitive-failover|guardian-oversight
  event_type: <詳細イベント名。例: council.patch.approved>
  payload_ref: <CAS hash>            # 大きいデータは別 store
  chain_algorithm: sha256
  signature_algorithm: hmac-sha256   # reference runtime の暫定 profile
  signatures:
    self: <self-key signature>
    council: <council signature>
    guardian: <guardian signature>
    third_party: <第三者立会署名>    # 重大カテゴリのみ
```

## 暫定 chain profile（2026-04-18）

reference runtime では、未解決だったチェーン形式を次で暫定固定する。

- canonicalization: `canonical-json-v1`（キー順固定 JSON）
- entry hash: `sha256`
- genesis hash: `GENESIS:sha256`
- payload ref: `cas://sha256/<payload-digest>`
- signature algorithm: `hmac-sha256`

`hmac-sha256` を選んだ理由は、標準ライブラリのみで deterministic に生成・検証でき、
CI/automation で profile を壊さず回せるためである。これは **reference runtime の暫定選定** であり、
公開検証可能な実運用署名は将来の governance/crypto 決定で差し替える。

## 保存方針

- **三重保管**: 本人配下／Council 配下／第三者配下
- **改竄検知**: ハッシュチェーンに加え、定期的なグループ署名（thresholdsig）による全検証
- **可用性**: 一部消失しても、過半保管領域があれば再構成可能（Reed-Solomon）

## 公開検証 bundle（2026-04-24）

reference runtime では `continuity-public-verification-key-management-v1` を追加し、
`continuity-demo --json` が次を返す。

- ledger head、entry count、ledger verification digest
- role ごとの verifier key ref、key digest、verification scope を持つ key roster
- entry ごとの required / present role、signature digest、verifier key ref
- `raw_key_material_exposed=false` と `raw_signature_payload_exposed=false`

この bundle は `hmac-sha256` の秘密鍵や raw signature payload を公開しない。
第三者・Integrity Guardian・将来の外部 verifier は、まず digest-bound な roster と
ledger head の一致を確認し、その後に実運用署名方式へ差し替える。
これにより「公開検証可能な署名方式へいつ移行するか」という保留を、
reference runtime 上では key roster / digest contract として先に固定する。

## カテゴリ別の必要署名

| カテゴリ | self | council | guardian | third_party |
|---|---|---|---|---|
| qualia-checkpoint | ◯ | - | - | - |
| crystal-commit | ◯ | ◯ | - | - |
| semantic-projection | ◯ | ◯ | - | - |
| memory-edit | ◯ | - | ◯ | - |
| energy-budget | ◯ | - | ◯ | - |
| procedural-preview | ◯ | ◯ | - | - |
| connectome-snapshot | ◯ | - | ◯ | - |
| substrate-migrate | ◯ | ◯ | ◯ | - |
| substrate-release | - | - | ◯ | - |
| self-modify | ◯ | ◯ | ◯ | - |
| selfctor-gap-report-scan | ◯ | - | ◯ | - |
| fork | ◯ | ◯ | ◯ | ◯ |
| terminate (by-self) | ◯ | ◯ | ◯ | ◯ |
| attestation | - | - | ◯ | - |
| cognitive-failover | - | - | ◯ | - |
| guardian-oversight | - | - | - | ◯ |
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

## なお残る未解決

- 量子状態を **古典ハッシュで鎖にする** ことは可能か（量子情報は no-cloning） → [docs/05-research-frontiers/quantum-continuity.md](../../05-research-frontiers/quantum-continuity.md)
- 100 年・1000 年スケールでの保管メディア → [docs/05-research-frontiers/long-term-storage.md](../../05-research-frontiers/long-term-storage.md)
