---
date: 2026-04-29
deciders: [yasufumi, codex-builder]
related_docs:
  - README.md
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_transmitter_session.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
status: decided
---

# Decision: OmoikaneOS の中心像を BioData Transmitter に寄せる

## Context

OmoikaneOS はマインドアップロード基盤 OS として、BDB、QualiaBuffer、
Sensory Loopback、Cognitive Services を個別に持っていた。
ただし user-facing な中心像としては、「どの生体データから何を作るのか」が
まだ曖昧で、脳波・心電などの実データから別モダリティの生体データを生成する
transmitter としては runtime / schema / eval が存在していなかった。

## Decision

名称と最終目標は OmoikaneOS のまま維持する。
L6 に `BioDataTransmitter` を追加し、source biosignal features を
`physiology-latent-body-state-v0` に束ね、そこから ECG/PPG/respiration/EEG/
affect/thought proxy を生成する。

中間表現は cardiac、autonomic、respiratory、neural、affect、thought-pressure
の各軸を持つ。文献 ref として PhysioNet、NeuroKit2、DEAP、
interoceptive prediction、CEBRA を束縛する。
主観同一性と semantic thought content の飛躍は runtime fact にせず、
`https://mind-upload.com/frontiers/biosignal-transmitter` の conflict sink ref に束縛する。

## Consequences

- `biodata-transmitter-demo --json` は session、body-state latent、generated bundle、validation を返す。
- public schema / IDL / eval / docs / IntegrityGuardian policy が source feature digest、latent digest、generated bundle digest、raw payload redaction、mind-upload.com conflict sink を検証する。
- thought target は attention-pressure proxy までであり、semantic thought content は生成しない。
- affect target は valence/arousal proxy までであり、discrete emotion label を断定しない。

## Revisit triggers

- 実 EEG/ECG/PPG/EDA/respiration dataset adapter を接続する時
- 個人内 calibration session を複数日にまたがって学習する時
- mind-upload.com 側の conflict sink に issue/post API ができた時
