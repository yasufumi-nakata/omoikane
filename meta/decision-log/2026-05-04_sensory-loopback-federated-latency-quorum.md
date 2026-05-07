---
decision_id: sensory-loopback-federated-latency-quorum-2026-05-04
status: accepted
date: 2026-05-04
area: interface/sensory-loopback
touchpoints:
  - src/omoikane/interface/sensory_loopback.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - specs/schemas/sensory_loopback_calibration_refresh_state_guard.schema
  - specs/schemas/README.md
  - specs/catalog.yaml
  - evals/interface/sensory_loopback_biodata_arbitration.yaml
  - evals/interface/sensory_loopback_public_schema_contract.yaml
  - evals/interface/README.md
  - docs/02-subsystems/interface/sensory-loopback.md
  - docs/07-reference-implementation/README.md
  - tests/unit/test_sensory_loopback.py
  - tests/integration/test_cli.py
  - tests/integration/test_interface_schema_contracts.py
  - tests/integration/test_reference_runtime.py
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/sensory_loopback.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.sensory_loopback.v0.idl
  - specs/schemas/sensory_loopback_session.schema
  - specs/schemas/sensory_loopback_receipt.schema
  - specs/schemas/sensory_loopback_artifact_family.schema
  - specs/schemas/sensory_loopback_biodata_arbitration_binding.schema
  - specs/schemas/sensory_loopback_calibration_refresh_state_guard.schema
---

# Decision

Sensory Loopback shared fields now support a bounded 5-8 participant latency
quorum profile: `federated-latency-quorum-v1`. The existing 3-4 participant
`weighted-latency-quorum-v1` profile remains unchanged, and strict latency
continues to require every participant timing gate to pass.

# Rationale

The deterministic repo gap was the documented scale-out boundary beyond four
participants for shared sensory fields. The safe reference-runtime closure is
not an unbounded mesh: it extends the same digest-only BioData arbitration
binding to a federated latency quorum with explicit participant weights,
threshold, failed participant ids, policy-authority digest, and fresh verifier
quorum. This lets the runtime verify bounded larger shared fields without
claiming subjective identity, thought content, or consciousness reproduction.

# Implementation

The runtime derives `federated-latency-quorum-v1` when a shared sensory loopback
session has five to eight participants and weighted quorum data is provided.
The schema caps were raised from four to eight participants for session,
receipt, artifact-family, BioData arbitration binding, and calibration refresh
guard payloads. The CLI demo now emits both a 3 participant weighted quorum and
a 5 participant federated quorum, and the public schema contract manifest binds
both paths to reviewer-facing schemas.

# Verification

Unit tests cover successful 5 participant federated acceptance, blocked
participant accounting, policy/verifier binding, and rejection of a weighted
profile above four participants. Integration tests assert the demo output and
public schema contracts for the new federated path.

# Revisit Triggers

- Shared sensory fields need more than eight participants.
- Latency policy authority moves from fixed digest-bound fixtures to a dynamic
  provider.
- Empirical multi-person hardware timing evidence requires a different quorum
  profile.
- Research evidence justifies changing the current BioData
  `body-state-surrogate-input-only` claim ceiling.
