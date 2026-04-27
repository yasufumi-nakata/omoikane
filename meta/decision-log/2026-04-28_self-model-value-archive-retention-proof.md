---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_value_archive_retention_proof.schema
  - evals/identity-fidelity/self_model_value_archive_retention_proof.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel value archive retention を external proof refs に束縛する

## Context

`self-model-value-lineage-timeline-v1` は、生成、future-self acceptance、retirement を
append-only timeline に束ね、retired value に archive snapshot ref を要求する。
ただし archive snapshot ref が外部 trustee、long-term storage、retention policy、
retrieval test refs と同じ digest-bound receipt に入っていないと、active writeback から
退役した value history の保持経路を reviewer-facing artifact として確認しにくい。

## Decision

`self-model-value-archive-retention-proof-v1` を追加し、
`self_model_value_archive_retention_proof` receipt で value timeline receipt digest、
timeline commit digest、archive snapshot digest set、retired value digest set、
trustee proof refs、long-term storage proof refs、retention policy refs、retrieval test refs を
`retention_commit_digest` に束縛する。

この receipt は external proof refs を digest-only に扱い、raw archive / trustee / storage /
continuity payload を保存しない。Council と Guardian は boundary-only review に留まり、
external veto や archive deletion authority を持たない。

## Consequences

- `self-model-demo --json` は `value_archive_retention_proof` branch と validation summary を返す。
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する。
- ledger event は retention proof digest、trustee proof binding、storage proof binding、
  archive deletion disallow を identity-fidelity evidence として残す。

## Revisit triggers

- 実在 trustee registry や long-term storage verifier の live response を receipt に接続する時
- archive retention の proof refresh / revocation / expiry window を別 receipt に分ける時
