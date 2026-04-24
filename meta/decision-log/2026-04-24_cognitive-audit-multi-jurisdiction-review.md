---
date: 2026-04-24
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/cognitive-audit-loop.md
  - docs/04-ai-governance/guardian-oversight.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/cognitive_audit_governance_binding.yaml
  - specs/interfaces/agentic.cognitive_audit_governance.v0.idl
  - specs/schemas/cognitive_audit_governance_binding.schema
status: decided
---

# Decision: cognitive audit governance は multi-jurisdiction reviewer quorum を要求する

## Context

`cognitive-audit-governance-demo` は local cognitive audit resolution を
network-attested oversight、Federation returned result、Heritage returned result へ
束縛できていました。

ただし cognitive 側の binding は reviewer network receipt id の列挙だけに留まり、
その reviewer quorum が複数法域の legal execution と jurisdiction bundle を
実際に覆っているかを machine-checkable に確認できませんでした。

## Options considered

- A: `network_receipt_ids` のみを維持し、法域 quorum は Guardian oversight 側の暗黙条件として扱う
- B: cognitive audit governance binding に reviewer binding の raw credential / legal package を埋め込む
- C: cognitive audit governance binding に digest-only の multi-jurisdiction review profile を追加する

## Decision

**C** を採択。

`cognitive-audit-multi-jurisdiction-review-v1` を canonical profile とし、
JP-13 / US-CA の 2 法域 quorum、legal policy refs、jurisdiction bundle refs、
legal execution ids、network receipt count、reviewer binding digest を
`cognitive_audit_governance_binding` へ追加しました。

## Consequences

- `bind_governance()` は reviewer bindings が 2 法域以上を覆らない場合 fail-closed になります
- public schema / IDL / eval / CLI demo は同じ profile id と required quorum を共有します
- raw credential、raw legal package、verifier transcript は引き続き保存せず、
  refs / digests / receipt ids だけを cognitive audit governance surface へ公開します

## Revisit triggers

- verifier transport を actual non-loopback transport へ接続したくなった時
- required jurisdiction quorum を policy-driven に切り替えたくなった時
- Federation / Heritage verdict の署名 payload を binding digest に含めたくなった時
