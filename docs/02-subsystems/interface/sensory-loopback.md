# Sensory Loopback (SL)

L6 Interface のサブシステム。**視覚 / 聴覚 / 触覚の自己フィードバック**を
bounded に返し、仮想空間での自己身体感覚を安定化する。

## 役割

- `visual / auditory / haptic` の 2 以上の channel を束ねて自己フィードバックを返す
- `WMS` の `world_state_ref` と `body_anchor_ref` に束縛し、
  avatar body の drift を検出する
- `avatar_body_map_ref` と `proprioceptive_calibration_ref` により、
  canonical な body segment map と calibration snapshot を receipt/family へ束縛する
- BioData Transmitter の confidence gate は body-state latent 由来の補助 confidence としてのみ扱い、
  body-map calibration と Guardian hold / stabilization contract を置き換えない
- artifact 本体は保持せず、`artifact_ref` と digest と summary のみを監査へ残す
- coherent / guardian-hold / stabilize の複数 scene を
  bounded な artifact family として束ね、回復経路を digest-only で再監査できる
- drift や latency overshoot 時は Guardian が safe baseline へ attenuate / hold する
- `QualiaBuffer` へは raw stream ではなく `qualia_binding_ref` だけを返し、
  surrogate tick と結び直す
- bounded な collective / IMC 共有空間では
  `participant_identity_ids` / `shared_imc_session_id` / `shared_collective_id` を束縛し、
  competing `attention_target` を guardian-mediated arbitration で machine-checkable にする

## Reference Runtime の固定 profile

| 項目 | 固定値 |
|---|---|
| channels | `visual / auditory / haptic` |
| latency_budget_ms | `90.0` |
| attenuation_latency_ms | `140.0` |
| coherence_drift_threshold | `0.20` |
| hold_drift_threshold | `0.35` |
| body_schema_mode | `virtual-self-anchor-v1` |
| body_map_profile | `avatar-proprioceptive-map-v1` |
| proprioceptive_calibration_policy | `ref-bound-avatar-map-v1` |
| public_schema_contract_profile | `sensory-loopback-public-schema-contract-v1` |
| artifact_storage_policy | `artifact-digest+summary-ref-only` |
| qualia_binding_policy | `surrogate-tick-ref` |
| artifact_family_policy | `multi-scene-artifact-family-v1` |
| artifact_family_max_scenes | `4` |
| shared_space_modes | `self-only / imc-shared / collective-shared` |
| arbitration_policy | `guardian-mediated-multi-self-loopback-v1` |

reference runtime では raw retinal/audio/haptic payload は扱わず、
**artifact ref + digest + avatar body-map alignment** に限定した contract を固定する。

## API

```yaml
sensory_loopback.open_session:
  input:
    identity_id: <identity ref>
    world_state_ref: <wms state ref>
    body_anchor_ref: <avatar body anchor>
    avatar_body_map_ref: <canonical avatar body map ref>
    proprioceptive_calibration_ref: <latest calibration snapshot ref>
    participant_identity_ids: [<identity ref>, ...]
    shared_imc_session_id: <imc session ref>
    shared_collective_id: <collective ref>
    channels: [visual, auditory, haptic]
  output: sensory_loopback_session

sensory_loopback.deliver_bundle:
  input:
    session_id: <loopback session>
    scene_summary: <bounded text summary>
    artifact_refs:
      visual: <artifact ref>
      auditory: <artifact ref>
      haptic: <artifact ref>
    latency_ms: <float>
    body_map_alignment_ref: <alignment receipt ref>
    body_map_alignment:
      core: <0.0..1.0>
      left-hand: <0.0..1.0>
      right-hand: <0.0..1.0>
      stance: <0.0..1.0>
    attention_target: <focus ref>
    guardian_observed: <bool>
    qualia_binding_ref: <qualia tick ref>
    owner_identity_id: <current shared-space owner>
    participant_attention_targets:
      <identity ref>: <focus ref>
    participant_presence_refs:
      <identity ref>: <presence ref>
  output: sensory_loopback_receipt

sensory_loopback.stabilize:
  input:
    session_id: <loopback session>
    reason: <text>
    restored_body_anchor_ref: <avatar body anchor>
  output: sensory_loopback_receipt

sensory_loopback.capture_artifact_family:
  input:
    session_id: <loopback session>
    family_label: <bounded family label>
    receipts: [<receipt>, <receipt>, ...]
  output: sensory_loopback_artifact_family
```

## 判定規則

| 条件 | 出力 |
|---|---|
| latency <= 90ms かつ drift <= 0.20 | `delivery_status=delivered` |
| latency <= 140ms かつ drift <= 0.35 | `delivery_status=attenuate-to-safe-baseline` |
| それ以外 | `delivery_status=guardian-hold` |
| shared space で participant target が衝突 | `guardian_observed=true` のときのみ `arbitration_status=guardian-mediated or guardian-hold` |

degraded bundle は Guardian observe が無い限り reject する。

## 不変条件

1. **world anchor 必須** ── `world_state_ref` 未束縛の loopback session は作らない
2. **digest-only audit** ── ledger には raw sensory payload を保存しない
3. **guardian recovery 必須** ── `guardian-hold` からの再開は `stabilize` 経由のみ
4. **2 channel 以上** ── body-coherent delivery を名乗るには最低 2 modality が必要
5. **qualia は ref のみ** ── loopback receipt は surrogate tick 参照だけを返す
6. **artifact family は同一 session 内限定** ── multi-scene family は 2-4 receipt を同一 session に束縛する
7. **body map calibration 必須** ── session と receipt は `avatar_body_map_ref` / `proprioceptive_calibration_ref` / `body_map_alignment_ref` を必ず持つ
8. **shared arbitration は guardian mediation 必須** ── multi-self loopback では participant map を省略せず、競合 focus は Guardian observe 下でのみ反映する

## reference runtime の扱い

- `interface.sensory_loopback.v0.idl` を追加し、
  `open_session / deliver_bundle / stabilize / snapshot / capture_artifact_family / snapshot_artifact_family` を定義
- `sensory_loopback_session.schema` /
  `sensory_loopback_receipt.schema` /
  `sensory_loopback_artifact_family.schema` を追加
- `sensory-loopback-demo --json` で coherent delivery、
  guardian hold、stabilize 復帰、multi-scene artifact family capture を 1 シナリオで可視化
- 同じ demo 内で shared IMC / collective loopback session を開き、
  `shared-aligned` と `guardian-mediated` arbitration path を
  digest-only artifact family として可視化
- 同じ demo は `schema_contracts` manifest で self-only / shared の
  session、receipt、artifact family を public schema path へ束縛し、
  integration test が各 payload を schema に直接通す
- `evals/interface/sensory_loopback_guard.yaml` で
  body coherence guard、avatar body-map calibration binding、qualia binding を固定
- `evals/interface/sensory_loopback_artifact_family.yaml` で
  family scene 順序、guardian intervention 数、final session binding、
  body-map binding を固定
- `evals/interface/sensory_loopback_multi_self_arbitration.yaml` で
  participant binding、IMC/collective binding、owner handoff、
  guardian-mediated arbitration tracking を固定
- `evals/interface/sensory_loopback_public_schema_contract.yaml` で
  CLI demo の schema manifest と public schema validation を固定

## 未解決

- raw retinal/audio/haptic payload を actual capture pipeline へ接続する repo 外 adapter
- 4 participant を超える shared sensory field や hardware timing 連動の arbitration scale-out

## 関連

- [README.md](README.md)
- [wms-spec.md](wms-spec.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
