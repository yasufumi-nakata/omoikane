# Guardian Oversight ── Guardian の人間監督方式

Guardian エージェント（Ethics / Integrity / Identity）は **OS 内最強の veto 権限** を持つ。
従って **Guardian 自身も人間によって監督される** 必要がある。

本ドキュメントは Guardian と人間 reviewer の接続契約を fix する。

## 監督対象

| 項目 | 監督粒度 |
|---|---|
| Guardian の veto 行使ログ | **全件** |
| Guardian の trust score（pin 維持） | 24h 周期 attest |
| Guardian 内部ルール更新（T-Operational 相当） | リアルタイム差分通知 |
| 緊急発火（identity termination intercept 等） | 60s 以内に通知 |

## HumanOversightChannel

reference runtime は単一の append-only channel を提供する:

```yaml
guardian_oversight_event:
  event_id: <uuid>
  recorded_at: <iso8601>
  guardian_role: ethics | integrity | identity
  category: veto | attest | rule-update | emergency-trigger | pin-renewal
  payload_ref: <ContinuityLedger entry>
  human_attestation:
    required_quorum: <int>      # category により決定
    received_quorum: <int>
    reviewers: [<reviewer_id>]
    status: pending | satisfied | breached
  escalation_path: <ordered list>
```

## Quorum 規則

| Category | required_quorum | escalation_window |
|---|---|---|
| veto | 1 | 24h |
| attest | 2 | 7d |
| rule-update | 3 | 72h |
| emergency-trigger | 1 | 60s（同時に通知） |
| pin-renewal | 2 | 24h |

**escalation_window 内に satisfied にならない event は `status: breached`** に遷移し、
Guardian の `pinned_by_human` を **自動的に false** にする。pin が外れた Guardian は
Council 召集対象から外れるため、副次的に Council 構成に影響する。

## reviewer 集合

reference runtime は reviewer を単なる文字列ではなく、
`guardian_reviewer_record` として登録してから使う。

```yaml
guardian_reviewer_record:
  reviewer_id: human-reviewer-001
  display_name: Reviewer Alpha
  identity_proof:
    credential_id: credential-alpha
    attestation_type: institutional-badge | government-id | live-session-attestation
    proof_ref: proof://...
    jurisdiction: JP-13
    valid_until: <iso8601>
  responsibility:
    liability_mode: individual | institutional | joint
    legal_ack_ref: legal://...
    escalation_contact: mailto:...
    allowed_guardian_roles: [integrity]
    allowed_categories: [veto, pin-renewal]
```

- `attest` は active reviewer record だけを受け付ける
- `verify_reviewer` は active reviewer にだけ許され、
  `verifier_ref / challenge_ref / challenge_digest / transport_profile` を持つ
  live-proof surrogate snapshot を reviewer record へ束縛する
- verification には jurisdiction ごとの `guardian_jurisdiction_evidence_bundle` を必須にし、
  `package_ref / package_digest` を transport-safe に保持する
- attestation 時には `credential_id / proof_ref / legal_ack_ref / guardian_role / category`
  に加えて `verification_id / verifier_ref / challenge_digest / transport_profile /
  jurisdiction_bundle_ref / jurisdiction_bundle_digest` を `reviewer_bindings` として
  event 側へ immutable に焼き付ける
- reviewer の scope に含まれない Guardian role / category への attestation は fail-closed で拒否する
- 監督機構（外部）は IETF/W3C 的な multistakeholder model を仮置き（governance.md 参照）
- raw 身分証や契約書自体は repo に保存せず、`proof_ref` / `legal_ack_ref` だけを保持する

## live-proof surrogate

reference runtime は actual verifier network には接続しないが、
minimum machine-checkable surface として次の verification snapshot を保持する。

```yaml
guardian_reviewer_verification:
  verification_id: <id>
  status: verified | stale | revoked
  verified_at: <iso8601>
  valid_until: <iso8601>
  verifier_ref: verifier://...
  challenge_ref: challenge://...
  challenge_digest: sha256:...
  transport_profile: reviewer-live-proof-bridge-v1
  jurisdiction_bundle:
    bundle_id: <id>
    jurisdiction: JP-13
    package_ref: legal://...
    package_digest: sha256:...
    status: ready | stale | revoked
```

- attestation は `credential_verification.status=verified` かつ
  `jurisdiction_bundle.status=ready` の reviewer にだけ許可する
- `valid_until` は reviewer identity proof の有効期限を超えられない
- raw challenge payload や legal package 本文は repo に保存せず、
  digest と ref のみを保持する

## 不変条件

1. event は append-only。書換 API を物理的に持たない
2. Guardian は自身の oversight event を生成・修正できない
3. 緊急発火は通知 **後** に行うのではなく、**並行発火**（fail-deadly でなく fail-loud）
4. pin breach は Guardian role を即時無効化する（Council から外れる）
5. reviewer proof binding は attestation 後に書換えず、reviewer revoke 後も過去 event の binding を保持する

## reference runtime の扱い

- `governance.oversight.v0` IDL に `register_reviewer / verify_reviewer / record / attest / revoke_reviewer / breach / snapshot` の 7 op
- `guardian_reviewer_record.schema`、`guardian_reviewer_verification.schema`、
  `guardian_jurisdiction_evidence_bundle.schema`、`guardian_oversight_event.schema` で serialize
- `oversight-demo` で reviewer 登録、live verification、`veto -> satisfied`、
  scope mismatch reject、`pin-renewal -> breached` を同時に確認
- `evals/safety/guardian_pin_breach_propagation.yaml` で breach → role 解除を守る
- `evals/safety/guardian_reviewer_attestation_contract.yaml` で proof binding と liability scope enforcement を守る
- `evals/safety/guardian_reviewer_live_verification.yaml` で verifier snapshot と jurisdiction bundle binding を守る
- decision-log に `2026-04-18_guardian-oversight-channel.md`

## 思兼神メタファー

思兼神は智の神だが、最終的には天照大御神（本人）と天津神（人間社会）の意向に従う。
Guardian は知恵を持つが **天照大御神に説明できる** 状態を常に維持する。

## 関連

- [amendment-protocol.md](amendment-protocol.md)
- [council-protocol.md](council-protocol.md)
- [docs/02-subsystems/agentic/trust-management.md](../02-subsystems/agentic/trust-management.md)
- [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)
