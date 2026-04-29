---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/ewa-safety.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.ewa.v0.idl
  - specs/schemas/ewa_audit.schema
  - specs/schemas/ewa_emergency_stop.schema
  - evals/safety/ewa_emergency_stop.yaml
  - evals/safety/ewa_regulator_permit_verifier.yaml
status: decided
closes_next_gaps:
  - ewa-regulator-permit-quorum-stop-audit-binding
---

# Decision: EWA permit quorum を停止・監査経路まで束縛する

## Context

EWA regulator permit quorum は `external_actuation_authorization` の hard input になったが、
実行後の command audit と emergency stop receipt は motor plan、stop-signal、
production connector、legal execution までの束縛で止まっていた。
そのため post-actuation review では authorization を gate した permit quorum が
停止・監査経路に直接残らない可能性があった。

## Decision

`ewa_audit` と `ewa_emergency_stop` に regulator permit quorum receipt id / digest / status、
threshold policy digest、verifier roster digest、revocation registry digest を保持する。
reference runtime は non-read-only command audit と emergency stop validation で同じ
quorum receipt を authorization と照合し、`quorum_status=complete` でない場合は
証跡を invalid にする。

raw permit、raw regulator response、raw threshold policy、raw roster payload は引き続き
保存しない。permit quorum は decision authority へ昇格せず、authorization を通した証跡として
post-actuation audit と forced stop に carry する。

## Consequences

- `ewa-demo --json` は approved command と emergency stop の両方で
  regulator permit quorum binding を返す。
- `ewa_emergency_stop.schema` と `ewa_audit.schema` は permit quorum evidence を必須化する。
- `ewa_emergency_stop` eval と `ewa_regulator_permit_verifier` eval は
  authorization だけでなく command audit / emergency stop までの証跡保持を検証する。

## Revisit triggers

- 本番 regulator API の freshness / certificate lifecycle を emergency stop 後の post-incident review に直接接続する時
- permit revocation が actuation 実行中に発生した場合の forced stop trigger を追加する時
