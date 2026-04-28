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
- [2026-04-23_semantic-procedural-handoff.md](2026-04-23_semantic-procedural-handoff.md)
- [2026-04-23_gap-report-decision-log-residuals.md](2026-04-23_gap-report-decision-log-residuals.md)
- [2026-04-23_yaoyorozu-inter-mind-negotiation-profile.md](2026-04-23_yaoyorozu-inter-mind-negotiation-profile.md)
- [2026-04-23_yaoyorozu-memory-edit-profile.md](2026-04-23_yaoyorozu-memory-edit-profile.md)
- [2026-04-23_yaoyorozu-task-graph-binding.md](2026-04-23_yaoyorozu-task-graph-binding.md)
- [2026-04-23_yaoyorozu-local-worker-dispatch.md](2026-04-23_yaoyorozu-local-worker-dispatch.md)
- [2026-04-23_yaoyorozu-worker-delta-receipt.md](2026-04-23_yaoyorozu-worker-delta-receipt.md)
- [2026-04-23_yaoyorozu-worker-patch-candidate-receipt.md](2026-04-23_yaoyorozu-worker-patch-candidate-receipt.md)
- [2026-04-23_gap-report-eval-inventory-drift.md](2026-04-23_gap-report-eval-inventory-drift.md)
- [2026-04-19_procedural-memory-preview.md](2026-04-19_procedural-memory-preview.md)
- [2026-04-19_procedural-writeback-gate.md](2026-04-19_procedural-writeback-gate.md)
- [2026-04-19_reasoning-service-contract-promotion.md](2026-04-19_reasoning-service-contract-promotion.md)
- [2026-04-19_imagination-failover-handoff.md](2026-04-19_imagination-failover-handoff.md)
- [2026-04-19_guardian-live-credential-verification.md](2026-04-19_guardian-live-credential-verification.md)
- [2026-04-19_language-disclosure-floor.md](2026-04-19_language-disclosure-floor.md)
- [2026-04-19_metacognition-self-monitor-loop.md](2026-04-19_metacognition-self-monitor-loop.md)
- [2026-04-19_self-model-threshold-profile.md](2026-04-19_self-model-threshold-profile.md)
- [2026-04-28_self-model-pathology-escalation-boundary.md](2026-04-28_self-model-pathology-escalation-boundary.md)
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
- [2026-04-22_termination-scheduler-cancellation-binding.md](2026-04-22_termination-scheduler-cancellation-binding.md)
- [2026-04-22_patch-generator-diff-eval-standalone-demos.md](2026-04-22_patch-generator-diff-eval-standalone-demos.md)
- [2026-04-22_sensory-loopback-body-map-calibration.md](2026-04-22_sensory-loopback-body-map-calibration.md)
- [2026-04-22_ethics-resolution-policy-and-schema-bound-decision.md](2026-04-22_ethics-resolution-policy-and-schema-bound-decision.md)
- [2026-04-22_guardian-verifier-transport-exchange.md](2026-04-22_guardian-verifier-transport-exchange.md)
- [2026-04-22_guardian-jurisdiction-legal-execution.md](2026-04-22_guardian-jurisdiction-legal-execution.md)
- [2026-04-22_ewa-guardian-oversight-gate.md](2026-04-22_ewa-guardian-oversight-gate.md)
- [2026-04-22_automation-reference-playbooks.md](2026-04-22_automation-reference-playbooks.md)
- [2026-04-21_builder-rollback-external-observer-receipts.md](2026-04-21_builder-rollback-external-observer-receipts.md)
- [2026-04-21_builder-rollback-current-worktree-direct-mutation.md](2026-04-21_builder-rollback-current-worktree-direct-mutation.md)
- [2026-04-20_builder-sandbox-apply-rollout.md](2026-04-20_builder-sandbox-apply-rollout.md)
- [2026-04-20_sensory-loopback-reference-runtime.md](2026-04-20_sensory-loopback-reference-runtime.md)
- [2026-04-22_distributed-transport-route-target-discovery.md](2026-04-22_distributed-transport-route-target-discovery.md)
- [2026-04-18_trust-score-update-policy.md](2026-04-18_trust-score-update-policy.md)
- [2026-04-24_trust-recovery-notice-scope-disclosure.md](2026-04-24_trust-recovery-notice-scope-disclosure.md)
- [2026-04-25_wms-distributed-approval-fanout.md](2026-04-25_wms-distributed-approval-fanout.md)
- [2026-04-25_wms-approval-collection-scaling.md](2026-04-25_wms-approval-collection-scaling.md)
- [2026-04-25_wms-registry-slo-retry-budget.md](2026-04-25_wms-registry-slo-retry-budget.md)
- [2026-04-25_energy-budget-floor-guard.md](2026-04-25_energy-budget-floor-guard.md)
- [2026-04-25_energy-budget-subsidy-authority-binding.md](2026-04-25_energy-budget-subsidy-authority-binding.md)
- [2026-04-25_energy-budget-shared-fabric-allocation.md](2026-04-25_energy-budget-shared-fabric-allocation.md)
- [2026-04-26_energy-budget-subsidy-signer-roster-verifier.md](2026-04-26_energy-budget-subsidy-signer-roster-verifier.md)
- [2026-04-26_energy-budget-subsidy-verifier-quorum.md](2026-04-26_energy-budget-subsidy-verifier-quorum.md)
- [2026-04-26_energy-budget-subsidy-quorum-threshold-policy.md](2026-04-26_energy-budget-subsidy-quorum-threshold-policy.md)
- [2026-04-26_imc-memory-glimpse-council-witness-receipt.md](2026-04-26_imc-memory-glimpse-council-witness-receipt.md)
- [2026-04-26_imc-memory-glimpse-reconsent-receipt.md](2026-04-26_imc-memory-glimpse-reconsent-receipt.md)
- [2026-04-27_imc-merge-thought-ethics-gate.md](2026-04-27_imc-merge-thought-ethics-gate.md)
- [2026-04-27_imc-merge-thought-window-policy-authority.md](2026-04-27_imc-merge-thought-window-policy-authority.md)
- [2026-04-27_imc-merge-thought-window-live-verifier.md](2026-04-27_imc-merge-thought-window-live-verifier.md)
- [2026-04-26_collective-dissolution-identity-confirmation-binding.md](2026-04-26_collective-dissolution-identity-confirmation-binding.md)
- [2026-04-26_collective-recovery-route-trace-binding.md](2026-04-26_collective-recovery-route-trace-binding.md)
- [2026-04-26_collective-external-registry-sync.md](2026-04-26_collective-external-registry-sync.md)
- [2026-04-26_collective-external-registry-ack-route-capture-export.md](2026-04-26_collective-external-registry-ack-route-capture-export.md)
- [2026-04-26_collective-external-registry-ack-live-endpoint-probe.md](2026-04-26_collective-external-registry-ack-live-endpoint-probe.md)
- [2026-04-26_collective-external-registry-ack-signed-response-envelope.md](2026-04-26_collective-external-registry-ack-signed-response-envelope.md)
- [2026-04-27_collective-external-registry-ack-mtls-client-certificate.md](2026-04-27_collective-external-registry-ack-mtls-client-certificate.md)
- [2026-04-27_collective-external-registry-ack-certificate-lifecycle.md](2026-04-27_collective-external-registry-ack-certificate-lifecycle.md)
- [2026-04-27_collective-external-registry-ack-ct-log-quorum.md](2026-04-27_collective-external-registry-ack-ct-log-quorum.md)
- [2026-04-27_collective-external-registry-ack-sct-policy-authority.md](2026-04-27_collective-external-registry-ack-sct-policy-authority.md)
- [2026-04-27_identity-confirmation-witness-registry-binding.md](2026-04-27_identity-confirmation-witness-registry-binding.md)
- [2026-04-27_wms-slo-threshold-authority-binding.md](2026-04-27_wms-slo-threshold-authority-binding.md)
- [2026-04-27_wms-slo-quorum-transport-plane-binding.md](2026-04-27_wms-slo-quorum-transport-plane-binding.md)
- [2026-04-27_wms-retry-budget-transport-binding.md](2026-04-27_wms-retry-budget-transport-binding.md)
- [2026-04-27_memory-replication-key-succession.md](2026-04-27_memory-replication-key-succession.md)
- [2026-04-28_catalog-inventory-receipt.md](2026-04-28_catalog-inventory-receipt.md)
- [2026-04-28_self-model-value-reassessment-retirement.md](2026-04-28_self-model-value-reassessment-retirement.md)
- [2026-04-28_self-model-value-timeline-lineage.md](2026-04-28_self-model-value-timeline-lineage.md)
- [2026-04-28_self-model-value-archive-retention-proof.md](2026-04-28_self-model-value-archive-retention-proof.md)
- [2026-04-28_self-model-value-archive-retention-refresh.md](2026-04-28_self-model-value-archive-retention-refresh.md)
- [2026-04-28_memory-replication-long-term-media-renewal.md](2026-04-28_memory-replication-long-term-media-renewal.md)
- [2026-04-28_self-model-autonomy-review-boundary.md](2026-04-28_self-model-autonomy-review-boundary.md)
- [2026-04-18_guardian-oversight-channel.md](2026-04-18_guardian-oversight-channel.md)
- [2026-04-18_ethics-rule-language.md](2026-04-18_ethics-rule-language.md)
