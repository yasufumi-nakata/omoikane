# Imagination

L3 Cognitive Services の反実仮想 scene 生成面。reference runtime では
**bounded counterfactual scene + IMC/WMS handoff gate** だけを固定し、
創造性や主観的想像体験の成立そのものは主張しない。

## 役割

- `Attention` の focus と `Affect` の guard を受けて 1 つの bounded scene を構成する
- primary backend 障害時に fallback backend へ **一度だけ** failover する
- `co_imagination` を open にしてよい条件を council witness と affect guard で固定する
- failover 時は scene を `private_reality` / `private-sandbox` へ縮退させる
- ledger には `imagination_shift` の要約のみ残し、scene 全文や raw payload は書かない

## reference runtime profile

| 項目 | 固定値 |
|---|---|
| policy_id | `bounded-counterfactual-handoff-v1` |
| primary | `counterfactual_scene_v1` |
| fallback | `continuity_scene_guard_v1` |
| max_scene_objects | `5` |
| requires_council_witness_for_co_imagination | `true` |
| degrade_to_private_reality | `true` |
| failover_mode | `single-switch` |

## API

```yaml
imagination.compose_scene:
  input:
    tick_id: <int>
    summary: <text>
    seed_prompt: safe-bridge rehearsal
    attention_focus: bridge-rehearsal
    affect_guard: nominal | observe | sandbox-notify
    world_mode_preference: shared_reality | private_reality | mixed
    continuity_pressure: <0.0..1.0>
    council_witnessed: <bool>
    memory_cues:
      - cue_id: peer-witness
        motif: council-witness
        weight: 0.24
  output: imagination_scene
```

`imagination_scene` は `scene_summary`, `scene_objects`, `counterfactual_axes`,
`handoff.mode`, `handoff.wms_mode`, `handoff.co_imagination_ready`,
`continuity_guard` を持つ。ledger に残す `imagination_shift` は
`scene_ref`, `selected_backend`, `handoff_mode`, `wms_mode`,
`affect_guard`, `co_imagination_ready`, `guard_aligned` に絞る。

## 不変条件

1. primary backend が落ちても fallback は 1 回のみ
2. `co_imagination` handoff は `affect_guard=nominal` かつ `council_witnessed=true` の時だけ許可
3. `observe` / `sandbox-notify` guard 時は `private_reality` へ縮退する
4. failover 中の imagination は `co_imagination_ready=true` を返さない
5. scene の共有 payload は IMC/WMS 側へ handoff し、ContinuityLedger には要約のみ残す

## reference runtime の扱い

- `cognitive.imagination.v0.idl` を追加し、`compose_scene / validate_scene / validate_shift` を定義
- `imagination_scene.schema` / `imagination_shift.schema` を追加
- `imagination-demo --json` で nominal baseline の `co_imagination` handoff と、
  failover 後の `private-sandbox` への縮退を一度に可視化
- `evals/cognitive/imagination_failover.yaml` で degraded failover と private fallback を固定

## 関連

- [README.md](README.md)
- [attention.md](attention.md)
- [volition.md](volition.md)
- [../interface/imc-protocol.md](../interface/imc-protocol.md)
- [../interface/wms-spec.md](../interface/wms-spec.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
