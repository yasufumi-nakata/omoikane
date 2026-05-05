---
decision_id: l3-cognitive-public-schema-contract-2026-05-05
status: accepted
date: 2026-05-05
area: cognitive/schema-contracts
touchpoints:
  - tests/integration/test_interface_schema_contracts.py
  - specs/schemas/affect_state.schema
  - specs/schemas/affect_transition.schema
  - specs/schemas/attention_focus.schema
  - specs/schemas/attention_shift.schema
  - specs/schemas/imagination_scene.schema
  - specs/schemas/imagination_shift.schema
  - specs/schemas/language_render.schema
  - specs/schemas/language_shift.schema
  - specs/schemas/metacognition_report.schema
  - specs/schemas/metacognition_shift.schema
  - specs/schemas/perception_frame.schema
  - specs/schemas/perception_shift.schema
  - specs/schemas/reasoning_trace.schema
  - specs/schemas/reasoning_shift.schema
  - specs/schemas/volition_intent.schema
  - specs/schemas/volition_shift.schema
tags:
  - l3-cognitive-contract
  - public-schema-validation
  - subagent-gap-candidate
---

# Decision: L3 cognitive demos must validate against public schemas

## Context

The hourly builder preflight and `gap-report --json` were clean. Read-only
subagent inspection still found that L3 perception, reasoning, affect,
attention, volition, imagination, language, and metacognition demos had public
schemas but no single integration test that validates both baseline and
failover payloads against those schemas.

## Decision

Add an integration schema contract test for the eight L3 cognitive demo
surfaces. The test validates each baseline and failover payload against its
public schema pair, while keeping the existing runtime validation flags as the
first gate.

## Boundary

This is a reference-runtime contract closure only. It does not add new L3
capability, does not claim consciousness reproduction, thought content
recovery, subjective identity, or complete personality reproduction, and does
not change any BioData or Neuro Integration claim ceiling.

## Verification

The closure is verified by the existing unittest suite and `gap-report --json`.
