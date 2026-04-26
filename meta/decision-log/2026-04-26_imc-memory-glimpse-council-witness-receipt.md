---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - specs/schemas/imc_memory_glimpse_receipt.schema
  - evals/interface/imc_memory_glimpse_council_witness.yaml
status: decided
closes_next_gaps:
  - imc.memory-glimpse.council-witness-digest-receipt
---

# Decision: IMC memory_glimpse を Council-witnessed digest receipt に束縛する

## Context

IMC の `memory_glimpse` mode は Council witness を要求し、
disclosure floor で raw memory fields を redaction していました。
ただし reviewer が確認できる evidence は handshake と message digest が中心で、
どの MemoryCrystal source segment が Council witness と同じ exchange に
束縛されたのかは first-class contract ではありませんでした。

## Options considered

- A: 既存の `imc_message.payload_digest` だけを維持し、MemoryCrystal source は docs に留める
- B: `memory_glimpse` 専用 receipt を追加し、MemoryCrystal manifest / segment digest、message digest、Council witness digest を束縛する
- C: redacted memory synopsis や selected source refs を receipt に直接保存する

## Decision

**B** を採択。

`council-witnessed-memory-glimpse-receipt-v1` は
MemoryCrystal manifest digest、selected segment digest set、IMC message payload digest、
Council session / resolution / Guardian attestation ref から作る witness digest を保持する。
raw memory payload と raw message payload は保存しない。

## Consequences

- `imc-demo --json` は `memory_glimpse_receipt` と validation flags を返す
- `interface.imc.v0` は `seal_memory_glimpse_receipt` operation を持つ
- `imc_memory_glimpse_receipt.schema` と
  `evals/interface/imc_memory_glimpse_council_witness.yaml` が同じ contract を検証する
- IntegrityGuardian は IMC memory_glimpse receipt の digest-only binding を監査できる

## Revisit triggers

- MemoryCrystal source を remote peer 側の verifier network へ提示する時
- memory glimpse に時間制限付き revoke / re-consent workflow を追加する時
- Council witness を Federation Council または Collective session witness へ拡張する時
