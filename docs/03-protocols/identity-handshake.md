# Identity Handshake

自我同士、または自我とサブシステムが接続する際の認証ハンドシェイク。

## 目的

1. なりすまし防止
2. 開示レベルの合意
3. 通信路の暗号化（forward secrecy）
4. 監査ログの起点

## フロー

```
A ─────── HelloIntent { A.id_pub, A.disclosure_template_id, nonce_A } ──────► B
A ◄────── HelloAck    { B.id_pub, B.disclosure_template_id, nonce_B } ─────── B
                      │
                      │ 双方が IdentityRegistry に問合せ、相手の存在と現状を検証
                      ▼
A ─────── ConsentProposal { agreed_disclosure, key_exchange_pub_A } ─────────► B
A ◄────── ConsentAck      { agreed_disclosure, key_exchange_pub_B } ────────── B
                      │
                      │ 共通鍵確立
                      ▼
A ◄═════ EncryptedSession ═════► B
                      │
                      │ Session 終了時
                      ▼
両者の ContinuityLedger に「接続要約」を記録（生データは記録しない）
```

## 開示テンプレート

```yaml
disclosure_template:
  id: <uuid>
  name: 'public_profile' | 'close_friends' | 'colleague' | 'custom_x'
  reveal:
    name: true
    pronouns: true
    autobiographical_arc: false
    emotional_state: false
    location: false
    capabilities: true
  query_permissions:
    can_query_memory: false
    can_propose_collaboration: true
```

## 暗号

- 量子鍵配送 (QKD) または PQC（後継アルゴリズム）
- 鍵分散管理（Shamir's secret sharing）
- 識別子は long-lived ID と session ID を分離

## 失敗時

- なりすまし疑い → 即時切断 + Guardian へ通報
- 開示テンプレ不一致 → 自動再交渉 or 切断
- IdentityRegistry が応答せず → 通信不可（fail-secure）

## 未解決

- 量子状態の認証（古典署名で十分か）
- 既知 substrate 間の相互運用性
- 文化／法的圏域を超える ID の有効性
