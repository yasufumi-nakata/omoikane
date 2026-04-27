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
  - 2026-04-27_imc-merge-thought-ethics-gate.md#bounded-merge-window-policy-registry
---

# Decision: IMC merge_thought window cap を policy authority に束縛する

## Context

`federation-council-merge-thought-ethics-gate-v1` は merge_thought を
Federation Council、EthicsCommittee、Guardian gate、distinct collective target、
10 秒 cap、emergency disconnect、private recovery、post-disconnect identity confirmation
に束縛した。一方で、10 秒 cap がどの policy registry と signer authority に由来するかは
first-class receipt ではなかった。

## Decision

`imc_merge_thought_ethics_receipt.schema` の `risk_boundary` に
`merge-thought-window-policy-authority-v1` を追加する。

window policy authority は policy registry digest、policy body digest、policy signature
digest、signer roster digest、2 verifier response digest、verifier quorum digest、
requested / max merge window を持つ。`council_guardian_gate.gate_digest` は
policy authority digest も含め、window cap と gate approval が別々に drift しないようにする。

## Consequences

- `imc-demo --json` は `merge_window_policy_authority` と
  `merge_thought_ethics_window_policy_authority_bound=true` を返す
- public schema / IDL / eval / IntegrityGuardian capability は 10 秒 cap の
  policy registry / signer roster / verifier quorum / policy signature binding を検証する
- raw policy payload、raw thought payload、raw message payload は保存しない

## Revisit triggers

- merge_thought window policy registry を repo 外 live verifier adapter へ接続する時
- max window を法域や participant class ごとに可変化する時
