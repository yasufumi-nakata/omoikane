---
date: 2026-04-19
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/README.md
  - docs/02-subsystems/interface/collective-identity.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - evals/interface/collective_merge_reversibility.yaml
  - specs/catalog.yaml
status: decided
---

# Decision: merge_thought を bounded collective contract として reference runtime に固定する

## Context

`interface.imc.v0` には既に `merge_thought` mode が存在していたが、
実際には open/close/dissolve の runtime contract が無く、
Collective が IdentityRegistry 上でどのように distinct ID を持つか、
merge 後にどう recovery へ戻るかも docs の構想止まりでした。
`gap-report --json` は all-zero だったため、今回は open question の穴埋めではなく、
README / roadmap / research frontier に残っていた durable surface を
runtime / schema / eval / CLI まで materialize する必要がありました。

## Options considered

- A: `merge_thought` は IMC mode 名だけに留め、Collective は research frontier のまま残す
- B: collective personhood と legal personhood まで含む広い制度設計を先に実装する
- C: distinct collective ID、10 秒 cap、private escape、post-disconnect identity confirmation に絞った bounded contract を先に固定する

## Decision

**C** を採択。

## Consequences

- `interface.collective.v0` を追加し、
  `register_collective / open_merge_session / close_merge_session / dissolve_collective`
  の 4 op を固定する
- `CollectiveIdentityService` は member 2-4 名、`merge_thought` only、
  `max_duration_seconds=10.0`、single active merge、`private_reality` escape、
  `all-members` identity confirmation を強制する
- `collective-demo` は IMC `merge_thought`、WMS major divergence、
  private escape、member recovery、collective dissolution を 1 シナリオで検証する
- legal personhood や長期存続 Collective は引き続き research frontier に残す

## Revisit triggers

- Collective を dissolve せず長時間維持する governance / fiscal contract が必要になった時
- 3 名以上の merge arbitration や subgroup split/merge を扱いたくなった時
- legal personhood や external registry attestation を reference runtime に持ち込みたくなった時
