# BioData Transmitter (BDT)

L6 Interface のサブシステム。脳波、心電、脈波、皮膚電気活動、呼吸などの
生体データから、その人に束縛された **体内状態の中間表現** を作り、そこから
別モダリティの生体データ proxy を生成する。

OmoikaneOS の名称と目標はそのまま維持する。中心像だけを
「マインドアップロード基盤 OS」から一段具体化し、アップロード対象者の
生体信号を **生体データ → internal body-state latent → 生体データ** として
相互変換できる transmitter を核に置く。

## 役割

- `eeg / ecg / ppg / eda / respiration` の特徴量を同一 identity の
  digest-bound feature summary として受け取る
- 心拍、HRV、呼吸、交感/副交感 proxy、EEG band proxy、valence/arousal proxy、
  thought-pressure proxy を `internal-body-state-latent` に束ねる
- `ecg / ppg / respiration / eeg / affect / thought` の target modality へ
  bounded synthetic signal summary を生成する
- thought は **semantic content** を生成せず、注意圧・認知負荷の proxy だけを返す
- affect は discrete emotion 断定ではなく valence/arousal proxy に留める
- 体内状態の中間表現は literature refs を持ち、主観同一性や thought content への
  飛躍は `mind-upload.com` の conflict sink ref へ送る

## Reference Runtime v0

`PYTHONPATH=src python3 -m omoikane.cli biodata-transmitter-demo --json` は、
1 人の identity について次を 1 シナリオで実行する。

1. source modalities と target modalities を固定した BDT session を開く
2. external dataset manifest と feature-window summary を digest-only adapter receipt に束縛する
3. 複数日の adapter receipt と body-state latent を longitudinal / circadian feature-window series profile に束縛する
4. EEG/ECG/PPG/EDA/respiration features から body-state latent を作る
5. latent digest に束縛した ECG/PPG/respiration/EEG/affect/thought proxy を生成する
6. literature-backed intermediate、mind-upload.com conflict sink、raw payload redaction、
   semantic thought content 非生成を検証する
7. 2 日分の body-state latent digest を束ねた person-bound calibration profile を作る
8. feature-window series の axis drift を bounded threshold receipt に束縛し、calibration confidence gate へ渡す
9. ContinuityLedger に session / dataset adapter / feature-window series / drift gate / latent / generated bundle / conflict sink / calibration binding を残す
10. calibration profile と feature-window drift gate を identity confirmation / sensory loopback の confidence gate へ
    digest-only receipt として束縛する

## 中間表現

`physiology-latent-body-state-v0` は「実際の人間の体内情報」に近い軸を優先する。

| 軸 | v0 の扱い |
|---|---|
| cardiac | `heart_rate_bpm`, `hrv_rmssd_ms`, `cardiac_load` |
| autonomic | `sympathetic_tone`, `parasympathetic_tone`, `arousal` |
| respiratory | `rate_bpm`, `phase` |
| neural | `alpha_suppression`, `theta_beta_ratio`, `cortical_load_proxy` |
| affect | `valence_proxy`, `arousal_proxy`, `circumplex-proxy` |
| thought | `attention_pressure_proxy`, `semantic_content_generated=false` |

この latent は本人の完全な心ではなく、別の生体データを生成するための
body-state carrier である。主観経験の同一性、思考内容の復元、qualia の正規表現は
OmoikaneOS runtime 内で断定しない。

## 文献境界

v0 は次の根拠を machine-readable refs として束縛する。

- PhysioNet / PhysioBank / PhysioToolkit: 複雑な生体信号の公開資源と評価基盤
- NeuroKit2: ECG/PPG/EDA/呼吸/EEG 特徴量を同じ処理語彙で扱うための実装語彙
- DEAP: EEG と peripheral physiological signals を affect rating と対応付ける代表 dataset
- Barrett & Simmons: interoceptive prediction を body-state / affect の中間理論として扱う
- CEBRA: neural / behavioural data を latent embedding として扱う機械学習上の参照点

論文が支えるのは「中間表現を作り、bounded proxy を生成する」範囲までであり、
本人の主観同一性や意味内容の完全復元ではない。

## mind-upload.com conflict sink

runtime が解決しない論点は `mind-upload.com` ref へ逃がす。

- `https://mind-upload.com/frontiers/biosignal-transmitter#qualia-equivalence`
- `https://mind-upload.com/frontiers/biosignal-transmitter#thought-content`

これにより、OmoikaneOS の reference runtime は実装可能な transmitter を進めつつ、
矛盾や証拠不足を設計内で既成事実化しない。

## 不変条件

1. **person-bound** ── session / latent / generated bundle は同じ `identity_id` に束縛する
2. **latent-first** ── source biosignal から直接 target を出さず、必ず body-state latent を経由する
3. **digest-only** ── raw source payload と raw generated waveform は保持しない
4. **thought ceiling** ── thought target は attention pressure proxy までで、semantic content は生成しない
5. **conflict sink** ── qualia equivalence と thought content の飛躍は mind-upload.com ref に束縛する
6. **literature refs** ── 中間表現は少なくとも 5 件の文献 ref に束縛する
7. **multi-day calibration** ── 個人内 calibration は 2 日以上の latent digest set と day refs だけを束ね、raw latent / raw calibration payload は保存しない
8. **confidence gate** ── identity confirmation / sensory loopback へ渡す時は calibration digest、source modality coverage、target 別 confidence threshold を receipt で束縛し、raw gate payload は保存しない
9. **dataset adapter** ── 実 dataset は manifest digest、feature-window digest、latent ref だけに束縛し、raw dataset payload、raw signal samples、raw feature-window payload は保存しない
10. **feature-window series** ── 複数 window の adapter receipt digest、latent digest、circadian phase ref、axis drift summary だけを保持し、raw dataset / feature-window / latent / series payload は保存しない
11. **series drift gate** ── calibration confidence gate が current series を参照する時は、series profile digest、calibration digest、axis drift threshold digest を直接束縛し、raw drift payload は保存しない

## 個人内 calibration

`multi-day-personal-biodata-calibration-v1` は、複数日の `physiology-latent-body-state-v0`
を source latent refs / digests と calibration day refs へ束縛する。profile は
heart rate、HRV、autonomic arousal、cortical load、valence、thought pressure、
interoceptive confidence の平均 baseline を返すが、raw source payload、raw latent payload、
raw calibration payload は保持しない。

この profile は個人固有の baseline を上げるための reference artifact であり、
主観同一性、qualia equivalence、semantic thought content の証明には使わない。

## Confidence gate 連携

`biodata-calibration-confidence-gate-v1` は、complete な calibration profile を
identity confirmation と sensory loopback の入口へ渡すための digest-only bridge である。
gate receipt は calibration ref / digest、source latent digest set、`eeg / ecg / ppg / eda /
respiration` の coverage、target gate refs、target 別 threshold を束縛する。

reference runtime では identity confirmation gate は `confidence_score >= 0.8`、
sensory loopback gate は `confidence_score >= 0.7` を要求する。これを満たしても
本人同一性や主観経験の証明にはせず、各 target の既存 Guardian / witness / body-map
contract の confidence input としてのみ扱う。raw calibration payload と raw gate payload は
保存しない。

## Dataset adapter

`biodata-dataset-feature-window-adapter-v1` は、外部 dataset の EEG/ECG/PPG/EDA/
respiration window を `dataset_ref`、`participant_ref`、`license_ref`、`window_ref`、
modality file refs の manifest digest と、normalized feature-window digest に束縛する。
adapter receipt は body-state latent ref / digest と source feature digest を同時に保持し、
full source modality coverage が揃う時だけ confidence gate ready として扱う。

この adapter は実 dataset 接続の入口を作るが、raw sample、raw dataset payload、
raw feature-window payload は保存しない。dataset の存在や主観同一性を runtime が
証明するものではなく、実験者が別途検証した feature summary を reference runtime へ
安全に渡すための contract である。

## Feature-window series

`biodata-feature-window-series-profile-v1` は、2 件以上の dataset adapter receipt と
対応する body-state latent を ordered series として束ねる。profile は adapter receipt
digest set、latent digest set、window refs、dataset refs、circadian phase refs、
source modality coverage、axis drift summary を持つ。

axis drift は heart rate、autonomic arousal、cortical load、valence、thought pressure、
interoceptive confidence の first / last / min / max / delta / direction だけを返す。
これは longitudinal drift や日内変動を calibration の前段で監査するための
digest-only profile であり、raw sample、raw feature-window、raw latent、raw series
payload は保持しない。profile は主観同一性や semantic thought recovery を証明しない。

## Feature-window series drift gate

`biodata-feature-window-series-drift-gate-v1` は、feature-window series の
axis drift summary を calibration confidence gate に渡す前の bounded gate として扱う。
gate receipt は series profile digest、calibration digest、source latent digest set、
axis threshold policy、axis 別 pass / blocked check、drift threshold digest を保持する。

reference runtime の初期 threshold は heart rate `12.0 bpm`、autonomic arousal /
cortical load / thought pressure `0.18`、valence `0.16`、interoceptive confidence
`0.05` である。すべて pass の場合だけ confidence gate はその drift gate digest を
直接束縛して identity confirmation / sensory loopback の target binding を pass にできる。
series / calibration / drift の raw payload は保存しない。

## 関連

- [bdb-protocol.md](bdb-protocol.md)
- [sensory-loopback.md](sensory-loopback.md)
- [../mind-substrate/qualia-buffer.md](../mind-substrate/qualia-buffer.md)
- [../../05-research-frontiers/biosignal-transmitter.md](../../05-research-frontiers/biosignal-transmitter.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
