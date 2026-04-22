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
- [2026-04-19_reasoning-service-contract-promotion.md](2026-04-19_reasoning-service-contract-promotion.md)
- [2026-04-19_imagination-failover-handoff.md](2026-04-19_imagination-failover-handoff.md)
- [2026-04-19_guardian-live-credential-verification.md](2026-04-19_guardian-live-credential-verification.md)
- [2026-04-19_language-disclosure-floor.md](2026-04-19_language-disclosure-floor.md)
- [2026-04-19_metacognition-self-monitor-loop.md](2026-04-19_metacognition-self-monitor-loop.md)
- [2026-04-19_self-model-threshold-profile.md](2026-04-19_self-model-threshold-profile.md)
- [2026-04-19_scheduler-artifact-sync-gate.md](2026-04-19_scheduler-artifact-sync-gate.md)
- [2026-04-19_scheduler-verifier-root-rotation.md](2026-04-19_scheduler-verifier-root-rotation.md)
- [2026-04-19_distributed-council-resolution.md](2026-04-19_distributed-council-resolution.md)
- [2026-04-19_cognitive-audit-loop.md](2026-04-19_cognitive-audit-loop.md)
- [2026-04-20_consensus-bus-reference-runtime.md](2026-04-20_consensus-bus-reference-runtime.md)
- [2026-04-20_distributed-transport-live-root-directory.md](2026-04-20_distributed-transport-live-root-directory.md)
- [2026-04-21_distributed-transport-non-loopback-route-trace.md](2026-04-21_distributed-transport-non-loopback-route-trace.md)
- [2026-04-21_external-actuation-authorization-artifact.md](2026-04-21_external-actuation-authorization-artifact.md)
- [2026-04-21_ewa-emergency-stop-protocol.md](2026-04-21_ewa-emergency-stop-protocol.md)
- [2026-04-21_design-reader-git-delta-scan.md](2026-04-21_design-reader-git-delta-scan.md)
- [2026-04-21_broker-dual-allocation-window.md](2026-04-21_broker-dual-allocation-window.md)
- [2026-04-22_broker-cross-host-dual-allocation.md](2026-04-22_broker-cross-host-dual-allocation.md)
- [2026-04-22_gap-report-truth-source-future-work.md](2026-04-22_gap-report-truth-source-future-work.md)
- [2026-04-22_sensory-loopback-body-map-calibration.md](2026-04-22_sensory-loopback-body-map-calibration.md)
- [2026-04-22_guardian-verifier-transport-exchange.md](2026-04-22_guardian-verifier-transport-exchange.md)
- [2026-04-22_guardian-jurisdiction-legal-execution.md](2026-04-22_guardian-jurisdiction-legal-execution.md)
- [2026-04-21_builder-rollback-external-observer-receipts.md](2026-04-21_builder-rollback-external-observer-receipts.md)
- [2026-04-21_builder-rollback-current-worktree-direct-mutation.md](2026-04-21_builder-rollback-current-worktree-direct-mutation.md)
- [2026-04-20_builder-sandbox-apply-rollout.md](2026-04-20_builder-sandbox-apply-rollout.md)
- [2026-04-20_sensory-loopback-reference-runtime.md](2026-04-20_sensory-loopback-reference-runtime.md)
- [2026-04-22_distributed-transport-route-target-discovery.md](2026-04-22_distributed-transport-route-target-discovery.md)
- [2026-04-18_trust-score-update-policy.md](2026-04-18_trust-score-update-policy.md)
- [2026-04-18_guardian-oversight-channel.md](2026-04-18_guardian-oversight-channel.md)
- [2026-04-18_ethics-rule-language.md](2026-04-18_ethics-rule-language.md)
