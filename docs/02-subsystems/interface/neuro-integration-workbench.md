# Neuro Integration Workbench

L6 Interface のマルチアプリケーション統合面。アンケートと EEG を最初の seed pair とし、
fMRI、脳オルガノイド、biosensor、behavioral task、omics、clinical metadata などを
同じ source bundle contract に追加できるようにする。

目的は「既存の計測アプリ、解析アプリ、データ整備アプリ、operator copilot、
coding-agent automation を 1 つの LLM-native workspace へ置き換えられる
reference runtime surface」を作ることである。これは mind uploading へ向かうための
神経科学統合基盤であり、意識再現や本人同一性成立の主張ではない。

## 役割

- `questionnaire` と `eeg` を必須 seed source として束縛する
- BioData Transmitter の `biodata-survey-eeg-window-fusion-v1` receipt を upstream
  digest として source bundle / analysis receipt に束縛する
- fMRI BOLD と脳オルガノイドは expansion context として扱い、本人の mind-state 証明へ昇格しない
- measurement / analysis / data-curation / operator-copilot / agent-automation の置換 lane を 1 workspace に束ねる
- 各 source type が 5 つの置換 lane すべてで app digest に覆われていることを
  application replacement plan receipt に束縛する
- replacement plan の各 lane に external connector ref、credential ref、data contract ref、
  LLM tool ref を digest-only で束縛し、実アプリ置換時の接続面を明示する
- 各 biological source summary を consent ref、measurement connector ref、collection window ref に
  束縛する collection protocol receipt を作り、収集面を analysis plan より前に固定する
- collection protocol の各 step から bounded collection result summary を生成し、
  semantic thought content 非生成と operator / coding-agent review readiness を
  collection run receipt に束縛する
- collection run result を calibration、artifact/QC、consent freshness、operator review、
  quality authority refs に measurement quality gate として束縛する
- source bundle 内の全 source-type pair に bounded analysis recipe を割り当て、
  questionnaire + EEG seed から fMRI / 脳オルガノイド等へ cross-modal analysis を広げる
- cross-modal analysis plan の全 pair について bounded result summary と operator /
  coding-agent review readiness を digest-only run receipt に束縛する
- measurement quality gate と cross-modal analysis run を、非 ML operator 向けの
  plain-language synthesis cards と coding-agent task に interpretation synthesis
  receipt として束縛する
- 非 ML 専門家向けの plain-language cards と coding agent 向け task template を同じ guide receipt に入れる
- raw questionnaire / EEG / neuroimaging / organoid / analysis / connector / credential /
  endpoint / collection / collection-result / quality / calibration / artifact / consent /
  interpretation / agent-task payload は保存しない
- claim ceiling は `feature-alignment-and-analysis-plan-only` に固定する

## Reference Runtime v0

`PYTHONPATH=src python3 -m omoikane.cli neuro-integration-demo --json` は、
1 人の identity に対して次を実行する。

1. measurement、analysis、data-curation、operator-copilot、agent-automation の 5 app receipt を登録する
2. BioData Transmitter で survey+EEG fusion receipt を作り、receipt digest / fused window digest を検証する
3. questionnaire、EEG、fMRI BOLD、brain organoid の feature summary と upstream fusion receipt digest を digest-only source bundle に束縛する
4. 非 ML 専門家 operator profile と source bundle / app digest set を workspace に束縛する
5. questionnaire distress / attention proxy と EEG cortical load / alpha suppression proxy の bounded alignment を作る
6. fMRI と脳オルガノイドは expansion lane として analysis receipt に残す
7. upstream Survey EEG Fusion binding を analysis receipt に残し、BioData 側 claim ceiling を上げない
8. plain-language cards と coding-agent task templates を operator guide receipt に束縛する
9. source type ごとに measurement / analysis / data-curation / operator-copilot /
   agent-automation の coverage を replacement plan receipt に束縛する
10. replacement plan に対して measurement ingest、analysis runner、curation ledger、
    operator console、agent runner connector refs を connector bundle に束縛する
11. 各 source summary を consent refs、measurement connector refs、collection window refs に
    collection protocol として束縛する
12. collection protocol の各 step から bounded quality / risk summary を collection run
    receipt として束縛する
13. collection run result を calibration、artifact/QC、consent freshness、operator review、
    quality authority refs に measurement quality gate として束縛する
14. 現在の source type 全ペアに survey+EEG alignment、EEG+fMRI context、
    organoid context、generic feature-summary screen の bounded recipe を割り当てる
15. 各 pair の bounded result summary を生成し、operator と coding agent の review-ready
    receipt として束縛する
16. quality gate と analysis run に基づき、各 pair を plain-language synthesis card と
    coding-agent task に束縛し、非 ML operator が確認できる解釈 receipt を作る
17. ContinuityLedger に upstream receipt、source bundle、workspace、analysis、guide、
    replacement plan、connector bundle、collection protocol、collection run、quality gate、
    cross-modal analysis plan、analysis run、interpretation synthesis を記録する

## 不変条件

1. **survey+EEG seed** ── questionnaire と EEG が揃わない source bundle は seed analysis に進めない
2. **Survey EEG Fusion binding** ── BioData の fusion receipt は digest / fused window digest として束縛し、raw survey answer や raw EEG sample は取り込まない
3. **expansion, not proof** ── fMRI と脳オルガノイドは context lane であり、意識・同一性の証明ではない
4. **LLM-native** ── coding agent と非 ML 専門家の両方が同じ schema-bound workflow を使える
5. **replaceable lanes** ── 計測、解析、整備、operator copilot、agent automation の lane coverage を workspace digest に束縛する
6. **source-type lane coverage** ── 現在束縛された各 source type は 5 つの置換 lane すべてで app digest に覆われる
7. **connector coverage** ── 実アプリ置換用 connector は endpoint / credential / permission / data contract / LLM tool ref だけを保持し、各 source type を 5 lane すべてで覆う
8. **collection protocol coverage** ── 現在束縛された各 source は consent ref、feature digest、measurement connector ref、collection window ref を持つ
9. **collection run summaries** ── collection run は step digest、quality summary、risk proxy、review readiness に限り、live device quality certification には昇格しない
10. **measurement quality gate** ── calibration / artifact QC / consent freshness は refs と bounded scores に限り、医療グレード QC には昇格しない
11. **cross-modal pair coverage** ── 現在の source type 全ペアは bounded recipe と 5 lane connector support を持つ
12. **bounded result summaries** ── result は pair digest と bounded axis summary に限り、診断や因果推論には昇格しない
13. **operator interpretation synthesis** ── 解釈は analysis result digest と quality item digest に基づく plain-language action summary に限り、upload readiness には昇格しない
14. **digest-only** ── raw source / raw app / raw analysis / raw connector / raw collection / raw quality / raw plan / raw result / raw interpretation payload を保存しない
15. **claim ceiling** ── semantic thought content、clinical diagnosis、consciousness reproduction、identity replacement、upload readiness はすべて false のまま維持する

## 関連

- [biodata-transmitter.md](biodata-transmitter.md)
- [sensory-loopback.md](sensory-loopback.md)
- [../../05-research-frontiers/biosignal-transmitter.md](../../05-research-frontiers/biosignal-transmitter.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
