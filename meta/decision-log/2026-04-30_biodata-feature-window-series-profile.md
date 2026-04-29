---
date: 2026-04-30
deciders: [yasufumi, codex-builder]
related_docs:
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/07-reference-implementation/README.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_feature_window_series_profile.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
closes_next_gaps:
  - biodata-feature-window-series-profile
---

# Decision: BioData feature-window series を longitudinal / circadian profile にする

## Context

`biodata-dataset-feature-window-adapter-v1` は単一 external dataset window を
manifest digest、feature-window digest、body-state latent ref に束縛できる。
しかし multi-day calibration の前段で、複数 window が同じ identity / session に属し、
adapter receipt digest と latent digest の ordered set、circadian phase refs、
axis drift summary を raw payload 無しで確認する contract が不足していた。

## Decision

`biodata-feature-window-series-profile-v1` を追加し、2 件以上の dataset adapter receipt と
対応する body-state latent を ordered series として束ねる。profile は adapter refs、
adapter receipt digest set、window refs、dataset refs、latent refs/digests、
source feature digests、circadian phase refs、required modality coverage、
heart rate / autonomic arousal / cortical load / valence / thought pressure /
interoceptive confidence の drift summary を保持する。

raw dataset payload、raw signal samples、raw feature-window payload、raw latent payload、
raw series payload は保存しない。series は longitudinal drift と日内変動の監査用
digest-only profile であり、主観同一性や semantic thought recovery を証明しない。

## Consequences

- `biodata-transmitter-demo --json` は dataset adapter receipt 2 件と
  feature-window series profile を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy は series digest set、
  profile digest、phase refs、axis drift summary、raw payload redaction を検証する。
- multi-day calibration は今後も body-state latent digest set から作るが、その前段に
  adapter receipt series の監査 surface が残る。

## Revisit triggers

- 実 dataset loader が window series を live source から組み立てる時
- circadian phase を external clock / sleep diary / wearable verifier に束縛する時
- calibration gate が feature-window series drift threshold を直接参照する時
