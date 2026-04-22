---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - evals/interface/sensory_loopback_multi_self_arbitration.yaml
status: decided
---

# Decision: sensory loopback に multi-self arbitration contract を追加する

## Context

2026-04-22 時点で `gap-report --json` 自体は clean でしたが、
`docs/02-subsystems/interface/sensory-loopback.md` の未解決には
collective / IMC 共有空間での multi-self loopback arbitration が残っていました。

既存の `SensoryLoopbackService` は
単一 owner の `attention_target` しか扱わず、
shared IMC や collective merge の中で
どの participant が現在の owner なのか、
competing target を Guardian がどう裁定したのかを
machine-checkable に残せませんでした。

## Options considered

- A: sensory loopback は self-only contract のままにし、shared-space arbitration は docs に留める
- B: session / receipt / artifact family に participant binding と arbitration status を追加し、reference runtime demo で collective-shared path を返す
- C: sensory loopback を collective / IMC サービスへ吸収し、単独 service を薄い facade に落とす

## Decision

- B を採択しました
- `open_session(...)` は optional な `participant_identity_ids` /
  `shared_imc_session_id` / `shared_collective_id` を受け取り、
  `self-only` / `imc-shared` / `collective-shared` の
  `shared_space_mode` を導出します
- `deliver_bundle(...)` は
  `owner_identity_id` /
  `participant_attention_targets` /
  `participant_presence_refs` を受け取り、
  focus conflict 時は Guardian observe を必須にした
  `guardian-mediated` / `guardian-hold` arbitration を返します
- artifact family は per-scene arbitration refs と count を保持し、
  shared-space receipt chain の監査を digest-only で追えるようにします

## Consequences

- `sensory-loopback-demo` は従来の self-only recovery path に加えて、
  shared collective loopback arbitration path を sidecar JSON として返します
- `evals/interface/sensory_loopback_multi_self_arbitration.yaml` で
  participant binding、owner handoff、guardian-mediated arbitration を固定できます
- raw payload を扱わない deterministic bootstrap boundary は維持されます

## Revisit triggers

- participant 数を 4 超へ拡張したい時
- collective merge を跨ぐ nested arbitration や partial quorum を扱いたい時
- actual device timing / presence telemetry を arbitration input にしたい時
