---
date: 2026-04-21
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/identity-lifecycle.md
  - docs/02-subsystems/kernel/README.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/kernel.identity.v0.idl
  - specs/schemas/identity_record.schema
  - evals/identity-fidelity/identity_pause_resume_contract.yaml
status: decided
---

# Decision: IdentityRegistry に bounded pause/resume contract を追加する

## Context

`gap-report --json` は clean でしたが、
`docs/02-subsystems/kernel/identity-lifecycle.md` は
`Active -> Paused -> Active / Terminated` を定義していた一方で、
`kernel.identity.v0.idl`、`identity_record.schema`、`IdentityRegistry`
実装は `create / fork / terminate` と `active / terminated` だけで止まっていました。

さらに `specs/catalog.yaml` には `identity_record.schema` 自体が未収載で、
この不整合は scanner にも拾われませんでした。

## Options considered

- A: pause/resume は docs-only のまま維持し、IdentityRegistry は create/fork/terminate だけに留める
- B: `pause / resume` を IDL・schema・runtime・CLI demo・eval・tests・catalog まで昇格し、latest pause cycle を machine-readable に固定する
- C: `Paused` の法的人格や Failed-Ascension trauma handling まで同時に制度化する

## Decision

Option B を採択します。

## Consequences

- `kernel.identity.v0` は `pause / resume` を first-class operation として持つ
- `identity_record.pause_state` は最新 1 回分の pause/resume cycle を保持し、
  `pause_authority / pause_reason / council_resolution_ref / resumed_at / resume_self_proof_ref`
  を machine-readable に残す
- Council initiated pause は `council_resolution_ref` を fail-closed で必須化し、
  self initiated pause はそれを持たない contract に固定する
- `identity-demo` と `identity_pause_resume_contract.yaml` により、
  council pause / self resume / self pause roundtrip を repo 内で検証できる
- residual future work は broad な pause 不在ではなく、
  `Paused` 状態の法的人格や Failed-Ascension trauma handling のような制度・研究論点へ縮小される

## Revisit triggers

- `Paused` identity に独立した legal/personhood policy を与えたくなった時
- Failed-Ascension 後の生体側ケアを identity lifecycle contract に組み込みたくなった時
- pause/resume cycle を最新 1 回ではなく append-only history として別 schema へ切り出したくなった時
