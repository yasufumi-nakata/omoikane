---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/README.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - evals/interface/imc_disclosure_floor.yaml
status: decided
---

# Decision: IMC の disclosure floor と緊急切断 contract を reference runtime に固定する

## Context

`gap-report --json` は clean でしたが、reference runtime README には
L6 interface の残課題として IMC/EWA が残っていました。
特に IMC は protocol docs に handshaking、段階的 disclosure、緊急切断の
概念がありながら、runtime / CLI / eval / tests が存在せず、
「狭い disclosure template 側に寄せる」「sealed fields を絶対に出さない」
という安全境界がコードで検証されていませんでした。

## Options considered

- A: IMC は docs-only のまま維持し、BDB/WMS/EWA とまとめて後回しにする
- B: peer attestation、forward secrecy、disclosure floor、summary-only audit、
  emergency disconnect に限定した bounded IMC contract を追加する
- C: collective registration、merge-thought、distributed council handoff まで v0 に含める

## Decision

**B** を採択。

## Consequences

- `interface.imc.v0` を追加し、`open_session / send / emergency_disconnect / snapshot`
  の 4 op を固定する
- `imc_handshake.schema`、`imc_message.schema`、`imc_session.schema` を追加し、
  memory_glimpse 系の高親密度モードでは council witness を必須にする
- `imc-demo` を追加し、handshake、disclosure redaction、summary+digest-only audit、
  unilateral disconnect をまとめて確認する
- EWA と collective / merge-thought の広域設計は引き続き future work に残す

## Revisit triggers

- collective を独立 identity として登録する bounded contract を追加したくなった時
- affect bridge や WMS presence と IMC session を cross-layer で束ねたくなった時
- merge-thought を `external-pending` 以上へ具体化する時
