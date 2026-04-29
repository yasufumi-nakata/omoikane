---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - docs/01-architecture/data-flow.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_calibration_profile.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-transmitter-multi-day-calibration-profile
---

# Decision: BioData Transmitter の multi-day calibration profile を runtime contract にする

## Context

BioData Transmitter は source biosignal features を body-state latent へ束ね、
bounded target biosignal proxy を生成できるようになった。
ただし revisit trigger に残っていた個人内 calibration は未接続で、複数日の latent を
どの digest family として束ねるかが reviewer-facing では確認できなかった。

## Decision

`multi-day-personal-biodata-calibration-v1` を追加し、2 日以上の
`physiology-latent-body-state-v0` refs / digests と calibration day refs を
`source_latent_digest_set_digest` に束縛する。
calibration profile は heart rate、HRV、autonomic arousal、cortical load、
valence、thought pressure、interoceptive confidence の mean baseline を返す。

raw source payload、raw latent payload、raw calibration payload は保存せず、
subjective equivalence と semantic thought content は引き続き false に固定する。

## Consequences

- `biodata-transmitter-demo --json` は calibration profile と calibration validation を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy が multi-day latent digest set と raw-payload redaction を検証する。
- 個人内 calibration は transmitter 精度の reference artifact であり、qualia equivalence や semantic thought recovery の証明にはしない。

## Revisit triggers

- 実 EEG/ECG/PPG/EDA/respiration dataset adapter を接続する時
- 2 日平均ではなく longitudinal drift / circadian profile を扱う時
- calibration profile を identity confirmation や sensory loopback の confidence gate に渡す時
