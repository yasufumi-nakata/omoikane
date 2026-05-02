---
date: 2026-05-02
status: decided
---

# Decision: gap-report は agent source definition violation も all-zero gate に含める

## Context

Yaoyorozu registry materialization は raw `agents/**/*.yaml` を
`schema-bound-agent-source-definition-v1` で検証してから digest-only manifest
へ束縛していました。一方で `gap-report --json` の all-zero gate は agent YAML
自体を独立した scan surface として検査しておらず、agent source が壊れても
Yaoyorozu demo まで進まないと見落とす余地がありました。

## Decision

`gap-report` に `agent_source_definition_violation_hits` /
`agent_source_definition_violation_count` を追加する。
scanner は `agents/**/*.yaml` を digest-bound scan surface に含め、
既存 Yaoyorozu validator で source definition を検証する。
違反時は source path、agent id、role、policy id、error count、短い violation
summary だけを返し、raw agent source payload は保存しない。

## Consequences

- 毎時 automation の all-zero gate は agent source definition drift を Yaoyorozu demo 前に検出できる。
- `gap_report.schema`、`selfctor.gap_report.v0.idl`、eval inventory、IntegrityGuardian policy は agent source validation を監査対象として扱う。
- raw agent source payload は scan receipt に保存せず、`agents/**/*.yaml` surface digest と violation summary だけで reviewer evidence を保持する。
