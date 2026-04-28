---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/council_convocation_session.schema
  - evals/agentic/yaoyorozu_council_convocation.yaml
status: decided
---

# Decision: Yaoyorozu convocation selection に role scope を再束縛する

## Context

Yaoyorozu registry は Councilor / Guardian / Builder の role-specific scope refs と
policy ref を保持するようになった。しかし reviewer が Council convocation artifact
だけを見る場合、選定された agent がどの deliberation / oversight / build surface
境界に基づいて選ばれたかを registry snapshot まで戻らずに確認しにくかった。

## Decision

`council_convocation_session` の selection payload に
`registry-selection-scope-binding-v1` を追加する。speaker / recorder は
`role_scope_kind=deliberation`、guardian liaison は `role_scope_kind=oversight`、
builder handoff は `role_scope_kind=build-surface` を持つ。profile-specific council
panel は selected agent の role に応じて `deliberation` / `oversight` /
`research-evidence` の scope を持つ。各 selection は registry entry 由来の scope refs と
policy ref だけを保持し、raw deliberation transcript、raw audit payload、raw research
payload、raw build payload は保存しない。

reference runtime は standing roles、council panel、builder handoff の scope binding を
convocation validation に含める。public schema と eval は同じ field を検証し、
`yaoyorozu-demo --json` でも top-level validation に露出する。

## Consequences

- Council handoff reviewer は convocation artifact だけで選定 agent の監査境界を確認できる。
- Builder handoff は coverage label だけでなく、選定 builder の build surface refs にも束縛される。
- raw transcript / audit / build payload 非保存の方針を selection artifact にも明示できる。

## Revisit triggers

- proposal profile ごとに Councilor deliberation policy を分岐する時
- Builder coverage area と build surface refs の対応を subdirectory 単位まで細分化する時
