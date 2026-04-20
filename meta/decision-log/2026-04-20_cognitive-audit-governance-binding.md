---
date: 2026-04-20
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/cognitive-audit-loop.md
  - docs/07-reference-implementation/README.md
  - evals/agentic/cognitive_audit_governance_binding.yaml
  - specs/interfaces/agentic.cognitive_audit_governance.v0.idl
  - specs/schemas/cognitive_audit_governance_binding.schema
status: decided
---

# Decision: cognitive audit follow-up を oversight / Federation / Heritage governance binding へ昇格する

## Context

`cognitive-audit-demo` により
qualia / self-model / metacognition / local Council review までは
machine-checkable でしたが、
`evals/cognitive/README.md` に残っていた
`distributed oversight / Federation / Heritage returned result` との直結は
未実装でした。

そのため、local `cognitive_audit_resolution` が
external review tier や reviewer verifier-network に
どう束縛されるかは repo 内で検証できませんでした。

## Options considered

- A: local cognitive audit loop のみを維持し、distributed governance binding は future work に残す
- B: local resolution をそのまま書き換え、distributed verdict を ad-hoc field で埋め込む
- C: local resolution を immutable に保ったまま、
  `cognitive_audit_governance_binding` という follow-up artifact を新設する

## Decision

**C** を採択。

## Consequences

- `agentic.cognitive_audit_governance.v0` /
  `cognitive_audit_governance_binding.schema` /
  `cognitive-audit-governance-demo` を追加する
- governance binding は
  reviewer verifier-network receipt を持つ oversight event と
  Federation / Heritage returned result を
  digest-safe ref のみで束ねる
- gate は
  `federation-attested-review` /
  `heritage-veto-boundary` /
  `distributed-conflict-human-escalation`
  に固定する
- local `cognitive_audit_resolution` 自体は不変のまま残し、
  override は binding artifact 側の `final_follow_up_action` で表す

## Revisit triggers

- verifier network を non-loopback / multi-jurisdiction transport へ拡張したい時
- distributed transport actual network と reviewer verifier network を統合したい時
- Federation / Heritage verdict を signed payload 付きで repo 内監査対象に上げたい時
