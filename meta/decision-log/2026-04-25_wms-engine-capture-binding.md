---
date: 2026-04-25
deciders:
  - codex
  - integrity-guardian
status: decided
related_docs:
  - docs/02-subsystems/interface/wms-spec.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.wms.v0.idl
  - specs/schemas/wms_engine_capture_binding_receipt.schema
  - evals/interface/wms_engine_capture_binding.yaml
closes_next_gaps:
  - 2026-04-25_wms-engine-route-trace-binding.md#wms.engine.packet-capture-privileged-acquisition-binding
---

# WMS engine capture binding

## Context

`wms_engine_route_binding_receipt` already binds the WMS engine transaction log to an authenticated
cross-host distributed transport authority-route trace. The remaining reviewer-facing gap was that
verified packet-capture export and delegated privileged capture acquisition existed in the distributed
transport surface, but WMS did not yet expose a first-class receipt that bound those artifacts to the
completed engine route binding.

## Decision

Implement `packet-capture-bound-wms-engine-route-v1` as a WMS capture binding receipt. The receipt
records only digest and reference evidence: route binding digest, authority trace digest, PCAP artifact
digest, readback digest, broker lease, capture filter digest, command digest, and aligned route refs.
It explicitly keeps raw engine payloads, raw route payloads, and raw packet bodies out of the WMS
receipt.

## Consequences

- `wms-demo --json` now returns `engine_packet_capture_export`,
  `engine_privileged_capture_acquisition`, and `engine_capture_binding` scenarios.
- `WorldModelSync.validate_engine_capture_binding_receipt` rejects mismatched capture, acquisition,
  route ref, and digest evidence.
- `wms_engine_capture_binding_receipt.schema`, `interface.wms.v0`, `wms_engine_capture_binding.yaml`,
  integration schema tests, and IntegrityGuardian invocation policy now share the same contract.

## Revisit Triggers

- A live signed packet-capture export replaces the reference fixture.
- Capture authorization becomes jurisdiction-specific rather than a delegated reference broker lease.
- A real WMS engine adapter emits route/capture evidence directly instead of through the reference demo.
