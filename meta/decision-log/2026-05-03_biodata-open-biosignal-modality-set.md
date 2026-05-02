---
decision_id: biodata-human-biosignal-open-catalog-2026-05-03
status: accepted
date: 2026-05-03
area: interface/biodata-transmitter
touchpoints:
  - src/omoikane/interface/biodata_transmitter.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_human_biosignal_catalog.schema
  - specs/schemas/biodata_transmitter_session.schema
  - specs/schemas/biodata_body_state_latent.schema
  - specs/schemas/biodata_signal_bundle.schema
  - specs/schemas/biodata_dataset_adapter_receipt.schema
  - specs/schemas/biodata_calibration_profile.schema
  - specs/schemas/biodata_feature_window_series_profile.schema
  - specs/schemas/biodata_calibration_confidence_gate.schema
  - specs/schemas/README.md
  - evals/interface/biodata_transmitter_roundtrip.yaml
  - evals/interface/README.md
  - docs/01-architecture/overview.md
  - docs/01-architecture/data-flow.md
  - docs/01-architecture/layered-model.md
  - docs/02-subsystems/interface/README.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - tests/unit/test_biodata_transmitter.py
  - tests/integration/test_interface_schema_contracts.py
---

# Decision

BioData Transmitter sessions now use an open biosignal modality set instead of
hard-coding EEG, ECG, PPG, EDA, and respiration as the only accepted biological
signals. The open set is not an empty free-text field: it is bound to
`human-biosignal-open-modality-catalog-v1`, a family catalog for human-derived
signals, with an explicit fallback for uncatalogued human biosensors.

# Rationale

The project goal is to convert from any available human biological signal
summary into the current body-state latent and then into another biological
signal proxy. A fixed enum was useful for the first reference runtime, but it
would reject future signals such as EMG, skin temperature, blood pressure, SpO2,
pupil diameter, voice acoustics, blood glucose, fNIRS, fMRI BOLD, or
device-specific ECG variants before they could be safely represented.

At the same time, accepting arbitrary strings without classification would make
the contract too weak for review. The runtime therefore binds known human
biosignals to a public catalog spanning neural electrical, neural magnetic,
neurovascular, evoked response, cardiac, vascular flow/perfusion, respiratory,
electrodermal, muscle, ocular, thermal, pressure/fluid, motion, acoustic,
gastrointestinal, urogenital, renal/urinary, biochemical, imaging, omics, and
sleep/circadian categories, while treating new human biosensors as
`uncatalogued_human_biosignal` generic proxies.

# Implementation

The runtime now normalizes common modality aliases, requires features to be
declared in the session, and stores per-modality `source_modality_projections`
with modality family, catalog status, catalog digest, feature digest,
feature-name digest, intensity proxy, variability proxy, and projection
confidence. Known targets still use dedicated proxy generation, while unknown
targets use `generic-feature-summary-to-biosignal-proxy-v1`.
The catalog is also emitted as `biodata_human_biosignal_catalog.schema` so
family coverage, alias targets, catalog digest, and uncatalogued fallback policy
are independently schema-validatable.
Calibration and confidence gates now require coverage of the session-declared
source modalities, not a globally fixed five-modality set.

# Verification

Unit tests cover custom EMG, skin-temperature, blood-pressure, 3-lead ECG,
SpO2, fMRI BOLD, pupil, voice, blood glucose, and uncatalogued human biosensor
roundtrips. Public schemas require catalog/family binding while preserving raw
payload redaction and no semantic-thought-content claims.

# Revisit Triggers

- Add target-specific generators when a new modality has enough evidence for a
  safer non-generic proxy.
- Tighten modality-name normalization if external dataset naming requires a
  signed registry or ontology binding.
