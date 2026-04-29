---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_dataset_adapter_receipt.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-dataset-feature-window-adapter
---

# Decision: BioData dataset feature-window adapter を digest-only contract にする

## Context

BioData Transmitter は multi-day calibration profile と confidence gate まで
接続されていたが、外部 EEG/ECG/PPG/EDA/respiration dataset から得た
feature summary をどの receipt として runtime に入れるかが未接続だった。
実 dataset adapter を接続する時、raw signal sample や raw dataset payload を
reference runtime に保存せず、manifest と feature-window の digest だけを
body-state latent に束縛する境界が必要だった。

## Decision

`biodata-dataset-feature-window-adapter-v1` を追加し、dataset ref、
participant ref、license ref、window ref、modality file refs を
`dataset_manifest_digest` に束縛する。adapter は normalized feature-window summary を
既存 `physiology-latent-body-state-v0` へ変換し、source feature digest、
latent ref / digest、full source modality coverage、adapter receipt digest を返す。

raw dataset payload、raw signal samples、raw feature-window payload、raw source payload は
保存しない。adapter は dataset の実在や主観同一性、semantic thought recovery の証明ではなく、
外部で検証済みの feature summary を safe reference runtime に渡すための bridge とする。

## Consequences

- `biodata-transmitter-demo --json` は dataset manifest と adapter receipt を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy が dataset manifest digest、
  source feature digest、latent digest、raw payload redaction を検証する。
- calibration profile と confidence gate は adapter 経由 latent を使えるが、
  raw dataset / sample は引き続き保持しない。

## Revisit triggers

- 実 PhysioNet / DEAP / OpenNeuro などの dataset loader を repo-local fixture ではなく
  live adapter として扱う時
- longitudinal drift / circadian profile を feature-window series として扱う時
- participant ごとの calibration gate を shared loopback arbitration に分配する時
