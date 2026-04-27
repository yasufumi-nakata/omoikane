---
date: 2026-04-27
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - specs/schemas/imc_merge_thought_ethics_receipt.schema
  - evals/interface/imc_merge_thought_ethics_gate.yaml
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - 2026-04-27_imc-merge-thought-window-policy-authority.md#repo-outside-live-verifier-adapter
---

# Decision: IMC merge_thought window policy を live verifier receipt に束縛する

## Context

`merge-thought-window-policy-authority-v1` は policy registry digest、signer roster
digest、verifier quorum digest、policy signature digest で 10 秒 cap の出所を固定した。
ただし verifier response は deterministic digest family のままで、repo 外 live verifier
adapter に差し替える前段の receipt が first-class ではなかった。

## Decision

`imc_merge_thought_ethics_receipt.schema` の
`risk_boundary.merge_window_policy_authority` に
`merge-thought-window-live-verifier-receipt-v1` receipt quorum を追加する。

live verifier receipt は HTTP JSON endpoint、verifier authority ref、jurisdiction、
network response digest、response signature digest、latency budget、raw payload redaction
を持つ。window policy authority digest と Council / Guardian gate digest は
live verifier quorum digest も含め、policy registry と gate approval が別々に drift
しないようにする。

## Consequences

- `imc-demo --json` は local live HTTP verifier bridge を probe し、2 verifier receipt を
  merge_thought ethics receipt に封入する
- public schema / IDL / eval / IntegrityGuardian capability は raw policy / verifier /
  response-signature payload を保存しないことを検証する
- unit test は live verifier network response digest の drift を receipt validation で検出する

## Revisit triggers

- live verifier endpoint を repo 外 production verifier network へ差し替える時
- window policy verifier quorum threshold を jurisdiction policy registry から取得する時
