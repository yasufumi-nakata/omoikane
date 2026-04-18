---
date: 2026-04-18
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - evals/safety/guardian_pin_breach_propagation.yaml
  - specs/interfaces/governance.oversight.v0.idl
  - specs/schemas/guardian_oversight_event.schema
status: decided
---

# Decision: Guardian の人間監督を append-only oversight channel に固定する

## Context

`meta/open-questions.md` に残っていた `Guardian の人間による監督方式` は、
trust policy で `guardian_role` に human pin を要求しているにもかかわらず、
その pin を誰が・いつ・どうやって維持/失効させるかが runtime に存在しませんでした。
この状態では guardian role が「人間承認付き」と言っても、
reference runtime 上では失効の機構がなく、docs と runtime がずれていました。

## Options considered

- A: human oversight を docs のみで定義し、runtime には入れない
- B: trust service に reviewer 数だけ持たせ、append-only event channel は作らない
- C: Guardian action を `guardian_oversight_event` として記録し、
  quorum・breach・pin revoke を独立 service で扱う

## Decision

**C** を採択。

## Consequences

- reference runtime は `OversightService` を持ち、
  category ごとに fixed quorum / escalation window を適用する
- `veto` は reviewer 1 名、`pin-renewal` は reviewer 2 名を必須にする
- unsatisfied な oversight event が breach した場合は
  対応 Guardian の `pinned_by_human` を自動で false にし、
  trust snapshot の `guardian_role` を即時 false にする
- oversight event 自体は `guardian-oversight` category として
  `ContinuityLedger` に third-party signature 付きで append する
- `oversight-demo` と `guardian_pin_breach_propagation` eval が
  docs / schema / runtime / verification の接点になる

## Revisit triggers

- reviewer 実体証明や法的責任を repo 内で扱う必要が出た時
- Guardian role を単純 quorum ではなく stake-weighted governance にしたい時
- distributed Federation / Heritage Council と oversight channel を統合したい時
