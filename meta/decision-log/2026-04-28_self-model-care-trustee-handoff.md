---
date: 2026-04-28
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/mind-substrate/self-model.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/mind.self_model.v0.idl
  - specs/schemas/self_model_care_trustee_handoff_receipt.schema
  - evals/identity-fidelity/self_model_care_trustee_handoff.yaml
  - agents/guardians/identity-guardian.yaml
status: decided
---

# Decision: SelfModel care trustee handoff を外部責任境界に固定する

## Context

`self-model-pathology-escalation-boundary-v1` は possible pathological self-assessment を
OS 内診断・強制補正へ進めず外部医療・法制度・care handoff へ渡す境界を固定した。
一方で、長期 trustee、care team、legal guardian の責任分担を OS がどこまで扱うかは
repo-local で machine-checkable な contract へ落ちていなかった。

## Decision

`self-model-care-trustee-responsibility-handoff-v1` を追加し、
`self_model_care_trustee_handoff_receipt` で source pathology escalation receipt、
外部 trustee refs、care team refs、legal guardian refs、responsibility boundary refs、
long-term review schedule、continuity ref を digest-only に束縛する。

reference runtime の scope は `boundary-and-evidence-routing-only` に限定する。
trustee authority、care team authority、legal guardian authority は外部人間社会側の制度に置き、
OS trustee role、OS medical authority、OS legal guardianship、SelfModel writeback、
forced correction、raw trustee / care / legal / SelfModel payload 保存はいずれも許可しない。

## Consequences

- `self-model-demo --json` は `care_trustee_handoff` branch と validation summary を返す
- public schema / IDL / identity-fidelity eval / IdentityGuardian capability は同じ policy id を共有する
- ledger event は care trustee handoff digest、long-term review requirement、no OS trustee role を identity-fidelity evidence として残す

## Revisit triggers

- 実世界の trustee / care team / legal guardian registry を first-class schema へ接続する時
- 外部医療・法制度側の adjudication result schema を OS 外 authority として取り込む時
