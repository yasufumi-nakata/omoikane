# Cognitive Audit Loop

L2 `QualiaBuffer`、L2 `SelfModelMonitor`、L3 `MetacognitionService`、
L4 `Council` を束ねる **bounded cognitive audit loop**。

目的は、認知系 primitive が guard 条件を超えた時に、
raw payload を露出せずに review を機械可読化することです。

## 固定ポリシー

| 項目 | 値 |
| --- | --- |
| policy_id | `cross-layer-cognitive-audit-v1` |
| allowed_layers | `L2 / L3 / L4` |
| qualia checkpoint category | `qualia-checkpoint` |
| audit category | `cognitive-audit` |
| divergence threshold | `0.35` |
| lucidity guard threshold | `0.65` |
| continuity pressure threshold | `0.75` |

## 入力

- `qualia_tick`
  - `tick_id`, `attention_target`, `lucidity`, `self_awareness`, `valence/arousal/clarity`
- `self_model_observation`
  - `abrupt_change`, `divergence`, `threshold`, active `values/goals/traits`
- `metacognition_report`
  - `reflection_mode`, `escalation_target`, `risk_posture`,
    `continuity_guard.guard_aligned`, `coherence_score`
- `qualia_checkpoint_ref`
  - ContinuityLedger 上の append-only entry ref

## 監査トリガ

- `abrupt-change`
- `observe-guard`
- `sandbox-notify`
- `low-lucidity`
- `high-continuity-pressure`

reference runtime では trigger を最大 4 件までに固定し、
`contain-and-review` のみ expedited session を許可します。
それ以外は standard session です。

## 出力

### `cognitive_audit_record`

- qualia / self-model / metacognition の digest-safe summary
- Council 向け `requested_action`
- `continuity_alignment`
  - `identity_matches`
  - `qualia_tick_matches_report`
  - `guard_consistent`
  - `threshold_exceeded`

### `cognitive_audit_resolution`

- `council_outcome`
- `follow_up_action`
  - `continue-monitoring`
  - `open-guardian-review`
  - `activate-containment`
  - `preserve-boundary`
  - `schedule-standard-session`
  - `escalate-to-human-governance`

### `cognitive_audit_governance_binding`

- local `cognitive_audit_resolution`
- optional Federation / Heritage `distributed_council_resolution`
- network-attested `guardian_oversight` reviewer binding
- `execution_gate`
  - `oversight-attested-local`
  - `federation-attested-review`
  - `heritage-veto-boundary`
  - `distributed-conflict-human-escalation`
- `final_follow_up_action`
  - local review action を preserve
  - Heritage veto 時は `preserve-boundary`
  - Federation approve と Heritage reject が衝突した時は `escalate-to-human-governance`

## 不変条件

1. qualia tick と metacognition source tick は同一 `tick_id` / `attention_target` を共有する
2. identity は qualia / self-model / metacognition 間で一致する
3. qualia checkpoint は ledger に append されてから audit record に束縛される
4. follow-up artifact は raw sensory embedding や private metacognition note を含まない
5. `abrupt_change` を含む監査は `continue-monitoring` で閉じない
6. `open-guardian-review` / `activate-containment` は network-bound reviewer receipt を持つ oversight event なしでは governance bind できない
7. Heritage `binding-rejected` returned result は local review action より優先して `preserve-boundary` に落とす
8. Federation `binding-approved` と Heritage `binding-rejected` が同時に来た時は human governance へ escalate する

## Reference Runtime

- `cognitive-audit-demo --json`
  - qualia checkpoint
  - abrupt self-model observation
  - metacognition guardian-review
  - Council approval
  - `cognitive.audit.resolved` ledger entry
- `cognitive-audit-governance-demo --json`
  - `cognitive.audit.resolved` を起点に reviewer verifier-network receipt を持つ oversight attestation
  - Federation returned result による review preserve
  - Heritage returned result による boundary preserve
  - Federation / Heritage conflict 時の human governance escalation
