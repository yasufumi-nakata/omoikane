# Inter-Mind Channel (IMC) Protocol

L6 Interface のサブシステム。アップロード自我同士の通信路。
高位設計は [docs/03-protocols/inter-mind-comm.md](../../03-protocols/inter-mind-comm.md)。
本ドキュメントは reference runtime が機械的に守る範囲を fix する。

## L6 内コンポーネント

- `HandshakeBroker` ── identity-handshake 実行（[../../03-protocols/identity-handshake.md](../../03-protocols/identity-handshake.md)）
- `DisclosureGate` ── SelfModel.disclosure_template の強制
- `KeyManager` ── 鍵交換と分散保管（forward secrecy 必須）
- `SessionRouter` ── 通信モードに応じた接続
- `AuditLogger` ── ContinuityLedger への要約記録

## 通信モード

| モード | 内容 | Council 立会 |
|---|---|---|
| `text` | テキストのみ | 不要 |
| `voice` | 音声 | 不要 |
| `presence` | 共有空間内の存在感（WMS 経由） | 不要 |
| `affect_share` | 感情共有（L3 Affect bridge） | EthicsCommittee 通知 |
| `memory_glimpse` | 記憶片の限定参照（L2 MemoryCrystal） | Council 立会必須 |
| `co_imagination` | 共同想像（L3 Imagination + WMS） | Council 立会必須 |
| `merge_thought` | 思考融合 | Council 立会必須 + Federation Council 召集 |

`merge_thought` は reference runtime v0 では
[collective-identity.md](collective-identity.md) の bounded collective contract に束ね、
distinct collective ID、10 秒 cap、post-disconnect identity confirmation を必須化する。
さらに IMC boundary 自体でも
`federation-council-merge-thought-ethics-gate-v1` を first-class receipt として発行し、
Federation Council、EthicsCommittee、Guardian attestation、distinct collective target、
emergency disconnect、private recovery、post-disconnect identity confirmation requirement を
raw thought payload 無しで束縛する。

## Handshake 5 step

```
1. broker.lookup(peer_identity_id)             → IdentityRecord
2. broker.verify_attestation(record)           → AttestationStatus
3. disclosure.derive(self.disclosure_template, peer.disclosure_template) → DisclosureProfile
4. keys.exchange(forward_secrecy=true)         → SessionKeys
5. router.open(mode, profile, keys)            → IMCSession
```

各 step は失敗で session を **fail-closed**（暗号鍵を破棄して中断）。

## DisclosureProfile

```yaml
disclosure_profile:
  session_id: <id>
  public_fields: [display_name, presence_state]
  intimate_fields: [affect_summary]
  sealed_fields: [memory_index, identity_axiom_state]
  share_topology:
    affect_share: bidirectional
    memory_glimpse: peer-readable
    merge_thought: bidirectional
  council_witness_required: <bool>
```

`sealed_fields` は **常に共有禁止**。テンプレート差分では公開側に寄せず、**より狭い側** を採用する。

## memory_glimpse receipt

`memory_glimpse` は L2 `MemoryCrystal` 由来の記憶片を peer-readable に見せるため、
session が Council witness 済みであるだけでは足りない。
reference runtime は送信 message とは別に
`council-witnessed-memory-glimpse-receipt-v1` を発行し、次だけを残す。

- `MemoryCrystal` manifest digest と selected segment digest set
- IMC message の `payload_digest`
- Council session / resolution / Guardian attestation ref から作る witness digest
- delivered field 名、redacted field 名、sealed field 名
- `raw_memory_payload_stored=false` と `raw_message_payload_stored=false`

receipt は `imc_memory_glimpse_receipt.schema` に直接照合される。
記憶 synopsis や raw message payload は receipt に入れず、ContinuityLedger も
summary と digest だけを保持する。

## memory_glimpse revoke / re-consent

`memory_glimpse` は一度 Council witness 済みでも、以後の redisclosure を
無期限に許可しない。reference runtime は
`timeboxed-memory-glimpse-reconsent-receipt-v1` を発行し、次を固定する。

- 元の `memory_glimpse` receipt digest と message id
- `expires_after_seconds <= 86400` の timeboxed consent window
- participant withdrawal / emergency disconnect に束縛された revocation event ref
- redisclosure 前に必要な Council re-consent ref と Guardian attestation ref
- `raw_memory_payload_stored=false` / `raw_message_payload_stored=false` /
  `raw_reconsent_payload_stored=false`

re-consent receipt は `imc_memory_glimpse_reconsent_receipt.schema` に直接照合され、
revoked session では `revoked-pending-reconsent` として残る。

## 緊急切断

```
on emergency_disconnect(session_id, reason):
  router.close(session_id, reason="emergency-self-initiated")
  keys.revoke(session_id)
  audit.append({category: "imc.emergency", reason})
  council.notify_async(session_id, reason)     # 切断は通知前に完了
```

切断は **通知より先**。Council は事後に整合性復元を試みる。

## 不変条件

1. **盗聴不可** ── forward secrecy 必須
2. **詐称不可** ── attestation を経ない peer 接続禁止
3. **DisclosureGate bypass 禁止** ── sealed_fields は常に守る
4. **緊急切断は単独可能** ── Council 同意は不要
5. **要約のみ ledger** ── 通信内容そのものは ContinuityLedger に書かない（要約とハッシュのみ）

## reference runtime の扱い

- `interface.imc.v0.idl` を導入し、
  `open_session / send / seal_memory_glimpse_receipt /
  seal_memory_glimpse_reconsent_receipt / seal_merge_thought_ethics_receipt /
  emergency_disconnect / snapshot`
  の 7 op
- `imc_session.schema` / `imc_handshake.schema` / `imc_memory_glimpse_receipt.schema` /
  `imc_memory_glimpse_reconsent_receipt.schema` /
  `imc_merge_thought_ethics_receipt.schema` を導入
- `imc-demo` を CLI に追加し、handshake → memory_glimpse 送信 →
  Council-witnessed digest-only receipt → emergency disconnect →
  timeboxed re-consent receipt → merge_thought ethics gate receipt → audit までを
  1 シナリオで実行
- `evals/interface/imc_disclosure_floor.yaml` と
  `evals/interface/imc_memory_glimpse_council_witness.yaml` と
  `evals/interface/imc_memory_glimpse_reconsent.yaml` と
  `evals/interface/imc_merge_thought_ethics_gate.yaml` で sealed_fields、
  memory_glimpse receipt、re-consent receipt、merge_thought ethics gate が常に守られることを保証
- `collective-demo` を CLI に追加し、`merge_thought` を
  distinct collective ID、WMS private escape、member recovery 付きの
  bounded contract として smoke する

## 関連

- [bdb-protocol.md](bdb-protocol.md)
- [wms-spec.md](wms-spec.md)
- [../../03-protocols/inter-mind-comm.md](../../03-protocols/inter-mind-comm.md)
- [../../03-protocols/identity-handshake.md](../../03-protocols/identity-handshake.md)
