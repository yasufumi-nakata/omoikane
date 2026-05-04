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
- fMRI BOLD と脳オルガノイドは expansion context として扱い、本人の mind-state 証明へ昇格しない
- measurement / analysis / data-curation / operator-copilot / agent-automation の置換 lane を 1 workspace に束ねる
- 非 ML 専門家向けの plain-language cards と coding agent 向け task template を同じ guide receipt に入れる
- raw questionnaire / EEG / neuroimaging / organoid / analysis payload は保存しない
- claim ceiling は `feature-alignment-and-analysis-plan-only` に固定する

## Reference Runtime v0

`PYTHONPATH=src python3 -m omoikane.cli neuro-integration-demo --json` は、
1 人の identity に対して次を実行する。

1. measurement、analysis、data-curation、operator-copilot、agent-automation の 5 app receipt を登録する
2. questionnaire、EEG、fMRI BOLD、brain organoid の feature summary を digest-only source bundle に束縛する
3. 非 ML 専門家 operator profile と source bundle / app digest set を workspace に束縛する
4. questionnaire distress / attention proxy と EEG cortical load / alpha suppression proxy の bounded alignment を作る
5. fMRI と脳オルガノイドは expansion lane として analysis receipt に残す
6. plain-language cards と coding-agent task templates を operator guide receipt に束縛する
7. ContinuityLedger に source bundle、workspace、analysis、guide を記録する

## 不変条件

1. **survey+EEG seed** ── questionnaire と EEG が揃わない source bundle は seed analysis に進めない
2. **expansion, not proof** ── fMRI と脳オルガノイドは context lane であり、意識・同一性の証明ではない
3. **LLM-native** ── coding agent と非 ML 専門家の両方が同じ schema-bound workflow を使える
4. **replaceable lanes** ── 計測、解析、整備、operator copilot、agent automation の lane coverage を workspace digest に束縛する
5. **digest-only** ── raw source / raw app / raw analysis payload を保存しない
6. **claim ceiling** ── clinical diagnosis、consciousness reproduction、identity replacement はすべて false のまま維持する

## 関連

- [biodata-transmitter.md](biodata-transmitter.md)
- [sensory-loopback.md](sensory-loopback.md)
- [../../05-research-frontiers/biosignal-transmitter.md](../../05-research-frontiers/biosignal-transmitter.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
