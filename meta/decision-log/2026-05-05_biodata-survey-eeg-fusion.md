---
decision_id: biodata-survey-eeg-fusion-2026-05-05
date: 2026-05-05
area: interface/biodata-transmitter
status: accepted
artifacts:
  - src/omoikane/interface/biodata_transmitter.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_survey_eeg_fusion_receipt.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
  - meta/glossary.md
tags:
  - biodata-survey-eeg-fusion
  - llm-native-no-ml-operator
  - digest-only-analysis-window
deciders: [yasufumi, codex-builder]
related_docs:
  - src/omoikane/interface/biodata_transmitter.py
  - src/omoikane/reference_os.py
  - specs/interfaces/interface.biodata_transmitter.v0.idl
  - specs/schemas/biodata_survey_eeg_fusion_receipt.schema
  - evals/interface/biodata_transmitter_roundtrip.yaml
  - docs/02-subsystems/interface/biodata-transmitter.md
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/07-reference-implementation/README.md
---

# Decision: アンケートと EEG は digest-only fusion receipt で統合する

## 背景

BioData Transmitter は human biosignal feature summary を body-state latent に束ね、
EEG や fMRI BOLD などの biosignal proxy を扱えるようになっていた。一方で、最初の実用
ユースケースである「アンケートデータと EEG データを統合して分析する」ための明示的な
contract はなかった。

アンケートは biosignal ではないが、自己報告・心理尺度・行動 annotation として EEG window
と同じ analysis window に束縛したい。ただし raw answer や raw EEG sample を保持すると
プライバシー、再同定、過剰診断のリスクが上がる。

## 決定

`biodata-survey-eeg-window-fusion-v1` を追加する。これは dataset adapter receipt、
body-state latent、EEG feature digest、survey instrument digest、survey score digest、
alignment evidence digest set を 1 つの `fused_window_digest` に束縛する receipt である。

出力は `digest-only-survey-eeg-feature-alignment-v1` policy に固定し、arousal、valence、
attention、fatigue など比較可能な axis の bounded alignment check だけを保持する。
`llm-native-no-ml-operator-playbook-v1` と plain-language operator summary ref を束縛し、
coding agent や機械学習に明るくない利用者が同じ artifact を読めるようにする。

## 境界

- raw survey answer、raw EEG sample、raw dataset payload、raw latent payload、raw fusion
  payload は保存しない。
- diagnosis、semantic thought content、subjective equivalence、consciousness reproduction、
  identity replacement はすべて false に固定する。
- この receipt は分析 input であり、心理診断、感情断定、意識再現、本人同一性証明ではない。

## 検証

- `BioDataTransmitter.bind_survey_eeg_window_fusion` と
  `validate_survey_eeg_window_fusion` を reference runtime に追加する。
- `biodata-transmitter-demo --json` は survey EEG fusion receipt と validation flags を返す。
- `biodata_survey_eeg_fusion_receipt.schema` と
  `evals/interface/biodata_transmitter_roundtrip.yaml` で schema / eval から検査できるようにする。

## 未解決

- self-report と EEG feature の関係は個人差、言語、質問文、測定条件に依存するため、
  `docs/05-research-frontiers/biosignal-transmitter.md` に研究課題として残す。
