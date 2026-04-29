---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_stop_signal_path.schema
  - specs/schemas/ewa_stop_signal_adapter_receipt.schema
  - specs/schemas/ewa_emergency_stop.schema
  - specs/schemas/ewa_audit.schema
  - evals/safety/ewa_emergency_stop.yaml
  - evals/safety/ewa_regulator_permit_verifier.yaml
status: decided
closes_next_gaps:
  - ewa-regulator-permit-revocation-forced-stop
---

# Decision: EWA permit revocation を forced stop trigger として束縛する

## Context

`2026-04-30_ewa-permit-quorum-stop-audit-binding.md` では、permit quorum を
authorization だけでなく command audit と emergency stop receipt まで carry した。
残っていた未充足点は、actuation 実行中に regulator permit revocation readback が
発生した場合、それ自体を safe stop の trigger として扱える machine-readable 経路だった。

## Options considered

- A: revocation を incident note として audit に追記するだけにする
- B: revocation を既存 `emergency-disconnect` に丸める
- C: revocation を独立した `regulator-permit-revoked` stop trigger として扱う

## Decision

C を採択する。`regulator-permit-revoked` を固定 stop trigger set に追加し、
stop-signal path / PLC adapter receipt / emergency stop / audit / IDL / eval / reference runtime
で一貫して扱う。

revocation 起因の emergency stop は revocation ref、sha256 digest、verifier ref、
verified_at、status=`revoked` を必須にする。raw revocation payload は保存しない。
revocation は stop trigger であり、regulator verifier を EWA の decision authority へ
昇格させない。

## Consequences

- `ewa-demo --json` は permit revocation readback による emergency stop を返す。
- stop-signal path と adapter receipt は 5 trigger coverage を要求する。
- `validate_emergency_stop` は revocation trigger の evidence 欠落を fail-closed にする。
- 非 revocation trigger では revocation evidence を空にし、status を `not-applicable` に保つ。

## Revisit triggers

- 本番 regulator API の revocation freshness / certificate lifecycle を live endpoint verifier と直結する時
- revocation registry の multi-jurisdiction quorum 自体を emergency stop trigger selection に含める時
