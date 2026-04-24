---
date: 2026-04-24
surface:
  - src/omoikane/agentic/cognitive_audit_governance.py
  - specs/schemas/cognitive_audit_verifier_transport_binding.schema
  - evals/cognitive/cognitive_audit_verifier_transport.yaml
closes_next_gaps:
  - evals/cognitive/README.md#actual-non-loopback-verifier-transport
---

# Decision: cognitive audit reviewer quorum は non-loopback verifier transport に束縛する

## Context

`cognitive_audit_governance_binding` は reviewer-network receipt、
JP-13 / US-CA の multi-jurisdiction quorum、
Federation / Heritage returned-result signature binding まで固定していました。
一方で cognitive eval surface には、reviewer verifier evidence を
actual non-loopback transport trace へ接続する次段が残っていました。

## Decision

`cognitive-audit-non-loopback-verifier-transport-v1` を追加し、
既存の `distributed_transport_authority_route_trace` から次だけを
digest-only profile として cognitive audit governance binding へ束ねます。

- authenticated route trace ref / digest
- authority plane ref / route-target discovery ref
- non-loopback / cross-host / socket trace / OS observer completion flags
- reviewer network receipt ids
- reviewer binding digest
- route binding digest

raw socket payload や reviewer credential payload は保持しません。

## Consequence

- `cognitive-audit-governance-demo --json` が actual non-loopback mTLS authority route trace を実行し、その縮約 profile を 3 つの governance binding へ共有します
- public schema は `cognitive_audit_verifier_transport_binding.schema` を直接検証できます
- `evals/cognitive/cognitive_audit_verifier_transport.yaml` が L3/L4 境界 eval として reviewer quorum と transport trace の binding を守ります
