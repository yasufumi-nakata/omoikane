# Sensory Loopback (SL)

L6 Interface のサブシステム。**視覚 / 聴覚 / 触覚の自己フィードバック**を
bounded に返し、仮想空間での自己身体感覚を安定化する。

## 役割

- `visual / auditory / haptic` の 2 以上の channel を束ねて自己フィードバックを返す
- `WMS` の `world_state_ref` と `body_anchor_ref` に束縛し、
  avatar body の drift を検出する
- artifact 本体は保持せず、`artifact_ref` と digest と summary のみを監査へ残す
- drift や latency overshoot 時は Guardian が safe baseline へ attenuate / hold する
- `QualiaBuffer` へは raw stream ではなく `qualia_binding_ref` だけを返し、
  surrogate tick と結び直す

## Reference Runtime の固定 profile

| 項目 | 固定値 |
|---|---|
| channels | `visual / auditory / haptic` |
| latency_budget_ms | `90.0` |
| attenuation_latency_ms | `140.0` |
| coherence_drift_threshold | `0.20` |
| hold_drift_threshold | `0.35` |
| body_schema_mode | `virtual-self-anchor-v1` |
| artifact_storage_policy | `artifact-digest+summary-ref-only` |
| qualia_binding_policy | `surrogate-tick-ref` |

reference runtime では raw retinal/audio/haptic stream は扱わず、
**artifact ref + digest + body coherence score** に限定した contract を固定する。

## API

```yaml
sensory_loopback.open_session:
  input:
    identity_id: <identity ref>
    world_state_ref: <wms state ref>
    body_anchor_ref: <avatar body anchor>
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
    body_coherence_score: <0.0..1.0>
    attention_target: <focus ref>
    guardian_observed: <bool>
    qualia_binding_ref: <qualia tick ref>
  output: sensory_loopback_receipt

sensory_loopback.stabilize:
  input:
    session_id: <loopback session>
    reason: <text>
    restored_body_anchor_ref: <avatar body anchor>
  output: sensory_loopback_receipt
```

## 判定規則

| 条件 | 出力 |
|---|---|
| latency <= 90ms かつ drift <= 0.20 | `delivery_status=delivered` |
| latency <= 140ms かつ drift <= 0.35 | `delivery_status=attenuate-to-safe-baseline` |
| それ以外 | `delivery_status=guardian-hold` |

degraded bundle は Guardian observe が無い限り reject する。

## 不変条件

1. **world anchor 必須** ── `world_state_ref` 未束縛の loopback session は作らない
2. **digest-only audit** ── ledger には raw sensory payload を保存しない
3. **guardian recovery 必須** ── `guardian-hold` からの再開は `stabilize` 経由のみ
4. **2 channel 以上** ── body-coherent delivery を名乗るには最低 2 modality が必要
5. **qualia は ref のみ** ── loopback receipt は surrogate tick 参照だけを返す

## reference runtime の扱い

- `interface.sensory_loopback.v0.idl` を追加し、
  `open_session / deliver_bundle / stabilize / snapshot` を定義
- `sensory_loopback_session.schema` /
  `sensory_loopback_receipt.schema` を追加
- `sensory-loopback-demo --json` で coherent delivery、
  guardian hold、stabilize 復帰を 1 シナリオで可視化
- `evals/interface/sensory_loopback_guard.yaml` で
  body coherence guard と qualia binding を固定

## 未解決

- raw retinal/audio/haptic stream の hardware-specific timing
- richer avatar body map と proprioceptive calibration
- collective / IMC 共有空間での multi-self loopback arbitration

## 関連

- [README.md](README.md)
- [wms-spec.md](wms-spec.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
