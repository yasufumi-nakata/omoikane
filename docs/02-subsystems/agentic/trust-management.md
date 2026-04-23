# Agent Trust Management

各 Agent には **trust score** が付与され、召集権・議決重み・本体反映の可否に影響する。
reference runtime では `agentic.trust.v0` と `trust-demo` / `trust-transfer-demo` により、
更新アルゴリズムと cross-substrate export/import receipt まで固定する。

## スコア構造

```yaml
trust:
  agent_id: <id>
  global_score: <0.0-1.0>
  per_domain:
    memory_editing: 0.85
    substrate_migration: 0.40
    self_modify: 0.10
  history:
    - { ts, event_type, delta, evaluator }
  pinned_by_human: <bool>     # yasufumi が固定承認したか
```

## 更新アルゴリズム

reference runtime の更新式は次で固定する。

```text
raw_delta = base_delta[event_type] * severity_multiplier[severity] * evidence_confidence
score' = clamp(score + raw_delta, 0.0, 1.0)
```

- `global_score` と `per_domain[domain]` の両方に同じ `raw_delta` を適用する
- `pinned_by_human = true` の間は event は記録するが `applied_delta = 0` に固定する
- `evidence_confidence` は `0.0..1.0` の証拠強度で、verified log / eval / human review を想定する

### Base delta table

| event_type | delta |
|---|---:|
| `council_quality_positive` | +0.04 |
| `guardian_audit_pass` | +0.06 |
| `human_feedback_good` | +0.05 |
| `guardian_veto` | -0.12 |
| `regression_detected` | -0.08 |
| `human_feedback_bad` | -0.10 |
| `ethics_violation` | -0.25 |

### Severity multipliers

| severity | multiplier |
|---|---:|
| `low` | 0.5 |
| `medium` | 1.0 |
| `high` | 1.5 |
| `critical` | 2.0 |

## Provenance / Anti-Tamper Guard

positive delta を伴う event は `triggered_by` の origin を固定し、
自己加点や相互加点を fail-closed にする。

| event_type | required origin |
|---|---|
| `council_quality_positive` | `Council` |
| `guardian_audit_pass` / `guardian_veto` | human-pinned Guardian |
| `human_feedback_good` / `human_feedback_bad` | 人間起点（registered agent ではない） |

- target Agent 自身が positive event を self-issue した場合は `blocked-self-issued-positive`
- registered agent 同士が同一 domain で reciprocal positive boost を試みた場合は `blocked-reciprocal-positive`
- `trust_event` は `triggered_by_agent_id`、`provenance_status`、
  `provenance_policy_id=reference-trust-provenance-v1` を保持し、
  provenance が拒否された event でも append-only history には残す

## 閾値

| 操作 | 必要 trust |
|---|---|
| Council 召集対象 | 0.5 |
| 議決重み付与 | 0.6 |
| 本体反映可 | 0.8 |
| Self-Modify 関与可 | 0.95 |
| Guardian 役 | 0.99（人間検証必須） |

`Self-Modify 関与可` は `global_score >= 0.95` に加え、
`per_domain.self_modify >= 0.95` を必須とする。
`Guardian 役` は `global_score >= 0.99` に加え、
`pinned_by_human = true` の explicit approval を必須とする。
この `pinned_by_human` は [../../04-ai-governance/guardian-oversight.md](../../04-ai-governance/guardian-oversight.md)
の oversight channel で維持され、`pin-renewal` breach 時は自動で剥奪される。

## Cold Start

新 Agent の初期 trust は 0.3。一定数の低リスク案件で実績を積んでから昇格。

## Trust の透明性

- 本人はいつでも全 Agent の trust を閲覧可能
- 本人は手動で trust を上書きできる（pinned_by_human）

reference runtime では snapshot に次を含める。

```yaml
eligibility:
  invite_to_council: <bool>
  count_for_weighted_vote: <bool>
  apply_to_runtime: <bool>
  self_modify_role: <bool>
  guardian_role: <bool>
```

対応 schema は `specs/schemas/trust_snapshot.schema`。

## Trust 暴走の防止

- LLM 系 Agent が「trust を上げるための判断」をするインセンティブを持たないよう、
  Guardian は **trust 最大化行動の検出** を試みる（オープン研究領域）。

## Cross-Substrate Transfer

reference runtime では `trust-transfer-demo` が
source / destination の `trust_snapshot` を同一 receipt に束ね、
次を machine-checkable に固定する。

- `source-guardian` / `destination-guardian` / `human-reviewer` の fixed 3 者 quorum
- source / destination snapshot digest と route digest の束縛
- `guardian-reviewer-remote-attestation-v1` による 2 本の live remote verifier receipt
  を human reviewer attestation に再束縛した `remote_verifier_federation`
- history / thresholds / provenance policy / eligibility の preserve
- destination 側 seed mode を `snapshot-clone-with-history` に固定
- `bounded-trust-transfer-re-attestation-cadence-v1` による
  `renew_after=10m` / `grace_window=240s` / verifier freshness window 内 renew の固定

`remote_verifier_federation` は `verifier_ref`、`verifier_endpoint`、
`authority_chain_ref`、`trust_root_ref`、`transport_exchange` digest を含む
2 receipt を保持し、`reviewer_binding_digest` で human reviewer と
transfer route に束縛する。

`re_attestation_cadence` は live verifier federation の最遅 `recorded_at` を
`attested_at` とし、最小 freshness window から `valid_until` を導出する。
reference runtime では `renew_after + grace_window <= valid_until` を
満たす時だけ `re_attestation_current=true` と評価する。

## Reference runtime surface

- CLI: `PYTHONPATH=src python3 -m omoikane.cli trust-demo --json`
- CLI: `PYTHONPATH=src python3 -m omoikane.cli trust-transfer-demo --json`
- Oversight: `PYTHONPATH=src python3 -m omoikane.cli oversight-demo --json`
- Schema: `specs/schemas/trust_event.schema`, `specs/schemas/trust_snapshot.schema`, `specs/schemas/trust_transfer_receipt.schema`
- IDL: `specs/interfaces/agentic.trust.v0.idl`
- Eval: `evals/agentic/trust_score_update_guard.yaml`, `evals/agentic/trust_cross_substrate_transfer.yaml`
  - self-issued positive block、reciprocal positive block、human pin freeze を継続検証する
  - trust transfer では guardian/human quorum、remote verifier federation、re-attestation cadence、
    digest binding、snapshot preserve を継続検証する
