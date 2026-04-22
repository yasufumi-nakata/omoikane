---
date: 2026-04-22
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/agentic/README.md
  - docs/02-subsystems/agentic/council-composition.md
  - docs/02-subsystems/agentic/yaoyorozu-roster.md
  - docs/04-ai-governance/subagent-roster.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/agentic.yaoyorozu.v0.idl
  - specs/schemas/agent_registry_entry.schema
  - specs/schemas/yaoyorozu_registry_snapshot.schema
  - specs/schemas/council_convocation_session.schema
  - evals/agentic/yaoyorozu_council_convocation.yaml
status: decided
---

# Decision: YaoyorozuRegistry と Council convocation を repo-local runtime surface に昇格する

## Context

L4 Agentic docs では `YaoyorozuRegistry` が
「利用可能 Agent の登録簿」として繰り返し参照され、
`Council` は案件ごとに動的召集される前提でした。
しかし 2026-04-22 時点の reference runtime は
`agentic.trust.v0` による trust update と
`consensus-bus-demo` / `task-graph-demo` の個別 surface までは持つ一方、
repo-local `agents/` 定義を machine-checkable な registry snapshot と
convocation artifact に束縛する surface がありませんでした。

そのため `agents/` の role / capability / trust_floor と
Council / Builder handoff の選定規則が docs 上の約束に留まり、
automation が「今の roster で誰を召集できるか」を
JSON contract として確認できない状態でした。

## Options considered

- A: `trust-demo` のみを維持し、registry / convocation は docs と手読みに委ねる
- B: repo-local `agents/` を sync する `YaoyorozuRegistryService` を追加し、
  trust-bound registry snapshot と bounded convocation artifact を固定する
- C: live subagent process orchestration まで同時に実装し、
  registry / convocation / execution を一気に接続する

## Decision

Option B を採択します。

- `agentic.yaoyorozu.v0` を追加し、
  `sync_registry` と `prepare_council_convocation` を public contract とします
- reference runtime は repo-local `agents/` から
  `yaoyorozu_registry_snapshot` を materialize し、
  `Self-Modify Patch` 用の `council_convocation_session` を返します
- standing role は `Speaker` / `Recorder` / `GuardianLiaison` / `SelfLiaison` に固定し、
  builder handoff は runtime / schema / eval / docs coverage を必須化します

## Consequences

- `yaoyorozu-demo` により
  `agents/` / trust / convocation / builder coverage を 1 本の JSON で監査できます
- `specs/schemas/agent_registry_entry.schema`、
  `yaoyorozu_registry_snapshot.schema`、
  `council_convocation_session.schema` が
  public validation target になります
- L4 residual gap は generic な registry 不在から、
  live worker discovery や actual process dispatch のような
  repo 外依存を含む次段へ縮小されます

## Revisit triggers

- `Self-Modify Patch` 以外の proposal profile
  （Memory Edit、Fork Request、Inter-Mind Negotiation）を
  convocation catalog に増やしたくなった時
- live subagent process orchestration や external worker health を
  registry snapshot に束縛したくなった時
- Council convocation を TaskGraph construction / ConsensusBus dispatch と
  same-session digest で直結したくなった時
