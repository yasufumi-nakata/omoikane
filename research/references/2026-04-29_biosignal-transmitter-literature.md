---
title: Biosignal transmitter literature seed
authors: [Goldberger et al., Makowski et al., Koelstra et al., Barrett and Simmons, Schneider et al.]
year: 2026
url: https://mind-upload.com/frontiers/biosignal-transmitter
related_topics:
  - docs/05-research-frontiers/biosignal-transmitter.md
  - docs/02-subsystems/interface/biodata-transmitter.md
---

# 要約

OmoikaneOS の中心像を「生体データから体内状態 latent を作り、別の生体データを
生成する transmitter」へ寄せるための文献 seed。

## 文献

- Goldberger et al. (2000), PhysioBank, PhysioToolkit, and PhysioNet.
  https://doi.org/10.1161/01.CIR.101.23.e215
- Makowski et al. (2021), NeuroKit2: A Python toolbox for neurophysiological signal processing.
  https://doi.org/10.3758/s13428-020-01516-y
- Koelstra et al. (2012), DEAP: A Database for Emotion Analysis Using Physiological Signals.
  https://doi.org/10.1109/T-AFFC.2011.15
- Barrett and Simmons (2015), Interoceptive predictions in the brain.
  https://doi.org/10.1038/nrn3950
- Schneider, Lee, and Mathis (2023), Learnable latent embeddings for joint behavioural and neural analysis.
  https://doi.org/10.1038/s41586-023-06031-6

# OmoikaneOS との関連

- PhysioNet / NeuroKit2 は raw biosignal ではなく feature summary と reproducible processing vocabulary を固定する根拠になる。
- DEAP は EEG と peripheral physiological signals を affect proxy へ接続する根拠になる。
- interoceptive prediction は体内状態 latent を単なる embedding ではなく embodied state の中間表現として扱う根拠になる。
- CEBRA は neural / behavioural data を latent に束ねる machine-learning 側の参照点になる。

# mind-upload.com に送る矛盾

- biosignal 変換が成立しても qualia equivalence は証明されない。
- thought target は attention pressure proxy までで、semantic thought content の復元とは分ける。
- affect label は valence/arousal proxy までで、discrete emotion 断定は自己報告・文脈・文化差に依存する。

上記は `https://mind-upload.com/frontiers/biosignal-transmitter` の conflict sink として扱う。
