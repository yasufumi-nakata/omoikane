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

`oversight-demo` は minimum machine-checkable surface として
次の live-proof surrogate verification snapshot を保持する。

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
  network_receipt: null
```

- attestation は `credential_verification.status=verified` かつ
  `jurisdiction_bundle.status=ready` の reviewer にだけ許可する
- `valid_until` は reviewer identity proof の有効期限を超えられない
- raw challenge payload や legal package 本文は repo に保存せず、
  digest と ref のみを保持する

## verifier network receipt

`oversight-network-demo` は fixed endpoint registry に対して
reviewer verification を actual verifier network receipt として materialize する。

```yaml
guardian_verifier_network_receipt:
  receipt_id: verifier-network-receipt-...
  reviewer_id: human-reviewer-network-001
  verifier_endpoint: verifier://guardian-oversight.jp
  verifier_ref: verifier://guardian-oversight.jp/reviewer-alpha
  jurisdiction: JP-13
  transport_profile: reviewer-live-proof-bridge-v1
  network_profile_id: guardian-reviewer-remote-attestation-v1
  challenge_ref: challenge://...
  challenge_digest: sha256:...
  authority_chain_ref: authority://guardian-oversight.jp/reviewer-attestation
  trust_root_ref: root://guardian-oversight.jp/reviewer-live-pki
  trust_root_digest: sha256:guardian-oversight-jp-reviewer-live-pki-v1
  transport_exchange:
    exchange_id: verifier-transport-exchange-...
    request_payload_ref: sealed://guardian-oversight/.../transport-request/...
    request_payload_digest: <sha256>
    response_payload_ref: sealed://guardian-oversight/.../transport-response/...
    response_payload_digest: <sha256>
    request_size_bytes: <int>
    response_size_bytes: <int>
  freshness_window_seconds: 900
  observed_latency_ms: 143.9
  receipt_status: verified
  recorded_at: <iso8601>
  digest: <sha256>
```

- verifier endpoint は fixed registry に存在しなければ fail-closed
- reviewer jurisdiction は endpoint 側の supported jurisdiction に含まれなければ reject
- `transport_exchange` は request / response payload 自体ではなく
  sealed ref と digest、byte count を保持し、raw transport body は repo 外に留める
- attestation event は必要に応じて `network_receipt_id / authority_chain_ref /
  trust_root_ref / trust_root_digest / transport_exchange_id / transport_exchange_digest`
  を immutable binding として保持する
- raw network transcript や credential payload 本文は repo に保存せず、
  sealed payload ref / payload digest / root ref / authority chain ref のみを残す

## jurisdiction legal execution

reviewer verification は verifier snapshot と jurisdiction bundle だけで止まらず、
attestation 前に 1 件の deterministic legal execution receipt まで materialize する。

```yaml
guardian_jurisdiction_legal_execution:
  execution_id: legal-execution-...
  reviewer_id: human-reviewer-network-001
  verification_id: reviewer-verification-...
  jurisdiction: JP-13
  transport_profile: reviewer-live-proof-bridge-v1
  execution_profile_id: guardian-jurisdiction-legal-execution-v1
  execution_scope: reviewer-attestation-preflight
  policy_ref: policy://guardian-oversight/jp-13/reviewer-attestation/v1
  policy_digest: <sha256>
  notice_authority_ref: authority://guardian-oversight.jp/legal-desk
  liability_mode: joint
  legal_ack_ref: legal://oversight-network/reviewer-alpha/v1
  escalation_contact: mailto:oversight-network-alpha@example.invalid
  jurisdiction_bundle_ref: legal://jp-13/guardian-oversight/v1
  network_receipt_id: verifier-network-receipt-...
  authority_chain_ref: authority://guardian-oversight.jp/reviewer-attestation
  trust_root_ref: root://guardian-oversight.jp/reviewer-live-pki
  executed_controls:
    - control_type: bundle-ready-check
    - control_type: liability-ack-bind
    - control_type: scope-manifest-bind
    - control_type: escalation-contact-bind
    - control_type: notice-authority-bind
  execution_status: executed
  digest: <sha256>
```

- legal execution は fixed jurisdiction policy registry から `policy_ref` と
  `notice_authority_ref` を選び、reviewer scope / liability / escalation contact を
  ready bundle に束縛する
- `verify_reviewer` / `verify_reviewer_from_network` は
  `credential_verification.legal_execution` を必須にし、
  attestation は `execution_status=executed` の receipt が無ければ fail-closed
- reviewer binding は `legal_execution_id / legal_execution_digest / legal_policy_ref` を
  immutable に保持し、jurisdiction-specific legal execution を event 側にも焼き付ける
- `cognitive_audit_governance_binding` は reviewer binding の `jurisdiction` /
  `jurisdiction_bundle_ref` / `legal_policy_ref` / `legal_execution_id` を束ね、
  JP-13 / US-CA など 2 法域以上の reviewer quorum を満たす時だけ governance bind する
- 同じ binding は Federation / Heritage returned result を
  `distributed-council-verdict-signature-binding-v1` で包み、
  signed payload digest / signature digest / signer ref だけを保持して、
  raw signature payload や participant credential body は保存しない
- `interface.ewa.v0` は reviewer binding の `verification_id / verifier_ref /
  network_receipt_id / authority_chain_ref / trust_root_ref / legal_execution_id` を
  `ewa_guardian_oversight_gate` に compile し、physical actuation authorization の前段 gate として再利用する
- raw legal package 本文や regulator transcript は repo に保存せず、
  policy ref / digest / notice authority / execution control digests のみを残す

## 不変条件

1. event は append-only。書換 API を物理的に持たない
2. Guardian は自身の oversight event を生成・修正できない
3. 緊急発火は通知 **後** に行うのではなく、**並行発火**（fail-deadly でなく fail-loud）
4. pin breach は Guardian role を即時無効化する（Council から外れる）
5. reviewer proof binding は attestation 後に書換えず、reviewer revoke 後も過去 event の binding を保持する

## reference runtime の扱い

- `governance.oversight.v0` IDL に
  `register_reviewer / verify_reviewer / verify_reviewer_from_network / record / attest / revoke_reviewer / breach / snapshot`
  の 8 op
- `guardian_reviewer_record.schema`、`guardian_reviewer_verification.schema`、
  `guardian_jurisdiction_legal_execution.schema`、
  `guardian_verifier_network_receipt.schema`、`guardian_verifier_transport_exchange.schema`、
  `guardian_jurisdiction_evidence_bundle.schema`、
  `guardian_oversight_event.schema` で serialize
- `oversight-demo` で reviewer 登録、live verification、`veto -> satisfied`、
  jurisdiction legal execution binding、scope mismatch reject、`pin-renewal -> breached` を同時に確認
- `oversight-network-demo` で verifier endpoint 解決、trust root binding、
  authority chain binding、transport exchange digest binding、jurisdiction legal execution binding、
  network-backed `veto -> satisfied` を確認
- `evals/safety/guardian_pin_breach_propagation.yaml` で breach → role 解除を守る
- `evals/safety/guardian_reviewer_attestation_contract.yaml` で proof binding と liability scope enforcement を守る
- `evals/safety/guardian_reviewer_live_verification.yaml` で verifier snapshot と jurisdiction bundle binding を守る
- `evals/safety/guardian_jurisdiction_legal_execution.yaml` で policy provenance と control completeness を守る
- `evals/safety/guardian_reviewer_verifier_network.yaml` で verifier endpoint / authority chain / trust root binding を守る
- decision-log に `2026-04-18_guardian-oversight-channel.md` と
  `2026-04-20_guardian-reviewer-verifier-network.md`、
  `2026-04-22_guardian-jurisdiction-legal-execution.md`

## 思兼神メタファー

思兼神は智の神だが、最終的には天照大御神（本人）と天津神（人間社会）の意向に従う。
Guardian は知恵を持つが **天照大御神に説明できる** 状態を常に維持する。

## 関連

- [amendment-protocol.md](amendment-protocol.md)
- [council-protocol.md](council-protocol.md)
- [docs/02-subsystems/agentic/trust-management.md](../02-subsystems/agentic/trust-management.md)
- [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)
