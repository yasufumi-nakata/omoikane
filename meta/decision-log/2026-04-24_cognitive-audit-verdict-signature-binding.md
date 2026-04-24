---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/cognitive-audit-loop.md
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.cognitive_audit_governance.v0.idl
  - specs/schemas/cognitive_audit_governance_binding.schema
  - specs/schemas/distributed_council_verdict_signature.schema
  - evals/agentic/cognitive_audit_governance_binding.yaml
status: decided
closes_next_gaps:
  - agentic.cognitive-audit.distributed-verdict-signature-binding
---

# Decision: cognitive audit governance は returned-result signature binding を digest に含める

## Context

`cognitive-audit-governance-demo` は Federation / Heritage returned result を
network-attested oversight と multi-jurisdiction reviewer quorum に束ねていました。
ただし governance binding 内の distributed verdict は normalized fields のみで、
returned-result payload が署名対象としてどの digest に固定されたかを
validation surface で確認できませんでした。

## Options considered

- A: distributed verdict の normalized fields だけを維持する
- B: raw Council signature payload を governance binding に埋め込む
- C: digest-only の `distributed-council-verdict-signature-binding-v1` を追加し、signed payload digest / signer ref / signature digest だけを binding digest に含める

## Decision

**C** を採択。

reference runtime は Federation / Heritage returned result ごとに
`distributed_council_verdict_signature` を生成し、
`cognitive_audit_governance_binding.distributed_verdicts[].signature_binding` へ含める。

## Consequences

- `validate_binding()` は signed verdict payload の tamper を検出し、
  `distributed_signature_bound=false` として fail-closed にする
- public schema / IDL / eval / docs は
  `distributed-council-verdict-signature-binding-v1` と
  `sha256-reference-signature-v1` を共有する
- raw signature payload、participant credential body、raw cognitive payload は保存せず、
  digest / ref / signature digest のみを公開 surface に残す
- IntegrityGuardian は cognitive audit governance binding 上の signature binding を
  検証対象 capability として持つ

## Revisit triggers

- returned result の署名を external distributed transport receipt と直接束縛する時
- Federation / Heritage signer roster を rotating key registry へ移す時
- human-governance escalation verdict にも同じ signature binding を拡張する時
