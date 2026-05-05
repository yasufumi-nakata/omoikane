# Observation Integration Workbench

L6 Interface の観測・計測統合面。人類がこれまで取得・計測してきた source を、
raw payload ではなく feature digest、provenance、rights、time、space、unit、
uncertainty、entity の alignment axes に縮約して扱う。

目的は「すべての実データを取り込む」ことではない。人間・地球・宇宙・社会・産業・
文化・ソフトウェアなどの観測 source を、同じ検証可能な source bundle、integration
graph、analysis plan、operator guide に乗せ、後続の Builder / Researcher / Guardian が
安全に解析順序を組み立てられる reference runtime surface を作ることである。
さらに、過去に行われた測定方法と解析方法も open-world method catalog として扱い、
測定法・解析法の名前や分類は digest-bound な ref に縮約する。

## 役割

- human biodata、neuroscience、clinical health、molecular omics、
  environmental earth、geospatial remote sensing、astronomical / cosmological、
  physics、chemical / materials、ecology、agriculture、industrial IoT、
  social / economic、cultural text / media、software telemetry、historical archival
  を open-world taxonomy として束縛する
- source manifest は feature digest、provenance ref、rights ref、time range、
  spatial ref、unit profile、uncertainty model、entity scope だけを受け取る
- questionnaire / interview / biosignal recording / imaging / sequencing / sensor /
  registry / experiment / simulation などの測定方法 family を method catalog に束縛する
- descriptive statistics / signal processing / spatial-temporal analysis /
  statistical inference / machine learning / graph analysis / omics bioinformatics /
  image analysis / simulation / qualitative analysis / privacy rights audit などの
  解析方法 family を method catalog に束縛する
- source family が違う node を cross-domain edge に束ね、graph digest と rights
  boundary を保持する
- ingest、normalize、align、model、audit、publish-digest の analysis lane を同じ
  graph digest と method catalog digest に束縛する
- 各 analysis lane の bounded result summary を analysis run receipt として束縛し、
  operator / coding-agent review readiness を明示する
- 非専門 operator 向け card と coding agent 向け task template を同じ guide receipt に入れる
- raw observation / personal / external dataset / analysis / instruction / result payload は保存しない
- claim ceiling は `cross-domain-feature-integration-plan-only` に固定する

## Reference Runtime v0

`PYTHONPATH=src python3 -m omoikane.cli observation-integration-demo --json` は、
1 人の identity に対して次を実行する。

1. observation taxonomy を作り、source family と alignment axes を digest-bound にする
2. measurement / analysis method catalog を作り、過去の測定法と解析法を open-world に分類する
3. EEG、fMRI BOLD、climate record、satellite imagery、telescope image、survey を
   6 つの異なる family として source bundle に束縛する
4. source bundle から cross-domain integration graph を作り、uncertainty propagation と
   rights boundary を固定する
5. analysis question を ingest / normalize / align / model / audit / publish-digest lane に分解し、
   各 lane を measurement method ref と analysis method ref に束縛する
6. beginner operator card と coding-agent task template を operator guide に束縛する
7. 各 lane の bounded result summary を digest-only analysis run として生成する
8. taxonomy、method catalog、source bundle、graph、analysis plan、guide、analysis run を ContinuityLedger に記録する

## 不変条件

1. **open-world taxonomy** ── catalog 外 source type は未知として扱えるが、family と alignment axes の束縛を外さない
2. **digest-only source bundle** ── raw observation payload、個人 payload、外部 dataset payload を保存しない
3. **method catalog, not method capture** ── 測定法と解析法は method id / ref / digest に縮約し、raw algorithm や code payload を保存しない
4. **rights-first graph** ── cross-domain edge は rights boundary と uncertainty propagation を持つ
5. **plan, not truth** ── 統合結果は解析計画であり、完全知識や真理統一の主張ではない
6. **bounded lane results** ── analysis run は lane ごとの bounded summary に限り、診断、因果真理、完全知識へ昇格しない
7. **claim ceiling** ── consciousness reproduction と identity replacement は false のまま維持する

## 研究課題

実世界の全観測 source には、権利、同意、単位、時空間解像度、測定誤差、entity 同定の
不一致が残る。reference runtime はこれらを隠さず、
[../../05-research-frontiers/observation-integration.md](../../05-research-frontiers/observation-integration.md)
へ分離する。

## 関連

- [neuro-integration-workbench.md](neuro-integration-workbench.md)
- [biodata-transmitter.md](biodata-transmitter.md)
- [../../05-research-frontiers/observation-integration.md](../../05-research-frontiers/observation-integration.md)
- [../../07-reference-implementation/README.md](../../07-reference-implementation/README.md)
