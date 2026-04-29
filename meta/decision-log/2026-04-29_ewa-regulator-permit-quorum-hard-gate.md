---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_regulator_permit_verifier_receipt.schema
  - specs/schemas/ewa_regulator_permit_quorum_receipt.schema
  - specs/schemas/external_actuation_authorization.schema
  - evals/safety/ewa_regulator_permit_verifier.yaml
status: decided
closes_next_gaps:
  - ewa-regulator-permit-quorum-hard-gate
---

# Decision: EWA regulator permit quorum を authorization hard input にする

## Context

EWA regulator permit verifier は single readback を legal execution に束縛していたが、
permit class ごとの複数 verifier threshold、verifier roster、revocation registry は
authorization artifact の hard input ではなかった。

## Decision

`ewa-regulator-permit-verifier-quorum-v1` を追加し、JP-13 と SG-01 の
accepted permit readback digest set、permit class、threshold policy digest、
verifier roster digest、revocation registry digest を束縛する。

`external_actuation_authorization` は、この quorum receipt id/digest と
complete status を必須 field として持つ。quorum は EWA authorization の hard input だが、
verifier / quorum 自身は decision authority へ昇格しない。raw permit、
raw regulator response、raw threshold policy、raw roster payload は保持しない。

## Consequences

- `ewa-demo --json` は primary / backup permit readback と quorum receipt を返す。
- `authorize` / `validate_authorization` は regulator permit quorum が complete でない場合に
  non-read-only actuation authorization を通さない。
- schema / IDL / eval / docs / IntegrityGuardian scope は同じ quorum profile と
  threshold policy id を共有する。

## Revisit triggers

- 本番 regulator API の route / certificate / freshness verifier を接続する時
- permit class ごとに required jurisdiction set を動的 registry へ移す時
- quorum receipt を emergency stop や post-actuation audit にも直接束縛する時
