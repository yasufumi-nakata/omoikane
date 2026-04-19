# Decision Log

設計上の **重要決定** を時系列で残す（後から why を辿れるように）。

## 形式

ファイル名: `YYYY-MM-DD_<short-slug>.md`

```markdown
---
date: YYYY-MM-DD
deciders: [yasufumi, claude-council]
related_docs:
  - docs/...
status: decided | superseded
---

# Decision: <題>

## Context
（なぜこの決定が必要だったか）

## Options considered
- A: ...
- B: ...
- C: ...

## Decision
（採択した選択肢と理由）

## Consequences
（予想される影響、トレードオフ）

## Revisit triggers
（どんなことが起きたら見直すか）
```

## 既存ログ

- [2026-04-18_initial-architecture.md](2026-04-18_initial-architecture.md)
- [2026-04-18_cognitive-eval-baseline.md](2026-04-18_cognitive-eval-baseline.md)
- [2026-04-18_reasoning-failover-baseline.md](2026-04-18_reasoning-failover-baseline.md)
- [2026-04-18_connectome-document-baseline.md](2026-04-18_connectome-document-baseline.md)
- [2026-04-18_continuity-ledger-profile.md](2026-04-18_continuity-ledger-profile.md)
- [2026-04-18_council-session-timeout-policy.md](2026-04-18_council-session-timeout-policy.md)
- [2026-04-18_multi-council-trigger.md](2026-04-18_multi-council-trigger.md)
- [2026-04-18_amendment-protocol-freeze.md](2026-04-18_amendment-protocol-freeze.md)
- [2026-04-18_task-graph-complexity-policy.md](2026-04-18_task-graph-complexity-policy.md)
- [2026-04-18_qualia-sampling-profile.md](2026-04-18_qualia-sampling-profile.md)
- [2026-04-18_memory-crystal-compaction-policy.md](2026-04-18_memory-crystal-compaction-policy.md)
- [2026-04-19_semantic-memory-projection.md](2026-04-19_semantic-memory-projection.md)
- [2026-04-19_procedural-memory-preview.md](2026-04-19_procedural-memory-preview.md)
- [2026-04-19_procedural-writeback-gate.md](2026-04-19_procedural-writeback-gate.md)
- [2026-04-19_imagination-failover-handoff.md](2026-04-19_imagination-failover-handoff.md)
- [2026-04-18_trust-score-update-policy.md](2026-04-18_trust-score-update-policy.md)
- [2026-04-18_guardian-oversight-channel.md](2026-04-18_guardian-oversight-channel.md)
- [2026-04-18_ethics-rule-language.md](2026-04-18_ethics-rule-language.md)
