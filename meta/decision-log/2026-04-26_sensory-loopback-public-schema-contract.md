---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - evals/interface/sensory_loopback_public_schema_contract.yaml
  - tests/integration/test_interface_schema_contracts.py
  - agents/guardians/integrity-guardian.yaml
status: decided
closes_next_gaps:
  - sensory-loopback.public-schema-contract
---

# Decision: Sensory Loopback demo を public schema contract manifest に束縛する

## Context

L6 Sensory Loopback は session、receipt、artifact family の public schema と
`sensory-loopback-demo --json` を持っていました。
ただし hidden gap として、demo 出力の self-only / collective-shared payload が
どの public schema に対応するかを reviewer-facing に列挙せず、
integration test も WMS / Collective の contract だけを直接 validation していました。

そのため CLI smoke と service-local validation は通っても、
schema drift が sensory loopback の reviewer-facing JSON まで届く前に止まりませんでした。

## Options considered

- A: 既存の service validation と unit test だけを維持する
- B: integration test で固定 path を直接 validation する
- C: runtime demo が `schema_contracts` manifest を返し、その manifest を integration test / eval / docs / IntegrityGuardian capability で共有する

## Decision

**C** を採択。

`sensory-loopback-public-schema-contract-v1` を reference profile に追加し、
`sensory-loopback-demo --json` は self-only と shared loopback の session、
receipt、artifact family payload を `schema_contracts` manifest に列挙する。

integration test は manifest の `payload_path` と `schema_path` を使い、
`sensory_loopback_session.schema`、`sensory_loopback_receipt.schema`、
`sensory_loopback_artifact_family.schema` に demo payload を直接通す。

## Consequences

- self-only と collective-shared の loopback JSON が同じ public schema contract で検証される
- eval / catalog / docs / IntegrityGuardian capability が同じ profile id を共有する
- artifact family や guardian-mediated receipt の schema drift を CLI demo 経由で検出できる

## Revisit triggers

- raw sensory capture adapter を repo 外 connector から取り込む時
- 4 participant 超の shared sensory field を public schema contract に分割する時
