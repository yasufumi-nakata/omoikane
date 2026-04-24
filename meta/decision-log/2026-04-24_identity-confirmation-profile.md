---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/kernel/identity-lifecycle.md
  - docs/07-reference-implementation/README.md
  - evals/identity-fidelity/identity_confirmation_profile.yaml
  - specs/interfaces/kernel.identity.v0.idl
  - specs/schemas/identity_confirmation_profile.schema
status: decided
closes_next_gaps:
  - kernel.identity.multidimensional-confirmation-profile
---

# Decision: Identity Confirmation を多次元 profile として固定する

## Context

`identity-demo` は pause / resume lifecycle を machine-readable にしていましたが、
Ascending → Active の「自己同一性確認」は docs 上の手順に留まり、
subjective self-report と第三者観察記録を同じ digest-bound artifact に
束縛できていませんでした。

## Options considered

- A: Identity Confirmation は docs-only のまま維持する
- B: 4 dimension の fixed profile を追加し、self-report と witness quorum を runtime / schema / eval / CLI で検証する
- C: scheduler Method A に直接埋め込み、IdentityRegistry からは分離する

## Decision

**B** を採択。

## Consequences

- `multidimensional-identity-confirmation-v1` は episodic recall、
  SelfModel alignment、subjective self-report、third-party witness alignment の
  4 dimension を必須にする
- subjective self-report は raw statement を保持せず statement digest と
  dimension evidence digest に束縛する
- clinician + guardian の accepted witness quorum が揃わない profile は
  `failed-ascension-or-repeat-ascending` として fail-closed になる
- `identity-confirmation-demo --json` は pass profile と blocked profile を同時に返し、
  public schema と eval が runtime output を検証する

## Revisit triggers

- Identity Confirmation を scheduler handle の protected stage gate に直接接続する時
- witness role を jurisdiction-specific reviewer registry へ拡張する時
- subjective report の raw payload redaction policy を trust transfer / oversight と共通化する時
