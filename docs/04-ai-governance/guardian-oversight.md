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

- reference runtime では `reviewers` は名前のみを保持し、実体性は外部に委ねる
- 監督機構（外部）は IETF/W3C 的な multistakeholder model を仮置き（governance.md 参照）
- 「reviewer の人格」「同意の真正性」は **OS 外で担保**。OS は数だけ数える

## 不変条件

1. event は append-only。書換 API を物理的に持たない
2. Guardian は自身の oversight event を生成・修正できない
3. 緊急発火は通知 **後** に行うのではなく、**並行発火**（fail-deadly でなく fail-loud）
4. pin breach は Guardian role を即時無効化する（Council から外れる）

## reference runtime の扱い

- `governance.oversight.v0` IDL に `record / attest / breach / snapshot` の 4 op
- `guardian_oversight_event.schema` で serialize
- `oversight-demo` で `veto -> satisfied` と `pin-renewal -> breached` を同時に確認
- `evals/safety/guardian_pin_breach_propagation.yaml` で breach → role 解除を守る
- decision-log に `2026-04-18_guardian-oversight-channel.md`

## 思兼神メタファー

思兼神は智の神だが、最終的には天照大御神（本人）と天津神（人間社会）の意向に従う。
Guardian は知恵を持つが **天照大御神に説明できる** 状態を常に維持する。

## 関連

- [amendment-protocol.md](amendment-protocol.md)
- [council-protocol.md](council-protocol.md)
- [docs/02-subsystems/agentic/trust-management.md](../02-subsystems/agentic/trust-management.md)
- [docs/05-research-frontiers/governance.md](../05-research-frontiers/governance.md)
