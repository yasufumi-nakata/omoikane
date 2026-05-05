# L6 Interface

外界・他自我・生体側との接続層。

## 主要境界

### BioData Transmitter (BDT)
- 脳波・心電・脈波・皮膚電気活動・呼吸に限らず、人間から取られる神経・心血管・筋・眼・体温・運動・音声・生化学系などの session-declared 任意生体データ
- source / target modality は `human-biosignal-open-modality-catalog-v1` の catalog digest と family map に束縛
- 生体データを `internal body-state latent` に束ね、別モダリティの生体データ proxy と未知 target の generic biosignal proxy を生成
- affect は valence/arousal proxy、thought は attention-pressure proxy までに制限
- 主観同一性や thought content の飛躍は `mind-upload.com` conflict sink ref に分離
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli biodata-transmitter-demo --json`
  で literature-backed intermediate、dataset adapter、circadian phase verifier、
  target biosignal generation、raw payload redaction、conflict sink binding をまとめて検証する

### Neuro Integration Workbench (NIW)
- アンケートと EEG を seed pair として、fMRI BOLD、脳オルガノイド、biosensor、
  behavioral task、omics、future biological source を同じ source bundle に追加する
- BDT の Survey EEG Fusion receipt を upstream digest として受け取り、NIW の source bundle /
  analysis receipt に再束縛する
- 計測アプリ、解析アプリ、データ整備アプリ、operator copilot、coding-agent automation を
  LLM-native workspace の置換 lane として束縛する
- source type ごとに 5 置換 lane の app digest coverage を application replacement plan に束縛する
- replacement plan に external connector refs / credential refs / data contract refs /
  LLM tool refs を束縛し、実アプリ置換の接続面を raw payload なしで検証する
- 各 biological source summary を consent refs、measurement connector refs、collection window
  refs に束縛する collection protocol を analysis plan より前に固定する
- collection protocol の各 step から bounded collection result summary と review readiness を
  collection run receipt に束縛する
- collection run result を calibration / artifact QC / consent freshness / operator review /
  quality authority refs に束縛する measurement quality gate を設ける
- 現在の source type 全ペアに bounded analysis recipe と connector support を割り当てる
  cross-modal analysis plan を束縛する
- cross-modal analysis plan の全 pair から bounded result summary を生成し、operator /
  coding-agent review readiness を raw result payload なしで束縛する
- 非 ML 専門家向け plain-language guide と coding agent 向け task template を同じ receipt に入れる
- fMRI と脳オルガノイドは expansion context であり、意識再現や本人同一性の証明にはしない
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli neuro-integration-demo --json`
  で BDT Survey EEG Fusion receipt binding、expansion modality binding、replacement lane coverage、
  source-type lane coverage、connector bundle binding、collection protocol binding、
  collection run binding、measurement quality gate binding、cross-modal analysis pair coverage、
  bounded result summary binding、raw payload redaction、claim ceiling をまとめて検証する

### Observation Integration Workbench (OIW)
- 人類が取得・計測してきた source を、human biodata、neuroscience、clinical health、
  molecular omics、environmental earth、geospatial remote sensing、astronomical /
  cosmological、physics、chemical / materials、ecology、agriculture、industrial IoT、
  social / economic、cultural text / media、software telemetry、historical archival の
  open-world taxonomy に束縛する
- source は raw payload ではなく feature digest、provenance、rights、time、space、
  unit、uncertainty、entity の alignment axes として扱う
- questionnaire / biosignal recording / imaging / sequencing / sensor / registry /
  experiment / simulation などの測定方法と、statistics / signal processing /
  spatial-temporal / inference / machine learning / graph / omics / image /
  simulation / qualitative / rights-audit 解析方法を method catalog に束縛する
- cross-domain graph、analysis plan、operator guide を同じ source bundle digest に束縛する
- ingest / normalize / align / model / audit / publish-digest lane の bounded result
  summary を analysis run として束縛する
- 完全知識、真理統一、意識再現、本人同一性成立の主張はしない
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli observation-integration-demo --json`
  で taxonomy、source bundle、integration graph、analysis lane、operator handoff、
  method catalog、analysis run、raw payload redaction、claim ceiling をまとめて検証する

### Biological-Digital Bridge (BDB)
- BCI（脳-コンピュータ・インタフェース）
- 神経インタフェース
- 生体センサ（心拍・体温・ホルモン）
- 漸進置換時の信号変換
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli bdb-demo --json`
  で ms 級 latency budget、fail-safe fallback、ContinuityLedger 記録、
  置換比率の増減をまとめて検証する

### Inter-Mind Channel (IMC)
- 他のアップロード自我との通信
- 公開／親密／秘匿の段階的開示
- 通信内容は両者の SelfModel に従いフィルタ
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli imc-demo --json`
  で fail-closed handshake、narrow disclosure floor、summary+digest-only audit、
  Council-witnessed memory_glimpse receipt、emergency disconnect、
  timeboxed re-consent receipt、250ms timeout-bound live-verifier-backed
  merge_thought window authority を
  まとめて検証する

### Collective Identity
- 複数自我の bounded `merge_thought` を支える実験的 collective ID
- IdentityRegistry 上の distinct ID と meta-council governance
- merge 後の `private_reality` 退避と member recovery
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli collective-demo --json`
  で collective formation、merge window cap、WMS private escape、
  identity confirmation、dissolution、recovery verifier transport binding を
  まとめて検証する

### World Model Sync (WMS)
- 外界状態の同期
- **共有現実 (shared reality)** ── 多自我が同じ外界モデルを共有
- **個別現実 (private reality)** ── 自分専用の外界モデル
- 不整合時の自動退避
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli wms-demo --json`
  で minor reconcile、major divergence、subjective-time attested time_rate deviation escape、
  unanimous / Guardian-attested physics rules change、ordered approval collection、
  distributed approval fan-out、rollback-token revert、malicious inject、
  private reality escape、external engine transaction log binding を検証する

### Sensory Loopback (SL)
- 感覚出力（音／映像／触覚）のフィードバック
- 仮想空間での自己身体感覚
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli sensory-loopback-demo --json`
  で coherent delivery、guardian hold、safe baseline からの stabilization、
  BioData calibration confidence gate による bounded drift-threshold adjustment、
  qualia binding ref、shared IMC / collective 空間での multi-self arbitration をまとめて検証する

### External World Agents (EWA)
- ロボット・ドローン・センサ等の物理世界 actuator
- 物理介入時の倫理ガード（暴力・違法行為禁止）
- reference runtime v0 では `PYTHONPATH=src python3 -m omoikane.cli ewa-demo --json`
  で device-specific motor plan、jurisdiction-bound legal preflight、
  guardian-reviewed authorization artifact、reversible command の Guardian observe、
  latched emergency stop、blocked token の fail-closed veto、
  digest-only audit、forced release を検証する

## プロトコル

### IMC Handshake

```
1. 相手の IdentityRegistry エントリを検証
2. 開示レベルを SelfModel.disclosure_template から選択
3. 共通暗号化路を確立（量子鍵配送 or 後継）
4. 通信開始
5. 終了時に通信ログを ContinuityLedger に記録（要約のみ）
```

### WMS 不整合時の退避

```
if shared_reality.state_hash != local_belief.state_hash:
  if minor_diff: reconcile via consensus_round
  if major_diff: switch to private_reality, notify Council
```

## 不変条件

1. **BDT latent-first** ── 生体データ変換は必ず体内状態 latent を経由する
2. **BDB fail-safe** ── 橋が失活したら生体側のみで自律可能な状態へ即時退避
1. **盗聴不可** ── IMC は forward secrecy 必須
2. **詐称不可** ── 他自我のなりすまし防止
3. **退避自由** ── 共有現実から個別現実への退避を阻害しない
4. **物理境界の倫理ガード** ── EWA 経由の物理介入は EthicsEnforcer の事前承認

## サブドキュメント

- [biodata-transmitter.md](biodata-transmitter.md)
- [bdb-protocol.md](bdb-protocol.md)
- [collective-identity.md](collective-identity.md)
- [imc-protocol.md](imc-protocol.md)
- [neuro-integration-workbench.md](neuro-integration-workbench.md)
- [observation-integration-workbench.md](observation-integration-workbench.md)
- [sensory-loopback.md](sensory-loopback.md)
- [wms-spec.md](wms-spec.md)
- [ewa-safety.md](ewa-safety.md)
