---
status: in-progress
priority: T0
last_revisit: 2026-05-06
researcher: yasufumi
---

# Biosignal Transmitter

## 問題定義

脳波、心電、脈波、皮膚電気活動、呼吸に限らず、人間から取られる神経、心血管、
呼吸、皮膚、筋、眼、体温、運動、音声、消化管、血液・間質液・汗・唾液・呼気、
睡眠/概日などの生体データから、その人の別モダリティの生体データを生成できるか。
OmoikaneOS ではこの問題を
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
- reference runtime は 2026-05-03 時点で
  `human-biosignal-open-modality-catalog-v1` を採用し、既知の human biosignal を
  family に束縛しつつ、catalog 外の新規 human biosignal も generic proxy として保持できる。
- catalog は `biodata_human_biosignal_catalog.schema` として公開され、family coverage、
  alias target、uncatalogued fallback policy、raw payload 非保持を machine-checkable にした。
- demo は EEG/ECG/PPG/EDA/呼吸に加えて EMG、体温、血圧、SpO2、瞳孔、音声、
  加速度、血糖、fNIRS、fMRI BOLD、未カタログ human biosensor の roundtrip を検証する。
- 2026-05-05 時点で `interface.neuro_integration_workbench.v0` を追加し、
  questionnaire + EEG を seed pair、fMRI BOLD と brain organoid を expansion lane とする
  multi-application workspace を reference runtime にした。
- reference runtime は `biodata-survey-eeg-window-fusion-v1` により、アンケート score
  summary digest と EEG feature-window digest を同じ analysis window に束縛し、非 ML
  利用者向け LLM workflow ref を持つ bounded receipt として検証する。
- Neuro Integration Workbench はこの Survey EEG Fusion receipt を upstream digest として
  source bundle / analysis receipt に束縛し、BioData 側の bounded receipt を multi-application
  workspace の seed にできる。
- 2026-05-05 時点で NIW は application connector bundle を追加し、measurement ingest、
  analysis runner、curation ledger、operator console、agent runner の connector refs /
  credential refs / data contract refs / LLM tool refs を replacement plan に digest-only で束縛する。
- 同日、NIW は collection protocol receipt を追加し、questionnaire、EEG、fMRI BOLD、
  brain organoid の source summaries を consent refs、measurement connector refs、
  collection window refs に analysis planning 前の digest-only 収集境界として束縛する。
- 続いて NIW は collection run receipt を追加し、collection protocol の各 step から
  bounded quality / risk summary と operator / coding-agent review readiness を digest-only で束縛する。
- さらに NIW は measurement quality gate を追加し、collection run result を calibration、
  artifact/QC、consent freshness、operator review、quality authority refs に digest-only で束縛する。
- 同日、NIW は cross-modal analysis plan を追加し、現在 source bundle に入っている source type
  全ペアへ bounded recipe と connector support を割り当てる。
- 続いて NIW は cross-modal analysis run を追加し、全 pair の bounded result summary と
  operator / coding-agent review readiness を digest-only receipt として束縛する。
- 2026-05-06 時点で NIW は interpretation synthesis receipt を追加し、measurement quality
  gate と cross-modal analysis run を plain-language synthesis cards と coding-agent tasks に
  束縛する。
- 同日、NIW reference demo は biosensor、behavioral task、omics、clinical metadata を
  questionnaire / EEG / fMRI / brain organoid と同じ source bundle、collection、
  quality gate、cross-modal analysis、interpretation synthesis pipeline に通すよう拡張した。
- 同日、NIW は open biodata source の axis derivation と analysis recipes を追加し、
  biosensor / behavioral task / omics / clinical metadata を generic feature fallback ではなく
  bounded context screen として扱うようにした。
- 同日、NIW は longitudinal timeline receipt を追加し、2 つの source-bundle window を
  per-source axis drift / stability proxy として束縛するようにした。
- 同日、NIW は operator runbook receipt を追加し、receipt chain 全体を 9 step の
  plain-language operator card と coding-agent task に束縛するようにした。

## ブロッキング要因

- biosignal の相互生成は相関を作れても、本人の主観経験と同一とは限らない。
- thought target は、注意圧や認知負荷 proxy までは扱えても、意味内容の復元を
  biosignal だけから断定できない。
- affect は valence / arousal で近似できるが、文化・文脈・自己報告に依存する
  discrete emotion label は過剰主張になりやすい。
- EEG / ECG / EDA / respiration のサンプリング条件、センサ位置、個人差、病態は
  latent の比較可能性を壊し得る。
- アンケートと EEG の feature alignment は、自己報告と神経電気 proxy の関係を見るだけであり、
  clinical diagnosis、意識再現、本人同一性置換の証拠にはならない。
- 脳オルガノイドは in-vitro neural tissue context であって、対象者本人の body-state latent や
  mind-state proof と同一視しない。
- self-report と EEG feature の alignment は測定条件、質問文、文化・言語、状態依存性に強く
  影響されるため、runtime では診断や感情断定ではなく score summary と EEG proxy の
  bounded alignment check に留める。

## 暫定運用方針

OmoikaneOS は `interface.biodata_transmitter.v0` を採用し、reference runtime では
次の範囲に限定する。

- source biosignal は feature summary digest だけを保持し、raw payload を保存しない
- intermediate は `physiology-latent-body-state-v0` として person-bound にする
- generated target は既知 modality では専用 bounded proxy、未知 modality では
  `generic-feature-summary-to-biosignal-proxy-v1` による bounded generic biosignal proxy に留める
- session は human biosignal catalog digest、source / target modality family map、
  未カタログ modality policy を束縛する
- circadian phase refs は external clock / sleep diary / wearable evidence digest に束縛し、
  raw phase verifier payload を保存しない
- 個人内 calibration は複数日の body-state latent digest set と day refs を
  `multi-day-personal-biodata-calibration-v1` に束縛し、raw source / latent / calibration payload は保存しない
- アンケートは raw answer ではなく normalized score summary digest として
  `biodata-survey-eeg-window-fusion-v1` に入れ、EEG feature digest、window alignment evidence、
  LLM-native no-ML operator profile に束縛する
- calibration は `biodata-calibration-confidence-gate-v1` として identity confirmation /
  sensory loopback に渡せるが、confidence input に留め、本人同一性や主観同一性の証明にはしない
- sensory loopback 側では `biodata-calibration-gated-drift-threshold-v1` として
  body-map drift threshold の最大 `0.04` の補助補正だけに使い、Guardian hold /
  body-map calibration / stabilization は置き換えない
- `interface.neuro_integration_workbench.v0` は measurement / analysis / data-curation /
  operator-copilot / agent-automation の 5 replacement lane を持つが、claim ceiling は
  `feature-alignment-and-analysis-plan-only` のままにする
- replacement plan receipt は、現在 source bundle に入っている各 source type が 5 lane
  すべてで app digest に覆われることだけを検証し、未知 source の科学的妥当性は別途研究課題として扱う
- application connector bundle は endpoint / credential / permission / data contract /
  LLM tool の参照と digest coverage だけを検証し、live connector の権限監査、課金、
  latency、実データ品質、外部 API 安全性は別途研究課題として扱う
- collection protocol は measurement connector coverage、consent ref、collection window ref
  の digest-only 境界だけを検証し、実測デバイスの校正、信号品質、被験者負荷、IRB/法務監査、
  longitudinal sampling 妥当性は別途研究課題として扱う
- collection run は feature summary completeness、construct coverage、connector binding、
  consent binding から bounded quality / risk proxy を返すだけで、実測デバイスの
  calibration、artifact rejection、clinical-grade QC、session burden safety を証明しない
- measurement quality gate は calibration / artifact QC / consent freshness refs と bounded
  score を束縛するが、実測機器の校正手順そのもの、artifact rejection algorithm の妥当性、
  IRB/法務承認、session burden safety、医療グレード品質保証は別途研究課題として扱う
- cross-modal analysis plan は全 source-type pair の分析計画 coverage だけを検証し、
  open biodata source には modality-specific context recipes を割り当てるが、
  modality-specific causal inference、large-scale cohort validity、clinical utility、
  upload-readiness は別途研究課題として扱う
- cross-modal analysis run は bounded compatibility / uncertainty summary だけを返し、
  medical-grade result、semantic thought content、subjective equivalence、upload readiness には
  昇格しない
- interpretation synthesis は quality item digest と analysis result digest から
  non-ML operator next action と coding-agent task を作るだけで、診断、因果推論、
  semantic thought content、subjective equivalence、upload readiness には昇格しない
- longitudinal timeline は repeated source-bundle window の axis drift / stability proxy
  だけを返し、人格同一性の連続性、clinical longitudinal validity、upload readiness の
  証明には昇格しない
- operator runbook は既存 receipt の順序化と review task だけを返し、operator 判断、
  臨床判断、semantic thought content、upload readiness の自動結論には昇格しない
- open biodata lane は source type coverage を増やすが、各 modality の専門的妥当性、
  専用 axis derivation と bounded context recipe を持っても、longitudinal stability、
  clinical validity、regulatory readiness は source-specific research frontier として残す
- Workbench は BioData の Survey EEG Fusion receipt digest / fused window digest を受け取るが、
  BioData 側の `survey-eeg-correlation-input-only` ceiling を診断や mind-state proof へ昇格しない
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
