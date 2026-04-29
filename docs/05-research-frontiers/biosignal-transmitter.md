---
status: in-progress
priority: T0
last_revisit: 2026-04-29
researcher: yasufumi
---

# Biosignal Transmitter

## 問題定義

脳波、心電、脈波、皮膚電気活動、呼吸などの生体データから、その人の
別モダリティの生体データを生成できるか。OmoikaneOS ではこの問題を
**生体データ → 実体に近い体内状態 latent → 生体データ** と分解する。

ここでいう体内状態 latent は、単なる任意の embedding ではなく、心拍、HRV、
呼吸、交感/副交感 proxy、EEG band proxy、interoceptive confidence、
valence/arousal proxy、thought-pressure proxy のように、人間の体内情報に
意味付けしやすい軸を優先する。

## 既知の進捗

- PhysioNet / PhysioBank / PhysioToolkit は、複雑な physiological signals を
  公開データと評価ツールで扱う基盤を示している。
- NeuroKit2 は ECG、PPG、EDA、呼吸、EEG などを同一ツールキットで処理する
  実装語彙を与える。
- DEAP は EEG と peripheral physiological signals を valence / arousal 等の
  affect annotation と組み合わせる代表例である。
- interoceptive prediction / inference は、身体内部状態と affect / embodied self を
  接続する中間理論として使える。
- CEBRA のような joint neural / behavioural latent embedding は、神経活動と行動を
  仮説駆動または自己教師ありで低次元 latent に束ねる参照点になる。

## ブロッキング要因

- biosignal の相互生成は相関を作れても、本人の主観経験と同一とは限らない。
- thought target は、注意圧や認知負荷 proxy までは扱えても、意味内容の復元を
  biosignal だけから断定できない。
- affect は valence / arousal で近似できるが、文化・文脈・自己報告に依存する
  discrete emotion label は過剰主張になりやすい。
- EEG / ECG / EDA / respiration のサンプリング条件、センサ位置、個人差、病態は
  latent の比較可能性を壊し得る。

## 暫定運用方針

OmoikaneOS は `interface.biodata_transmitter.v0` を採用し、reference runtime では
次の範囲に限定する。

- source biosignal は feature summary digest だけを保持し、raw payload を保存しない
- intermediate は `physiology-latent-body-state-v0` として person-bound にする
- generated target は ECG/PPG/respiration/EEG/affect/thought の bounded proxy に留める
- thought は semantic content を生成しない
- qualia equivalence と thought content の飛躍は
  `https://mind-upload.com/frontiers/biosignal-transmitter` の conflict sink ref に束縛する

## 解決時のシステムへの影響

- BDB は neuron-level gradual replacement だけでなく、多モダリティ生体信号の
  transmitter として厚くなる。
- QualiaBuffer は raw sensory stream ではなく body-state latent と stronger binding を持つ。
- Sensory Loopback は avatar output だけでなく、生体データ再生成の feedback target になる。
- identity confirmation は自己報告、witness、body-state latent の三者整合を使える。

## 関連文献／実験

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
