---
date: 2026-04-26
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/imc-protocol.md
  - docs/03-protocols/inter-mind-comm.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.imc.v0.idl
  - specs/schemas/imc_memory_glimpse_reconsent_receipt.schema
  - evals/interface/imc_memory_glimpse_reconsent.yaml
status: decided
closes_next_gaps:
  - imc.memory-glimpse.revoke-reconsent-timebox
---

# Decision: IMC memory_glimpse を timeboxed revoke/re-consent receipt に束縛する

## Context

`council-witnessed-memory-glimpse-receipt-v1` は MemoryCrystal source、
message digest、Council witness を digest-only に束縛しました。
ただし一度 witness 済みの memory_glimpse が、participant withdrawal 後も
同じ source を再共有できるかどうかは first-class receipt ではありませんでした。

## Options considered

- A: emergency disconnect だけで memory_glimpse の再共有禁止を表す
- B: raw re-consent transcript を保存して人間 reviewer が再共有可否を読む
- C: 元の receipt digest、revocation event、timeboxed window、Council re-consent、
  Guardian attestation を digest-only receipt に束縛する

## Decision

**C** を採択。

`timeboxed-memory-glimpse-reconsent-receipt-v1` は元の memory_glimpse receipt digest、
message id、selected MemoryCrystal segment digest set、participant withdrawal の
revocation event ref、`expires_after_seconds<=86400` の consent window、
Council re-consent ref、Guardian attestation ref を束縛する。
raw memory payload、raw message payload、raw re-consent payload は保存しない。

## Consequences

- `imc-demo --json` は `memory_glimpse_reconsent_receipt` と validation flags を返す
- `interface.imc.v0` は `seal_memory_glimpse_reconsent_receipt` operation を持つ
- public schema / eval / IntegrityGuardian capability は同じ timeboxed re-consent profile を共有する
- revoked session は `revoked-pending-reconsent` として残り、redisclosure には Council / Guardian の再承認が必要になる

## Revisit triggers

- remote peer 側の verifier network へ re-consent proof を提示する時
- re-consent window を jurisdiction policy registry から動的に導出する時
- Collective session witness を memory_glimpse re-consent に拡張する時
